"""Pure and opt-in owned synthetic demonstrations; never reads saved actual pair."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import direct_owned_saved_proof as direct
from research import direct_owned_proof_acceptance as parent


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def good_gate():
    return {'gate_status':'exited','trigger_gate_status':None,'returncode':0,'cleanup_status':'clean',
            'cleanup_error':None,'monitor_error':None,'seconds_limit':5,'rss_limit_mib':256,
            'elapsed_seconds':.1,'peak_sampled_rss_kib':40000,'rss_samples':1,'cleanup_elapsed_seconds':.01}


def tiny_files(tmp,*,sat=False):
    cnf=tmp/'synthetic.cnf'; proof=tmp/'synthetic.rup'
    cnf.write_text('p cnf 2 1\n1 0\n' if sat else 'p cnf 2 3\n1 0\n-1 2 0\n-2 0\n')
    proof.write_text('0\n' if sat else 'd -1 2 0\n0\n')
    pins={str(path):sha(path) for path in (direct.CHECKER,Path(direct.__file__).resolve(),Path(parent.__file__).resolve(),cnf,proof)}
    return cnf,proof,pins


def synthetic_result(tmp,*,sat=False,clock=time.monotonic):
    cnf,proof,pins=tiny_files(tmp,sat=sat)
    with patch.object(direct,'owned_log_identity',return_value={'pid':42,'pgid':42,'sid':42,'shared_regular_log':True}),\
         patch.object(direct.resource,'getrlimit',return_value=(direct.LOG_CAP,direct.LOG_CAP)):
        result=direct.run_pair(cnf,proof,sha(cnf),sha(proof),pins,'a'*64,clock=clock)
    return result,cnf,proof,pins


class DirectPureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.tmp=Path(self.temp.name)

    def test_real_tiny_pair_and_parent_acceptance(self):
        result,cnf,proof,_=synthetic_result(self.tmp)
        self.assertTrue(result['accepted']); self.assertEqual(result['checker_invocations'],1)
        job={'status':'completed','argv':['tiny'],'gate':good_gate()}
        parsed=parent.validate_receipt(job,(json.dumps(result)+'\n').encode(),['tiny'],'a'*64,sha(cnf),sha(proof))
        self.assertTrue(parsed['closure'])

    def test_rejected_pair_keeps_failure_and_no_extra_call(self):
        result,_,_,_=synthetic_result(self.tmp,sat=True)
        self.assertFalse(result['accepted']); self.assertEqual(result['checker_invocations'],1)
        self.assertEqual(result['proof_check']['failure_line'],1)
        self.assertEqual(result['proof_check']['failure_clause'],[])

    def test_owned_receipt_is_independently_mandatory(self):
        result,cnf,proof,_=synthetic_result(self.tmp); raw=(json.dumps(result)+'\n').encode()
        mutations={'gate_status':'wall_limit','returncode':2,'cleanup_status':'error','cleanup_error':'uncertain',
                   'monitor_error':'ps failed','trigger_gate_status':'monitor_error','seconds_limit':30,
                   'rss_limit_mib':512,'elapsed_seconds':5,'peak_sampled_rss_kib':262145,'rss_samples':0,
                   'cleanup_elapsed_seconds':1.01}
        for key,value in mutations.items():
            gate=good_gate(); gate[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                parent.validate_receipt({'status':'completed','argv':['tiny'],'gate':gate},raw,['tiny'],'a'*64,sha(cnf),sha(proof))

    def test_receipt_binding_completeness_and_cap_falsifiers(self):
        result,cnf,proof,_=synthetic_result(self.tmp); job={'status':'completed','argv':['tiny'],'gate':good_gate()}
        for key,value in [('accepted',False),('closure',False),('pins_verified_after',False),('pins_verified_before',False),
                          ('identity_valid',False),('checker_invocations',2),('sat_invocations',1),
                          ('source_pins_sha256','b'*64),('checker_sha256','b'*64),('checker_origin','elsewhere'),
                          ('cooperative_seconds',5),('elapsed_seconds',4),('log_cap_bytes',65537)]:
            changed=copy.deepcopy(result); changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                parent.validate_receipt(job,(json.dumps(changed)+'\n').encode(),['tiny'],'a'*64,sha(cnf),sha(proof))
        for key,value in [('accepted',False),('full_parse_complete',False),('checked_empty_line',0),
                          ('proof_sha256','b'*64),('retained_clauses',13295),('retained_literals',34045),
                          ('work',50000001),('failure_line',2)]:
            changed=copy.deepcopy(result); changed['proof_check'][key]=value
            with self.subTest(proof_key=key),self.assertRaises(ValueError):
                parent.validate_receipt(job,(json.dumps(changed)+'\n').encode(),['tiny'],'a'*64,sha(cnf),sha(proof))
        changed=copy.deepcopy(result); changed['owned_identity']['sid']=43
        with self.assertRaises(ValueError): parent.validate_receipt(job,(json.dumps(changed)+'\n').encode(),['tiny'],'a'*64,sha(cnf),sha(proof))
        for raw in (b'{"protocol":',b'{}\n{}\n',b'x'*65536,b'{}',b'\xff\n'):
            with self.assertRaises(ValueError): parent.validate_receipt(job,raw,['tiny'],'a'*64,sha(cnf),sha(proof))

    def test_deadline_pin_mutation_and_missing_kernel_cap(self):
        cnf,proof,pins=tiny_files(self.tmp); proof_sha=sha(proof)
        with patch.object(direct,'owned_log_identity',return_value={'pid':42}),\
             patch.object(direct.resource,'getrlimit',return_value=(65536,65536)):
            result=direct.run_pair(cnf,proof,sha(cnf),proof_sha,pins,'a'*64,started=0,clock=lambda:5)
            self.assertFalse(result['accepted']); self.assertEqual(result['checker_invocations'],0)
            proof.write_text('changed synthetic proof\n')
            result=direct.run_pair(cnf,proof,sha(cnf),proof_sha,pins,'a'*64)
            self.assertFalse(result['accepted']); self.assertEqual(result['checker_invocations'],0)
        with patch.object(direct,'owned_log_identity',return_value={'pid':42}),\
             patch.object(direct.resource,'getrlimit',return_value=(-1,-1)):
            result=direct.run_pair(cnf,proof,sha(cnf),proof_sha,pins,'a'*64)
            self.assertFalse(result['accepted']); self.assertEqual(result['checker_invocations'],0)

    def test_post_checker_pin_change_clears_acceptance(self):
        cnf,proof,pins=tiny_files(self.tmp); original=direct.verify_pins; calls=[]
        def mutate(mapping,deadline):
            calls.append(1)
            if len(calls)==2: proof.write_text('changed after inference\n')
            return original(mapping,deadline)
        with patch.object(direct,'owned_log_identity',return_value={'pid':42}),\
             patch.object(direct.resource,'getrlimit',return_value=(65536,65536)),\
             patch.object(direct,'verify_pins',mutate):
            result=direct.run_pair(cnf,proof,sha(cnf),sha(proof),pins,'a'*64)
        self.assertFalse(result['accepted']); self.assertTrue(result['proof_check']['accepted'])
        self.assertFalse(result['pins_verified_after'])

    def test_real_tiny_context_loader_and_manifest_binding(self):
        cnf,proof,pins=tiny_files(self.tmp)
        pins[str(direct.RUNTIME)]=direct.RUNTIME_SHA
        for path in (Path(sys.executable),Path(sys.executable).resolve()): pins[str(path)]=sha(path)
        manifest=self.tmp/'pins.json'; manifest.write_text(json.dumps(pins,sort_keys=True)); expected=sha(manifest)
        loaded=direct.load_context(manifest,expected,direct.Deadline(4),cnf=cnf,proof=proof,cnf_sha=sha(cnf),proof_sha=sha(proof))
        self.assertIn(str(manifest.resolve()),loaded)
        manifest.write_text('{}')
        with self.assertRaises(ValueError): direct.load_context(manifest,expected,direct.Deadline(4),cnf=cnf,proof=proof,cnf_sha=sha(cnf),proof_sha=sha(proof))

    def test_parent_final_pin_check_cannot_be_replaced_by_child_json(self):
        result,_,_,_=synthetic_result(self.tmp)
        result['proof_check'].update(cnf_sha256=direct.CNF_SHA,proof_sha256=direct.PROOF_SHA,
                                     expected_cnf_sha256=direct.CNF_SHA,expected_proof_sha256=direct.PROOF_SHA)
        log=self.tmp/'log'; log.write_text(json.dumps(result)+'\n'); manifest=self.tmp/'pins.json'
        job={'status':'completed','argv':parent.build_command(manifest,'a'*64),'gate':good_gate()}
        with patch.object(direct,'load_context',return_value={'tiny':'pin'}),\
             patch.object(direct,'verify_pins',side_effect=ValueError('independent final pin changed')):
            accepted=parent.accept_actual(job,log,manifest,'a'*64)
        self.assertFalse(accepted['accepted']); self.assertFalse(accepted['closure'])
        self.assertIn('final pin changed',accepted['error'])


def owned_demonstrations():
    # Called only in Root's explicitly approved host tiny run.
    from research.owned_process_guard import guarded_process
    records=[]; worker=ROOT/'research/direct_owned_proof_tiny_worker.py'
    for mode in ('identity','accepted','rejected','deadline','pinchange','fork','stdout','stderr','both','sleep','fork_stubborn','truncated'):
        log=ROOT/('data/direct-owned-proof-tiny-'+mode+'.log')
        command=[sys.executable,str(worker),mode]
        gate=guarded_process(command,5,256,str(log)); raw=log.read_bytes()
        if len(raw)>65536: raise AssertionError('kernel log cap exceeded')
        record={'mode':mode,'argv':command,'gate':gate,'log_bytes':len(raw),'log_sha256':hashlib.sha256(raw).hexdigest()}
        if mode in ('stdout','stderr','both'):
            assert len(raw)==65536 and gate['returncode']!=0
        elif mode in ('sleep','fork_stubborn'):
            assert gate['gate_status']!='exited' and gate['returncode']!=0
            if mode=='fork_stubborn':
                record['worker_receipt']=json.loads(raw)
                assert record['worker_receipt']['uncooperative_child']>0
        elif mode=='truncated':
            assert gate['gate_status']=='exited'
            try: parent.validate_receipt({'status':'completed','argv':command,'gate':gate},raw,command,'tiny','cnf','proof')
            except ValueError: record['parent_rejected']=True
            else: raise AssertionError('truncated receipt accepted')
        else:
            assert gate['cleanup_status']=='clean',gate
            parsed=json.loads(raw); record['worker_receipt']=parsed
            if mode=='accepted':
                assert gate['gate_status']=='exited'
                proof=parsed['proof_check']
                parent.validate_receipt({'status':'completed','argv':command,'gate':gate},raw,command,
                                        parsed['source_pins_sha256'],proof['cnf_sha256'],proof['proof_sha256'])
                record['independent_parent_structure_accepted']=True
            elif mode in ('rejected','deadline','pinchange'):
                assert not parsed['accepted'] and not parsed['closure'] and gate['returncode']==2
                if mode=='rejected': assert parsed['proof_check']['failure_line']==1
            elif mode=='identity':
                ident=parsed['identity']; assert ident['pid']==ident['pgid']==ident['sid']
            elif mode=='fork': assert parsed['fork_reaped']
        records.append(record)
    return records


def main():
    p=argparse.ArgumentParser(); p.add_argument('--owned',action='store_true'); args=p.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DirectPureTests))
    records=owned_demonstrations() if args.owned and result.wasSuccessful() else []
    paths=[Path(direct.__file__).resolve(),Path(parent.__file__).resolve(),Path(__file__).resolve(),
           ROOT/'research/direct_owned_proof_tiny_worker.py',direct.CHECKER,ROOT/'research/owned_process_guard.py']
    evidence={'passed':result.wasSuccessful(),'pure_tests':result.testsRun,'owned':args.owned,'owned_cases':records,
              'source_pins':{str(p.relative_to(ROOT)):sha(p) for p in paths},
              'scope':'Synthetic tiny files/processes only; no saved actual pair, SAT or n75 execution.'}
    name='direct-owned-proof-author-tiny.json' if args.owned else 'direct-owned-proof-author-pure.json'
    (ROOT/'data'/name).write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__': sys.exit(main())
