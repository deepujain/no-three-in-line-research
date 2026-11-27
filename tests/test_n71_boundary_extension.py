import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import n71_boundary_extension as ext

FIXTURE = {'n':3, 'points':[[0,0],[2,2],[0,1],[1,0],[1,2],[2,1]]}


class BoundaryExtensionTests(unittest.TestCase):
    def test_boundary_selection_exhaustive_tiny_arithmetic(self):
        n=11; orbits=ext.boundary_orbits(n); choices=ext.selections(n)
        self.assertEqual(len(orbits),12); self.assertEqual(len(choices),51)
        boundary={0,1,2,3,7,8,9,10}
        all_choices=[]
        for ids in itertools.combinations(range(12),4):
            points=[p for i in ids for p in orbits[i][1]]
            if all(sum(y==r for x,y in points)==2 for r in boundary):
                all_choices.append(ids)
        self.assertEqual(tuple(all_choices),choices)
        for ids in choices:
            points=[p for i in ids for p in orbits[i][1]]
            self.assertEqual(len(set(points)),16)
            self.assertTrue(all(x in boundary and y in boundary and x!=y and x+y!=n-1 for x,y in points))
            self.assertTrue(all(sum(x==r for x,y in points)==2 for r in boundary))

    def test_tiny_fixture_and_full_candidate_check(self):
        self.assertTrue(ext.validate_fixture(FIXTURE))
        with tempfile.TemporaryDirectory() as d:
            result=ext.check_extensions(FIXTURE,10,Path(d))
            self.assertTrue(result['complete'])
            self.assertEqual(result['completed_candidates'],51)
            self.assertEqual(len(result['candidate_checks']),51)
            self.assertEqual(len(list(Path(d).glob('witness-*.json'))),result['valid_candidates'])

    def test_invalid_fixture_and_input(self):
        for f in ({'n':3,'points':[[0,0],[0,0]]}, {'n':3,'points':[[0,0],[1,1],[2,2]]}):
            with self.assertRaises(ValueError): ext.validate_fixture(f)
        for n in (True,8,10):
            with self.assertRaises(ValueError):ext.boundary_orbits(n)

    def test_timeout_keeps_partial_result_incomplete(self):
        ticks=iter((0,2,2))
        with tempfile.TemporaryDirectory() as d:
            result=ext.check_extensions(FIXTURE,1,Path(d),clock=lambda:next(ticks))
        self.assertEqual(result['status'],'timeout')
        self.assertFalse(result['complete'])
        self.assertEqual(result['completed_candidates'],0)

    def test_immediate_witness_write(self):
        fake = {'valid':True,'point_count':22,'normalized_sha256':'a'*64}
        with tempfile.TemporaryDirectory() as d:
            writes=[]
            def save(path,data):writes.append(path)
            with patch.object(ext,'verify_certificate',return_value=fake), \
                 patch.object(ext,'verify_certificate_bruteforce',return_value=fake), \
                 patch.object(ext,'validate_fixture',return_value='b'*64), \
                 patch.object(ext,'atomic',side_effect=save):
                result=ext.check_extensions(FIXTURE,10,Path(d))
            self.assertEqual(len(writes),51)
            self.assertEqual(result['valid_candidates'],51)


if __name__=='__main__':unittest.main()
