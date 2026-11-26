import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.guided_repair import audit, audit_translation, blockers, deletion_sets
from research import guided_repair
from src.verify import verify_certificate_bruteforce


def brute_repairs(seed, budget):
    n = seed["n"] + 1
    old = [tuple(point) for point in seed["points"]]
    results = {}
    for deleted_count in range(min(budget, len(old)) + 1):
        for deleted in itertools.combinations(range(len(old)), deleted_count):
            remaining = [point for i, point in enumerate(old) if i not in deleted]
            pool = [point for point in itertools.product(range(n), repeat=2) if point not in remaining]
            counts = {str(len(old) + 1): 0, str(len(old) + 2): 0}
            for gain in (1, 2):
                for additions in itertools.combinations(pool, deleted_count + gain):
                    if verify_certificate_bruteforce({"n": n, "points": remaining + list(additions)})["valid"]:
                        counts[str(len(old) + gain)] += 1
            results[deleted] = counts
    return results


class GuidedRepairTests(unittest.TestCase):
    def test_tiny_neighborhoods_match_full_bruteforce(self):
        seeds = [{"n": 1, "points": [[0, 0]]},
                 {"n": 2, "points": [[0, 0]]},
                 {"n": 2, "points": [[0, 0], [1, 1]]},
                 {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}]
        for seed in seeds:
            for budget in (0, 1, 2, 3):
                with self.subTest(seed=seed, budget=budget):
                    actual = audit_translation(seed, max_deletions=budget, collect_deletion_results=True)
                    self.assertEqual(actual["status"], "complete")
                    expected = brute_repairs(seed, budget)
                    found = {tuple(row["deletion_indices"]): row["valid_addition_subsets_by_target_size"]
                             for row in actual["per_deletion_results"]}
                    for deleted, counts in expected.items():
                        self.assertEqual(found.get(deleted, {key: 0 for key in counts}), counts)
                    for key in actual["compatible_addition_subsets_by_target_size"]:
                        self.assertEqual(actual["compatible_addition_subsets_by_target_size"][key],
                                         sum(counts[key] for counts in expected.values()))

    def test_endpoint_supersets_include_optional_extra_deletions(self):
        eligible = [((0, 0), ((0, 1), (2, 3)))]
        actual = set(deletion_sets(5, eligible, 3))
        expected = {deleted for size in (2, 3) for deleted in itertools.combinations(range(5), size)
                    if set(deleted).intersection((0, 1)) and set(deleted).intersection((2, 3))}
        self.assertEqual(actual, expected)

    def test_invalid_seeds_and_budgets(self):
        invalid = {"n": 3, "points": [[0, 0], [1, 1], [2, 2]]}
        with self.assertRaises(ValueError):
            audit(invalid)
        with self.assertRaises(ValueError):
            audit_translation({"n": 1, "points": [[0, 0]]}, max_deletions=-1)
        with self.assertRaises(ValueError):
            audit({"n": 1, "points": [[0, 0]]}, seconds=float("nan"))

    def test_timeout_reports_incomplete(self):
        result = audit({"n": 1, "points": [[0, 0]]}, seconds=0)
        self.assertEqual(result["status"], "timeout_incomplete")
        self.assertEqual(result["translations"][0]["deletion_sets_completed"], 0)

    def test_timeout_during_pair_preprocessing_is_incomplete(self):
        current_time = [0]
        original = guided_repair._collinear

        def expire_on_first_pair(*points):
            current_time[0] = 2
            return original(*points)

        seed = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        with patch("research.guided_repair.time.monotonic", side_effect=lambda: current_time[0]), \
             patch("research.guided_repair._collinear", side_effect=expire_on_first_pair):
            result = audit_translation(seed, max_deletions=3, deadline=1)
        self.assertEqual(result["status"], "timeout_incomplete")
        self.assertEqual(result["phase"], "checking_addition_subsets")
        self.assertEqual(result["deletion_sets_completed"], 0)

    def test_found_certificate_is_independently_validated_before_callback(self):
        found = []
        result = audit_translation({"n": 1, "points": [[0, 0]]}, max_deletions=0,
                                   on_certificate=lambda cert, deleted: found.append((cert, deleted)))
        self.assertTrue(found)
        for certificate, deleted in found:
            self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])
            self.assertEqual(deleted, [])
            self.assertIn("integer_cross_products", certificate["metadata"]["independent_validation"])
        self.assertEqual(len(result["found_certificates"]), 2)


if __name__ == "__main__":
    unittest.main()
