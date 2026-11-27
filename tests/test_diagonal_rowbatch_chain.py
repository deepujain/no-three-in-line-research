import fcntl
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
import sys
from unittest.mock import patch

from research import diagonal_rowbatch_chain as chain
from research import diagonal_rowbatch_checkpoint as cp
from research import diagonal_rowbatch_checkpoint_guard as guard
from research import diagonal_secant_checkpoint as old_checkpoint
from tests.test_diagonal_rowbatch_checkpoint_guard import worker


def sampled_worker(*args,**kwargs):
    r=worker(*args,**kwargs)
    r.update(rss_samples=1,peak_sampled_rss_kib=40000,monitor_error=None,elapsed_seconds=.1)
    return r


class ChainTests(unittest.TestCase):
    def test_standalone_cli_aggregate_budget(self):
        shim=('import runpy,sys; sys.path.insert(0,"src"); '
              'import research.diagonal_rowbatch_checkpoint_guard as g; '
              'from tests.test_diagonal_rowbatch_chain import sampled_worker; '
              'g.guarded_process=sampled_worker; sys.argv=sys.argv[1:]; '
              'runpy.run_path("research/diagonal_rowbatch_chain.py",run_name="__main__")')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root)
            result=subprocess.run([sys.executable,'-c',shim,'research/diagonal_rowbatch_chain.py',
                '--n','3','--checkpoint',str(p),'--expected-sha256',h,'--ledger-dir',str(root/'cli'),
                '--max-nodes','1','--seconds','120','--invocation-seconds','10','--max-invocations','1'],
                cwd=chain.ROOT,capture_output=True,text=True,check=True)
            report=json.loads(result.stdout)
            self.assertEqual(report['status'],'invocation_limit')
            self.assertEqual(report['aggregate_seconds'],120)
            self.assertEqual(report['seconds_limit'],10)

    def initial(self,n,directory):
        p=directory/'frontier';r=cp.run(n,120,1,p);return p,r['checkpoint_sha256']

    def test_slices_match_reference_prefix_and_stop_on_witness(self):
        for n in (3,5):
            with self.subTest(n=n), tempfile.TemporaryDirectory() as d:
                root=Path(d);p,h=self.initial(n,root);ref=root/'reference';shutil.copyfile(p,ref)
                with patch.object(guard,'guarded_process',side_effect=sampled_worker):
                    result=chain.run(n,p,h,root/'chain',max_nodes=5,max_invocations=26)
                self.assertEqual(result['status'],'witness',result)
                self.assertFalse(result['complete'])
                self.assertEqual(result['invocations'][-1]['status'],'accepted')
                refhash=h;events=[];r=None
                for item in result['invocations']:
                    r=cp.run(n,120,5,ref,expected_sha256=refhash,on_witness=events.append)
                    refhash=r['checkpoint_sha256']
                self.assertTrue(events)
                self.assertEqual(p.read_bytes(),ref.read_bytes())
                self.assertEqual(result['current_accepted_sha256'],refhash)
                self.assertEqual(result['invocations'][-1]['witness_visits_delta'],len(events))
                self.assertFalse(any(x['witness_visits_delta'] for x in result['invocations'][:-1]))
                self.assertEqual(result['reserved_seconds'],32*len(result['invocations']))
                self.assertEqual(json.loads((root/'chain/ledger.json').read_text()),result)
                with self.assertRaises(FileExistsError):chain.run(n,p,refhash,root/'chain',max_nodes=5)

    def test_single_use_locks_and_invalid_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root)
            with open(str(p)+'.chain.lock','a+b') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaisesRegex(ValueError,'owned'):chain.run(3,p,h,root/'locked',max_nodes=1)
            for n,digest in ((4,h),(3,'0'*64)):
                with self.assertRaises(ValueError):chain.run(n,p,digest,root/'invalid',max_nodes=1)
            with self.assertRaises(ValueError):chain.run(3,p,h,root/'invalid',max_nodes=1,aggregate_seconds=901)
            with self.assertRaises(ValueError):chain.run(3,p,h,root/'invalid',max_nodes=1,max_invocations=27)
            old=root/'old-schema';old_result=old_checkpoint.run(3,10,1,old)
            with self.assertRaisesRegex(ValueError,'identity'):chain.run(3,old,old_result['checkpoint_sha256'],root/'wrong-schema',max_nodes=1)
            huge=root/'huge';huge.write_bytes(b'x'*(guard.MAX_CHECKPOINT_BYTES+1))
            with self.assertRaisesRegex(ValueError,'size limit'):chain.run(3,huge,chain.sha(huge.read_bytes()),root/'too-large',max_nodes=1)

    def test_reconstruction_timeout_rejected_without_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root);old=p.read_bytes()
            def timeout(command,seconds,rss_mib,log_path,*,cancelled):
                job=json.loads(Path(command[-1]).read_text());data=json.loads(Path(job['staged_checkpoint']).read_text())
                report={'status':'timeout','checkpoint_sha256':h,'nodes_this_run':0,'nodes_total':data['nodes'],
                        'witness_visits_total':data['witness_visits'],'slice_index':data['slice_index'],'slice_counts':data['slice_counts']}
                guard.atomic(job['worker_result'],guard.encode(report))
                return {'gate_status':'exited','cleanup_status':'clean','returncode':0,
                        'rss_samples':1,'peak_sampled_rss_kib':40000,'monitor_error':None,'elapsed_seconds':.1}
            with patch.object(guard,'guarded_process',side_effect=timeout):
                result=chain.run(3,p,h,root/'timeout',max_nodes=1)
            self.assertEqual(result['status'],'rejected');self.assertEqual(result['current_accepted_sha256'],h)
            self.assertEqual(p.read_bytes(),old)
            self.assertEqual(json.loads(Path(str(p)+'.chain-owner.json').read_text())['status'],'rejected')

    def test_missing_report_and_guard_failure_stop_without_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root)
            with patch.object(guard,'run',return_value={'status':'node_limit'}) as mocked:
                result=chain.run(3,p,h,root/'missing',max_nodes=1)
            self.assertEqual(result['status'],'rejected');self.assertEqual(mocked.call_count,1)
            self.assertEqual(result['current_accepted_sha256'],h)
            self.assertEqual(result['invocations'][0]['status'],'rejected')
            self.assertNotIn('accepted_sha256',result['invocations'][0])
            with self.assertRaisesRegex(ValueError,'independent ownership audit'):chain.run(3,p,h,root/'missing',max_nodes=1)
            with self.assertRaisesRegex(ValueError,'independent ownership audit'):chain.run(3,p,h,root/'new-ledger',max_nodes=1)

    def test_terminal_publication_late_failures_are_rejected(self):
        for failure in ('wall','cancel','source','source_error'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as d:
                root=Path(d);p,h=self.initial(3,root);actual=guard.atomic;real_clock=time.monotonic
                real_sources=chain.source_hashes;offset=[0];changed=[False]
                def write(path,payload):
                    actual(path,payload)
                    if Path(path).name=='ledger.json' and json.loads(payload).get('status')=='invocation_limit':
                        if failure=='wall':offset[0]=1000
                        elif failure=='cancel':os.kill(os.getpid(),signal.SIGTERM)
                        else:changed[0]=True
                def sources():
                    if changed[0] and failure=='source_error':raise OSError('unreadable source')
                    return {} if changed[0] else real_sources()
                with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'atomic',side_effect=write), \
                     patch.object(chain.time,'monotonic',side_effect=lambda:real_clock()+offset[0]), \
                     patch.object(chain,'source_hashes',side_effect=sources):
                    result=chain.run(3,p,h,root/'chain',max_nodes=1,max_invocations=1)
                self.assertEqual(result['status'],'rejected')
                self.assertEqual(result['current_accepted_sha256'],h)
                item=result['invocations'][-1]
                self.assertEqual(item['status'],'rejected');self.assertNotIn('accepted_sha256',item)
                self.assertEqual(item['published_unaccepted_sha256'],chain.sha(p.read_bytes()))
                self.assertEqual(json.loads(Path(str(p)+'.chain-owner.json').read_text())['status'],'rejected')

    def test_guard_exceptions_do_not_reuse_prior_report(self):
        for fail_at in (1,2):
            with self.subTest(fail_at=fail_at),tempfile.TemporaryDirectory() as d:
                root=Path(d);p,h=self.initial(5,root);real=guard.run;calls=[0]
                def fail(*args,**kwargs):
                    calls[0]+=1
                    if calls[0]==fail_at:raise OSError('guard failed')
                    return real(*args,**kwargs)
                with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'run',side_effect=fail):
                    result=chain.run(5,p,h,root/'guard-error',max_nodes=1)
                self.assertEqual(result['status'],'rejected');self.assertEqual(calls[0],fail_at)
                last=result['invocations'][-1]
                self.assertEqual(last['status'],'rejected')
                self.assertNotIn('published_unaccepted_sha256',last)

    def test_bad_guard_numbers_and_timeout_stop(self):
        for field,value in [('elapsed_seconds',float('nan')),('peak_sampled_rss_kib',True),('elapsed_seconds',30.0)]:
            with self.subTest(field=field,value=value),tempfile.TemporaryDirectory() as d:
                root=Path(d);p,h=self.initial(3,root);real=guard.run
                def bad(*args,**kwargs):
                    report=real(*args,**kwargs);report['guard'][field]=value
                    guard.atomic(args[5],guard.encode(report));return report
                with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'run',side_effect=bad):
                    result=chain.run(3,p,h,root/'bad',max_nodes=1)
                self.assertEqual(result['status'],'rejected');self.assertEqual(result['current_accepted_sha256'],h)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root);real=guard.run
            def timeout(*args,**kwargs):
                report=real(*args,**kwargs);report['status']='timeout';report['worker_result']['status']='timeout'
                guard.atomic(args[5],guard.encode(report));return report
            with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'run',side_effect=timeout) as call:
                result=chain.run(3,p,h,root/'timeout',max_nodes=1)
            self.assertEqual(result['status'],'timeout');self.assertEqual(call.call_count,1)

    def test_invocation_limit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(5,root)
            with patch.object(guard,'guarded_process',side_effect=sampled_worker) as call:
                result=chain.run(5,p,h,root/'one',max_nodes=1,max_invocations=1)
            self.assertEqual(result['status'],'invocation_limit');self.assertEqual(call.call_count,1)

    def test_witness_missing_and_report_counter_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root)
            real=guard.run
            def falsify(*args,**kwargs):
                report=real(*args,**kwargs)
                report['worker_result']['nodes_this_run']+=1
                guard.atomic(args[5],guard.encode(report))
                return report
            with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'run',side_effect=falsify):
                result=chain.run(3,p,h,root/'badcounter',max_nodes=1)
            self.assertEqual(result['status'],'rejected');self.assertEqual(result['current_accepted_sha256'],h)
            self.assertNotEqual(chain.sha(p.read_bytes()),h)

    def test_reservation_and_cancellation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root)
            with patch.object(guard,'run',side_effect=AssertionError('no launch')):
                result=chain.run(3,p,h,root/'budget',max_nodes=1,aggregate_seconds=91)
            self.assertEqual(result['status'],'reservation_limit');self.assertEqual(result['reserved_seconds'],0)
            def cancel(command,seconds,rss_mib,log_path,*,cancelled):
                os.kill(os.getpid(),signal.SIGTERM)
                self.assertTrue(cancelled())
                return {'gate_status':'cancelled','cleanup_status':'clean','returncode':-9}
            with patch.object(guard,'guarded_process',side_effect=cancel):
                result=chain.run(3,p,h,root/'cancel',max_nodes=1)
            self.assertEqual(result['status'],'rejected');self.assertEqual(result['current_accepted_sha256'],h)
            self.assertEqual(len(result['invocations']),1)

    def test_time_expires_after_ledger_write_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root);actual=guard.atomic;clock=time.monotonic;offset=[0]
            def atomic(path,payload):
                actual(path,payload)
                if Path(path).name=='ledger.json' and json.loads(payload).get('current_accepted_sha256')!=h:
                    offset[0]=1000
            with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'atomic',side_effect=atomic), \
                 patch.object(chain.time,'monotonic',side_effect=lambda:clock()+offset[0]):
                result=chain.run(3,p,h,root/'deadline',max_nodes=1)
            self.assertEqual(result['status'],'aggregate_deadline')
            self.assertEqual(result['current_accepted_sha256'],h)
            self.assertEqual(result['invocations'][0]['status'],'rejected')

    def test_interrupted_ledger_refuses_new_chain(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root);actual=guard.atomic
            def interrupt(path,payload):
                actual(path,payload)
                if Path(path).name=='ledger.json' and json.loads(payload).get('current_accepted_sha256')!=h:
                    raise KeyboardInterrupt('after accepted ledger write')
            with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'atomic',side_effect=interrupt):
                with self.assertRaises(KeyboardInterrupt):chain.run(3,p,h,root/'interrupted',max_nodes=1)
            self.assertEqual(json.loads(Path(str(p)+'.chain-owner.json').read_text())['status'],'running')
            with self.assertRaisesRegex(ValueError,'independent ownership audit'):
                chain.run(3,p,chain.sha(p.read_bytes()),root/'new-chain',max_nodes=1)

    def test_missing_persisted_witness_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,h=self.initial(3,root);real=guard.run
            def remove_witness(*args,**kwargs):
                result=real(*args,**kwargs)
                for path in Path(result['witness_dir']).glob('*.json'):path.unlink()
                return result
            with patch.object(guard,'guarded_process',side_effect=sampled_worker),patch.object(guard,'run',side_effect=remove_witness):
                result=chain.run(3,p,h,root/'missing-witness',max_nodes=20)
            self.assertEqual(result['status'],'rejected')
            self.assertIn('missing persisted witness',result['invocations'][-1]['error'])


if __name__=='__main__':unittest.main()
