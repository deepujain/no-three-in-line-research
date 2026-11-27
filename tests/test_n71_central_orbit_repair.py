"""Only n3->n11 tiny geometry and abstract arithmetic; no n79 construction."""
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import n71_central_orbit_repair as repair
from src.verify import verify_certificate

FIXTURE = {'n': 3, 'points': [[0,0], [2,2], [0,1], [1,0], [1,2], [2,1]]}


class CentralRepairTests(unittest.TestCase):
    def test_all_raw_tiny_degree_cases_against_actual_row_loads(self):
        edges = repair.edge_specs(1, (2,3,4,5))
        self.assertEqual(len(edges), 25)
        choices = repair.degree_choices(edges, {0:1, 1:1, 2:2, 3:2, 4:2, 5:2})
        orbits = [repair.edge_points(11, e) for e in edges]
        self.assertEqual(len(set(orbits)), 25)
        row_vectors = [tuple(sum(y == r for x,y in orbit) for r in range(11)) for orbit in orbits]
        target = tuple(1 if r in (4,6) else 2 for r in range(11))
        independent = []
        for ids in itertools.combinations(range(25), 5):
            if all(sum(row_vectors[i][r] for i in ids) == target[r] for r in range(11)):
                independent.append(ids)
        self.assertEqual(choices, tuple(independent))
        removed_id = edges.index((0,1,1))
        self.assertEqual(sum(removed_id in ids for ids in choices), 51)
        self.assertEqual(len(choices), 547)
        for ids in choices:
            points = [(4,4), (6,6)]+[p for i in ids for p in orbits[i]]
            self.assertEqual(len(set(points)), 22)
            self.assertTrue(all(sum(x == r for x,y in points) == 2 for r in range(11)))

    def test_exact_filter_agrees_with_independent_small_verifier(self):
        base = ((0,0), (1,2))
        available = [(x,y) for x in range(3) for y in range(3) if (x,y) not in base]
        for added in itertools.combinations(available, 3):
            conflict = repair.first_added_conflict(base, added)
            self.assertEqual(conflict is None, verify_certificate({'n':3,'points':list(base+added)})['valid'])
            if conflict:
                (ax,ay),(bx,by),(cx,cy) = conflict
                self.assertEqual((bx-ax)*(cy-ay), (by-ay)*(cx-ax))
                self.assertTrue(all(tuple(p) in base+added for p in conflict))

    def test_tiny_complete_preserves_all_readdition_cases(self):
        with tempfile.TemporaryDirectory() as out:
            report = repair.check_case(FIXTURE, 25, Path(out))
        self.assertTrue(report['complete'])
        self.assertEqual(report['status'], 'complete')
        self.assertEqual(report['completed_candidates'], 547)
        self.assertEqual(sum(r['readds_deleted'] for r in report['candidate_checks']), 51)
        self.assertEqual(len(report['candidate_orbit_checks']), 25)
        self.assertEqual(len({tuple(r['edge_ids']) for r in report['candidate_checks']}), 547)
        orbit_checks = {r['edge_id']:r for r in report['candidate_orbit_checks']}
        for record in report['candidate_checks']:
            if record['result'] == 'filtered_orbit':
                self.assertFalse(orbit_checks[record['blocking_edge_id']]['admissible'])
            else:
                self.assertFalse(record['valid'])
        self.assertEqual(report['valid_candidates'], 0)

    def test_every_filter_survivor_gets_both_final_verifiers(self):
        fake = {'valid':False, 'point_count':22, 'normalized_sha256':'a'*64,
                'conflicts':[{'points':[[0,0],[1,1],[2,2]]}]}
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',return_value=None), \
                patch.object(repair,'verify_certificate',return_value=fake) as fast, \
                patch.object(repair,'verify_certificate_bruteforce',return_value=fake) as brute:
            report = repair.check_case(FIXTURE,25,Path(out))
        self.assertTrue(report['complete'])
        self.assertEqual(fast.call_count,547)
        self.assertEqual(brute.call_count,547)

    def test_witness_is_saved_before_early_return(self):
        fake = {'valid':True, 'point_count':22, 'normalized_sha256':'a'*64}
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair,'first_added_conflict',return_value=None), \
                patch.object(repair,'verify_certificate',return_value=fake), \
                patch.object(repair,'verify_certificate_bruteforce',return_value=fake), \
                patch.object(repair,'atomic') as save:
            report = repair.check_case(FIXTURE,25,Path(out))
        self.assertEqual(report['status'],'witness')
        self.assertFalse(report['complete'])
        self.assertEqual(report['completed_candidates'],1)
        save.assert_called_once()
        self.assertEqual(save.call_args.args[0].name,'witness-'+('a'*64)+'.json')

    def test_timeout_during_filter_keeps_partial_evidence(self):
        with tempfile.TemporaryDirectory() as out, \
                patch.object(repair, 'first_added_conflict', side_effect=[None, TimeoutError('stop')]):
            report = repair.check_case(FIXTURE,25,Path(out))
        self.assertEqual(report['status'], 'timeout')
        self.assertFalse(report['complete'])
        self.assertEqual(len(report['candidate_orbit_checks']), 1)
        self.assertEqual(report['completed_candidates'], 0)

    def test_timeout_and_strict_budget(self):
        ticks = iter((0,2,2))
        with tempfile.TemporaryDirectory() as out:
            report=repair.check_case(FIXTURE,1,Path(out),clock=lambda:next(ticks))
        self.assertFalse(report['complete'])
        self.assertEqual((report['status'],report['completed_candidates']),('timeout',0))
        for seconds in (True,0,26,float('nan')):
            with self.assertRaises(ValueError):
                repair.check_case(FIXTURE,seconds,Path('.'))
        with self.assertRaises(ValueError):
            repair.check_case({'n':3,'points':[[0,0],[0,0]]},25,Path('.'))


if __name__ == '__main__':
    unittest.main()
