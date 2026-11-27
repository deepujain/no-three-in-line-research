import itertools
import unittest
from research import score11_four_deletion_repair as m
from research.score11_cover_repair import minimal_covers


class FourDeletionTests(unittest.TestCase):
    def test_extended_census_matches_all_small_hitting_sets(self):
        points=set(range(7)); graph=[{0},{1},{2,3,4}]
        covers=minimal_covers(graph,4,1,lambda:0)
        self.assertEqual(len(covers),3)
        actual=set(m.deletion_sets(points,covers,1,lambda:0))
        expected={frozenset(s) for k in range(5) for s in itertools.combinations(points,k)
                  if all(set(s)&e for e in graph)}
        self.assertEqual(actual,expected)
        self.assertEqual(sum(len(x)==3 for x in actual),3)
        self.assertEqual(sum(len(x)==4 for x in actual),9)

    def test_fail_closed(self):
        with self.assertRaises(ValueError):
            m.deletion_sets({0,1,2},[{0,1}],1,lambda:0)
        with self.assertRaises(ValueError):
            m.deletion_sets({0,1,2},[{0,1,4}],1,lambda:0)
        with self.assertRaises(TimeoutError):
            m.deletion_sets({0,1,2,3},[{0,1,2}],1,lambda:1)


if __name__ == '__main__':
    unittest.main()
