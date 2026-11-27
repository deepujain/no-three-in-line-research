import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research import near_quarter_q_pair_probe as m
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_readonly_probe import probe_orbit


class QPairTests(unittest.TestCase):
    def test_cap_no_truncation(self):
        self.assertEqual(len(m.bounded_mask([1]*320+[0])),320)
        self.assertIsNone(m.bounded_mask([1]*321))
        with self.assertRaises(ValueError):m.bounded_mask([True])

    def test_sat_witness_degrees_and_pair_cuts(self):
        class Solver:
            def __init__(self,model):self.model=model
            def solve_limited(self,**kwargs):return True
            def get_model(self):return self.model
            def interrupt(self):pass
        edges=[(0,1),(1,2),(0,2)]
        ok=m.native_answer(Solver([1,2,3]),[1,2,3],edges,[2,2,2],[],100,lambda:0,expected_selected=3)
        self.assertEqual(ok['status'],'sat_relaxation_only')
        self.assertEqual(ok['selected_local_ids'],[1,2,3])
        with self.assertRaises(RuntimeError):m.native_answer(Solver([1,2]),[1,2,3],edges,[2,2,2],[],100,lambda:0,expected_selected=3)
        with self.assertRaises(RuntimeError):m.native_answer(Solver([1,2,3]),[1,2,3],edges,[2,2,2],[(1,2)],100,lambda:0,expected_selected=3)

    def test_late_false_unknown_and_timer_join(self):
        order=[]
        class Solver:
            def solve_limited(self,**kwargs):return False
            def interrupt(self):order.append('interrupt')
        class Timer:
            def __init__(self,delay,callback):self.callback=callback
            def start(self):self.callback()
            def cancel(self):order.append('cancel')
            def join(self):order.append('join')
        with patch.object(m.threading,'Timer',Timer):
            self.assertEqual(m.native_answer(Solver(),[],[],[],[],1,lambda:0)['status'],'unknown')
        self.assertEqual(order,['interrupt','cancel','join'])

    def test_cap_blocks_solver_no_checkpoint_input(self):
        from types import SimpleNamespace
        class State:
            def __init__(self,n,check):self.map_digest=SimpleNamespace(hex=lambda:m.MAP_HASH);self.points=tuple((i,0) for i in range(66))
            def push(self,v):return True
        sample={'mask':[1]*321+[0]*1200,'mask_sha256':'mock'}
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'mask_and_bounds',return_value=sample),patch.object(m,'PackedOrbitState',State),patch.object(m,'source_manifest',return_value={}),patch('pysat.solvers.Solver') as solver,patch('research.near_quarter_factor_shadow.prefix_paths',side_effect=AssertionError('private checkpoint')):
            report=m.run(Path(tmp),25,clock=lambda:0)
        self.assertEqual(report['status'],'mask_capacity');self.assertFalse(report['complete'])
        self.assertEqual(report['pair_completed'],0);solver.assert_not_called()

    def test_tiny_pairs_use_reviewed_kernel(self):
        state=PackedOrbitState(5);state.push(state.bounds['four']+1)
        ids=[i for i in range(1,state.bounds['four']+1) if probe_orbit(state,i)]
        before=state.snapshot();counts={'pair_started':0,'pair_completed':0}
        m.incompatible_pairs(state,ids,lambda:None,counts)
        self.assertEqual(counts['pair_completed'],len(ids)*(len(ids)-1)//2)
        self.assertEqual(state.snapshot(),before)


if __name__=='__main__':unittest.main()

class QFlowTests(unittest.TestCase):
    def test_complete_mocked_probe_checks_gate_and_reports_scoped_unsat(self):
        from types import SimpleNamespace
        sample={'mask':[1,1]+[0]*1519,'mask_sha256':'x','demands':[2]*23+[0]*17,'edges':[(0,1),(0,1)]}
        class State:
            def __init__(self,n,check):self.map_digest=SimpleNamespace(hex=lambda:m.MAP_HASH);self.points=tuple((i,0) for i in range(66))
            def push(self,v):return True
        class Solver:
            def __init__(self,**kwargs):self.clauses=[]
            def add_clause(self,c):self.clauses.append(c)
            def delete(self):pass
        def pairs(state,ids,check,report):report['pair_started']=1;report['pair_completed']=1;return [(1,2)]
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'mask_and_bounds',return_value=sample),patch.object(m,'PackedOrbitState',State),patch.object(m,'incompatible_pairs',side_effect=pairs),patch.object(m,'degree_clauses',return_value=([[-1]],SimpleNamespace(top=2))),patch.object(m,'source_manifest',return_value={}),patch.object(m,'native_answer',return_value={'status':'unsat_solver_reported','basis':'trusted_native_solver_no_proof'}),patch('pysat.solvers.Solver',Solver):
            report=m.run(Path(tmp),25,clock=lambda:0)
        self.assertTrue(report['complete']);self.assertEqual(report['status'],'unsat_solver_reported')
        self.assertEqual(report['pair_completed'],1);self.assertEqual(report['pair_cut_ids'],[[1,2]])

    def test_incomplete_pair_census_blocks_solver(self):
        from types import SimpleNamespace
        sample={'mask':[1,1]+[0]*1519,'mask_sha256':'x','demands':[2]*23+[0]*17,'edges':[(0,1),(0,1)]}
        class State:
            def __init__(self,n,check):self.map_digest=SimpleNamespace(hex=lambda:m.MAP_HASH);self.points=tuple((i,0) for i in range(66))
            def push(self,v):return True
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'mask_and_bounds',return_value=sample),patch.object(m,'PackedOrbitState',State),patch.object(m,'incompatible_pairs',return_value=[]),patch.object(m,'source_manifest',return_value={}),patch('pysat.solvers.Solver') as solver:
            with self.assertRaisesRegex(ValueError,'incomplete pair census'):m.run(Path(tmp),25,clock=lambda:0)
            solver.assert_not_called()


class QInputChecks(unittest.TestCase):
    def test_corruption_blocks_native(self):
        valid=[2]*23+[0]*17
        m.validate_incidence([1,2],[(0,1),(2,3)],valid)
        for edges,demands in (([(0,0),(2,3)],valid), ([(0,1)],valid), ([(0,1),(2,40)],valid), ([(0,1),(2,3)],[46]+[0]*39)):
            with self.assertRaises(ValueError):m.validate_incidence([1,2],edges,demands)
        for cuts,started,completed in (([(1,2)],0,1), ([(1,2),(1,2)],1,1), ([(1,3)],1,1)):
            with self.assertRaises(ValueError):m.validate_pair_census(cuts,2,started,completed)

    def test_invalid_incidence_blocks_solver_in_run(self):
        from types import SimpleNamespace
        sample={'mask':[1,1]+[0]*1519,'mask_sha256':'x','demands':[2]*23+[0]*17,'edges':[(0,0),(2,3)]}
        class State:
            def __init__(self,n,check):self.map_digest=SimpleNamespace(hex=lambda:m.MAP_HASH);self.points=tuple((i,0) for i in range(66))
            def push(self,v):return True
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'mask_and_bounds',return_value=sample),patch.object(m,'PackedOrbitState',State),patch.object(m,'source_manifest',return_value={}),patch('pysat.solvers.Solver') as solver:
            with self.assertRaisesRegex(ValueError,'edge endpoints'):m.run(Path(tmp),25,clock=lambda:0)
            solver.assert_not_called()
