"""Focused complete-mask/policy integration; actual geometry n3/n5/n7 only."""
import copy
import hashlib
from itertools import combinations
import unittest
from unittest.mock import patch

from research import near_quarter_rowbatch_core as core_module
from research import near_quarter_rowbatch_checkpoint as codec
from research.near_quarter_packed_state import PackedStop
from research.near_quarter_radius_graph import radius_obstruction
from src.near_quarter_model import orbit_map
from src.verify import verify_certificate_bruteforce


class RadiusIntegrationTests(unittest.TestCase):
    statistics = {}

    def test_complete_mask_hook_preserves_passing_mrv_order_and_geometry(self):
        checked = new_rejections = hook_calls = 0
        for n in (3, 5, 7):
            model, m = orbit_map(n), n//2
            four = m*m
            completions = []
            for d in range(four+1, four+m+1):
                for ids in combinations(range(1, four+1), m):
                    selected = frozenset((d, *ids))
                    points = [list(p) for v in selected for p in model['orbits'][v-1]]
                    if verify_certificate_bruteforce({'n': n, 'points': points})['valid']:
                        completions.append(selected)
            for d in range(four+1, four+m+1):
                for bits in range(1 << four):
                    chosen = [v+1 for v in range(four) if bits & (1 << v)]
                    if len(chosen) >= m:
                        continue
                    core = core_module.PackedRowBatchCore(n)
                    if not all(core.state.push(v) for v in (d, *chosen)):
                        continue
                    checked += 1
                    snapshot = core.state.snapshot()
                    expected_mask = bytearray(four)
                    for v in core.orbits:
                        if v not in core.state.selected and core.state.push(v):
                            expected_mask[v-1] = 1
                            core.state.pop()
                    self.assertEqual(core.state.snapshot(), snapshot)
                    with patch.object(core_module, 'radius_obstruction', return_value=None):
                        old_reason, old_row, old_domain = core._scan(lambda: None)
                    def hook(n, rows, orbits, mask, remaining, check):
                        nonlocal hook_calls
                        hook_calls += 1
                        self.assertEqual(bytes(mask), bytes(expected_mask))
                        self.assertEqual(core.state.snapshot(), snapshot)
                        return radius_obstruction(n, rows, orbits, mask, remaining, check)
                    with patch.object(core_module, 'radius_obstruction', side_effect=hook):
                        reason, row, domain = core._scan(lambda: None)
                    self.assertEqual(core.state.snapshot(), snapshot)
                    if reason == core_module.RADIUS_SHORTFALL:
                        new_rejections += 1
                        self.assertEqual(old_reason, 0)
                        prefix = frozenset((d, *chosen))
                        self.assertFalse(any(prefix <= completion for completion in completions))
                    else:
                        self.assertEqual((reason, row), (old_reason, old_row))
                        if domain is not None:
                            self.assertEqual((domain.ids, domain.weights, domain.deficit, domain.remaining),
                                (old_domain.ids, old_domain.weights, old_domain.deficit, old_domain.remaining))
        self.statistics.update(prefixes=checked, hook_calls=hook_calls, new_rejections=new_rejections)
        self.assertEqual((checked, new_rejections), (73, 8))

    def test_graph_budget_stop_preserves_counted_frontier_and_no_prune_commit(self):
        template = core_module.PackedRowBatchCore(5, diagonal_order=(6,))
        template.step()
        template.step()
        self.assertEqual(template.frames[-1].phase, core_module.COUNTED)
        calls = 0
        def count():
            nonlocal calls
            calls += 1
        def counted_hook(n, rows, orbits, mask, remaining, check):
            return radius_obstruction(n, rows, orbits, mask, remaining, count)
        with patch.object(core_module, 'radius_obstruction', side_effect=counted_hook):
            finished = copy.deepcopy(template)
            finished.step()
        self.assertEqual(finished.frames[-1].close_reason, core_module.RADIUS_SHORTFALL)
        for boundary in range(1, calls+1):
            core = copy.deepcopy(template)
            old = (core.state.snapshot(), tuple(core.frames), dict(core.counts))
            seen = 0
            def stop():
                nonlocal seen
                seen += 1
                if seen == boundary:
                    raise PackedStop('graph budget')
            def stopped_hook(n, rows, orbits, mask, remaining, check):
                return radius_obstruction(n, rows, orbits, mask, remaining, stop)
            with patch.object(core_module, 'radius_obstruction', side_effect=stopped_hook):
                with self.assertRaises(PackedStop):
                    core.step()
            self.assertEqual((core.state.snapshot(), tuple(core.frames), core.counts), old)
            self.assertEqual(core.work['interrupted_scans'], 1)
        self.statistics['pruning_hook_stop_boundaries'] = calls

    def test_policy_source_binding_and_radius_frame_private_replay(self):
        core = core_module.PackedRowBatchCore(5, diagonal_order=(6,))
        for _ in range(3):
            core.step()
        self.assertEqual(core.frames[-1].close_reason, core_module.RADIUS_SHORTFALL)
        self.assertEqual(core.counts['orbit_prunes'], 1)
        manifest = codec.identity(core)
        self.assertEqual(manifest[12], 2)
        self.assertEqual(codec.identity(core_module.TinyRowBatchCore(3))[12], 1)
        old_policy = bytearray(manifest)
        old_policy[12] = 1
        with self.assertRaises(ValueError):
            codec._identity_shape(bytes(old_policy))
        chain = b'r'*32
        raw = codec.encode(core, parent_hash=bytes(32), chain_id=chain)
        record = codec.TrustedRecord(hashlib.sha256(raw).digest(), bytes(32), chain)
        replayed = codec.loads(raw, trusted_record=record, expected_identity=manifest)
        self.assertEqual((replayed.frames, replayed.counts, replayed.state.snapshot()),
                         (core.frames, core.counts, core.state.snapshot()))
        with patch.object(core_module, 'RADIUS_SOURCE_SHA', b'x'*32):
            with self.assertRaisesRegex(ValueError, 'radius helper source'):
                core.check_sources()


if __name__ == '__main__':
    unittest.main()
