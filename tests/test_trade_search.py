import itertools
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.trade_search import (accept_swap, complete_seed, decompose, degree_two,
                              random_permutations, recolor_cycle, search,
                              state_points, swap_proposal, rotation_proposal,
                              accept_rotation, checked_full_state,
                              rectangle_proposal, audit_rectangles)
from src.verify import collinear_triples_bruteforce, verify_certificate_bruteforce


class TradeTests(unittest.TestCase):
    def test_every_legal_uncolored_small_switch_has_exact_delta_and_degrees(self):
        rng = random.Random(710)
        checked = 0
        for n in range(2, 9):
            permutations = random_permutations(n, rng)
            points = state_points(permutations)
            score = len(collinear_triples_bruteforce(sorted(points)))
            expected_histogram = {}
            for first, second in itertools.combinations(sorted(points), 2):
                proposal = rectangle_proposal(points, first, second)
                self.assertEqual(proposal, rectangle_proposal(points, second, first))
                if proposal is None:
                    continue
                delta, changed = proposal
                self.assertTrue(degree_two(changed, n))
                self.assertEqual(score + delta, len(collinear_triples_bruteforce(sorted(changed))))
                self.assertEqual(state_points(decompose(changed, n)), changed)
                expected_histogram[delta] = expected_histogram.get(delta, 0) + 1
                checked += 1
            report = audit_rectangles({"n": n, "points": sorted(points)})
            self.assertEqual(report["status"], "complete")
            self.assertEqual(report["delta_histogram"], expected_histogram)
            self.assertEqual(report["point_pairs_examined"], n * (2 * n - 1))
        self.assertGreater(checked, 100)

    def test_rectangle_resume_is_deterministic_and_retains_best(self):
        state = {"n": 7, "points": sorted(state_points(random_permutations(7, random.Random(51))))}
        original_score = len(collinear_triples_bruteforce(state["points"]))
        settings = dict(max_iterations=200, resume_state=state, move_kind="rectangle",
                        focus_probability=.85, tabu_size=30, history_size=40)
        first = search(7, None, 414, **settings)
        second = search(7, None, 414, **settings)
        self.assertEqual(first["search_state"], second["search_state"])
        self.assertLessEqual(first["run"]["best_score"], original_score)
        self.assertEqual(first["run"]["rectangle_proposals"], first["run"]["iterations"])
        self.assertTrue(verify_certificate_bruteforce(first["incumbent"])["valid"])

    def test_rectangle_audit_timeout_is_partial(self):
        points = sorted(state_points(random_permutations(5, random.Random(2))))
        report = audit_rectangles({"n": 5, "points": points}, seconds=0)
        self.assertEqual(report["status"], "timeout_incomplete")
        self.assertEqual(report["point_pairs_examined"], 0)
    def test_continuous_worker_revisit_history_is_bounded(self):
        result = search(12, None, 917, max_iterations=200, temperature=10,
                        move_kind="mixed", history_size=2)
        self.assertLessEqual(result["run"]["tracked_state_hashes"], 2)
        self.assertEqual(result["run"]["state_history_capacity"], 2)
        self.assertGreater(result["run"]["state_history_evictions"], 0)
        self.assertIn("not lifetime", result["run"]["state_hash_revisit_scope"])
    def test_every_legal_small_triple_rotation_has_exact_delta_and_degrees(self):
        rng = random.Random(313)
        checked = 0
        for n in range(3, 8):
            permutations = random_permutations(n, rng)
            points = state_points(permutations)
            old_score = len(collinear_triples_bruteforce(sorted(points)))
            for color in range(2):
                for rows in itertools.permutations(range(n), 3):
                    proposal = rotation_proposal(permutations, points, color, rows)
                    if proposal is None:
                        continue
                    delta, new_points = proposal
                    self.assertTrue(degree_two(new_points, n))
                    self.assertEqual(old_score + delta, len(collinear_triples_bruteforce(sorted(new_points))))
                    copied = [list(p) for p in permutations]
                    accept_rotation(copied, color, rows)
                    self.assertEqual(state_points(copied), new_points)
                    checked += 1
        self.assertGreater(checked, 300)

    def test_resume_recomputes_score_and_preserves_best_and_seed(self):
        baseline = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        full = {"n": 3, "points": sorted(state_points(complete_seed(baseline, 3, random.Random(7)))),
                "collinear_triple_count": -100, "valid": True}
        points, score, _ = checked_full_state(full, 3)
        self.assertEqual(score, len(collinear_triples_bruteforce(sorted(points))))
        first = search(3, None, 991, max_iterations=200, initial=baseline, resume_state=full,
                       move_kind="mixed", focus_probability=.8, tabu_size=20)
        second = search(3, None, 991, max_iterations=200, initial=baseline, resume_state=full,
                        move_kind="mixed", focus_probability=.8, tabu_size=20)
        self.assertEqual(first["search_state"], second["search_state"])
        self.assertEqual(first["run"]["initial_full_state_score"], score)
        self.assertLessEqual(first["run"]["best_score"], score)
        self.assertGreaterEqual(len(first["incumbent"]["points"]), 4)
        self.assertTrue(verify_certificate_bruteforce(first["incumbent"])["valid"])
        with self.assertRaises(ValueError):
            checked_full_state({"n": 3, "points": [[0, 0]]}, 3)
        with self.assertRaises(ValueError):
            checked_full_state({"n": 3, "points": [[True, 0]]}, 3)

    def test_every_legal_small_swap_preserves_degrees_and_exact_score(self):
        rng = random.Random(17)
        checked = 0
        for n in range(2, 8):
            permutations = random_permutations(n, rng)
            points = state_points(permutations)
            old_score = len(collinear_triples_bruteforce(sorted(points)))
            for color, first, second in itertools.product(range(2), range(n), range(n)):
                proposal = swap_proposal(permutations, points, color, first, second)
                if proposal is None:
                    continue
                delta, new_points = proposal
                self.assertTrue(degree_two(new_points, n))
                self.assertEqual(old_score + delta, len(collinear_triples_bruteforce(sorted(new_points))))
                copied = [list(p) for p in permutations]
                accept_swap(copied, color, first, second)
                self.assertEqual(state_points(copied), new_points)
                checked += 1
        self.assertGreater(checked, 100)

    def test_cycle_recoloring_preserves_state_and_disjoint_permutations(self):
        rng = random.Random(29)
        for n in range(2, 12):
            permutations = random_permutations(n, rng)
            points = state_points(permutations)
            for row in range(n):
                recolor_cycle(permutations, row)
                self.assertEqual(state_points(permutations), points)
                for permutation in permutations:
                    self.assertEqual(sorted(permutation), list(range(n)))

    def test_decomposition_roundtrip_and_seed_completion(self):
        seed = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        for random_seed in range(10):
            completed = complete_seed(seed, 3, random.Random(random_seed))
            points = state_points(completed)
            self.assertTrue(degree_two(points, 3))
            self.assertEqual(state_points(decompose(points, 3)), points)
        with self.assertRaises(ValueError):
            decompose({(0, 0)}, 2)

    def test_operation_capped_search_reproducibility_and_incumbent(self):
        initial = {"n": 2, "points": [[0, 0], [0, 1], [1, 0], [1, 1]]}
        first = search(3, None, 2026, max_iterations=100, initial=initial)
        second = search(3, None, 2026, max_iterations=100, initial=initial)
        self.assertEqual(first["search_state"], second["search_state"])
        self.assertEqual(first["incumbent"], second["incumbent"])
        self.assertGreaterEqual(len(first["incumbent"]["points"]), 4)
        self.assertTrue(verify_certificate_bruteforce(first["incumbent"])["valid"])
        self.assertLessEqual(first["run"]["iterations"], 100)

    def test_invalid_search_state_is_not_presented_as_certificate(self):
        result = search(5, None, 11, max_iterations=0)
        state = result["search_state"]
        self.assertEqual(state["valid"], verify_certificate_bruteforce(state)["valid"])
        self.assertEqual(state["collinear_triple_count"], len(collinear_triples_bruteforce(state["points"])))
        if not state["valid"]:
            self.assertEqual(state["state_kind"], "invalid_full_search_state")
        self.assertTrue(verify_certificate_bruteforce(result["incumbent"])["valid"])

    def test_known_small_full_solution(self):
        result = search(2, None, 5, max_iterations=0)
        self.assertEqual(result["run"]["best_score"], 0)
        self.assertEqual(len(result["incumbent"]["points"]), 4)

    def test_invalid_bounds(self):
        for n, seconds, cap in [(1, 0, 0), (True, 0, 0), (3, -1, 0),
                                 (3, float("inf"), 0), (3, None, None), (3, None, -1)]:
            with self.assertRaises(ValueError):
                search(n, seconds, 1, cap)


if __name__ == "__main__":
    unittest.main()
