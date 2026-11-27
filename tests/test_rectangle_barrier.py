from collections import deque
import itertools
from pathlib import Path
import random
import json
import subprocess
import tempfile
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.rectangle_barrier import barrier_search
from src.trade_search import random_permutations, state_points, degree_two
from src.verify import collinear_triples_bruteforce, normalized_sha256, verify_certificate_bruteforce


def brute_component(source, threshold):
    n = source["n"]
    # Independent graph: enumerate every degree-two state, then compare set
    # differences of state pairs; do not call the production move generator.
    vertices = {}
    for subset in itertools.combinations(itertools.product(range(n), repeat=2), 2 * n):
        if degree_two(subset, n) and len(collinear_triples_bruteforce(subset)) <= threshold:
            key = frozenset(subset)
            vertices[key] = len(collinear_triples_bruteforce(subset))
    start = frozenset(map(tuple, source["points"]))
    reached, queue = {start}, deque([start])
    while queue:
        current = queue.popleft()
        for other in vertices:
            removed, added = current - other, other - current
            if len(removed) == len(added) == 2 and other not in reached:
                reached.add(other)
                queue.append(other)
    return {normalized_sha256(n, points): vertices[points] for points in reached}


class RectangleBarrierTests(unittest.TestCase):
    def test_partial_pair_scan_resumes_without_discarding_frontier(self):
        source = {"n": 4, "points": sorted(state_points(random_permutations(4, random.Random(5))))}
        clock = itertools.count(step=.0001)
        with patch("research.rectangle_barrier.time.monotonic", side_effect=lambda: next(clock)):
            partial = barrier_search(source, 20, seconds=.002, max_states=1000)
        partial = json.loads(json.dumps(partial))
        self.assertEqual(partial["status"], "timeout_incomplete")
        self.assertTrue(any(0 < node["next_pair_index"] < 28 for node in partial["nodes"]))
        self.assertEqual(set(partial["frontier_state_hashes"]),
                         {node["normalized_sha256"] for node in partial["nodes"] if not node["neighborhood_complete"]})
        resumed = barrier_search(source, 20, seconds=10, max_states=1000, resume=partial)
        fresh = barrier_search(source, 20, seconds=10, max_states=1000)
        self.assertEqual(resumed["status"], "complete_frontier_exhausted")
        self.assertIn("trusted, unmodified local", resumed["checkpoint_trust_model"])
        self.assertIn("trusted local checkpoint", resumed["completeness_basis"])
        self.assertEqual({node["normalized_sha256"] for node in resumed["nodes"]},
                         {node["normalized_sha256"] for node in fresh["nodes"]})
        self.assertEqual(resumed["old_edge_pairs_examined"], fresh["old_edge_pairs_examined"])

    def test_state_limit_resume_and_threshold_raise(self):
        source = {"n": 3, "points": sorted(state_points(random_permutations(3, random.Random(3))))}
        capped = barrier_search(source, 10, max_states=1)
        restored = barrier_search(source, 10, max_states=100, resume=capped)
        self.assertEqual(restored["status"], "complete_frontier_exhausted")
        score = len(collinear_triples_bruteforce(source["points"]))
        low = barrier_search(source, score)
        raised = barrier_search(source, score + 1, resume=low)
        fresh = barrier_search(source, score + 1)
        self.assertTrue(raised["threshold_was_raised"])
        self.assertEqual({node["normalized_sha256"] for node in raised["nodes"]},
                         {node["normalized_sha256"] for node in fresh["nodes"]})
        damaged = json.loads(json.dumps(capped))
        damaged["nodes"][0]["score"] += 1
        with self.assertRaises(ValueError):
            barrier_search(source, 10, resume=damaged)

    def test_cli_checkpoint_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = {"n": 3, "points": sorted(state_points(random_permutations(3, random.Random(3))))}
            (root / "source.json").write_text(json.dumps(source))
            (root / "baseline.json").write_text(json.dumps({"n": 3, "points": []}))
            common = [sys.executable, str(ROOT / "research/rectangle_barrier.py"),
                      "--baseline", str(root / "baseline.json"), "--threshold", "10",
                      "--output", str(root / "checkpoint.json")]
            first = subprocess.run(common + ["--source", str(root / "source.json"), "--seconds", "0"],
                                   capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 2, first.stderr)
            self.assertTrue((root / "checkpoint.json").exists())
            second = subprocess.run(common + ["--resume", str(root / "checkpoint.json"), "--seconds", "10"],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(second.returncode, 0, second.stderr)
            report = json.loads((root / "checkpoint.json").read_text())
            self.assertEqual(report["status"], "complete_frontier_exhausted")
            self.assertEqual(report["resume_count"], 1)
    def test_complete_small_components_match_independent_full_graph(self):
        for n in (2, 3, 4):
            source = {"n": n, "points": sorted(state_points(random_permutations(n, random.Random(91))))}
            score = len(collinear_triples_bruteforce(source["points"]))
            for threshold in (score, score + 1):
                with self.subTest(n=n, threshold=threshold):
                    expected = brute_component(source, threshold)
                    actual = barrier_search(source, threshold, seconds=10, max_states=1000)
                    self.assertEqual(actual["status"], "complete_frontier_exhausted")
                    self.assertEqual({node["normalized_sha256"]: node["score"] for node in actual["nodes"]}, expected)
                    self.assertTrue(all(node["neighborhood_complete"] for node in actual["nodes"]))
                    self.assertEqual(actual["pending_frontier_count"], 0)

    def test_limits_are_explicitly_incomplete(self):
        source = {"n": 3, "points": sorted(state_points(random_permutations(3, random.Random(3))))}
        timed = barrier_search(source, 10, seconds=0)
        self.assertEqual(timed["status"], "timeout_incomplete")
        self.assertEqual(timed["neighborhoods_completed"], 0)
        capped = barrier_search(source, 10, seconds=10, max_states=1)
        self.assertEqual(capped["status"], "state_limit_incomplete")
        self.assertEqual(capped["discovered_state_count"], 1)
        self.assertFalse(capped["nodes"][0]["neighborhood_complete"])

    def test_better_state_paths_reconstruct_exact_states(self):
        source = {"n": 4, "points": sorted(state_points(random_permutations(4, random.Random(5))))}
        score = len(collinear_triples_bruteforce(source["points"]))
        calls = []
        report = barrier_search(source, score + 5, seconds=10, max_states=1000,
                                on_improvement=lambda state, incumbent: calls.append((state, incumbent)))
        self.assertTrue(calls)
        for improvement, incumbent in calls:
            points = set(map(tuple, source["points"]))
            for step in improvement["path"]:
                self.assertEqual(normalized_sha256(4, points), step["from_normalized_sha256"])
                points.difference_update(map(tuple, step["old_edges"]))
                points.update(map(tuple, step["replacement_edges"]))
                self.assertTrue(degree_two(points, 4))
                self.assertEqual(normalized_sha256(4, points), step["to_normalized_sha256"])
                self.assertEqual(len(collinear_triples_bruteforce(sorted(points))), step["resulting_score"])
            self.assertEqual(points, set(map(tuple, improvement["state"]["points"])))
            self.assertTrue(verify_certificate_bruteforce(incumbent)["valid"])
        self.assertEqual(report["best_score"], min(node["score"] for node in report["nodes"]))


if __name__ == "__main__":
    unittest.main()
