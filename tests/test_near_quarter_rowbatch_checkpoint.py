"""Tiny-only phase/replay regressions for the isolated near-quarter contract."""
import hashlib
from itertools import combinations, product
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.near_quarter_rowbatch_cursor import Cursor, Domain, NONE, SINGLE, PAIR, END
from research.near_quarter_rowbatch_core import (
    TinyRowBatchCore, ACTIVE, EXHAUSTED, FOUND, ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE, ZERO)
from research import near_quarter_rowbatch_checkpoint as ck
from research.near_quarter_tiny_batches import tiny_batch_traversal

CHAIN = b'C'*32


class Stop(Exception):
    pass


def roundtrip(core, parent=ZERO):
    raw = ck.encode(core, parent_hash=parent, chain_id=CHAIN)
    record = ck.TrustedRecord(hashlib.sha256(raw).digest(), parent, CHAIN)
    return ck.loads(raw, trusted_record=record, expected_identity=ck.identity(core)), raw, record


def mutate(raw, offset, replacement):
    changed = bytearray(raw)
    changed[offset:offset+len(replacement)] = replacement
    changed[14:46] = hashlib.sha256(changed[46:]).digest()
    return bytes(changed)


def projection(core):
    return core.outer, core.slice_index, tuple(core.frames), tuple(sorted(core.counts.items())), core.state.snapshot()


class RowBatchCheckpointTests(unittest.TestCase):
    def test_cursor_exact_covers_and_large_pair_coordinates(self):
        for length in range(6):
            for weights in product((1, 2), repeat=length):
                ids = tuple(reversed(range(1, length+1)))
                for deficit, remaining in product((1, 2), range(4)):
                    domain = Domain(ids, weights, deficit, remaining)
                    expected = [(ids[i],) for i, w in enumerate(weights) if w == deficit and remaining]
                    if deficit == 2 and remaining >= 2:
                        expected += [(ids[i], ids[j]) for i, j in combinations(range(length), 2) if weights[i] == weights[j] == 1]
                    got, cursor = [], domain.first()
                    while cursor.kind != END:
                        got.append(domain.batch(cursor))
                        cursor = domain.successor(cursor)
                    self.assertEqual(got, expected)
        domain = Domain(tuple(range(1, 1522)), (1,)*1521, 2, 39)
        self.assertEqual(domain.batch(Cursor(PAIR, 1519, 1520)), (1520, 1521))
        self.assertEqual(domain.successor(Cursor(PAIR, 1519, 1520)), Cursor(END))
        self.assertGreater(1521*1520//2, 65535)
        for bad in (Cursor(NONE), Cursor(PAIR, 1, 1), Cursor(SINGLE, 0), Cursor(END, 1)):
            with self.assertRaises(ValueError):
                domain.validate(bad)
        with self.assertRaises(ValueError):
            Domain(range(1522), (1,)*1522, 2, 39)
        self.assertEqual(ck.grid_bounds(79), (39, 1521, 1560, 40))
        for n in (True, 80, 81):
            with self.assertRaises(ValueError):
                ck.grid_bounds(n)
        for n in (9, 71, 79):
            with self.assertRaises(ValueError):
                TinyRowBatchCore(n)

    def test_each_tiny_phase_roundtrips_and_leaf_sets_match_frozen_reference(self):
        phases = set()
        for n in (3, 5, 7):
            for reverse in (False, True):
                four, m = (n//2)**2, n//2
                kwargs = {} if not reverse else dict(
                    diagonal_order=tuple(reversed(range(four+1, four+m+1))),
                    orbit_order=tuple(reversed(range(1, four+1))), row_order=tuple(reversed(range(n))))
                core = TinyRowBatchCore(n, **kwargs)
                found, parent = [], ZERO
                transitions = 0
                while core.outer != EXHAUSTED:
                    before = projection(core)
                    restored, raw, record = roundtrip(core, parent)
                    self.assertEqual(projection(restored), before)
                    parent, core = record.content_sha256, restored
                    phases.update(frame.phase for frame in core.frames)
                    if core.frames and core.frames[-1].phase == LEAF:
                        found.append(tuple(sorted(core.state.selected)))
                        core.ack_leaf(core.frames[-1].leaf_digest)
                    else:
                        self.assertTrue(core.step())
                    transitions += 1
                    self.assertLess(transitions, 500)
                terminal, raw, record = roundtrip(core, parent)
                self.assertFalse(terminal.step())
                reference = tiny_batch_traversal(n, **kwargs)
                self.assertEqual(found, [tuple(v) for v in reference['unique_sets']])
                self.assertEqual(core.counts['leaves'], reference['full_leaf_visits'])
                self.assertEqual(core.counts['nodes'], reference['nodes'])
        self.assertEqual(phases, {ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE})

    def test_one_node_stages_equal_uninterrupted_and_found_event_is_idempotent(self):
        for n in (3, 5, 7):
            baseline, staged = TinyRowBatchCore(n), TinyRowBatchCore(n)
            expected, got = [], []
            baseline.run(10000, on_leaf=lambda ids, event: expected.append(ids))
            parent = ZERO
            for stage in range(50):
                before = staged.counts['nodes']
                status = staged.run(1, on_leaf=lambda ids, event: got.append(ids))
                self.assertLessEqual(staged.counts['nodes']-before, 1)
                staged, raw, record = roundtrip(staged, parent)
                parent = record.content_sha256
                if status == 'declared_slices_exhausted':
                    break
            else:
                self.fail('tiny one-node stages did not terminate')
            self.assertEqual(got, expected)
            self.assertEqual(projection(staged), projection(baseline))
        core = TinyRowBatchCore(3, leaf_mode=1)
        self.assertEqual(core.run(100), 'leaf_pending')
        for _ in range(3):
            core, raw, record = roundtrip(core)
            self.assertEqual(core.counts['leaves'], 1)
        event = core.frames[-1].leaf_digest
        core.ack_leaf(event)
        self.assertEqual(core.outer, FOUND)
        for _ in range(3):
            core, raw, record = roundtrip(core)
            before = dict(core.counts)
            core.ack_leaf(event)
            self.assertFalse(core.step())
            self.assertEqual(core.counts, before)
        with self.assertRaises(ValueError):
            core.ack_leaf(b'X'*32)

    def test_abstract_quota_pair_frontiers_resume_without_duplicate_leaves(self):
        # Explicitly synthetic row quotas, NOT an orbit-map/geometry fixture.
        incidences = ((0, 1), (0, 1), (1, 2), (1, 2), (0, 2), (0, 2), (0, 0), (1, 1), (2, 2))
        class QuotaState:
            def __init__(self):
                self.n, self.rows, self.selected = 7, [0, 0, 0, 2, 2, 2, 2], []
                self.model = {'four_count': 9, 'orbits':
                    [tuple((i, row) for i, row in enumerate(rows)) for rows in incidences]+
                    [((0, 3), (1, 3))]*3}
            @property
            def four_selected(self):
                return sum(v <= 9 for v in self.selected)
            def push(self, variable):
                if variable in self.selected:
                    return False
                if variable > 9:
                    if self.selected:
                        return False
                else:
                    rows = incidences[variable-1]
                    if self.four_selected >= 3 or any(self.rows[r]+rows.count(r) > 2 for r in range(3)):
                        return False
                    for row in rows:
                        self.rows[row] += 1
                self.selected.append(variable)
                return True
            def pop(self):
                variable = self.selected.pop()
                if variable <= 9:
                    for row in incidences[variable-1]:
                        self.rows[row] -= 1
            def full_family_leaf(self):
                return self.four_selected == 3 and self.rows == [2]*7
            def snapshot(self):
                return tuple(self.rows), tuple(self.selected)
        class QuotaCore(TinyRowBatchCore):
            def __init__(self, n, **kwargs):
                super().__init__(n, **kwargs)
                self.state = QuotaState()
                self.map_digest = self._map_digest()
        expected = {tuple(sorted((10, *chosen))) for chosen in combinations(range(1, 10), 3)
                    if all(sum(incidences[v-1].count(row) for v in chosen) == 2 for row in range(3))}
        # Dependency injection remains strictly in this test, never an input
        # option or source-identity bypass offered by the production loader.
        good = {'valid_full_witness': True}
        with patch.object(ck, 'TinyRowBatchCore', QuotaCore), \
                patch.object(ck, 'check_candidate', return_value=good), \
                patch('research.near_quarter_rowbatch_core.check_candidate', return_value=good):
            for reverse in (False, True):
                kwargs = dict(diagonal_order=(10,))
                if reverse:
                    kwargs.update(orbit_order=tuple(range(9, 0, -1)), row_order=tuple(range(6, -1, -1)))
                baseline, core = QuotaCore(7, **kwargs), QuotaCore(7, **kwargs)
                probe = QuotaCore(7, **kwargs)
                probe.step()
                unchanged = projection(probe)
                for depth in (2, 3):  # stop after first/second successful pair orbit
                    def stop_during_pair():
                        if len(probe.state.selected) >= depth:
                            raise Stop()
                    with self.assertRaises(Stop):
                        probe._push_batch((1, 2), stop_during_pair)
                    self.assertEqual(projection(probe), unchanged)
                self.assertFalse(probe._push_batch((7, 1), lambda: None))
                self.assertEqual(projection(probe), unchanged)
                real_push = probe.state.push
                def fail_second(variable):
                    if variable == 2:
                        raise Stop()
                    return real_push(variable)
                with patch.object(probe.state, 'push', side_effect=fail_second), self.assertRaises(Stop):
                    probe._push_batch((1, 2), lambda: None)
                self.assertEqual(projection(probe), unchanged)
                baseline_ids = []
                baseline.run(10000, on_leaf=lambda ids, event: baseline_ids.append(ids))
                found, pair_pending, parent = [], 0, ZERO
                for transition in range(1000):
                    core, raw, record = roundtrip(core, parent)
                    parent = record.content_sha256
                    if core.outer == EXHAUSTED:
                        break
                    if core.frames and core.frames[-1].phase == PENDING and len(core.frames[-1].pending) == 2:
                        pair_pending += 1
                    if core.frames and core.frames[-1].phase == LEAF:
                        found.append(tuple(sorted(core.state.selected)))
                        core.ack_leaf(core.frames[-1].leaf_digest)
                    else:
                        core.step()
                else:
                    self.fail('synthetic tiny quota fixture did not finish')
                self.assertGreater(pair_pending, 0)
                self.assertEqual(set(found), expected)
                self.assertEqual(len(found), len(expected))
                self.assertEqual(found, baseline_ids)
                self.assertEqual(projection(core), projection(baseline))
        self.assertEqual(len(expected), 12)

    def test_strict_envelope_identity_parent_chain_and_phase_corruption(self):
        core = TinyRowBatchCore(3)
        while not (core.frames and core.frames[-1].phase == ENTER and len(core.frames) == 2):
            core.step()
        restored, raw, record = roundtrip(core)
        manifest = ck.identity(core)
        with patch.object(ck, '_identity_shape', side_effect=AssertionError('parsed before external hash')):
            with self.assertRaisesRegex(ValueError, 'external content'):
                ck.loads(raw, trusted_record=ck.TrustedRecord(b'X'*32, ZERO, CHAIN), expected_identity=manifest)
        for wrong in (ck.TrustedRecord(record.content_sha256, b'P'*32, CHAIN),
                      ck.TrustedRecord(record.content_sha256, ZERO, b'Q'*32)):
            with self.assertRaisesRegex(ValueError, 'parent/chain'):
                ck.loads(raw, trusted_record=wrong, expected_identity=manifest)
        base = 46+704+2*(len(core.diagonals)+len(core.orbits)+len(core.rows))
        cases = [mutate(raw, 46+576+10, b'\xff\xff'),  # excessive frames
                 mutate(raw, base+96+7, b'\x00\x01'),  # invalid child origin
                 mutate(raw, base+96+11, b'\x00\x01'),  # inactive ENTER row
                 mutate(raw, base+91, b'\x01'),        # reserved frame bytes
                 mutate(raw, 46+15, b'\x01')]
        for broken in cases:
            trusted = ck.TrustedRecord(hashlib.sha256(broken).digest(), ZERO, CHAIN)
            with self.assertRaises(ValueError):
                ck.loads(broken, trusted_record=trusted, expected_identity=manifest)
        with self.assertRaises(ValueError):
            ck.parse(raw+b'x', trusted_record=record, expected_identity=manifest)
        with self.assertRaises(ValueError):
            ck.parse(bytes(ck.MAX_WIRE_BYTES+1), trusted_record=record, expected_identity=manifest)

    def test_live_path_event_counters_and_geometry_must_be_coherent(self):
        core = TinyRowBatchCore(3)
        while not (len(core.frames) == 2 and core.frames[-1].phase == ENTER):
            core.step()
        loaded, raw, record = roundtrip(core)
        # A live child needs one committed accepted batch, not a rejection.
        broken = mutate(raw, 46+576+36, struct.pack('>Q', core.counts['attempts']))
        with self.assertRaisesRegex(ValueError, 'counter relationship'):
            ck.loads(broken, trusted_record=ck.TrustedRecord(hashlib.sha256(broken).digest(), ZERO, CHAIN),
                     expected_identity=ck.identity(core))
        core.run(100)
        self.assertEqual(core.frames[-1].phase, LEAF)
        core.ack_leaf(core.frames[-1].leaf_digest)
        loaded, raw, record = roundtrip(core)
        broken = mutate(raw, 46+576+20, bytes(8))
        with self.assertRaisesRegex(ValueError, 'active event counter'):
            ck.loads(broken, trusted_record=ck.TrustedRecord(hashlib.sha256(broken).digest(), ZERO, CHAIN),
                     expected_identity=ck.identity(core))
        # Actual reachable prune closures also require their named counter.
        pruned = TinyRowBatchCore(5)
        while not (pruned.frames and pruned.frames[-1].phase == DONE):
            pruned.step()
        reason = pruned.frames[-1].close_reason
        counter_index = {ck.ORBIT_SHORTFALL: 4, ck.ROW_SHORTFALL: 5, ck.TARGET_NONLEAF: 6}[reason]
        loaded, raw, record = roundtrip(pruned)
        broken = mutate(raw, 46+576+12+8*counter_index, bytes(8))
        with self.assertRaisesRegex(ValueError, 'active event counter'):
            ck.loads(broken, trusted_record=ck.TrustedRecord(hashlib.sha256(broken).digest(), ZERO, CHAIN),
                     expected_identity=ck.identity(pruned))
        with tempfile.TemporaryDirectory() as directory:
            with ck.ChainLease(directory, expected_parent=ZERO, chain_id=CHAIN) as lease:
                for field, index in (('rows', 0), ('blocked', 0), ('selected', 0)):
                    corrupt = TinyRowBatchCore(3)
                    corrupt.step()
                    values = getattr(corrupt.state, field)
                    values[index] += 1
                    with self.assertRaisesRegex(ValueError, 'live geometry/frontier'):
                        ck.save_candidate(corrupt, lease=lease)
                    self.assertEqual(list(Path(directory).glob('*.nqrb')), [])

    def test_cancellation_at_every_replay_check_never_adopts_partial_core(self):
        core = TinyRowBatchCore(7)
        while not (core.frames and len(core.frames) >= 2):
            core.step()
        restored, raw, record = roundtrip(core)
        old = projection(core)
        calls = [0]
        def count():
            calls[0] += 1
        ck.loads(raw, trusted_record=record, expected_identity=ck.identity(core), check=count)
        total = calls[0]
        self.assertGreater(total, 10)
        for boundary in range(1, total+1):
            current = [0]
            def stop():
                current[0] += 1
                if current[0] == boundary:
                    raise Stop()
            with self.assertRaises(Stop):
                ck.loads(raw, trusted_record=record, expected_identity=ck.identity(core), check=stop)
            self.assertEqual(projection(core), old)

    def test_cursor_and_pending_interruption_preserve_frontier(self):
        domain = Domain((3, 2, 1), (1, 1, 1), 2, 3)
        cursor = domain.first()
        with self.assertRaises(Stop):
            domain.successor(cursor, lambda: (_ for _ in ()).throw(Stop()))
        self.assertEqual(cursor, Cursor(PAIR, 0, 1))
        core = TinyRowBatchCore(3)
        while not (core.frames and core.frames[-1].phase == PENDING):
            core.step()
        old = projection(core)
        real_push = core.state.push
        def expire_after_push(variable):
            accepted = real_push(variable)
            expired[0] = True
            return accepted
        expired = [False]
        def check():
            if expired[0]:
                raise Stop()
        with patch.object(core.state, 'push', side_effect=expire_after_push), self.assertRaises(Stop):
            core.step(check=check)
        self.assertEqual(projection(core), old)

    def test_immutable_save_lease_and_publication_faults(self):
        core = TinyRowBatchCore(3)
        core.step()
        with tempfile.TemporaryDirectory() as directory:
            lease = ck.ChainLease(directory, expected_parent=ZERO, chain_id=CHAIN)
            with lease:
                with self.assertRaises(FileExistsError):
                    with ck.ChainLease(directory, expected_parent=ZERO, chain_id=CHAIN):
                        pass
                path, record = ck.save_candidate(core, lease=lease)
                original = path.read_bytes()
                again, same = ck.save_candidate(core, lease=lease)
                self.assertEqual((again, same), (path, record))
                loaded = ck.read_checkpoint(path, trusted_record=record, expected_identity=ck.identity(core))
                self.assertEqual(projection(loaded), projection(core))
                for boundary in ('after_write', 'after_file_fsync', 'after_link', 'after_directory_fsync', 'after_temp_unlink'):
                    def fail(where):
                        if where == boundary:
                            raise Stop()
                    with self.assertRaises(Stop):
                        ck.save_candidate(core, lease=lease, fault=fail)
                    self.assertEqual(path.read_bytes(), original)
                self.assertEqual(list(Path(directory).glob('.candidate-*')), [])
            self.assertFalse((Path(directory)/'writer.lease').exists())
            stale = Path(directory)/'writer.lease'
            stale.write_bytes(b'stale')
            with self.assertRaises(FileExistsError):
                with ck.ChainLease(directory, expected_parent=ZERO, chain_id=CHAIN):
                    pass
            self.assertEqual(stale.read_bytes(), b'stale')


if __name__ == '__main__':
    unittest.main()
