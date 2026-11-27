"""Coordinate-only pinned manifest, n9/n11 subsets and injected batch tests."""
import itertools
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import n73_one_orbit_repairs as repair
from src.verify import verify_certificate, verify_certificate_bruteforce

CENTRAL_RETAINED = ((3,3),(5,5))
CENTRAL_REMOVED = ((3,4),(4,3),(4,5),(5,4))
POSITIVE_RETAINED = ((3,3),(4,5),(5,4),(5,6),(6,5),(7,7))
POSITIVE_REMOVED = ((3,6),(4,3),(6,7),(7,4))


class N73RepairTests(unittest.TestCase):
    def test_both_degree_counts_against_every_tiny_row_load(self):
        for n,retained,removed,total in ((9,CENTRAL_RETAINED,CENTRAL_REMOVED,62),
                                       (11,POSITIVE_RETAINED,POSITIVE_REMOVED,124)):
            center=n//2
            inner=tuple(sorted({abs(v-center) for p in removed for v in p}))
            outer=tuple(range(center-2,center+1))
            edges=repair.edge_specs(inner,outer)
            orbits=[repair.edge_points(n,e) for e in edges]
            demands={**{r:1 for r in inner},**{r:2 for r in outer}}
            choices=repair.degree_choices(edges,demands)
            vectors=[tuple(sum(y==r for x,y in points) for r in range(n)) for points in orbits]
            target=tuple(2-sum(y==r for x,y in retained) for r in range(n))
            expected=tuple(ids for ids in itertools.combinations(range(len(edges)),4)
                if all(sum(vectors[i][r] for i in ids)==target[r] for r in range(n)))
            self.assertEqual(choices,expected)
            self.assertEqual(len(choices),total)
            self.assertEqual(sum(orbits.index(removed) in ids for ids in choices),8)
            self.assertEqual(len(edges),16 if inner[0]==0 else 20)
            for ids in choices:
                points=list(retained)+[p for i in ids for p in orbits[i]]
                self.assertEqual(len(set(points)),2*n)
                self.assertTrue(all(sum(x==r for x,y in points)==2 for r in range(n)))

    def test_pinned36_manifest_and_radius36_coordinate_only(self):
        fixture=repair.load_pinned(repair.ROOT/'data/published-n73-rct4.raw',
                                   repair.ROOT/'data/published-n73-rct4-candidate.json')
        cases=repair.validate_cases(fixture,repair.CASE_MANIFEST.read_bytes())
        self.assertEqual([c['source_orbit_index'] for c in cases],list(range(36)))
        self.assertEqual(sum(c['degree_choices'] for c in cases),4402)
        self.assertEqual(sum(c['exact_readdition_choices'] for c in cases),288)
        self.assertEqual([c['source_orbit_index'] for c in cases if 0 in c['inner_radii']],[3])
        self.assertTrue(any(36 in c['inner_radii'] for c in cases))
        self.assertEqual(len(repair.edge_specs((1,36),(37,38,39))),20)
        with self.assertRaises(ValueError):
            repair.validate_cases(fixture,repair.CASE_MANIFEST.read_bytes()+b' ')

    def test_real_tiny_filter_and_any_witness_dual_valid(self):
        for n,retained,removed,total in ((9,CENTRAL_RETAINED,CENTRAL_REMOVED,62),
                                       (11,POSITIVE_RETAINED,POSITIVE_REMOVED,124)):
            self.assertTrue(verify_certificate({'n':n,'points':list(retained)})['valid'])
            saved=[]
            report=repair.evaluate_deletion(n,retained,removed,check=lambda:None,
                                            on_witness=lambda *args:saved.append(args))
            if report['status']=='witness':
                self.assertEqual(len(saved),1)
                self.assertTrue(all(v(saved[0][0])['valid'] for v in
                                    (verify_certificate,verify_certificate_bruteforce)))
                self.assertFalse(report['complete'])
            else:
                self.assertTrue(report['complete'])
                self.assertEqual(report['completed_candidates'],total)
                self.assertEqual(sum(r['readds_deleted'] for r in report['candidate_checks']),8)

    def test_surviving_finals_both_checked_and_early_witness(self):
        for n,retained,removed,total in ((9,CENTRAL_RETAINED,CENTRAL_REMOVED,62),
                                       (11,POSITIVE_RETAINED,POSITIVE_REMOVED,124)):
            calls=[]
            def negative(cert):
                calls.append(cert)
                return {'valid':False,'normalized_sha256':'a'*64,
                        'conflicts':[{'points':[[0,0],[1,1],[2,2]]}]}
            with patch.object(repair,'first_added_conflict',return_value=None):
                report=repair.evaluate_deletion(n,retained,removed,check=lambda:None,
                    on_witness=lambda *_:self.fail('unexpected'),verifiers=(negative,negative))
            self.assertEqual(len(calls),2*total)
            self.assertTrue(report['complete'])
        saved=[]
        def positive(_):return {'valid':True,'normalized_sha256':'b'*64}
        with patch.object(repair,'first_added_conflict',return_value=None):
            report=repair.evaluate_deletion(11,POSITIVE_RETAINED,POSITIVE_REMOVED,check=lambda:None,
                on_witness=lambda *args:saved.append(args),verifiers=(positive,positive))
        self.assertEqual((report['status'],report['completed_candidates']),('witness',1))
        self.assertEqual(len(saved),1)
        self.assertFalse(report['complete'])

    def test_opposite_retained_orientation_and_filter_timeout(self):
        opposite=repair.edge_points(11,(1,2,-1))
        with patch.object(repair,'first_added_conflict',return_value=[[0,0],[1,1],[2,2]]) as filt:
            report=repair.evaluate_deletion(11,POSITIVE_RETAINED+opposite,POSITIVE_REMOVED,
                                            check=lambda:None,on_witness=lambda *_:None)
        row=next(r for r in report['candidate_orbit_checks'] if r['edge']==[1,2,-1])
        self.assertTrue(row['retained_overlap'])
        self.assertFalse(row['admissible'])
        self.assertEqual(filt.call_count,19)
        with patch.object(repair,'first_added_conflict',side_effect=[None,TimeoutError('stop')]):
            report=repair.evaluate_deletion(11,POSITIVE_RETAINED,POSITIVE_REMOVED,
                                            check=lambda:None,on_witness=lambda *_:None)
        self.assertEqual(report['status'],'timeout')
        self.assertEqual(len(report['candidate_orbit_checks']),1)
        self.assertFalse(report['complete'])

    def test_batch_complete_and_partial_coverage_shared_deadline(self):
        source={(x-3,y-3) for x,y in POSITIVE_RETAINED+POSITIVE_REMOVED}
        cases=[{'source_orbit_index':i,'points':[[x-3,y-3] for x,y in POSITIVE_REMOVED],
                'degree_choices':124} for i in range(36)]
        cases[3]=dict(cases[3],degree_choices=62)
        done_calls=[]
        def done(*args,**kwargs):
            done_calls.append(1)
            count=62 if len(done_calls)==4 else 124
            return {'status':'complete','complete':True,'completed_candidates':count,'valid_candidates':0}
        report=repair.evaluate_batch(11,source,cases,check=lambda:None,on_witness=lambda *_:None,evaluator=done)
        self.assertTrue(report['complete'])
        self.assertEqual(report['declared_degree_choices'],4402)
        self.assertEqual(report['completed_cases'],36)
        self.assertEqual(report['completed_candidates'],4402)
        seen=[]
        def partial(*args,**kwargs):
            seen.append(1)
            return {'status':'complete' if len(seen)==1 else 'timeout','complete':len(seen)==1,
                    'completed_candidates':124 if len(seen)==1 else 2,'valid_candidates':0}
        report=repair.evaluate_batch(11,source,cases,check=lambda:None,on_witness=lambda *_:None,evaluator=partial)
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[1])
        self.assertEqual(report['unstarted_case_indices'],list(range(2,36)))
        self.assertEqual(report['completed_candidates'],126)
        self.assertFalse(report['complete'])
        ticks=[]
        def deadline():
            ticks.append(1)
            if len(ticks)==2:raise TimeoutError('shared stop')
        report=repair.evaluate_batch(11,source,cases,check=deadline,on_witness=lambda *_:None,evaluator=done)
        self.assertEqual(report['completed_case_indices'],[0])
        self.assertEqual(report['partial_case_indices'],[])
        self.assertEqual(report['unstarted_case_indices'],list(range(1,36)))

    def test_strict_scope_and_radii(self):
        for seconds in (True,0,26,float('nan')):
            with self.assertRaises(ValueError):repair.check_batch({'n':73},seconds,Path('.'))
        with self.assertRaises(ValueError):repair.check_batch({'n':71},25,Path('.'))
        for inner,outer in (((0,0),(1,2,3)),((1,37),(37,38,39)),((-1,2),(3,4,5)),((True,2),(3,4,5))):
            with self.assertRaises(ValueError):repair.edge_specs(inner,outer)


if __name__=='__main__':unittest.main()
