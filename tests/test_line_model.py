import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import line_model
from verify import collinear_triples_bruteforce


class LineModelTest(unittest.TestCase):
    def test_all_subsets_through_four_against_independent_determinants(self):
        for n in range(1, 5):
            points = [(x, y) for y in range(n) for x in range(n)]
            index = {p: i for i, p in enumerate(points)}
            lines = list(line_model.maximal_lines(n))
            masks = [sum(1 << index[p] for p in line) for line in lines]
            self.assertEqual(len(set(masks)), len(masks))
            counts = line_model.model_counts(n)
            self.assertEqual(counts['maximal_lines_length_at_least_3'], len(lines))
            self.assertEqual(counts['line_variable_incidences'], sum(map(len, lines)))
            for subset in range(1 << len(points)):
                model_ok = all((subset & mask).bit_count() <= 2 for mask in masks)
                selected = [p for i, p in enumerate(points) if subset & (1 << i)]
                exact_ok = not collinear_triples_bruteforce(selected)
                self.assertEqual(model_ok, exact_ok, (n, subset))

    def test_counts_and_negative_slopes(self):
        for n in range(3, 9):
            lines = list(line_model.maximal_lines(n))
            stats = line_model.model_counts(n)
            self.assertEqual(len(lines), stats['maximal_lines_length_at_least_3'])
            self.assertEqual(sum(map(len, lines)), stats['line_variable_incidences'])
            self.assertIn(tuple((i,n-1-i) for i in range(n)), lines)
            self.assertEqual(len(set(lines)), len(lines))
            for line in lines:
                self.assertGreaterEqual(len(line), 3)
                dx, dy = line[1][0]-line[0][0], line[1][1]-line[0][1]
                self.assertTrue(dx > 0 or (dx == 0 and dy == 1))
                self.assertEqual(__import__('math').gcd(dx, abs(dy)), 1)
                self.assertFalse(0 <= line[0][0]-dx < n and 0 <= line[0][1]-dy < n)
                self.assertFalse(0 <= line[-1][0]+dx < n and 0 <= line[-1][1]+dy < n)

    def test_invalid_n(self):
        for n in (0, -1, True, 1.0):
            with self.assertRaises(ValueError):
                line_model.model_counts(n)

if __name__ == '__main__':
    unittest.main()
