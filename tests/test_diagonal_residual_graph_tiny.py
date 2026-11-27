"""Independent tiny all-subset completion oracle for residual graph bounds."""
from collections import Counter
from itertools import combinations, product
import unittest
from unittest.mock import patch

from research import diagonal_residual_graph_tiny as residual
from research.diagonal_rowbatch_tiny import census as frozen_census
from research.diagonal_secant_dfs_fast import SecantState
from src.verify import verify_certificate, verify_certificate_bruteforce

EVIDENCE = {}


class Stop(Exception):
    pass


def determinant_valid(points):
    return all((b[0]-a[0])*(c[1]-a[1]) != (b[1]-a[1])*(c[0]-a[0])
               for a, b, c in combinations(points, 3))


def admissible(points, n, deficit):
    return (len(points) == len(set(points)) and determinant_valid(points) and
            all(sum(y == r for x, y in points) <= 2-(r == deficit) and
                sum(x == r for x, y in points) <= 2-(r == deficit) for r in range(n)))


def snapshot(state):
    return (tuple(state.points), frozenset(state.occupied), tuple(state.rows),
            tuple(state.columns), tuple(state.blocked), tuple(state.frames))


def all_prefix_audit(n):
    # The oracle does not call either the new predicate or the frozen orbit
    # builder to enumerate points, validity, or full-superset existence.
    edges = tuple(combinations(range(n), 2))
    orbits = tuple(((a, b), (b, a)) for a, b in edges)
    statistics = Counter()
    rules = Counter()
    extra = Counter()
    examples = {}
    certificate_hashes = set()
    for deficit, diagonal in product(range(n), repeat=2):
        valid = {}
        for mask in range(1 << len(orbits)):
            statistics['raw_subsets'] += 1
            points = ((diagonal, diagonal),)+tuple(
                point for i, orbit in enumerate(orbits) if mask & (1 << i) for point in orbit)
            if admissible(points, n, deficit):
                valid[mask] = points
        full = {mask: points for mask, points in valid.items() if len(points) == 2*n-1}
        for points in full.values():
            cert = {'n': n, 'points': [list(p) for p in points]}
            proofs = (verify_certificate(cert), verify_certificate_bruteforce(cert))
            assert all(p['valid'] and p['point_count'] == 2*n-1 for p in proofs)
            assert proofs[0]['normalized_sha256'] == proofs[1]['normalized_sha256']
            certificate_hashes.add(proofs[0]['normalized_sha256'])
        for mask, points in valid.items():
            statistics['valid_partial_states'] += 1
            full_supersets = [candidate for candidate in full if mask & candidate == mask]
            statistics['extendible_states'] += bool(full_supersets)
            expected_edges = tuple(edge for i, edge in enumerate(edges)
                if not mask & (1 << i) and admissible(points+orbits[i], n, deficit))
            state = SecantState(n, deficit)
            assert state.push(((diagonal, diagonal),))
            for i, orbit in enumerate(orbits):
                if mask & (1 << i):
                    assert state.push(orbit)
            before = snapshot(state)
            assessment = residual.scan(state)
            assert snapshot(state) == before
            assert assessment.edges == expected_edges
            needs = tuple(2-(r == deficit)-sum(y == r for x, y in points) for r in range(n))
            assert assessment.needs == needs
            assert not (assessment.rejected and full_supersets), (n, deficit, diagonal, mask)
            if not any(needs):
                assert not assessment.rejected
            if assessment.rejected:
                statistics['rejected_states'] += 1
                rules.update(assessment.violations)
                row_choices = [(sum(r in edge for edge in expected_edges), r, need)
                               for r, need in enumerate(needs) if need]
                size, row, need = min(row_choices)
                if size >= need:
                    statistics['rejects_before_frozen_empty_domain'] += 1
                    extra.update(assessment.violations)
                    for rule in assessment.violations:
                        examples.setdefault(rule, {'deficit': deficit, 'diagonal': diagonal,
                            'selected_orbit_indices': [i for i in range(len(orbits)) if mask & (1 << i)],
                            'needs': list(needs), 'admissible_edges': [list(e) for e in expected_edges]})
    return {'n': n, **dict(statistics), 'rule_hits': {r: rules[r] for r in residual.RULES},
            'extra_rule_hits': {r: extra[r] for r in residual.RULES},
            'extra_examples': examples, 'full_certificate_hashes': sorted(certificate_hashes)}


def factor_demands(n, edges, *, distinct_colors):
    possible = set()
    for mask in range(1 << len(edges)):
        degrees, colors = [0]*n, set()
        valid = True
        for i, (a, b) in enumerate(edges):
            if mask & (1 << i):
                if distinct_colors and a+b in colors:
                    valid = False
                    break
                colors.add(a+b)
                degrees[a] += 1
                degrees[b] += 1
        if valid and max(degrees) <= 2:
            possible.add(tuple(degrees))
    return possible


class ResidualGraphTests(unittest.TestCase):
    def test_all_geometry_prefixes_and_all_completion_supersets_n2_through_n5(self):
        reports = [all_prefix_audit(n) for n in range(2, 6)]
        self.assertEqual([r['raw_subsets'] for r in reports], [8, 72, 1024, 25600])
        self.assertEqual([len(r['full_certificate_hashes']) for r in reports], [2, 4, 10, 16])
        EVIDENCE['all_prefix_oracle'] = reports

    def test_exhaustive_abstract_graphs_and_demands_n2_through_n4(self):
        cases = factors = colorful = 0
        for n in range(2, 5):
            complete = tuple(combinations(range(n), 2))
            for mask in range(1 << len(complete)):
                edges = tuple(e for i, e in enumerate(complete) if mask & (1 << i))
                ordinary = factor_demands(n, edges, distinct_colors=False)
                rainbow = factor_demands(n, edges, distinct_colors=True)
                for needs in product(range(3), repeat=n):
                    if sum(needs) % 2:
                        continue
                    result = residual.assess(needs, edges)
                    graph_failures = set(result.violations) & set(residual.RULES[:3])
                    if needs in ordinary:
                        self.assertFalse(graph_failures)
                        factors += 1
                    if needs in rainbow:
                        self.assertFalse(result.rejected)
                        colorful += 1
                    cases += 1
        EVIDENCE['abstract_oracle'] = {'grids': [2, 3, 4], 'graph_demand_cases': cases,
            'ordinary_feasible_cases': factors, 'distinct_color_feasible_cases': colorful}

    def test_strictness_isolated_vertices_duplicates_and_shared_colors(self):
        # Even demand, enough degree, but bipartite side demands 2 != 4.
        result = residual.assess((1, 1, 1, 1, 2), [(a, b) for a in (0, 1) for b in (2, 3, 4)])
        self.assertEqual(result.violations, ('bipartite_imbalance',))
        # Enough degree, even component and balanced sides; only three colors
        # available for four required edges.
        result = residual.assess((2, 2, 2, 2), [(a, b) for a in (0, 1) for b in (2, 3)])
        self.assertEqual(result.violations, ('global_color_shortage', 'component_color_shortage'))
        isolated = residual.assess((1, 1, 0), [])
        self.assertIn('component_parity', isolated.violations)
        self.assertIn('row_shortage', isolated.violations)
        duplicate = residual.assess((2, 2), [(0, 1), (1, 0)])
        self.assertEqual(duplicate.edges, ((0, 1),))
        self.assertIn('row_shortage', duplicate.violations)
        shared = residual.assess((1, 1, 1, 1), [(0, 3), (1, 2)])
        self.assertEqual(shared.violations, ('global_color_shortage',))
        self.assertFalse(residual.assess((2, 2, 2), [(0, 1), (0, 2), (1, 2)]).rejected)
        self.assertFalse(residual.assess((0, 0, 0), [(0, 1)]).rejected)
        self.assertEqual(residual.assess((1, 1, 0), [(2, 0), (1, 0), (0, 1)]).edges, ((0, 1),))

    def test_every_interruption_boundary_returns_no_partial_verdict(self):
        total = 0
        for deficit in range(5):
            state = SecantState(5, deficit)
            self.assertTrue(state.push(((0, 0),)))
            before = snapshot(state)
            calls = [0]
            def counting():
                calls[0] += 1
            expected = residual.scan(state, check=counting)
            for boundary in range(1, calls[0]+1):
                ticks = [0]
                def stop():
                    ticks[0] += 1
                    if ticks[0] == boundary:
                        raise Stop()
                with self.assertRaises(Stop):
                    residual.scan(state, check=stop)
                self.assertEqual(snapshot(state), before)
                total += 1
            self.assertEqual(residual.scan(state), expected)
        EVIDENCE['interrupted_complete_scan_boundaries'] = total

    def test_tiny_bounds_and_malformed_graphs(self):
        with patch.object(residual, 'pair_orbits', side_effect=AssertionError('allocated')):
            for n in (1, 6, 79, True):
                with self.assertRaises(ValueError):
                    residual.census(n)
        for needs, edges in [((1,), []), ((1,)*6, []), ((1, 0), []), ((True, 1), []),
                             ((3, 1), []), ((1, 1), [(0, 0)]), ((1, 1), [(0, 2)]),
                             ((1, 1), [(True, 1)]), ((1, 1), [(0, 1)]*3)]:
            with self.assertRaises(ValueError):
                residual.assess(needs, edges)
        with self.assertRaises(ValueError):
            residual.census(3, use_bounds=1)

    def test_integrated_tiny_survivor_order_matches_frozen_reference(self):
        reports = []
        for n in range(2, 6):
            expected = []
            def collect(cert):
                proof = verify_certificate(cert)
                expected.append((cert['metadata']['deficit'], cert['metadata']['diagonal'],
                                 proof['normalized_sha256']))
            frozen = frozen_census(n, on_witness=collect)
            unpruned = residual.census(n, use_bounds=False)
            pruned = residual.census(n)
            self.assertEqual(unpruned['nodes'], frozen['nodes'])
            self.assertEqual(unpruned['witnesses'], expected)
            self.assertEqual(pruned['witnesses'], expected)
            self.assertLessEqual(pruned['nodes'], unpruned['nodes'])
            reports.append({'n': n, 'unpruned_nodes': unpruned['nodes'],
                'pruned_nodes': pruned['nodes'], 'witnesses': len(expected), 'rule_hits': pruned['rule_hits']})
        EVIDENCE['tiny_traversal_equivalence'] = reports


if __name__ == '__main__':
    unittest.main()
