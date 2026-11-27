import json
from itertools import combinations, product
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from research import diagonal_residual_checkpoint as cp
from research import diagonal_rowbatch_checkpoint as frozen_control
from research import diagonal_residual_graph_tiny as tiny
from tests.test_diagonal_residual_graph_tiny import all_prefix_audit, admissible, snapshot
from research import diagonal_rowbatch_tiny as reference
from research import diagonal_secant_checkpoint as old


EVIDENCE = {}


class ResidualCheckpointTests(unittest.TestCase):
    def test_sliced_matches_reference_order_and_counts(self):
        reports=[]
        for n in (3,4,5):
            expected=tiny.census(n)
            with tempfile.TemporaryDirectory() as directory:
                baseline_path=Path(directory)/'baseline'
                baseline=cp.run(n,120,10000,baseline_path)
                baseline_data=json.loads(baseline_path.read_bytes())
                for quota in (1,2,5):
                    path=Path(directory)/f'quota-{quota}';h=None;found=[];stages=0
                    while True:
                        def save(cert):
                            found.append((cert['metadata']['deficit'],cert['metadata']['diagonal'],
                                          cp.verify_certificate(cert)['normalized_sha256']))
                        report=cp.run(n,120,quota,path,expected_sha256=h,on_witness=save)
                        self.assertLessEqual(report['nodes_this_run'],quota)
                        self.assertEqual(json.loads(path.read_bytes())['previous_checkpoint_sha256'],h)
                        h=report['checkpoint_sha256'];stages+=1
                        self.assertEqual(h,cp.sha(path.read_bytes()))
                        if report['status']=='all_declared_slices_exhausted':break
                        self.assertLess(stages,300)
                        self.assertEqual(report['status'],'node_limit')
                    self.assertEqual(found,expected['witnesses'])
                    self.assertEqual(report['nodes_total'],expected['nodes'])
                    self.assertEqual(report['slice_counts'],baseline['slice_counts'])
                    self.assertEqual(report['witness_visits_total'],len(expected['witnesses']))
                    terminal=json.loads(path.read_bytes())
                    terminal.pop('previous_checkpoint_sha256')
                    clean=dict(baseline_data);clean.pop('previous_checkpoint_sha256')
                    self.assertEqual(terminal,clean)
                    self.assertNotIn('physical_work',terminal)
                    reports.append({'n':n,'quota':quota,'stages':stages,
                                    'nodes':report['nodes_total'],'witnesses':len(found)})
        EVIDENCE['one_node_and_sliced_equivalence']=reports

    def test_invalid_hash_identity_schema_and_relocation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';result=cp.run(5,10,2,p);h=result['checkpoint_sha256']
            q=Path(d)/'copy';shutil.copyfile(p,q)
            self.assertEqual(cp.run(5,10,2,q,expected_sha256=h)['nodes_total'],4)
            for call in (lambda:cp.run(5,10,1,p),lambda:cp.run(5,10,1,p,expected_sha256='0'*64),
                         lambda:cp.run(4,10,1,p,expected_sha256=h),lambda:cp.run(5,10,1,p,expected_sha256=h,deficits=[0])):
                with self.assertRaises(ValueError):call()
            data=json.loads(p.read_text());data['frames'][0]['next']=9999;p.write_bytes(cp.encode(data))
            with self.assertRaises(ValueError):cp.run(5,10,1,p,expected_sha256=cp.sha(p.read_bytes()))
            data=json.loads(q.read_text());data['nodes']+=1;q.write_bytes(cp.encode(data))
            with self.assertRaisesRegex(ValueError,'counters'):
                cp.run(5,10,1,q,expected_sha256=cp.sha(q.read_bytes()))
            for method,label in ((old,'old'),(frozen_control,'frozen-control')):
                previous=Path(d)/label;r=method.run(3,10,1,previous)
                with self.assertRaisesRegex(ValueError,'identity'):cp.run(3,10,1,previous,expected_sha256=r['checkpoint_sha256'])

    def test_interruption_before_after_publication_and_callback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';r=cp.run(3,10,1,p);h=r['checkpoint_sha256'];before=p.read_bytes()
            with patch.object(cp,'atomic',side_effect=RuntimeError('before')):
                with self.assertRaises(RuntimeError):cp.run(3,10,1,p,expected_sha256=h)
            self.assertEqual(p.read_bytes(),before)
            atomic=cp.atomic
            def after(path,payload):atomic(path,payload);raise RuntimeError('after')
            with patch.object(cp,'atomic',side_effect=after):
                with self.assertRaises(RuntimeError):cp.run(3,10,1,p,expected_sha256=h)
            self.assertEqual(json.loads(p.read_text())['previous_checkpoint_sha256'],h)
            with self.assertRaises(ValueError):cp.run(3,10,1,p,expected_sha256=h)
            h=cp.sha(p.read_bytes())
            while True:
                before=p.read_bytes()
                try:r=cp.run(3,10,1,p,expected_sha256=h,on_witness=lambda cert:(_ for _ in ()).throw(RuntimeError('callback')))
                except RuntimeError:break
                h=r['checkpoint_sha256']
            self.assertEqual(p.read_bytes(),before)
            found=[];cp.run(3,10,1,p,expected_sha256=h,on_witness=found.append)
            self.assertEqual(len(found),1)
            self.assertTrue(cp.verify_certificate(found[0])['valid'])
            self.assertTrue(cp.verify_certificate_bruteforce(found[0])['valid'])

    def test_timeout_source_change_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';ticks=iter(i/1000 for i in range(10000))
            with patch.object(cp.time,'monotonic',side_effect=lambda:next(ticks)):
                result=cp.run(5,.01,100,p)
            self.assertEqual(result['status'],'timeout');saved=p.read_bytes();h=result['checkpoint_sha256'];sources=cp.source_hashes()
            with patch.object(cp,'source_hashes',side_effect=[sources,{}]):
                with self.assertRaisesRegex(ValueError,'sources changed'):cp.run(5,10,1,p,expected_sha256=h)
            self.assertEqual(p.read_bytes(),saved)
            for n,seconds,nodes in [(1,1,1),(80,1,1),(True,1,1),(3,0,1),(3,float('nan'),1),(3,1,0)]:
                with self.assertRaises(ValueError):cp.run(n,seconds,nodes,Path(d)/'unused')

    def test_bounded_parser_and_restore_timeout_preserve_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';r=cp.run(5,10,2,p);h=r['checkpoint_sha256'];saved=p.read_bytes()
            with patch.object(cp,'check_deadline',side_effect=TimeoutError):
                result=cp.run(5,1,100,p,expected_sha256=h)
            self.assertEqual(result['status'],'timeout');self.assertEqual(result['nodes_this_run'],0)
            self.assertEqual(result['checkpoint_sha256'],h);self.assertEqual(p.read_bytes(),saved)
            huge=Path(d)/'huge';huge.write_bytes(b'x'*(cp.MAX_CHECKPOINT_BYTES+1))
            with self.assertRaisesRegex(ValueError,'size limit'):cp.run(5,10,1,huge,expected_sha256=cp.sha(huge.read_bytes()))
            huge.write_bytes(b'[]')
            with self.assertRaisesRegex(ValueError,'object'):cp.run(5,10,1,huge,expected_sha256=cp.sha(huge.read_bytes()))
            data=json.loads(saved);data['frames']=[{'batch':None,'next':None}]*6
            p.write_bytes(cp.encode(data))
            with self.assertRaisesRegex(ValueError,'counters'):cp.run(5,10,1,p,expected_sha256=cp.sha(p.read_bytes()))

    def test_all_prefix_scan_matches_independent_oracle(self):
        def production_scan(state):
            orbits=cp.pair_orbits(state.n)
            selected={i for i,orbit in enumerate(orbits) if orbit[0] in state.occupied}
            needs,flags,degrees,rules=cp.residual_scan(state,selected,orbits)
            return tiny.Assessment(needs,tuple(orbit[0] for i,orbit in enumerate(orbits) if flags[i]),rules)
        with patch.object(tiny,'scan',side_effect=production_scan):
            reports=[all_prefix_audit(n) for n in range(2,6)]
        EVIDENCE['independent_all_prefix_oracle']=reports

    def test_graph_and_combination_interruptions_on_distinct_prefix_shapes(self):
        representatives={}
        n=5;orbits=cp.pair_orbits(n)
        for deficit,diagonal in product(range(n),repeat=2):
            for mask in range(1<<len(orbits)):
                points=((diagonal,diagonal),)+tuple(p for i,o in enumerate(orbits) if mask&(1<<i) for p in o)
                if not admissible(points,n,deficit):continue
                state=cp.SecantState(n,deficit);self.assertTrue(state.push(((diagonal,diagonal),)))
                selected={i for i in range(len(orbits)) if mask&(1<<i)}
                for index in sorted(selected):self.assertTrue(state.push(orbits[index]))
                result=tiny.scan(state)
                edges=set(result.edges)
                triangle=any((a,b) in edges and (a,c) in edges and (b,c) in edges for a,b,c in combinations(range(n),3))
                key=(result.violations,triangle,bool(selected),not any(result.needs))
                representatives.setdefault(key,(state,selected))
        boundaries=0
        for state,selected in representatives.values():
            before=snapshot(state);calls=[0]
            def counting(deadline):calls[0]+=1
            with patch.object(cp,'check_deadline',side_effect=counting):
                expected=cp.candidates(state,selected,orbits,None)
            for boundary in range(1,calls[0]+1):
                ticks=[0]
                def expire(deadline):
                    ticks[0]+=1
                    if ticks[0]==boundary:raise TimeoutError
                with patch.object(cp,'check_deadline',side_effect=expire),self.assertRaises(TimeoutError):
                    cp.candidates(state,selected,orbits,None)
                self.assertEqual(snapshot(state),before)
                boundaries+=1
            self.assertEqual(cp.candidates(state,selected,orbits,None),expected)
        self.assertTrue(any(key[1] for key in representatives))
        self.assertTrue(any('component_parity' in key[0] for key in representatives))
        self.assertTrue(any('global_color_shortage' in key[0] for key in representatives))
        EVIDENCE['interruption_shapes']=len(representatives)
        EVIDENCE['interruption_boundaries']=boundaries

    def test_explicit_slices_policy_and_physical_work_faults(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'subset'
            report=cp.run(5,10,10000,path,deficits=[3,0],diagonals=[4,1])
            expected=[]
            reference.census(5,deficits=[0,3],diagonals=[1,4],on_witness=expected.append)
            self.assertEqual(report['witness_visits_total'],len(expected))
            data=json.loads(path.read_bytes())
            self.assertEqual(data['identity']['deficits'],[0,3])
            self.assertEqual(data['identity']['diagonals'],[1,4])
            self.assertEqual(data['identity']['prune_policy'],'residual-row-degree-component-parity-bipartite-sum-v1')
            data['identity']['prune_policy']='old-policy';path.write_bytes(cp.encode(data))
            with self.assertRaisesRegex(ValueError,'identity'):
                cp.run(5,10,1,path,expected_sha256=cp.sha(path.read_bytes()),deficits=[0,3],diagonals=[1,4])
        state=cp.SecantState(3,0);self.assertTrue(state.push(((0,0),)))
        orbits=cp.pair_orbits(3)
        with self.assertRaisesRegex(ValueError,'incomplete'):
            cp.residual_scan(state,set(),orbits[:-1])
        with self.assertRaisesRegex(ValueError,'canonical'):
            cp.residual_scan(state,set(),list(reversed(orbits)))
        work=cp.new_work();work['edge_tests']=cp.MAX_U64
        before=snapshot(state)
        with self.assertRaises(OverflowError):cp.residual_scan(state,set(),orbits,work=work)
        self.assertEqual(snapshot(state),before)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'pending'
            with patch.object(cp,'check_deadline',side_effect=TimeoutError):
                stopped=cp.run(3,10,1,path)
            self.assertEqual(stopped['nodes_this_run'],0)
            self.assertEqual(json.loads(path.read_bytes())['frames'],[{'batch':None,'next':None}])
            self.assertEqual(stopped['physical_work']['traversal']['completed_scans'],0)


if __name__=='__main__':unittest.main()
