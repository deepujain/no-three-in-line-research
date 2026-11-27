import itertools
import threading
import time
import unittest
from research.near_quarter_radius_factor import radius_factor


def feasible(demands,edges):
    for mask in range(1<<len(edges)):
        degree=[0]*len(demands)
        for i,(u,v) in enumerate(edges):
            if mask>>i & 1: degree[u]+=1;degree[v]+=1
        if degree==list(demands): return True
    return False


class RadiusFactorTests(unittest.TestCase):
    def test_tiny_multigraphs_against_exact_oracle(self):
        for n,mults in ((3,range(3)),(4,range(2))):
            pairs=list(itertools.combinations(range(n),2))
            for counts in itertools.product(mults,repeat=len(pairs)):
                edges=[edge for edge,num in zip(pairs,counts) for _ in range(num)]
                for demands in itertools.product(range(3),repeat=n):
                    result=radius_factor(demands,edges,time.monotonic()+2)
                    self.assertEqual(result['status'],'sat' if feasible(demands,edges) else 'unsat')

    def test_hub_five_triangles_unsat(self):
        edges=[]
        for k in range(5):
            a,b,c=(1+3*k,2+3*k,3+3*k)
            edges.extend(((a,b),(b,c),(c,a),(0,a)))
        result=radius_factor([1]*16,edges,time.monotonic()+2)
        self.assertEqual(result['status'],'unsat')
        self.assertEqual(result['basis'],'trusted_native_solver')

    def test_deadline_and_unknown(self):
        self.assertEqual(radius_factor([1,1],[(0,1)],0,clock=lambda:0)['status'],'unknown')
        class UnknownSolver:
            def __init__(self,**kwargs): pass
            def add_clause(self,clause): pass
            def solve_limited(self,**kwargs): return None
            def delete(self): pass
            def interrupt(self): pass
        self.assertEqual(radius_factor([1,1],[(0,1)],time.monotonic()+2,solver_class=UnknownSolver)['status'],'unknown')

    def test_timer_interruption_cannot_return_unsat(self):
        class SlowSolver:
            def __init__(self,**kwargs): self.event=threading.Event()
            def add_clause(self,clause): pass
            def solve_limited(self,**kwargs): self.event.wait(1); return False
            def interrupt(self): self.event.set()
            def delete(self): pass
        result=radius_factor([1,1],[(0,1)],time.monotonic()+0.01,solver_class=SlowSolver)
        self.assertEqual(result['status'],'unknown')

    def test_invalid_witness_never_accepted(self):
        class BadSolver:
            def __init__(self,**kwargs): pass
            def add_clause(self,clause): pass
            def solve_limited(self,**kwargs): return True
            def get_model(self): return [-1]
            def delete(self): pass
            def interrupt(self): pass
        with self.assertRaises(RuntimeError):
            radius_factor([1,1],[(0,1)],time.monotonic()+2,solver_class=BadSolver)


if __name__=='__main__': unittest.main()
