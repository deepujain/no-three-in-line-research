from collections import Counter
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import score11_connected_path8 as m
from src.verify import verify_certificate_bruteforce


class ConnectedPathTests(unittest.TestCase):
    def test_quota_generator_against_all_small_binary_matrices(self):
        for deleted in ({(0, 0), (0, 1), (1, 1), (1, 2)},
                        {(0, 0), (1, 0), (1, 1), (2, 1)}):
            cells = list(itertools.product(sorted({x for x, y in deleted}), sorted({y for x, y in deleted})))
            rows = Counter(x for x, y in deleted)
            cols = Counter(y for x, y in deleted)
            for size in (len(deleted), len(deleted) - 1):
                expected = set()
                for factor in itertools.combinations(cells, size):
                    rc = Counter(x for x, y in factor)
                    cc = Counter(y for x, y in factor)
                    if all(rc[x] <= rows[x] for x in rc) and all(cc[y] <= cols[y] for y in cc):
                        expected.add(frozenset(factor))
                result = list(m.quota_factors(deleted, size))
                self.assertEqual(set(result), expected)
                self.assertEqual(len(result), len(expected))

    def test_six_paths_and_approved_quota_histograms_without_geometry(self):
        manifest = m.load_evidence()
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        cycles, paths = m.connected_paths(points)
        self.assertEqual(sorted(map(len, cycles)), [4, 12, 142])
        cases = manifest['eight_edge_paths']['deletion_cases']
        self.assertEqual(paths, {frozenset(map(tuple, c['deleted'])) for c in cases})
        saw_nonextendable = False
        for case in cases:
            deleted = frozenset(map(tuple, case['deleted']))
            full = set(m.quota_factors(deleted, 8))
            partial = set(m.quota_factors(deleted, 7))
            for size, factors, name in ((8, full, 'full158'), (7, partial, 'partial157')):
                expected = manifest['eight_edge_paths'][name + '_quota_factors_by_effective_deletions']
                self.assertEqual(Counter(len(deleted - f) for f in factors), Counter({int(k): v for k, v in expected.items()}))
            from_full = {f - {p} for f in full for p in f}
            self.assertTrue(from_full <= partial)
            saw_nonextendable |= bool(partial - from_full)
        self.assertTrue(saw_nonextendable)

    def test_geometry_classes_against_tiny_bruteforce(self):
        retained = {(0, 0), (1, 2), (2, 1)}
        cells = {(0, 3), (1, 3), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3)}
        safe = {p for p in cells if not m.point_conflicts(p, retained)}
        for size in (1, 2, 3):
            for factor_tuple in itertools.combinations(sorted(cells), size):
                factor = frozenset(factor_tuple)
                cert = {'n': 4, 'points': [list(p) for p in sorted(retained | factor)]}
                expected = verify_certificate_bruteforce(cert)['conflict_count'] == 0
                self.assertEqual(m.factor_geometry(retained, factor, safe, math.inf, lambda: 0), expected)

    def test_deadline_during_generation_and_before_validation(self):
        with self.assertRaises(TimeoutError):
            list(m.quota_factors({(0, 0)}, 1, 1, lambda: 1))
        ticks = iter((0, 2, 3))
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'load_source') as source:
            report = m.run(Path('unused'), Path(directory), 1, clock=lambda: next(ticks))
            self.assertEqual(report['status'], 'timeout')
            self.assertFalse(report['complete'])
            self.assertTrue(all(t['status'] == 'unstarted' and t['quota_completed'] == 0 for t in report['templates']))
            source.assert_not_called()

    def test_evidence_tampering_rejected(self):
        with patch.dict(m.EVIDENCE, {'data/score11-connected-patch-arithmetic.json': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'evidence hash mismatch'):
                m.load_evidence()

    def test_interrupted_geometry_does_not_count_completed_factor(self):
        manifest = m.load_evidence()
        points = set(map(tuple, json.loads((m.ROOT / 'data/trades-n79-seed270079-state.json').read_text())['points']))
        deleted = frozenset(map(tuple, manifest['eight_edge_paths']['deletion_cases'][0]['deleted']))
        factor = next(f for f in m.quota_factors(deleted, 8) if len(deleted - f) > 5 and (deleted - f) & m.COVER)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(m, 'load_source', return_value=(points, [m.COVER])), patch.object(m, 'point_conflicts', return_value=0), patch.object(m, 'quota_factors', return_value=iter((factor,))), patch.object(m, 'factor_geometry', side_effect=TimeoutError):
                report = m.run(Path('unused'), Path(directory), 1, clock=lambda: 0)
            self.assertEqual(report['status'], 'timeout')
            first = report['templates'][0]
            self.assertEqual(first['status'], 'partial')
            self.assertEqual((first['quota_started'], first['quota_completed']), (1, 0))
            self.assertEqual((first['geometry_started'], first['geometry_completed']), (1, 0))
            self.assertTrue(all(t['status'] == 'unstarted' for t in report['templates'][1:]))

    def test_witness_requires_both_full_validators_before_atomic_save(self):
        good = {'valid': True, 'point_count': 157, 'normalized_sha256': 'abc'}
        bad = {**good, 'valid': False}
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch.object(m, 'verify_certificate', return_value=good), patch.object(m, 'verify_certificate_bruteforce', return_value=bad):
                with self.assertRaises(RuntimeError):
                    m.save_witness({(0, 0)}, {(1, 1)}, frozenset(), 0, out)
                self.assertEqual(list(out.iterdir()), [])
            with patch.object(m, 'verify_certificate', return_value=good), patch.object(m, 'verify_certificate_bruteforce', return_value=good):
                m.save_witness({(0, 0)}, {(1, 1)}, frozenset(), 0, out)
                saved = json.loads((out / 'witness-abc.json').read_text())
                self.assertEqual(saved['metadata']['effective_original_deletions'], [[1, 1]])


if __name__ == '__main__':
    unittest.main()
