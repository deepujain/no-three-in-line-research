import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import (collinear_triples, collinear_triples_bruteforce,
                        normalized_direction, verify_certificate,
                        verify_certificate_bruteforce)


class VerifyTests(unittest.TestCase):
    def assert_agree(self, certificate):
        fast = verify_certificate(certificate)
        slow = verify_certificate_bruteforce(certificate)
        self.assertEqual({k: v for k, v in fast.items() if k != "algorithm"},
                         {k: v for k, v in slow.items() if k != "algorithm"})
        return fast

    def test_valid_small_sets(self):
        for n, points in [(1, []), (1, [[0, 0]]),
                          (2, [[0, 0], [0, 1], [1, 0], [1, 1]])]:
            with self.subTest(n=n, points=points):
                self.assertTrue(self.assert_agree({"n": n, "points": points})["valid"])

    def test_every_slope_and_input_order(self):
        for triple in [((1, 0), (1, 2), (1, 4)),
                       ((0, 1), (2, 1), (4, 1)),
                       ((0, 0), (2, 1), (4, 2)),
                       ((0, 4), (2, 3), (4, 2)),
                       ((1, 0), (2, 2), (3, 4))]:
            for points in itertools.permutations(triple):
                report = self.assert_agree({"n": 5, "points": list(points)})
                self.assertFalse(report["valid"])
                self.assertEqual(report["conflict_count"], 1)

    def test_all_conflicts_are_reported_once(self):
        report = self.assert_agree({"n": 5, "points": [[i, i] for i in range(5)]})
        self.assertEqual(report["conflict_count"], 10)
        self.assertEqual([c["indices"] for c in report["conflicts"]],
                         [list(t) for t in itertools.combinations(range(5), 3)])

    def test_malformed_schema_and_coordinates(self):
        bad = [None, [], {}, {"n": True, "points": []},
               {"n": 3.0, "points": []}, {"n": 0, "points": []},
               {"n": -1, "points": []}, {"n": "3", "points": []},
               {"n": 3, "points": {}}, {"n": 3, "points": [None]},
               {"n": 3, "points": [[0]]}, {"n": 3, "points": [[0, 1, 2]]},
               {"n": 3, "points": [[True, 1]]},
               {"n": 3, "points": [[1, False]]},
               {"n": 3, "points": [[1.0, 1]]},
               {"n": 3, "points": [[1, float("nan")]]},
               {"n": 3, "points": [["1", 1]]},
               {"n": 3, "points": [[0, 0], [0, 0]]},
               {"n": 3, "points": [[-1, 0]]},
               {"n": 3, "points": [[0, 3]]}]
        for certificate in bad:
            with self.subTest(certificate=certificate):
                report = self.assert_agree(certificate)
                self.assertFalse(report["valid"])
                self.assertTrue(report["errors"])
                self.assertIsNone(report["normalized_sha256"])

    def test_no_fixed_width_overflow_or_float_rounding(self):
        size = 10 ** 100
        exact_line = {"n": size + 1, "points": [[0, 0], [size // 2, size // 2], [size, size]]}
        almost_line = {"n": size + 2, "points": [[0, 0], [size // 2, size // 2], [size, size + 1]]}
        self.assertFalse(self.assert_agree(exact_line)["valid"])
        self.assertTrue(self.assert_agree(almost_line)["valid"])

    def test_hash_is_canonical_and_excludes_metadata(self):
        original = {"n": 3, "points": [[2, 2], [0, 0]], "metadata": {"note": "first"}}
        reordered = {"n": 3, "points": [[0, 0], [2, 2]], "metadata": {"note": "second"}}
        expected = hashlib.sha256(b'{"n":3,"points":[[0,0],[2,2]]}').hexdigest()
        self.assertEqual(self.assert_agree(original)["normalized_sha256"], expected)
        self.assertEqual(self.assert_agree(reordered)["normalized_sha256"], expected)
        self.assertNotEqual(self.assert_agree({"n": 4, "points": original["points"]})["normalized_sha256"], expected)

    def test_exhaustive_three_by_three_subsets(self):
        grid = list(itertools.product(range(3), repeat=2))
        for mask in range(1 << len(grid)):
            points = [point for i, point in enumerate(grid) if mask & (1 << i)]
            self.assertEqual(collinear_triples(points), collinear_triples_bruteforce(points))

    def test_randomized_differential_audit(self):
        rng = random.Random(20261126)
        for _ in range(200):
            n = rng.randrange(1, 10)
            grid = list(itertools.product(range(n), repeat=2))
            points = rng.sample(grid, rng.randrange(min(len(grid), 24) + 1))
            self.assert_agree({"n": n, "points": points})

    def test_primitive_unoriented_directions(self):
        for dx, dy, expected in [(0, -12, (0, 1)), (-12, 0, (1, 0)),
                                 (-6, -9, (2, 3)), (6, -9, (2, -3))]:
            self.assertEqual(normalized_direction(dx, dy), expected)
        with self.assertRaises(ValueError):
            normalized_direction(0, 0)

    def test_cli_success_invalid_and_malformed(self):
        for content, code in [('{"n":2,"points":[[0,0],[1,1]]}', 0),
                              ('{"n":3,"points":[[0,0],[1,1],[2,2]]}', 1),
                              ('{"n":2,"points":[[0.0,0]]}', 1),
                              ('{"n":NaN,"points":[]}', 2), ('{broken', 2)]:
            result = subprocess.run([sys.executable, str(ROOT / "src/verify.py"), "-"],
                                    input=content, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, code, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["valid"], code == 0)
        result = subprocess.run([sys.executable, str(ROOT / "src/verify.py"), "/nonexistent/certificate.json"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
