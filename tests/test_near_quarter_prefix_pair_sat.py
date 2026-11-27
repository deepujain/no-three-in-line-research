import itertools
import unittest
from collections import Counter
from research import near_quarter_prefix_pair_sat as m
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_readonly_probe import probe_orbit
from src.verify import verify_certificate_bruteforce
from pysat.solvers import Solver


class PrefixPairTests(unittest.TestCase):
    def test_pairs_against_det_and_restoration(self):
        for n in (5,7):
            state=PackedOrbitState(n);diag=state.bounds['four']+1
            self.assertTrue(state.push(diag));before=state.snapshot()
            variables=[i for i in range(1,state.bounds['four']+1) if probe_orbit(state,i)]
            counts={'pair_started':0,'pair_completed':0}
            actual=set(m.incompatible_pairs(state,variables,lambda:None,counts))
            expected=set()
            for i,j in itertools.combinations(range(len(variables)),2):
                pts=list(state.points)+list(state.model['orbits'][variables[i]-1])+list(state.model['orbits'][variables[j]-1])
                report=verify_certificate_bruteforce({'n':n,'points':[list(p) for p in pts]})
                axis=all(v<=2 for v in Counter(x for x,y in pts).values()) and all(v<=2 for v in Counter(y for x,y in pts).values())
                if not report['valid'] or not axis: expected.add((i+1,j+1))
            self.assertEqual(actual,expected)
            self.assertEqual(counts['pair_completed'],len(variables)*(len(variables)-1)//2)
            self.assertEqual(state.snapshot(),before)

    def test_interrupted_pair_restores_state(self):
        state=PackedOrbitState(7);state.push(state.bounds['four']+1)
        variables=[i for i in range(1,state.bounds['four']+1) if probe_orbit(state,i)]
        before=state.snapshot();count=[0]
        def check():
            count[0]+=1
            if count[0]==20: raise TimeoutError
        with self.assertRaises(TimeoutError): m.incompatible_pairs(state,variables,check,{'pair_started':0,'pair_completed':0})
        self.assertEqual(state.snapshot(),before)

    def test_degree_projection_all_tiny_models(self):
        edges=[(0,1),(0,1),(1,2),(0,2)]
        for demands in itertools.product(range(3),repeat=3):
            if any(sum(v in e for e in edges)<d for v,d in enumerate(demands)):continue
            clauses,pool=m.degree_clauses(demands,edges,lambda:None)
            with Solver(name='glucose3',bootstrap_with=clauses) as solver:
                for bits in itertools.product((0,1),repeat=len(edges)):
                    degree=[sum(bit for bit,e in zip(bits,edges) if v in e) for v in range(3)]
                    assumptions=[i+1 if bit else -(i+1) for i,bit in enumerate(bits)]
                    self.assertEqual(solver.solve(assumptions=assumptions),degree==list(demands))

    def test_three_orbit_mapping_and_determinants(self):
        pts={(0,0),(1,1),(2,2),(0,1)}
        bad=m.first_bad_triple(pts,lambda:None)
        self.assertEqual(set(bad),{(0,0),(1,1),(2,2)})
        self.assertEqual(m.triple_cut(bad,{(0,0):3,(1,1):2,(2,2):1}),(1,2,3))
        with self.assertRaises(RuntimeError): m.triple_cut(bad,{(0,0):1,(1,1):1})
        self.assertIsNone(m.first_bad_triple({(0,0),(1,2),(2,1)},lambda:None))


if __name__=='__main__':unittest.main()

class SolveLoopTests(unittest.TestCase):
    def _context(self):
        import threading
        class State:
            n=3;points=();model={'orbits':(((0,0),),((1,1),),((2,2),))}
        class Solver:
            def __init__(self,answer=True): self.answer=answer;self.added=[]
            def solve_limited(self,**kwargs): return self.answer
            def get_model(self): return [1,2,3]
            def add_clause(self,c): self.added.append(c)
        report={'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        return State(),Solver(),report,threading.Event()

    def test_complete_loop_enforces_cut_limit(self):
        from pathlib import Path
        import tempfile
        state,solver,report,fired=self._context()
        with tempfile.TemporaryDirectory() as tmp:
            m.solve_models(solver,state,[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)],report,lambda:None,fired,1,lambda:0,Path(tmp),target_points=3,target_orbits=3,cut_limit=1)
        self.assertEqual(report['status'],'cut_limit');self.assertFalse(report['complete'])
        self.assertEqual(report['triple_cuts'],1);self.assertEqual(solver.added,[[-1,-2,-3]])

    def test_timer_race_false_is_unknown(self):
        from pathlib import Path
        import tempfile
        state,solver,report,fired=self._context()
        fired.set();solver.answer=False
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(TimeoutError):
            m.solve_models(solver,state,[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)],report,lambda:None,fired,1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
        self.assertFalse(report['complete']);self.assertEqual(report['status'],'incomplete')

    def test_real_pinned_prefix_extraction_without_geometry(self):
        import hashlib
        paths,pins=m.prefix_paths(lambda:None)
        main=[ids for label,depth,ids in paths if label=='main' and depth==19]
        self.assertEqual(main,[m.EXPECTED_IDS])
        for path,digest in pins:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest)

class SolveFailureTests(unittest.TestCase):
    def test_unsat_unknown_and_repeat(self):
        import tempfile,threading
        from pathlib import Path
        class State:
            n=3;points=();model={'orbits':(((0,0),),((1,1),),((2,2),))}
        class Solver:
            def __init__(self,answer): self.answer=answer;self.cuts=[]
            def solve_limited(self,**kwargs): return self.answer
            def get_model(self): return [1,2,3]
            def add_clause(self,c): self.cuts.append(c)
        def report():return {'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        with tempfile.TemporaryDirectory() as tmp:
            args=(State(),[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)])
            r=report();m.solve_models(Solver(False),*args,r,lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            self.assertEqual(r['status'],'unsat_solver_reported');self.assertTrue(r['complete'])
            with self.assertRaises(TimeoutError):m.solve_models(Solver(None),*args,report(),lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            with self.assertRaisesRegex(RuntimeError,'repeated'):m.solve_models(Solver(True),*args,report(),lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            class Broken(Solver):
                def get_model(self):return [1,2]
            with self.assertRaisesRegex(RuntimeError,'degree model'):m.solve_models(Broken(True),*args,report(),lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)

    def test_late_verified_witness_saved_and_dual_failure_not_saved(self):
        import tempfile,threading
        from pathlib import Path
        from unittest.mock import patch
        class State:
            n=3;points=();model={'orbits':(((0,0),),((1,2),),((2,1),))}
        class Solver:
            def solve_limited(self,**kwargs):return True
            def get_model(self):return [1,2,3]
        def report():return {'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        good={'valid':True,'point_count':3,'normalized_sha256':'abc'}
        expired=[False]
        def check():
            if expired[0]:raise TimeoutError
        def validate(_):expired[0]=True;return good
        args=(Solver(),State(),[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)])
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m,'verify_certificate',return_value=good),patch.object(m,'verify_certificate_bruteforce',side_effect=validate):
                r=report();m.solve_models(*args,r,check,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            self.assertEqual(r['status'],'witness');self.assertTrue((Path(tmp)/'witness-abc.json').exists())
        expired[0]=False
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m,'verify_certificate',return_value=good),patch.object(m,'verify_certificate_bruteforce',return_value={**good,'valid':False}):
                with self.assertRaises(RuntimeError):m.solve_models(*args,report(),check,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_incomplete_pairs_block_solver_construction(self):
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        class State:
            points=tuple((i,0) for i in range(78))
            def __init__(self,*a,**kw):pass
            def push(self,v):return True
        def pairs(state,variables,check,counts):counts['pair_completed']=5150;return []
        ids=tuple(range(1,21));sample={'mask_sha256':'x','mask':[1]*102}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m,'EXPECTED_IDS',ids),patch.object(m,'MASK_HASH','x'),patch.object(m,'prefix_paths',return_value=([('main',19,ids)],[])),patch.object(m,'mask_and_bounds',return_value=sample),patch.object(m,'PackedOrbitState',State),patch.object(m,'incompatible_pairs',side_effect=pairs),patch.object(m,'source_manifest',return_value={}),patch('pysat.solvers.Solver') as solver:
                with self.assertRaisesRegex(ValueError,'incomplete pair'):m.run(Path(tmp),25,clock=lambda:0)
                solver.assert_not_called()

class AdditionalBoundaryTests(unittest.TestCase):
    def test_interruption_inside_push_never_returns_pair_verdict(self):
        state=PackedOrbitState(7);state.push(state.bounds['four']+1)
        variables=[i for i in range(1,state.bounds['four']+1) if probe_orbit(state,i)]
        before=state.snapshot();ticks=[0]
        def budget():
            ticks[0]+=1
            if ticks[0]==10: raise TimeoutError
        state.bind_check(budget)
        with self.assertRaises(TimeoutError):
            m.incompatible_pairs(state,variables,lambda:None,{'pair_started':0,'pair_completed':0})
        if not state.poisoned:
            self.assertEqual(state.snapshot(),before)

    def test_one_bad_triple_then_unsat(self):
        import tempfile,threading
        from pathlib import Path
        class State:
            n=3;points=();model={'orbits':(((0,0),),((1,1),),((2,2),))}
        class Solver:
            def __init__(self):self.answers=iter((True,False));self.cuts=[]
            def solve_limited(self,**kwargs):return next(self.answers)
            def get_model(self):return [1,2,3]
            def add_clause(self,c):self.cuts.append(c)
        solver=Solver();report={'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        with tempfile.TemporaryDirectory() as tmp:
            m.solve_models(solver,State(),[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)],report,lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
        self.assertEqual(report['status'],'unsat_solver_reported');self.assertEqual(solver.cuts,[[-1,-2,-3]])
        self.assertEqual(report['triple_cut_ids'],[[1,2,3]])

    def test_timer_join_before_solver_deletion(self):
        order=[]
        class Timer:
            def cancel(self):order.append('cancel')
            def join(self):order.append('join')
        class Solver:
            def delete(self):order.append('delete')
        m.dispose_solver(Timer(),Solver())
        self.assertEqual(order,['cancel','join','delete'])
