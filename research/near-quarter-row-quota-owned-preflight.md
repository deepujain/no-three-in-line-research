# Row-quota build preflight with owned-process cleanup

Status: separate adapter implemented; independent adapter review and tiny host
CLI gate pending. The helper already passed independent review and four
supervisor-run tiny actual-host checks. No n79 build was run by this worker.
Model setting: `gpt-6.1-sol`, reasoning `high`.

`research/near_quarter_row_quota_owned_preflight.py` preserves the reviewed
row-quota worker's exact model header, clause stream, native Glucose3 build,
progress counters, parent/deadline checks, and never-solve behavior. It changes
the guard import to `research/owned_process_guard.py` and uses a cancellation
flag predicate so SIGTERM/SIGINT do not interrupt bounded cleanup. Historical
encoders, preflights and guards are unchanged.

The adapter binds ten current source hashes: original model, line generator,
verifier, compact model, row-quota model, owned-process guard, historical guard
utilities (`atomic` and `sha`), historical row-quota preflight, this adapter,
and shared CLI entrypoint. The child checks bindings before import and after
construction; the parent checks again before accepting completion. A cleanup,
monitor, memory, wall, launch, cancellation, worker, or binding failure clears
completion and the accepted full model hash while retaining published counters.

The optional CLI route is:

```sh
.venv/bin/python src/lazy_sat.py --near-quarter-row-quota-owned-preflight \
  --n 3 --mode build --seconds 5 --rss-mib 256 \
  --output data/near-quarter-row-quota-owned-preflight-n3.json
```

The only mode is `build`, with unchanged maximum 30 seconds and 256 MiB. Native
RSS is sampled for the guard parent plus spawned group/observed descendants;
cleanup time and peak RSS count toward guard gates. It is a sampled kill gate,
not a kernel memory cap. The fixed worker retains its spawned SID and PGID.
Cleanup failure may leave live processes and is never accepted as completion.
The detailed ownership, race, and sampling limits are documented in
`research/owned-process-guard.md`.

Validation before host gate: nine tests pass, one explicit host test skips.
Tests build n3/n5 formulas natively without solving, check independent formula
hash/count reconstruction, source-change rejection, child deadline/parent loss,
all guard failures overriding completed state, cancellation predicate behavior,
and CLI dispatch with invalid mode rejection. The shared dispatcher preserves
both diagonal routes and every historical near-quarter route.

After independent review, the supervisor can explicitly run the tiny actual
CLI n3/n5 gate with:

```sh
OWNED_ROW_PREFLIGHT_HOST_TESTS=1 .venv/bin/python -m unittest \
  tests.test_near_quarter_row_quota_owned_preflight -v
```

Any later n79 run belongs to the supervisor and needs the approved source
bindings. This adapter adds no automatic numerical retries or cap changes.
