import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from research import diagonal_residual_checkpoint_guard as guard
from research import diagonal_residual_graph_tiny as reference
from src.verify import verify_certificate,verify_certificate_bruteforce


def worker(command,seconds,rss_mib,log_path,*,cancelled):
    with open(log_path,'wb') as log:
        result=subprocess.run(command,stdout=log,stderr=log,timeout=seconds)
    return {'gate_status':'exited' if result.returncode==0 else 'worker_error',
            'cleanup_status':'clean','returncode':result.returncode}


class CheckpointGuardTests(unittest.TestCase):
    def test_standalone_source_identity_and_limits(self):
        from research import diagonal_residual_checkpoint as core
        self.assertEqual(guard.SOURCES['entrypoint'],Path(guard.__file__).resolve())
        self.assertEqual(guard.SOURCES['guard'],guard.SOURCES['entrypoint'])
        for key,path in core.SOURCES.items():self.assertEqual(guard.SOURCES[key],path)
        self.assertNotIn(guard.ROOT/'src/lazy_sat.py',guard.SOURCES.values())
        with tempfile.TemporaryDirectory() as d:
            for seconds,rss in ((31,256),(30,257),(True,256),(30,True),(float('nan'),256)):
                with self.subTest(seconds=seconds,rss=rss),patch.object(guard,'guarded_process') as launch:
                    with self.assertRaises(ValueError):guard.run(3,seconds,rss,1,Path(d)/'frontier',Path(d)/'out')
                    launch.assert_not_called()

    def test_tiny_cli_resume(self):
        shim=('import sys; '
              'import research.diagonal_residual_checkpoint_guard as g; '
              'from tests.test_diagonal_residual_checkpoint_guard import worker; '
              'g.guarded_process=worker; sys.argv=sys.argv[1:]; '
              'raise SystemExit(g.main())')
        with tempfile.TemporaryDirectory() as d:
            for n in (3,5):
                checkpoint=Path(d)/('checkpoint'+str(n));out=Path(d)/('out'+str(n))
                args=['research/diagonal_residual_checkpoint_guard.py','--n',str(n),
                      '--seconds','10','--max-nodes','1','--checkpoint',str(checkpoint),'--output',str(out)]
                initial=subprocess.run([sys.executable,'-c',shim,*args],cwd=guard.ROOT,capture_output=True,text=True,check=True)
                first=json.loads(initial.stdout);self.assertEqual(first['status'],'node_limit')
                args[args.index('--max-nodes')+1]='10000'
                args.extend(['--expected-sha256',first['accepted_checkpoint_sha256']])
                final=subprocess.run([sys.executable,'-c',shim,*args],cwd=guard.ROOT,capture_output=True,text=True,check=True)
                self.assertEqual(json.loads(final.stdout)['status'],'all_declared_slices_exhausted')

    def test_unchanged_reconstruction_timeout_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'frontier';out=root/'report'
            with patch.object(guard,'guarded_process',side_effect=worker):first=guard.run(3,10,256,1,p,out)
            old=p.read_bytes();h=first['accepted_checkpoint_sha256']
            def timeout(command,seconds,rss_mib,log_path,*,cancelled):
                job=json.loads(Path(command[-1]).read_text());data=json.loads(Path(job['staged_checkpoint']).read_text())
                assert job['expected_sha256']==h
                result={'status':'timeout','checkpoint_sha256':h,'nodes_this_run':0,'nodes_total':data['nodes'],
                        'witness_visits_total':data['witness_visits'],'slice_index':data['slice_index'],'slice_counts':data['slice_counts']}
                guard.atomic(job['worker_result'],guard.encode(result))
                return {'gate_status':'exited','cleanup_status':'clean','returncode':0}
            with patch.object(guard,'guarded_process',side_effect=timeout):result=guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(result['status'],'reconstruction_timeout')
            self.assertIsNone(result['accepted_checkpoint_sha256']);self.assertFalse(result['complete'])
            self.assertEqual(p.read_bytes(),old)

    def test_guard_rejects_oversized_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'frontier';p.write_bytes(b'x'*(guard.MAX_CHECKPOINT_BYTES+1))
            with self.assertRaisesRegex(ValueError,'size limit'):
                guard.run(3,10,256,1,p,Path(d)/'out',expected_sha256=guard.sha(p.read_bytes()))

    def test_small_sliced_resume(self):
        for n in (3,5):
            with self.subTest(n=n), tempfile.TemporaryDirectory() as d:
                root=Path(d);checkpoint=root/'frontier';out=root/'report';h=None;found=set()
                baseline=reference.census(n)
                while True:
                    with patch.object(guard,'guarded_process',side_effect=worker):
                        result=guard.run(n,10,256,20,checkpoint,out,expected_sha256=h)
                    self.assertEqual(json.loads(out.read_text()),result)
                    self.assertTrue(result['accepted_checkpoint_sha256'],result)
                    self.assertEqual(result['accepted_checkpoint_sha256'],guard.sha(checkpoint.read_bytes()))
                    data=json.loads(checkpoint.read_text())
                    self.assertEqual(data['previous_checkpoint_sha256'],h)
                    self.assertEqual(data['identity']['format'],'diagonal-residual-rowbatch-frontier-v1')
                    self.assertEqual(data['identity']['prune_policy'],'residual-row-degree-component-parity-bipartite-sum-v1')
                    self.assertNotIn('physical_work',data)
                    work=result['worker_result']['physical_work']
                    self.assertEqual(set(work),{'restore','traversal'})
                    self.assertTrue(all(type(v) is int and v>=0 for group in work.values() for v in group.values()))
                    for field in ('restore_seconds','traversal_seconds','publication_seconds'):
                        self.assertGreaterEqual(result['worker_result'][field],0)
                    h=result['accepted_checkpoint_sha256']
                    for p in Path(result['witness_dir']).glob('*.json'):
                        cert=json.loads(p.read_text());checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                        self.assertTrue(all(c['valid'] and c['point_count']==2*n-1 for c in checks))
                        self.assertEqual(cert['metadata']['guard_source_hashes'],result['source_hashes'])
                        self.assertEqual(cert['metadata']['method'],'diagonal_residual_checkpoint')
                        found.add(checks[0]['normalized_sha256'])
                    if result['complete']:break
                    self.assertEqual(result['status'],'node_limit')
                self.assertTrue(found)
                self.assertEqual(result['worker_result']['nodes_total'],baseline['nodes'])
                self.assertEqual(result['worker_result']['witness_visits_total'],len(baseline['witnesses']))
                self.assertEqual(found,{row[2] for row in baseline['witnesses']})

    def test_old_schema_policy_and_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'frontier';out=root/'report'
            with patch.object(guard,'guarded_process',side_effect=worker):first=guard.run(3,10,256,1,p,out)
            old=p.read_bytes();h=first['accepted_checkpoint_sha256']
            for field,value in (('format','diagonal-rowbatch-frontier-v1'),
                                ('prune_policy','row-degree-only'),
                                ('source_hashes',{})):
                def tamper(command,seconds,rss_mib,log_path,*,cancelled):
                    result=worker(command,seconds,rss_mib,log_path,cancelled=cancelled)
                    job=json.loads(Path(command[-1]).read_text());staged=Path(job['staged_checkpoint'])
                    data=json.loads(staged.read_text());data['identity'][field]=value
                    staged.write_bytes(guard.encode(data));report=Path(job['worker_result'])
                    body=json.loads(report.read_text());body['checkpoint_sha256']=guard.sha(staged.read_bytes())
                    report.write_bytes(guard.encode(body));return result
                with self.subTest(field=field),patch.object(guard,'guarded_process',side_effect=tamper):
                    with self.assertRaisesRegex(ValueError,'identity'):guard.run(3,10,256,1,p,out,expected_sha256=h)
                self.assertEqual(p.read_bytes(),old)
            original=json.loads(old);original['identity']['format']='diagonal-rowbatch-frontier-v1'
            p.write_bytes(guard.encode(original));wrong=p.read_bytes()
            with patch.object(guard,'guarded_process',side_effect=worker):
                result=guard.run(3,10,256,1,p,out,expected_sha256=guard.sha(wrong))
            self.assertEqual(result['status'],'worker_error');self.assertEqual(p.read_bytes(),wrong)
            self.assertIsNone(result['accepted_checkpoint_sha256'])

    def test_failure_does_not_publish_frontier(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'frontier';out=root/'out'
            with patch.object(guard,'guarded_process',side_effect=worker): first=guard.run(3,10,256,1,p,out)
            old=p.read_bytes();h=first['accepted_checkpoint_sha256']
            for reason in ('wall_limit','rss_limit','monitor_error','cleanup_error','cancelled'):
                def fail(command,seconds,rss_mib,log_path,*,cancelled):
                    result=worker(command,seconds,rss_mib,log_path,cancelled=cancelled)
                    result['gate_status']=reason
                    return result
                with self.subTest(reason=reason),patch.object(guard,'guarded_process',side_effect=fail):
                    result=guard.run(3,10,256,100,p,out,expected_sha256=h)
                self.assertFalse(result['complete']);self.assertEqual(result['status'],reason)
                self.assertIsNone(result['accepted_checkpoint_sha256']);self.assertEqual(p.read_bytes(),old)
                if reason=='wall_limit':
                    saved=list(Path(result['witness_dir']).glob('*.json'))
                    self.assertTrue(saved)
                    self.assertTrue(all(verify_certificate_bruteforce(json.loads(q.read_text()))['valid'] for q in saved))
            with patch.object(guard,'guarded_process',return_value={'gate_status':'exited','cleanup_status':'error','returncode':0}):
                result=guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(result['status'],'cleanup_error');self.assertEqual(p.read_bytes(),old)
            sources=guard.hashes()
            with patch.object(guard,'guarded_process',side_effect=worker),patch.object(guard,'hashes',side_effect=[sources,{}]):
                result=guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(result['status'],'source_changed');self.assertEqual(p.read_bytes(),old)
            with patch.object(guard,'guarded_process',side_effect=worker):
                result=guard.run(5,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(result['status'],'worker_error');self.assertEqual(p.read_bytes(),old)

    def test_sigterm_and_lock_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'frontier';out=root/'out'
            def cancel(command,seconds,rss_mib,log_path,*,cancelled):
                os.kill(os.getpid(),signal.SIGTERM);self.assertTrue(cancelled())
                return {'gate_status':'cancelled','cleanup_status':'clean','returncode':-9}
            with patch.object(guard,'guarded_process',side_effect=cancel): result=guard.run(3,10,256,1,p,out)
            self.assertEqual(result['status'],'cancelled');self.assertFalse(p.exists())
            with open(str(p)+'.lock','a+b') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaisesRegex(ValueError,'already owned'):guard.run(3,10,256,1,p,out)
            with patch.object(guard,'guarded_process',side_effect=worker):first=guard.run(3,10,256,1,p,out)
            for pin in (None,'0'*64):
                with self.assertRaisesRegex(ValueError,'hash'):guard.run(3,10,256,1,p,out,expected_sha256=pin)
            with self.assertRaises(ValueError):guard.run(3,10,256,1,p,Path(str(p)+'.lock'),expected_sha256=first['accepted_checkpoint_sha256'])

    def test_tamper_and_interrupt_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'frontier';out=root/'out'
            with patch.object(guard,'guarded_process',side_effect=worker):first=guard.run(3,10,256,1,p,out)
            old=p.read_bytes();h=first['accepted_checkpoint_sha256']
            def tamper(command,seconds,rss_mib,log_path,*,cancelled):
                result=worker(command,seconds,rss_mib,log_path,cancelled=cancelled)
                job=json.loads(Path(command[-1]).read_text());staged=Path(job['staged_checkpoint']);data=json.loads(staged.read_text())
                data['identity']['n']=999;staged.write_bytes(guard.encode(data))
                report=Path(job['worker_result']);body=json.loads(report.read_text());body['checkpoint_sha256']=guard.sha(staged.read_bytes());report.write_bytes(guard.encode(body))
                return result
            with patch.object(guard,'guarded_process',side_effect=tamper):
                with self.assertRaisesRegex(ValueError,'identity'):guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(p.read_bytes(),old)
            actual=guard.atomic
            def interrupt(path,payload):
                if Path(path).resolve()==p.resolve():raise RuntimeError('before promotion')
                return actual(path,payload)
            with patch.object(guard,'guarded_process',side_effect=worker),patch.object(guard,'atomic',side_effect=interrupt):
                with self.assertRaises(RuntimeError):guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(p.read_bytes(),old)
            def after(path,payload):
                actual(path,payload)
                if Path(path).resolve()==p.resolve():raise RuntimeError('after promotion')
            with patch.object(guard,'guarded_process',side_effect=worker),patch.object(guard,'atomic',side_effect=after):
                with self.assertRaises(RuntimeError):guard.run(3,10,256,1,p,out,expected_sha256=h)
            self.assertEqual(json.loads(p.read_text())['previous_checkpoint_sha256'],h)
            self.assertNotEqual(p.read_bytes(),old)
            self.assertEqual(json.loads(out.read_text())['status'],'incomplete')

    def test_reject_failures_during_promotion_and_final_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for failure in ('wall_limit','cancelled','source_changed','late_report_wall'):
                with self.subTest(failure=failure):
                    p=root/(failure+'-frontier');out=root/(failure+'-out')
                    with patch.object(guard,'guarded_process',side_effect=worker):first=guard.run(3,10,256,1,p,out)
                    h=first['accepted_checkpoint_sha256'];actual_atomic=guard.atomic
                    actual_hashes=guard.hashes; actual_clock=time.monotonic
                    changed=[False];offset=[0];writes=[0]
                    def atomic(path,payload):
                        actual_atomic(path,payload)
                        if Path(path).resolve()==p.resolve():
                            if failure=='wall_limit':offset[0]=100
                            elif failure=='cancelled':os.kill(os.getpid(),signal.SIGTERM)
                            elif failure=='source_changed':changed[0]=True
                        if Path(path).resolve()==out.resolve():
                            writes[0]+=1
                            if failure=='late_report_wall' and writes[0]==2:offset[0]=100
                    def hashes():
                        return {} if changed[0] else actual_hashes()
                    with patch.object(guard,'guarded_process',side_effect=worker), \
                         patch.object(guard,'atomic',side_effect=atomic), \
                         patch.object(guard,'hashes',side_effect=hashes), \
                         patch.object(guard.time,'monotonic',side_effect=lambda:actual_clock()+offset[0]):
                        result=guard.run(3,10,256,1,p,out,expected_sha256=h)
                    self.assertEqual(result['status'],'wall_limit' if failure=='late_report_wall' else failure)
                    self.assertFalse(result['complete'])
                    self.assertIsNone(result['accepted_checkpoint_sha256'])
                    self.assertEqual(result['published_checkpoint_sha256'],guard.sha(p.read_bytes()))
                    if failure=='source_changed':self.assertFalse(result['guard']['source_stable'])
                    self.assertEqual(json.loads(p.read_text())['previous_checkpoint_sha256'],h)
                    self.assertEqual(json.loads(out.read_text()),result)


if __name__=='__main__':unittest.main()
