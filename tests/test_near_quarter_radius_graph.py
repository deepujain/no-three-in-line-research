"""Independent degree-subset and tiny geometric completion oracles only."""
import itertools
import unittest

from research.near_quarter_radius_graph import component_obstruction, radius_obstruction
from research.near_quarter_tiny_secants import TinyOrbitState
from src.near_quarter_model import orbit_map
from src.verify import verify_certificate_bruteforce


class RadiusGraphTests(unittest.TestCase):
    statistics = {}

    def test_abstract_degree_subset_oracle_with_parallel_edges(self):
        cases = rejected = 0
        for vertices, parallel in ((3, True), (4, False)):
            pairs = list(itertools.combinations(range(vertices), 2))
            for multiplicities in itertools.product(range(3 if parallel else 2), repeat=len(pairs)):
                edges = [edge for edge, count in zip(pairs, multiplicities) for _ in range(count)]
                feasible = set()
                for bits in range(1 << len(edges)):
                    degree = [0]*vertices
                    for i, (u, v) in enumerate(edges):
                        if bits & (1 << i):
                            degree[u] += 1
                            degree[v] += 1
                    feasible.add(tuple(degree))
                for demand in itertools.product(range(3), repeat=vertices):
                    cases += 1
                    reason = component_obstruction(demand, edges)
                    if reason:
                        rejected += 1
                        self.assertNotIn(demand, feasible)
        self.statistics['abstract_cases'] = cases
        self.statistics['abstract_rejected'] = rejected

    def test_strictness_examples_and_allowed_cycles(self):
        triangles = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]
        self.assertEqual(component_obstruction([1]*6, triangles), 'component_parity')
        k23 = [(u, v) for u in (0, 1) for v in (2, 3, 4)]
        self.assertEqual(component_obstruction([1, 1, 1, 1, 2], k23), 'bipartite_balance')
        self.assertIsNone(component_obstruction([2]*3, [(0, 1), (1, 2), (2, 0)]))
        self.assertIsNone(component_obstruction([2]*4, [(0, 1), (0, 1), (2, 3), (2, 3)]))
        self.assertEqual(component_obstruction([2], []), 'bipartite_balance')
        self.assertIsNone(component_obstruction([0], []))

    def test_tiny_mapping_and_every_valid_prefix_against_completion_oracle(self):
        totals = {}
        for n in (3, 5, 7):
            model, m = orbit_map(n), n//2
            four = model['four_count']
            completions = []
            for diagonal in range(four+1, four+m+1):
                for selected in itertools.combinations(range(1, four+1), m):
                    ids = frozenset((diagonal, *selected))
                    points = [list(p) for v in ids for p in model['orbits'][v-1]]
                    if verify_certificate_bruteforce({'n': n, 'points': points})['valid']:
                        completions.append(ids)
            for orbit in model['orbits'][:four]:
                pairs = {tuple(sorted((abs(x-m), abs(y-m)))) for x, y in orbit}
                self.assertEqual(len(pairs), 1)
                u, v = next(iter(pairs))
                self.assertNotEqual(u, v)
            counts = {'prefixes': 0, 'graph_rejections': 0, 'additional_over_row_orbit_bounds': 0,
                      'oracle_completions': len(completions)}
            for diagonal in range(four+1, four+m+1):
                for bits in range(1 << four):
                    chosen = [v+1 for v in range(four) if bits & (1 << v)]
                    if len(chosen) >= m:
                        continue  # Existing target/leaf handling precedes the scanner.
                    state = TinyOrbitState(n)
                    prefix = frozenset((diagonal, *chosen))
                    if not all(state.push(v) for v in (diagonal, *chosen)):
                        continue
                    counts['prefixes'] += 1
                    mask = bytearray(four)
                    for v in range(1, four+1):
                        if v not in prefix and state.push(v):
                            mask[v-1] = 1
                            state.pop()
                    rows_before, mask_before = tuple(state.rows), bytes(mask)
                    reason = radius_obstruction(n, state.rows, model['orbits'], mask, m-len(chosen))
                    self.assertEqual((tuple(state.rows), bytes(mask)), (rows_before, mask_before))
                    if reason:
                        counts['graph_rejections'] += 1
                        self.assertFalse(any(prefix <= completion for completion in completions))
                        # Independent optimistic individual-row bound, matching
                        # the existing relaxation without invoking its scanner.
                        row_pass = sum(mask) >= m-len(chosen)
                        for row in range(n):
                            weights = [sum(y == row for x, y in model['orbits'][i])
                                       for i, mark in enumerate(mask) if mark]
                            r = m-len(chosen)
                            c1, c2 = weights.count(1), weights.count(2)
                            upper = 2*min(c2, r)+min(c1, max(0, r-c2))
                            row_pass = row_pass and upper >= 2-state.rows[row]
                        if row_pass:
                            counts['additional_over_row_orbit_bounds'] += 1
            totals[n] = counts
        self.statistics['tiny'] = totals

    def test_interruptions_return_no_partial_verdict_and_do_not_mutate(self):
        demands = [2, 2, 2, 2]
        edges = [(0, 1), (0, 1), (2, 3), (2, 3)]
        class Stop(Exception):
            pass
        checks = 0
        def count():
            nonlocal checks
            checks += 1
        self.assertIsNone(component_obstruction(demands, edges, count))
        for boundary in range(1, checks+1):
            seen = 0
            def stop():
                nonlocal seen
                seen += 1
                if seen == boundary:
                    raise Stop()
            with self.assertRaises(Stop):
                component_obstruction(demands, edges, stop)
            self.assertEqual(demands, [2]*4)
            self.assertEqual(edges, [(0, 1), (0, 1), (2, 3), (2, 3)])
        self.statistics['graph_interrupt_boundaries'] = checks
        rows, orbits, mask = [1, 0, 1], orbit_map(3)['orbits'], bytearray([1])
        checks = 0
        self.assertIsNone(radius_obstruction(3, rows, orbits, mask, 1, count))
        for boundary in range(1, checks+1):
            seen = 0
            with self.assertRaises(Stop):
                radius_obstruction(3, rows, orbits, mask, 1, stop)
            self.assertEqual((rows, mask), ([1, 0, 1], bytearray([1])))
        self.statistics['mapped_interrupt_boundaries'] = checks


if __name__ == '__main__':
    unittest.main()
