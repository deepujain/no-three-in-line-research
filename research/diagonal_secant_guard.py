"""Externally guarded diagonal DFS; sampled RSS is not a kernel memory cap."""
import time
MODULE_STARTED = time.monotonic()
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.near_quarter_preflight import process_rss_kib

SOURCES = {'core': ROOT/'research/diagonal_secant_dfs.py',
           'verifier': ROOT/'src/verify.py', 'guard': Path(__file__).resolve(),
           'rss_monitor': ROOT/'research/near_quarter_preflight.py',
           'entrypoint': ROOT/'src/lazy_sat.py'}


def hashes():
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in SOURCES.items()}


def atomic(path, value):
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.'+path.name+'.', delete=False) as f:
        temp = f.name
        try:
            json.dump(value, f, sort_keys=True)
            f.write('\n')
            f.flush()
        except BaseException:
            os.unlink(temp)
            raise
    try:
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def worker(job):
    if hashes() != job['source_hashes']:
        raise ValueError('source changed before import')
    from research.diagonal_secant_dfs import search
    def save(cert):
        if hashes() != job['source_hashes']:
            raise ValueError('source changed before witness publication')
        cert['metadata']['source_hashes'] = job['source_hashes']
        path = Path(job['witness_dir'])/(cert['metadata']['normalized_sha256']+'.json')
        atomic(path, cert)
    result = search(job['n'], job['seconds'], job['max_nodes'], deficits=job['deficits'],
                    diagonals=job['diagonals'], on_witness=save)
    if hashes() != job['source_hashes']:
        raise ValueError('source changed during search')
    atomic(job['state'], result)


def run(n, seconds, rss_mib, max_nodes, output, deficits=None, diagonals=None, started=None):
    started = time.monotonic() if started is None else started
    if type(n) is not int or n < 2: raise ValueError('n must be >= 2')
    if not math.isfinite(seconds) or not 0 < seconds <= 30: raise ValueError('seconds must be in (0,30]')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256: raise ValueError('rss-mib must be in (0,256]')
    if type(max_nodes) is not int or max_nodes < 1: raise ValueError('max-nodes must be positive')
    for indices in (deficits, diagonals):
        if indices is not None and (not indices or len(set(indices)) != len(indices) or
                                    any(type(i) is not int or not 0 <= i < n for i in indices)):
            raise ValueError('invalid slice indices')
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source_hashes = hashes()
    report = {'n':n, 'status':'incomplete', 'complete':False, 'source_hashes':source_hashes,
              'deficits':list(range(n)) if deficits is None else sorted(deficits),
              'diagonal_indices':list(range(n)) if diagonals is None else sorted(diagonals),
              'scope':'Only declared main-diagonal-reflection slices; no unrestricted infeasibility conclusion.',
              'seconds_limit':seconds, 'rss_limit_mib':rss_mib, 'max_nodes':max_nodes}
    interrupted = False
    def handle_term(signum, frame):
        nonlocal interrupted
        interrupted = True
    old_handler = signal.signal(signal.SIGTERM, handle_term)
    process = None
    reason = None
    peak = samples = 0
    error = None
    try:
        with tempfile.TemporaryDirectory(prefix='diagonal-dfs-guard-') as tmp:
            tmp = Path(tmp)
            state = tmp/'state.json'
            witness_dir = Path(tempfile.mkdtemp(prefix=output.name+'.witnesses-', dir=output.parent))
            job = {'n':n, 'seconds':seconds, 'max_nodes':max_nodes, 'deficits':deficits,
                   'diagonals':diagonals, 'state':str(state), 'witness_dir':str(witness_dir),
                   'source_hashes':source_hashes}
            report['witness_dir'] = str(witness_dir)
            atomic(output, report)
            atomic(tmp/'job.json', job)
            with open(tmp/'worker.log', 'wb') as log:
                if interrupted: reason = 'sigterm'
                elif time.monotonic()-started >= seconds: reason = 'wall_limit'
                else:
                    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--_worker', str(tmp/'job.json')],
                                               stdout=log, stderr=log, start_new_session=True)
                try:
                    while process is not None and process.poll() is None:
                        if interrupted: reason = 'sigterm'; break
                        if time.monotonic()-started >= seconds: reason = 'wall_limit'; break
                        try: rss = process_rss_kib(process.pid)
                        except (OSError, ValueError, subprocess.SubprocessError) as exc:
                            reason, error = 'monitor_error', str(exc); break
                        samples += 1
                        peak = max(peak, rss)
                        if rss > rss_mib*1024: reason = 'rss_limit'; break
                        if time.monotonic()-started >= seconds: reason = 'wall_limit'; break
                        time.sleep(min(.025, max(0, seconds-(time.monotonic()-started))))
                    if reason is None and interrupted: reason = 'sigterm'
                    elif reason is None and time.monotonic()-started >= seconds: reason = 'wall_limit'
                    elif reason is None and not samples: reason, error = 'monitor_error', 'worker exited before an RSS sample'
                finally:
                    if process is not None:
                        try: os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                        process.wait()
            if state.exists(): report['worker_result'] = json.loads(state.read_text())
            if process is not None and reason is None and process.returncode != 0: reason = 'worker_error'
            source_stable = hashes() == source_hashes
            if reason is None and not source_stable: reason = 'source_changed'
            if reason is None and interrupted: reason = 'sigterm'
            elif reason is None and time.monotonic()-started >= seconds: reason = 'wall_limit'
            if reason is None:
                status = report.get('worker_result', {}).get('status', 'worker_incomplete')
                report['status'] = status
                report['complete'] = status == 'all_declared_slices_exhausted'
            else: report['status'] = reason
            report['guard'] = {'peak_sampled_rss_kib':peak, 'samples':samples,
                'returncode':None if process is None else process.returncode, 'error':error,
                'source_stable':source_stable,
                'rss_scope':'parent plus worker process group and descendants; transient ps helper excluded',
                'semantics':'sampled gate, possible overshoot; wall limit includes setup'}
            report['worker_log_tail'] = (tmp/'worker.log').read_bytes()[-4096:].decode(errors='replace')
            report['witness_dir'] = str(witness_dir)
            report['elapsed_seconds'] = time.monotonic()-started
            atomic(output, report)
    finally:
        if process is not None and process.poll() is None:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait()
        signal.signal(signal.SIGTERM, old_handler)
    return report


def main(argv=None, started=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == '--_worker':
        worker(json.loads(Path(args[1]).read_text())); return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--rss-mib', type=float, default=256)
    parser.add_argument('--max-nodes', type=int, required=True)
    parser.add_argument('--deficit', type=int, action='append')
    parser.add_argument('--diagonal', type=int, action='append')
    parser.add_argument('--output', type=Path, required=True)
    parsed = parser.parse_args(args)
    try:
        report = run(parsed.n, parsed.seconds, parsed.rss_mib, parsed.max_nodes, parsed.output,
                     parsed.deficit, parsed.diagonal, started=MODULE_STARTED if started is None else started)
    except (ValueError, OSError) as exc: parser.error(str(exc))
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__': sys.exit(main())
