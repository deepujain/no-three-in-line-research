import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from research import diagonal_residual_root_preflight as pf
from research import diagonal_residual_graph_tiny as tiny


def fake_guard(command,seconds,rss_mib,log_path,*,cancelled):
    with open(log_path,'wb') as log:
        result=subprocess.run(command,stdout=log,stderr=log,timeout=seconds)
    return {'gate_status':'exited' if result.returncode==0 else 'worker_error',
            'returncode':result.returncode,'cleanup_status':'clean','cleanup_error':None,
            'rss_samples':1,'cleanup_samples':1,'monitor_error':None,
            'peak_sampled_rss_kib':1,'seconds_limit':seconds,'rss_limit_mib':rss_mib,
            'elapsed_seconds':.001,'gate_semantics':'MOCKED; no host resource evidence'}


class RootPreflightTests(unittest.TestCase):
    def test_all_tiny_roots_one_scan_and_control_order(self):
        passed=rejected=0
        for n in (3,5):
            for d in range(n):
                for t in range(n):
                    state=pf.SecantState(n,d);self.assertTrue(state.push(((t,t),)))
                    expected=tiny.scan(state)
                    with patch.object(pf.residual,'run',side_effect=AssertionError('no DFS')), \
                         patch.object(pf.control,'run',side_effect=AssertionError('no DFS')), \
                         patch.object(pf.residual,'residual_scan',wraps=pf.residual.residual_scan) as scan:
                        result=pf.scan_root(n,d,t,time.monotonic()+5)
                    self.assertEqual(scan.call_count,1)
                    self.assertEqual(result['violations'],list(expected.violations))
                    self.assertEqual(result['needs'],list(expected.needs))
                    self.assertEqual(result['available_count'],len(expected.edges))
                    self.assertEqual(result['physical_work']['completed_scans'],1)
                    self.assertEqual(result['physical_work']['edge_tests'],n*(n-1)//2)
                    self.assertEqual(result['control_compared'],not expected.rejected)
                    self.assertEqual(result['nodes'],0);self.assertFalse(result['search_performed'])
                    passed+=not expected.rejected;rejected+=expected.rejected
        self.assertTrue(passed);self.assertTrue(rejected)

    def test_tiny_mocked_subprocess_driver_and_saved_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            for n in (3,5):
                out=Path(directory)/str(n)
                with patch.object(pf,'guarded_process',side_effect=fake_guard):result=pf.run(n,0,0,10,256,out)
                self.assertTrue(result['accepted'],result)
                self.assertEqual(json.loads((out/'report.json').read_text()),{k:v for k,v in result.items() if k!='invocation_seconds'})
                self.assertGreaterEqual(result['invocation_seconds'],result['elapsed_seconds'])
                job=json.loads((out/'job.json').read_text())
                self.assertEqual(result['job_sha256'],pf.sha((out/'job.json').read_bytes()))
                self.assertEqual(result['worker_report_sha256'],pf.sha((out/'worker.json').read_bytes()))
                self.assertEqual(result['accepted_scan']['physical_work']['scan_attempts'],1)
                self.assertEqual(job['source_hashes'],pf.sources())
                self.assertFalse(result['complete']);self.assertFalse(result['search_performed'])
                self.assertFalse(list(out.glob('*checkpoint*')))

    def test_bounds_before_allocation_and_json_strictness(self):
        for values in ((True,0,0),(80,0,0),(1,0,0),(3,True,0),(3,0,3)):
            with patch.object(pf,'SecantState') as state:
                with self.assertRaises(ValueError):pf.scan_root(*values,time.monotonic()+5)
                state.assert_not_called()
        for data in (b'{"x":1,"x":2}',b'{"x":NaN}',b'['*6+b']'*6,b' '*16385):
            with self.assertRaises(ValueError):pf.decode(data)
        with tempfile.TemporaryDirectory() as directory:
            for seconds,rss in ((31,256),(10,257),(True,256),(10,True)):
                with patch.object(pf,'guarded_process') as launch:
                    with self.assertRaises(ValueError):pf.run(3,0,0,seconds,rss,Path(directory)/'bad')
                    launch.assert_not_called()

    def test_deadline_cancel_and_control_mismatch_no_report(self):
        with self.assertRaises(TimeoutError):pf.scan_root(3,0,0,time.monotonic()-1)
        with self.assertRaises(InterruptedError):pf.scan_root(3,0,0,time.monotonic()+5,lambda:True)
        # n3 (0,2) is a passing root; wrong control ordering is fatal.
        with patch.object(pf.control,'candidates',return_value=[('wrong',)]):
            with self.assertRaisesRegex(ValueError,'control candidate'):pf.scan_root(3,0,2,time.monotonic()+5)
        actual=pf.residual.residual_scan
        def mutation(state,*args,**kwargs):
            result=actual(state,*args,**kwargs);state.rows[0]+=1;return result
        with patch.object(pf.residual,'residual_scan',side_effect=mutation):
            with self.assertRaisesRegex(ValueError,'mutated'):pf.scan_root(3,0,0,time.monotonic()+5)

    def test_scan_boundary_timeout_has_no_partial_verdict(self):
        real=pf.residual.check_deadline;calls=[0]
        def count(deadline):calls[0]+=1;real(deadline)
        with patch.object(pf.residual,'check_deadline',side_effect=count):pf.scan_root(5,0,0,time.monotonic()+5)
        for stop_at in range(1,calls[0]+1):
            seen=[0]
            def interrupt(deadline):
                seen[0]+=1
                if seen[0]==stop_at:raise TimeoutError
            with patch.object(pf.residual,'check_deadline',side_effect=interrupt):
                with self.assertRaises(TimeoutError):pf.scan_root(5,0,0,time.monotonic()+5)

    def test_job_hash_schema_and_report_counter_faults(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'good'
            with patch.object(pf,'guarded_process',side_effect=fake_guard):result=pf.run(3,0,2,10,256,out)
            self.assertTrue(result['accepted'],result)
            job=pf.decode((out/'job.json').read_bytes());report=pf.decode((out/'worker.json').read_bytes())
            with self.assertRaisesRegex(ValueError,'job digest'):pf.worker(out/'job.json','0'*64)
            for field,value in (('schema','old'),('n',True),('deadline',float('inf')),('extra',1)):
                bad=dict(job);bad[field]=value
                with self.assertRaises(ValueError):pf.validate_job(bad)
            for field,value in (('nodes',True),('control_compared',False),('state_unchanged',False),
                                ('violations',['invented']),('available_count',9999),('batch_count',True)):
                bad=copy.deepcopy(report);bad['result'][field]=value
                with self.assertRaises(ValueError):pf.validate_result(bad,job,result['job_sha256'])
            bad=copy.deepcopy(report);bad['result']['physical_work']['completed_scans']=2
            with self.assertRaises(ValueError):pf.validate_result(bad,job,result['job_sha256'])

    def test_helper_and_postworker_failures_reject(self):
        cases=('wall_limit','rss_limit','monitor_error','cleanup_error','no_samples','late_source','cancelled','bad_report')
        with tempfile.TemporaryDirectory() as directory:
            for case in cases:
                def helper(command,seconds,rss_mib,log_path,*,cancelled):
                    gate=fake_guard(command,seconds,rss_mib,log_path,cancelled=cancelled)
                    if case in ('wall_limit','rss_limit','monitor_error','cleanup_error'):gate['gate_status']=case
                    if case=='no_samples':gate['rss_samples']=0
                    if case=='cancelled':os.kill(os.getpid(),signal.SIGTERM)
                    if case=='bad_report':(Path(command[-2]).parent/'worker.json').write_text('{}')
                    return gate
                actual=pf.sources;seen=[0]
                def sources(*args,**kwargs):
                    seen[0]+=1
                    return {} if case=='late_source' and seen[0]>1 else actual(*args,**kwargs)
                with self.subTest(case=case),patch.object(pf,'guarded_process',side_effect=helper), \
                     patch.object(pf,'sources',side_effect=sources):
                    result=pf.run(3,0,0,10,256,Path(directory)/case)
                self.assertFalse(result['accepted']);self.assertIsNone(result['accepted_scan'])
                self.assertEqual(result['status'],'rejected')

    def test_late_publication_failures_clear_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            for case in ('clock','cancel','source','before_write','after_write'):
                out=Path(directory)/case;real_atomic=pf.atomic;real_clock=time.monotonic
                real_sources=pf.sources;offset=[0];changed=[False]
                def atomic(path,payload):
                    if Path(path).name=='report.json' and case=='before_write':raise OSError('before')
                    real_atomic(path,payload)
                    if Path(path).name=='report.json':
                        if case=='clock':offset[0]=100
                        elif case=='cancel':os.kill(os.getpid(),signal.SIGTERM)
                        elif case=='source':changed[0]=True
                        elif case=='after_write':raise OSError('after')
                with patch.object(pf,'guarded_process',side_effect=fake_guard), \
                     patch.object(pf,'atomic',side_effect=atomic), \
                     patch.object(pf.time,'monotonic',side_effect=lambda:real_clock()+offset[0]), \
                     patch.object(pf,'sources',side_effect=lambda *a,**kw:{} if changed[0] else real_sources(*a,**kw)):
                    if case in ('before_write','after_write'):
                        with self.assertRaises(OSError):pf.run(3,0,0,10,256,out)
                    else:
                        result=pf.run(3,0,0,10,256,out)
                        self.assertFalse(result['accepted']);self.assertIsNone(result['accepted_scan'])
                        self.assertEqual(json.loads((out/'report.json').read_text()),{k:v for k,v in result.items() if k!='invocation_seconds'})


if __name__=='__main__':unittest.main()
