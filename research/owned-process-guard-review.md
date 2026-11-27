# Independent owned-process guard review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
The separate helper is approved for its four tiny actual-host gates. Numerical
adapter integration, source binding and caller artifact semantics remain a
separate review. No numerical model, n79 build, search or benchmark was run by
this reviewer. All historical guards and encoders remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| `research/owned_process_guard.py` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |
| `tests/test_owned_process_guard.py` | `3fb42e95cf847b8efa4cc0bb0166b074658e67754c44e16239d50a13217c2995` |
| `tests/test_owned_process_guard_host.py` | `aa10ec7e3bf25789bafe2a950f8a807fee338d33f5fbdcf88d0b1255936973e6` |

The helper addresses the unnecessary unconditional final group signal in the
historical guard. A normal child exit alone cannot establish cleanup: the
new helper requires direct-child reaping plus a fresh validated full process
snapshot containing no remaining original-group or observed descendant member.
Only that evidence permits skipping a signal. It does not turn arbitrary
EPERM into success.

The snapshot checks row shape, numeric values, duplicate PIDs, process states
and positive guard RSS. Owned live rows need positive RSS; zombies remain
nonempty members even with zero RSS. The tracker remembers observed descendants
and persistent violations, discovers reparented original-group members, and
checks current SID/PGID with OS calls. It refuses the guard's own group and
foreign sessions. Changed/disappeared identities force another full snapshot.
Observed group/session deviations invalidate success; a secondary group can
be removed best effort only with fresh proof that it remains in the worker's
spawned session.

Every cleanup signal follows that inspection. After EPERM, only a fresh empty
snapshot with the root reaped resolves the narrow exit race. A subsequent
nonempty inspection latches failure, even if later cleanup succeeds. Denied,
malformed or missing monitoring and identity errors also latch failure. ESRCH
alone never establishes empty membership. Cleanup polls and has bounded
sampling/wait limits, with no unbounded child wait. The guard includes cleanup
elapsed time and sampled RSS in its final resource decision, retains the
pre-cleanup trigger, and rejects late completion after a resource/monitor or
cleanup failure. A successful cleanup sample cannot replace the required
ordinary monitor sample.

The API is deliberately restricted to controlled workers and descendants that
retain the spawned session and group. Sampling cannot capture every unobserved
detached descendant. Separate OS identity calls and signaling are not an atomic
kernel operation. The helper does not guarantee removal on a cleanup error:
persistently denied monitoring or signaling can leave a live process. Such a
report must remain incomplete and must not be described as verified reaping.
RSS is sampled, includes native memory, and may overshoot; the ps helper is
excluded. The caller owns signal handling; an ordinary raised BaseException
unwinds through cleanup, whereas uncatchable SIGKILL does not.

I independently read the implementation and all final tests, then ran the
34-test suite: 30 deterministic tests passed in 0.023 seconds and four opt-in
actual-host tests skipped. Coverage includes normal sampled success and peak
retention, reparented descendants after root exit, cancellation before/after
spawn, launch failure, live EPERM and verified exit race, ESRCH refresh, monitor
denial/recovery, malformed snapshots, foreign/guard-group refusal, persistent
ownership violations, zombies, bounded cleanup and final wall/RSS overrides.
These mocks establish state-machine behavior, not actual host process cleanup.

The reviewed opt-in host tests use sleeping Python children and one same-group
descendant, without importing a model or solver. They check ordinary completion,
wall and RSS termination, and cleanup after the direct parent exits. The lead
owns these host gates. A later numerical wrapper must bind this exact helper,
preserve its final failure semantics, and atomically retain caller diagnostics.
