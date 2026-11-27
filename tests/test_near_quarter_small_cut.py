import itertools
import unittest
from research.near_quarter_small_cut import small_cut_obstruction as cut
from research.near_quarter_radius_graph import component_obstruction


def feasible(demands,edges):
    for mask in range(1<<len(edges)):
        degree=[0]*len(demands)
        for i,(u,v) in enumerate(edges):
            if mask & (1<<i): degree[u]+=1; degree[v]+=1
        if degree==list(demands): return True
    return False


class SmallCutTests(unittest.TestCase):
    def test_exhaustive_tiny_graphs_and_parallel_edges(self):
        counts=[0,0]
        # Every simple graph on four vertices and every demand vector.
        for n,multiplicity in ((3,range(3)),(4,range(2))):
            pairs=list(itertools.combinations(range(n),2))
            for weights in itertools.product(multiplicity,repeat=len(pairs)):
                edges=[edge for edge,w in zip(pairs,weights) for _ in range(w)]
                for demands in itertools.product(range(3),repeat=n):
                    answer=cut(demands,edges)
                    possible=feasible(demands,edges)
                    if answer is not None: counts[0]+=1; self.assertFalse(possible)
                    if possible: counts[1]+=1; self.assertIsNone(answer)
        self.assertGreater(counts[0],0);self.assertGreater(counts[1],0)

    def test_distinct_synthetic_and_parallel_capacity(self):
        demands=[2,2,2,1,1]
        edges=[(0,1),(0,3),(1,4),(2,3),(2,4),(3,4)]
        self.assertIsNone(component_obstruction(demands,edges))
        self.assertFalse(feasible(demands,edges))
        self.assertEqual(cut(demands,edges),(0,1,2))
        self.assertIsNone(cut([2,2],[(0,1),(0,1)]))
        self.assertEqual(cut([2,2],[(0,1)]),(0,1))

    def test_interruptions_and_invalid_edges(self):
        demands=[2,2,2,1,1];edges=[(0,1),(0,3),(1,4),(2,3),(2,4),(3,4)]
        for ds,es in ((demands,edges),([2,2],[(0,1),(0,1)])):
            seen=[]
            def count(): seen.append(None)
            cut(ds,es,count)
            for stop in range(len(seen)):
                state=[0]
                def check():
                    if state[0]==stop: raise TimeoutError
                    state[0]+=1
                with self.assertRaises(TimeoutError): cut(ds,es,check)
        for invalid in ([(0,0)],[(0,5)],[(True,1)]):
            with self.assertRaises(ValueError): cut(demands,invalid)


if __name__=='__main__':
    unittest.main()
