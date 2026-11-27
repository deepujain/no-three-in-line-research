"""Tiny replay equivalence, exact physical reduction and retained validation."""
import hashlib
import struct
import unittest
from unittest.mock import patch

from research import near_quarter_rowbatch_checkpoint as codec
from research.near_quarter_rowbatch_core import (
    PackedRowBatchCore, EXHAUSTED, FOUND, ENTER, LEAF, ZERO)
from research.near_quarter_packed_state import PackedStop
from tests.test_near_quarter_rowbatch_checkpoint import mutate

CHAIN = b'u'*32


def frontiers(n):
    core = PackedRowBatchCore(n)
    while True:
        raw = codec.encode(core, parent_hash=ZERO, chain_id=CHAIN)
        yield core, raw, codec.TrustedRecord(hashlib.sha256(raw).digest(), ZERO, CHAIN)
        if core.outer in (EXHAUSTED, FOUND):
            return
        if core.frames and core.frames[-1].phase == LEAF:
            core.ack_leaf(core.frames[-1].leaf_digest)
        else:
            core.step()


def projection(core):
    return (core.outer, core.slice_index, tuple(core.frames), dict(core.counts), core.state.snapshot())


def replay(raw, record, identity, *, redundant=False, check=lambda: None):
    """Repeat-scan mode restores the former discarded parent-domain rebuild.

    It reuses the same full private replay plus a full _domain check at each
    unchanged parent geometry immediately before the actual child push.
    """
    calls = []
    original_scan, original_push = PackedRowBatchCore._scan, PackedRowBatchCore._push_batch
    parsed = codec.parse(raw, trusted_record=record, expected_identity=identity)
    incoming = 0
    def scan(core, check):
        before = dict(core.state.work)
        start_probes = core.work['restore_probes']
        result = original_scan(core, check)
        calls.append({'selected': tuple(core.state.selected),
            'work': {k: core.state.work[k]-before[k] for k in before},
            'probes': core.work['restore_probes']-start_probes})
        return result
    def push(core, batch, check):
        nonlocal incoming
        if redundant:
            core._domain(parsed.frames[incoming], check)
        incoming += 1
        return original_push(core, batch, check)
    with patch.object(PackedRowBatchCore, '_scan', new=scan):
        with patch.object(PackedRowBatchCore, '_push_batch', new=push):
            core = codec.loads(raw, trusted_record=record, expected_identity=identity, check=check)
    return core, calls


class ReplayReuseTests(unittest.TestCase):
    statistics = {}

    def test_all_tiny_frontiers_repeat_scan_equivalence_and_exact_work_reduction(self):
        frames = checks = saved_scans = saved_probes = 0
        phases = set()
        representatives = {}
        for n in (3, 5, 7):
            for live, raw, record in frontiers(n):
                manifest = codec.identity(live)
                optimized, calls = replay(raw, record, manifest)
                repeated, old_calls = replay(raw, record, manifest, redundant=True)
                self.assertEqual(projection(optimized), projection(live))
                self.assertEqual(projection(optimized), projection(repeated))
                ancestors = max(0, len(live.frames)-1)
                self.assertEqual(len(old_calls)-len(calls), ancestors)
                duplicate_calls = old_calls[1::2][:ancestors]
                # Interior WAITING scans appear as validate,repeat pairs before
                # any possible terminal/top scan, in the same declared order.
                for key in optimized.state.work:
                    expected = sum(call['work'][key] for call in duplicate_calls)
                    self.assertEqual(repeated.state.work[key]-optimized.state.work[key], expected)
                expected_probes = sum(call['probes'] for call in duplicate_calls)
                self.assertEqual(repeated.work['restore_probes']-optimized.work['restore_probes'], expected_probes)
                saved_scans += ancestors
                saved_probes += expected_probes
                checks += 1
                phases.update(frame.phase for frame in live.frames)
                if live.frames:
                    representatives.setdefault(live.frames[-1].phase, (raw, record, manifest))
                    frames = max(frames, len(live.frames))
        self.assertEqual(phases, set(range(1, 8)))
        self.assertGreater(saved_scans, 0)
        self.statistics.update(frontiers=checks, max_tiny_frames=frames,
                               saved_scans=saved_scans, saved_probes=saved_probes)
        self.__class__.representatives = representatives

    def test_every_replay_boundary_discards_private_state(self):
        chosen = next((raw, record, codec.identity(core)) for core, raw, record in frontiers(3)
                      if len(core.frames) == 2 and core.frames[-1].phase == ENTER)
        raw, record, manifest = chosen
        boundaries = 0
        def count():
            nonlocal boundaries
            boundaries += 1
        baseline, _ = replay(raw, record, manifest, check=count)
        for boundary in range(1, boundaries+1):
            seen = 0
            adopted = []
            def stop():
                nonlocal seen
                seen += 1
                if seen == boundary:
                    raise PackedStop('replay budget')
            with self.assertRaises(PackedStop):
                adopted.append(codec.loads(raw, trusted_record=record, expected_identity=manifest, check=stop))
            self.assertEqual(adopted, [])
        self.statistics['interruption_boundaries'] = boundaries
        self.assertEqual(baseline.counts['nodes'], 1)

    def test_bad_domain_origin_and_successor_still_reject(self):
        live, raw, record = next((core, raw, record) for core, raw, record in frontiers(7)
                                if len(core.frames) == 2 and core.frames[-1].phase == ENTER)
        parsed = codec.parse(raw, trusted_record=record, expected_identity=codec.identity(live))
        base = 46+704+2*(len(parsed.diagonals)+len(parsed.orbits)+len(parsed.rows))
        cases = {'domain_digest': (mutate(raw, base+16, b'x'*32), 'reconstructed domain mismatch'),
                 'domain_length': (mutate(raw, base+14, struct.pack('>H', parsed.frames[0].domain_length+1)), 'reconstructed domain mismatch'),
                 'origin': (mutate(raw, base+96+6, struct.pack('>BHH', 1, 1520, 0)), 'noncanonical cursor'),
                 'successor': (mutate(raw, base+48, struct.pack('>BHH', 1, 0, 0)), 'parent-child committed cursor mismatch')}
        for name, (changed, message) in cases.items():
            changed_record = codec.TrustedRecord(hashlib.sha256(changed).digest(), ZERO, CHAIN)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, message):
                    codec.loads(changed, trusted_record=changed_record, expected_identity=codec.identity(live))
        self.statistics['malformed_replay_cases'] = list(cases)


if __name__ == '__main__':
    unittest.main()
