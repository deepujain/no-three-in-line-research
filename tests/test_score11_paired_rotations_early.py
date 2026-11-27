import itertools
import unittest
from research import score11_paired_rotations_early as m
from src.verify import verify_certificate_bruteforce


class EarlyIntersectionTests(unittest.TestCase):
    def test_all_grid3_subsets(self):
        cells=list(itertools.product(range(3),repeat=2))
        for mask in range(1<<len(cells)):
            points=[p for i,p in enumerate(cells) if mask & (1<<i)]
            report=verify_certificate_bruteforce({'n':3,'points':points})
            triples=[set(map(tuple,c['points'])) for c in report['conflicts']]
            expected=set.intersection(*triples) if triples else None
            actual,early=m.conflict_deletion_candidates(points)
            self.assertEqual(actual,expected)
            if early: self.assertEqual(actual,set())

    def test_four_collinear_and_nonempty_common(self):
        four={(0,0),(1,1),(2,2),(3,3)}
        self.assertEqual(m.conflict_deletion_candidates(four),(set(),True))
        shared={(0,0),(1,1),(2,2),(1,0),(2,0)}
        answer,early=m.conflict_deletion_candidates(shared)
        self.assertEqual(answer,{(0,0)});self.assertFalse(early)


if __name__=='__main__':
    unittest.main()
