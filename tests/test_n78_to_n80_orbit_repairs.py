"""Small even-grid geometry, coordinate-only manifest and injected accounting."""
import hashlib
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import n78_to_n80_orbit_repairs as repair
from src.verify import verify_certificate, verify_certificate_bruteforce

LOOP_REMOVED=((1,1),(1,2),(2,1),(2,2))
RETAINED=((1,5),(2,1),(3,3),(3,4),(4,3),(4,4),(5,6),(6,2))
REMOVED=((1,2),(2,6),(5,1),(6,5))


class EvenRepairTests(unittest.TestCase):
    def test_even_constructor_complete_orbit_partition_including_loops(self):
        for n in (4,6,8):
            radii=range(1,n,2)
            specs=[(u,v,s) for u,v in itertools.combinations_with_replacement(radii,2)
                   for s in ((1,) if u==v else (1,-1))]
            actual={repair.orbit_points(n,e) for e in specs}
            expected={tuple(sorted(((x,y),(y,n-1-x),(n-1-x,n-1-y),(n-1-y,x))))
                      for x in range(n) for y in range(n)}
            self.assertEqual(actual,expected)
            self.assertEqual(len(actual),n*n//4)
            self.assertEqual(sum(len(o) for o in actual),n*n)

    def test_loop_inclusive_factors_against_every_actual_tiny_row_load(self):
        for n,retained,removed,expected in ((4,(),LOOP_REMOVED,2),(8,RETAINED,REMOVED,6)):
            inner=tuple(sorted({abs(2*v-(n-1)) for p in removed for v in p}))
            outer=n-1;loop=len(inner)==1
            edges=repair.edge_specs(inner,outer)
            demands={r:2 if loop else 1 for r in inner};demands[outer]=2
            orbits=[repair.orbit_points(n,e) for e in edges]
            independent=[]
            for ids in itertools.combinations(range(len(edges)),2):
                points=list(retained)+[p for i in ids for p in orbits[i]]
                if all(sum(y==r for x,y in points)==2 for r in range(n)):
                    independent.append(ids)
                    self.assertTrue(all(sum(x==r for x,y in points)==2 for r in range(n)))
            choices=repair.degree_choices(edges,demands)
            self.assertEqual(choices,tuple(independent))
            self.assertEqual(len(choices),expected)
            outer_id=edges.index((outer,outer,1));removed_id=orbits.index(removed)
            self.assertEqual(sum(outer_id in ids for ids in choices),1 if loop else 2)
            self.assertEqual(sum(removed_id in ids for ids in choices),1)

    def test_pinned39_manifest_coordinate_only(self):
        raw=(repair.ROOT/'data/published-n78.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),repair.FIXTURE_SHA256)
        cases=repair.validate_cases(json.loads(raw),repair.CASE_MANIFEST.read_bytes())
        self.assertEqual([c['source_orbit_index'] for c in cases],list(range(39)))
        self.assertEqual([c['source_orbit_index'] for c in cases if c['deleted_is_diagonal_loop']],[38])
        self.assertEqual(sum(c['degree_choices_including_outer_loop'] for c in cases),230)
        self.assertEqual(sum(c['outer_loop_rejections_by_proof'] for c in cases),77)
        self.assertEqual(sum(c['degree_choices_after_outer_loop_prune'] for c in cases),153)
        with self.assertRaises(ValueError):
            repair.validate_cases(json.loads(raw),repair.CASE_MANIFEST.read_bytes()+b' ')

    def test_all_remaining_survivors_dual_checked_all_raw_records_preserved(self):
        for n,retained,removed,proof,total,outer_count in (
                (4,(),LOOP_REMOVED,((0,0),(1,1),(2,2)),2,1),
                (8,RETAINED,REMOVED,((0,0),(3,3),(4,4)),6,2)):
            calls=[]
            def negative(cert):
                calls.append(cert)
                return {'valid':False,'normalized_sha256':'a'*64,
                        'conflicts':[{'points':[[0,0],[1,1],[2,2]]}]}
            with patch.object(repair,'first_added_conflict',return_value=None):
                report=repair.evaluate_deletion(n,retained,removed,proof,check=lambda:None,
                    on_witness=lambda *_:self.fail('unexpected'),verifiers=(negative,negative))
            self.assertTrue(report['complete'])
            self.assertEqual(report['completed_candidates'],total)
            self.assertEqual(report['proof_rejected_candidates'],outer_count)
            self.assertEqual(len(calls),2*(total-outer_count))
            self.assertEqual(sum(r['readds_deleted'] for r in report['candidate_checks']),1)
            self.assertTrue(all(r['result']=='outer_loop_proof' for r in report['candidate_checks'] if r['readds_deleted']))

    def test_real_tiny_filter_proofs_and_early_valid_witness(self):
        self.assertTrue(verify_certificate({'n':8,'points':list(RETAINED)})['valid'])
        for n,retained,removed,proof in ((4,(),LOOP_REMOVED,((0,0),(1,1),(2,2))),
                                       (8,RETAINED,REMOVED,((0,0),(3,3),(4,4)))):
            saved=[]
            report=repair.evaluate_deletion(n,retained,removed,proof,check=lambda:None,
                                            on_witness=lambda *args:saved.append(args))
            for record in report['candidate_checks']:
                if record['result']=='outer_loop_proof':
                    (ax,ay),(bx,by),(cx,cy)=record['blocking_triple']
                    self.assertEqual((bx-ax)*(cy-ay),(by-ay)*(cx-ax))
            if report['status']=='witness':
                self.assertEqual(len(saved),1)
                self.assertTrue(all(v(saved[0][0])['valid'] for v in
                                    (verify_certificate,verify_certificate_bruteforce)))
                self.assertFalse(report['complete'])
            else:self.assertTrue(report['complete'])

    def test_bad_proof_and_partial_filter_timeout_reject_completeness(self):
        with patch.object(repair,'first_added_conflict',return_value=[[0,0],[1,1],[2,2]]):
            with self.assertRaisesRegex(RuntimeError,'determinant'):
                repair.evaluate_deletion(8,RETAINED,REMOVED,((0,0),(3,3),(3,4)),
                                         check=lambda:None,on_witness=lambda *_:None)
            with self.assertRaisesRegex(RuntimeError,'absent'):
                repair.evaluate_deletion(8,RETAINED,REMOVED,((0,0),(3,3),(7,6)),
                                         check=lambda:None,on_witness=lambda *_:None)
        with patch.object(repair,'first_added_conflict',side_effect=[None,TimeoutError('stop')]):
            report=repair.evaluate_deletion(8,RETAINED,REMOVED,((0,0),(3,3),(4,4)),
                                            check=lambda:None,on_witness=lambda *_:None)
        self.assertEqual(report['status'],'timeout')
        self.assertEqual(len(report['candidate_orbit_checks']),1)
        self.assertFalse(report['complete'])

    def test_batch_complete_partial_unstarted_and_shared_deadline(self):
        source={(x-1,y-1) for x,y in RETAINED+REMOVED}
        cases=[{'source_orbit_index':i,'points':[[x-1,y-1] for x,y in REMOVED],
                'degree_choices_including_outer_loop':6 if i<38 else 2,
                'outer_loop_rejections_by_proof':2 if i<38 else 1} for i in range(39)]
        seen=[]
        def done(*args,**kwargs):
            seen.append(1);loop=len(seen)==39
            return {'status':'complete','complete':True,'completed_candidates':2 if loop else 6,
                    'proof_rejected_candidates':1 if loop else 2,'valid_candidates':0}
        report=repair.evaluate_batch(8,source,cases,(),check=lambda:None,on_witness=lambda *_:None,evaluator=done)
        self.assertTrue(report['complete'])
        self.assertEqual((report['completed_cases'],report['completed_candidates'],report['proof_rejected_candidates']),(39,230,77))
        seen.clear()
        def partial(*args,**kwargs):
            seen.append(1)
            return {'status':'complete' if len(seen)==1 else 'timeout','complete':len(seen)==1,
                    'completed_candidates':6 if len(seen)==1 else 1,
                    'proof_rejected_candidates':2 if len(seen)==1 else 0,'valid_candidates':0}
        report=repair.evaluate_batch(8,source,cases,(),check=lambda:None,on_witness=lambda *_:None,evaluator=partial)
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[1])
        self.assertEqual(report['unstarted_case_indices'],list(range(2,39)))
        self.assertFalse(report['complete'])
        ticks=[];seen.clear()
        def deadline():
            ticks.append(1)
            if len(ticks)==2:raise TimeoutError('stop')
        report=repair.evaluate_batch(8,source,cases,(),check=deadline,on_witness=lambda *_:None,evaluator=done)
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[])
        self.assertEqual(report['unstarted_case_indices'],list(range(1,39)))

    def test_strict_even_scope_and_soft_budget(self):
        for n,e in ((5,(1,3,1)),(4,(0,3,1)),(4,(1,2,1)),(4,(1,1,-1)),(4,(1,5,1))):
            with self.assertRaises(ValueError):repair.orbit_points(n,e)
        for seconds in (True,0,26,float('nan')):
            with self.assertRaises(ValueError):repair.check_batch({'n':78},seconds,Path('.'))
        with self.assertRaises(ValueError):repair.check_batch({'n':73},25,Path('.'))


if __name__=='__main__':unittest.main()
