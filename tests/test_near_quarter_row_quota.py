import importlib.util
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.near_quarter_model import orbit_map,expand,weighted_lines
from src.near_quarter_compact import streamed_cnf as compact_cnf
from src.near_quarter_row_quota import at_least_two,row_floor_clauses,row_quota_counts,streamed_cnf
from src.verify import collinear_triples_bruteforce

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None


class RowQuotaTests(unittest.TestCase):
    def test_zero_auxiliary_positive_lower_bound_all_small_weighted_assignments(self):
        for size in range(6):
            for coefficients in product((1,2,3),repeat=size):
                clauses = list(at_least_two(enumerate(coefficients,1)))
                for bits in product((False,True),repeat=size):
                    expected = sum(w for w,b in zip(coefficients,bits) if b) >= 2
                    self.assertEqual(all(any(bits[v-1] for v in c) for c in clauses),expected,
                                     (coefficients,bits))
                self.assertTrue(all(1 <= v <= size for c in clauses for v in c))

    def test_representative_row_floors_match_every_tiny_assignment(self):
        for n in (3,5,7):
            model = orbit_map(n)
            clauses = list(row_floor_clauses(model))
            self.assertEqual(len(clauses),(n//2)*(n-1)+1)
            self.assertEqual(sum(map(len,clauses)),(n//2)*(n-1)*(n-2)+n//2)
            for bits in product((False,True),repeat=len(model['orbits'])):
                selected = {v for v,b in enumerate(bits,1) if b}
                points = expand(model,selected)
                rows = [sum(y == row for x,y in points) for row in range(n)]
                columns = [sum(x == column for x,y in points) for column in range(n)]
                expected = all(load >= 2 for load in rows)
                self.assertEqual(all(any(v in selected for v in c) for c in clauses),expected)
                self.assertEqual(rows,rows[::-1])
                self.assertEqual(rows,columns)

    def test_row_caps_and_floors_imply_original_cardinality_on_all_tiny_assignments(self):
        for n in (3,5,7):
            model = orbit_map(n)
            lines = list(weighted_lines(model,False))
            floors = list(row_floor_clauses(model))
            for bits in product((False,True),repeat=len(model['orbits'])):
                selected = {v for v,b in enumerate(bits,1) if b}
                diagonal = sum(v > model['four_count'] for v in selected)
                valid_lines = all(sum(w for v,w in weights if v in selected) <= 2 for _,weights in lines)
                old = valid_lines and diagonal == 1 and len(selected)-diagonal == n//2
                new = valid_lines and diagonal == 1 and all(any(v in selected for v in c) for c in floors)
                self.assertEqual(new,old,(n,bits))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_complete_cnf_projected_equivalence_against_compact_and_exact_geometry(self):
        from pysat.solvers import Solver
        for n in (3,5,7):
            model = orbit_map(n)
            with Solver(name='glucose3',bootstrap_with=compact_cnf(model)) as old, \
                    Solver(name='glucose3',bootstrap_with=streamed_cnf(model)) as new:
                for bits in product((False,True),repeat=len(model['orbits'])):
                    selected = {v for v,b in enumerate(bits,1) if b}
                    diagonal = sum(v > model['four_count'] for v in selected)
                    expected = (diagonal == 1 and len(selected)-diagonal == n//2 and
                                not collinear_triples_bruteforce(expand(model,selected)))
                    fixed = [v if b else -v for v,b in enumerate(bits,1)]
                    self.assertEqual(old.solve(assumptions=fixed),expected,(n,bits))
                    self.assertEqual(new.solve(assumptions=fixed),expected,(n,bits))
            self.assertEqual(row_quota_counts(model)['encoding_variant'],
                             'near-quarter-row-floor-shared-capacity-v1')


if __name__ == '__main__':
    unittest.main()
