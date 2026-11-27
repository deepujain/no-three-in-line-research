"""Exact tiny oracle and interruption faults; no broad-grid instantiation."""
from itertools import combinations, product
import hashlib
import struct
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import near_quarter_packed_state as packed
from research.near_quarter_tiny_secants import TinyOrbitState
from src.near_quarter_model import orbit_map, expand, check_candidate
from src.verify import collinear_triples_bruteforce
from tests.test_near_quarter_tiny_secants import reference_counts, admissible_subset

EVIDENCE = {}


def build(n, ids=()):
    state = packed.PackedOrbitState(n)
    for variable in ids:
        if not state.push(variable):
            raise AssertionError(('invalid test prefix', n, ids, variable))
    return state


def geometry(state):
    return state.snapshot()[:10]


def valid_cases():
    # Enumerate only the4/64/4096 tiny subsets, not a production traversal.
    for n in (3, 5, 7):
        model = orbit_map(n)
        for bits in product((False, True), repeat=len(model['orbits'])):
            ids = tuple(v for v, bit in enumerate(bits, 1) if bit)
            if admissible_subset(model, ids):
                yield n, model, ids


class PackedStateTests(unittest.TestCase):
    def assert_geometry(self, state, reference=None):
        points, n = state.points, state.n
        self.assertEqual(list(state.blocked), reference_counts(points, n))
        self.assertEqual(list(state.rows), [sum(y == row for x, y in points) for row in range(n)])
        self.assertEqual(list(state.columns), [sum(x == col for x, y in points) for col in range(n)])
        self.assertEqual(sum(state.occupied), len(points))
        self.assertEqual(set(state.selected), set(range(1, state.bounds['orbits']+1)) & set(state.selected))
        self.assertTrue(all(v <= 2 for v in (*state.rows, *state.columns)))
        self.assertLessEqual(max(state.blocked), len(points)*(len(points)-1)//2)
        self.assertTrue(all(v == 0 for v in state._point_cells[state._point_count:]))
        self.assertTrue(all(v == 0 for v in state._selected_ids[state._selected_count:]))
        self.assertTrue(state.assert_checkpointable())
        if reference is not None:
            self.assertEqual(points, tuple(reference.points))
            self.assertEqual(state.selected, tuple(reference.selected))
            self.assertEqual(state.blocked, reference.blocked)
            self.assertEqual(state.rows, reference.rows)
            self.assertEqual(state.columns, reference.columns)
            self.assertEqual(state.occupied, reference.occupied)
            self.assertEqual(state.four_selected, reference.four_selected)
            self.assertEqual(state.diagonal_selected, reference.diagonal_selected)

    def test_bounds_before_allocation_and_exact_ordered_map(self):
        with patch.object(packed.PackedOrbitState, '_build_model', side_effect=AssertionError('allocated')):
            for n in (True, False, 1, 2, 80, 81, 10000000, None, 3.0):
                with self.assertRaises(ValueError):
                    packed.PackedOrbitState(n)
        with patch.object(packed, 'array') as wrong_width:
            wrong_width.return_value.itemsize = 4
            with self.assertRaisesRegex(ValueError, 'two-byte'):
                packed.PackedOrbitState(3)
        bounds = packed.packed_bounds(79)  # Arithmetic only, no model or geometry.
        self.assertEqual(bounds, {'m': 39, 'four': 1521, 'diagonal': 39, 'orbits': 1560,
            'incidences': 6162, 'cells': 6241, 'points': 158, 'selected': 40, 'pair_count': 12403})
        for n in (3, 5, 7):
            state = build(n)
            frozen = orbit_map(n)
            self.assertEqual(list(state.model['orbits']), frozen['orbits'])
            raw_map = struct.pack('>HH', n, len(frozen['orbits']))
            for orbit in frozen['orbits']:
                raw_map += bytes((len(orbit),))+b''.join(struct.pack('>HH', x, y) for x, y in orbit)
            self.assertEqual(state.map_digest, hashlib.sha256(b'NQRB-MAP-v1\0'+raw_map).digest())
            self.assertEqual(state.model['orbits'][-1], frozen['orbits'][-1])
            self.assertNotIn('point_to_var', state.model)
            self.assertEqual(state._orbit_offsets[-1], len(state._orbit_cells))
            with self.assertRaises(TypeError):
                state.model['orbits'][True]
            with self.assertRaises(IndexError):
                state.model['orbits'][len(state.model['orbits'])]
            for variable in (0, True, None, len(frozen['orbits'])+1):
                with self.assertRaises(ValueError):
                    state.push(variable)
            with self.assertRaises(ValueError):
                state.pop()
            self.assert_geometry(state)
        EVIDENCE['n79_arithmetic_only'] = bounds

    def test_every_tiny_grid_line_matches_integer_determinants(self):
        pairs = 0
        for n in (3, 5, 7):
            for a, b in combinations(range(n*n), 2):
                ax, ay, bx, by = a % n, a//n, b % n, b//n
                expected = {y*n+x for y in range(n) for x in range(n)
                    if (bx-ax)*(y-ay) == (by-ay)*(x-ax)}
                for first, second in ((a, b), (b, a)):
                    start, step, length = packed.line_span(first, second, n)
                    self.assertEqual({start+i*step for i in range(length)}, expected)
                    self.assertLessEqual(length, n)
                pairs += 1
        EVIDENCE['unordered_tiny_grid_pairs'] = pairs

    def test_every_tiny_subset_extension_and_full_undo_matches_frozen_and_determinants(self):
        census = {}
        for n in (3, 5, 7):
            model = orbit_map(n)
            valid = full = extensions = 0
            for bits in product((False, True), repeat=len(model['orbits'])):
                ids = tuple(v for v, bit in enumerate(bits, 1) if bit)
                state, reference = build(n), TinyOrbitState(n)
                empty = state.snapshot()
                accepted = True
                for variable in ids:
                    before = state.snapshot()
                    got, expected = state.push(variable), reference.push(variable)
                    self.assertIs(got, expected)
                    if not got:
                        self.assertEqual(state.snapshot(), before)
                        accepted = False
                        break
                self.assertIs(accepted, admissible_subset(model, ids))
                self.assert_geometry(state, reference)
                if accepted:
                    valid += 1
                    full += state.full_family_leaf()
                    if state.full_family_leaf():
                        self.assertTrue(check_candidate(state.model, state.selected)['valid_full_witness'])
                    for variable in range(1, len(model['orbits'])+1):
                        before = state.snapshot()
                        got, expected = state.push(variable), reference.push(variable)
                        extensions += 1
                        self.assertIs(got, expected)
                        self.assertIs(got, variable not in ids and admissible_subset(model, (*ids, variable)))
                        self.assert_geometry(state, reference)
                        if got:
                            state.pop()
                            reference.pop()
                        self.assertEqual(state.snapshot(), before)
                while state.selected:
                    state.pop()
                    reference.pop()
                    self.assert_geometry(state, reference)
                self.assertEqual(state.snapshot(), empty)
            census[n] = {'subsets': 2**len(model['orbits']), 'valid_partial_subsets': valid,
                         'full_family_subsets': full, 'extension_attempts': extensions}
        self.assertEqual([census[n]['valid_partial_subsets'] for n in (3, 5, 7)], [4, 17, 100])
        self.assertEqual([census[n]['full_family_subsets'] for n in (3, 5, 7)], [1, 0, 0])
        self.assertEqual([census[n]['extension_attempts'] for n in (3, 5, 7)], [8, 102, 1200])
        EVIDENCE['tiny_census'] = census

    def test_every_construction_budget_boundary_discards_private_state(self):
        count = [0]
        def counting():
            count[0] += 1
        packed.PackedOrbitState(7, check=counting)
        for boundary in range(1, count[0]+1):
            calls = [0]
            def stop():
                calls[0] += 1
                if calls[0] == boundary:
                    raise packed.PackedStop()
            with self.assertRaises(packed.PackedStop):
                packed.PackedOrbitState(7, check=stop)
        EVIDENCE['construction_stop_boundaries_n7'] = count[0]

    def test_stop_at_every_checked_point_update_and_orbit_commit_boundary(self):
        # Automatically select successful representatives with secant work at
        # each grid and both orbit sizes; no representative exceeds tiny n7.
        representatives = []
        for n in (3, 5, 7):
            found = {}
            for grid, model, ids in valid_cases():
                if grid != n:
                    continue
                for variable in range(1, len(model['orbits'])+1):
                    kind = variable <= model['four_count']
                    if kind in found or not ids or variable in ids:
                        continue
                    state = build(n, ids)
                    if state.push(variable):
                        found[kind] = (n, ids, variable)
                if len(found) == 2:
                    break
            self.assertEqual(len(found), 2)
            representatives.extend(found.values())
        injected, stages = 0, set()
        for n, ids, variable in representatives:
            probe = build(n, ids)
            count = [0]
            def counting():
                count[0] += 1
                if probe._progress is not None:
                    stages.add(probe._progress.stage)
                if probe._orbit_phase == packed.ORBIT_COMMIT:
                    stages.add(packed.ORBIT_COMMIT)
            probe.bind_check(counting)
            self.assertTrue(probe.push(variable))
            for boundary in range(1, count[0]+1):
                state = build(n, ids)
                before, calls = state.snapshot(), [0]
                def stop():
                    calls[0] += 1
                    if calls[0] >= boundary:  # Sticky deadline during inverse.
                        raise packed.PackedStop('injected update stop')
                state.bind_check(stop)
                with self.assertRaises(packed.PackedStop):
                    state.push(variable)
                self.assertEqual(state.snapshot(), before)
                state.bind_check(lambda: None)
                self.assertTrue(state.push(variable))
                state.pop()
                self.assertEqual(state.snapshot(), before)
                injected += 1
        self.assertEqual(stages, {packed.POINT_PRECHECK, packed.LINE_BUILD, packed.CELL_UPDATE,
                                  packed.POINT_COMMIT, packed.ORBIT_COMMIT})
        EVIDENCE['point_orbit_stop_boundaries'] = injected
        EVIDENCE['successful_representatives'] = [[n, list(ids), v] for n, ids, v in representatives]

    def test_pop_latches_stops_and_rollback_works_with_already_expired_budget(self):
        tests = 0
        for n, model, ids in valid_cases():
            if not ids:
                continue
            state = build(n, ids)
            parent = build(n, ids[:-1]).snapshot()
            polls = [0]
            def expired_during_inverse():
                if state._operation == packed.POP:
                    polls[0] += 1
                    raise packed.PackedStop('inverse stop')
            state.bind_check(expired_during_inverse)
            state.pop()
            self.assertGreater(polls[0], 0)
            self.assertEqual(geometry(state), parent[:10])
            self.assertTrue(state.stop_latched)
            self.assertFalse(state.poisoned)
            with self.assertRaises(packed.PackedStop):
                state.assert_checkpointable()
            with self.assertRaises(packed.PackedStop):
                state.raise_latched()
            self.assertEqual(state.snapshot(), parent)
            state.bind_check(lambda: (_ for _ in ()).throw(packed.PackedStop('already expired')))
            if state.selected:
                # Explicit owner rollback can drain more than one orbit while
                # preserving a stop for later propagation after frame commit.
                while state.selected:
                    state.rollback_last_orbit()
                self.assertTrue(state.stop_latched)
                with self.assertRaises(packed.PackedStop):
                    state.raise_latched()
                self.assertEqual(state.snapshot(), build(n).snapshot())
            tests += 1
        EVIDENCE['valid_partial_pop_stop_cases'] = tests

    def test_overflow_underflow_and_inverse_poll_fault_poison_without_continuation(self):
        state = build(3)
        def overflow():
            progress = state._progress
            if progress is not None and progress.stage == packed.CELL_UPDATE:
                state.blocked[progress.line_start+progress.next_cell*progress.line_step] = 65535
        state.bind_check(overflow)
        with self.assertRaisesRegex(packed.PackedStateError, 'overflow'):
            state.push(1)
        self.assertTrue(state.poisoned)
        for operation in (lambda: state.push(1), state.pop, state.assert_checkpointable):
            with self.assertRaises(packed.PackedStateError):
                operation()
        state = build(3, (1,))
        first, second = state._point_cells[state._point_count-1], state._point_cells[0]
        start, step, length = packed.line_span(first, second, 3)
        def underflow():
            if state._operation == packed.POP:
                state.blocked[start] = 0
        state.bind_check(underflow)
        with self.assertRaisesRegex(packed.PackedStateError, 'underflow'):
            state.pop()
        self.assertTrue(state.poisoned)
        with self.assertRaises(packed.PackedStateError):
            state.assert_checkpointable()
        state = build(3, (1,))
        parent = build(3).snapshot()
        def inverse_fault():
            if state._operation == packed.POP:
                raise RuntimeError('unexpected poll exception')
        state.bind_check(inverse_fault)
        with self.assertRaisesRegex(packed.PackedStateError, 'inverse polling'):
            state.pop()
        self.assertEqual(geometry(state), parent[:10])
        self.assertTrue(state.poisoned)
        with self.assertRaises(packed.PackedStateError):
            state.assert_checkpointable()
        EVIDENCE['fatal_faults'] = ['increment overflow', 'inverse underflow', 'unexpected inverse polling exception']

    def test_point_rollback_inverse_failure_is_poisoned_and_never_retried(self):
        state = build(3)
        target = [None]
        def inverse_underflow():
            progress = state._progress
            if progress is not None and progress.next_cell:
                target[0] = progress.line_start+(progress.next_cell-1)*progress.line_step
                state.blocked[target[0]] = 0
                raise packed.PackedStop('force incomplete-point inverse')
        state.bind_check(inverse_underflow)
        original = state._decrement
        attempts = [0]
        def count_decrement(cell):
            attempts[0] += 1
            return original(cell)
        with patch.object(state, '_decrement', side_effect=count_decrement):
            with self.assertRaisesRegex(packed.PackedStateError, 'underflow'):
                state.push(1)
        self.assertIsNotNone(target[0])
        self.assertEqual(attempts[0], 1)
        self.assertTrue(state.poisoned)
        self.assertTrue(state._inverse_failed)
        with self.assertRaises(packed.PackedStateError):
            state.assert_checkpointable()
        state = build(3)
        parent = state.snapshot()
        def before_mutation_exception():
            progress = state._progress
            if progress is not None and progress.stage == packed.CELL_UPDATE:
                raise RuntimeError('injected forward exception before update')
        state.bind_check(before_mutation_exception)
        with self.assertRaisesRegex(RuntimeError, 'before update'):
            state.push(1)
        self.assertEqual(geometry(state), parent[:10])
        self.assertTrue(state.poisoned)
        with self.assertRaises(packed.PackedStateError):
            state.push(1)
        state = build(3)
        state.work['orbit_attempts'] = packed.MAX_U64
        with self.assertRaisesRegex(packed.PackedStateError, 'physical counter'):
            state.push(1)
        self.assertTrue(state.poisoned)
        EVIDENCE['extra_fatal_faults'] = ['incomplete-point inverse fails once without retry',
            'forward exception restores geometry and poisons', 'physical work counter overflow']

    def test_two_orbit_owner_transactions_restore_after_second_stop_or_rejection(self):
        transactions = stops = rejected = 0
        for n, model, ids in valid_cases():
            for first, second in combinations(range(1, len(model['orbits'])+1), 2):
                if first in ids or second in ids:
                    continue
                state = build(n, ids)
                before = state.snapshot()
                if not state.push(first):
                    continue
                child = state.snapshot()
                def expired():
                    raise packed.PackedStop('second orbit stop')
                state.bind_check(expired)
                with self.assertRaises(packed.PackedStop):
                    state.push(second)
                self.assertEqual(state.snapshot(), child)
                state.rollback_last_orbit()
                with self.assertRaises(packed.PackedStop):
                    state.raise_latched()
                self.assertEqual(state.snapshot(), before)
                stops += 1
                state.bind_check(lambda: None)
                self.assertTrue(state.push(first))
                expected = second not in state.selected and admissible_subset(model, (*state.selected, second))
                accepted = state.push(second)
                self.assertIs(accepted, expected)
                if accepted:
                    state.pop()
                else:
                    rejected += 1
                state.pop()
                self.assertEqual(state.snapshot(), before)
                transactions += 1
        self.assertGreater(rejected, 0)
        EVIDENCE['owner_pair_transactions'] = transactions
        EVIDENCE['owner_pair_second_stops'] = stops
        EVIDENCE['owner_pair_second_rejections'] = rejected


if __name__ == '__main__':
    unittest.main()
