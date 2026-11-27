import importlib.util
from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))
from research import near_quarter_preflight as original
from research import near_quarter_compact_preflight as compact

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
try:
    subprocess.run(['ps','-axo','pid=,ppid=,pgid=,rss='],check=True,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=.5)
    HAVE_PS = True
except (OSError,subprocess.SubprocessError):
    HAVE_PS = False


class CompactPreflightTests(unittest.TestCase):
    def test_reuses_exact_frozen_guard_and_refuses_weaker_limits(self):
        self.assertIs(compact.guarded_process,original.guarded_process)
        self.assertEqual(compact.sha(ROOT/'research/near_quarter_preflight.py'),
                         '1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27')
        for seconds,memory in ((31,256),(30,257),(0,256),(30,float('nan'))):
            with self.assertRaises(ValueError):
                compact.preflight(3,seconds,memory,'unused.json')

    def test_parent_failure_overrides_completed_child_and_keeps_lower_bounds(self):
        for reason in ('wall_limit','rss_limit','monitor_error','worker_error'):
            def failed_guard(command,seconds,memory,log_path):
                job = json.loads(Path(command[-1]).read_text())
                state = compact.initial_state(3,job['source_hashes'])
                state.update(complete=True,cnf_complete=True,build_complete=True,status='built',
                             clauses=9,clauses_added=9,variables=7,c4_line_groups=3,
                             model_sha256='fake')
                compact.atomic(job['state'],state)
                Path(log_path).write_text('')
                return {'gate_status':reason}
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                with patch.object(compact,'guarded_process',side_effect=failed_guard):
                    report = compact.preflight(3,30,256,Path(directory)/'report.json')
                self.assertEqual(report['status'],reason)
                self.assertEqual(report['clauses_added'],9)
                self.assertEqual(report['c4_line_groups'],3)
                self.assertFalse(report['complete'])
                self.assertFalse(report['cnf_complete'])
                self.assertFalse(report['build_complete'])
                self.assertIsNone(report['model_sha256'])
                self.assertIsNone(report['solver_result'])

    def test_source_change_and_startup_kill_never_report_complete(self):
        def empty_guard(command,seconds,memory,log_path):
            Path(log_path).write_text('')
            return {'gate_status':'wall_limit'}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(compact,'guarded_process',side_effect=empty_guard):
                report = compact.preflight(3,1,256,Path(directory)/'startup.json')
            self.assertEqual(report['clauses'],0)
            self.assertEqual(report['c4_line_groups'],0)
            self.assertFalse(report['c4_line_groups_complete'])
            sources = compact.source_hashes()
            changed = {**sources,'compact_source_sha256':'changed'}
            with patch.object(compact,'guarded_process',side_effect=empty_guard), \
                    patch.object(compact,'source_hashes',side_effect=[sources,changed]):
                report = compact.preflight(3,1,256,Path(directory)/'changed.json')
            self.assertEqual(report['status'],'source_changed')
            self.assertFalse(report['complete'])

    def test_child_refuses_changed_compact_source_before_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)/'state.json'
            sources = {**compact.source_hashes(),'compact_source_sha256':'wrong'}
            self.assertEqual(compact.worker({'n':3,'state':str(state),'source_hashes':sources}),2)
            report = json.loads(state.read_text())
            self.assertEqual(report['clauses'],0)
            self.assertFalse(report['complete'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_tiny_native_construction_never_calls_solve_and_matches_stream(self):
        from src.near_quarter_model import orbit_map, maximal_lines
        from src.near_quarter_compact import streamed_cnf,line_groups,compact_counts
        for n in (3,5,7):
            model = orbit_map(n)
            clauses = list(streamed_cnf(model))
            groups = list(line_groups(model))
            with tempfile.TemporaryDirectory() as directory:
                state = Path(directory)/'state.json'
                with patch('pysat.solvers.Solver.solve',side_effect=AssertionError('no search')), \
                        patch('pysat.solvers.Solver.solve_limited',side_effect=AssertionError('no search')):
                    result = compact.worker({'n':n,'state':str(state),'source_hashes':compact.source_hashes()})
                self.assertEqual(result,0)
                report = json.loads(state.read_text())
                self.assertTrue(report['build_complete'])
                self.assertEqual(report['clauses_added'],len(clauses))
                self.assertEqual(report['variables'],max([len(model['orbits'])]+[abs(v) for c in clauses for v in c]))
                self.assertEqual(report['c4_line_groups'],len(groups))
                self.assertEqual(report['weighted_line_groups'],len(groups)-1)
                self.assertEqual(report['represented_full_lines'],sum(1 for _ in maximal_lines(n)))
                self.assertEqual(report['special_diagonal_groups'],1)
                header = {'family':compact_counts(model),'off_diagonal_quotient':'full C4',
                          'exceptional_diagonal_guards':True}
                content = json.dumps(header,sort_keys=True,separators=(',',':'))+'\n'
                content += ''.join(json.dumps(c,separators=(',',':'))+'\n' for c in clauses)
                self.assertEqual(report['model_sha256'],hashlib.sha256(content.encode()).hexdigest())
                self.assertIsNone(report['solver_result'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_source_change_after_tiny_stream_refuses_complete_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)/'state.json'
            sources = compact.source_hashes()
            changed = {**sources,'compact_source_sha256':'changed'}
            with patch.object(compact,'source_hashes',side_effect=[sources,changed]):
                result = compact.worker({'n':3,'state':str(state),'source_hashes':sources})
            self.assertEqual(result,2)
            report = json.loads(state.read_text())
            self.assertEqual(report['clauses_added'],2)
            self.assertFalse(report['build_complete'])
            self.assertIsNone(report['model_sha256'])
            self.assertIsNotNone(report['prefix_sha256'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_parent_build_with_mocked_rss_reports_all_source_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(original,'process_rss_kib',return_value=1000):
                report = compact.preflight(3,5,256,Path(directory)/'report.json')
            self.assertTrue(report['complete'],report)
            self.assertEqual(report['source_hashes'],compact.source_hashes())
            self.assertEqual(report['clauses'],report['clauses_added'])
            self.assertEqual(report['guard']['rss_limit_mib'],256)
            self.assertEqual(report['guard']['seconds_limit'],5)
            self.assertFalse(report['search_performed'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_opt_in_adapter_forwards_arguments_and_return_code(self):
        from lazy_sat import main
        args = ['--near-quarter-compact-preflight','--n','3','--seconds','5',
                '--rss-mib','256','--mode','build','--output','unused.json']
        original_args = args.copy()
        with patch.object(compact,'main',return_value=2) as delegate:
            self.assertEqual(main(args),2)
            delegate.assert_called_once_with(args[1:])
        self.assertEqual(args,original_args)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_invalid_compact_options_never_fall_through_to_search(self):
        import lazy_sat
        for extra in (['--mode','count'],['--n','0']):
            with patch.object(lazy_sat,'search',side_effect=AssertionError('no search')), \
                    patch.object(original,'main',side_effect=AssertionError('wrong preflight')), \
                    redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    lazy_sat.main(['--near-quarter-compact-preflight','--n','3',
                                   '--output','unused.json']+extra)
                self.assertEqual(result.exception.code,2)

    @unittest.skipUnless(HAVE_PS and HAVE_PYSAT,'real host ps and optional PySAT required')
    def test_real_host_subprocess_build_via_existing_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'report.json'
            result = subprocess.run([sys.executable,str(ROOT/'src/lazy_sat.py'),
                '--near-quarter-compact-preflight','--n','3','--seconds','5','--rss-mib','256',
                '--mode','build','--output',str(output)],capture_output=True,text=True,timeout=8)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report,json.loads(result.stdout))
            self.assertTrue(report['build_complete'])
            self.assertEqual(report['source_hashes'],compact.source_hashes())
            self.assertEqual(report['clauses_added'],2)
            self.assertEqual(report['c4_line_groups'],3)
            self.assertEqual(report['weighted_line_groups'],2)
            self.assertEqual(report['represented_full_lines'],8)
            self.assertGreater(report['guard']['peak_sampled_rss_kib'],0)
            self.assertFalse(report['search_performed'])
            self.assertIsNone(report['solver_result'])


if __name__ == '__main__':
    unittest.main()
