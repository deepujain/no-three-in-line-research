import importlib.util
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.near_quarter_model import orbit_map, expand, weighted_lines, streamed_cnf as original_cnf
from src.near_quarter_compact import line_groups, shared_capacity_clauses, streamed_cnf, compact_counts
from src.verify import collinear_triples_bruteforce

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None


class NearQuarterCompactTests(unittest.TestCase):
    def test_line_groups_partition_full_geometry_with_explicit_diagonals(self):
        for n in (3,5,7):
            model = orbit_map(n)
            lines = dict(weighted_lines(model,False))
            groups = list(line_groups(model))
            covered = set()
            specials = 0
            for group in groups:
                rotated = group['line']
                members = set()
                diagonal_ids = set()
                for _ in range(4):
                    members.add(rotated)
                    weights = lines[rotated]
                    self.assertEqual(tuple((v,w) for v,w in weights if v <= model['four_count']),
                                     group['off_diagonal_weights'])
                    diagonal = [(v,w) for v,w in weights if v > model['four_count']]
                    diagonal_ids.update(v for v,w in diagonal)
                    if not group['special_diagonal_orbit']:
                        self.assertLessEqual(len(diagonal),1)
                        self.assertTrue(all(w == 1 for v,w in diagonal))
                    rotated = tuple(sorted((y,n-1-x) for x,y in rotated))
                self.assertEqual(group['orbit_size'],len(members))
                self.assertFalse(covered.intersection(members))
                covered.update(members)
                self.assertEqual(set(group['diagonal_guards']),diagonal_ids)
                if group['special_diagonal_orbit']:
                    specials += 1
                    self.assertEqual(group['off_diagonal_weights'],())
                else:
                    self.assertLessEqual(len(diagonal_ids),2)
            self.assertEqual(covered,set(lines))
            self.assertEqual(specials,1)

    def test_all_tiny_assignments_factorization_matches_full_geometry(self):
        for n in (3,5,7):
            model = orbit_map(n)
            groups = list(line_groups(model))
            for bits in product((False,True),repeat=len(model['orbits'])):
                selected = {v for v,b in enumerate(bits,1) if b}
                # Include the global exactly-one diagonal condition required
                # when omitting the explicit main/anti-diagonal capacities.
                if sum(v > model['four_count'] for v in selected) != 1:
                    continue
                factored = True
                for group in groups:
                    if group['special_diagonal_orbit']:
                        continue
                    weight = sum(w for v,w in group['off_diagonal_weights'] if v in selected)
                    if weight > 2 or (weight > 1 and selected.intersection(group['diagonal_guards'])):
                        factored = False
                        break
                self.assertEqual(factored, not collinear_triples_bruteforce(expand(model,selected)),
                                 (n,selected))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_synthetic_weighted_guards_exhaustive_including_long_counters(self):
        from pysat.formula import IDPool
        from pysat.solvers import Solver
        supports = [(), (1,), (2,), (1,1), (1,2), (2,2), (3,),
                    (1,1,1,1,1), (1,1,1,1,1,1), (2,1,1,1,1,1,1), (3,2,1,1)]
        for coefficients in supports:
            count = len(coefficients)
            weights = tuple(enumerate(coefficients,1))
            for guard_count in (0,1,2):
                guards = tuple(range(count+1,count+1+guard_count))
                total = count+guard_count
                pool = IDPool(start_from=total+1)
                with Solver(name='glucose3',bootstrap_with=shared_capacity_clauses(weights,guards,pool)) as solver:
                    for bits in product((False,True),repeat=total):
                        value = sum(w for w,b in zip(coefficients,bits) if b)
                        active = any(bits[count:])
                        expected = value <= 2 and (not active or value <= 1)
                        self.assertEqual(solver.solve(assumptions=[v if b else -v for v,b in enumerate(bits,1)]),
                                         expected,(coefficients,guard_count,bits))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_complete_tiny_cnf_equivalence_and_compaction(self):
        from pysat.solvers import Solver
        for n in (3,5,7):
            model = orbit_map(n)
            baseline = list(original_cnf(model))
            compact = list(streamed_cnf(model))
            max_id = lambda clauses:max([len(model['orbits'])]+[abs(v) for c in clauses for v in c])
            self.assertLessEqual(len(compact),len(baseline))
            self.assertLessEqual(max_id(compact),max_id(baseline))
            with Solver(name='glucose3',bootstrap_with=baseline) as old, Solver(name='glucose3',bootstrap_with=compact) as new:
                for bits in product((False,True),repeat=len(model['orbits'])):
                    selected = {v for v,b in enumerate(bits,1) if b}
                    count_four = sum(v <= model['four_count'] for v in selected)
                    count_diagonal = len(selected)-count_four
                    expected = (count_four == n//2 and count_diagonal == 1 and
                                not collinear_triples_bruteforce(expand(model,selected)))
                    fixed = [v if b else -v for v,b in enumerate(bits,1)]
                    self.assertEqual(old.solve(assumptions=fixed),expected,(n,bits))
                    self.assertEqual(new.solve(assumptions=fixed),expected,(n,bits))
            identities = compact_counts(model)
            self.assertEqual(identities['encoding_variant'],'c4-shared-offdiagonal-direct-small-v1')
            self.assertEqual(len(identities['compact_source_sha256']),64)


if __name__ == '__main__':
    unittest.main()
