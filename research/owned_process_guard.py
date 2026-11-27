"""Fail-closed sampled guard for fixed workers retaining their spawned session/group.

Historical guards are deliberately unchanged. This helper is not integrated yet.
A worker and all descendants MUST retain the Popen(start_new_session=True) PGID
and SID. Observed deviations fail closed; unobserved detached descendants cannot
be guaranteed by a sampled monitor. No cached PID alone authorizes a signal.
"""
from dataclasses import dataclass, field
import math
import os
import signal
import subprocess
import time


class SnapshotRace(Exception):
    """A process vanished during inspection; another full snapshot is required."""


@dataclass(frozen=True)
class ProcessRow:
    pid: int
    ppid: int
    pgid: int
    rss: int
    stat: str

    @property
    def zombie(self):
        return self.stat.startswith('Z')


def process_snapshot(timeout=.5):
    """Read a full host snapshot. macOS ps sess is intentionally not used."""
    result = subprocess.run(['ps', '-axo', 'pid=,ppid=,pgid=,rss=,stat='],
                            capture_output=True, text=True, check=True, timeout=timeout)
    rows = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError('malformed process monitor row')
        pid, ppid, pgid, rss = map(int, fields[:4])
        if pid <= 0 or ppid < 0 or pgid <= 0 or rss < 0 or pid in rows:
            raise ValueError('invalid process monitor row')
        stat = fields[4]
        if stat[0] not in 'RSDTtXZWIU?':
            raise ValueError('invalid process state')
        rows[pid] = ProcessRow(pid, ppid, pgid, rss, stat)
    parent = rows.get(os.getpid())
    if parent is None or parent.zombie or parent.rss <= 0:
        raise ValueError('process monitor omitted guard positive RSS')
    return rows


@dataclass
class Inspection:
    rss: int
    groups: set = field(default_factory=set)
    members: set = field(default_factory=set)
    live: set = field(default_factory=set)
    errors: list = field(default_factory=list)


class OwnedProcessTracker:
    """Track observed descendants; prove fresh SID/PGID before group signals."""
    def __init__(self, pid):
        self.pid = pid
        self.guard_pid = os.getpid()
        self.guard_group = os.getpgrp()
        self.observed = {pid}
        self.violations = []
        if pid <= 0 or pid == self.guard_pid or pid == self.guard_group:
            raise ValueError('unsafe spawned group identity')

    def inspect(self, process, rows):
        process.poll()  # Reap the root when possible before considering emptiness.
        parent = rows.get(self.guard_pid)
        if parent is None or parent.zombie or parent.rss <= 0:
            raise ValueError('process monitor omitted guard positive RSS')
        candidates = {p for p, row in rows.items()
                      if row.pgid == self.pid or p in self.observed}
        while True:
            expanded = candidates | {p for p, row in rows.items() if row.ppid in candidates}
            if expanded == candidates:
                break
            candidates = expanded
        self.observed.update(candidates)
        if process.returncode is None and self.pid not in rows:
            raise SnapshotRace('live root absent from fresh snapshot')
        inspection = Inspection(parent.rss, errors=self.violations)
        for pid in sorted(candidates):
            row = rows[pid]
            # A guard row reached through stale/reused ownership must never count
            # as owned, and especially must never authorize a group signal.
            if pid == self.guard_pid or row.pgid == self.guard_group:
                inspection.errors.append(f'candidate {pid} overlaps guard group')
                inspection.members.add(pid)
                continue
            try:
                sid, pgid = os.getsid(pid), os.getpgid(pid)
            except ProcessLookupError as exc:
                raise SnapshotRace(f'candidate {pid} vanished during identity check') from exc
            if pgid != row.pgid:
                raise SnapshotRace(f'candidate {pid} changed group during inspection')
            inspection.members.add(pid)
            if sid != self.pid:
                inspection.errors.append(f'candidate {pid} has foreign session')
                continue
            if row.pgid != self.pid:
                inspection.errors.append(f'candidate {pid} left spawned process group')
            if pid == self.pid and row.ppid != self.guard_pid:
                inspection.errors.append('spawned root has unexpected parent')
            inspection.rss += row.rss
            if not row.zombie:
                if row.rss <= 0:
                    raise ValueError('owned live process lacks positive RSS')
                inspection.live.add(pid)
                inspection.groups.add(pgid)
        return inspection


def cleanup_owned_process(process, tracker=None, *, timeout=1.0, max_samples=40):
    """Bound cleanup; an EPERM is excused only after fresh verified emptiness.

    Returns diagnostics, never treats a monitor/identity error as successful
    cleanup. Every actual signal follows a new complete snapshot and identity
    inspection. An observed ownership violation stays fatal even if safely
    verified groups can subsequently be removed. Caller must include cleanup in
    its wall gate. The timeout bounds waits plus each remaining ps timeout.
    """
    if not math.isfinite(timeout) or timeout <= 0 or type(max_samples) is not int or max_samples < 1:
        raise ValueError('invalid cleanup bounds')
    started = time.monotonic()
    deadline = started + timeout
    errors = []
    pending_permission = None
    samples = peak = 0
    try:
        tracker = tracker or OwnedProcessTracker(process.pid)
        for _ in range(max_samples):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                rows = process_snapshot(min(.5, remaining))
                inspection = tracker.inspect(process, rows)
            except SnapshotRace:
                continue  # ESRCH is not evidence of an empty group.
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                message = f'{type(exc).__name__}: {exc}'
                if message not in errors:
                    errors.append(message)
                time.sleep(min(.025, max(0, deadline-time.monotonic())))
                continue  # Best effort retry, but the monitor failure stays fatal.
            samples += 1
            peak = max(peak, inspection.rss)
            errors.extend(e for e in inspection.errors if e not in errors)
            if not inspection.members and process.poll() is not None:
                # Also resolves the narrow signal/exit EPERM race. Any earlier
                # real monitoring or ownership error remains a failure.
                pending_permission = None
                return {'cleanup_status': 'error' if errors else 'clean',
                        'cleanup_error': '; '.join(errors) or None,
                        'cleanup_samples': samples, 'peak_sampled_rss_kib': peak,
                        'cleanup_elapsed_seconds': time.monotonic()-started}
            if pending_permission is not None:
                # Fresh evidence still shows a group after EPERM: this is a
                # genuine failed cleanup even if a later best effort succeeds.
                errors.append(pending_permission)
                pending_permission = None
            for group in sorted(inspection.groups):
                if group == tracker.guard_group or group <= 0:
                    errors.append('refused unsafe cleanup group')
                    continue
                try:
                    os.killpg(group, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Require a fresh empty snapshot on the next pass.
                except PermissionError as exc:
                    pending_permission = f'PermissionError: {exc}'
                except OSError as exc:
                    errors.append(f'{type(exc).__name__}: {exc}')
            # No unbounded wait(): poll reaps the direct child. Zombie-only
            # groups must disappear in a subsequent snapshot before success.
            process.poll()
            time.sleep(min(.025, max(0, deadline-time.monotonic())))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        errors.append(f'{type(exc).__name__}: {exc}')
    if pending_permission:
        errors.append(pending_permission)
    errors.append('cleanup could not verify reaped root and empty owned group within bounds')
    return {'cleanup_status': 'error', 'cleanup_error': '; '.join(errors),
            'cleanup_samples': samples, 'peak_sampled_rss_kib': peak,
            'cleanup_elapsed_seconds': time.monotonic()-started}


def guarded_process(command, seconds, rss_mib, log_path, *, cancelled=None):
    """Sample guard parent + owned native RSS; cleanup counts toward wall cap.

    ``cancelled`` is an optional caller-owned cancellation predicate. A raised
    BaseException also triggers bounded cleanup and is re-raised. Signal handler
    installation is the caller's responsibility; a SIGKILL cannot be unwound.
    """
    if not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('seconds must be in (0,30]')
    if not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('rss-mib must be in (0,256]')
    started = time.monotonic()
    peak = samples = 0
    reason = error = None
    process = tracker = None
    cleanup = {'cleanup_status': 'not_launched', 'cleanup_error': None,
               'cleanup_samples': 0, 'cleanup_elapsed_seconds': 0}
    with open(log_path, 'wb') as log:
        try:
            if cancelled and cancelled():
                reason = 'cancelled'
            else:
                process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
                tracker = OwnedProcessTracker(process.pid)
            while process is not None and process.poll() is None:
                if cancelled and cancelled():
                    reason = 'cancelled'
                    break
                remaining = seconds-(time.monotonic()-started)
                if remaining <= 0:
                    reason = 'wall_limit'
                    break
                try:
                    inspection = tracker.inspect(process, process_snapshot(min(.5, remaining)))
                    if inspection.errors:
                        raise ValueError('; '.join(inspection.errors))
                except SnapshotRace:
                    continue
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    reason, error = 'monitor_error', f'{type(exc).__name__}: {exc}'
                    break
                if inspection.members:
                    samples += 1
                    peak = max(peak, inspection.rss)
                    if inspection.rss > rss_mib*1024:
                        reason = 'rss_limit'
                        break
                time.sleep(min(.025, max(0, seconds-(time.monotonic()-started))))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            reason, error = 'launch_error' if process is None else 'monitor_error', f'{type(exc).__name__}: {exc}'
        finally:
            if process is not None:
                cleanup = cleanup_owned_process(process, tracker)
                peak = max(peak, cleanup['peak_sampled_rss_kib'])
    trigger = reason
    if cleanup['cleanup_status'] == 'error':
        reason = 'cleanup_error'
    elif reason is None and peak > rss_mib*1024:
        reason = 'rss_limit'
    elif reason is None and time.monotonic()-started >= seconds:
        reason = 'wall_limit'
    elif reason is None and not samples:
        reason, error = 'monitor_error', 'worker exited before any RSS sample'
    if reason is None and cancelled and cancelled():
        reason = 'cancelled'
    return {'gate_status': reason or ('exited' if process.returncode == 0 else 'worker_error'),
            'trigger_gate_status': trigger, 'returncode': None if process is None else process.returncode,
            'elapsed_seconds': time.monotonic()-started,
            'rss_samples': samples, 'monitor_error': error,
            'seconds_limit': seconds, 'rss_limit_mib': rss_mib, **cleanup,
            'peak_sampled_rss_kib': peak,
            'rss_scope': 'guard parent plus spawned process group and observed descendants; native heap included',
            'gate_semantics': 'sampled RSS gate; cleanup included in wall gate; possible sampling overshoot; transient ps excluded'}
