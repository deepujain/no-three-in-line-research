"""One-shot Glucose3 child and same-session bounded native supervision.

No group signals: solver/checker inherit the worker's process group. Sampled
ancestry cannot prove the absence of an unseen detached fork; the unchanged
outer owned-session guard is authoritative for that limitation.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time

STREAM_CAP = 65536
PROOF_CAP = 8*1024*1024
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUNTIME_MANIFEST = ROOT/'data/fixed-pool-boolean-scaffold-runtime-pins.json'
RUNTIME_SHA256 = '1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a'


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(65536): h.update(block)
    return h.hexdigest()


def verify_pins(pins):
    if not pins: raise ValueError('missing runtime/source pins')
    for path, expected in pins.items():
        if digest(path) != expected: raise ValueError('pin changed: '+str(path))


def runtime_contract(path=RUNTIME_MANIFEST, *, inspect_imports=False):
    if digest(path) != RUNTIME_SHA256: raise ValueError('unreviewed runtime manifest')
    runtime = json.loads(Path(path).read_text()); verify_pins(runtime['pins'])
    if (runtime['backend'] != 'PySAT Glucose3 1.8.dev24'
            or runtime['interpreter'] != sys.executable
            or runtime['resolved_interpreter'] != str(Path(sys.executable).resolve())):
        raise ValueError('runtime interpreter/backend mismatch')
    import importlib.util
    for name in runtime['optional_imports_absent']:
        if name in sys.modules or importlib.util.find_spec(name) is not None:
            raise ValueError('unexpected optional backend import: '+name)
    if inspect_imports:
        import importlib.metadata
        import pysat
        import pysat.solvers
        import pysolvers
        dist = Path(importlib.metadata.distribution('python-sat')._path)
        paths = [Path(pysolvers.__file__), dist/'METADATA', dist/'licenses/LICENSE.txt']
        for name, module in tuple(sys.modules.items()):
            if name == 'pysat' or name.startswith('pysat.'):
                origin = getattr(module, '__file__', None)
                if origin is None: raise ValueError('native package module lacks source origin')
                paths.append(Path(origin))
        if pysat.__version__ != '1.8.dev24' or any(str(p) not in runtime['pins'] for p in paths):
            raise ValueError('native import origin/version mismatch')
        verify_pins(runtime['pins'])
    return runtime


def snapshot(seconds=.08):
    """Bound even the observer's pipes; lstart distinguishes observed PID reuse."""
    p = subprocess.Popen(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart=,stat='],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buffers = [bytearray(), bytearray()]; sel = selectors.DefaultSelector()
    deadline = time.monotonic()+seconds
    try:
        for i, f in enumerate((p.stdout, p.stderr)):
            os.set_blocking(f.fileno(), False); sel.register(f, selectors.EVENT_READ, i)
        while sel.get_map():
            if time.monotonic() >= deadline: raise TimeoutError('process observer timeout')
            for key, _ in sel.select(min(.005, max(0, deadline-time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), 8192)
                if not chunk: sel.unregister(key.fileobj); continue
                buffers[key.data].extend(chunk)
                if len(buffers[key.data]) >= STREAM_CAP: raise ValueError('process observer output cap')
        p.wait(timeout=max(.001, deadline-time.monotonic()))
        if p.returncode: raise ValueError('process observer failed: '+buffers[1].decode('ascii', 'replace'))
        rows = {}
        for line in buffers[0].decode('ascii').splitlines():
            fields = line.split()
            if len(fields) != 9: raise ValueError('process observer format')
            pid, ppid, pgid = map(int, fields[:3]); born = tuple(fields[3:8]); stat = fields[8]
            if pid != p.pid: rows[pid] = (ppid, pgid, born, stat)
        return rows
    finally:
        if p.poll() is None:
            p.kill()
            try: p.wait(timeout=.02)
            except subprocess.TimeoutExpired: pass
        sel.close(); p.stdout.close(); p.stderr.close()


class Tracker:
    def __init__(self, process, baseline):
        self.process = process; self.parent = os.getpid(); self.group = os.getpgrp(); self.sid = os.getsid(0)
        self.baseline = set(baseline); self.seen = {}; self.errors = []

    def inspect(self, seconds=.08):
        # Bind direct-child identity BEFORE poll can reap and release its PID.
        # An already reaped direct PID is never signalling authority.
        rows = snapshot(seconds)
        candidates = set(self.seen)-{self.process.pid}
        if self.process.returncode is None: candidates.add(self.process.pid)
        while True:
            more = candidates | {pid for pid, row in rows.items() if row[0] in candidates}
            if more == candidates: break
            candidates = more
        live = []
        for pid in candidates:
            if pid not in rows: continue
            row = rows[pid]
            if pid == self.parent or pid in self.baseline:
                self.errors.append('candidate overlaps preexisting process'); continue
            if pid in self.seen and row[2] != self.seen[pid]:
                self.errors.append('observed PID identity changed'); continue
            self.seen[pid] = row[2]
            try: valid = os.getpgid(pid) == row[1] == self.group and os.getsid(pid) == self.sid
            except ProcessLookupError: continue
            if not valid: self.errors.append('native descendant left inherited group/session'); continue
            live.append((pid, row[3].startswith('Z')))
        # A newly orphaned group member without observed ancestry is uncertain,
        # never authority to kill an unrelated process.
        unknown = [pid for pid, row in rows.items() if row[1] == self.group
                   and pid not in self.baseline and pid not in candidates and pid != self.parent]
        if unknown: self.errors.append('unattributed new process in worker group')
        if self.process.returncode is None and self.process.pid not in rows:
            if self.process.poll() is None: raise RuntimeError('live direct child absent from process snapshot')
        return live

    def signal(self, sig, seconds):
        for pid, zombie in self.inspect(seconds):
            if not zombie:
                try: os.kill(pid, sig)
                except ProcessLookupError: pass


def cleanup(process, tracker):
    start = time.monotonic(); end = start+.5; term_end = start+.1
    try:
        while time.monotonic() < end:
            left = end-time.monotonic()
            live = tracker.inspect(min(.04, left))
            if not live and process.poll() is not None:
                return {'clean': not tracker.errors, 'errors': sorted(set(tracker.errors)),
                        'seconds': time.monotonic()-start, 'observed_pids': sorted(tracker.seen)}
            sig = signal.SIGTERM if time.monotonic() < term_end else signal.SIGKILL
            # Every signal follows a fresh identity/ancestry inspection above.
            for pid, zombie in live:
                if not zombie:
                    try: os.kill(pid, sig)
                    except ProcessLookupError: pass
            process.poll(); time.sleep(min(.005, max(0, end-time.monotonic())))
    except Exception as error:
        tracker.errors.append(f'{type(error).__name__}: {error}')
    # A fresh direct-child identity is still required for best-effort SIGKILL.
    if process.poll() is None:
        try: tracker.signal(signal.SIGKILL, max(.001, min(.02, end-time.monotonic())))
        except Exception: pass
        process.poll()
    return {'clean': False, 'errors': sorted(set(tracker.errors+['cleanup not verified within 0.5 seconds'])),
            'seconds': time.monotonic()-start, 'observed_pids': sorted(tracker.seen)}


def run_child(command, seconds, pins, *, latest_end=None):
    if not math.isfinite(seconds) or not 0 < seconds <= 10: raise ValueError('native time slice')
    verify_pins(pins); baseline = snapshot()
    started = time.monotonic()
    if latest_end is not None: seconds = min(seconds, latest_end-started)
    if seconds <= 0: raise TimeoutError('no native slice after launch preparation')
    deadline = started+seconds
    p = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=ROOT)  # Deliberately no new session or process group.
    tracker = Tracker(p, baseline); buffers = [bytearray(), bytearray()]; reason = 'exited'
    sel = selectors.DefaultSelector(); failure = None; observer_deadline = False; observer_error = None
    try:
        for i, f in enumerate((p.stdout, p.stderr)):
            os.set_blocking(f.fileno(), False); sel.register(f, selectors.EVENT_READ, i)
        while True:
            if time.monotonic() >= deadline: reason = 'timeout'; break
            remaining = deadline-time.monotonic()
            observer_deadline = remaining <= .04
            tracker.inspect(min(.04, max(.001, remaining)))
            if tracker.errors: reason = 'lifecycle_error'; break
            for key, _ in sel.select(min(.01, max(0, deadline-time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), 8192)
                if not chunk: sel.unregister(key.fileobj); continue
                remaining = STREAM_CAP-len(buffers[key.data])
                buffers[key.data].extend(chunk[:remaining])
                if len(chunk) >= remaining:
                    reason = 'stdout_cap' if key.data == 0 else 'stderr_cap'; break
            if reason != 'exited': break
            if not sel.get_map() and p.poll() is not None: break
    except BaseException as error:
        if isinstance(error, TimeoutError) and observer_deadline and time.monotonic() >= deadline:
            reason = 'timeout'; observer_error = str(error)
        else:
            reason = 'supervisor_error'; failure = error
    finally:
        result_cleanup = cleanup(p, tracker)
        sel.close(); p.stdout.close(); p.stderr.close()
    verify_pins(pins)
    result = {'reason': reason, 'returncode': p.poll(), 'cleanup': result_cleanup,
              'elapsed_seconds': time.monotonic()-started,
              'stdout': buffers[0].decode('ascii', 'strict'), 'stderr': buffers[1].decode('ascii', 'strict')}
    if observer_error is not None: result['observer_timeout_at_child_deadline'] = observer_error
    if failure is not None:
        if not isinstance(failure, Exception): raise failure
        result['error'] = f'{type(failure).__name__}: {failure}'
    return result


def solver_child(cnf, proof, expected):
    # Applies to the native trace tempfile, output file, and inherited forks.
    resource.setrlimit(resource.RLIMIT_FSIZE, (PROOF_CAP, PROOF_CAP))
    runtime_contract(inspect_imports=True)
    from research.bounded_rup_checker import Budget, load_cnf
    from pysat.solvers import Glucose3
    # Strict input is independently parsed. Keeping the DB in the child avoids
    # a Python clause list in the worker; native/interpreter RSS is outer-guarded.
    variables, database, actual, _ = load_cnf(cnf, Budget(seconds=10))
    if actual != expected: raise ValueError('solver CNF digest mismatch')
    with Glucose3(with_proof=True) as solver:
        for clause, multiplicity in database.items():
            for _ in range(multiplicity): solver.add_clause(list(clause))
        answer = solver.solve()  # Exactly one native solve call.
        if answer is True:
            model = solver.get_model()
            if (model is None or len(model) != variables or len({abs(v) for v in model}) != variables
                    or any(not 0 < abs(v) <= variables for v in model)):
                raise ValueError('native incomplete model')
            text = ' '.join(map(str, model))
            if len(text.encode('ascii')) > 32768: raise ValueError('native model cap')
            return {'answer': 'SAT', 'cnf_sha256': actual, 'model': text,
                    'pid': os.getpid(), 'pgid': os.getpgrp(), 'sid': os.getsid(0)}
        if answer is not False: raise ValueError('native returned unknown, not UNSAT')
        solver.prfile.flush()
        size = os.fstat(solver.prfile.fileno()).st_size
        if size >= PROOF_CAP: raise ValueError('native proof cap reached')
        solver.prfile.seek(0); total = 0
        with Path(proof).open('xb') as target:
            while block := solver.prfile.read(65536):
                total += len(block)
                if total >= PROOF_CAP: raise ValueError('proof cap reached')
                target.write(block)
            target.flush(); os.fsync(target.fileno())
        if total != size: raise ValueError('proof size changed')
        return {'answer': 'UNSAT', 'cnf_sha256': actual, 'proof_sha256': digest(proof),
                'proof_bytes': total, 'pid': os.getpid(), 'pgid': os.getpgrp(), 'sid': os.getsid(0)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cnf', type=Path, required=True); p.add_argument('--proof', type=Path, required=True)
    p.add_argument('--cnf-sha256', required=True); a = p.parse_args()
    try: result = solver_child(a.cnf, a.proof, a.cnf_sha256)
    except Exception as error:
        print(json.dumps({'answer': 'ERROR', 'error': f'{type(error).__name__}: {error}'})); return 2
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == '__main__': sys.exit(main())
