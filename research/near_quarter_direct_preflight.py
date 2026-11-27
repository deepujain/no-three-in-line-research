"""Owned-guard count/build preflight for explicit direct threshold pairs.

Count mode measures the C4 support histogram and exact aggregate encoding costs
without constructing a native Solver or complete CNF. Build mode inserts the
chosen complete CNF without searching. Both retain <=30 seconds / <=256 MiB.
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
from research.near_quarter_preflight import atomic,sha
from research.owned_process_guard import guarded_process

SOURCE_PATHS = {
    'model_source_sha256':ROOT/'src/near_quarter_model.py',
    'line_generator_sha256':ROOT/'src/line_model.py',
    'verifier_source_sha256':ROOT/'src/verify.py',
    'compact_source_sha256':ROOT/'src/near_quarter_compact.py',
    'row_quota_source_sha256':ROOT/'src/near_quarter_row_quota.py',
    'threshold_source_sha256':ROOT/'src/near_quarter_direct_thresholds.py',
    'guard_source_sha256':ROOT/'research/owned_process_guard.py',
    'original_guard_utilities_sha256':ROOT/'research/near_quarter_preflight.py',
    'preflight_source_sha256':Path(__file__).resolve(),
    'cli_entrypoint_sha256':ROOT/'src/lazy_sat.py',
}


class PreflightStopped(RuntimeError):
    pass


@contextmanager
def cancellation_signals():
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


def validate_thresholds(first,second):
    if any(type(value) is not int or value not in (5,6,7) for value in (first,second)):
        raise ValueError('explicit direct thresholds must each be 5, 6 or 7')


def initial_state(n,mode,first,second,sources):
    return {'n':n,'mode':mode,'backend':'glucose3' if mode == 'build' else None,
            'status':'incomplete','phase':'startup','complete':False,
            'cnf_complete':False,'build_complete':False,'counts_complete':False,
            'support_histogram_complete':False,'support_histogram':[],
            'search_performed':False,'solver_result':None,'native_solver_constructed':False,
            'clauses':0,'clauses_added':0,'variables':0,'literals':0,
            'model_sha256':None,'prefix_sha256':None,'candidate_formula_counts':[],
            'thresholds':{'atmost_two':first,'conditional_atmost_one':second},
            'c4_line_groups':0,'c4_line_groups_complete':False,'represented_full_lines':0,
            'special_diagonal_groups':0,'weighted_line_groups':0,
            'counter_semantics':'observed lower bounds until complete; count mode has no formula digest',
            'count_semantics':'histogram multiplied by exact installed encoder emissions, plus diagonal equality and row floors',
            'source_hashes':sources,'preflight_source_sha256':sources['preflight_source_sha256']}


def capacity_cost(key,config):
    """Emit one bounded synthetic capacity to measure its exact installed cost."""
    from pysat.formula import IDPool
    from src.near_quarter_direct_thresholds import shared_capacity_clauses
    light,heavy,forced,guards = key
    coefficients = forced*[3]+heavy*[2]+light*[1]
    real = len(coefficients)+guards
    pool = IDPool(start_from=real+1)
    clauses = list(shared_capacity_clauses(enumerate(coefficients,1),
        range(len(coefficients)+1,real+1),pool,config))
    return len(clauses),pool.top-real,sum(map(len,clauses))


def aggregate_counts(model,histogram,publish=lambda:None):
    """No Solver: count nine candidates from fresh histogram and small capacities."""
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    from src.near_quarter_direct_thresholds import CapacityThresholds
    real = len(model['orbits'])
    diagonal = list(range(model['four_count']+1,real+1))
    pool = IDPool(start_from=real+1)
    diagonal_clauses = CardEnc.equals(lits=diagonal,bound=1,vpool=pool,
                                      encoding=EncType.seqcounter).clauses
    m,n = model['n']//2,model['n']
    fixed_clauses = len(diagonal_clauses)+m*(n-1)+1
    fixed_auxiliary = pool.top-real
    fixed_literals = sum(map(len,diagonal_clauses))+m*(n-1)*(n-2)+m
    candidates = []
    for first in (5,6,7):
        for second in (5,6,7):
            config = CapacityThresholds(first,second)
            clauses,auxiliary,literals = fixed_clauses,fixed_auxiliary,fixed_literals
            for key,count in sorted(histogram.items()):
                local_clauses,local_auxiliary,local_literals = capacity_cost(key,config)
                clauses += count*local_clauses
                auxiliary += count*local_auxiliary
                literals += count*local_literals
                publish()
            candidates.append({'thresholds':{'atmost_two':first,'conditional_atmost_one':second},
                               'clauses':clauses,'auxiliaries':auxiliary,'variables':real+auxiliary,
                               'literals':literals})
    return candidates


def worker(job):
    state = initial_state(job['n'],job['mode'],job['atmost_two'],job['conditional_atmost_one'],job['source_hashes'])
    histogram = {}
    last_publish = 0
    solver = None
    def publish(force=False):
        nonlocal last_publish
        now = time.monotonic()
        progress = state['phase'] in ('line_groups','histogram_costs','cnf')
        if progress and now >= job['deadline_monotonic']:
            raise PreflightStopped('preflight deadline reached')
        if force or now-last_publish >= .05:
            if progress and (os.getppid() != job['guard_parent_pid'] or
                             not Path(job['guard_alive_path']).exists()):
                raise PreflightStopped('guard parent disappeared')
            state['support_histogram'] = [dict(light=key[0],heavy=key[1],forced=key[2],guards=key[3],groups=count)
                                          for key,count in sorted(histogram.items())]
            atomic(job['state'],state)
            last_publish = now
    publish(True)
    try:
        validate_thresholds(job['atmost_two'],job['conditional_atmost_one'])
        if job['mode'] not in ('count','build'):
            raise ValueError('mode must be count or build')
        if os.getppid() != job['guard_parent_pid'] or not Path(job['guard_alive_path']).exists():
            raise PreflightStopped('guard parent disappeared before import')
        if source_hashes() != job['source_hashes']:
            raise ValueError('source hash changed before encoder import')
        from src.near_quarter_model import orbit_map
        from src.near_quarter_compact import line_groups
        from src.near_quarter_direct_thresholds import CapacityThresholds,model_header,streamed_cnf
        model = orbit_map(job['n'])
        config = CapacityThresholds(job['atmost_two'],job['conditional_atmost_one'])
        header = model_header(model,config)
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
                weights = group['off_diagonal_weights']
                key = (sum(w == 1 for _,w in weights),sum(w == 2 for _,w in weights),
                       sum(w > 2 for _,w in weights),len(group['diagonal_guards']))
                histogram[key] = histogram.get(key,0)+1
            publish()
        state.update(c4_line_groups_complete=True,support_histogram_complete=True,phase='histogram_costs')
        publish(True)
        state['candidate_formula_counts'] = aggregate_counts(model,histogram,publish)
        selected = next(row for row in state['candidate_formula_counts'] if row['thresholds'] == state['thresholds'])
        state['counts_complete'] = True
        if job['mode'] == 'count':
            state.update(clauses=selected['clauses'],variables=selected['variables'],literals=selected['literals'])
        else:
            state['phase'] = 'cnf'
            publish(True)
            from pysat.solvers import Solver
            solver = Solver(name='glucose3')
            state['native_solver_constructed'] = True
            digest = hashlib.sha256()
            digest.update((json.dumps(header,sort_keys=True,separators=(',',':'))+'\n').encode())
            for clause in streamed_cnf(model,config):
                digest.update((json.dumps(clause,separators=(',',':'))+'\n').encode())
                state['clauses'] += 1
                state['literals'] += len(clause)
                state['variables'] = max(state['variables'],max(map(abs,clause),default=0))
                solver.add_clause(clause)
                state['clauses_added'] += 1
                state['prefix_sha256'] = digest.hexdigest()
                publish()
            if (state['clauses'],state['variables'],state['literals']) != (selected['clauses'],selected['variables'],selected['literals']):
                raise ValueError('constructed formula differs from exact histogram counts')
            state.update(model_sha256=digest.hexdigest(),cnf_complete=True,build_complete=True)
        if source_hashes() != job['source_hashes']:
            raise ValueError('source hash changed during preflight')
        if time.monotonic() >= job['deadline_monotonic']:
            raise PreflightStopped('preflight deadline reached')
        state.update(status='built' if job['mode'] == 'build' else 'counted',phase='complete',complete=True)
        publish(True)
        return 0
    except PreflightStopped as exc:
        state.update(status='incomplete',phase='finished',error=str(exc),complete=False,
                     counts_complete=False,support_histogram_complete=False,cnf_complete=False,build_complete=False,model_sha256=None)
        publish(True)
        return 0
    except Exception as exc:
        state.update(status='error',phase='finished',error=f'{type(exc).__name__}: {exc}',complete=False,
                     counts_complete=False,support_histogram_complete=False,cnf_complete=False,build_complete=False,model_sha256=None)
        publish(True)
        return 2
    finally:
        if solver is not None:
            solver.delete()


def preflight(n,mode,first,second,seconds,rss_mib,output):
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('n must be an odd integer >= 3')
    if mode not in ('count','build'):
        raise ValueError('mode must be count or build')
    validate_thresholds(first,second)
    if not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('seconds must be positive and <= 30')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('rss-mib must be positive and <= 256')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    sources = source_hashes()
    report = initial_state(n,mode,first,second,sources)
    with tempfile.TemporaryDirectory(prefix='near-quarter-direct-preflight-') as directory:
        directory = Path(directory)
        state_path,log_path,job_path = (directory/name for name in ('state.json','worker.log','job.json'))
        alive_path = directory/'guard-alive'
        alive_path.touch()
        atomic(job_path,{'n':n,'mode':mode,'atmost_two':first,'conditional_atmost_one':second,
                        'state':str(state_path),'source_hashes':sources,
                        'guard_parent_pid':os.getpid(),'guard_alive_path':str(alive_path),
                        'deadline_monotonic':time.monotonic()+seconds})
        atomic(output,report)
        try:
            try:
                with cancellation_signals() as cancelled:
                    guard = guarded_process([sys.executable,str(Path(__file__).resolve()),
                                             '--_worker',str(job_path)],seconds,rss_mib,log_path,cancelled=cancelled)
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
                              status=guard['gate_status'] if stable else 'source_changed',complete=False,
                              counts_complete=False,support_histogram_complete=False,
                              cnf_complete=False,build_complete=False,model_sha256=None)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            report.update(status='host_error',error=str(exc),complete=False,counts_complete=False,
                          support_histogram_complete=False,cnf_complete=False,build_complete=False,model_sha256=None)
        atomic(output,report)
    return report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == '--_worker':
        return worker(json.loads(Path(args[1]).read_text()))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True)
    parser.add_argument('--mode',choices=('count','build'),required=True)
    parser.add_argument('--atmost-two-direct-limit',type=int,choices=(5,6,7),required=True)
    parser.add_argument('--conditional-atmost-one-direct-limit',type=int,choices=(5,6,7),required=True)
    parser.add_argument('--seconds',type=float,default=30)
    parser.add_argument('--rss-mib',type=float,default=256)
    parser.add_argument('--output',type=Path,required=True)
    parsed = parser.parse_args(args)
    try:
        report = preflight(parsed.n,parsed.mode,parsed.atmost_two_direct_limit,
            parsed.conditional_atmost_one_direct_limit,parsed.seconds,parsed.rss_mib,parsed.output)
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
