import itertools
import unittest
from research import score11_paired_rotations as m
from src.verify import verify_certificate_bruteforce


class PairedRotationTests(unittest.TestCase):
    def test_simultaneous_rotations_against_direct_construction(self):
        for n in (3,5):
            permutations=[list(range(n)),[(r+1)%n for r in range(n)]]
            original={(r,permutations[c][r]) for c in (0,1) for r in range(n)}
            saw_cancellation=saw_collision=False
            for r0,r1,s0,s1 in itertools.product(itertools.combinations(range(n),3),itertools.combinations(range(n),3),(-1,1),(-1,1)):
                new=m.rotated_pair(permutations,(r0,r1),(s0,s1))
                shifted=[p[:] for p in permutations]
                for color,rows,sign in ((0,r0,s0),(1,r1,s1)):
                    vals=[permutations[color][r] for r in rows]
                    for i,r in enumerate(rows): shifted[color][r]=vals[(i+sign)%3]
                oracle={(r,shifted[c][r]) for c in (0,1) for r in range(n)}
                if len(oracle)!=2*n:
                    saw_collision=True; self.assertIsNone(new); continue
                self.assertEqual(new,oracle)
                if len(original-new)<6: saw_cancellation=True
                report=verify_certificate_bruteforce({'n':n,'points':[list(p) for p in sorted(new)]})
                conflicts=[set(map(tuple,c['points'])) for c in report['conflicts']]
                expected=None if not conflicts else set.intersection(*conflicts)
                self.assertEqual(m.conflict_deletion_candidates(new),expected)
                old=verify_certificate_bruteforce({'n':n,'points':[list(p) for p in sorted(original)]})
                old_conflicts=[set(map(tuple,c['points'])) for c in old['conflicts']]
                unhit=[x for x in old_conflicts if not x&(original-new)]
                self.assertEqual(m.old_conflict_possible(old_conflicts,original-new),not unhit or bool(set.intersection(*unhit)))
            self.assertTrue(saw_collision)
            self.assertTrue(saw_cancellation)

    def test_surviving_old_triples_and_empty_case(self):
        a,b,c,d,e=range(5)
        self.assertTrue(m.old_conflict_possible([{a,b,c},{a,d,e}],set()))
        self.assertFalse(m.old_conflict_possible([{a,b,c},{d,e,5}],set()))
        self.assertTrue(m.old_conflict_possible([{a,b,c}],{a}))
        self.assertIsNone(m.conflict_deletion_candidates({(0,0),(1,2),(2,1)}))


if __name__=='__main__':
    unittest.main()
