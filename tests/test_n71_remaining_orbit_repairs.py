"""Manifest arithmetic, tiny n13 subsets and injected batch accounting only."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import n71_remaining_orbit_repairs as batch
from research import n71_noncentral_orbit_repair as previous

RETAINED = ((4,4),(5,6),(6,5),(6,7),(7,6),(8,8))
REMOVED = ((4,7),(5,4),(7,8),(8,5))
SOURCE = {(x-4,y-4) for x,y in RETAINED+REMOVED}
CASES = [{'source_orbit_index':i,'points':[[x-4,y-4] for x,y in REMOVED]} for i in range(3)]


class RemainingRepairTests(unittest.TestCase):
    def test_frozen33_manifest_exact_source_coverage_coordinate_only(self):
        raw = (batch.ROOT/'data/published-n71-rct4.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),batch.FIXTURE_SHA256)
        fixture = json.loads(raw)
        manifest_raw = batch.CASE_MANIFEST.read_bytes()
        cases = batch.validate_cases(fixture,manifest_raw)
        self.assertEqual(len(cases),33)
        self.assertEqual([c['source_orbit_index'] for c in cases],list(range(1,19))+list(range(20,35)))
        points = {tuple(p) for p in fixture['points']}
        groups = sorted({tuple(sorted(((x,y),(y,70-x),(70-x,70-y),(70-y,x))))
                         for x,y in points if x != y})
        kept = {tuple(tuple(p) for p in c['points']) for c in cases}
        self.assertEqual(kept|{batch.CENTRAL,batch.FIRST},set(groups))
        self.assertFalse(kept.intersection((batch.CENTRAL,batch.FIRST)))
        self.assertTrue(all(len({abs(v-35) for p in orbit for v in p})==2 and
                            0 not in {abs(v-35) for p in orbit for v in p} for orbit in kept))
        with self.assertRaises(ValueError):
            batch.validate_cases(fixture,manifest_raw+b' ')

    def test_parameterized_tiny_case_matches_frozen_first_checker(self):
        report = batch.evaluate_deletion(13,RETAINED,REMOVED,check=lambda:None,
                                        on_witness=lambda *_:self.fail('unexpected witness'))
        previous_report = previous._evaluate(13,RETAINED,REMOVED,25,Path('.'))
        self.assertTrue(report['complete'])
        for key in ('candidate_orbit_checks','candidate_checks','completed_candidates',
                    'valid_candidates','deleted_edge_id','radius_demands'):
            self.assertEqual(report[key],previous_report[key])
        self.assertEqual(report['completed_candidates'],1094)
        self.assertEqual(sum(r['readds_deleted'] for r in report['candidate_checks']),51)

    def test_parameterized_survivors_dual_checked_and_witness_saved_first(self):
        calls = []
        def negative(cert):
            calls.append(cert)
            return {'valid':False,'normalized_sha256':'a'*64,
                    'conflicts':[{'points':[[0,0],[1,1],[2,2]]}]}
        with patch.object(batch,'first_added_conflict',return_value=None):
            report = batch.evaluate_deletion(13,RETAINED,REMOVED,check=lambda:None,
                on_witness=lambda *_:self.fail('unexpected witness'),verifiers=(negative,negative))
        self.assertEqual(len(calls),2188)
        self.assertTrue(report['complete'])
        saved = []
        def positive(_):return {'valid':True,'normalized_sha256':'b'*64}
        with patch.object(batch,'first_added_conflict',return_value=None):
            report = batch.evaluate_deletion(13,RETAINED,REMOVED,check=lambda:None,
                on_witness=lambda *args:saved.append(args),verifiers=(positive,positive))
        self.assertEqual(len(saved),1)
        self.assertEqual((report['status'],report['complete'],report['completed_candidates']),('witness',False,1))
        self.assertEqual(len(saved[0][0]['points']),26)

    def test_partial_filter_record_preserved(self):
        with patch.object(batch,'first_added_conflict',side_effect=[None,TimeoutError('stop')]):
            report = batch.evaluate_deletion(13,RETAINED,REMOVED,check=lambda:None,on_witness=lambda *_:None)
        self.assertEqual(report['status'],'timeout')
        self.assertEqual(len(report['candidate_orbit_checks']),1)
        self.assertEqual(report['completed_candidates'],0)
        self.assertFalse(report['complete'])

    def test_shared_batch_complete_partial_unstarted_and_witness_accounting(self):
        seen = []
        def fake(_n,retained,removed,*,check,on_witness):
            self.assertEqual(retained,RETAINED)
            self.assertEqual(removed,REMOVED)
            seen.append(1)
            return {'status':'complete' if len(seen)==1 else 'timeout','complete':len(seen)==1,
                    'completed_candidates':1094 if len(seen)==1 else 3,'valid_candidates':0}
        report = batch.evaluate_batch(13,SOURCE,CASES,check=lambda:None,on_witness=lambda *_:None,evaluator=fake)
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[1])
        self.assertEqual(report['unstarted_case_indices'],[2])
        self.assertEqual(report['completed_candidates'],1097)
        self.assertFalse(report['complete'])
        def done(*args,**kwargs):
            return {'status':'complete','complete':True,'completed_candidates':1094,'valid_candidates':0}
        cases = [dict(CASES[0],source_orbit_index=i) for i in range(33)]
        report = batch.evaluate_batch(13,SOURCE,cases,check=lambda:None,on_witness=lambda *_:None,evaluator=done)
        self.assertTrue(report['complete'])
        self.assertEqual((report['completed_cases'],report['completed_candidates']),(33,36102))
        saved = []
        def witness(n,retained,removed,*,check,on_witness):
            on_witness({'n':13,'points':[]},(1,2,3,4,5),'c'*64)
            return {'status':'witness','complete':False,'completed_candidates':1,'valid_candidates':1}
        report = batch.evaluate_batch(13,SOURCE,CASES,check=lambda:None,
            on_witness=lambda *args:saved.append(args),evaluator=witness)
        self.assertEqual(report['status'],'witness')
        self.assertEqual(len(saved),1)
        self.assertEqual(saved[0][0],CASES[0])
        self.assertEqual(report['unstarted_case_indices'],[1,2])

    def test_deadline_between_cases_keeps_completed_prefix(self):
        checks = []
        def check():
            checks.append(1)
            if len(checks)==2:raise TimeoutError('shared deadline')
        def done(*args,**kwargs):
            return {'status':'complete','complete':True,'completed_candidates':1094,'valid_candidates':0}
        report = batch.evaluate_batch(13,SOURCE,CASES,check=check,on_witness=lambda *_:None,evaluator=done)
        self.assertEqual(report['status'],'timeout')
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[])
        self.assertEqual(report['unstarted_case_indices'],[1,2])
        self.assertFalse(report['complete'])

    def test_strict_cli_scope_budget(self):
        for seconds in (True,0,26,float('nan')):
            with self.assertRaises(ValueError):batch.check_batch({'n':71},seconds,Path('.'))
        with self.assertRaises(ValueError):batch.check_batch({'n':3},25,Path('.'))


if __name__ == '__main__':
    unittest.main()
