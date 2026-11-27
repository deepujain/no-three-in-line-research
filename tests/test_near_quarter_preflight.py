import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.near_quarter_preflight import guarded_process, preflight, process_rss_kib, sha, worker, MODEL, LINES

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
try:
    subprocess.run(['ps','-axo','pid=,ppid=,pgid=,rss='], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=.5)
    HAVE_PS = True
except (OSError, subprocess.SubprocessError):
    HAVE_PS = False


class NearQuarterPreflightTests(unittest.TestCase):
    def test_os_rss_includes_native_child_tree_and_guard_parent(self):
        rows = f'100 1 100 1000\n101 100 100 2000\n102 101 102 3000\n{os.getpid()} 1 9 4000\n999 1 999 9000\n'
        with patch('research.near_quarter_preflight.subprocess.run',
                   return_value=subprocess.CompletedProcess([], 0, rows, '')):
            self.assertEqual(process_rss_kib(100), 10000)

    def test_empty_partial_malformed_or_invalid_monitor_rows_fail_closed(self):
        for rows in ('', '100 1 100 1000\n', f'{os.getpid()} 1 9 4000\n',
                     f'100 1 100 1000\n{os.getpid()} 1 9 0\n',
                     f'100 1 100 -1\n{os.getpid()} 1 9 4000\n',
                     '100 1\n', 'not a process row\n'):
            with self.subTest(rows=rows):
                with patch('research.near_quarter_preflight.subprocess.run',
                           return_value=subprocess.CompletedProcess([], 0, rows, '')):
                    with self.assertRaises(ValueError):
                        process_rss_kib(100)

    def check_guard_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, '-c', 'import time; time.sleep(10)']
            wall = guarded_process(command, .15, 256, Path(directory)/'wall.log')
            self.assertEqual(wall['gate_status'], 'wall_limit')
            self.assertLess(wall['elapsed_seconds'], 2)
            memory = guarded_process(command, 2, .001, Path(directory)/'rss.log')
            self.assertEqual(memory['gate_status'], 'rss_limit')
            self.assertLess(memory['returncode'], 0)

    @unittest.skipUnless(HAVE_PS, 'host ps unavailable in this sandbox')
    def test_real_host_enforces_wall_and_rss_without_child_cooperation(self):
        self.check_guard_limits()

    def test_host_enforces_limits_with_mock_rss_sampler(self):
        with patch('research.near_quarter_preflight.process_rss_kib', return_value=1000):
            self.check_guard_limits()

    def test_monitor_failure_is_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('research.near_quarter_preflight.process_rss_kib', side_effect=OSError('no monitor')):
                report = guarded_process([sys.executable, '-c', 'import time; time.sleep(10)'],
                                         2, 256, Path(directory)/'log')
            self.assertEqual(report['gate_status'], 'monitor_error')
            self.assertLess(report['returncode'], 0)

    def test_gate_failure_overrules_child_completion_and_preserves_counters(self):
        def fake_guard(command, seconds, rss_mib, log_path):
            job = json.loads(Path(command[-1]).read_text())
            Path(job['state']).write_text(json.dumps({'complete':True, 'status':'built',
                'weighted_lines':7, 'clauses':9, 'clauses_added':9, 'variables':5,
                'cnf_complete':True, 'build_complete':True, 'model_sha256':'fake'}))
            Path(log_path).write_text('')
            return {'gate_status':'rss_limit'}
        with tempfile.TemporaryDirectory() as directory:
            with patch('research.near_quarter_preflight.guarded_process', side_effect=fake_guard):
                report = preflight(3, 'build', 30, 256, Path(directory)/'out.json')
            self.assertEqual(report['status'], 'rss_limit')
            self.assertEqual(report['clauses_added'], 9)
            self.assertTrue(report['worker_observed_complete'])
            self.assertFalse(report['complete'])
            self.assertFalse(report['build_complete'])
            self.assertIsNone(report['model_sha256'])
            self.assertIsNone(report['solver_result'])

    def test_refuses_weaker_gates(self):
        for seconds, memory in ((31,256),(30,257),(0,256),(30,float('nan'))):
            with self.assertRaises(ValueError):
                preflight(3,'count',seconds,memory,'unused.json')

    def test_changed_source_refused_before_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)/'state.json'
            self.assertEqual(worker({'n':3, 'mode':'count', 'state':str(state),
                                     'source_hashes':{'model_source_sha256':'wrong'}}), 2)
            report = json.loads(state.read_text())
            self.assertEqual(report['clauses'], 0)
            self.assertEqual(report['weighted_lines'], 0)
            self.assertFalse(report['complete'])
            self.assertIsNone(report['model_sha256'])

    def test_startup_limit_retains_explicit_zero_counters(self):
        def fake_guard(command, seconds, rss_mib, log_path):
            Path(log_path).write_text('')
            return {'gate_status':'wall_limit'}
        with tempfile.TemporaryDirectory() as directory:
            with patch('research.near_quarter_preflight.guarded_process', side_effect=fake_guard):
                report = preflight(3, 'build', 1, 256, Path(directory)/'report.json')
            self.assertEqual(report['status'], 'wall_limit')
            self.assertEqual(report['clauses'], 0)
            self.assertEqual(report['variables'], 0)
            self.assertEqual(report['weighted_lines'], 0)
            self.assertFalse(report['cnf_complete'])

    @unittest.skipUnless(HAVE_PYSAT, 'optional python-sat not installed')
    def test_tiny_count_and_native_build_match_frozen_stream(self):
        from src.near_quarter_model import orbit_map, streamed_cnf, weighted_lines
        model = orbit_map(3)
        clauses = list(streamed_cnf(model))
        expected_variables = max(len(model['orbits']), max(abs(v) for c in clauses for v in c))
        with tempfile.TemporaryDirectory() as directory:
            # This tests construction, not RSS accuracy. Real host ps gating is
            # separately tested when permitted; production never falls back.
            with patch('research.near_quarter_preflight.process_rss_kib', return_value=1000):
                reports = [preflight(3, mode, 5, 256, Path(directory)/(mode+'.json'))
                           for mode in ('count','build')]
            for report in reports:
                self.assertTrue(report['complete'], report)
                self.assertEqual(report['clauses'], len(clauses))
                self.assertEqual(report['variables'], expected_variables)
                self.assertEqual(report['weighted_lines'], len(list(weighted_lines(model))))
                self.assertTrue(report['weighted_lines_complete'])
                self.assertEqual(report['source_hashes'], {'model_source_sha256':sha(MODEL),
                                                          'line_generator_sha256':sha(LINES)})
                self.assertFalse(report['search_performed'])
                self.assertIsNone(report['solver_result'])
            self.assertEqual(reports[0]['model_sha256'], reports[1]['model_sha256'])
            self.assertEqual(reports[0]['clauses_added'], 0)
            self.assertEqual(reports[1]['clauses_added'], len(clauses))
            self.assertTrue(reports[1]['build_complete'])


if __name__ == '__main__':
    unittest.main()
