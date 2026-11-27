"""Tiny exhaustive equivalence of mirror shortcut and original DFS."""
import unittest

from research import diagonal_secant_dfs as baseline
from research import diagonal_secant_dfs_fast as fast
from tests.test_diagonal_secant_dfs import reference, snapshot


class MirrorAdmissibilityTests(unittest.TestCase):
    def test_predicate_matches_push_at_all_reachable_partial_states(self):
        for n in (3, 4, 5):
            orbits = [((i,i),) for i in range(n)] + baseline.pair_orbits(n)
            pairs = baseline.pair_orbits(n)
            for deficit in range(n):
                state = baseline.SecantState(n, deficit)
                def visit(start):
                    sums = {x+y for x,y in state.points}
                    for orbit in pairs:
                        before = snapshot(state)
                        predicted = fast.mirror_pair_admissible(state, orbit, sums)
                        actual = state.push(orbit)
                        if actual: state.pop()
                        self.assertEqual(snapshot(state), before)
                        self.assertEqual(predicted, actual, (n, deficit, before[0], orbit))
                    for idx in range(start, len(orbits)):
                        before = snapshot(state)
                        if state.push(orbits[idx]):
                            visit(idx+1)
                            state.pop()
                        self.assertEqual(snapshot(state), before)
                visit(0)

    def test_full_search_sets_order_and_nodes(self):
        for n in (3, 4, 5):
            with self.subTest(n=n):
                outputs = []
                for module in (baseline, fast):
                    visits = []
                    def collect(cert):
                        visits.append((cert['metadata']['deficit'], cert['metadata']['diagonal'],
                                       tuple(map(tuple, cert['points']))))
                    result = module.search(n, 120, 1000000, on_witness=collect)
                    self.assertEqual(result['status'], 'all_declared_slices_exhausted')
                    outputs.append((result, visits))
                original, optimized = outputs
                self.assertEqual(original[1], optimized[1])
                self.assertEqual(original[0]['nodes'], optimized[0]['nodes'])
                self.assertEqual(original[0]['witness_visits'], optimized[0]['witness_visits'])
                self.assertEqual(original[0]['slice_results'], optimized[0]['slice_results'])
                self.assertEqual({frozenset(v[2]) for v in optimized[1]}, reference(n))


if __name__ == '__main__': unittest.main()
