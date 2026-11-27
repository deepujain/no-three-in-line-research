import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import score11_deficiency_walk as walk
from src.verify import collinear_triples_bruteforce, verify_certificate_bruteforce


class DeficiencyWalkTests(unittest.TestCase):
    def setUp(self):
        self.n = 3
        self.source = {(x, y) for x in range(3) for y in range(3) if x != y}
        self.score = len(collinear_triples_bruteforce(sorted(self.source)))
        self.points, self.removed, self.start_score = walk.initialize(self.source, self.n, self.score)

    def test_init_and_relocations_match_determinants_and_reverse(self):
        incidence = {p: self.score - len(collinear_triples_bruteforce(sorted(self.source - {p}))) for p in self.source}
        self.assertEqual(self.removed, min(self.source, key=lambda p: (-incidence[p], p)))
        for kind in ('row', 'column'):
            for p in sorted(self.points):
                proposal = walk.relocation(self.points, self.n, p, kind)
                if proposal is None:
                    continue
                delta, result = proposal
                self.assertEqual(self.start_score + delta, len(collinear_triples_bruteforce(sorted(result))))
                added = next(iter(result - self.points))
                back_delta, back = walk.relocation(result, self.n, added, kind)
                self.assertEqual(back, self.points)
                self.assertEqual(back_delta, -delta)
        with self.assertRaises(ValueError):
            walk.relocation(self.points, self.n, (0, 0), 'row') if (0, 0) not in self.points else walk.relocation(self.points, self.n, (-1, -1), 'row')

    def test_rectangles_and_membership(self):
        from itertools import combinations
        for a, b in combinations(sorted(self.points), 2):
            proposal = walk.rectangle(self.points, self.n, a, b)
            if proposal:
                delta, result = proposal
                self.assertEqual(self.start_score + delta, len(collinear_triples_bruteforce(sorted(result))))
                back = walk.rectangle(result, self.n, *sorted(result - self.points))
                self.assertEqual(back, (-delta, self.points))
        with self.assertRaises(ValueError):
            walk.rectangle(self.points, self.n, self.removed, next(iter(self.points)))

    def test_deterministic_walk_and_saved_dual_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            paths = [Path(d) / 'a', Path(d) / 'b']
            source = {(x, y) for x in range(4) for y in range(4) if x == y or x + y == 3}
            score = len(collinear_triples_bruteforce(sorted(source)))
            reports = [walk.walk(4, source, score, p, seed=279157, max_proposals=30) for p in paths]
            self.assertGreater(reports[0]['attempted'], 0)
            self.assertGreater(reports[0]['accepted'], 0)
            for report in reports:
                self.assertIn(report['status'], ('witness', 'proposal_cap'))
            for key in ('attempted', 'legal', 'accepted', 'moves', 'best_score', 'best_normalized_sha256', 'status'):
                self.assertEqual(reports[0][key], reports[1][key])
            saved = json.loads(paths[0].read_text())
            check = verify_certificate_bruteforce(saved)
            self.assertEqual(check['conflict_count'], saved['metadata']['exact_conflict_count'])
            self.assertEqual(check['valid'], saved['metadata']['valid'])
            self.assertEqual(len(saved['validators']), 2)

    def test_validator_mismatch_fails_closed(self):
        real = walk.verify_certificate_bruteforce
        def bad(cert):
            result = real(cert)
            result['conflict_count'] += 1
            return result
        with tempfile.TemporaryDirectory() as d, patch.object(walk, 'verify_certificate_bruteforce', bad):
            path = Path(d) / 'best'
            report = walk.walk(self.n, self.source, self.score, path, max_proposals=0)
            self.assertEqual(report['status'], 'error')
            self.assertFalse(path.exists())

    def test_late_witness_is_saved(self):
        # n=2, three cells have no collinear triple; deadline passes during validator two.
        points = {(0, 0), (0, 1), (1, 0)}
        real = walk.verify_certificate_bruteforce
        now = [0]
        def slow(cert):
            result = real(cert)
            now[0] = 11
            return result
        with tempfile.TemporaryDirectory() as d, patch.object(walk, 'verify_certificate_bruteforce', slow):
            path = Path(d) / 'best'
            walk.audit_save(points, 2, 0, path, {}, 10, lambda: now[0])
            self.assertTrue(json.loads(path.read_text())['metadata']['valid'])

    def test_timeout_before_second_validator_saves_nothing(self):
        now = [0]
        real = walk.verify_certificate
        def slow(cert):
            result = real(cert)
            now[0] = 11
            return result
        with tempfile.TemporaryDirectory() as d, patch.object(walk, 'verify_certificate', slow):
            path = Path(d) / 'best'
            with self.assertRaises(TimeoutError):
                walk.audit_save(self.points, self.n, self.start_score, path, {}, 10, lambda: now[0])
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
