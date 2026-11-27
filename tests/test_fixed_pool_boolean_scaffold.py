"""Author tests: bounded parser/proof/process paths on synthetic input only."""
from collections import Counter
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from research import boolean_scaffold_cnf as c
from research import boolean_scaffold_native as native
from research import bounded_rup_checker as checker
from research import fixed_pool_boolean_scaffold157 as gate
from research.boolean_scaffold_cnf_independent_tiny_audit import make_inputs, valuation

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = []


class PureTests(unittest.TestCase):
    def test_model_parser(self):
        self.assertEqual(c.parse_model('1 -2', 2), {1: True, 2: False})
        for raw in ('1', '1 1', '1 -1', '1 0', '1 3', '1 -2 0', '1 +2', 'x -2', '1 --2'):
            with self.subTest(raw=raw), self.assertRaises(ValueError): c.parse_model(raw, 2)
        with self.assertRaises(ValueError): c.parse_model(' '*32769, 0)

    def test_stream_hash_counts_and_write_failures(self):
        args = make_inputs({(0,0),(1,1),(2,2)}, [(0,1)])
        layout = c.Layout(1,1,3,1)
        self.assertEqual(c.Layout(246,64,157,8).variables, 2645)  # arithmetic only
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'formula.cnf'; receipt = c.write_cnf(path, *args, layout)
            clauses = [v for _,v in c.iter_clauses(*args, layout)]
            expected = ('p cnf %d %d\n' % (layout.variables,len(clauses)) + ''.join(
                ''.join(str(v)+' ' for v in clause)+'0\n' for clause in clauses)).encode()
            self.assertEqual(path.read_bytes(), expected); self.assertEqual(receipt['sha256'], hashlib.sha256(expected).hexdigest())
            self.assertEqual(receipt['literals'], sum(map(len, clauses)))
            with self.assertRaises(FileExistsError): c.write_cnf(path,*args,layout)
            def timeout(): raise TimeoutError()
            with self.assertRaises(TimeoutError): c.write_cnf(Path(tmp)/'late',*args,layout,timeout)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['formula.cnf'])

    def test_proof_negatives_and_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            formula = Path(tmp)/'a.cnf'; proof = Path(tmp)/'a.rup'
            formula.write_text('p cnf 1 2\n1 0\n-1 0\n')
            def check(raw):
                proof.write_bytes(raw)
                return checker.check_proof(formula,proof,c.digest(formula),c.digest(proof))
            self.assertTrue(check(b'0\n')['accepted'])
            self.assertTrue(check(b'0\nd 1 0\n')['accepted'])
            for raw in (b'',b'0',b'2 0\n0\n',b'd 0\n0\n',b'0\nx\n',b'0\nd 1 0\nd 1 0\n',b'\xff\n'):
                with self.subTest(raw=raw),self.assertRaises(ValueError): check(raw)
            formula.write_text('p cnf 1 1\n1 0\n')
            with self.assertRaises(ValueError): check(b'0\n')
            proof.write_text('1 0\n')
            with self.assertRaises(ValueError): checker.check_proof(formula,proof,'0'*64,c.digest(proof))
            formula.write_text('p cnf 3 8\n'+''.join(' '.join(map(str,row))+' 0\n' for row in product(*[(i,-i) for i in range(1,4)])))
            proof.write_text('2 3 0\n3 0\n1 0\n0\n')
            with self.assertRaises(TimeoutError): checker.check_proof(formula,proof,c.digest(formula),c.digest(proof),work=1)
            self.assertTrue(checker.check_proof(formula,proof,c.digest(formula),c.digest(proof))['accepted'])

    def test_pins_fail_before_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'pin'; p.write_text('before'); pins={str(p):c.digest(p)}; p.write_text('after')
            with patch.object(native.subprocess,'Popen',side_effect=AssertionError('spawned')):
                with self.assertRaises(ValueError): native.run_child(['unused'],1,pins)

    def test_runtime_manifest_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'runtime.json'; p.write_text('{"backend":"PySAT Glucose3 1.8.dev24"}')
            with self.assertRaises(ValueError): native.runtime_contract(p)

    @unittest.skipUnless(native.RUNTIME_MANIFEST.is_file(), 'Exact pinned native host manifest is absent')
    def test_loaded_backend_origins_and_optional_presence(self):
        import importlib.util
        import pysat.engines
        self.assertEqual(native.runtime_contract(inspect_imports=True)['version'],'1.8.dev24')
        with patch.object(pysat.engines,'__file__','/unexpected/engines.py'):
            with self.assertRaises(ValueError): native.runtime_contract(inspect_imports=True)
        with patch.object(importlib.util,'find_spec',return_value=SimpleNamespace(origin='unexpected')):
            with self.assertRaises(ValueError): native.runtime_contract()

    @unittest.skipUnless(native.RUNTIME_MANIFEST.is_file(), 'Exact pinned native host manifest is absent')
    def test_unknown_native_status_and_exact_cap_are_incomplete(self):
        import pysat.solvers
        with tempfile.TemporaryDirectory() as tmp,tempfile.TemporaryFile() as trace:
            formula=Path(tmp)/'a.cnf'; formula.write_text('p cnf 1 1\n1 0\n'); proof=Path(tmp)/'a.rup'
            for answer in (None,False):
                solver=MagicMock(); solver.__enter__.return_value=solver; solver.solve.return_value=answer
                if answer is False:
                    trace.truncate(native.PROOF_CAP); solver.prfile=trace
                with patch.object(native.resource,'setrlimit'),patch.object(native,'runtime_contract'),\
                     patch.object(pysat.solvers,'Glucose3',return_value=solver):
                    with self.assertRaises(ValueError): native.solver_child(formula,proof,c.digest(formula))
                self.assertEqual(solver.solve.call_count,1); self.assertFalse(proof.exists())

    def test_uncertain_cleanup_is_bounded_and_cannot_accept(self):
        clock=[0.0]; signals=[]; process=SimpleNamespace(pid=999999,poll=lambda:None)
        tracker=SimpleNamespace(inspect=lambda seconds:[(999999,False)],errors=[],seen={999999:('birth',)},
                                signal=lambda sig,seconds:None)
        with patch.object(native.time,'monotonic',side_effect=lambda:clock[0]),\
             patch.object(native.time,'sleep',side_effect=lambda seconds:clock.__setitem__(0,clock[0]+seconds)),\
             patch.object(native.os,'kill',side_effect=lambda pid,sig:signals.append((clock[0],pid,sig))):
            result=native.cleanup(process,tracker)
        self.assertFalse(result['clean']); self.assertLessEqual(result['seconds'],.500001)
        self.assertTrue(any(sig==15 for _,_,sig in signals)); self.assertTrue(any(sig==9 for _,_,sig in signals))
        self.assertTrue(all(at < .1 for at,_,sig in signals if sig==15))
        with self.assertRaises(RuntimeError): gate.child_json({'reason':'exited','returncode':0,'cleanup':result,'stdout':'{}'})

    def test_observer_timeout_classification_and_launch_reserve(self):
        for duration,after,want in ((1,.041,'supervisor_error'),(.02,.021,'timeout')):
            clock=[0.0]; reads=[]; writes=[]
            for _ in range(2):
                r,w=os.pipe(); reads.append(os.fdopen(r,'rb')); writes.append(w)
            process=SimpleNamespace(pid=999999,stdout=reads[0],stderr=reads[1],returncode=-9,poll=lambda:-9)
            def inspect(seconds):
                clock[0]=after; raise TimeoutError('process observer timeout')
            tracker=SimpleNamespace(inspect=inspect,errors=[])
            try:
                with patch.object(native,'verify_pins'),patch.object(native,'snapshot',return_value={}),\
                     patch.object(native.subprocess,'Popen',return_value=process),patch.object(native,'Tracker',return_value=tracker),\
                     patch.object(native,'cleanup',return_value={'clean':True}),patch.object(native.time,'monotonic',side_effect=lambda:clock[0]):
                    result=native.run_child(['tiny'],duration,{'tiny':'pin'})
                self.assertEqual(result['reason'],want)
                self.assertEqual('observer_timeout_at_child_deadline' in result,want=='timeout')
            finally:
                for fd in writes: os.close(fd)
        with patch.object(native,'verify_pins'),patch.object(native,'snapshot',return_value={}),\
             patch.object(native.subprocess,'Popen',side_effect=AssertionError('launched after reserve')),\
             patch.object(native.time,'monotonic',return_value=1):
            with self.assertRaises(TimeoutError): native.run_child(['tiny'],1,{'tiny':'pin'},latest_end=.9)

    def test_reaped_direct_pid_never_authorizes_signalling(self):
        process=SimpleNamespace(pid=999999,returncode=0,poll=lambda:0)
        tracker=native.Tracker(process,{})
        row=(os.getpid(),os.getpgrp(),('same','second','birth','is','insufficient'),'S')
        with patch.object(native,'snapshot',return_value={process.pid:row}),patch.object(native.os,'kill',side_effect=AssertionError('unsafe signal')):
            tracker.signal(15,.02)
        self.assertFalse(tracker.seen); self.assertTrue(tracker.errors)

    def test_late_second_validator_saves_before_root(self):
        # A synthetic scaffold passes real direct geometry/axis invariants. Only
        # validation timing is stubbed, to cross deadline exactly in validator2.
        A={(0,0),(1,1),(2,2)}; S=A|{(3,3)}
        args=make_inputs(A,[(0,1)]); A,pool,arcs,tables,conflicts=args
        report={'seed_count':1,'cnf':{'sha256':'tiny'},'counters':gate.old.new_counters()}
        expired=[False]
        def check():
            if expired[0]: raise TimeoutError()
        def dual(P,n,check):
            check(); expired[0]=True
            return {'n':n,'points':sorted(P)},[{'normalized_sha256':'tiny'}]*2
        with tempfile.TemporaryDirectory() as tmp,patch.object(gate.frozen,'dual_valid',dual),patch.object(gate.native,'verify_pins'):
            decoded=gate.save_scaffold(4,A,S,pool,arcs,tables,conflicts,(0,),Path(tmp),report,check,{'tiny':'pin'})
            self.assertTrue((Path(tmp)/'valid149-diagnostic.json').is_file())
            with patch.object(gate.old,'residual_domains',side_effect=AssertionError('root started')):
                with self.assertRaises(TimeoutError): gate.optional_root(4,A,S,decoded,Path(tmp),report,check,{'tiny':'pin'})
            self.assertNotIn('root',report)


class NativeTinyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not native.RUNTIME_MANIFEST.is_file():
            raise unittest.SkipTest('Exact pinned native host manifest is absent; native host tests require it')
        cls.pins=json.loads((ROOT/'data/fixed-pool-boolean-scaffold-runtime-pins.json').read_text())['pins']
        for name in ('boolean_scaffold_native.py','bounded_rup_checker.py','boolean_scaffold_native_tiny_fixture.py'):
            p=ROOT/'research'/name; cls.pins[str(p)]=c.digest(p)

    def run_fixture(self, mode, seconds=2, extra=()):
        command=[sys.executable,str(ROOT/'research/boolean_scaffold_native_tiny_fixture.py'),mode,*map(str,extra)]
        result=native.run_child(command,seconds,self.pins); EVIDENCE.append({'fixture':mode,**result}); return result

    def test_identity_caps_timeout_fork(self):
        identity=self.run_fixture('identity'); self.assertEqual(identity['reason'],'exited'); self.assertTrue(identity['cleanup']['clean'])
        obj=json.loads(identity['stdout']); self.assertEqual((obj['pgid'],obj['sid']),(os.getpgrp(),os.getsid(0)))
        for mode in ('stdout','stderr'):
            result=self.run_fixture(mode); self.assertEqual(result['reason'],mode+'_cap'); self.assertTrue(result['cleanup']['clean'])
            self.assertEqual(len(result[mode]),65536)
        for mode in ('sleep','fork'):
            result=self.run_fixture(mode,.25); self.assertEqual(result['reason'],'timeout'); self.assertTrue(result['cleanup']['clean'],result)
            self.assertLess(result['cleanup']['seconds'],.5)
        self.assertGreaterEqual(len(result['cleanup']['observed_pids']),2)

    def test_kernel_native_file_caps_and_fork_inheritance(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('cap','fork_cap','exact_cap','partial_cap'):
                result=self.run_fixture(mode,2,('--path',Path(tmp)/mode)); self.assertEqual(result['reason'],'exited'); self.assertTrue(result['cleanup']['clean'])
                obj=json.loads(result['stdout']); self.assertEqual(obj['bytes'],native.PROOF_CAP); self.assertEqual(obj['limit'],[native.PROOF_CAP]*2)
                self.assertTrue(obj['cap_reached_is_incomplete'])
                if mode=='partial_cap': self.assertEqual(obj['partial'],16)

    def test_real_tiny_sat_unsat_and_independent_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            for label,body in [('sat','p cnf 2 2\n1 2 0\n-1 2 0\n'),('unsat','p cnf 3 8\n'+''.join(' '.join(map(str,row))+' 0\n' for row in product(*[(i,-i) for i in range(1,4)])))]:
                formula=tmp/(label+'.cnf'); formula.write_text(body); proof=tmp/(label+'.rup')
                command=[sys.executable,str(ROOT/'research/boolean_scaffold_native.py'),'--cnf',str(formula),'--proof',str(proof),'--cnf-sha256',c.digest(formula)]
                result=native.run_child(command,3,self.pins); EVIDENCE.append({'fixture':label,**result})
                obj=gate.child_json(result); self.assertEqual(obj['answer'],label.upper())
                if label=='sat': c.parse_model(obj['model'],2)
                else:
                    command=[sys.executable,str(ROOT/'research/bounded_rup_checker.py'),'--cnf',str(formula),'--proof',str(proof),'--cnf-sha256',c.digest(formula),'--proof-sha256',c.digest(proof),'--seconds','2']
                    result=native.run_child(command,2,self.pins); EVIDENCE.append({'fixture':'checker',**result})
                    self.assertTrue(gate.child_json(result)['accepted'])
                    EVIDENCE.append({'fixture':'proof_binding','cnf_sha256':c.digest(formula),'proof_sha256':c.digest(proof),'proof':proof.read_text()})


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    # Keep cap evidence bounded in the artifact as well as during capture.
    for entry in EVIDENCE:
        for stream in ('stdout','stderr'):
            if stream in entry and len(entry[stream])>2048:
                raw=entry.pop(stream); entry[stream+'_bytes']=len(raw); entry[stream+'_sha256']=hashlib.sha256(raw.encode()).hexdigest()
    path=ROOT/'data/fixed-pool-boolean-scaffold-author-tiny.json'
    path.write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'evidence':EVIDENCE},indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
