from collections import Counter
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import score11_connected_paths_flow_census as m


class FlowCensusTests(unittest.TestCase):
    def test_all_small_flows_against_exhaustive_subsets(self):
        rectangle = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for mask in range(16):
            cells = {p for i, p in enumerate(rectangle) if mask >> i & 1}
            for caps in itertools.product(range(3), repeat=4):
                rows, cols = dict(enumerate(caps[:2])), dict(enumerate(caps[2:]))
                expected = 0
                for size in range(len(cells) + 1):
                    for selected in itertools.combinations(cells, size):
                        rc = Counter(x for x, y in selected)
                        cc = Counter(y for x, y in selected)
                        if all(rc[x] <= rows[x] for x in rows) and all(cc[y] <= cols[y] for y in cols):
                            expected = max(expected, size)
                cert = m.maximum_axis_flow(cells, rows, cols)
                self.assertEqual(cert['flow_value'], expected)
                self.assertEqual(m.verify_flow_certificate(cells, rows, cols, cert), expected)

    def test_reverse_residual_augmentation_and_corrupt_certificates(self):
        cells = {(0, 0), (0, 1), (1, 0)}
        rows = cols = {0: 1, 1: 1}
        cert = m.maximum_axis_flow(cells, rows, cols)
        self.assertEqual(cert['flow_value'], 2)
        self.assertEqual(set(map(tuple, cert['selected_cells'])), {(0, 1), (1, 0)})
        for key, value in [('flow_value', 1), ('cut_capacity', 1), ('selected_cells', [[0, 0], [0, 1]])]:
            altered = {**cert, key: value}
            with self.assertRaises(ValueError):
                m.verify_flow_certificate(cells, rows, cols, altered)

    def test_source_incidence_manifest_only_without_geometry(self):
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        manifest = m.load_manifest(points)
        self.assertEqual(Counter(c['length'] for c in manifest['cases']), {10: 8, 12: 10, 16: 14})
        self.assertEqual(sum(c['candidate_cells'] for c in manifest['cases']), 1668)
        for case in manifest['cases']:
            deleted = set(map(tuple, case['deleted']))
            self.assertEqual(dict(case['row_capacities']), Counter(x for x, y in deleted))
            self.assertEqual(dict(case['column_capacities']), Counter(y for x, y in deleted))
            self.assertEqual(case['insertions_for_157'], case['length'] - 1)

    def test_tiny_safe_cell_filter_against_integer_determinants(self):
        retained = {(0, 0), (1, 3), (2, 1), (3, 4)}
        for p in itertools.product(range(5), repeat=2):
            if p in retained:
                continue
            blocked = any((a[0] - p[0]) * (b[1] - p[1]) == (a[1] - p[1]) * (b[0] - p[0])
                          for a, b in itertools.combinations(retained, 2))
            self.assertEqual(bool(m.point_conflicts(p, retained)), blocked)

    def test_deadline_and_flow_timeout_accounting_with_mock_geometry(self):
        with self.assertRaises(TimeoutError):
            m.maximum_axis_flow({(0, 0)}, {0: 1}, {0: 1}, 1, lambda: 1)
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        from research.score11_connected_path8 import COVER
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(m, 'load_source', return_value=(points, [COVER])), patch.object(m, 'point_conflicts', return_value=0), patch.object(m, 'maximum_axis_flow', side_effect=TimeoutError):
                report = m.run(Path('unused'), Path(directory), 1, clock=lambda: 0)
        self.assertEqual(report['status'], 'timeout')
        self.assertFalse(report['complete'])
        self.assertEqual(report['case_completed'], 0)
        self.assertEqual((report['cell_checks_started'], report['cell_checks_completed']), (30, 30))
        self.assertEqual(report['cases'][0]['status'], 'partial_flow')
        self.assertEqual(len(report['cases'][0]['safe_cells']), 30)
        self.assertTrue(all(c['status'] == 'unstarted' for c in report['cases'][1:]))

    def test_interrupted_cell_is_not_completed(self):
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        from research.score11_connected_path8 import COVER
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(m, 'load_source', return_value=(points, [COVER])), patch.object(m, 'point_conflicts', side_effect=TimeoutError):
                report = m.run(Path('unused'), Path(directory), 1, clock=lambda: 0)
        self.assertEqual(report['cases'][0]['status'], 'partial_safe_census')
        self.assertEqual((report['cell_checks_started'], report['cell_checks_completed']), (1, 0))

    def test_complete_bound_classifications_with_mock_safe_census(self):
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        from research.score11_connected_path8 import COVER
        for mocked_conflicts, eligible in ((0, 32), (1, 0)):
            with tempfile.TemporaryDirectory() as directory:
                with patch.object(m, 'load_source', return_value=(points, [COVER])), patch.object(m, 'point_conflicts', return_value=mocked_conflicts):
                    report = m.run(Path('unused'), Path(directory), 1, clock=lambda: 0)
            self.assertTrue(report['complete'])
            self.assertEqual(report['case_completed'], 32)
            self.assertEqual((report['cell_checks_started'], report['cell_checks_completed']), (1668, 1668))
            self.assertEqual(report['eligible_cases'], eligible)
            self.assertEqual(report['closed_cases'], 32 - eligible)
            self.assertTrue(all(c['status'] == 'complete' for c in report['cases']))
            if eligible:
                self.assertTrue(all(c['final_cardinality_upper_bound'] == 158 for c in report['cases']))

    def test_prevalidation_timeout_and_changed_evidence(self):
        ticks = iter((0, 2, 3))
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'load_source') as source:
            report = m.run(Path('unused'), Path(directory), 1, clock=lambda: next(ticks))
            source.assert_not_called()
            self.assertEqual(report['status'], 'timeout')
            self.assertEqual(len(report['cases']), 32)
            self.assertTrue(all(c['status'] == 'unstarted' for c in report['cases']))
        with patch.dict(m.PINS, {m.MANIFEST: '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'pinned evidence changed'):
                m.load_manifest(set())


if __name__ == '__main__':
    unittest.main()
