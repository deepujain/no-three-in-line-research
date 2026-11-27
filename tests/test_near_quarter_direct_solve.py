import hashlib
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
from research import owned_process_guard as owned_guard
from research import near_quarter_direct_solve as solve
from src.near_quarter_model import orbit_map
from src.verify import verify_certificate,verify_certificate_bruteforce

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
HAVE_PS = os.environ.get('DIRECT_THRESHOLD_SOLVE_HOST_TESTS') == '1'


def fixture_hash(n,first=7,second=7):
    from src.near_quarter_direct_thresholds import CapacityThresholds,model_header,streamed_cnf
    model = orbit_map(n)
    config = CapacityThresholds(first,second)
    digest = hashlib.sha256()
    digest.update((json.dumps(model_header(model,config),sort_keys=True,separators=(',',':'))+'\n').encode())
    for clause in streamed_cnf(model,config):
        digest.update((json.dumps(clause,separators=(',',':'))+'\n').encode())
    return digest.hexdigest()


def job_for(directory,n=3):
    directory = Path(directory)
    alive = directory/'alive'
    alive.touch()
    return {'n':n,'atmost_two':7,'conditional_atmost_one':7,'source_hashes':solve.source_hashes(),
            'state':str(directory/'state.json'),'witness_directory':str(directory/'witnesses'),
            'expected_model_sha256':fixture_hash(n) if HAVE_PYSAT else '0'*64,'deadline_monotonic':time.monotonic()+5,
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


class DirectThresholdSolveTests(unittest.TestCase):
    def test_caps_and_frozen_guard_and_verifier_provenance(self):
        self.assertIs(solve.guarded_process,owned_guard.guarded_process)
        self.assertEqual(solve.source_hashes()['guard_source_sha256'],
                         'c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48')
        self.assertEqual(solve.source_hashes()['verifier_source_sha256'],solve.sha(ROOT/'src/verify.py'))
        for seconds,memory in ((31,256),(30,257),(0,256),(30,float('nan'))):
            with self.assertRaises(ValueError):
                solve.run(3,7,7,seconds,memory,'unused.json')

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
                    self.assertEqual(report['model_sha256'],fixture_hash(n))
                else:
                    self.assertIs(report['solver_result'],False)
                    self.assertEqual(report['conclusion'],'restricted_family_unsat_solver_reported')
                    self.assertIsNone(report['witness_file'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_none_and_integer_zero_are_never_unsat(self):
        for answer in (None,0,1,'False'):
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
        def broken_stream(model,config):
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
                        with patch('src.near_quarter_direct_thresholds.streamed_cnf',broken_stream):
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
        for reason in ('rss_limit','wall_limit','monitor_error','cleanup_error','cancelled','launch_error'):
            def failed_guard(command,seconds,memory,log_path,**kwargs):
                job = json.loads(Path(command[-1]).read_text())
                state = solve.initial_state(3,job['source_hashes'],None,7,7)
                state.update(complete=True,search_complete=True,cnf_complete=True,build_complete=True,
                             status='verified_witness',conclusion='verified_witness',solver_result=True,
                             witness_file='already-saved.json',witness_sha256='fake',model_sha256='fake')
                solve.atomic(job['state'],state)
                Path(log_path).write_text('')
                return {'gate_status':reason}
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as directory:
                with patch.object(solve,'guarded_process',side_effect=failed_guard):
                    report = solve.run(3,7,7,5,256,Path(directory)/'report.json',expected_model_sha256='0'*64)
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

    def test_signal_cancellation_is_flag_and_restores_handler(self):
        prior = signal.getsignal(signal.SIGTERM)
        with solve.cancellation_signals() as cancelled:
            self.assertFalse(cancelled())
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
            self.assertTrue(cancelled())
        self.assertIs(signal.getsignal(signal.SIGTERM),prior)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_adapter_and_mock_guard_parent_tiny_run(self):
        from lazy_sat import main
        args = ['--near-quarter-direct-solve','--n','3','--seconds','5',
                '--atmost-two-direct-limit','7','--conditional-atmost-one-direct-limit','7',
                '--expected-model-sha256',fixture_hash(3),'--output','unused.json']
        with patch.object(solve,'main',return_value=2) as delegate:
            self.assertEqual(main(args),2)
            delegate.assert_called_once_with(args[1:])
        def fake_guard(command,seconds,memory,log_path,*,cancelled):
            job = json.loads(Path(command[-1]).read_text())
            Path(log_path).write_text('')
            self.assertFalse(cancelled())
            with patch.object(solve.os,'getppid',return_value=job['guard_parent_pid']):
                code = solve.worker(job)
            return {'gate_status':'exited' if code == 0 else 'worker_error','cleanup_status':'clean'}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(solve,'guarded_process',side_effect=fake_guard):
                report = solve.run(3,7,7,5,256,Path(directory)/'report.json',expected_model_sha256=fixture_hash(3))
            self.assertTrue(report['complete'],report)
            self.assertEqual(report['conclusion'],'verified_witness')

    @unittest.skipUnless(HAVE_PYSAT and HAVE_PS,'real host ps and optional PySAT required')
    def test_real_host_subprocess_sat_and_scoped_unsat(self):
        with tempfile.TemporaryDirectory() as directory:
            for n in (3,5):
                output = Path(directory)/f'report-{n}.json'
                result = subprocess.run([sys.executable,str(ROOT/'src/lazy_sat.py'),
                    '--near-quarter-direct-solve','--n',str(n),'--seconds','5','--rss-mib','256',
                    '--atmost-two-direct-limit','7','--conditional-atmost-one-direct-limit','7',
                    '--output',str(output),'--expected-model-sha256',fixture_hash(n)],capture_output=True,text=True,timeout=8)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report = json.loads(output.read_text())
                self.assertTrue(report['complete'])
                self.assertGreater(report['guard']['peak_sampled_rss_kib'],0)
                self.assertEqual(report['source_hashes'],solve.source_hashes())
                self.assertIs(report['solver_result'],n == 3)


    def test_expected_hash_is_required_and_malformed_values_are_rejected(self):
        for expected in (None,False,0,'','A'*64,'g'*64,'0'*63):
            with self.subTest(expected=expected),self.assertRaises(ValueError):
                solve.run(3,7,7,5,256,'unused.json',expected_model_sha256=expected)
        self.assertEqual(len(solve.source_hashes()),12)

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_missing_hash_or_changed_source_never_solves(self):
        for mode in ('missing_hash','source_change'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                job = job_for(directory)
                if mode == 'missing_hash':
                    job['expected_model_sha256'] = None
                stub = SolverStub(False)
                with patch('pysat.solvers.Solver',return_value=stub):
                    if mode == 'source_change':
                        with patch.object(solve,'source_hashes',return_value={}):
                            self.assertEqual(solve.worker(job),2)
                    else:
                        self.assertEqual(solve.worker(job),2)
                report = json.loads(Path(job['state']).read_text())
                self.assertEqual(stub.calls,0)
                self.assertFalse(report['search_performed'])
                self.assertIsNone(report['solver_result'])
                self.assertIsNone(report['conclusion'])

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_invalid_sat_models_never_persist_witness(self):
        model5 = orbit_map(5)
        chosen = {1,2,model5['four_count']+1}
        invalid_geometry = [v if v in chosen else -v for v in range(1,len(model5['orbits'])+1)]
        for n,assignment in ((3,None),(3,[1]),(3,[1,-1,2]),(5,invalid_geometry)):
            with self.subTest(n=n,assignment=assignment),tempfile.TemporaryDirectory() as directory:
                job = job_for(directory,n)
                stub = SolverStub(True,assignment=assignment)
                with patch('pysat.solvers.Solver',return_value=stub), \
                     patch.object(solve,'persist_witness',side_effect=AssertionError('invalid witness')) as persist:
                    self.assertEqual(solve.worker(job),2)
                report = json.loads(Path(job['state']).read_text())
                self.assertFalse(report['complete'])
                self.assertIsNone(report['solver_result'])
                self.assertIsNone(report['witness_file'])
                persist.assert_not_called()

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_sat_timer_join_then_native_free_precede_verification_and_persistence(self):
        events = []
        stub = SolverStub(True,assignment=[1,2],events=events)
        real_check = __import__('src.near_quarter_model',fromlist=['check_candidate']).check_candidate
        real_persist = solve.persist_witness
        class TimerStub:
            def __init__(self,remaining,callback):
                pass
            def start(self):
                events.append('start')
            def cancel(self):
                events.append('cancel')
            def join(self):
                events.append('join')
        def check(*args):
            events.append('verify')
            return real_check(*args)
        def persist(*args):
            events.append('persist')
            return real_persist(*args)
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory)
            with patch('pysat.solvers.Solver',return_value=stub), \
                 patch.object(solve.threading,'Timer',TimerStub), \
                 patch('src.near_quarter_model.check_candidate',side_effect=check), \
                 patch.object(solve,'persist_witness',side_effect=persist):
                self.assertEqual(solve.worker(job),0)
        self.assertLess(events.index('join'),events.index('delete'))
        self.assertLess(events.index('delete'),events.index('verify'))
        self.assertLess(events.index('verify'),events.index('persist'))
        self.assertEqual(events.count('delete'),1)

    def test_parent_source_failure_overrides_completed_false(self):
        def fake_guard(command,seconds,memory,log_path,**kwargs):
            job = json.loads(Path(command[-1]).read_text())
            state = solve.initial_state(3,job['source_hashes'],job['expected_model_sha256'],7,7)
            state.update(complete=True,search_complete=True,cnf_complete=True,build_complete=True,
                         status='restricted_family_unsat_solver_reported',
                         conclusion='restricted_family_unsat_solver_reported',solver_result=False,
                         model_sha256='fake')
            solve.atomic(job['state'],state)
            Path(log_path).write_text('')
            return {'gate_status':'exited','cleanup_status':'clean'}
        sources = solve.source_hashes()
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(solve,'guarded_process',side_effect=fake_guard), \
             patch.object(solve,'source_hashes',side_effect=[sources,{}]):
            report = solve.run(3,7,7,5,256,Path(directory)/'report.json',expected_model_sha256='0'*64)
        self.assertEqual(report['status'],'source_changed')
        self.assertFalse(report['complete'])
        self.assertIsNone(report['solver_result'])
        self.assertIsNone(report['conclusion'])
        self.assertIsNone(report['model_sha256'])

    def test_parent_witness_hash_failure_clears_acceptance(self):
        def fake_guard(command,seconds,memory,log_path,**kwargs):
            job = json.loads(Path(command[-1]).read_text())
            witness = Path(job['witness_directory'])/'tampered.json'
            witness.write_text('tampered')
            state = solve.initial_state(3,job['source_hashes'],job['expected_model_sha256'],7,7)
            state.update(complete=True,search_complete=True,cnf_complete=True,build_complete=True,
                         status='verified_witness',conclusion='verified_witness',solver_result=True,
                         witness_file=str(witness),witness_sha256='0'*64,model_sha256='fake')
            solve.atomic(job['state'],state)
            Path(log_path).write_text('')
            return {'gate_status':'exited','cleanup_status':'clean'}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(solve,'guarded_process',side_effect=fake_guard):
            report = solve.run(3,7,7,5,256,Path(directory)/'report.json',expected_model_sha256='0'*64)
        self.assertEqual(report['status'],'host_error')
        self.assertFalse(report['complete'])
        self.assertIsNone(report['solver_result'])
        self.assertIsNone(report['witness_file'])
        self.assertIsNotNone(report['worker_observed_witness_file'])


    def test_explicit_threshold_pair_required_by_api_and_cli(self):
        for first,second in ((4,7),(7,8),(None,7),(7,True)):
            with self.subTest(first=first,second=second),self.assertRaises(ValueError):
                solve.run(3,first,second,5,256,'unused.json',expected_model_sha256='0'*64)
        from contextlib import redirect_stderr
        import io
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as result:
            solve.main(['--n','3','--seconds','5','--expected-model-sha256','0'*64,'--output','unused.json'])
        self.assertEqual(result.exception.code,2)
        sources = solve.source_hashes()
        self.assertEqual(sources['threshold_source_sha256'],'57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb')
        self.assertEqual(sources['build_preflight_source_sha256'],'4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92')

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_changed_threshold_branches_are_wired_and_wrong_pair_hash_never_solves(self):
        for first,second,clauses,variables in ((5,5,372,95),(6,6,374,87),(7,7,438,23)):
            with tempfile.TemporaryDirectory() as directory:
                job = job_for(directory,9)
                job.update(atmost_two=first,conditional_atmost_one=second,
                           expected_model_sha256=fixture_hash(9,first,second))
                stub = SolverStub(None)
                with patch('pysat.solvers.Solver',return_value=stub):
                    self.assertEqual(solve.worker(job),0)
                report = json.loads(Path(job['state']).read_text())
            self.assertEqual(stub.calls,1)
            self.assertEqual(report['model_sha256'],fixture_hash(9,first,second))
            self.assertEqual((report['clauses_added'],report['variables']),(clauses,variables))
            self.assertEqual(report['thresholds'],{'atmost_two':first,'conditional_atmost_one':second})
            self.assertIsNone(report['solver_result'])
            self.assertFalse(report['complete'])
        with tempfile.TemporaryDirectory() as directory:
            job = job_for(directory,9)
            job['expected_model_sha256'] = fixture_hash(9,5,5)
            stub = SolverStub(False)
            with patch('pysat.solvers.Solver',return_value=stub):
                self.assertEqual(solve.worker(job),2)
            report = json.loads(Path(job['state']).read_text())
        self.assertEqual(stub.calls,0)
        self.assertFalse(report['search_performed'])
        self.assertIsNone(report['model_sha256'])
        self.assertIsNone(report['solver_result'])


if __name__ == '__main__':
    unittest.main()
