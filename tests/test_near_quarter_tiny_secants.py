"""Exhaustive tiny state evidence, independently rebuilding by determinants."""
from itertools import combinations,product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_tiny_secants import TinyOrbitState,grid_line,tiny_mrv_traversal
from src.near_quarter_model import orbit_map,expand,check_candidate
from src.verify import collinear_triples_bruteforce

CENSUS = {}


def reference_counts(points,n):
    result = [0]*(n*n)
    for a,b in combinations(points,2):
        for y in range(n):
            for x in range(n):
                if (b[0]-a[0])*(y-a[1]) == (b[1]-a[1])*(x-a[0]):
                    result[y*n+x] += 1
    return result


def admissible_subset(model,selected):
    four = sum(v <= model['four_count'] for v in selected)
    diagonal = len(selected)-four
    return (four <= model['n']//2 and diagonal <= 1 and
            not collinear_triples_bruteforce(expand(model,selected)))


class TinyOrbitSecantTests(unittest.TestCase):
    def check_state(self,state):
        n = state.n
        self.assertEqual(list(state.blocked),reference_counts(state.points,n))
        self.assertEqual(list(state.rows),[sum(y == row for x,y in state.points) for row in range(n)])
        self.assertEqual(list(state.columns),[sum(x == column for x,y in state.points) for column in range(n)])
        self.assertEqual(sum(state.occupied),len(state.points))
        self.assertTrue(all(v <= 2 for v in state.rows))
        self.assertTrue(all(v <= 2 for v in state.columns))
        self.assertLessEqual(max(state.blocked),len(state.points)*(len(state.points)-1)//2)

    def test_grid_lines_match_independent_determinants_for_every_tiny_point_pair(self):
        for n in (3,5,7):
            points = [(x,y) for y in range(n) for x in range(n)]
            for a,b in combinations(points,2):
                expected = {y*n+x for x,y in points
                    if (b[0]-a[0])*(y-a[1]) == (b[1]-a[1])*(x-a[0])}
                self.assertEqual(set(grid_line(a,b,n)),expected)
                self.assertEqual(set(grid_line(b,a,n)),expected)

    def test_every_tiny_orbit_subset_and_every_valid_extension_with_exact_undo(self):
        for n in (3,5,7):
            model = orbit_map(n)
            valid = full = extension_checks = 0
            for bits in product((False,True),repeat=len(model['orbits'])):
                selected = [v for v,b in enumerate(bits,1) if b]
                state = TinyOrbitState(n)
                empty = state.snapshot()
                accepted = True
                for variable in selected:
                    before = state.snapshot()
                    if not state.push(variable):
                        self.assertEqual(state.snapshot(),before)
                        accepted = False
                        break
                    self.check_state(state)
                self.assertIs(accepted,admissible_subset(model,selected),(n,selected))
                if accepted:
                    valid += 1
                    self.check_state(state)
                    full += state.full_family_leaf()
                    if state.full_family_leaf():
                        self.assertTrue(check_candidate(model,selected)['valid_full_witness'])
                    for variable in range(1,len(model['orbits'])+1):
                        before = state.snapshot()
                        expected = variable not in selected and admissible_subset(model,selected+[variable])
                        added = state.push(variable)
                        extension_checks += 1
                        self.assertIs(added,expected,(n,selected,variable))
                        if added:
                            self.check_state(state)
                            state.pop()
                        self.assertEqual(state.snapshot(),before)
                while state.selected:
                    state.pop()
                    self.check_state(state)
                self.assertEqual(state.snapshot(),empty)
            CENSUS[n] = {**CENSUS.get(n,{}),'subsets':2**len(model['orbits']),'valid_partial_subsets':valid,
                         'full_family_subsets':full,'extension_checks':extension_checks,
                         'packed_counter_bytes':state.blocked.itemsize*n*n,
                         'scope':'tiny exact state/undo checks, not a timed production DFS'}

    def test_tiny_only_guard_and_invalid_orbit_ids(self):
        for n in (1,9,79,True):
            with self.assertRaises(ValueError):
                TinyOrbitState(n)
        state = TinyOrbitState(3)
        for variable in (0,3,True,None):
            with self.assertRaises(ValueError):
                state.push(variable)
        with self.assertRaises(ValueError):
            state.pop()
        self.assertEqual(state.blocked.itemsize,2)


    def test_diagonal_first_mrv_and_optimistic_row_bounds_preserve_tiny_complete_sets(self):
        for n in (3,5,7):
            model = orbit_map(n)
            expected = set()
            for four in combinations(range(1,model['four_count']+1),n//2):
                for diagonal in range(model['four_count']+1,len(model['orbits'])+1):
                    chosen = tuple(sorted((*four,diagonal)))
                    if not collinear_triples_bruteforce(expand(model,chosen)):
                        expected.add(chosen)
            forward = tiny_mrv_traversal(n)
            reverse = tiny_mrv_traversal(n,
                diagonal_order=list(reversed(range(model['four_count']+1,len(model['orbits'])+1))),
                orbit_order=list(reversed(range(1,model['four_count']+1))),row_order=list(reversed(range(n))))
            for result in (forward,reverse):
                self.assertEqual(result['status'],'tiny_slices_exhausted')
                self.assertEqual({tuple(ids) for ids in result['unique_sets']},expected)
            self.assertNotEqual(forward['order_identity_sha256'],reverse['order_identity_sha256'])
            CENSUS.setdefault(n,{})['mrv_forward'] = {k:forward[k] for k in ('nodes','full_leaf_visits','row_shortfall_prunes','orbit_shortfall_prunes','order_identity_sha256')}
            CENSUS.setdefault(n,{})['mrv_reverse'] = {k:reverse[k] for k in ('nodes','full_leaf_visits','row_shortfall_prunes','orbit_shortfall_prunes','order_identity_sha256')}
        self.assertEqual(tiny_mrv_traversal(3,max_nodes=1)['status'],'tiny_node_limit')
        for n in (9,79):
            with self.assertRaises(ValueError):
                tiny_mrv_traversal(n)
        with self.assertRaises(ValueError):
            tiny_mrv_traversal(3,orbit_order=[])


if __name__ == '__main__':
    unittest.main()
