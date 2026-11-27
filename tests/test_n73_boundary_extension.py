import hashlib
import tempfile
import unittest
from pathlib import Path

from research import n73_boundary_extension as m


class BoundaryArithmeticTests(unittest.TestCase):
    def test_small_grid_choices_fill_outer_rows_and_columns(self):
        n = 9
        orbits = m.boundary_orbits(n)
        selections = m.selections(n)
        self.assertEqual(len(selections), 8)
        self.assertEqual(len(set(selections)), 8)
        for choice in selections:
            edges = [orbits[i][0] for i in choice]
            self.assertEqual(len(set(edges)), 3)
            points = [p for i in choice for p in orbits[i][1]]
            self.assertEqual(len(set(points)), 12)
            self.assertEqual([sum(y == r for x, y in points) for r in (0, 1, 2, 6, 7, 8)], [2]*6)
            self.assertEqual([sum(x == c for x, y in points) for c in (0, 1, 2, 6, 7, 8)], [2]*6)
            self.assertTrue(all(x != y and x + y != n-1 for x, y in points))

    def test_invalid_target(self):
        for n in (True, 5, 8):
            with self.assertRaises(ValueError):
                m.boundary_orbits(n)

    def test_pinned_decode_and_tamper(self):
        raw = m.ROOT/'data/published-n73-rct4.raw'
        fixture = m.ROOT/'data/published-n73-rct4-candidate.json'
        loaded = m.load_pinned(raw, fixture)
        self.assertEqual(len(loaded['points']), 146)
        with tempfile.TemporaryDirectory() as tmp:
            changed = Path(tmp)/'raw'
            changed.write_bytes(raw.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                m.load_pinned(changed, fixture)
            changed.write_bytes(fixture.read_bytes()+b' ')
            with self.assertRaises(ValueError):
                m.load_pinned(raw, changed)


if __name__ == '__main__':
    unittest.main()
