import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.search import _candidate_cost, _prune, search
from src.verify import collinear_triples_bruteforce, verify_certificate, verify_certificate_bruteforce


class SearchTests(unittest.TestCase):
    def test_trivial_target_and_no_work_needed(self):
        for n, count in [(1, 1), (2, 4)]:
            certificate = search(n, 0, 17)
            self.assertEqual(len(certificate["points"]), count)
            self.assertEqual(certificate["metadata"]["iterations"], 0)
            self.assertEqual(certificate["metadata"]["stopping_reason"], "target_reached")
            self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])

    def test_zero_budget_always_returns_independently_valid_subset(self):
        for n in range(3, 11):
            certificate = search(n, 0, 20261126)
            self.assertTrue(verify_certificate(certificate)["valid"])
            self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])
            self.assertLessEqual(len(certificate["points"]), 2 * n)
            self.assertGreater(len(certificate["points"]), 0)
            self.assertEqual(certificate["metadata"]["seed"], 20261126)
            self.assertEqual(certificate["metadata"]["iterations"], 0)

    def test_fixed_initialization_is_seed_reproducible(self):
        first = search(9, 0, 99)
        second = search(9, 0, 99)
        self.assertEqual(first["points"], second["points"])
        self.assertEqual(first["metadata"]["normalized_sha256"], second["metadata"]["normalized_sha256"])
        self.assertIn("wall-clock", first["metadata"]["reproducibility"])

    def test_invalid_parameters(self):
        for n, seconds, seed in [(0, 0, 1), (True, 0, 1), (2.0, 0, 1),
                                 (3, -1, 1), (3, float("nan"), 1),
                                 (3, float("inf"), 1), (3, True, 1),
                                 (3, "1", 1), (3, 0, True), (3, 0, 1.0)]:
            with self.assertRaises(ValueError):
                search(n, seconds, seed)
        with self.assertRaises(ValueError):
            search(3, 0, 1, delete_count=0)

    def test_initial_incumbent_is_preserved_and_embedded(self):
        initial = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        certificate = search(3, 0, 10, initial=initial)
        self.assertEqual(certificate["points"], initial["points"])
        self.assertEqual(certificate["n"], 3)
        self.assertEqual(certificate["metadata"]["initial_point_count"], 4)
        self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])
        with self.assertRaises(ValueError):
            search(1, 0, 10, initial=initial)
        with self.assertRaises(ValueError):
            search(3, 0, 10, initial={"n": 3, "points": [[0, 0], [1, 1], [2, 2]]})

    def test_initial_search_adds_points_with_a_deterministic_test_clock(self):
        clock = itertools.count(step=0.0001)
        initial = {"n": 2, "points": [[0, 0]]}
        with patch("src.search.time.monotonic", side_effect=lambda: next(clock)):
            certificate = search(3, .1, 17, initial=initial)
        self.assertGreater(len(certificate["points"]), 1)
        self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])
        self.assertGreater(certificate["metadata"]["iterations"], 0)

    def test_initial_search_repairs_without_losing_incumbent(self):
        clock = itertools.count(step=0.0001)
        initial = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        with patch("src.search.time.monotonic", side_effect=lambda: next(clock)):
            certificate = search(3, .1, 19, initial=initial, delete_count=2)
        self.assertGreaterEqual(len(certificate["points"]), 4)
        self.assertGreater(certificate["metadata"]["restarts"], 1)
        self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])

    def test_candidate_cost_matches_independent_triples(self):
        points = [(0, 0), (1, 2), (2, 1), (2, 3), (3, 0), (3, 3)]
        for index in range(len(points)):
            for candidate in itertools.product(range(4), repeat=2):
                if any(candidate == point for j, point in enumerate(points) if j != index):
                    continue
                changed = list(points)
                changed[index] = candidate
                actual = sum(index in triple for triple in collinear_triples_bruteforce(changed))
                self.assertEqual(_candidate_cost(points, index, candidate), actual)

    def test_pruning_arbitrary_conflicted_grid(self):
        original = list(itertools.product(range(4), repeat=2))
        pruned = _prune(original)
        self.assertEqual(len(original), 16)
        self.assertTrue(set(pruned).issubset(original))
        self.assertEqual(collinear_triples_bruteforce(pruned), [])

    def test_cli_writes_certificate_and_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested/result.json"
            result = subprocess.run([sys.executable, str(ROOT / "src/search.py"),
                                     "--n", "5", "--seconds", "0", "--seed", "314",
                                     "--output", str(output)],
                                    text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            certificate = json.loads(output.read_text())
            self.assertTrue(json.loads(result.stdout)["valid"])
            self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])
            self.assertEqual(certificate["metadata"]["normalized_sha256"],
                             json.loads(result.stdout)["normalized_sha256"])


if __name__ == "__main__":
    unittest.main()
