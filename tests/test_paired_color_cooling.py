import unittest
from research import paired_color_cooling as m
from research import paired_color_walk as base
from tests.test_paired_color_walk import brute


class CoolingTests(unittest.TestCase):
    def test_schedule_boundaries_and_midpoint(self):
        self.assertEqual(m.temperature(-1, 25), 4.0)
        self.assertEqual(m.temperature(0, 25), 4.0)
        self.assertAlmostEqual(m.temperature(12.5, 25), 2.01)
        self.assertAlmostEqual(m.temperature(25, 25), 0.02)
        self.assertAlmostEqual(m.temperature(26, 25), 0.02)
        for elapsed, seconds in ((float('nan'), 25), (0, 0), (0, float('inf'))):
            with self.assertRaises(ValueError):
                m.temperature(elapsed, seconds)

    def test_tiny_final_score_and_repeatability(self):
        for n in (3,5):
            a = m.walk(n, 279401, 25, 100, clock=lambda: 0)
            b = m.walk(n, 279401, 25, 100, clock=lambda: 0)
            for key in ('initializer','initial_score','iterations','accepted','illegal','restarts','best_pi','best_points','best_score','final_temperature'):
                self.assertEqual(a[key], b[key])
            initial = base.walk(n, 279401, 25, 0, clock=lambda: 0)
            self.assertEqual((a['initializer'], a['initial_score']), (initial['initializer'], initial['initial_score']))
            self.assertGreaterEqual(a['final_current_score'], a['best_score'])
            self.assertEqual(a['best_score'], brute(map(tuple, a['best_points'])))
            self.assertEqual(a['initial_temperature'], 4.0)
            self.assertEqual(a['final_temperature'], 4.0)


if __name__ == '__main__':
    unittest.main()
