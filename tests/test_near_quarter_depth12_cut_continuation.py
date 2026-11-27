from contextlib import ExitStack, contextmanager
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from research import near_quarter_depth12_cut_continuation as m
from research.seeded_cut_boolean_oracle import fixture


class SeedTests(unittest.TestCase):
    def synthetic(self):
        triples=list(combinations(range(1,80),3))[:181]
        seed={'selected_prefix_ids':list(m.EXPECTED_IDS[:13]),'orbit_variable_ids':list(range(1,370)),
              'pair_cut_ids':[list(c) for c in list(combinations(range(1,370),2))[:9539]],
              'triple_cut_ids':[list(c) for c in triples],
              'triple_cut_records':[{'ids':list(c),'points':[[v-1,0] for v in c]} for c in triples]}
        state=SimpleNamespace(map_digest=bytes.fromhex(m.MAP_HASH),points=(),model={'orbits':tuple(((i%79,0),) for i in range(369))})
        return seed,state

    def test_pinned_predecessor_loading_and_immutability(self):
        before={p:hashlib.sha256((m.ROOT/p).read_bytes()).hexdigest() for p in m.INPUT_PINS}
        seed=m.load_seed(lambda:None)
        self.assertEqual((len(seed['pair_cut_ids']),len(seed['triple_cut_records'])),(9539,181))
        self.assertEqual(before,m.INPUT_PINS)
        self.assertEqual(before,{p:hashlib.sha256((m.ROOT/p).read_bytes()).hexdigest() for p in before})

    def test_changed_report_and_audit_rejected(self):
        for path in (m.PARENT_REPORT,m.PARENT_AUDIT,m.PARENT_RECEIPT):
            pins={**m.INPUT_PINS,path:'0'*64}
            with patch.object(m,'INPUT_PINS',pins),self.assertRaisesRegex(ValueError,'hash mismatch'):
                m.load_seed(lambda:None)

    def test_seeded_ids_geometry_and_identity(self):
        seed,state=self.synthetic()
        self.assertEqual(len(m.validate_seed(seed,state,seed['orbit_variable_ids'],m.MASK_HASH,lambda:None)),9539)
        for mutation,message in (
            (lambda s:s['selected_prefix_ids'].reverse(),'map mismatch'),
            (lambda s:s['orbit_variable_ids'].reverse(),'map mismatch'),
            (lambda s:s['pair_cut_ids'].__setitem__(1,s['pair_cut_ids'][0]),'binary'),
            (lambda s:s['pair_cut_ids'].__setitem__(0,[1,True]),'binary'),
            (lambda s:s['triple_cut_ids'].__setitem__(1,s['triple_cut_ids'][0]),'duplicate'),
            (lambda s:s['triple_cut_records'][0]['points'].__setitem__(2,[2,1]),'collinear'),
            (lambda s:s['triple_cut_records'][0]['points'].__setitem__(2,[3,0]),'membership'),
            (lambda s:s['triple_cut_records'][0]['points'].__setitem__(2,[2,True]),'points')):
            changed=deepcopy(seed);mutation(changed)
            with self.assertRaisesRegex(ValueError,message):m.validate_seed(changed,state,seed['orbit_variable_ids'],m.MASK_HASH,lambda:None)
        with self.assertRaisesRegex(ValueError,'map mismatch'):
            m.validate_seed(seed,state,seed['orbit_variable_ids'],'changed',lambda:None)
        state.map_digest=b'0'*32
        with self.assertRaisesRegex(ValueError,'map mismatch'):
            m.validate_seed(seed,state,seed['orbit_variable_ids'],m.MASK_HASH,lambda:None)


class LoopTests(unittest.TestCase):
    def report(self,seed=True):
        ids=[[1,2,3]] if seed else []
        return {'status':'incomplete','complete':False,'model_count':0,'witnesses':0,'degree_clauses':0,'degree_literals':0,
                'pair_cuts':0,'pair_cut_ids':[],'retained_triple_cuts':len(ids),'new_triple_cuts':0,'triple_cuts':len(ids),
                'triple_cut_ids':ids,'triple_cut_records':[{'ids':[1,2,3],'points':[[0,0],[1,0],[2,0]]}] if seed else []}

    def run_loop(self,models,report,cap=1000,answer=False,fired=None,clock=lambda:0,check=lambda:None,out=None):
        class Solver:
            def __init__(self):self.models=iter(models);self.added=[];self.current=None;self.calls=0
            def solve_limited(self,**kw):
                self.calls+=1
                self.current=next(self.models,None)
                return answer if self.current is None else True
            def get_model(self):return self.current
            def add_clause(self,c):self.added.append(c)
        points=fixture()['point_by_local_variable']
        state=SimpleNamespace(n=5,points=(),model={'orbits':tuple((tuple(p),) for p in points)})
        solver=Solver()
        with tempfile.TemporaryDirectory() as tmp:
            m.solve_models(solver,state,[1,2,3,4,5],[3,3],[(0,1)]*5,report,check,fired or threading.Event(),1,clock,Path(out or tmp),target_points=3,target_orbits=3,cut_limit=cap)
        return solver

    def test_boolean_oracle_and_total_remaining_budget(self):
        oracle=fixture()
        for cap in (1,2,4):
            r=self.report();solver=self.run_loop(oracle['new_cut_sequence'],r,cap)
            self.assertEqual((r['retained_triple_cuts'],r['new_triple_cuts'],r['triple_cuts']),(1,cap-1,cap))
            self.assertEqual(r['triple_cut_ids'],oracle['stages'][cap-1]['cut_ids'])
            self.assertEqual(solver.added,[[-v for v in c] for c in oracle['new_cut_sequence'][:cap-1]])
            self.assertEqual(r['status'],'cut_limit')
            self.assertEqual(r.get('final_literals',3),3*cap)
        self.assertEqual(1000-181,819)

    def test_seed_and_new_cut_model_violations_fail(self):
        for models in ([[1,2,3]],[[1,2,4],[1,2,4]]):
            with self.assertRaisesRegex(RuntimeError,'repeated excluded'):
                self.run_loop(models,self.report())
        r=self.report();r['pair_cut_ids']=[[1,2]]
        with self.assertRaisesRegex(RuntimeError,'binary cut'):self.run_loop([[1,2,4]],r)
        r=self.report();r['triple_cut_ids'].append([1,2,3]);r['triple_cuts']=2
        with self.assertRaisesRegex(ValueError,'seeded total'):self.run_loop([],r)

    def test_native_answers_deadline_and_timers(self):
        for answer,status in ((False,'unsat_solver_reported'),(None,'solver_unknown')):
            r=self.report();self.run_loop([],r,answer=answer);self.assertEqual(r['status'],status)
        fired=threading.Event();fired.set()
        with self.assertRaises(TimeoutError):self.run_loop([],self.report(),fired=fired)
        with self.assertRaises(TimeoutError):self.run_loop([],self.report(),clock=lambda:1)
        events=[]
        class Timer:
            def cancel(self):events.append('cancel')
            def join(self):events.append('join')
        class Solver:
            def delete(self):events.append('delete')
        m.dispose_solver(Timer(),Solver());self.assertEqual(events,['cancel','join','delete'])

    def test_late_witness_and_dual_failure(self):
        good={'valid':True,'point_count':3,'normalized_sha256':'tiny'};expired=[False]
        def check():
            if expired[0]:raise TimeoutError
        def second(cert):expired[0]=True;return good
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate',return_value=good),patch.object(m,'verify_certificate_bruteforce',side_effect=second):
            r=self.report();self.run_loop([[1,2,5]],r,check=check,out=tmp)
            self.assertTrue((Path(tmp)/'witness-tiny.json').exists());self.assertEqual(r['status'],'witness')
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate',return_value=good),patch.object(m,'verify_certificate_bruteforce',return_value={**good,'valid':False}):
            with self.assertRaisesRegex(RuntimeError,'dual verification'):self.run_loop([[1,2,5]],self.report(),out=tmp)
            self.assertEqual(list(Path(tmp).iterdir()),[])


class AdapterTests(unittest.TestCase):
    @contextmanager
    def fake_run(self,status='unsat_solver_reported',timeout_depth=None):
        tick=[0];events=[];stages=[];states=[];deadlines=[]
        class State:
            def __init__(self,n,check):self.ids=[];states.append(self)
            def push(self,v):self.ids.append(v);return True
            @property
            def points(self):return [(i,0) for i in range(2+4*(len(self.ids)-1))]
        class Solver:
            def __init__(self,**kw):self.clauses=[];events.append(self)
            def add_clause(self,c):self.clauses.append(c)
            def delete(self):events.append('delete')
            def interrupt(self):pass
        class Timer:
            def __init__(self,remaining,callback):events.append(('timer',remaining))
            def start(self):pass
            def cancel(self):events.append('cancel')
            def join(self):events.append('join')
        def sample(n,ids,check):
            d=len(ids)-1
            if d==timeout_depth:raise TimeoutError
            return {'mask':[1]*369+[0]*(1521-369),'mask_sha256':m.MASK_HASH,'demands':[2]*(39-d),'edges':[(0,1)]*369}
        def pairs(state,variables,check,stage):
            self.assertNotEqual(stage['depth'],12);stage['pair_started']=stage['pair_completed']=67896
            return [(1,3)]
        def solve(solver,state,variables,demands,edges,stage,check,fired,deadline,clock,out,**kw):
            stages.append(deepcopy(stage));deadlines.append(deadline)
            self.assertEqual(kw,{'target_orbits':39-stage['depth'],'cut_limit':1000})
            stage['status']=status;stage['complete']=status in ('witness','unsat_solver_reported');tick[0]+=1
        seed={'triple_cut_ids':[[1,2,3]]*181,'triple_cut_records':[{'ids':[1,2,3],'points':[[0,0],[1,0],[2,0]]}]*181}
        with ExitStack() as stack:
            for name,value in [('PackedOrbitState',State),('mask_and_bounds',sample),('incompatible_pairs',pairs),('solve_models',solve),('Timer',Timer),('source_manifest',lambda:{}),('load_seed',lambda check:seed),('validate_seed',lambda *a:[(1,2)]*9539),('degree_clauses',lambda *a:([[1,2]]*3192+[[1,2,3]]*1810,SimpleNamespace(top=2823)))]:
                stack.enter_context(patch.object(m,name,value))
            stack.enter_context(patch('pysat.solvers.Solver',Solver))
            yield SimpleNamespace(tick=tick,events=events,stages=stages,states=states,deadlines=deadlines,seed=seed)

    def test_three_stages_shared_deadline_seeded_then_fresh(self):
        with self.fake_run() as f,tempfile.TemporaryDirectory() as tmp:
            before=deepcopy(f.seed);r=m.run(Path(tmp),25,clock=lambda:f.tick[0]);self.assertEqual(before,f.seed)
        self.assertEqual([s['depth'] for s in f.stages],[12,11,10]);self.assertEqual(f.deadlines,[25]*3)
        self.assertEqual([s['retained_triple_cuts'] for s in f.stages],[181,0,0])
        self.assertEqual([s['triple_cuts'] for s in f.stages],[181,0,0])
        self.assertEqual([s['pair_completed'] for s in f.stages],[0,67896,67896])
        self.assertEqual(len(f.states),3);self.assertEqual(len(set(map(id,f.states))),3)
        self.assertEqual([e for e in f.events if isinstance(e,tuple)],[('timer',25),('timer',24),('timer',23)])
        self.assertEqual([e for e in f.events if isinstance(e,str)],['cancel','join','delete']*3)
        self.assertEqual(r['stages'][0]['final_clauses'],14722);self.assertEqual(r['stages'][0]['final_literals'],31435)
        self.assertEqual(r['status'],'all_ancestors_unsat_solver_reported')

    def test_unsat_only_advancement_and_timeout_preserves_completed(self):
        for status in ('solver_unknown','cut_limit','mask_capacity','degree_shortfall','witness','timeout'):
            with self.fake_run(status) as f,tempfile.TemporaryDirectory() as tmp:
                r=m.run(Path(tmp),25,clock=lambda:f.tick[0])
            self.assertEqual([s['depth'] for s in f.stages],[12]);self.assertEqual(r['stages'][1]['status'],'unstarted')
        with self.fake_run(timeout_depth=11) as f,tempfile.TemporaryDirectory() as tmp:
            r=m.run(Path(tmp),25,clock=lambda:f.tick[0])
        self.assertEqual(r['stages'][0]['status'],'unsat_solver_reported');self.assertEqual(r['status'],'timeout')

    def test_fixed_scope_and_capacity(self):
        self.assertEqual(m.DEPTHS,(12,11,10));self.assertEqual(m.capacity_bounds(480)['pair_census'],114960)
        for depth in (14,13,9):
            with self.assertRaises(ValueError):m.prefix_for_depth(m.EXPECTED_IDS,depth)
        self.assertIsNone(m.bounded_variables([1]*481))
        with self.assertRaises(ValueError):m.bounded_variables([True])
        self.assertEqual([39-d for d in m.DEPTHS],[27,28,29])


if __name__=='__main__':unittest.main()
