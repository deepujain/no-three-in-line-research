import collections
import unittest
from research.diagonal_rowbatch_tiny import census
from research.diagonal_secant_dfs_fast import search
from tests.test_diagonal_secant_dfs import reference


class RowBatchTests(unittest.TestCase):
    def test_full_census_unique_and_matches_original(self):
        for n in (3,4,5):
            with self.subTest(n=n):
                visits=[];result=census(n,on_witness=lambda c:visits.append((c['metadata']['deficit'],c['metadata']['diagonal'],frozenset(map(tuple,c['points'])))))
                original=[];old=search(n,120,1000000,on_witness=lambda c:original.append((c['metadata']['deficit'],c['metadata']['diagonal'],frozenset(map(tuple,c['points'])))))
                self.assertEqual(old['status'],'all_declared_slices_exhausted')
                self.assertEqual(len(visits),len(set(visits)))
                self.assertEqual(len(visits),len({v[2] for v in visits}))
                self.assertEqual(set(visits),set(original))
                self.assertEqual({x[2] for x in visits},reference(n))
                self.assertEqual(result['witness_visits'],len(visits))
                byslice=collections.Counter((d,t) for d,t,_ in visits)
                for row in result['slice_results']:
                    self.assertEqual(row['witness_visits'],byslice[row['deficit'],row['diagonal']])

    def test_tiny_limit_and_indices(self):
        for n in (1,6,True):
            with self.assertRaises(ValueError):census(n)
        for values in ([],[0,0],[3],[True]):
            with self.assertRaises(ValueError):census(3,deficits=values)
        selected=[]
        census(3,deficits=[2],diagonals=[0],on_witness=lambda c:selected.append(c))
        self.assertTrue(selected)
        self.assertTrue(all(c['metadata']['deficit']==2 and c['metadata']['diagonal']==0 for c in selected))


if __name__=='__main__':unittest.main()
