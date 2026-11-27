"""Abstract degree cases and n13 prepared subsets; no full tiny-source claim."""
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import n71_noncentral_orbit_repair as repair
from src.verify import verify_certificate

RETAINED = ((4,4),(5,6),(6,5),(6,7),(7,6),(8,8))
REMOVED = ((4,7),(5,4),(7,8),(8,5))
DEMANDS = {1:1,2:1,3:2,4:2,5:2,6:2}


class NoncentralRepairTests(unittest.TestCase):
    def test_1094_against_all_actual_tiny_row_loads(self):
        edges = repair.edge_specs((1,2),(3,4,5,6))
        self.assertEqual(len(edges),30)
        orbits = [repair.edge_points(13,e) for e in edges]
        self.assertEqual(len(set(orbits)),30)
        vectors = [tuple(sum(y==r for x,y in orbit) for r in range(13)) for orbit in orbits]
        target = tuple(2-sum(y==r for x,y in RETAINED) for r in range(13))
        expected = tuple(ids for ids in itertools.combinations(range(30),5)
            if all(sum(vectors[i][r] for i in ids)==target[r] for r in range(13)))
        choices = repair.degree_choices(edges,DEMANDS)
        self.assertEqual(choices,expected)
        removed_id = orbits.index(REMOVED)
        self.assertEqual(sum(removed_id in ids for ids in choices),51)
        self.assertEqual(len(choices),1094)
        self.assertTrue(verify_certificate({'n':13,'points':list(RETAINED)})['valid'])
        for ids in choices:
            points = list(RETAINED)+[p for i in ids for p in orbits[i]]
            self.assertEqual(len(set(points)),26)
            self.assertTrue(all(sum(x==r for x,y in points)==2 for r in range(13)))

    def test_tiny_prepared_subset_complete_and_readdition(self):
        with tempfile.TemporaryDirectory() as out:
            report = repair._evaluate(13,RETAINED,REMOVED,25,Path(out))
        self.assertTrue(report['complete'])
        self.assertEqual(report['completed_candidates'],1094)
        self.assertEqual(sum(r['readds_deleted'] for r in report['candidate_checks']),51)
        self.assertEqual(len(report['candidate_orbit_checks']),30)
        self.assertEqual(report['valid_candidates'],0)

    def test_retained_opposite_orientation_is_explicitly_rejected(self):
        opposite = repair.edge_points(13,(1,2,-1))
        # Synthetic overlap fixture: only the defensive overlap branch is tested.
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',return_value=[[0,0],[1,1],[2,2]]) as filt:
            report = repair._evaluate(13,RETAINED+opposite,REMOVED,25,Path(out))
        matches = [r for r in report['candidate_orbit_checks'] if r['edge']==[1,2,-1]]
        self.assertEqual(len(matches),1)
        self.assertTrue(matches[0]['retained_overlap'])
        self.assertFalse(matches[0]['admissible'])
        self.assertEqual(filt.call_count,29)
        self.assertTrue(report['complete'])

    def test_every_survivor_dual_checked_and_early_witness(self):
        negative = {'valid':False,'normalized_sha256':'a'*64,
                    'conflicts':[{'points':[[0,0],[1,1],[2,2]]}]}
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',return_value=None), \
                patch.object(repair,'verify_certificate',return_value=negative) as first, \
                patch.object(repair,'verify_certificate_bruteforce',return_value=negative) as second:
            report = repair._evaluate(13,RETAINED,REMOVED,25,Path(out))
        self.assertTrue(report['complete'])
        self.assertEqual((first.call_count,second.call_count),(1094,1094))
        positive = {'valid':True,'normalized_sha256':'b'*64}
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',return_value=None), \
                patch.object(repair,'verify_certificate',return_value=positive), \
                patch.object(repair,'verify_certificate_bruteforce',return_value=positive), \
                patch.object(repair,'atomic') as save:
            report = repair._evaluate(13,RETAINED,REMOVED,25,Path(out))
        self.assertEqual((report['status'],report['completed_candidates']),('witness',1))
        self.assertFalse(report['complete'])
        save.assert_called_once()

    def test_timeout_before_and_during_filter(self):
        ticks = iter((0,2,2))
        with tempfile.TemporaryDirectory() as out:
            report = repair._evaluate(13,RETAINED,REMOVED,1,Path(out),clock=lambda:next(ticks))
        self.assertEqual((report['status'],report['completed_candidates']),('timeout',0))
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',side_effect=[None,TimeoutError('stop')]):
            report = repair._evaluate(13,RETAINED,REMOVED,25,Path(out))
        self.assertEqual(report['status'],'timeout')
        self.assertEqual(len(report['candidate_orbit_checks']),1)
        self.assertFalse(report['complete'])

    def test_strict_scope_and_inputs(self):
        for seconds in (True,0,26,float('nan')):
            with self.assertRaises(ValueError):
                repair._evaluate(13,RETAINED,REMOVED,seconds,Path('.'))
        with self.assertRaises(ValueError):
            repair.check_case({'n':5,'points':[]},25,Path('.'))
        for inner,outer in (((0,1),(2,3,4,5)),((1,1),(2,3,4,5)),((1,3),(2,4,5,6))):
            with self.assertRaises(ValueError):
                repair.edge_specs(inner,outer)


if __name__ == '__main__':
    unittest.main()
