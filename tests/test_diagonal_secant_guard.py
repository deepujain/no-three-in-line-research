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

from research import diagonal_secant_guard as guard
from src.verify import verify_certificate, verify_certificate_bruteforce


class GuardTests(unittest.TestCase):
    def test_tiny_search_and_witnesses(self):
        with tempfile.TemporaryDirectory() as d:
            for n in (3, 5):
                path = Path(d)/str(n)
                with patch.object(guard, 'process_rss_kib', return_value=40000):
                    report = guard.run(n, 10, 256, 100000, path, started=time.monotonic())
                self.assertTrue(report['complete'], report)
                self.assertEqual(report['status'], 'all_declared_slices_exhausted')
                self.assertGreater(report['guard']['samples'], 0)
                self.assertEqual(json.loads(path.read_text()), report)
                witnesses = list(Path(report['witness_dir']).glob('*.json'))
                self.assertTrue(witnesses)
                for path in witnesses:
                    cert = json.loads(path.read_text())
                    self.assertTrue(verify_certificate(cert)['valid'])
                    self.assertTrue(verify_certificate_bruteforce(cert)['valid'])
                    self.assertEqual(cert['metadata']['source_hashes'], report['source_hashes'])

    def test_monitor_and_rss_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            for sample, expected in [(OSError('denied'), 'monitor_error'), (262145, 'rss_limit')]:
                with self.subTest(expected=expected):
                    with patch.object(guard, 'process_rss_kib', side_effect=sample if isinstance(sample, Exception) else None, return_value=sample):
                        report = guard.run(5, 10, 256, 100000, Path(d)/expected, started=time.monotonic())
                    self.assertEqual(report['status'], expected)
                    self.assertFalse(report['complete'])
                    self.assertIsNotNone(report['guard']['returncode'])

    def test_sigterm_kills_and_reaps_worker(self):
        with tempfile.TemporaryDirectory() as d:
            pid = []
            original = subprocess.Popen
            def spawn(*args, **kwargs):
                process = original(*args, **kwargs)
                pid.append(process.pid)
                return process
            def terminate(_pid):
                os.kill(os.getpid(), signal.SIGTERM)
                return 40000
            with patch.object(guard.subprocess, 'Popen', side_effect=spawn), patch.object(guard, 'process_rss_kib', side_effect=terminate):
                report = guard.run(5, 10, 256, 100000, Path(d)/'out', started=time.monotonic())
            self.assertEqual(report['status'], 'sigterm')
            self.assertFalse(report['complete'])
            with self.assertRaises(ProcessLookupError): os.kill(pid[0], 0)

    def test_setup_deadline_and_invalid_limits(self):
        with tempfile.TemporaryDirectory() as d:
            report = guard.run(3, .01, 256, 100, Path(d)/'out', started=time.monotonic()-1)
            self.assertEqual(report['status'], 'wall_limit')
            self.assertFalse(report['complete'])
            for seconds, rss in [(31,256), (1,257), (0,1), (1,float('nan'))]:
                with self.assertRaises(ValueError): guard.run(3, seconds, rss, 1, Path(d)/'out', started=time.monotonic())

    def test_dispatch(self):
        sys.path.insert(0, str(guard.ROOT/'src'))
        import lazy_sat
        with patch.object(guard, 'main', return_value=7) as mock:
            self.assertEqual(lazy_sat.main(['--diagonal-secant-guard', '--n', '3']), 7)
            self.assertEqual(mock.call_args.args[0], ['--n', '3'])

    def test_imported_run_uses_fresh_clock(self):
        with tempfile.TemporaryDirectory() as d, patch.object(guard, 'MODULE_STARTED', 0), \
                patch.object(guard, 'process_rss_kib', return_value=40000):
            report = guard.run(3, 10, 256, 10000, Path(d)/'out')
            self.assertTrue(report['complete'], report)

    def test_source_binding_and_atomic_witness_order(self):
        from research import diagonal_secant_dfs as core
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            state = directory/'state'
            sources = guard.hashes()
            job = {'source_hashes':sources, 'n':3, 'seconds':10, 'max_nodes':10000,
                   'deficits':None, 'diagonals':None, 'state':str(state), 'witness_dir':d}
            with patch.object(guard, 'hashes', return_value={'changed':'yes'}):
                with self.assertRaisesRegex(ValueError, 'before import'): guard.worker(job)
            self.assertFalse(state.exists())
            with patch.object(guard, 'hashes', side_effect=[sources, {'changed':'yes'}]), \
                    patch.object(core, 'search', return_value={'status':'all_declared_slices_exhausted'}):
                with self.assertRaisesRegex(ValueError, 'during search'): guard.worker(job)
            self.assertFalse(state.exists())
            original = guard.atomic
            def checked_atomic(path, value):
                if Path(path) == state:
                    witnesses = list(directory.glob('*.json'))
                    self.assertTrue(witnesses, 'witness must be published before terminal state')
                    self.assertTrue(all(verify_certificate_bruteforce(json.loads(p.read_text()))['valid'] for p in witnesses))
                else:
                    self.assertFalse(state.exists())
                original(path, value)
            with patch.object(guard, 'atomic', side_effect=checked_atomic): guard.worker(job)
            self.assertEqual(json.loads(state.read_text())['status'], 'all_declared_slices_exhausted')

    def test_failure_overrides_already_published_completion(self):
        class FakeProcess:
            pid = 99999999
            returncode = 0
            def __init__(self, command, **kwargs):
                job = json.loads(Path(command[-1]).read_text())
                guard.atomic(job['state'], {'status':'all_declared_slices_exhausted'})
                self.polls = 0
            def poll(self):
                self.polls += 1
                return None if self.polls == 1 else 0
            def wait(self): return 0
        with tempfile.TemporaryDirectory() as d:
            for kind in ('rss_limit', 'monitor_error', 'wall_limit', 'source_changed'):
                with self.subTest(kind=kind):
                    original_hashes = guard.hashes()
                    def monitor(pid):
                        if kind == 'monitor_error': raise OSError('denied')
                        if kind == 'wall_limit': time.sleep(.12)
                        return 262145 if kind == 'rss_limit' else 40000
                    hashes = [original_hashes, {'changed':'yes'} if kind == 'source_changed' else original_hashes]
                    with patch.object(guard.subprocess, 'Popen', FakeProcess), \
                            patch.object(guard.os, 'killpg'), \
                            patch.object(guard, 'process_rss_kib', side_effect=monitor), \
                            patch.object(guard, 'hashes', side_effect=hashes):
                        report = guard.run(3, .1 if kind == 'wall_limit' else 10, 256, 100,
                                           Path(d)/kind, started=time.monotonic())
                    self.assertEqual(report['worker_result']['status'], 'all_declared_slices_exhausted')
                    self.assertEqual(report['status'], kind)
                    self.assertFalse(report['complete'])


if __name__ == '__main__': unittest.main()
