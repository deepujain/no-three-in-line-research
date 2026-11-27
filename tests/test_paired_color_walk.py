import itertools
import random
import unittest
from collections import Counter
from research import paired_color_walk as m


def brute(points):
    return sum((b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])
               for a,b,c in itertools.combinations(sorted(points), 3))


class PairedColorWalkTests(unittest.TestCase):
    def test_all_small_permutations_and_swaps(self):
        coverage = Counter()
        for n in (3, 5):
            for pi in itertools.permutations(range(n)):
                try:
                    points = m.paired_points(pi)
                except ValueError:
                    continue
                self.assertEqual(len(points), 2*n)
                self.assertEqual({(n-1-r,n-1-c) for r,c in points}, points)
                self.assertEqual(Counter(r for r,c in points), Counter({i:2 for i in range(n)}))
                self.assertEqual(Counter(c for r,c in points), Counter({i:2 for i in range(n)}))
                score = brute(points)
                self.assertEqual(m.exact_score(points), score)
                for a,b in itertools.combinations(range(n),2):
                    tag = 'mirror' if a+b == n-1 else 'center' if n//2 in (a,b) else 'other'
                    move = m.proposal(pi, points, a, b)
                    if move is None:
                        coverage['collision'] += 1
                        continue
                    coverage[tag] += 1
                    new_pi, new_points, delta = move
                    self.assertEqual(score+delta, brute(new_points))
                    reverse = m.proposal(new_pi, new_points, a, b)
                    self.assertEqual(reverse[0], list(pi))
                    self.assertEqual(reverse[1], points)
                    self.assertEqual(reverse[2], -delta)
        for tag in ('mirror','center','other','collision'):
            self.assertGreater(coverage[tag], 0, tag)

    def test_bad_inputs(self):
        for pi in ([0,1,2], [1,1,0], [0,1,2,3], [True,1,2]):
            with self.assertRaises(ValueError):
                m.paired_points(pi)
        points=m.paired_points([1,2,0])
        with self.assertRaises(ValueError):
            m.proposal([1,2,0], points, 0, 0)

    def test_initializer_is_seeded_and_bounded(self):
        for n in (3, 5):
            a = m.initialize(n, random.Random(14), 1, lambda: 0)
            b = m.initialize(n, random.Random(14), 1, lambda: 0)
            self.assertEqual(a, b)
            self.assertEqual(a[1], m.paired_points(a[0]))
        class IllegalRandom:
            calls = 0
            def shuffle(self, values):
                self.calls += 1  # Identity always overlaps its reflection.
        rng = IllegalRandom()
        pi, points, kind = m.initialize(5, rng, 1, lambda: 0)
        self.assertEqual(rng.calls, 32)
        self.assertEqual(kind, 'cyclic_fallback')
        self.assertEqual(points, m.paired_points(pi))
        rng = IllegalRandom()
        self.assertEqual(m.initialize(5, rng, 1, lambda: 1)[2], 'cyclic_fallback')
        self.assertEqual(rng.calls, 0)

    def test_seeded_small_iteration_run(self):
        for n in (3,5):
            a=m.walk(n, 42, 10, 75)
            b=m.walk(n, 42, 10, 75)
            for key in ('initializer','initial_score','iterations','accepted','illegal','restarts','best_pi','best_points','best_score'):
                self.assertEqual(a[key], b[key])
            self.assertEqual(a['best_score'], brute(map(tuple,a['best_points'])))


if __name__ == '__main__':
    unittest.main()
