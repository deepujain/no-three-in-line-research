import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from research import diagonal_rowbatch_checkpoint as cp
from research import diagonal_rowbatch_tiny as reference
from research import diagonal_secant_checkpoint as old


class RowBatchCheckpointTests(unittest.TestCase):
    def test_sliced_matches_reference_order_and_counts(self):
        for n in (3,4,5):
            expected=[]
            baseline=reference.census(n,on_witness=lambda c:expected.append((c['metadata']['deficit'],c['metadata']['diagonal'],c['points'])))
            for quota in (1,2,5):
                with self.subTest(n=n,quota=quota),tempfile.TemporaryDirectory() as d:
                    path=Path(d)/'frontier';h=None;found=[]
                    while True:
                        report=cp.run(n,120,quota,path,expected_sha256=h,on_witness=lambda c:found.append((c['metadata']['deficit'],c['metadata']['diagonal'],c['points'])))
                        self.assertLessEqual(report['nodes_this_run'],quota)
                        h=report['checkpoint_sha256']
                        if report['status']=='all_declared_slices_exhausted':break
                        self.assertEqual(report['status'],'node_limit')
                    self.assertEqual(found,expected)
                    self.assertEqual(report['nodes_total'],baseline['nodes'])
                    self.assertEqual(report['witness_visits_total'],baseline['witness_visits'])
                    self.assertEqual(report['slice_counts'],[[r['nodes'],r['witness_visits']] for r in baseline['slice_results']])
                    self.assertEqual(len(found),len({frozenset(map(tuple,v[2])) for v in found}))

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
            previous=Path(d)/'old';r=old.run(3,10,1,previous)
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
            for n,seconds,nodes in [(1,1,1),(80,1,1),(3,0,1),(3,float('nan'),1),(3,1,0)]:
                with self.assertRaises(ValueError):cp.run(n,seconds,nodes,Path(d)/'unused')

    def test_bounded_parser_and_restore_timeout_preserve_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';r=cp.run(5,10,2,p);h=r['checkpoint_sha256'];saved=p.read_bytes()
            ticks=iter([0,0,0,0,2,2,2])
            with patch.object(cp.time,'monotonic',side_effect=lambda:next(ticks)):
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

    def test_combination_materialization_checks_deadline(self):
        state=cp.SecantState(5,0);self.assertTrue(state.push(((0,0),)))
        orbits=cp.pair_orbits(5);byrow=[[] for _ in range(5)]
        for i,orbit in enumerate(orbits):
            for y in {p[1] for p in orbit}:byrow[y].append(i)
        # With ample time for the row scans, then expiry during combinations.
        ticks=iter([0]*23+[2]*100)
        with patch.object(cp.time,'monotonic',side_effect=lambda:next(ticks)):
            with self.assertRaises(TimeoutError):cp.candidates(state,set(),orbits,byrow,1)


if __name__=='__main__':unittest.main()
