# Bounded row-quota solve with owned-process cleanup

Status: separate implementation independently approved for the supervisor's tiny
actual-host n3/n5 gate. No n79 solve was run by this worker. Model setting:
`gpt-6.1-sol`, reasoning `high`.

The separate `research/near_quarter_row_quota_owned_solve.py` keeps all historical
solvers, encoders, preflights and the reviewed owned-process helper unchanged.
The first solve cap/default is **30 seconds including construction**, with the
same maximum **256 MiB sampled native RSS**. The supervisor chose a shorter
first trial within the previously discussed 120-second ceiling, so this uses
the reviewed helper directly without extending its limit or duplicating its
monitor loop. There is no automatic retry or cap increase.

## Formula identity and resource evidence

The supervisor's preceding build-only r23 completed the exact row-quota CNF:
2,072,304 clauses, 475,708 variables, full hash
`397546bb8cbd65a7bb9ebfb1c22d14e41dc1a4092e25d310a00bdaeff7344b3d`.
The reported 12.77565 seconds, 223,712 KiB sampled peak (218.46875 MiB),
311 ordinary samples, and clean 0.0119-second cleanup describe construction
only. That leaves 37.53125 MiB of measured headroom; it does not establish that
native solve allocations or SAT-model materialization fit the same cap.

The new solver requires an expected full hash, uses the exact reviewed row
header and clause stream, and inserts every clause before any solver call.
Missing, malformed, mismatched or partial formulas cannot reach search. It
omits the build-only preflight's separate line-group census; its own measured
construction time must be read from its report. An accepted complete digest
must still equal the observed build-only digest.

Eleven source bindings cover the original model, line generator, compact and
row-quota models, owned-process helper, historical atomic/hash utilities,
historical compact decoder/witness utilities, approved row-header source,
verifier, this solver wrapper, and shared CLI entrypoint. Bindings are checked
before encoder import, after construction, after solve, before persistence,
before conclusion and by the guarded parent.

## Result and witness gates

Only genuine Python `True` or `False`, with no timer event and before the shared
deadline, can finish a search. `None` is no result; integer zero/one and other
unexpected returns are errors. False means only
`restricted_family_unsat_solver_reported`, with `proof_checked=false`; it is
neither an independent proof nor unrestricted infeasibility.

For True, the reviewed decoder requires every real orbit variable exactly
once, valid integer/range literals, `(n-1)/2` selected four-orbits and exactly
one diagonal pair. The native formula is freed after model extraction and
before geometric verification. The frozen independent integer checkers both
must accept the expanded set of exactly `2*n` points.

The reviewed witness writer fully writes and fsyncs the verified bytes, links
an immutable hash-named destination without replacement, checks existing bytes
on reuse, and fsyncs the directory. It publishes the witness before a terminal
conclusion. The parent hashes the saved file before accepting success. A later
failure clears accepted conclusion/result/model/witness fields while retaining
an observed path for separate re-audit. This does not protect against arbitrary
later external file modification.

The remaining-budget timer is canceled and joined before native destruction
or solver-reference changes. Startup/construction check the parent PID, alive
marker and deadline. SIGTERM/SIGINT set a flag so bounded cleanup is not
interrupted. The unchanged helper includes cleanup in its own final wall/RSS
gates; cleanup failure overrides conclusions. Persistent denied monitoring or
signals can leave a live process, and such a run remains incomplete. As in the
approved preflight, preliminary CLI/import/report setup precedes the helper's
clock; the child deadline is set before worker launch. The `ps` helper is
excluded from sampled RSS, which can overshoot between samples. SIGKILL cannot
be unwound, and fixed workers must retain their spawned session/group.

## Validation and supervisor gate

Eighteen deterministic/tiny-native tests pass; one explicit host case skips.
Coverage includes n3 SAT and n5 scoped UNSAT, expected-hash requirements and
mismatch/partial-stream no-solve, nonboolean and interrupted results, source
changes, malformed/wrong-family/geometrically invalid SAT models, timer/native
free ordering, witness-before-state persistence, immutable byte collision,
parent witness hash refusal, cancellation flags, startup/deadline checks,
cleanup/resource/monitor/launch failures overriding a completed child, and CLI
dispatch. Independent review is in
`research/near-quarter-row-quota-owned-solve-review.md`.

After independent approval the supervisor runs:

```sh
OWNED_ROW_SOLVE_HOST_TESTS=1 .venv/bin/python -m unittest \
  tests.test_near_quarter_row_quota_owned_solve -v
```

The separately scheduled first n79 command must use
`--near-quarter-row-quota-owned-solve --n 79 --seconds 30 --rss-mib 256`
with required `--expected-model-sha256` equal to the complete r23 hash above,
an explicit output path and witness directory. Only the supervisor owns that
run; later results need independent artifact and resource-status inspection.
