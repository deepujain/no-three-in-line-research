"""Integration tests; helper resource monitoring has its own tests."""
import json
import contextlib
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from research import diagonal_secant_fast_guard as guard
from src.verify import verify_certificate, verify_certificate_bruteforce


def run_worker(command, seconds, rss_mib, log_path, *, cancelled):
    assert not cancelled()
    with open(log_path, 'wb') as log:
        p = subprocess.run(command, stdout=log, stderr=log, timeout=seconds)
    return {'gate_status':'exited' if p.returncode == 0 else 'worker_error',
            'cleanup_status':'clean', 'returncode':p.returncode}


class FastGuardTests(unittest.TestCase):
    def test_imported_main_uses_fresh_clock_and_respects_explicit_start(self):
        args = ['--n','3','--max-nodes','1','--output','unused']
        with patch.object(guard, 'MODULE_STARTED', 0), \
                patch.object(guard, 'run', return_value={'complete':True}) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            before = time.monotonic()
            self.assertEqual(guard.main(args), 0)
            self.assertGreaterEqual(run.call_args.kwargs['started'], before)
            self.assertEqual(guard.main(args, started=123), 0)
            self.assertEqual(run.call_args.kwargs['started'], 123)

    def test_dispatch(self):
        sys.path.insert(0,str(guard.ROOT/'src'))
        import lazy_sat
        with patch.object(guard,'main',return_value=7) as mocked:
            self.assertEqual(lazy_sat.main(['--diagonal-secant-fast-guard','--n','3']),7)
            self.assertEqual(mocked.call_args.args[0],['--n','3'])

    def test_tiny_worker_witnesses_and_binding(self):
        with tempfile.TemporaryDirectory() as d:
            for n in (3,5):
                with patch.object(guard, 'guarded_process', side_effect=run_worker):
                    result = guard.run(n,10,256,100000,Path(d)/str(n))
                self.assertTrue(result['complete'], result)
                self.assertEqual(result['status'], 'all_declared_slices_exhausted')
                self.assertTrue({'core','fast_core','verifier','guard','cleanup','entrypoint'} <= set(result['source_hashes']))
                witnesses = list(Path(result['witness_dir']).glob('*.json'))
                self.assertTrue(witnesses)
                for p in witnesses:
                    cert = json.loads(p.read_text())
                    self.assertTrue(verify_certificate(cert)['valid'])
                    self.assertTrue(verify_certificate_bruteforce(cert)['valid'])
                    self.assertEqual(cert['metadata']['method'], 'diagonal_secant_dfs_fast')
                    self.assertEqual(cert['metadata']['source_hashes'], result['source_hashes'])

    def test_failure_overrides_completed_child(self):
        with tempfile.TemporaryDirectory() as d:
            for failure in ('wall_limit','rss_limit','monitor_error','cleanup_error','cancelled'):
                def guarded(command, seconds, rss_mib, log_path, *, cancelled):
                    result = run_worker(command, seconds, rss_mib, log_path, cancelled=cancelled)
                    result['gate_status'] = failure
                    return result
                with self.subTest(failure=failure), patch.object(guard, 'guarded_process', side_effect=guarded):
                    result = guard.run(3,10,256,10000,Path(d)/failure)
                self.assertEqual(result['worker_result']['status'], 'all_declared_slices_exhausted')
                self.assertEqual(result['status'], failure)
                self.assertFalse(result['complete'])
            def bad_cleanup(*args, **kwargs):
                return {'gate_status':'exited','cleanup_status':'error','returncode':0}
            with patch.object(guard, 'guarded_process', side_effect=bad_cleanup):
                result=guard.run(3,10,256,10000,Path(d)/'badcleanup')
            self.assertEqual(result['status'],'cleanup_error')

    def test_sigterm_forwarded_to_owned_guard(self):
        with tempfile.TemporaryDirectory() as d:
            def cancellation(command, seconds, rss_mib, log_path, *, cancelled):
                os.kill(os.getpid(),signal.SIGTERM)
                self.assertTrue(cancelled())
                return {'gate_status':'cancelled','cleanup_status':'clean','returncode':-9}
            with patch.object(guard, 'guarded_process', side_effect=cancellation):
                result=guard.run(3,10,256,10000,Path(d)/'out')
            self.assertEqual(result['status'],'cancelled')
            self.assertFalse(result['complete'])

    def test_deadline_and_source_binding(self):
        from research import diagonal_secant_dfs_fast as core
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'out'
            with patch.object(guard,'guarded_process',side_effect=AssertionError('must not launch')):
                result=guard.run(3,.01,256,100,out,started=time.monotonic()-1)
            self.assertEqual(result['status'],'wall_limit')
            sources=guard.hashes()
            job={'source_hashes':sources,'n':3,'seconds':10,'max_nodes':10000,
                 'deficits':None,'diagonals':None,'state':str(Path(d)/'state'),'witness_dir':d}
            with patch.object(guard,'hashes',return_value={}):
                with self.assertRaisesRegex(ValueError,'before import'): guard.worker(job)
            with patch.object(guard,'hashes',side_effect=[sources,{}]), \
                 patch.object(core,'search',return_value={'status':'all_declared_slices_exhausted'}):
                with self.assertRaisesRegex(ValueError,'during search'): guard.worker(job)
            self.assertFalse(Path(job['state']).exists())
            with patch.object(guard,'hashes',side_effect=[sources,{}]), \
                 patch.object(guard,'guarded_process',side_effect=run_worker):
                result=guard.run(3,10,256,10000,Path(d)/'changed')
            self.assertEqual(result['status'],'source_changed')
            self.assertFalse(result['complete'])

    def test_atomic_witness_precedes_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            sources=guard.hashes(); state=Path(d)/'state'
            job={'source_hashes':sources,'n':3,'seconds':10,'max_nodes':10000,
                 'deficits':None,'diagonals':None,'state':str(state),'witness_dir':d}
            atomic = guard.atomic
            def check(path, value):
                if Path(path)==state:
                    witnesses=list(Path(d).glob('*.json'))
                    self.assertTrue(witnesses)
                    self.assertTrue(all(verify_certificate_bruteforce(json.loads(p.read_text()))['valid'] for p in witnesses))
                else: self.assertFalse(state.exists())
                atomic(path,value)
            with patch.object(guard,'atomic',side_effect=check): guard.worker(job)
            self.assertEqual(json.loads(state.read_text())['status'],'all_declared_slices_exhausted')


if __name__ == '__main__': unittest.main()
