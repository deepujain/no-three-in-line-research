import itertools
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import score11_deficiency_neighborhood as census
from src.verify import collinear_triples_bruteforce


def score(points):
    return len(collinear_triples_bruteforce(sorted(points)))


class NeighborhoodTests(unittest.TestCase):
    def test_complete_tiny_independent_histogram_and_unique_neighbors(self):
        points = {(0, 0), (0, 1), (1, 0)}
        with tempfile.TemporaryDirectory() as d:
            result = census.census(2, points, score(points), Path(d) / 'best')
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(result['complete'])
        self.assertEqual([result['classes'][k]['completed'] for k in ('row', 'column', 'rectangle')], [3, 3, 3])
        neighbors = set()
        expected = {k: {} for k in ('row', 'column', 'rectangle')}
        r, c = 1, 1
        for kind, old in census.attempts(points):
            if kind == 'row':
                new = {(r, old[0][1])}
            elif kind == 'column':
                new = {(old[0][0], c)}
            else:
                a, b = old
                if a[0] == b[0] or a[1] == b[1]:
                    continue
                new = {(a[0], b[1]), (b[0], a[1])}
            if new & points:
                continue
            candidate = points - set(old) | new
            self.assertNotIn(frozenset(candidate), neighbors)
            neighbors.add(frozenset(candidate))
            delta = score(candidate) - score(points)
            expected[kind][delta] = expected[kind].get(delta, 0) + 1
        for kind in expected:
            row = result['classes'][kind]
            self.assertEqual(row['deltas'], expected[kind])
            self.assertEqual(row['completed'], row['legal'] + row['illegal'])
            self.assertEqual(row['legal'], sum(row['deltas'].values()))

    def test_order_and_partial_prefix(self):
        points = {(0, 0), (0, 1), (1, 0)}
        kinds = [kind for kind, _ in census.attempts(points)]
        self.assertEqual(kinds, ['row'] * 3 + ['column'] * 3 + ['rectangle'] * 3)
        tick = [-1]
        def clock():
            tick[0] += 1
            return tick[0]
        with tempfile.TemporaryDirectory() as d:
            result = census.census(2, points, 0, Path(d) / 'best', seconds=5, clock=clock)
        self.assertEqual(result['status'], 'timeout')
        self.assertFalse(result['complete'])
        self.assertLess(sum(row['completed'] for row in result['classes'].values()), 9)

    def test_identity_and_inverse_fail_closed(self):
        points = {(0, 0), (0, 1), (1, 0)}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'best'
            result = census.census(2, points, 0, path, expected_normalized='bad')
            self.assertEqual(result['status'], 'error')
            self.assertFalse(path.exists())
            with patch.object(census.base, 'relocation', return_value=(0, points)):
                result = census.census(2, points, 0, path)
                self.assertEqual(result['status'], 'error')
                self.assertFalse(result['complete'])

    def test_final_identity_recheck_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'pinned'
            path.write_bytes(b'original')
            pins = {path: hashlib.sha256(b'original').hexdigest()}
            self.assertEqual(census.finalize_identity({'status': 'complete', 'complete': True}, pins)['status'], 'complete')
            path.write_bytes(b'changed')
            report = census.finalize_identity({'status': 'complete', 'complete': True}, pins)
            self.assertEqual(report['status'], 'error')
            self.assertFalse(report['complete'])

    def test_improved_state_saved_with_both_validators(self):
        points = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'best'
            result = census.census(3, points, score(points), path)
            self.assertEqual(result['status'], 'witness')
            self.assertFalse(result['complete'])
            saved = json.loads(path.read_text())
            self.assertLess(score({tuple(p) for p in saved['points']}), score(points))
            self.assertEqual(len(saved['validators']), 2)


if __name__ == '__main__':
    unittest.main()
