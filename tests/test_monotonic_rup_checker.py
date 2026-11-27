"""Synthetic and exhaustive tiny checks only; never read the saved actual pair."""
from collections import deque
from dataclasses import replace
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import platform
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from research import monotonic_rup_checker as m
from research import saved_boolean_proof_check as runner
EVIDENCE=[]


def literal_up(formula, candidate):
    """Independent signed-set simplification with a unit agenda."""
    clauses={frozenset(c) for c in formula if not any(-v in c for v in c)}
    agenda=deque(-v for v in candidate); assigned=set()
    agenda.extend(next(iter(c)) for c in clauses if len(c)==1)
    if frozenset() in clauses: return True
    while agenda:
        v=agenda.popleft()
        if -v in assigned: return True
        if v in assigned: continue
        assigned.add(v); simplified=set()
        for c in clauses:
            if v in c: continue
            smaller=c-{-v}
            if not smaller: return True
            simplified.add(smaller)
            if len(smaller)==1: agenda.append(next(iter(smaller)))
        clauses=simplified
    return False


def mask(clause):
    return (sum(1 << (v-1) for v in set(clause) if v>0),
            sum(1 << (-v-1) for v in set(clause) if v<0))


def encoded(formula):
    return [(*mask(c),len(c)) for c in formula]


def models(formula,n):
    return [bits for bits in product((False,True),repeat=n)
            if all(any(bits[abs(v)-1]==(v>0) for v in clause) for clause in formula)]


class PropagationTests(unittest.TestCase):
    def test_exhaustive_two_variable_formulas_and_three_variable_pairs(self):
        comparisons=entailed=0
        for n in (1,2,3):
            clauses=[tuple((i+1)*v for i,v in enumerate(states) if v)
                     for states in product((0,1,-1),repeat=n)]
            formulae=([tuple(clauses[i] for i,b in enumerate(bits) if b)
                       for bits in product((False,True),repeat=len(clauses))] if n<=2
                      else [f for width in range(3) for f in combinations(clauses,width)])
            for formula in formulae:
                satisfying=models(formula,n)
                for candidate in clauses:
                    got=m.rup(encoded(formula),mask(candidate),m.Budget())
                    self.assertEqual(got,literal_up(formula,candidate))
                    if got:
                        self.assertTrue(all(any(bits[abs(v)-1]==(v>0) for v in candidate) for bits in satisfying))
                        entailed+=1
                    comparisons+=1
        self.assertGreater(comparisons,14000); self.assertGreater(entailed,1000)

    def test_opposite_signs_tautologies_duplicates_and_chains(self):
        cases=[([(1,-1)],(1,),False), ([(1,1)],(1,),True),
               ([(1,)],(1,-1),True), ([(1,),(-1,)],(),True),
               ([(1,),(-1,2),(-2,3),(-3,)],(),True),
               ([(-1,2),(2,)],(1,),False)]
        for formula,candidate,want in cases:
            self.assertEqual(m.rup(encoded(formula),mask(candidate),m.Budget()),want)
            self.assertEqual(literal_up(formula,candidate),want)
        self.assertTrue(models([(-1,2),(2,)],2))  # RAT-only p is not entailed.


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.cnf=Path(self.temp.name)/'tiny.cnf'; self.proof=Path(self.temp.name)/'tiny.rup'

    def check(self,formula,proof,*,variables=3,limits=None,**kwargs):
        self.cnf.write_text('p cnf %d %d\n'%(variables,len(formula))+''.join(
            ' '.join(map(str,c))+(' ' if c else '')+'0\n' for c in formula))
        self.proof.write_bytes(proof if isinstance(proof,bytes) else proof.encode())
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        return m.check_pair(self.cnf,self.proof,sha(self.cnf),sha(self.proof),
                            limits=limits or m.Limits(),**kwargs)

    def test_deleted_reason_retained_and_multiset_deletions_exact(self):
        formula=[(1,),(-1,2),(-2,)]
        self.assertFalse(literal_up([(1,),(-2,)],()))
        result=self.check(formula,'d -1 2 0\n0\n')
        self.assertTrue(result['accepted']); self.assertEqual(result['checked_empty_line'],2)
        self.assertEqual(result['retained_clauses'],4); self.assertEqual(result['retained_literals'],4)
        result=self.check([(1,),(1,),(-1,)],'d 1 0\nd 1 0\n0\n')
        self.assertTrue(result['accepted']); self.assertEqual(result['deletions'],2)
        bad=self.check([(1,),(1,),(-1,)],'d 1 0\nd 1 0\nd 1 0\n0\n')
        self.assertFalse(bad['accepted']); self.assertEqual(bad['failure_line'],3); self.assertEqual(bad['failure_clause'],[1])

    def test_unjustified_candidate_is_not_inserted_rat_and_cube_rejected(self):
        for formula,candidate in [([(1,)],(2,)),([(-1,2),(2,)],(1,))]:
            result=self.check(formula,' '.join(map(str,candidate))+' 0\n0\n')
            self.assertFalse(result['accepted']); self.assertEqual(result['failure_line'],1)
            self.assertEqual(result['failure_clause'],list(candidate)); self.assertEqual(result['additions'],0)
        cube=list(product(*[(i,-i) for i in range(1,4)]))
        self.assertFalse(models(cube,3)); self.assertFalse(self.check(cube,'0\n')['accepted'])
        checked=self.check(cube,'2 3 0\n3 0\n1 0\n0\n')
        self.assertTrue(checked['accepted']); self.assertEqual(checked['additions'],4)

    def test_every_record_after_empty_and_first_failure_line(self):
        formula=[(1,),(-1,)]
        for proof,line in [('0\nd 2 0\n',2),('0\nx 0\n',2),('0\n2 0',2),('0\n\xff\n',2)]:
            raw=proof.encode('latin-1'); result=self.check(formula,raw)
            self.assertFalse(result['accepted']); self.assertFalse(result['closure']); self.assertEqual(result['failure_line'],line)
        self.assertTrue(self.check(formula,'0\nd 1 0\n')['accepted'])
        result=self.check(formula,'1 0\n'); self.assertFalse(result['accepted'])
        self.assertTrue(result['full_parse_complete']); self.assertIsNone(result['checked_empty_line'])

    def test_digest_and_byte_record_storage_caps(self):
        formula=[(1,),(-1,)]
        for limits in [replace(m.Limits(),work=0),replace(m.Limits(),proof_records=0),
                       replace(m.Limits(),retained_clauses=2),replace(m.Limits(),proof_bytes=1),
                       replace(m.Limits(),cnf_bytes=1)]:
            result=self.check(formula,'0\n',limits=limits)
            self.assertFalse(result['accepted']); self.assertFalse(result['closure'])
        result=self.check(formula,'1 1 0\n0\n',limits=replace(m.Limits(),retained_literals=3))
        self.assertFalse(result['accepted']); self.assertEqual(result['failure_line'],1)
        self.assertTrue(self.check(formula,'0\n',limits=replace(m.Limits(),proof_bytes=2))['accepted'])
        # Both digest checks are independent of a syntactically valid empty step.
        self.check(formula,'0\n')
        result=m.check_pair(self.cnf,self.proof,'0'*64,hashlib.sha256(self.proof.read_bytes()).hexdigest())
        self.assertFalse(result['accepted']); self.assertIn('digest mismatch',result['error'])

    def test_parser_domains_headers_and_raw_duplicate_accounting(self):
        for proof in ('4 0\n','0 0\n','+1 0\n','--1 0\n','1\n','d\n','\n'):
            self.assertFalse(self.check([(1,),(-1,)],proof)['accepted'])
        self.assertTrue(self.check([(1,1),(-1,-1)],'0\n')['accepted'])
        result=self.check([(1,-1)],'1 0\n0\n')
        self.assertFalse(result['accepted']); self.assertEqual(result['failure_line'],1)
        self.assertFalse(self.check([(1,),(-1,)],b'x'*20000+b'\n')['accepted'])
        self.check([(1,),(-1,)],'0\n')
        self.cnf.write_text('p cnf 3 3\n1 0\n-1 0\n')
        result=m.check_pair(self.cnf,self.proof,hashlib.sha256(self.cnf.read_bytes()).hexdigest(),hashlib.sha256(self.proof.read_bytes()).hexdigest())
        self.assertFalse(result['accepted']); self.assertIn('count mismatch',result['error'])

    def test_parse_digest_catches_mutation_after_preflight(self):
        self.check([(1,),(-1,)],'0\n1 0\n')
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        cnf_sha,proof_sha=sha(self.cnf),sha(self.proof); original=m.hash_file
        def mutate(path,cap,budget):
            result=original(path,cap,budget)
            if Path(path)==self.proof: self.proof.write_text('0\n2 0\n')
            return result
        with patch.object(m,'hash_file',mutate):
            result=m.check_pair(self.cnf,self.proof,cnf_sha,proof_sha)
        self.assertFalse(result['accepted']); self.assertIn('proof parse digest mismatch',result['error'])

    def test_deadline_and_work_checks(self):
        with self.assertRaises(TimeoutError): m.rup(encoded([(1,)]),mask((1,)),m.Budget(work=0))
        clock=[0.0]
        def advance(): clock[0]+=.1; return clock[0]
        result=self.check([(1,),(-1,)],'0\n',seconds=.01,started=0,clock=advance)
        self.assertFalse(result['accepted']); self.assertEqual(result['status'],'timeout')
        with self.assertRaises(ValueError): m.Limits(retained_clauses=13295)


class RunnerTests(unittest.TestCase):
    def report(self): return {'checker_invocations':0,'sat_invocations':0,'complete':False,'closure':False}

    def response(self,accepted=True):
        receipt={'accepted':accepted,'closure':accepted,'full_parse_complete':accepted,
                 'checked_empty_line':3 if accepted else None,'cnf_sha256':'cnf','proof_sha256':'proof',
                 'status':'checked_monotonic_rup_unsat' if accepted else 'rejected',
                 'failure_line':None if accepted else 2,'failure_clause':None if accepted else [1],
                 'error':None if accepted else 'non-RUP addition'}
        return {'reason':'exited','returncode':0 if accepted else 2,'cleanup':{'clean':True},'stdout':json.dumps(receipt)}

    def test_one_child_acceptance_rejection_and_cleanup_binding(self):
        for mode in ('accepted','rejected','uncertain','outputcap','mismatched_hash'):
            response=self.response(mode!='rejected')
            if mode=='uncertain': response['cleanup']['clean']=False
            if mode=='outputcap': response['reason']='stdout_cap'
            if mode=='mismatched_hash':
                r=json.loads(response['stdout']); r['proof_sha256']='different'; response['stdout']=json.dumps(r)
            report=self.report()
            with patch.object(runner.native,'verify_pins'),patch.object(runner.native,'run_child',return_value=response) as child:
                if mode=='mismatched_hash':
                    with self.assertRaises(ValueError): runner.execute('tiny.cnf','tiny.rup','cnf','proof',{'tiny':'pin'},report,25,lambda:None,clock=lambda:0)
                else: runner.execute('tiny.cnf','tiny.rup','cnf','proof',{'tiny':'pin'},report,25,lambda:None,clock=lambda:0)
            self.assertEqual(child.call_count,1); self.assertEqual(child.call_args.args[1],5)
            self.assertEqual(child.call_args.kwargs['latest_end'],24)
            self.assertEqual(report['closure'],mode=='accepted'); self.assertEqual(report['sat_invocations'],0)
            if mode=='rejected': self.assertEqual(report['proof_check']['failure_line'],2)

    def test_no_slice_prohibits_child_and_pin_changes_reject(self):
        report=self.report()
        with patch.object(runner.native,'verify_pins'),patch.object(runner.native,'run_child',side_effect=AssertionError('launched')):
            with self.assertRaises(TimeoutError): runner.execute('tiny.cnf','tiny.rup','cnf','proof',{'tiny':'pin'},report,1,lambda:None,clock=lambda:0)
        self.assertEqual(report['checker_invocations'],0)
        with patch.object(runner.native,'verify_pins',side_effect=ValueError('pin changed')):
            with self.assertRaises(ValueError): runner.execute('tiny.cnf','tiny.rup','cnf','proof',{'tiny':'pin'},self.report(),25,lambda:None,clock=lambda:0)


@unittest.skipUnless(runner.native.RUNTIME_MANIFEST.is_file(),'Exact pinned host runtime manifest is absent')
class NativeTinyTests(unittest.TestCase):
    def test_only_synthetic_pair_in_one_checker_child(self):
        pins=dict(runner.native.runtime_contract()['pins'])
        for path in (Path(m.__file__).resolve(),Path(runner.__file__).resolve(),Path(runner.native.__file__).resolve()):
            pins[str(path)]=runner.native.digest(path)
        for label,clauses,proof in [('accepted',[(1,),(-1,2),(-2,)],'d -1 2 0\n0\n'),
                                    ('rejected',[(1,)],'0\n')]:
            with tempfile.TemporaryDirectory() as tmp:
                tmp=Path(tmp); cnf=tmp/'synthetic.cnf'; trace=tmp/'synthetic.rup'
                cnf.write_text('p cnf 2 %d\n'%len(clauses)+''.join(' '.join(map(str,c))+' 0\n' for c in clauses)); trace.write_text(proof)
                report={'checker_invocations':0,'sat_invocations':0,'complete':False,'closure':False}
                deadline=time.monotonic()+25
                runner.execute(cnf,trace,runner.native.digest(cnf),runner.native.digest(trace),pins,report,deadline,lambda:None)
                self.assertEqual(report['checker_invocations'],1); self.assertEqual(report['sat_invocations'],0)
                self.assertEqual(report['closure'],label=='accepted'); self.assertTrue(report['checker_process']['cleanup']['clean'])
                if label=='rejected': self.assertEqual(report['proof_check']['failure_line'],1)
                EVIDENCE.append({'fixture':label,'formula':clauses,'proof':proof,'report':report})


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    root=Path(__file__).resolve().parents[1]
    pins={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
          (Path(m.__file__).resolve(),Path(runner.__file__).resolve(),Path(__file__).resolve())}
    (root/'data/monotonic-rup-author-tiny.json').write_text(json.dumps({'passed':result.wasSuccessful(),
        'tests':result.testsRun,'skipped':len(result.skipped),'source_pins':pins,'platform':platform.platform(),
        'command':['.venv/bin/python','-m','tests.test_monotonic_rup_checker'],'evidence':EVIDENCE,
        'scope':'Synthetic tiny pairs only; saved Boolean proof was never read or replayed.'},indent=2,sort_keys=True)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
