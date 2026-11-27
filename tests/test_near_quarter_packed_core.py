"""Adapter2 integration: tiny equivalence and coherent cancellation only."""
import copy
import hashlib
from itertools import combinations
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.near_quarter_rowbatch_core import (
    TinyRowBatchCore, PackedRowBatchCore, BETWEEN, ACTIVE, EXHAUSTED, FOUND,
    ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE, ZERO)
from research import near_quarter_rowbatch_checkpoint as ck
from research.near_quarter_packed_state import PackedStop, PackedStateError, POP
from tests.test_near_quarter_rowbatch_checkpoint import mutate

CHAIN = b'P'*32
EVIDENCE = {}


def snapshot(core):
    return (core.outer, core.slice_index, tuple(core.frames), tuple(sorted(core.counts.items())), core.state.snapshot())


def math_snapshot(core):
    s = core.state
    return (core.outer, core.slice_index, tuple(core.frames), tuple(sorted(core.counts.items())),
            tuple(s.selected), tuple(s.points), s.blocked.tobytes(), bytes(s.occupied), bytes(s.rows), bytes(s.columns))


def encode(core, parent=ZERO):
    raw = ck.encode(core, parent_hash=parent, chain_id=CHAIN)
    return raw, ck.TrustedRecord(hashlib.sha256(raw).digest(), parent, CHAIN)


def restore(raw, record, manifest, check=lambda: None):
    return ck.loads(raw, trusted_record=record, expected_identity=manifest, check=check)


def all_frontiers(n):
    core = PackedRowBatchCore(n)
    while True:
        raw, record = encode(core)
        yield core, raw, record
        if core.outer in (EXHAUSTED, FOUND):
            return
        if core.frames and core.frames[-1].phase == LEAF:
            core.ack_leaf(core.frames[-1].leaf_digest)
        else:
            core.step()


class PackedCoreTests(unittest.TestCase):
    def test_adapter2_tiny_every_phase_and_one_node_resume_equals_adapter1_oracle(self):
        census, phases, pair_frames = [], set(), 0
        for n in (3, 5, 7):
            for reverse in (False, True):
                m, four = n//2, (n//2)**2
                kwargs = {} if not reverse else dict(diagonal_order=tuple(range(four+m, four, -1)),
                    orbit_order=tuple(range(four, 0, -1)), row_order=tuple(range(n-1, -1, -1)))
                tiny, core = TinyRowBatchCore(n, leaf_mode=1, **kwargs), PackedRowBatchCore(n, **kwargs)
                parent, leaves = ZERO, []
                while True:
                    before = snapshot(core)
                    raw, record = encode(core, parent)
                    manifest = ck.identity(core)
                    self.assertEqual(manifest[9:11], b'\x02\x01')
                    core = restore(raw, record, manifest)
                    self.assertEqual(snapshot(core), before)
                    self.assertEqual(math_snapshot(core), math_snapshot(tiny))
                    parent = record.content_sha256
                    phases.update(frame.phase for frame in core.frames)
                    pair_frames += sum(len(frame.incoming) == 2 for frame in core.frames)
                    if core.outer in (EXHAUSTED, FOUND):
                        self.assertFalse(core.step())
                        break
                    if core.frames and core.frames[-1].phase == LEAF:
                        leaves.append(tuple(sorted(core.state.selected)))
                        core.ack_leaf(core.frames[-1].leaf_digest)
                        tiny.ack_leaf(tiny.frames[-1].leaf_digest)
                    else:
                        core.step()
                        tiny.step()
                self.assertEqual(len(leaves), int(n == 3))
                self.assertEqual(core.counts['nodes'], {3: 2, 5: 5, 7: 11}[n])
                staged = PackedRowBatchCore(n, **kwargs)
                staged_leaves = []
                for stage in range(50):
                    before_nodes = staged.counts['nodes']
                    status = staged.run(1, on_leaf=lambda ids, event: staged_leaves.append(ids))
                    self.assertLessEqual(staged.counts['nodes']-before_nodes, 1)
                    raw, record = encode(staged)
                    staged = restore(raw, record, ck.identity(staged))
                    if status in ('found', 'declared_slices_exhausted'):
                        break
                else:
                    self.fail('tiny adapter2 stage loop did not finish')
                self.assertEqual(snapshot(staged), snapshot(core))
                self.assertEqual(staged_leaves, leaves)
                if n == 3:
                    event = core.frames[-1].leaf_digest
                    for _ in range(3):
                        core.ack_leaf(event)
                        self.assertFalse(core.step())
                        self.assertEqual(core.counts['leaves'], 1)
                census.append({'n': n, 'reverse': reverse, 'nodes': core.counts['nodes'],
                               'leaves': len(leaves), 'outer': core.outer})
        self.assertEqual(phases, {ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE})
        EVIDENCE['tiny_adapter_equivalence'] = census
        EVIDENCE['reachable_two_orbit_incoming_frame_occurrences'] = pair_frames

    def test_stop_at_every_representative_step_check_keeps_old_or_committed_frontier(self):
        representatives = {}
        for n in (3, 5, 7):
            for core, raw, record in all_frontiers(n):
                if core.outer in (EXHAUSTED, FOUND):
                    continue
                phase = core.frames[-1].phase if core.frames else BETWEEN+10
                key = (phase, len(core.frames[-1].incoming) if core.frames else 0)
                representatives.setdefault(key, (raw, record, ck.identity(core)))
        boundaries, changed = 0, 0
        for raw, record, manifest in representatives.values():
            template = restore(raw, record, manifest)
            baseline = copy.deepcopy(template)
            old = snapshot(baseline)
            count = [0]
            def counting():
                count[0] += 1
            baseline.step(check=counting)
            committed = snapshot(baseline)
            saved, authority = encode(baseline)
            self.assertEqual(snapshot(restore(saved, authority, ck.identity(baseline))), committed)
            for boundary in range(1, count[0]+1):
                core = copy.deepcopy(template)
                calls = [0]
                def sticky_stop():
                    calls[0] += 1
                    if calls[0] >= boundary:
                        raise PackedStop('step stop')
                with self.assertRaises(PackedStop):
                    core.step(check=sticky_stop)
                self.assertTrue(core.state.assert_checkpointable())
                after = snapshot(core)
                self.assertIn(after, (old, committed))
                changed += after != old
                # Full snapshot equals one of two already roundtripped valid
                # frontiers; avoid redundant file/source replay per fault.
                boundaries += 1
        self.assertGreater(changed, 0)  # Stop during pop propagated AFTER frame commit.
        EVIDENCE['step_stop_boundaries'] = boundaries
        EVIDENCE['step_stops_after_coherent_pop_commit'] = changed

    def test_restore_stop_at_every_checked_boundary_adopts_no_partial_frontier(self):
        core = PackedRowBatchCore(3)
        while len(core.frames) < 2:
            core.step()
        old = snapshot(core)
        raw, record = encode(core)
        manifest, calls = ck.identity(core), [0]
        def counting():
            calls[0] += 1
        restored = restore(raw, record, manifest, counting)
        self.assertGreater(restored.work['restore_probes'], 0)
        self.assertGreater(restored.restore_work['cell_increments'], 0)
        for boundary in range(1, calls[0]+1):
            seen = [0]
            def stop():
                seen[0] += 1
                if seen[0] >= boundary:
                    raise PackedStop('restore stop')
            with self.assertRaises(PackedStop):
                restore(raw, record, manifest, stop)
            self.assertEqual(snapshot(core), old)
        EVIDENCE['restore_stop_boundaries'] = calls[0]

    def test_owner_pair_cleanup_handles_expired_budget_and_pending_stop(self):
        core = PackedRowBatchCore(7)
        core.step()
        old = snapshot(core)
        accepted_pair = rejected_pair = None
        for pair in combinations(core.orbits, 2):
            if not core.state.push(pair[0]):
                continue
            if core.state.push(pair[1]):
                core.state.pop()
                accepted_pair = accepted_pair or pair
            else:
                rejected_pair = rejected_pair or pair
            core.state.pop()
            if accepted_pair and rejected_pair:
                break
        self.assertIsNotNone(accepted_pair)
        self.assertIsNotNone(rejected_pair)
        base = len(core.state.selected)
        for depth in (base+1, base+2):
            def after_orbit():
                if len(core.state.selected) >= depth:
                    raise PackedStop('pair accepted orbit stop')
            with self.assertRaises(PackedStop):
                core._push_batch(accepted_pair, after_orbit)
            self.assertEqual(snapshot(core), old)
        def on_owner_inverse():
            if core.state._operation == POP:
                raise PackedStop('rejected pair owner undo stop')
        with self.assertRaises(PackedStop):
            core._push_batch(rejected_pair, on_owner_inverse)
        self.assertEqual(snapshot(core), old)
        self.assertTrue(core.state.assert_checkpointable())
        EVIDENCE['accepted_pair'] = list(accepted_pair)
        EVIDENCE['rejected_pair'] = list(rejected_pair)

    def test_closed_adapter_source_map_poison_latch_and_save_faults(self):
        with patch('research.near_quarter_rowbatch_core.PackedOrbitState', side_effect=AssertionError('allocated')):
            for n, mode in ((80, 1), (True, 1), (3, 2), (3, True)):
                with self.assertRaises(ValueError):
                    PackedRowBatchCore(n, leaf_mode=mode)
        core = PackedRowBatchCore(3)
        core.step()
        raw, record = encode(core)
        manifest = ck.identity(core)
        self.assertNotEqual(manifest, ck.identity(TinyRowBatchCore(3, leaf_mode=1)))
        broken = mutate(raw, 46+10, b'\x02')
        with self.assertRaises(ValueError):
            restore(broken, ck.TrustedRecord(hashlib.sha256(broken).digest(), ZERO, CHAIN), bytes(broken[46:558]))
        with self.assertRaises(ValueError):
            restore(raw, record, ck.identity(TinyRowBatchCore(3, leaf_mode=1)))
        with tempfile.TemporaryDirectory() as directory:
            with ck.ChainLease(directory, expected_parent=ZERO, chain_id=CHAIN) as lease:
                path, authority = ck.save_candidate(core, lease=lease)
                original = path.read_bytes()
                self.assertGreater(core.validation_work['cell_increments'], 0)
                self.assertEqual(snapshot(ck.read_checkpoint(path, trusted_record=authority,
                    expected_identity=manifest)), snapshot(core))
                for boundary in ('after_write', 'after_file_fsync', 'after_link', 'after_directory_fsync', 'after_temp_unlink'):
                    def fail(where):
                        if where == boundary:
                            raise PackedStop('save fault')
                    with self.assertRaises(PackedStop):
                        ck.save_candidate(core, lease=lease, fault=fail)
                    self.assertEqual(path.read_bytes(), original)
                for field in ('blocked', 'rows', '_point_cells'):
                    corrupt = PackedRowBatchCore(3)
                    corrupt.step()
                    getattr(corrupt.state, field)[0] += 1
                    with self.assertRaisesRegex(ValueError, 'live geometry/frontier'):
                        ck.save_candidate(corrupt, lease=lease)
                corrupt = PackedRowBatchCore(3)
                corrupt.state._orbit_cells[0] = (corrupt.state._orbit_cells[0]+1) % 9
                with self.assertRaisesRegex(ValueError, 'map identity'):
                    ck.save_candidate(corrupt, lease=lease)
                corrupt = PackedRowBatchCore(3)
                corrupt.state._poisoned = True
                with self.assertRaises(PackedStateError):
                    ck.save_candidate(corrupt, lease=lease)
                corrupt = PackedRowBatchCore(3)
                corrupt.step()
                def inverse_stop():
                    if corrupt.state._operation == POP:
                        raise PackedStop()
                corrupt.state.bind_check(inverse_stop)
                corrupt.state.pop()
                with self.assertRaises(PackedStop):
                    ck.save_candidate(corrupt, lease=lease)
                self.assertEqual(path.read_bytes(), original)
        EVIDENCE['save_fault_boundaries'] = 5


if __name__ == '__main__':
    unittest.main()
