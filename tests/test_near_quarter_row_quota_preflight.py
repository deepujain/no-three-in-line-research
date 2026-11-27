from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))
from research import near_quarter_preflight as original
from research import near_quarter_row_quota_preflight as preflight

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
try:
    subprocess.run(['ps','-axo','pid=,ppid=,pgid=,rss='],check=True,
                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=.5)
    HAVE_PS = True
except (OSError,subprocess.SubprocessError):
    HAVE_PS = False


def job_for(directory,n=3):
    directory = Path(directory)
    alive = directory/'alive'
    alive.touch()
    return {'n':n,'source_hashes':preflight.source_hashes(),'state':str(directory/'state.json'),
            'guard_parent_pid':os.getppid(),'guard_alive_path':str(alive),
            'deadline_monotonic':time.monotonic()+5}


class RowQuotaPreflightTests(unittest.TestCase):
    def test_guard_identity_project_hashes_and_limits(self):
        self.assertIs(preflight.guarded_process,original.guarded_process)
        sources = preflight.source_hashes()
        self.assertEqual(len(sources),8)
        self.assertEqual(sources['guard_source_sha256'],
                         '1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27')
        self.assertEqual(sources['row_quota_source_sha256'],
                         'dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704')
        self.assertEqual(sources['verifier_source_sha256'],preflight.sha(ROOT/'src/verify.py'))
        self.assertEqual(sources['cli_entrypoint_sha256'],preflight.sha(ROOT/'src/lazy_sat.py'))
        for seconds,memory in ((31,256),(30,257),(0,256),(30,float('nan'))):
            with self.assertRaises(ValueError):
                preflight.preflight(3,seconds,memory,'unused.json')

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_tiny_native_construction_counts_hashes_and_never_solve(self):
        from src.near_quarter_model import orbit_map,maximal_lines
        from src.near_quarter_compact import line_groups
        from src.near_quarter_row_quota import streamed_cnf,row_quota_counts,row_floor_clauses
        for n in (3,5):
            model = orbit_map(n)
            clauses = list(streamed_cnf(model))
            groups = list(line_groups(model))
            floors = list(row_floor_clauses(model))
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory,n)
                with patch('pysat.solvers.Solver.solve',side_effect=AssertionError('no solve')), \
                        patch('pysat.solvers.Solver.solve_limited',side_effect=AssertionError('no solve')):
                    self.assertEqual(preflight.worker(job),0)
                report = json.loads(Path(job['state']).read_text())
                self.assertTrue(report['build_complete'])
                self.assertEqual(report['clauses_added'],len(clauses))
                self.assertEqual(report['variables'],max([len(model['orbits'])]+[abs(v) for c in clauses for v in c]))
                self.assertEqual(report['c4_line_groups'],len(groups))
                self.assertEqual(report['represented_full_lines'],sum(1 for _ in maximal_lines(n)))
                self.assertEqual(report['weighted_line_groups'],len(groups)-1)
                self.assertEqual(report['special_diagonal_groups'],1)
                self.assertEqual(report['row_floor_clauses_algebraic'],len(floors))
                self.assertEqual(report['row_floor_literals_algebraic'],sum(map(len,floors)))
                header = {'family':row_quota_counts(model),'off_diagonal_quotient':'full C4',
                          'exceptional_diagonal_guards':True,'row_floor_representatives':'0..n//2',
                          'row_floor':'weighted occupancy >= 2; replaces global four-orbit equality'}
                content = json.dumps(header,sort_keys=True,separators=(',',':'))+'\n'
                content += ''.join(json.dumps(c,separators=(',',':'))+'\n' for c in clauses)
                self.assertEqual(report['model_sha256'],hashlib.sha256(content.encode()).hexdigest())
                self.assertFalse(report['search_performed'])
                self.assertIsNone(report['solver_result'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_source_changes_before_and_after_stream_cannot_complete(self):
        for after in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory)
                changed = {**job['source_hashes'],'verifier_source_sha256':'changed'}
                sequence = [job['source_hashes'],changed] if after else [changed]
                with patch.object(preflight,'source_hashes',side_effect=sequence):
                    self.assertEqual(preflight.worker(job),2)
                report = json.loads(Path(job['state']).read_text())
                self.assertFalse(report['complete'])
                self.assertFalse(report['cnf_complete'])
                self.assertIsNone(report['model_sha256'])
                self.assertEqual(report['clauses_added'],4 if after else 0)

    def test_parent_gate_failure_overrules_completed_child_and_keeps_partial_counts(self):
        for reason in ('rss_limit','wall_limit','monitor_error','worker_error'):
            def failed_guard(command,seconds,memory,log_path):
                job = json.loads(Path(command[-1]).read_text())
                state = preflight.initial_state(3,job['source_hashes'])
                state.update(complete=True,cnf_complete=True,build_complete=True,
                             model_sha256='fake',clauses=4,clauses_added=4,status='built')
                preflight.atomic(job['state'],state)
                Path(log_path).write_text('')
                return {'gate_status':reason}
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as directory:
                with patch.object(preflight,'guarded_process',side_effect=failed_guard):
                    report = preflight.preflight(3,5,256,Path(directory)/'out.json')
                self.assertEqual(report['status'],reason)
                self.assertEqual(report['clauses_added'],4)
                self.assertFalse(report['complete'])
                self.assertIsNone(report['model_sha256'])

    def test_startup_host_cancellation_and_source_change_fail_closed(self):
        def empty_guard(command,seconds,memory,log_path):
            Path(log_path).write_text('')
            return {'gate_status':'wall_limit'}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(preflight,'guarded_process',side_effect=empty_guard):
                report = preflight.preflight(3,5,256,Path(directory)/'empty.json')
            self.assertEqual(report['clauses'],0)
            self.assertFalse(report['c4_line_groups_complete'])
            with patch.object(preflight,'guarded_process',side_effect=preflight.PreflightStopped('SIGTERM')):
                report = preflight.preflight(3,5,256,Path(directory)/'cancel.json')
            self.assertEqual(report['status'],'cancelled')
            sources = preflight.source_hashes()
            with patch.object(preflight,'guarded_process',side_effect=empty_guard), \
                    patch.object(preflight,'source_hashes',side_effect=[sources,{**sources,'cli_entrypoint_sha256':'changed'}]):
                report = preflight.preflight(3,5,256,Path(directory)/'changed.json')
            self.assertEqual(report['status'],'source_changed')
            self.assertFalse(report['complete'])

    def test_child_parent_loss_and_deadline_never_build(self):
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
            self.assertEqual(report['clauses_added'],0)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_mock_rss_parent_native_n3_build(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(original,'process_rss_kib',return_value=1000):
                report = preflight.preflight(3,5,256,Path(directory)/'report.json')
            self.assertTrue(report['complete'],report)
            self.assertEqual(report['source_hashes'],preflight.source_hashes())
            self.assertEqual(report['clauses_added'],4)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_cli_forwards_and_invalid_mode_never_falls_through(self):
        import lazy_sat
        args = ['--near-quarter-row-quota-preflight','--n','3','--seconds','5',
                '--rss-mib','256','--mode','build','--output','unused.json']
        with patch.object(preflight,'main',return_value=2) as delegate:
            self.assertEqual(lazy_sat.main(args),2)
            delegate.assert_called_once_with(args[1:])
        with patch.object(lazy_sat,'search',side_effect=AssertionError('no search')), \
                redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                lazy_sat.main(['--near-quarter-row-quota-preflight','--n','3',
                               '--mode','count','--output','unused.json'])
            self.assertEqual(result.exception.code,2)

    @unittest.skipUnless(HAVE_PS and HAVE_PYSAT,'real host ps and optional PySAT required')
    def test_real_host_subprocess_build_n3_n5(self):
        with tempfile.TemporaryDirectory() as directory:
            for n,clauses in ((3,4),(5,25)):
                output = Path(directory)/f'n{n}.json'
                result = subprocess.run([sys.executable,str(ROOT/'src/lazy_sat.py'),
                    '--near-quarter-row-quota-preflight','--n',str(n),'--seconds','5','--rss-mib','256',
                    '--mode','build','--output',str(output)],capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report = json.loads(output.read_text())
                self.assertTrue(report['build_complete'])
                self.assertEqual(report['clauses_added'],clauses)
                self.assertEqual(report['source_hashes'],preflight.source_hashes())
                self.assertGreater(report['guard']['peak_sampled_rss_kib'],0)
                self.assertFalse(report['search_performed'])
                self.assertIsNone(report['solver_result'])


if __name__ == '__main__':
    unittest.main()
