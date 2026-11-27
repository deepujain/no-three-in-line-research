# Guarded solve of the compact near-quarter family

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. The separate wrapper is `research/near_quarter_compact_solve.py`, exposed by `src/lazy_sat.py --near-quarter-compact-solve`. The original model, compact encoder, host guard and both build-only preflights remain frozen. No n79 build or search was executed by the author. The exact orbit DFS described in `research/near-quarter-next-literature.md` remains a fallback proposal; its implementation was deferred when root's compact n79 construction succeeded.

## Scope and resource gate

This searches only the approved near-quarter-turn family at target `2*n`: exactly `n//2` off-diagonal four-orbits, exactly one main-diagonal half-turn pair and an empty anti-diagonal. It does not search target 157 or unrestricted configurations. A native false answer is reported as `restricted_family_unsat_solver_reported`, with `proof_checked=false`; it is not an independently checked infeasibility proof.

The wrapper reuses the exact frozen sampled host guard. RSS may not exceed the configured ceiling of at most 256 MiB; the guard sums its parent plus worker process group/observed descendants, including native solver allocations, and kills the worker group on a limit or monitor failure. Missing/malformed/invalid required process rows fail closed. The transient `ps` helper is excluded. Sampling and scheduling allow overshoot; this is not a kernel peak-allocation ceiling.

The maximum allocation is 120 seconds, including CNF construction, solve, decoding, both geometric checks and witness persistence. A child deadline starts before worker launch, and the original host guard independently enforces the total time. During construction, the child checks the deadline between yielded clauses. Only after complete CNF exhaustion and source/hash checks does it call `solve_limited(expect_interrupt=True)` with a native interrupt timer for the remaining time. The timer is cancelled and joined before any native solver deletion. A timer-boundary result is conservatively incomplete, even if the native answer is false.

The compact n79 build report measured only 4.265625 MiB remaining sampled headroom below the cap. Solving may learn more clauses. PySAT `get_model()` materializes the entire auxiliary assignment, which can itself exceed that remaining headroom. The wrapper avoids a second full-model copy and deletes the native solver immediately after obtaining a SAT assignment, before allocating verification state. This does not guarantee that obtaining the assignment fits. The same cap applies throughout; no increase or memory-fit claim is made.

## Terminal result and witness rules

The complete CNF model hash uses the same deterministic family/header/ordered-clause format as the frozen compact preflight. No separate line-count pass is repeated. `--expected-model-sha256` can bind construction to a previously measured complete formula; a mismatch stops before any solve call.

Native results are checked by identity: true, false and None are distinct, and integer zero is not accepted as false. None, interruption, deadline/resource failure and unexpected results are incomplete. Solver search begins only after the entire model is constructed. Reports preserve observed clause/variable lower bounds and a prefix hash, separating them from final completion.

For SAT, every real orbit variable must have one assignment with no duplicate or contradictory real literal. All literals must be integers in the emitted variable range. The selected IDs must contain exactly `n//2` four-orbits and one diagonal pair. Expanding those IDs fixes the actual family geometry, which must then pass both independent exact verifiers and target-size checks. Their shared source file, `src/verify.py`, is part of the immutable source binding.

Only then is the full certificate serialized as a deterministic, content-hashed witness file. Its bytes are written and fsynced to a temporary file, linked atomically without replacing any existing witness, and the destination directory is fsynced. An existing same-name file must match the verified bytes exactly. The saved witness path/hash are checkpointed before terminal success is published. Reports include source identities, selected IDs and both checker results in the witness payload.

The parent rechecks all source hashes and the saved witness file hash. Host kill, source change or host error clears every affirmative terminal conclusion, solver result, completion flag and accepted witness reference. `worker_observed_witness_file` can retain a path for a separate audit: a correctly persisted certificate may survive a later failed run, while the run itself remains incomplete.

## Cancellation and source binding

A separate SIGTERM/SIGINT context in this wrapper raises through the original guard so its process-group cleanup runs. The frozen guard is not patched. A private guard-alive marker and parent-PID binding prevent a delayed child from starting construction after startup cancellation; construction heartbeats also check both. The marker is removed whenever the guarded launch returns or raises. A tiny actual-process test sends SIGTERM after child startup and confirms the sleeping child is reaped.

SIGKILL is uncatchable. Killing only the guard parent can leave a child until its own checks/native deadline act, and the absent parent cannot monitor RSS. This wrapper makes no general SIGKILL cancellation guarantee. The pool must preserve its ordinary process-tree supervision. The worker creates no subprocesses and does not change its original session/group.

Six source hashes are captured before spawn, checked by the child before imports/after construction/after solve/after validation/before terminal reporting, and rechecked by the parent: original model, line generator, compact encoder, original host guard, both-verifier source file and this wrapper (including its witness helper). They identify local sources, not the interpreter or native solver binary. The supervisor separately records the updated CLI entrypoint hash.

## Tiny verification and eventual command

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_compact_solve.py -v
.venv/bin/python src/lazy_sat.py --near-quarter-compact-solve \
  --n 3 --seconds 5 --rss-mib 256 \
  --output data/near-quarter-compact-solve-n3.json
```

Thirteen tiny tests were prepared: twelve pass here and the actual-host subprocess test skips because this sandbox denies `ps`. Tests include actual n3 SAT and n5 restricted-family UNSAT, exact build-only model-hash agreement, malformed real assignments, None/zero distinction, forced interruption, timer join ordering, incomplete streams and expected-hash rejection before solve, source mutation after solve, immutable witness collision/reuse, witness-before-result publication, parent failure overriding child success, startup deadline/parent-loss checks, actual SIGTERM child cleanup, and opt-in CLI forwarding. A parent/child n3 run mocks only RSS; real host measurements remain a separate check.

For a separately approved/scheduled first n79 allocation, root can use the known complete model identity without increasing either cap:

```sh
.venv/bin/python src/lazy_sat.py --near-quarter-compact-solve \
  --n 79 --seconds 120 --rss-mib 256 \
  --expected-model-sha256 909f510443e97c8b909e783115df53f6360f87b18dbce471794ffdf09bb4c2f6 \
  --output data/near-quarter-compact-solve-n79.json
```

Independent wrapper source review, real-host tiny checks and a free numerical lane are required before that allocation. Neither this document nor the prepared command starts it.

| Frozen artifact | SHA-256 |
|---|---|
| `research/near_quarter_compact_solve.py` | `6eac77e957bb47f69118c3f70f5530c7d4bed84621f7309359b6f466c96f1ef5` |
| `tests/test_near_quarter_compact_solve.py` | `9b692d222a9cdd1df246cfd2d49d3554ee6ab35682bc3c0eaad03787372c579e` |
| `src/lazy_sat.py` adapter | `26a129e71be745510ac951291546f7262fc1590ba6b26a677e9fa77c5de6e005` |
| Unchanged `src/verify.py` | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |
| Unchanged `src/near_quarter_compact.py` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| Unchanged `research/near_quarter_preflight.py` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
