"""Keep bounded numerical experiments working between shepherd reviews.

This is a process supervisor, not an AI agent. It consumes an immutable job
manifest, runs at most three one-core children, records exact argv/source hashes
and receipts, and enforces the pilot deadline and aggregate worker-time budget.
Run from the repository: .venv/bin/python src/experiment_pool.py --queue research/queue.json
"""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'src/lazy_sat.py', 'src/trade_search.py', 'research/guided_repair.py',
           'research/corner_repair.py', 'research/embedding_worker.py', 'research/rectangle_barrier.py',
           'research/neutral_repair.py'}


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


def validate_job(job):
    if not isinstance(job, dict) or not isinstance(job.get('id'), str):
        raise ValueError('job needs string id')
    if not job['id'] or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in job['id']):
        raise ValueError('job id must be lowercase ASCII letters/digits/hyphens')
    if job.get('script') not in ALLOWED:
        raise ValueError('script is not an approved experiment entry point')
    seconds = job.get('seconds')
    if type(seconds) is not int or not 1 <= seconds <= 900:
        raise ValueError('job duration must be an integer from 1 through 900 seconds')
    args = job.get('args')
    if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        raise ValueError('args must be a string array')
    if '--seconds' in args:
        raise ValueError('supervisor supplies the time limit')
    if not job.get('hypothesis'):
        raise ValueError('record a research purpose before running a job')
    return job


def terminate(child):
    if child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=3)


def rss_kib(pids):
    if not pids:
        return 0
    result = subprocess.run(['ps', '-o', 'rss=', '-p', ','.join(map(str, pids))],
                            capture_output=True, text=True, check=False)
    if result.returncode not in (0,1):
        raise RuntimeError('Cannot enforce memory limit: ps failed: '+result.stderr)
    if result.returncode == 1:
        for pid in pids:
            try:
                os.kill(pid,0)
            except ProcessLookupError:
                continue
            raise RuntimeError('Cannot enforce memory limit: live child absent from ps')
    values=result.stdout.split()
    if any(not value.isdigit() for value in values):
        raise RuntimeError('Cannot parse memory accounting')
    return sum(map(int,values))


def supervise(queue_path, max_workers=3, poll_seconds=2):
    if not 1 <= max_workers <= 3:
        raise ValueError('at most three workers')
    state = json.loads((ROOT/'research/state.json').read_text())
    if state.get('status') == 'paused_by_user':
        raise RuntimeError('Research paused by human; explicit human resume is required')
    deadline = dt.datetime.fromisoformat(state['deadline'].replace('Z', '+00:00'))
    records = ROOT/'data/experiments'
    records.mkdir(parents=True, exist_ok=True)
    used_before = float(state.get('initial_research_compute_seconds_reserved', 300))
    limit = float(state.get('compute_seconds_limit', 21600))
    completed = {p.stem: json.loads(p.read_text()) for p in records.glob('*.json')}
    for receipt in completed.values():
        if receipt.get('status') == 'reserved_before_spawn':
            raise RuntimeError('Unresolved launch reservation; reconcile before starting any new worker')
        if receipt.get('status') == 'running_reserved' and receipt.get('pid'):
            try:
                os.kill(receipt['pid'],0)
            except ProcessLookupError:
                continue
            raise RuntimeError('A worker from an earlier supervisor may still be alive; reconcile before relaunch')
    spent = used_before + sum(r['elapsed_seconds'] for r in completed.values())
    running = {}
    stop_requested = False

    def stop(signum, frame):
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    status_path = ROOT/'data/runner-status.json'
    try:
        while True:
            now = time.monotonic()
            reason = None
            if stop_requested:
                reason = 'stop_requested'
            elif utcnow() >= deadline-dt.timedelta(seconds=30):
                reason = 'pilot_deadline'
            elif spent + sum(now-r['started'] for r in running.values()) >= limit-60:
                reason = 'compute_budget'
            elif rss_kib([r['child'].pid for r in running.values()]) > 256*1024:
                reason = 'aggregate_rss_limit_256MiB'
            for job_id, record in list(running.items()):
                child = record['child']
                elapsed = now-record['started']
                job_reason = reason
                if elapsed > record['job']['seconds']+30:
                    job_reason = 'hard_timeout_including_overhead'
                if job_reason:
                    terminate(child)
                code = child.poll()
                if code is None:
                    continue
                record['log'].close()
                receipt = {'job':record['job'], 'argv':record['argv'], 'pid':child.pid,
                           'started_at':record['started_at'], 'finished_at':utcnow().isoformat(),
                           'elapsed_seconds':time.monotonic()-record['started'], 'exit_code':code,
                           'status':job_reason or ('completed' if code == 0 else 'failed'),
                           'entrypoint_sha256':record['hash'],
                           'log':str(record['log_path'].relative_to(ROOT)),
                           'note':'A completed process is not a mathematical success. Inspect its exact evidence.'}
                save(records/(job_id+'.json'), receipt)
                completed[job_id] = receipt
                spent += receipt['elapsed_seconds']
                del running[job_id]
            if reason:
                save(status_path, {'status':reason, 'pid':os.getpid(), 'active':[],
                                   'compute_seconds_accounted':spent, 'updated_at':utcnow().isoformat()})
                return
            manifest = json.loads(queue_path.read_text())
            active_limit = manifest.get('max_concurrent', max_workers)
            if type(active_limit) is not int or not 1 <= active_limit <= max_workers:
                raise ValueError('max_concurrent must be between one and the pool worker limit')
            jobs = [validate_job(job) for job in manifest['jobs']]
            ids = [job['id'] for job in jobs]
            if len(ids) != len(set(ids)):
                raise ValueError('duplicate job ids')
            for job in jobs:
                if job['id'] in completed and completed[job['id']].get('job') != job:
                    raise ValueError('Completed job identity changed; use a new id for a new experiment')
            available = limit-spent-60-sum(r['job']['seconds']+30 for r in running.values())
            for job in jobs:
                if len(running) >= active_limit:
                    break
                if job['id'] in completed or job['id'] in running:
                    continue
                if job['seconds']+30 > available or (deadline-utcnow()).total_seconds() < job['seconds']+30:
                    continue
                program = ROOT/job['script']
                argv = [sys.executable, str(program), *job['args'], '--seconds', str(job['seconds'])]
                log_path = ROOT/'data/run-logs'/(job['id']+'.log')
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log = log_path.open('a')
                env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONUNBUFFERED='1')
                source_hash=hashlib.sha256(program.read_bytes()).hexdigest()
                started=time.monotonic(); started_at=utcnow().isoformat()
                reservation={'job':job,'argv':argv,'status':'reserved_before_spawn',
                             'elapsed_seconds':job['seconds']+30,'entrypoint_sha256':source_hash,
                             'started_at':started_at,'note':'Conservative time reservation until completion receipt replaces it.'}
                save(records/(job['id']+'.json'),reservation)
                try:
                    child = subprocess.Popen(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                             env=env, start_new_session=True)
                except BaseException:
                    log.close()
                    save(records/(job['id']+'.json'),dict(reservation,status='failed_to_start',elapsed_seconds=0))
                    raise
                running[job['id']] = {'child':child,'job':job,'argv':argv,'log':log,'log_path':log_path,
                                      'started':started,'started_at':started_at,'hash':source_hash}
                save(records/(job['id']+'.json'),dict(reservation,status='running_reserved',pid=child.pid))
                available -= job['seconds']+30
            save(status_path, {'status':'running' if running else 'queue_exhausted_or_budget_reserved',
                               'pid':os.getpid(), 'compute_seconds_accounted':spent,
                               'compute_seconds_limit':limit,'updated_at':utcnow().isoformat(),
                               'active':[{'id':key,'pid':r['child'].pid,'script':r['job']['script'],
                                          'seconds_requested':r['job']['seconds'],
                                          'elapsed_seconds':time.monotonic()-r['started']} for key,r in running.items()],
                               'completed_job_count':len(completed)})
            if not running:
                return
            time.sleep(poll_seconds)
    finally:
        for job_id, record in running.items():
            terminate(record['child'])
            record['log'].close()
            receipt = {'job':record['job'],'argv':record['argv'],'pid':record['child'].pid,
                       'started_at':record['started_at'],'finished_at':utcnow().isoformat(),
                       'elapsed_seconds':time.monotonic()-record['started'],
                       'exit_code':record['child'].returncode,'status':'supervisor_exception_or_exit',
                       'entrypoint_sha256':record['hash'],
                       'log':str(record['log_path'].relative_to(ROOT)),
                       'note':'Terminated without a normal completion; no mathematical conclusion.'}
            save(records/(job_id+'.json'), receipt)
            spent += receipt['elapsed_seconds']
        if running:
            save(status_path, {'status':'supervisor_exception_or_exit','pid':os.getpid(),
                               'active':[],'compute_seconds_accounted':spent,
                               'updated_at':utcnow().isoformat()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--max-workers', type=int, default=3)
    args = parser.parse_args()
    with (ROOT/'.run-lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another experiment pool owns the lock.', file=sys.stderr)
            return 2
        supervise(args.queue.resolve(), args.max_workers)
    return 0


if __name__ == '__main__':
    sys.exit(main())
