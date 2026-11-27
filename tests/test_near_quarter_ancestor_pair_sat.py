import unittest
from research import near_quarter_ancestor_pair_sat as m


class AncestorTests(unittest.TestCase):
    def test_prefix_counts_and_identity(self):
        self.assertEqual([len(m.prefix_for_depth(m.EXPECTED_IDS,d)) for d in m.DEPTHS],[19,18,17])
        self.assertEqual([2+4*d for d in m.DEPTHS],[74,70,66])
        self.assertEqual([39-d for d in m.DEPTHS],[21,22,23])
        with self.assertRaises(ValueError):m.prefix_for_depth(m.EXPECTED_IDS[:-1],18)
        with self.assertRaises(ValueError):m.prefix_for_depth(m.EXPECTED_IDS,15)

    def test_mask_cap_never_truncates(self):
        self.assertEqual(len(m.bounded_variables([1]*200+[0]*5)),200)
        self.assertIsNone(m.bounded_variables([1]*201+[0]*4))
        with self.assertRaises(ValueError):m.bounded_variables([1,2])
        self.assertEqual(200*199//2,19900)

    def test_advance_only_unsat_and_preserve_previous(self):
        for stop in ('witness','timeout','solver_unknown','cut_limit','mask_capacity','degree_shortfall'):
            report={'status':'incomplete','complete':False,'stages':[{'depth':x,'status':'unstarted'} for x in m.DEPTHS]}
            seen=[]
            def run(stage):
                seen.append(stage['depth']);stage['evidence']=stage['depth']
                stage['status']='unsat_solver_reported' if stage['depth']==18 else stop
            m.adaptive_loop(report,run)
            self.assertEqual(seen,[18,17]);self.assertEqual(report['status'],stop)
            self.assertEqual(report['stages'][0]['evidence'],18)
            self.assertEqual(report['stages'][2]['status'],'unstarted')
            self.assertEqual(report['complete'],stop=='witness')
        report={'status':'incomplete','complete':False,'stages':[{'depth':x,'status':'unstarted'} for x in m.DEPTHS]}
        m.adaptive_loop(report,lambda stage:stage.update(status='unsat_solver_reported'))
        self.assertTrue(report['complete']);self.assertEqual(report['status'],'all_ancestors_unsat_solver_reported')

    def test_later_interruption_preserves_prior_stage(self):
        report={'status':'incomplete','complete':False,'stages':[{'depth':x,'status':'unstarted'} for x in m.DEPTHS]}
        def run(stage):
            if stage['depth']==18:stage.update(status='unsat_solver_reported',pair_completed=99)
            else:raise TimeoutError
        with self.assertRaises(TimeoutError):m.adaptive_loop(report,run)
        self.assertEqual(report['stages'][0]['pair_completed'],99)
        self.assertEqual(report['stages'][1]['status'],'incomplete')
        self.assertEqual(report['stages'][2]['status'],'unstarted')


if __name__=='__main__':unittest.main()

class AncestorAdapterTests(unittest.TestCase):
    def test_new_solve_loop_reuses_independent_fake_solver_cases(self):
        from unittest.mock import patch
        import tests.test_near_quarter_prefix_pair_sat as base
        with patch.object(base,'m',m):
            base.SolveLoopTests('test_complete_loop_enforces_cut_limit').test_complete_loop_enforces_cut_limit()
            base.SolveLoopTests('test_timer_race_false_is_unknown').test_timer_race_false_is_unknown()
            base.SolveFailureTests('test_late_verified_witness_saved_and_dual_failure_not_saved').test_late_verified_witness_saved_and_dual_failure_not_saved()
            base.AdditionalBoundaryTests('test_one_bad_triple_then_unsat').test_one_bad_triple_then_unsat()
        # The new loop distinguishes an unexpired native None from timeout.
        import tempfile,threading
        from pathlib import Path
        class State:n=3;points=();model={'orbits':(((0,0),),((1,1),),((2,2),))}
        class Solver:
            def solve_limited(self,**kwargs):return None
        report={'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        with tempfile.TemporaryDirectory() as tmp:
            m.solve_models(Solver(),State(),[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)],report,lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
        self.assertEqual(report['status'],'solver_unknown');self.assertFalse(report['complete'])

    def test_real_prefix_fake_three_stage_shared_deadline_and_cleanup(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from pathlib import Path
        import tempfile
        tick=[0];events=[];states=[];targets=[];deadlines=[]
        class State:
            def __init__(self,n,check):self.ids=[];states.append(self)
            def push(self,var):self.ids.append(var);return True
            @property
            def points(self):return tuple((i,0) for i in range(2+4*(len(self.ids)-1)))
        class Solver:
            def __init__(self,**kw):events.append('solver')
            def add_clause(self,c):pass
            def delete(self):events.append('delete')
            def interrupt(self):events.append('interrupt')
        class Timer:
            def __init__(self,remaining,callback):events.append(('timer',remaining))
            def start(self):events.append('start')
            def cancel(self):events.append('cancel')
            def join(self):events.append('join')
        def mask(n,ids,check):
            d=len(ids)-1
            return {'mask':[1],'mask_sha256':str(d),'demands':[2*(39-d)],'edges':[]}
        def pairs(state,variables,check,stage):
            self.assertEqual(stage['pair_completed'],0);events.append('pairs');return []
        def solve(solver,state,variables,demands,edges,stage,check,fired,deadline,clock,out,*,target_orbits):
            targets.append(target_orbits);deadlines.append(deadline);stage['status']='unsat_solver_reported';stage['complete']=True;tick[0]+=1
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'PackedOrbitState',State),patch.object(m,'mask_and_bounds',side_effect=mask),patch.object(m,'incompatible_pairs',side_effect=pairs),patch.object(m,'degree_clauses',return_value=([],SimpleNamespace(top=1))),patch.object(m,'solve_models',side_effect=solve),patch.object(m.threading,'Timer',Timer),patch('pysat.solvers.Solver',Solver):
            report=m.run(Path(tmp),25,clock=lambda:tick[0])
        self.assertEqual(targets,[21,22,23]);self.assertEqual(deadlines,[25,25,25])
        self.assertEqual([x for x in events if isinstance(x,tuple)],[('timer',25),('timer',24),('timer',23)])
        self.assertEqual(len(states),3);self.assertEqual(len({id(x) for x in states}),3)
        self.assertEqual([x for x in events if x in ('cancel','join','delete')],['cancel','join','delete']*3)
        self.assertEqual(report['status'],'all_ancestors_unsat_solver_reported')

    def test_incomplete_pair_gate_before_any_solver(self):
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        class State:
            def __init__(self,n,check):self.ids=[]
            def push(self,var):self.ids.append(var);return True
            @property
            def points(self):return tuple((i,0) for i in range(2+4*(len(self.ids)-1)))
        def mask(n,ids,check):return {'mask':[1,1],'mask_sha256':'x','demands':[42],'edges':[]}
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'PackedOrbitState',State),patch.object(m,'mask_and_bounds',side_effect=mask),patch.object(m,'incompatible_pairs',return_value=[]),patch('pysat.solvers.Solver') as solver:
            with self.assertRaisesRegex(ValueError,'incomplete pair census'):m.run(Path(tmp),25,clock=lambda:0)
            solver.assert_not_called()

    def test_repeated_cut_and_bad_model_fail_closed(self):
        import tempfile,threading
        from pathlib import Path
        class State:n=3;points=();model={'orbits':(((0,0),),((1,1),),((2,2),))}
        class Solver:
            def __init__(self,model):self.model=model
            def solve_limited(self,**kwargs):return True
            def get_model(self):return self.model
            def add_clause(self,c):pass
        def report():return {'status':'incomplete','complete':False,'model_count':0,'triple_cuts':0,'witnesses':0}
        with tempfile.TemporaryDirectory() as tmp:
            args=(State(),[1,2,3],[2,2,2],[(0,1),(1,2),(0,2)])
            with self.assertRaisesRegex(RuntimeError,'repeated'):
                m.solve_models(Solver([1,2,3]),*args,report(),lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
            with self.assertRaisesRegex(RuntimeError,'degree model'):
                m.solve_models(Solver([1,2]),*args,report(),lambda:None,threading.Event(),1,lambda:0,Path(tmp),target_points=3,target_orbits=3)
