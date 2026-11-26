"""Exact geometry tests for classical baseline generators and caveats."""

import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from constructions import (is_prime, lifted_parabola, make_certificate,
                           norm_conic, one_point_extensions, parabola)
from verify import verify_certificate, verify_certificate_bruteforce


class ConstructionsTests(unittest.TestCase):
    def assert_valid_both(self, certificate):
        self.assertTrue(verify_certificate(certificate)["valid"])
        self.assertTrue(verify_certificate_bruteforce(certificate)["valid"])

    def test_quadratic_graphs_and_embeddings(self):
        for p in (2, 3, 5, 7, 11, 17, 31):
            for a, b, c in ((1, 0, 0), (-1, 3, -7), (p + 1, 2, 1)):
                points = parabola(p, a, b, c)
                self.assertEqual(len(points), p)
                self.assert_valid_both({"n": p, "points": points})
            self.assert_valid_both(make_certificate("parabola", p, p + 4))

    def test_conic_count_equation_and_geometry(self):
        for p in (3, 5, 7, 11, 17, 31, 79):
            for d in (v for v in range(2, p)
                      if pow(v, (p - 1) // 2, p) == p - 1):
                points = norm_conic(p, d)
                self.assertEqual(len(set(points)), p + 1)
                self.assertTrue(all((x * x - d * y * y - 1) % p == 0
                                    for x, y in points))
                self.assert_valid_both({"n": p, "points": points})

    def test_rectangular_lift(self):
        for p in (2, 3, 5, 11, 17):
            points = lifted_parabola(p)
            self.assertEqual(len(set(points)), 2 * p)
            self.assertTrue(all(x < p and y < 2 * p for x, y in points))
            self.assert_valid_both(make_certificate("lifted-parabola", p))

    def test_bad_parameters(self):
        for value in (True, 2.0, -3, 0, 1, 9, 25):
            self.assertFalse(is_prime(value))
            with self.assertRaises(ValueError):
                parabola(value)
        for function, args in ((parabola, (5, 5)), (parabola, (5, True)),
                               (norm_conic, (2,)), (norm_conic, (7, 2)),
                               (norm_conic, (7, 0)), (norm_conic, (7, True)),
                               (make_certificate, ("conic", 7, 6)),
                               (make_certificate, ("lifted-parabola", 5, 5)),
                               (make_certificate, ("unknown", 5))):
            with self.assertRaises(ValueError):
                function(*args)

    def test_counterexamples_are_really_counterexamples(self):
        for p in (3, 5, 7):
            union = sorted(set(parabola(p)) | set(parabola(p, c=1)))
            self.assertFalse(verify_certificate({"n": p, "points": union})["valid"])
            self.assertTrue({(0, 1), (1, 1), (p - 1, 1)} <= set(union))
        composite_graph = [(x, x * x % 9) for x in range(9)]
        self.assertFalse(verify_certificate({"n": 9, "points": composite_graph})["valid"])
        original = [(0, 4), (1, 0), (2, 1)]
        wrapped = [(x, (y + 1) % 5) for x, y in original]
        self.assert_valid_both({"n": 5, "points": original})
        self.assertFalse(verify_certificate({"n": 5, "points": wrapped})["valid"])

    def test_one_hole_extension_is_exhaustive_for_n2(self):
        source = list(itertools.product(range(2), repeat=2))
        candidates = list(one_point_extensions(2, source))
        self.assertEqual(len(candidates), 4)
        boundary = set(itertools.product(range(3), repeat=2)) - set(source)
        for deleted, candidate in candidates:
            self.assertEqual(len(candidate), 6)
            old = set(source) - {deleted}
            feasible_by_counts = []
            for added in itertools.combinations(boundary, 3):
                full = old | set(added)
                if all(sum(x == i for x, _ in full) == 2 and
                       sum(y == i for _, y in full) == 2 for i in range(3)):
                    feasible_by_counts.append(full)
            self.assertEqual(feasible_by_counts, [set(candidate)])
        self.assertTrue(any(verify_certificate({"n": 3, "points": c})["valid"]
                            for _, c in candidates))


if __name__ == "__main__":
    unittest.main()
