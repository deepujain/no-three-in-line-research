import importlib.util
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
from research import near_quarter_preflight as original
from research import near_quarter_compact_solve as solve
from src.near_quarter_model import orbit_map
from src.verify import verify_certificate,verify_certificate_bruteforce

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
    return {'n':n,'source_hashes':solve.source_hashes(),
            'state':str(directory/'state.json'),'witness_directory':str(directory/'witnesses'),
            'expected_model_sha256':None,'deadline_monotonic':time.monotonic()+5,
            'guard_parent_pid':os.getppid(),'guard_alive_path':str(alive)}


class SolverStub:
    def __init__(self,answer=None,assignment=None,events=None):
        self.answer = answer
        self.assignment = assignment
        self.events = events if events is not None else []
        self.calls = 0
    def add_clause(self,clause):
        self.events.append('clause')
    def solve_limited(self,**kwargs):
        self.calls += 1
        self.events.append('solve')
        return self.answer
    def get_model(self):
        return self.assignment
    def interrupt(self):
        self.events.append('interrupt')
    def delete(self):
        self.events.append('delete')


class CompactSolveTests(unittest.TestCase):
    def test_caps_and_frozen_guard_and_verifier_provenance(self):
        self.assertIs(solve.guarded_process,original.guarded_process)
        self.assertEqual(solve.source_hashes()['guard_source_sha256'],
                         '1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27')
        self.assertEqual(solve.source_hashes()['verifier_source_sha256'],solve.sha(ROOT/'src/verify.py'))
        for seconds,memory in ((121,256),(120,257),(0,256),(120,float('nan'))):
            with self.assertRaises(ValueError):
                solve.run(3,seconds,memory,'unused.json')

    def test_decoder_rejects_missing_conflicting_outside_or_wrong_family_assignments(self):
        model = orbit_map(3)
        self.assertEqual(solve.decode_orbits(model,[1,2],2),[1,2])
        for assignment in (None,[1],[1,-1,2],[True,2],[1,2,3],[-1,2],[1,-2]):
            with self.subTest(assignment=assignment),self.assertRaises(ValueError):
                solve.decode_orbits(model,assignment,2)

    def test_immutable_witness_reuse_and_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            path,digest = solve.persist_witness(directory,{'n':3,'points':[]})
            self.assertEqual(solve.persist_witness(directory,{'n':3,'points':[]}),(path,digest))
            self.assertEqual(solve.sha(path),digest)
            Path(path).write_text('tampered')
            with self.assertRaises(ValueError):
                solve.persist_witness(directory,{'n':3,'points':[]})

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_real_tiny_sat_unsat_and_witness_before_terminal_publication(self):
        published = []
        real_atomic = solve.atomic
        def observed_atomic(path,state):
            if state.get('conclusion') == 'verified_witness':
                self.assertTrue(Path(state['witness_file']).exists())
                self.assertEqual(solve.sha(state['witness_file']),state['witness_sha256'])
            published.append((state.get('complete'),state.get('witness_file')))
            return real_atomic(path,state)
        for n in (3,5):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory,n)
                with patch.object(solve,'atomic',side_effect=observed_atomic):
                    self.assertEqual(solve.worker(job),0)
                report = json.loads(Path(job['state']).read_text())
                self.assertTrue(report['complete'],report)
                self.assertTrue(report['cnf_complete'])
                self.assertTrue(report['search_complete'])
                self.assertFalse(report['proof_checked'])
                if n == 3:
                    self.assertIs(report['solver_result'],True)
                    self.assertEqual(report['conclusion'],'verified_witness')
                    certificate = json.loads(Path(report['witness_file']).read_text())
                    self.assertTrue(verify_certificate(certificate)['valid'])
                    self.assertTrue(verify_certificate_bruteforce(certificate)['valid'])
                    self.assertIn((False,report['witness_file']),published)
                    # Exact model identity matches the frozen build-only n3 fixture.
                    baseline = json.loads((ROOT/'data/near-quarter-compact-preflight-n3.json').read_text())
                    self.assertEqual(report['model_sha256'],baseline['model_sha256'])
                else:
                    self.assertIs(report['solver_result'],False)
                    self.assertEqual(report['conclusion'],'restricted_family_unsat_solver_reported')
                    self.assertIsNone(report['witness_file'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_none_and_integer_zero_are_never_unsat(self):
        for answer in (None,0):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory)
                stub = SolverStub(answer)
                with patch('pysat.solvers.Solver',return_value=stub):
                    solve.worker(job)
                report = json.loads(Path(job['state']).read_text())
                self.assertFalse(report['complete'])
                self.assertIsNone(report['solver_result'])
                self.assertIsNone(report['conclusion'])
                self.assertEqual(stub.calls,1)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_interruption_overrules_false_and_timer_join_precedes_delete(self):
        events = []
        stub = SolverStub(False,events=events)
        class TimerStub:
            def __init__(self,remaining,callback):
                self.callback = callback
            def start(self):
                self.callback()
            def cancel(self):
                events.append('cancel')
            def join(self):
                events.append('join')
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory)
            with patch('pysat.solvers.Solver',return_value=stub),patch.object(solve.threading,'Timer',TimerStub):
                self.assertEqual(solve.worker(job),0)
            report = json.loads(Path(job['state']).read_text())
            self.assertEqual(report['status'],'interrupted')
            self.assertIsNone(report['solver_result'])
            self.assertLess(events.index('join'),events.index('delete'))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_partial_stream_or_expected_hash_mismatch_never_solves(self):
        def broken_stream(model):
            yield [1]
            raise ValueError('incomplete CNF')
        for broken in (True,False):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory)
                stub = SolverStub(False)
                if not broken:
                    job['expected_model_sha256'] = '0'*64
                with patch('pysat.solvers.Solver',return_value=stub):
                    if broken:
                        with patch('src.near_quarter_compact.streamed_cnf',broken_stream):
                            solve.worker(job)
                    else:
                        solve.worker(job)
                report = json.loads(Path(job['state']).read_text())
                self.assertEqual(stub.calls,0)
                self.assertFalse(report['complete'])
                self.assertIsNone(report['model_sha256'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_changed_source_after_solve_rejects_even_false(self):
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory)
            sources = job['source_hashes']
            changed = {**sources,'verifier_source_sha256':'changed'}
            stub = SolverStub(False)
            with patch('pysat.solvers.Solver',return_value=stub), \
                    patch.object(solve,'source_hashes',side_effect=[sources,sources,changed]):
                solve.worker(job)
            report = json.loads(Path(job['state']).read_text())
            self.assertFalse(report['complete'])
            self.assertIsNone(report['model_sha256'])
            self.assertIsNone(report['solver_result'])

    def test_host_failure_clears_conclusions_but_records_observed_witness_path(self):
        for reason in ('rss_limit','wall_limit','monitor_error'):
            def failed_guard(command,seconds,memory,log_path):
                job = json.loads(Path(command[-1]).read_text())
                state = solve.initial_state(3,job['source_hashes'],None)
                state.update(complete=True,search_complete=True,cnf_complete=True,build_complete=True,
                             status='verified_witness',conclusion='verified_witness',solver_result=True,
                             witness_file='already-saved.json',witness_sha256='fake',model_sha256='fake')
                solve.atomic(job['state'],state)
                Path(log_path).write_text('')
                return {'gate_status':reason}
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as directory:
                with patch.object(solve,'guarded_process',side_effect=failed_guard):
                    report = solve.run(3,5,256,Path(directory)/'report.json')
                self.assertEqual(report['status'],reason)
                self.assertFalse(report['complete'])
                self.assertIsNone(report['conclusion'])
                self.assertIsNone(report['solver_result'])
                self.assertIsNone(report['witness_file'])
                self.assertEqual(report['worker_observed_witness_file'],'already-saved.json')

    def test_child_startup_or_construction_deadline_and_parent_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory)
            Path(job['guard_alive_path']).unlink()
            self.assertEqual(solve.worker(job),0)
            report = json.loads(Path(job['state']).read_text())
            self.assertEqual(report['status'],'cancelled')
            self.assertFalse(report['search_performed'])
            Path(job['guard_alive_path']).touch()
            job['deadline_monotonic'] = time.monotonic()-1
            self.assertEqual(solve.worker(job),0)
            report = json.loads(Path(job['state']).read_text())
            self.assertEqual(report['status'],'budget_exhausted')
            self.assertFalse(report['search_performed'])

    def test_sigterm_unwinds_guard_and_reaps_sleeping_child(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            pid_file = directory/'child.pid'
            script = directory/'cancel.py'
            child_code = 'import os,time; from pathlib import Path; Path('+repr(str(pid_file))+').write_text(str(os.getpid())); time.sleep(10)'
            script.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\n'
                'from research import near_quarter_preflight as g\n'
                'from research.near_quarter_compact_solve import cancellation_signals,CancellationRequested\n'
                'g.process_rss_kib=lambda pid: 1000\n'
                'try:\n'
                ' with cancellation_signals():\n'
                '  g.guarded_process([sys.executable,"-c",'+repr(child_code)+'],5,256,'+repr(str(directory/'log'))+')\n'
                'except CancellationRequested:\n'
                ' sys.exit(2)\n')
            process = subprocess.Popen([sys.executable,str(script)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic()+3
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(pid_file.exists())
                child = int(pid_file.read_text())
                process.send_signal(signal.SIGTERM)
                self.assertEqual(process.wait(timeout=2),2)
                with self.assertRaises(ProcessLookupError):
                    os.kill(child,0)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_adapter_and_mocked_sampler_parent_tiny_run(self):
        from lazy_sat import main
        args = ['--near-quarter-compact-solve','--n','3','--seconds','5','--output','unused.json']
        with patch.object(solve,'main',return_value=2) as delegate:
            self.assertEqual(main(args),2)
            delegate.assert_called_once_with(args[1:])
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(original,'process_rss_kib',return_value=1000):
                report = solve.run(3,5,256,Path(directory)/'report.json')
            self.assertTrue(report['complete'],report)
            self.assertEqual(report['conclusion'],'verified_witness')

    @unittest.skipUnless(HAVE_PYSAT and HAVE_PS,'real host ps and optional PySAT required')
    def test_real_host_subprocess_sat_and_scoped_unsat(self):
        with tempfile.TemporaryDirectory() as directory:
            for n in (3,5):
                output = Path(directory)/f'report-{n}.json'
                result = subprocess.run([sys.executable,str(ROOT/'src/lazy_sat.py'),
                    '--near-quarter-compact-solve','--n',str(n),'--seconds','5','--rss-mib','256',
                    '--output',str(output)],capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report = json.loads(output.read_text())
                self.assertTrue(report['complete'])
                self.assertGreater(report['guard']['peak_sampled_rss_kib'],0)
                self.assertEqual(report['source_hashes'],solve.source_hashes())
                self.assertIs(report['solver_result'],n == 3)


if __name__ == '__main__':
    unittest.main()
