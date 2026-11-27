"""Build-only row-quota near-quarter preflight: <=30 seconds, <=256 MiB.

Uses the unchanged fail-closed sampled parent-plus-child host RSS guard.
Never solves. Streaming does not bound native memory; sampling can overshoot.
All previous compilers, preflights and solver wrappers remain unchanged.
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
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_preflight import atomic,guarded_process,sha

SOURCE_PATHS = {
    'model_source_sha256':ROOT/'src/near_quarter_model.py',
    'line_generator_sha256':ROOT/'src/line_model.py',
    'verifier_source_sha256':ROOT/'src/verify.py',
    'compact_source_sha256':ROOT/'src/near_quarter_compact.py',
    'row_quota_source_sha256':ROOT/'src/near_quarter_row_quota.py',
    'guard_source_sha256':ROOT/'research/near_quarter_preflight.py',
    'preflight_source_sha256':Path(__file__).resolve(),
    'cli_entrypoint_sha256':ROOT/'src/lazy_sat.py',
}


class PreflightStopped(RuntimeError):
    pass


@contextmanager
def cancellation_signals():
    def cancel(signum,frame):
        raise PreflightStopped(f'cancelled by signal {signum}')
    previous = {sig:signal.signal(sig,cancel) for sig in (signal.SIGTERM,signal.SIGINT)}
    try:
        yield
    finally:
        for sig,handler in previous.items():
            signal.signal(sig,handler)


def source_hashes():
    return {key:sha(path) for key,path in SOURCE_PATHS.items()}


def initial_state(n,sources):
    m = n//2
    return {'n':n,'mode':'build','backend':'glucose3','status':'incomplete','phase':'startup',
            'complete':False,'cnf_complete':False,'build_complete':False,
            'search_performed':False,'solver_result':None,
            'clauses':0,'clauses_added':0,'variables':0,
            'model_sha256':None,'prefix_sha256':None,
            'c4_line_groups':0,'c4_line_groups_complete':False,
            'represented_full_lines':0,'weighted_line_groups':0,
            'special_diagonal_groups':0,'diagonal_guard_incidence_sum':0,
            'row_floor_clauses_algebraic':m*(n-1)+1,
            'row_floor_literals_algebraic':m*(n-1)*(n-2)+m,
            'counter_semantics':'last atomically published lower bounds until complete',
            'line_count_semantics':'full C4 groups; weighted groups exclude special diagonals',
            'source_hashes':sources,'preflight_source_sha256':sources['preflight_source_sha256']}


def model_header(model):
    from src.near_quarter_row_quota import row_quota_counts
    return {'family':row_quota_counts(model),'off_diagonal_quotient':'full C4',
            'exceptional_diagonal_guards':True,'row_floor_representatives':'0..n//2',
            'row_floor':'weighted occupancy >= 2; replaces global four-orbit equality'}


def worker(job):
    state = initial_state(job['n'],job['source_hashes'])
    last_publish = 0
    solver = None
    def publish(force=False):
        nonlocal last_publish
        now = time.monotonic()
        progress_phase = state['phase'] in ('line_groups','cnf')
        if progress_phase and now >= job['deadline_monotonic']:
            raise PreflightStopped('construction deadline reached')
        if force or now-last_publish >= .05:
            if progress_phase and (os.getppid() != job['guard_parent_pid'] or
                                   not Path(job['guard_alive_path']).exists()):
                raise PreflightStopped('guard parent disappeared')
            atomic(job['state'],state)
            last_publish = now
    publish(True)
    try:
        if os.getppid() != job['guard_parent_pid'] or not Path(job['guard_alive_path']).exists():
            raise PreflightStopped('guard parent disappeared before import')
        if source_hashes() != job['source_hashes']:
            raise ValueError('source hash changed before encoder import')
        from src.near_quarter_model import orbit_map
        from src.near_quarter_compact import line_groups
        from src.near_quarter_row_quota import streamed_cnf
        model = orbit_map(job['n'])
        header = model_header(model)
        state['family'] = header['family']
        state['variables'] = len(model['orbits'])
        state['phase'] = 'line_groups'
        publish(True)
        for group in line_groups(model):
            state['c4_line_groups'] += 1
            state['represented_full_lines'] += group['orbit_size']
            if group['special_diagonal_orbit']:
                state['special_diagonal_groups'] += 1
            else:
                state['weighted_line_groups'] += 1
                state['diagonal_guard_incidence_sum'] += len(group['diagonal_guards'])
            publish()
        state.update(c4_line_groups_complete=True,phase='cnf')
        publish(True)
        from pysat.solvers import Solver
        solver = Solver(name='glucose3')
        digest = hashlib.sha256()
        digest.update((json.dumps(header,sort_keys=True,separators=(',',':'))+'\n').encode())
        for clause in streamed_cnf(model):
            digest.update((json.dumps(clause,separators=(',',':'))+'\n').encode())
            state['clauses'] += 1
            state['variables'] = max(state['variables'],max(map(abs,clause),default=0))
            solver.add_clause(clause)
            state['clauses_added'] += 1
            state['prefix_sha256'] = digest.hexdigest()
            publish()
        if source_hashes() != job['source_hashes']:
            raise ValueError('source hash changed during construction')
        if time.monotonic() >= job['deadline_monotonic']:
            raise PreflightStopped('construction deadline reached')
        state.update(status='built',phase='complete',complete=True,cnf_complete=True,
                     build_complete=True,model_sha256=digest.hexdigest(),prefix_sha256=digest.hexdigest())
        publish(True)
        return 0
    except PreflightStopped as exc:
        state.update(status='incomplete',phase='finished',error=str(exc),complete=False,
                     cnf_complete=False,build_complete=False,model_sha256=None)
        publish(True)
        return 0
    except Exception as exc:
        state.update(status='error',phase='finished',error=f'{type(exc).__name__}: {exc}',complete=False,
                     cnf_complete=False,build_complete=False,model_sha256=None)
        publish(True)
        return 2
    finally:
        if solver is not None:
            solver.delete()


def preflight(n,seconds,rss_mib,output):
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('n must be an odd integer >= 3')
    if not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('seconds must be positive and <= 30')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('rss-mib must be positive and <= 256')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    sources = source_hashes()
    report = initial_state(n,sources)
    with tempfile.TemporaryDirectory(prefix='near-quarter-row-quota-preflight-') as directory:
        directory = Path(directory)
        state_path,log_path,job_path = (directory/name for name in ('state.json','worker.log','job.json'))
        alive_path = directory/'guard-alive'
        alive_path.touch()
        atomic(job_path,{'n':n,'state':str(state_path),'source_hashes':sources,
                        'guard_parent_pid':os.getpid(),'guard_alive_path':str(alive_path),
                        'deadline_monotonic':time.monotonic()+seconds})
        atomic(output,report)
        try:
            try:
                with cancellation_signals():
                    guard = guarded_process([sys.executable,str(Path(__file__).resolve()),
                                             '--_worker',str(job_path)],seconds,rss_mib,log_path)
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
                report.update(worker_observed_complete=report['complete'],
                              status=guard['gate_status'] if stable else 'source_changed',
                              complete=False,cnf_complete=False,build_complete=False,model_sha256=None)
        except PreflightStopped as exc:
            if state_path.exists():
                report.update(json.loads(state_path.read_text()))
            report.update(status='cancelled',error=str(exc),complete=False,
                          cnf_complete=False,build_complete=False,model_sha256=None)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            report.update(status='host_error',error=str(exc),complete=False,
                          cnf_complete=False,build_complete=False,model_sha256=None)
        atomic(output,report)
    return report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == '--_worker':
        return worker(json.loads(Path(args[1]).read_text()))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True)
    parser.add_argument('--mode',choices=('build',),default='build')
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--rss-mib',type=float,default=256)
    parser.add_argument('--output',type=Path,required=True)
    parsed = parser.parse_args(args)
    try:
        report = preflight(parsed.n,parsed.seconds,parsed.rss_mib,parsed.output)
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
