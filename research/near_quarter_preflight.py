"""Host-guarded count/build preflight for the reviewed near-quarter CNF.

Never solves. Default gates: 30 seconds and 256 MiB monitor-plus-child RSS.
RSS is sampled by the host, including native solver allocations; it is not a
kernel allocation cap. Leave headroom for sampling overshoot and the monitor.
"""
import argparse
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
MODEL = ROOT/'src/near_quarter_model.py'
LINES = ROOT/'src/line_model.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True)+'\n')
    os.replace(temporary, path)


def process_rss_kib(pid):
    """Sum fresh session/group and descendants, including native allocations."""
    result = subprocess.run(['ps','-axo','pid=,ppid=,pgid=,rss='],
                            capture_output=True, text=True, check=True, timeout=.5)
    rows = [tuple(map(int, row.split())) for row in result.stdout.splitlines() if row.strip()]
    if any(len(row) != 4 for row in rows):
        raise ValueError('malformed process monitor row')
    by_pid = {row[0]:row for row in rows}
    if len(by_pid) != len(rows) or any(row[3] < 0 for row in rows):
        raise ValueError('invalid process monitor rows')
    for required_pid in (os.getpid(), pid):
        if required_pid not in by_pid or by_pid[required_pid][3] <= 0:
            raise ValueError('process monitor omitted required positive RSS')
    included = {pid}
    while True:
        expanded = included | {p for p, parent, group, _ in rows
                               if parent in included or group == pid}
        if expanded == included:
            break
        included = expanded
    included.add(os.getpid())
    return sum(rss for p, _, _, rss in rows if p in included)


def guarded_process(command, seconds, rss_mib, log_path):
    """Host guard; monitoring failure is fatal, never interpreted as success."""
    started = time.monotonic()
    peak = 0
    samples = 0
    reason = None
    error = None
    with open(log_path, 'wb') as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
        try:
            while process.poll() is None:
                if time.monotonic()-started >= seconds:
                    reason = 'wall_limit'
                    break
                try:
                    rss = process_rss_kib(process.pid)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    reason = 'monitor_error'
                    error = str(exc)
                    break
                peak = max(peak, rss)
                samples += 1
                if rss > rss_mib*1024:
                    reason = 'rss_limit'
                    break
                if time.monotonic()-started >= seconds:
                    reason = 'wall_limit'
                    break
                time.sleep(min(.025, max(0, seconds-(time.monotonic()-started))))
            # Conservative terminal checks: a final child publication cannot
            # override an observed gate failure, even if exit races the guard.
            if reason is None and time.monotonic()-started >= seconds:
                reason = 'wall_limit'
            if reason is None and not samples:
                reason = 'monitor_error'
                error = 'worker exited before any RSS sample'
        finally:
            # Remove surviving members of the original group after child exit.
            # This fixed worker does not spawn or re-session other processes.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return {'gate_status':reason or ('exited' if process.returncode == 0 else 'worker_error'),
            'returncode':process.returncode, 'elapsed_seconds':time.monotonic()-started,
            'peak_sampled_rss_kib':peak, 'rss_samples':samples,
            'monitor_error':error, 'seconds_limit':seconds, 'rss_limit_mib':rss_mib,
            'rss_scope':'guard parent plus child process group and descendants; native heap included',
            'gate_semantics':'sampled RSS kill gate; possible sampling overshoot; transient ps helper excluded'}


def worker(job):
    """Only construction; no solver search, SAT or UNSAT result is produced."""
    state = {'status':'incomplete', 'phase':'startup', 'complete':False,
             'weighted_lines':0, 'weighted_lines_complete':False,
             'clauses':0, 'variables':0, 'clauses_added':0,
             'cnf_complete':False, 'build_complete':False,
             'model_sha256':None, 'prefix_sha256':None,
             'counter_semantics':'last atomically published lower bounds until complete',
             'search_performed':False, 'solver_result':None,
             'n':job['n'], 'mode':job['mode'], 'source_hashes':job['source_hashes']}
    last_publish = 0
    def publish(force=False):
        nonlocal last_publish
        now = time.monotonic()
        if force or now-last_publish >= .05:
            atomic(job['state'], state)
            last_publish = now
    def stable():
        return job['source_hashes'] == {'model_source_sha256':sha(MODEL),
                                      'line_generator_sha256':sha(LINES)}
    publish(True)
    solver = None
    try:
        if not stable():
            raise ValueError('source hash changed before import')
        sys.path.insert(0, str(ROOT))
        from src.near_quarter_model import orbit_map, family_counts, weighted_lines, streamed_cnf
        model = orbit_map(job['n'])
        state['family'] = family_counts(model)
        state['variables'] = len(model['orbits'])
        state['phase'] = 'weighted_lines'
        publish(True)
        for _ in weighted_lines(model):
            state['weighted_lines'] += 1
            publish()
        state['weighted_lines_complete'] = True
        state['phase'] = 'cnf'
        publish(True)
        if job['mode'] == 'build':
            from pysat.solvers import Solver
            solver = Solver(name='glucose3')
        digest = hashlib.sha256()
        digest.update((json.dumps({'family':state['family'], 'quotient_halfturn':True},
                                 sort_keys=True, separators=(',',':'))+'\n').encode())
        for clause in streamed_cnf(model):
            digest.update((json.dumps(clause, separators=(',',':'))+'\n').encode())
            state['clauses'] += 1
            state['variables'] = max(state['variables'], max(map(abs, clause), default=0))
            if solver is not None:
                solver.add_clause(clause)
                state['clauses_added'] += 1
            state['prefix_sha256'] = digest.hexdigest()
            publish()
        if not stable():
            raise ValueError('source hash changed during construction')
        state.update(status='built' if solver is not None else 'counted', phase='complete',
                     complete=True, cnf_complete=True, build_complete=solver is not None,
                     model_sha256=digest.hexdigest(), prefix_sha256=digest.hexdigest())
        publish(True)
        return 0
    except Exception as exc:
        state.update(status='error', error=f'{type(exc).__name__}: {exc}')
        publish(True)
        return 2
    finally:
        if solver is not None:
            solver.delete()


def preflight(n, mode, seconds, rss_mib, output):
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('n must be an odd integer >= 3')
    if mode not in ('count', 'build'):
        raise ValueError('mode must be count or build')
    if not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('seconds must be positive and <= 30')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('rss-mib must be positive and <= 256')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    sources = {'model_source_sha256':sha(MODEL), 'line_generator_sha256':sha(LINES)}
    report = {'n':n, 'mode':mode, 'status':'incomplete', 'complete':False,
              'phase':'startup', 'weighted_lines':0, 'weighted_lines_complete':False,
              'clauses':0, 'clauses_added':0, 'variables':0,
              'cnf_complete':False, 'build_complete':False,
              'model_sha256':None, 'prefix_sha256':None,
              'counter_semantics':'last atomically published lower bounds until complete',
              'search_performed':False, 'solver_result':None,
              'source_hashes':sources, 'preflight_source_sha256':sha(__file__)}
    with tempfile.TemporaryDirectory(prefix='near-quarter-preflight-') as directory:
        directory = Path(directory)
        state_path = directory/'state.json'
        log_path = directory/'worker.log'
        job_path = directory/'job.json'
        atomic(job_path, {'n':n, 'mode':mode, 'state':str(state_path), 'source_hashes':sources})
        atomic(output, report)
        try:
            guard = guarded_process([sys.executable, str(Path(__file__).resolve()),
                                     '--_worker', str(job_path)], seconds, rss_mib, log_path)
            if state_path.exists():
                report.update(json.loads(state_path.read_text()))
            report['guard'] = guard
            report['worker_log_tail'] = log_path.read_bytes()[-4096:].decode(errors='replace')
            stable = sources == {'model_source_sha256':sha(MODEL), 'line_generator_sha256':sha(LINES)}
            if guard['gate_status'] != 'exited' or not stable:
                report['worker_observed_complete'] = report['complete']
                report.update(status=guard['gate_status'] if stable else 'source_changed',
                              complete=False, cnf_complete=False, build_complete=False,
                              model_sha256=None)
            elif not report['complete']:
                report['status'] = 'worker_incomplete'
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            report.update(status='host_error', complete=False, error=str(exc),
                          cnf_complete=False, build_complete=False, model_sha256=None)
        atomic(output, report)
    return report


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == '--_worker':
        return worker(json.loads(Path(args[1]).read_text()))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--mode', choices=('count','build'), default='count')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--rss-mib', type=float, default=256)
    parser.add_argument('--output', type=Path, required=True)
    parsed = parser.parse_args(args)
    try:
        report = preflight(parsed.n, parsed.mode, parsed.seconds, parsed.rss_mib, parsed.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
