import itertools
import unittest
from research import score11_five_deletion_repair as m
from research.score11_cover_repair import minimal_covers


class FiveDeletionTests(unittest.TestCase):
    def test_five_point_census_matches_small_hitting_set_oracle(self):
        points=set(range(7)); graph=[{0},{1},{2,3,4}]
        covers=minimal_covers(graph,5,1,lambda:0)
        actual=set(m.deletion_sets(points,covers,1,lambda:0))
        expected={frozenset(s) for k in range(6) for s in itertools.combinations(points,k)
                  if all(set(s)&e for e in graph)}
        self.assertEqual(actual,expected)
        self.assertEqual([sum(len(s)==k for s in actual) for k in (3,4,5)], [3,9,10])

    def test_fail_closed_and_timeout(self):
        with self.assertRaises(ValueError):
            m.deletion_sets({0,1,2},[{0,1}],1,lambda:0)
        with self.assertRaises(TimeoutError):
            m.deletion_sets({0,1,2,3},[{0,1,2}],1,lambda:1)


if __name__ == '__main__':
    unittest.main()
