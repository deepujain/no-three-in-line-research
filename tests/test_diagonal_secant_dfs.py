import itertools
import unittest
from unittest.mock import patch

from research.diagonal_secant_dfs import SecantState, pair_orbits, search


def valid(points):
    return all((b[0]-a[0])*(c[1]-a[1]) != (b[1]-a[1])*(c[0]-a[0])
               for a, b, c in itertools.combinations(points, 3))


def reference(n):
    cells = list(itertools.product(range(n), repeat=2))
    if n <= 4:
        candidates = itertools.combinations(cells, 2*n-1)
    else:
        orbits = [((i, i),) for i in range(n)] + pair_orbits(n)
        candidates = (tuple(p for i, orbit in enumerate(orbits) if mask & (1 << i) for p in orbit)
                      for mask in range(1 << len(orbits)))
    return {frozenset(p) for p in candidates if len(p) == 2*n-1
            and {(y,x) for x,y in p} == set(p) and valid(p)}


def snapshot(state):
    return (tuple(state.points), frozenset(state.occupied), tuple(state.rows),
            tuple(state.columns), tuple(state.blocked), tuple(state.frames))


def check_state(test, state):
    points = state.points
    test.assertEqual(set(points), state.occupied)
    test.assertEqual(state.rows, [sum(y == i for x,y in points) for i in range(state.n)])
    test.assertEqual(state.columns, [sum(x == i for x,y in points) for i in range(state.n)])
    expected = []
    for y in range(state.n):
        for x in range(state.n):
            expected.append(sum((b[0]-a[0])*(y-a[1]) == (b[1]-a[1])*(x-a[0])
                                for a,b in itertools.combinations(points, 2)))
    test.assertEqual(state.blocked, expected)
    test.assertTrue(all(v >= 0 for v in state.blocked))


class DiagonalSearchTests(unittest.TestCase):
    def test_exhaustive_witness_sets(self):
        fixtures = {
            3: frozenset({(0,0),(0,1),(1,0),(1,2),(2,1)}),
            4: frozenset({(0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,3)}),
        }
        for n in (3, 4, 5):
            with self.subTest(n=n):
                expected = reference(n)
                found = set()
                report = search(n, 120, 1000000,
                                on_witness=lambda cert: found.add(frozenset(map(tuple, cert['points']))))
                self.assertEqual(report['status'], 'all_declared_slices_exhausted')
                self.assertEqual(len(report['slice_results']), n*n)
                self.assertTrue(all(s['status'] == 'exhausted' for s in report['slice_results']))
                self.assertEqual(found, expected)
                if n in fixtures:
                    self.assertIn(fixtures[n], found)

    def test_reachable_partial_states_and_rollback(self):
        for n in (3, 4, 5):
            orbits = [((i,i),) for i in range(n)] + pair_orbits(n)
            for d in range(n):
                state = SecantState(n, d)
                def explore(start):
                    check_state(self, state)
                    for i in range(start, len(orbits)):
                        before = snapshot(state)
                        points = list(state.points) + list(orbits[i])
                        expected = (len(points) == len(set(points)) and valid(points)
                                    and all(sum(y == j for x,y in points) <= state.target[j]
                                            and sum(x == j for x,y in points) <= state.target[j]
                                            for j in range(n)))
                        accepted = state.push(orbits[i])
                        self.assertEqual(accepted, expected)
                        check_state(self, state)
                        if accepted:
                            explore(i+1)
                            state.pop()
                        self.assertEqual(snapshot(state), before)
                        check_state(self, state)
                explore(0)

    def test_bounds_and_inputs(self):
        report = search(4, 10, 1)
        self.assertEqual(report['status'], 'node_limit')
        self.assertEqual(report['slice_results'][0]['status'], 'node_limit')
        # Force expiry while checking candidate orbits, inside a visited node.
        ticks = iter([0, 0, 0, 0, 2, 2])
        with patch('research.diagonal_secant_dfs.time.monotonic', side_effect=lambda: next(ticks)):
            report = search(4, 1, 100)
        self.assertEqual(report['status'], 'timeout')
        self.assertEqual(report['slice_results'][0]['status'], 'timeout')
        for args in [(1,1,1), (3,0,1), (3,float('nan'),1), (3,1,0), (True,1,1)]:
            with self.assertRaises(ValueError): search(*args)
        with self.assertRaises(ValueError): search(3,1,1,deficits=[0,0])
        state = SecantState(3,0)
        for orbit in [(), ((0,0),(0,0)), ([0,0],), ((True,0),)]:
            with self.assertRaises(ValueError): state.push(orbit)
        with self.assertRaises(ValueError): state.pop()


if __name__ == '__main__': unittest.main()
