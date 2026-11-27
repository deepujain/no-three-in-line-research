import unittest
from research import reproduce_main_ancestor_pairs as m
from research.near_quarter_packed_state import PackedOrbitState
from src.verify import verify_certificate_bruteforce
from unittest.mock import patch


class ReproductionTests(unittest.TestCase):
    def test_tiny_rebuild_and_axis_solver(self):
        for n in (3,5,7):
            state=PackedOrbitState(n);diag=state.bounds['four']+1
            result=m.rebuild(n,(diag,),lambda:None)
            self.assertEqual(result['variables'],sorted(set(result['variables'])))
            self.assertEqual(len(result['pair_cuts']),len(set(result['pair_cuts'])))
            self.assertIn(m.solve(result['formula'],__import__('time').monotonic()+2),('sat','unsat'))

    def test_rebuild_does_not_read_private_checkpoint(self):
        with patch('research.near_quarter_factor_shadow.prefix_paths',side_effect=AssertionError('private checkpoint read')):
            result=m.rebuild(5,(5,),lambda:None)
        self.assertGreater(len(result['variables']),0)

    def test_late_false_after_interrupt_is_unknown_and_cleanup_ordered(self):
        order=[]
        class Solver:
            def __init__(self,**kwargs):pass
            def add_clause(self,clause):pass
            def solve_limited(self,**kwargs):return False
            def interrupt(self):order.append('interrupt')
            def delete(self):order.append('delete')
        class Timer:
            def __init__(self,remaining,callback):self.callback=callback
            def start(self):self.callback()
            def cancel(self):order.append('cancel')
            def join(self):order.append('join')
        with patch.object(m,'Solver',Solver),patch.object(m.threading,'Timer',Timer):
            self.assertEqual(m.solve([],1,clock=lambda:0),'unknown')
        self.assertEqual(order,['interrupt','cancel','join','delete'])

    def test_invalid_or_interrupted_prefix(self):
        with self.assertRaises(ValueError):m.rebuild(3,(999,),lambda:None)
        def stop():raise TimeoutError
        with self.assertRaises(TimeoutError):m.rebuild(3,(2,),stop)
        self.assertEqual(m.solve([],0,clock=lambda:0),'unknown')


if __name__=='__main__':unittest.main()
