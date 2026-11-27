# Separate owned-process cleanup guard

Status: implementation checkpoint, independent review pending; no production or
numerical adapter integration. Historical guards and encoders are unchanged.
Model setting: `gpt-6.1-sol`, reasoning `high`.

`research/owned_process_guard.py` offers:

- `OwnedProcessTracker(pid)`: instantiate immediately after a
  `Popen(..., start_new_session=True)` launch. Retain this instance across monitor
  samples and cleanup so observed descendant and ownership violations persist.
- `tracker.inspect(process, process_snapshot(timeout))`: obtains sampled parent
  plus owned native RSS, verified groups, live/member PID sets and violations.
  `SnapshotRace` requires a new full snapshot and cannot establish emptiness.
- `cleanup_owned_process(process, tracker=None, *, timeout=1.0, max_samples=40)`:
  bounded cleanup returning `cleanup_status` (`clean`/`error`), `cleanup_error`,
  `cleanup_samples`, `cleanup_elapsed_seconds`, and `peak_sampled_rss_kib`.
- `guarded_process(command, seconds, rss_mib, log_path, *, cancelled=None)`:
  compatible basic guard result keys, plus cleanup diagnostics and
  `trigger_gate_status` (pre-cleanup failure, if any). Limits remain at most 30
  seconds and 256 MiB. No cap changes or automatic retries occur.

A full fresh `ps pid,ppid,pgid,rss,stat` snapshot is checked for complete row
shape, unique positive PIDs, valid group/RSS values and guard positive RSS.
Live owned rows require positive RSS. Zero-RSS zombies are tracked as nonempty;
they require bounded disappearance after root reaping. `ps sess` is omitted:
macOS can print zero despite `os.getsid` returning the actual session ID.

The direct worker must retain the guard as parent and its spawned PID as PGID
and SID. Original group membership catches ordinary reparented descendants even
when the root has exited. Observed descendant closure persists across samples.
Every candidate is checked with fresh `os.getsid`/`os.getpgid` before it can
authorize a group signal. The guard's own group is excluded. Observed workers
leaving their original group fail closed; an observed secondary group can be
removed best effort only while fresh identity proves it belongs to the spawned
session. Foreign sessions are never signaled.

Cleanup polls/reaps the direct child and skips `killpg` only after a fresh full
snapshot proves the root exited and no owned/observed members remain. A live
verified group receives SIGKILL followed by fresh verification. If `killpg`
raises EPERM, only a new empty snapshot with a reaped root excuses the exit
race. Fresh evidence of remaining members latches the failure even if later
best effort cleanup succeeds. ESRCH requires another full snapshot; it does not
prove emptiness. Monitor or identity errors latch failure while bounded fresh
retries permit safe best effort cleanup. No unconditional `wait()` can hang. A cleanup error can mean a live process
could not be removed (for example, persistently denied monitor or signal
access); failure never guarantees reaping or absence of descendants.

The final guard gate includes cleanup elapsed time and its sampled RSS peak.
Cleanup failure overrides a prior gate, retained in `trigger_gate_status`.
Completion requires an ordinary monitor sample as before. The caller owns
signal handling: `cancelled` supports a SIGTERM flag, while a raised
`BaseException` triggers cleanup then propagates. SIGKILL cannot unwind Python.

This is a restricted fixed-worker contract. Workers and all descendants must
retain the spawned session and group. A sampled monitor cannot guarantee
capture of an unobserved descendant that detaches between samples. PID identity
checks reduce stale PID/group risk but do not provide a kernel atomic
identity-and-signal primitive. Sampled RSS includes native allocations, excludes
the transient `ps` helper, and can overshoot between samples.

Validation: 30 deterministic mock tests pass, covering live EPERM, the verified
empty exit race, ESRCH refresh, malformed/denied monitor, bounded cleanup,
zombies, ownership violations, descendants, own-group exclusion, cancellation,
launch failure, cleanup wall/RSS accounting, and preservation of monitor peak.
No host guard trial has run in this worker sandbox. Four optional tiny host
checks are prepared in `tests/test_owned_process_guard_host.py`; the supervising
agent must review first, then explicitly opt in with
`OWNED_GUARD_HOST_TESTS=1`. They use only sleeping Python processes and one
same-group descendant, never numerical models or solvers.
