"""Read-only packed scanner versus actual mutating admission, tiny only."""
import copy
import unittest
from unittest.mock import patch

from research import near_quarter_rowbatch_core as cm
from research.near_quarter_readonly_probe import probe_orbit
from research.near_quarter_packed_state import PackedStop


def mutating_query(state, variable, check):
    state.bind_check(check)
    if not state.push(variable):
        return False
    state.rollback_last_orbit()
    state.raise_latched()
    return True


def domain_projection(result):
    reason, row, domain = result
    return reason, row, None if domain is None else (domain.ids, domain.weights, domain.deficit, domain.remaining)


def projection(core):
    return (core.outer, core.slice_index, tuple(core.frames), dict(core.counts), core.state.snapshot())


class ReadonlyIntegrationTests(unittest.TestCase):
    statistics = {}

    def test_all_tiny_prefix_masks_histograms_and_order_match_mutating_admission(self):
        checked = 0
        for n in (3, 5, 7):
            m, four = n//2, (n//2)**2
            for d in range(four+1, four+m+1):
                for bits in range(1 << four):
                    chosen = [v+1 for v in range(four) if bits & (1 << v)]
                    if len(chosen) >= m:
                        continue
                    core = cm.PackedRowBatchCore(n)
                    if not all(core.state.push(v) for v in (d, *chosen)):
                        continue
                    checked += 1
                    before, work = core.state.snapshot(), dict(core.state.work)
                    actual = domain_projection(core._scan(lambda: None))
                    self.assertEqual((core.state.snapshot(), core.state.work), (before, work))
                    with patch.object(cm, 'probe_orbit', side_effect=mutating_query):
                        expected = domain_projection(core._scan(lambda: None))
                    self.assertEqual(core.state.snapshot(), before)
                    self.assertEqual(actual, expected)
        self.assertEqual(checked, 73)
        self.statistics['coherent_prefix_scans'] = checked

    def test_every_forward_reverse_tiny_frontier_and_counters_match(self):
        census = []
        def trace(n, reverse, legacy):
            m, four = n//2, (n//2)**2
            kwargs = {} if not reverse else {
                'diagonal_order': tuple(range(four+m, four, -1)),
                'orbit_order': tuple(range(four, 0, -1)), 'row_order': tuple(range(n-1, -1, -1))}
            core = cm.PackedRowBatchCore(n, **kwargs)
            history = []
            while True:
                history.append(projection(core))
                if core.outer in (cm.EXHAUSTED, cm.FOUND):
                    break
                if core.frames and core.frames[-1].phase == cm.LEAF:
                    core.ack_leaf(core.frames[-1].leaf_digest)
                elif legacy:
                    with patch.object(cm, 'probe_orbit', side_effect=mutating_query):
                        core.step()
                else:
                    core.step()
            return core, history
        for n in (3, 5, 7):
            for reverse in (False, True):
                actual, history = trace(n, reverse, False)
                expected, old_history = trace(n, reverse, True)
                self.assertEqual(history, old_history)
                self.assertEqual(actual.work, expected.work)
                self.assertLess(actual.state.work['cell_increments'], expected.state.work['cell_increments'])
                census.append({'n': n, 'reverse': reverse, 'frontiers': len(history),
                    'nodes': actual.counts['nodes'], 'domain_probes': actual.work['domain_probes'],
                    'mutating_probe_increments': expected.state.work['cell_increments'],
                    'readonly_probe_increments': actual.state.work['cell_increments']})
        self.statistics['traversals'] = census

    def test_each_integrated_query_stop_preserves_frontier_geometry_and_mutation_work(self):
        template = cm.PackedRowBatchCore(7)
        template.step()
        template.step()
        checks = 0
        def counted(state, variable, check):
            def count():
                nonlocal checks
                checks += 1
                check()
            return probe_orbit(state, variable, count)
        with patch.object(cm, 'probe_orbit', side_effect=counted):
            completed = copy.deepcopy(template)
            completed.step()
        for boundary in range(1, checks+1):
            core = copy.deepcopy(template)
            before, work = projection(core), dict(core.state.work)
            seen = 0
            def stopped(state, variable, check):
                def stop():
                    nonlocal seen
                    seen += 1
                    if seen == boundary:
                        raise PackedStop('query budget')
                    check()
                return probe_orbit(state, variable, stop)
            with patch.object(cm, 'probe_orbit', side_effect=stopped):
                with self.assertRaises(PackedStop):
                    core.step()
            self.assertEqual((projection(core), core.state.work), (before, work))
            self.assertEqual(core.work['interrupted_scans'], 1)
        with patch.object(cm, 'READONLY_SOURCE_SHA', b'x'*32):
            with self.assertRaisesRegex(ValueError, 'read-only helper source'):
                template.check_sources()
        self.statistics['integrated_query_stop_boundaries'] = checks


if __name__ == '__main__':
    unittest.main()
