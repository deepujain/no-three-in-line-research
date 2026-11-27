"""Owned-guard explicit-threshold solve: <=30 seconds including construction.

Requires the expected complete threshold CNF hash before any search. The
unchanged sampled 256 MiB gate includes native memory and bounded cleanup.
SAT requires exact family decoding, dual verification and durable publication.
False is restricted-family solver-reported UNSAT, without proof checking.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_preflight import atomic, sha
from research.owned_process_guard import guarded_process
from research.near_quarter_compact_solve import decode_orbits, persist_witness
from research.near_quarter_direct_preflight import validate_thresholds

SOURCE_PATHS = {
    'model_source_sha256':ROOT/'src/near_quarter_model.py',
    'line_generator_sha256':ROOT/'src/line_model.py',
    'compact_source_sha256':ROOT/'src/near_quarter_compact.py',
    'row_quota_source_sha256':ROOT/'src/near_quarter_row_quota.py',
    'guard_source_sha256':ROOT/'research/owned_process_guard.py',
    'original_guard_utilities_sha256':ROOT/'research/near_quarter_preflight.py',
    'decode_witness_utilities_sha256':ROOT/'research/near_quarter_compact_solve.py',
    'threshold_source_sha256':ROOT/'src/near_quarter_direct_thresholds.py',
    'build_preflight_source_sha256':ROOT/'research/near_quarter_direct_preflight.py',
    'cli_entrypoint_sha256':ROOT/'src/lazy_sat.py',
    'verifier_source_sha256':ROOT/'src/verify.py',
    'solve_source_sha256':Path(__file__).resolve(),
}


class CancellationRequested(RuntimeError):
    pass


class BudgetExpired(RuntimeError):
    pass


@contextmanager
def cancellation_signals():
    """Keep SIGTERM/SIGINT as flags while reviewed bounded cleanup runs."""
    cancelled = [False]
    def cancel(signum,frame):
        cancelled[0] = True
    previous = {sig:signal.signal(sig,cancel) for sig in (signal.SIGTERM,signal.SIGINT)}
    try:
        yield lambda: cancelled[0]
    finally:
        for sig,handler in previous.items():
            signal.signal(sig,handler)


def source_hashes():
    return {key:sha(path) for key,path in SOURCE_PATHS.items()}


def initial_state(n,sources,expected,first,second):
    return {'n':n,'target':2*n,'mode':'build_and_solve','backend':'glucose3',
            'scope':'near-quarter-turn restricted family; target 2*n',
            'thresholds':{'atmost_two':first,'conditional_atmost_one':second},
            'status':'incomplete','phase':'startup','complete':False,'search_complete':False,
            'search_performed':False,'solver_result':None,'conclusion':None,
            'proof_checked':False,'clauses':0,'clauses_added':0,'variables':0,
            'cnf_complete':False,'build_complete':False,'model_sha256':None,
            'prefix_sha256':None,'witness_file':None,'witness_sha256':None,
            'counter_semantics':'last atomically published lower bounds until CNF complete',
            'expected_model_sha256':expected,'source_hashes':sources,
            'solve_source_sha256':sources['solve_source_sha256']}


def validate_expected_hash(value):
    if (type(value) is not str or len(value) != 64 or
            any(c not in '0123456789abcdef' for c in value)):
        raise ValueError('expected model SHA-256 is required: 64 lowercase hex digits')


def worker(job):
    state = initial_state(job['n'],job['source_hashes'],job['expected_model_sha256'],
                          job['atmost_two'],job['conditional_atmost_one'])
    started = time.monotonic()
    last_publish = 0
    solver = None
    timer = None
    fired = threading.Event()
    def publish(force=False):
        nonlocal last_publish
        now = time.monotonic()
        if state['phase'] == 'cnf':
            if now >= job['deadline_monotonic']:
                raise BudgetExpired('construction deadline reached')
        if force or now-last_publish >= .05:
            if state['phase'] == 'cnf' and (os.getppid() != job['guard_parent_pid'] or
                                           not Path(job['guard_alive_path']).exists()):
                raise CancellationRequested('guard parent disappeared during construction')
            atomic(job['state'],state)
            last_publish = now
    def stable():
        if source_hashes() != job['source_hashes']:
            raise ValueError('source hashes changed')
    def stop_timer():
        nonlocal timer
        if timer is not None:
            timer.cancel()
            timer.join()
            timer = None
    publish(True)
    try:
        if os.getppid() != job['guard_parent_pid'] or not Path(job['guard_alive_path']).exists():
            raise CancellationRequested('guard parent disappeared before construction')
        stable()
        validate_expected_hash(job['expected_model_sha256'])
        validate_thresholds(job['atmost_two'],job['conditional_atmost_one'])
        from src.near_quarter_model import orbit_map,check_candidate
        from src.near_quarter_direct_thresholds import CapacityThresholds,model_header,streamed_cnf
        from pysat.solvers import Solver
        model = orbit_map(job['n'])
        config = CapacityThresholds(job['atmost_two'],job['conditional_atmost_one'])
        header = model_header(model,config)
        state['family'] = header['family']
        state['variables'] = len(model['orbits'])
        state['phase'] = 'cnf'
        publish(True)
        solver = Solver(name='glucose3')
        digest = hashlib.sha256()
        digest.update((json.dumps(header,sort_keys=True,separators=(',',':'))+'\n').encode())
        for clause in streamed_cnf(model,config):
            digest.update((json.dumps(clause,separators=(',',':'))+'\n').encode())
            state['clauses'] += 1
            state['variables'] = max(state['variables'],max(map(abs,clause),default=0))
            solver.add_clause(clause)
            state['clauses_added'] += 1
            state['prefix_sha256'] = digest.hexdigest()
            publish()
        stable()
        state.update(cnf_complete=True,build_complete=True,model_sha256=digest.hexdigest(),
                     build_seconds=time.monotonic()-started)
        if digest.hexdigest() != job['expected_model_sha256']:
            raise ValueError('complete CNF hash differs from expected preflight model')
        remaining = job['deadline_monotonic']-time.monotonic()
        if remaining <= 0:
            state.update(status='budget_exhausted',phase='finished')
            publish(True)
            return 0
        def interrupt():
            fired.set()
            solver.interrupt()
        timer = threading.Timer(remaining,interrupt)
        timer.daemon = True
        timer.start()
        state.update(phase='solve',search_performed=True)
        publish(True)
        solve_started = time.monotonic()
        answer = solver.solve_limited(expect_interrupt=True)
        state['solve_seconds'] = time.monotonic()-solve_started
        stop_timer()  # Must join before deleting the solver or changing its reference.
        state['timer_interrupt_fired'] = fired.is_set()
        stable()
        if fired.is_set() or time.monotonic() >= job['deadline_monotonic']:
            state.update(status='interrupted',phase='finished')
            publish(True)
            return 0
        if answer is None:
            state.update(status='no_result',phase='finished')
            publish(True)
            return 0
        if answer is not True and answer is not False:
            raise ValueError('unexpected native solve result')
        if answer is True:
            # PySAT materializes every auxiliary literal. Free the native CNF
            # immediately afterward, before allocating verification state.
            assignment = solver.get_model()
            solver.delete()
            solver = None
            selected = decode_orbits(model,assignment,state['variables'])
            del assignment
            checked = check_candidate(model,selected)
            if not checked['valid_full_witness']:
                raise ValueError('decoded SAT model fails independent exact verifiers')
            stable()
            payload = {**checked['certificate'],'selected_orbit_ids':selected,
                       'scope':state['scope'],'model_sha256':state['model_sha256'],
                       'source_hashes':job['source_hashes'],'checks':checked['checks']}
            path,witness_hash = persist_witness(job['witness_directory'],payload)
            state.update(witness_file=path,witness_sha256=witness_hash,
                         witness_geometry_sha256=checked['checks'][0]['normalized_sha256'])
            # A valid saved witness can survive a later kill without implying
            # that the enclosing guarded run completed successfully.
            publish(True)
            conclusion = 'verified_witness'
        else:
            solver.delete()
            solver = None
            conclusion = 'restricted_family_unsat_solver_reported'
        stable()
        if time.monotonic() >= job['deadline_monotonic']:
            state.update(status='budget_exhausted',phase='finished')
        else:
            state.update(status=conclusion,phase='finished',complete=True,search_complete=True,
                         conclusion=conclusion,solver_result=answer)
        publish(True)
        return 0
    except (BudgetExpired,CancellationRequested) as exc:
        state.update(status='budget_exhausted' if isinstance(exc,BudgetExpired) else 'cancelled',
                     phase='finished',error=str(exc),complete=False,search_complete=False,
                     solver_result=None,conclusion=None)
        publish(True)
        return 0
    except Exception as exc:
        state.update(status='error',error=f'{type(exc).__name__}: {exc}',complete=False,
                     phase='finished',search_complete=False,solver_result=None,conclusion=None,
                     cnf_complete=False,build_complete=False,model_sha256=None)
        publish(True)
        return 2
    finally:
        stop_timer()
        if solver is not None:
            solver.delete()


def run(n,first,second,seconds,rss_mib,output,witness_directory=None,expected_model_sha256=None):
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('n must be an odd integer >= 3')
    if not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('seconds must be positive and <= 30 including build')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('rss-mib must be positive and <= 256')
    validate_thresholds(first,second)
    validate_expected_hash(expected_model_sha256)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    witness_directory = Path(witness_directory or output.parent/'near-quarter-witnesses').resolve()
    witness_directory.mkdir(parents=True,exist_ok=True)
    sources = source_hashes()
    report = initial_state(n,sources,expected_model_sha256,first,second)
    with tempfile.TemporaryDirectory(prefix='near-quarter-direct-solve-') as directory:
        directory = Path(directory)
        state_path,log_path,job_path = (directory/name for name in ('state.json','worker.log','job.json'))
        alive_path = directory/'guard-alive'
        alive_path.touch()
        atomic(job_path,{'n':n,'atmost_two':first,'conditional_atmost_one':second,
                        'state':str(state_path),'source_hashes':sources,
                        'expected_model_sha256':expected_model_sha256,
                        'witness_directory':str(witness_directory),
                        'guard_parent_pid':os.getpid(),
                        'guard_alive_path':str(alive_path),
                        'deadline_monotonic':time.monotonic()+seconds})
        atomic(output,report)
        try:
            try:
                with cancellation_signals() as cancelled:
                    guard = guarded_process([sys.executable,str(Path(__file__).resolve()),
                                             '--_worker',str(job_path)],seconds,rss_mib,log_path,
                                             cancelled=cancelled)
            finally:
                alive_path.unlink(missing_ok=True)
            if state_path.exists():
                report.update(json.loads(state_path.read_text()))
            report['guard'] = guard
            with open(log_path,'rb') as log:
                log.seek(0,2)
                log.seek(max(0,log.tell()-4096))
                report['worker_log_tail'] = log.read().decode(errors='replace')
            stable = sources == source_hashes()
            if guard['gate_status'] != 'exited' or not stable:
                report.update(worker_observed_status=report['status'],
                              worker_observed_witness_file=report['witness_file'],
                              status=guard['gate_status'] if stable else 'source_changed',
                              complete=False,search_complete=False,conclusion=None,solver_result=None,
                              cnf_complete=False,build_complete=False,model_sha256=None,
                              witness_file=None,witness_sha256=None)
            elif report['witness_file'] is not None and sha(report['witness_file']) != report['witness_sha256']:
                raise ValueError('saved witness file hash mismatch')
        except CancellationRequested as exc:
            if state_path.exists():
                report.update(json.loads(state_path.read_text()))
            report.update(status='cancelled',error=str(exc),complete=False,search_complete=False,
                          conclusion=None,solver_result=None,cnf_complete=False,build_complete=False,
                          model_sha256=None,worker_observed_witness_file=report['witness_file'],
                          witness_file=None,witness_sha256=None)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            report.update(status='host_error',error=str(exc),complete=False,search_complete=False,
                          conclusion=None,solver_result=None,cnf_complete=False,build_complete=False,
                          model_sha256=None,worker_observed_witness_file=report['witness_file'],
                          witness_file=None,witness_sha256=None)
        atomic(output,report)
    return report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == '--_worker':
        return worker(json.loads(Path(args[1]).read_text()))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True)
    parser.add_argument('--atmost-two-direct-limit',type=int,choices=(5,6,7),required=True)
    parser.add_argument('--conditional-atmost-one-direct-limit',type=int,choices=(5,6,7),required=True)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--rss-mib',type=float,default=256)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--witness-directory',type=Path)
    parser.add_argument('--expected-model-sha256',required=True)
    parsed = parser.parse_args(args)
    try:
        report = run(parsed.n,parsed.atmost_two_direct_limit,parsed.conditional_atmost_one_direct_limit,
                     parsed.seconds,parsed.rss_mib,parsed.output,
                     parsed.witness_directory,parsed.expected_model_sha256)
    except (OSError,ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
