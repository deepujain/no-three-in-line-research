"""Exhaustive tiny admission equivalence; no core hook or broad-grid state."""
import random
import unittest
from unittest.mock import patch

from research.near_quarter_readonly_probe import probe_orbit, _probe_cells
from research.near_quarter_packed_state import PackedOrbitState, PackedStop, PackedStateError
from src.near_quarter_model import orbit_map
from src.verify import verify_certificate_bruteforce


class ReadonlyProbeTests(unittest.TestCase):
    statistics = {}

    def test_every_tiny_coherent_subset_candidate_matches_push_and_determinants(self):
        census = {}
        representatives = {}
        for n in (3, 5, 7):
            model = orbit_map(n)
            total = len(model['orbits'])
            valid = attempts = admitted = 0
            for bits in range(1 << total):
                state = PackedOrbitState(n)
                chosen = [v+1 for v in range(total) if bits & (1 << v)]
                if not all(state.push(v) for v in chosen):
                    continue
                valid += 1
                for variable in range(1, total+1):
                    attempts += 1
                    before, work = state.snapshot(), dict(state.work)
                    observed = probe_orbit(state, variable)
                    self.assertEqual((state.snapshot(), state.work), (before, work))
                    actual = state.push(variable)
                    self.assertEqual(observed, actual)
                    if actual:
                        admitted += 1
                        state.pop()
                    self.assertEqual(state.snapshot(), before)
                    four = variable <= state.bounds['four']
                    eligible = (variable not in chosen and
                        (state.four_selected < state.bounds['m'] if four else state.diagonal_selected < 1))
                    if eligible:
                        points = [list(p) for v in (*chosen, variable) for p in model['orbits'][v-1]]
                        axis = all(sum(y == r for x, y in points) <= 2 and
                                   sum(x == r for x, y in points) <= 2 for r in range(n))
                        expected = axis and verify_certificate_bruteforce({'n': n, 'points': points})['valid']
                    else:
                        expected = False
                    self.assertEqual(observed, expected)
                    representatives.setdefault((n, observed), (tuple(chosen), variable))
            census[n] = {'valid_subsets': valid, 'candidate_checks': attempts, 'admitted': admitted}
        self.statistics['exhaustive'] = census
        self.__class__.representatives = representatives

    def test_seeded_random_insertion_orders_and_repeated_candidates(self):
        rng = random.Random(790026)
        checked = 0
        for n in (3, 5, 7):
            for _ in range(40):
                state = PackedOrbitState(n)
                order = list(range(1, state.bounds['orbits']+1))
                rng.shuffle(order)
                for variable in order:
                    before = state.snapshot()
                    result = probe_orbit(state, variable)
                    self.assertEqual(result, state.push(variable))
                    if result:
                        self.assertFalse(probe_orbit(state, variable))
                        if rng.randrange(2):
                            state.pop()
                            self.assertEqual(state.snapshot(), before)
                    checked += 1
        self.statistics['random_order_checks'] = checked

    def test_explicit_axes_and_triple_partition_cases(self):
        state = PackedOrbitState(5)
        self.assertTrue(state.push(5))  # (0,0),(4,4).
        def check(cells, expected):
            before, work = state.snapshot(), dict(state.work)
            self.assertEqual(_probe_cells(state, cells, lambda: None), expected)
            self.assertEqual((state.snapshot(), state.work), (before, work))
        check((1, 2), False)  # Existing row0 load1 +2new.
        check((5, 10), False)  # Existing column0 load1 +2new.
        check((12,), False)  # Two-old/one-new on diagonal.
        check((11, 22), False)  # (1,2),(2,4) with old(0,0).
        check((7, 7), False)  # Duplicate cells before line construction.
        with patch('research.near_quarter_readonly_probe.line_span', side_effect=AssertionError('equal endpoints')):
            check((7, 7), False)
        empty = PackedOrbitState(5)
        self.assertFalse(_probe_cells(empty, (0, 6, 12), lambda: None))  # Three-new diagonal.
        self.assertTrue(_probe_cells(empty, (1, 10), lambda: None))
        self.assertFalse(probe_orbit(state, 6))  # Second diagonal family cap.
        for value in (True, 0, state.bounds['orbits']+1):
            with self.assertRaises(ValueError):
                probe_orbit(state, value)

    def test_every_query_budget_boundary_preserves_snapshot_and_work(self):
        boundaries = 0
        for n, chosen, variable in ((3, (2,), 1), (5, (5,), 4), (7, (10,), 8)):
            state = PackedOrbitState(n)
            for v in chosen:
                self.assertTrue(state.push(v))
            count = 0
            def tally():
                nonlocal count
                count += 1
            probe_orbit(state, variable, tally)
            before, work = state.snapshot(), dict(state.work)
            for boundary in range(1, count+1):
                seen = 0
                def stop():
                    nonlocal seen
                    seen += 1
                    if seen == boundary:
                        raise PackedStop('read-only budget')
                with self.assertRaises(PackedStop):
                    probe_orbit(state, variable, stop)
                self.assertEqual((state.snapshot(), state.work), (before, work))
            boundaries += count
        self.statistics['interruption_boundaries'] = boundaries
        bad = PackedOrbitState(3)
        bad._poisoned = True
        with self.assertRaises(PackedStateError):
            probe_orbit(bad, 1)
        bad = PackedOrbitState(3)
        bad._latched_stop = PackedStop('latched')
        with self.assertRaises(PackedStop):
            probe_orbit(bad, 1)


if __name__ == '__main__':
    unittest.main()
