from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))
from research import near_quarter_direct_preflight as preflight
from research import owned_process_guard as owned_guard

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
HOST = os.environ.get('DIRECT_THRESHOLD_HOST_TESTS') == '1'


def job_for(directory,n=3,mode='count',first=7,second=7):
    directory = Path(directory)
    alive = directory/'alive'
    alive.touch()
    return {'n':n,'mode':mode,'atmost_two':first,'conditional_atmost_one':second,
            'source_hashes':preflight.source_hashes(),'state':str(directory/'state.json'),
            'guard_parent_pid':os.getppid(),'guard_alive_path':str(alive),
            'deadline_monotonic':time.monotonic()+5}


class DirectPreflightTests(unittest.TestCase):
    def test_guard_and_source_bindings_and_explicit_threshold_limits(self):
        self.assertIs(preflight.guarded_process,owned_guard.guarded_process)
        sources = preflight.source_hashes()
        self.assertEqual(len(sources),10)
        self.assertEqual(sources['guard_source_sha256'],'c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48')
        self.assertEqual(sources['threshold_source_sha256'],'57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb')
        for first,second in ((4,5),(5,8),(True,5),(5,None)):
            with self.assertRaises(ValueError):
                preflight.preflight(3,'count',first,second,5,256,'unused.json')
        for seconds,memory in ((31,256),(30,257),(0,256),(30,float('nan'))):
            with self.assertRaises(ValueError):
                preflight.preflight(3,'count',7,7,seconds,memory,'unused.json')
        with self.assertRaises(ValueError):
            preflight.preflight(3,'solve',7,7,5,256,'unused.json')

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_count_mode_histogram_all_candidates_match_complete_tiny_stream_without_solver(self):
        from src.near_quarter_model import orbit_map,maximal_lines
        from src.near_quarter_compact import line_groups
        from src.near_quarter_direct_thresholds import CapacityThresholds,streamed_cnf
        for n in (3,5,7,9):
            model = orbit_map(n)
            expected = {}
            for first in (5,6,7):
                for second in (5,6,7):
                    clauses = list(streamed_cnf(model,CapacityThresholds(first,second)))
                    variables = max([len(model['orbits'])]+[abs(v) for c in clauses for v in c])
                    expected[(first,second)] = (len(clauses),variables,sum(map(len,clauses)))
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory,n)
                with patch('pysat.solvers.Solver',side_effect=AssertionError('count mode must not construct Solver')):
                    self.assertEqual(preflight.worker(job),0)
                report = json.loads(Path(job['state']).read_text())
            self.assertTrue(report['complete'],report)
            self.assertTrue(report['counts_complete'])
            self.assertTrue(report['support_histogram_complete'])
            self.assertFalse(report['native_solver_constructed'])
            self.assertFalse(report['cnf_complete'])
            self.assertFalse(report['build_complete'])
            self.assertFalse(report['search_performed'])
            self.assertIsNone(report['model_sha256'])
            self.assertIsNone(report['prefix_sha256'])
            self.assertEqual(report['clauses_added'],0)
            self.assertEqual(report['c4_line_groups'],sum(1 for _ in line_groups(model)))
            self.assertEqual(report['represented_full_lines'],sum(1 for _ in maximal_lines(n)))
            self.assertEqual(sum(r['groups'] for r in report['support_histogram']),report['weighted_line_groups'])
            self.assertEqual(len(report['candidate_formula_counts']),9)
            for row in report['candidate_formula_counts']:
                key = row['thresholds']['atmost_two'],row['thresholds']['conditional_atmost_one']
                self.assertEqual((row['clauses'],row['variables'],row['literals']),expected[key],(n,key))
            self.assertEqual((report['clauses'],report['variables'],report['literals']),expected[(7,7)])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_tiny_native_build_exact_hash_counts_and_no_search(self):
        from src.near_quarter_model import orbit_map
        from src.near_quarter_direct_thresholds import CapacityThresholds,model_header,streamed_cnf
        for n in (3,5,9):
            for first,second in ((5,5),(6,6),(7,7)):
                model = orbit_map(n)
                config = CapacityThresholds(first,second)
                clauses = list(streamed_cnf(model,config))
                content = json.dumps(model_header(model,config),sort_keys=True,separators=(',',':'))+'\n'
                content += ''.join(json.dumps(c,separators=(',',':'))+'\n' for c in clauses)
                with tempfile.TemporaryDirectory() as directory:
                    job = job_for(directory,n,'build',first,second)
                    with patch('pysat.solvers.Solver.solve',side_effect=AssertionError('no solve')), \
                         patch('pysat.solvers.Solver.solve_limited',side_effect=AssertionError('no solve')):
                        self.assertEqual(preflight.worker(job),0)
                    report = json.loads(Path(job['state']).read_text())
                self.assertTrue(report['complete'],report)
                self.assertTrue(report['cnf_complete'])
                self.assertTrue(report['build_complete'])
                self.assertTrue(report['native_solver_constructed'])
                self.assertEqual(report['clauses_added'],len(clauses))
                self.assertEqual(report['model_sha256'],hashlib.sha256(content.encode()).hexdigest())
                self.assertFalse(report['search_performed'])
                self.assertIsNone(report['solver_result'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_aggregate_mismatch_cannot_accept_native_build(self):
        original = preflight.aggregate_counts
        def changed(*args):
            rows = original(*args)
            for row in rows:
                row['clauses'] += 1
            return rows
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory,mode='build')
            with patch.object(preflight,'aggregate_counts',side_effect=changed):
                self.assertEqual(preflight.worker(job),2)
            report = json.loads(Path(job['state']).read_text())
        self.assertFalse(report['complete'])
        self.assertIsNone(report['model_sha256'])
        self.assertIn('differs from exact histogram',report['error'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_source_changes_before_or_after_counting_cannot_complete(self):
        for after in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory)
                sources = job['source_hashes']
                with patch.object(preflight,'source_hashes',side_effect=[sources,{}] if after else [{}]):
                    self.assertEqual(preflight.worker(job),2)
                report = json.loads(Path(job['state']).read_text())
            self.assertFalse(report['complete'])
            self.assertFalse(report['counts_complete'])
            self.assertFalse(report['support_histogram_complete'])
            self.assertIsNone(report['model_sha256'])

    def test_parent_gate_failure_clears_accepted_totals_and_keeps_diagnostic_rows(self):
        for reason in ('rss_limit','wall_limit','monitor_error','cleanup_error','cancelled','launch_error','worker_error'):
            def fake_guard(command,seconds,memory,log_path,**kwargs):
                job = json.loads(Path(command[-1]).read_text())
                state = preflight.initial_state(3,'count',7,7,job['source_hashes'])
                state.update(complete=True,counts_complete=True,support_histogram_complete=True,
                             clauses=4,variables=2,status='counted',candidate_formula_counts=[{'clauses':4}])
                preflight.atomic(job['state'],state)
                Path(log_path).write_text('')
                return {'gate_status':reason}
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as directory, \
                 patch.object(preflight,'guarded_process',side_effect=fake_guard):
                report = preflight.preflight(3,'count',7,7,5,256,Path(directory)/'out.json')
            self.assertFalse(report['complete'])
            self.assertFalse(report['counts_complete'])
            self.assertFalse(report['support_histogram_complete'])
            self.assertEqual(report['status'],reason)
            self.assertEqual(report['clauses'],4)
            self.assertTrue(report['worker_observed_complete'])
            self.assertEqual(report['candidate_formula_counts'],[{'clauses':4}])

    def test_source_change_in_parent_clears_count_acceptance(self):
        sources = preflight.source_hashes()
        def fake_guard(command,seconds,memory,log_path,**kwargs):
            Path(log_path).write_text('')
            return {'gate_status':'exited'}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(preflight,'guarded_process',side_effect=fake_guard), \
             patch.object(preflight,'source_hashes',side_effect=[sources,{}]):
            report = preflight.preflight(3,'count',7,7,5,256,Path(directory)/'out.json')
        self.assertEqual(report['status'],'source_changed')
        self.assertFalse(report['counts_complete'])

    def test_child_parent_loss_and_expired_deadline_remain_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory)
            Path(job['guard_alive_path']).unlink()
            self.assertEqual(preflight.worker(job),0)
            self.assertFalse(json.loads(Path(job['state']).read_text())['complete'])
            Path(job['guard_alive_path']).touch()
            job['deadline_monotonic'] = time.monotonic()-1
            self.assertEqual(preflight.worker(job),0)
            report = json.loads(Path(job['state']).read_text())
        self.assertFalse(report['complete'])
        self.assertFalse(report['counts_complete'])
        self.assertEqual(report['clauses_added'],0)

    def test_signal_is_flag_and_cli_requires_explicit_mode_and_thresholds(self):
        prior = signal.getsignal(signal.SIGTERM)
        with preflight.cancellation_signals() as cancelled:
            self.assertFalse(cancelled())
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
            self.assertTrue(cancelled())
        self.assertIs(signal.getsignal(signal.SIGTERM),prior)
        with redirect_stderr(io.StringIO()):
            for missing in ([],['--mode','count'],['--mode','solve']):
                with self.assertRaises(SystemExit) as result:
                    preflight.main(['--n','3','--output','unused.json',*missing])
                self.assertEqual(result.exception.code,2)

    @unittest.skipUnless(HOST and HAVE_PYSAT,'explicit reviewed host gate only')
    def test_actual_host_cli_n9_count_and_build(self):
        with tempfile.TemporaryDirectory() as directory:
            for mode in ('count','build'):
                output = Path(directory)/f'{mode}.json'
                result = subprocess.run([sys.executable,str(ROOT/'src/lazy_sat.py'),
                    '--near-quarter-direct-preflight','--n','9','--mode',mode,
                    '--atmost-two-direct-limit','7','--conditional-atmost-one-direct-limit','7',
                    '--seconds','5','--rss-mib','256','--output',str(output)],
                    capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report = json.loads(output.read_text())
                self.assertTrue(report['complete'],report)
                self.assertEqual(report['clauses'],438)
                self.assertEqual(report['variables'],23)
                self.assertEqual(report['guard']['cleanup_status'],'clean')
                self.assertFalse(report['search_performed'])
                self.assertEqual(report['build_complete'],mode == 'build')
                self.assertEqual(report['source_hashes'],preflight.source_hashes())


    def test_cli_dispatch_forwards_only_to_new_preflight_and_rejects_solve(self):
        import lazy_sat
        args = ['--near-quarter-direct-preflight','--n','3','--mode','count',
                '--atmost-two-direct-limit','7','--conditional-atmost-one-direct-limit','6',
                '--output','unused.json']
        with patch.object(preflight,'main',return_value=2) as delegate:
            self.assertEqual(lazy_sat.main(args),2)
            delegate.assert_called_once_with(args[1:])
        with patch.object(lazy_sat,'search',side_effect=AssertionError('no search')), \
             redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                lazy_sat.main(['--near-quarter-direct-preflight','--n','3','--mode','solve',
                    '--atmost-two-direct-limit','7','--conditional-atmost-one-direct-limit','7',
                    '--output','unused.json'])
            self.assertEqual(result.exception.code,2)


if __name__ == '__main__':
    unittest.main()
