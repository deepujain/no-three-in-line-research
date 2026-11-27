import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from research import diagonal_secant_checkpoint as cp
from research import diagonal_secant_dfs_fast as fast


class CheckpointTests(unittest.TestCase):
    def test_sliced_matches_unsliced_order_and_nodes(self):
        for n in (3,4,5):
            with self.subTest(n=n), tempfile.TemporaryDirectory() as directory:
                expected=[]
                baseline=fast.search(n,120,1000000,on_witness=lambda c:expected.append((c['metadata']['deficit'],c['metadata']['diagonal'],c['points'])))
                actual=[];path=Path(directory)/'frontier'; h=None
                while True:
                    report=cp.run(n,120,3,path,expected_sha256=h,on_witness=lambda c:actual.append((c['metadata']['deficit'],c['metadata']['diagonal'],c['points'])))
                    h=report['checkpoint_sha256']
                    if report['status']=='all_declared_slices_exhausted':break
                    self.assertEqual(report['status'],'node_limit')
                self.assertEqual(actual,expected)
                self.assertEqual(report['nodes_total'],baseline['nodes'])
                self.assertEqual(report['witness_visits_total'],baseline['witness_visits'])
                self.assertEqual(report['slice_counts'],[[v['nodes'],v['witness_visits']] for v in baseline['slice_results']])
                self.assertEqual(report['slice_index'],n*n)

    def test_relocation_hash_identity_and_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'one'; result=cp.run(4,10,1,p); h=result['checkpoint_sha256']
            q=Path(d)/'two';shutil.copyfile(p,q)
            self.assertEqual(cp.run(4,10,1,q,expected_sha256=h)['nodes_total'],2)
            for call in (lambda:cp.run(4,10,1,p), lambda:cp.run(4,10,1,p,expected_sha256='0'*64),
                         lambda:cp.run(5,10,1,p,expected_sha256=h),
                         lambda:cp.run(4,10,1,p,expected_sha256=h,deficits=[0])):
                with self.assertRaises(ValueError):call()
            data=json.loads(p.read_text());data['frames'][0]['next']=999
            p.write_bytes(cp.encode(data))
            with self.assertRaises(ValueError):cp.run(4,10,1,p,expected_sha256=cp.sha(p.read_bytes()))
            p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaises(ValueError):cp.run(4,10,1,p,expected_sha256=h)

    def test_interrupt_before_and_after_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier'; first=cp.run(3,10,1,p); h=first['checkpoint_sha256']; old=p.read_bytes()
            with patch.object(cp,'atomic',side_effect=RuntimeError('before replace')):
                with self.assertRaises(RuntimeError):cp.run(3,10,1,p,expected_sha256=h)
            self.assertEqual(p.read_bytes(),old)
            actual_atomic=cp.atomic
            def after(path,payload):
                actual_atomic(path,payload)
                raise RuntimeError('after replace')
            with patch.object(cp,'atomic',side_effect=after):
                with self.assertRaises(RuntimeError):cp.run(3,10,1,p,expected_sha256=h)
            self.assertNotEqual(p.read_bytes(),old)
            self.assertEqual(json.loads(p.read_text())['previous_checkpoint_sha256'],h)
            with self.assertRaises(ValueError):cp.run(3,10,1,p,expected_sha256=h)
            current=cp.sha(p.read_bytes())
            self.assertEqual(cp.run(3,10,1,p,expected_sha256=current)['nodes_total'],3)

    def test_callback_failure_replays_without_skipping(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';r=cp.run(3,10,1,p);h=r['checkpoint_sha256']
            while True:
                saved=p.read_bytes()
                def fail(cert): raise RuntimeError('callback failure')
                try:r=cp.run(3,10,1,p,expected_sha256=h,on_witness=fail)
                except RuntimeError:break
                h=r['checkpoint_sha256']
            self.assertEqual(saved,p.read_bytes())
            visits=[];r=cp.run(3,10,1,p,expected_sha256=h,on_witness=visits.append)
            self.assertEqual(len(visits),1)
            self.assertTrue(all(check['valid'] for check in (cp.verify_certificate(visits[0]),cp.verify_certificate_bruteforce(visits[0]))))

    def test_timeout_and_source_change_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier'
            ticks=iter(i/1000 for i in range(10000))
            with patch.object(cp.time,'monotonic',side_effect=lambda: next(ticks)):
                result=cp.run(5,.01,100,p)
            self.assertEqual(result['status'],'timeout')
            self.assertLess(result['slice_index'],25)
            saved=p.read_bytes();h=result['checkpoint_sha256'];sources=cp.source_hashes()
            with patch.object(cp,'source_hashes',side_effect=[sources,{'changed':'yes'}]):
                with self.assertRaisesRegex(ValueError,'sources changed'):
                    cp.run(5,10,1,p,expected_sha256=h)
            self.assertEqual(p.read_bytes(),saved)


if __name__=='__main__':unittest.main()
