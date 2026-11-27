"""Synthetic source-independent contraction comparisons; no n76 fixture reads."""
from itertools import combinations
from array import array
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research import occupied_contraction75 as worker


def direct(points, c, r):
    image = [(x-int(x > c), y-int(y > r)) for x, y in points if x != c and y != r]
    bad = sum((b[0]-a[0])*(d[1]-a[1]) == (b[1]-a[1])*(d[0]-a[0]) for a, b, d in combinations(image, 3))
    return image, bad


class ContractionTests(unittest.TestCase):
    def test_all_small_axis_full_sources(self):
        sources = cuts = 0
        for n in (2, 3, 4):
            for points in combinations([(x, y) for x in range(n) for y in range(n)], 2*n):
                if any(sum(p[a] == v for p in points) != 2 for a in (0, 1) for v in range(n)):
                    continue
                counts = {}; scores, witnesses = worker.census(points, n, counters=counts)
                sources += 1
                self.assertEqual(counts['triples'], len(list(combinations(points, 3))))
                for c in range(n):
                    for r in range(n):
                        cuts += 1; image, bad = direct(points, c, r)
                        self.assertEqual(scores[c*(n+1)+r], bad)
                        if (c, r) in points:
                            self.assertEqual(len(image), 2*n-3)
                            self.assertEqual((c, r) in witnesses, bad > 0)
                            if bad:
                                triple = witnesses[c, r]
                                self.assertTrue(set(triple) <= set(points))
                                self.assertEqual(direct(triple, c, r)[1], 1)
        self.assertEqual((sources, cuts), (97, 1498))

    def test_compression_does_not_preserve_geometry(self):
        source = [(0,0),(0,1),(1,2),(1,3),(2,0),(2,1),(3,2),(3,3)]
        scores, witnesses = worker.census(source, 4)
        self.assertEqual(scores[1*5+2], 1)
        self.assertIn((1, 2), witnesses)

    def test_deadline_does_not_return_partial_census(self):
        count = {}; calls = []
        def stop():
            calls.append(1)
            if len(calls) == 3: raise TimeoutError('synthetic interruption')
        with self.assertRaises(TimeoutError): worker.census([(0,0),(0,1),(1,0),(1,1)], 2, stop, count)
        self.assertEqual(count['triples'], 2)

    def test_reject_bad_source(self):
        for source, n in [([], 2), ([(0,0)]*4, 2), ([(0,0),(0,1),(1,0),(1,2)], 2)]:
            with self.subTest(source=source), self.assertRaises(ValueError): worker.census(source, n)

    def synthetic_run(self, mode):
        # The source is generated here and deliberately NOT geometry-validated:
        # validator/census stubs isolate run's artifact/deadline/pin contract.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'data').mkdir(); (root/'src').mkdir(); out = root/'out'; out.mkdir()
            source = {'n': 76, 'source_record': 1,
                      'points': [[x, y] for x in range(76) for y in (x, (x+1)%76)]}
            fixture = root/worker.FIXTURE; fixture.write_text(json.dumps(source))
            verifier = root/'src/verify.py'; verifier.write_text('synthetic pin')
            paths = [Path(worker.__file__).resolve(), fixture, verifier]
            pins = {str(p): worker.digest(p) for p in paths}
            manifest = root/'manifest.json'; manifest.write_text(json.dumps(pins))
            clock = [0.0]; seen = []; verifier_hash_calls = []
            real_digest = worker.digest
            def digest(path):
                if Path(path) == verifier:
                    verifier_hash_calls.append(1)
                    if mode == 'latepins' and len(verifier_hash_calls) == 2: clock[0] = 26
                return real_digest(path)
            def validate(cert):
                seen.append(cert['n'])
                return {'valid': True, 'point_count': len(cert['points']), 'normalized_sha256': worker.NORMALIZED}
            def second(cert):
                result = validate(cert)
                if cert['n'] == 75:
                    if mode == 'late': clock[0] = 26
                    if mode == 'drift': verifier.write_text('changed')
                return result
            def census(points, n, check, counters):
                self.assertEqual(n, 76)
                if mode == 'incomplete': raise TimeoutError('synthetic census interruption')
                return array('q', [0])*(77*77), {}
            with patch.object(worker, 'ROOT', root), patch.object(worker, 'FIXTURE_SHA', worker.digest(fixture)), \
                 patch.object(worker, 'verify_certificate', validate), patch.object(worker, 'verify_certificate_bruteforce', second), \
                 patch.object(worker, 'census', census), patch.object(worker, 'digest', digest):
                report = worker.run(out, manifest, started=0, clock=lambda: clock[0])
            saved = (out/'valid149.json').exists()
            if saved:
                self.assertEqual(len(json.loads((out/'valid149.json').read_text())['certificate']['points']), 149)
            self.assertEqual(json.loads((out/'report.json').read_text())['closure'], report['closure'])
            return report, saved, seen

    def test_late_validator_saves_before_deadline_recheck(self):
        report, saved, seen = self.synthetic_run('late')
        self.assertTrue(saved); self.assertTrue(report['witness_saved'])
        self.assertEqual(report['status'], 'timeout'); self.assertFalse(report['closure']); self.assertFalse(report['complete'])
        self.assertEqual(seen, [76, 76, 75, 75])

    def test_final_pin_drift_rejects_promotion(self):
        report, saved, _ = self.synthetic_run('drift')
        self.assertTrue(saved); self.assertEqual(report['status'], 'error')
        self.assertFalse(report['identity_valid']); self.assertFalse(report['closure']); self.assertFalse(report['complete'])

    def test_incomplete_census_never_closes(self):
        report, saved, seen = self.synthetic_run('incomplete')
        self.assertFalse(saved); self.assertFalse(report['closure']); self.assertFalse(report['complete'])
        self.assertEqual(seen, [76, 76])

    def test_final_pin_hashing_cannot_cross_deadline_with_completion(self):
        report, saved, _ = self.synthetic_run('latepins')
        self.assertTrue(saved); self.assertTrue(report['identity_valid'])
        self.assertEqual(report['status'], 'timeout'); self.assertFalse(report['complete']); self.assertFalse(report['closure'])


if __name__ == '__main__': unittest.main()
