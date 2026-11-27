import itertools
import unittest
from collections import Counter
from research import score11_cover_repair as m
from src.verify import verify_certificate_bruteforce


class CoverRepairTests(unittest.TestCase):
    def test_all_small_hypergraphs_against_combinations(self):
        universe = range(5)
        edges = list(map(frozenset,itertools.combinations(universe,3)))
        for mask in range(1,1 << len(edges)):
            graph = [e for i,e in enumerate(edges) if mask & (1<<i)]
            actual = set(m.minimal_covers(graph, 4, 1, lambda:0))
            expected = set()
            for k in range(5):
                for choice in itertools.combinations(universe,k):
                    s=frozenset(choice)
                    if all(s & e for e in graph) and all(any(s & e == {p} for e in graph) for p in s):
                        expected.add(s)
            self.assertEqual(actual,expected)

    def test_timeout_never_claims_completed_census(self):
        with self.assertRaises(TimeoutError):
            m.minimal_covers([{1,2,3}], 4, 1, lambda:1)

    def test_small_repairs_against_exhaustive_cell_oracle(self):
        for n in (3,5):
            points={(r,c) for r in range(n) for c in (r,(r+1)%n)}
            cert={'n':n,'points':[list(p) for p in sorted(points)]}
            report=verify_certificate_bruteforce(cert)
            conflicts=[set(map(tuple,c['points'])) for c in report['conflicts']]
            for cover in m.minimal_covers(conflicts,4,1,lambda:0):
                retained=points-set(cover)
                self.assertTrue(verify_certificate_bruteforce({'n':n,'points':list(retained)})['valid'])
                rows=sorted({x for x,y in cover}); cols=sorted({y for x,y in cover})
                cells=[p for p in itertools.product(rows,cols) if p not in retained]
                expected=set()
                for size in range(len(cells)+1):
                    for added in itertools.combinations(cells,size):
                        s=retained | set(added)
                        if len(s)<2*n-1 or len(s)>2*n:
                            continue
                        if max(Counter(x for x,y in s).values())>2 or max(Counter(y for x,y in s).values())>2:
                            continue
                        if verify_certificate_bruteforce({'n':n,'points':list(s)})['valid']:
                            expected.add(frozenset(s))
                actual=[]
                m.search_cover(n,points,set(cover),1,lambda:0,lambda s:actual.append(frozenset(s)))
                self.assertEqual(set(actual),expected)
                self.assertEqual(len(actual),len(set(actual)))


if __name__ == '__main__':
    unittest.main()
