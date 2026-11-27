import importlib.util
from itertools import combinations, product
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from near_quarter_model import orbit_map,expand,weighted_lines,check_candidate,streamed_cnf,capacity_clauses
from verify import collinear_triples_bruteforce, verify_certificate_bruteforce
HAVE_PYSAT=importlib.util.find_spec('pysat') is not None

class NearQuarterTests(unittest.TestCase):
    def test_orbit_sizes_disjointness_and_diagonals(self):
        for n in (3,5,7):
            model=orbit_map(n);m=n//2
            self.assertEqual(model['four_count'],m*m)
            self.assertEqual(model['diagonal_count'],m)
            self.assertEqual(len(model['point_to_var']),n*n-n)
            self.assertTrue(all((x,n-1-x) not in model['point_to_var'] for x in range(n)))
            self.assertTrue(all(len(o)==4 for o in model['orbits'][:m*m]))
            self.assertTrue(all(len(o)==2 for o in model['orbits'][m*m:]))

    def test_every_small_assignment_matches_geometry_and_quotient(self):
        for n in (3,5,7):
            model=orbit_map(n); lines=list(weighted_lines(model,False)); quot=list(weighted_lines(model,True))
            self.assertTrue(any(sum(w==2 for _,w in v)>0 for _,v in lines))
            self.assertTrue(all(w<=2 for _,v in lines for _,w in v))
            for mask in range(1<<len(model['orbits'])):
                selected={v for v in range(1,len(model['orbits'])+1) if mask & (1<<(v-1))}
                def valid_constraints(ls):
                    return all(sum(w for v,w in weights if v in selected)<=2 for _,weights in ls)
                expected=not collinear_triples_bruteforce(expand(model,selected))
                self.assertEqual(valid_constraints(lines),expected,(n,mask))
                self.assertEqual(valid_constraints(quot),expected,(n,mask))

    def test_source_n3_fixture(self):
        model=orbit_map(3)
        fixture={(0,0),(2,2),(0,1),(1,0),(1,2),(2,1)}
        selected={model['point_to_var'][p] for p in fixture}
        self.assertEqual(set(map(tuple,expand(model,selected))),fixture)
        self.assertTrue(verify_certificate_bruteforce({'n':3,'points':list(fixture)})['valid'])
        self.assertTrue(check_candidate(model,selected)['valid_full_witness'])
        self.assertFalse(check_candidate(model,[])['valid_full_witness'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_streamed_cnf_matches_every_small_assignment(self):
        from pysat.solvers import Solver
        for n in (3,5,7):
            model=orbit_map(n);N=len(model['orbits']); four=model['four_count']
            for quotient in (False,True):
                with Solver(name='glucose3',bootstrap_with=streamed_cnf(model,quotient)) as solver:
                    for mask in range(1<<N):
                        selected={v for v in range(1,N+1) if mask&(1<<(v-1))}
                        points=expand(model,selected)
                        expected=(sum(v<=four for v in selected)==n//2 and
                                  sum(v>four for v in selected)==1 and
                                  not collinear_triples_bruteforce(points))
                        assumptions=[v if v in selected else -v for v in range(1,N+1)]
                        self.assertEqual(solver.solve(assumptions=assumptions),expected,(n,quotient,mask))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_weighted_cnf_including_synthetic_heavy_coefficients(self):
        from pysat.solvers import Solver
        from pysat.formula import IDPool
        weights=((1,1),(2,1),(3,1),(4,2),(5,2),(6,3))
        pool=IDPool(start_from=7)
        with Solver(name='glucose3',bootstrap_with=capacity_clauses(weights,pool)) as solver:
            for bits in product((False,True),repeat=6):
                expected=sum(w for (v,w),b in zip(weights,bits) if b)<=2
                self.assertEqual(solver.solve(assumptions=[i+1 if b else -(i+1) for i,b in enumerate(bits)]),expected)

if __name__=='__main__':unittest.main()
