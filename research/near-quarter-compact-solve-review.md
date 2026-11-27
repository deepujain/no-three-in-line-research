# Independent bounded compact search review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, reasoning `high`, 2026-11-27.
The exact frozen wrapper below is approved for a separately scheduled initial
run of at most 120 seconds including construction, under the unchanged
256 MiB sampled guard. The Lead owns scheduling. This reviewer ran only tiny
correctness cases and did not execute n79 search.

## Frozen identities

* `research/near_quarter_compact_solve.py`:
  `6eac77e957bb47f69118c3f70f5530c7d4bed84621f7309359b6f466c96f1ef5`
* `tests/test_near_quarter_compact_solve.py`:
  `9b692d222a9cdd1df246cfd2d49d3554ee6ab35682bc3c0eaad03787372c579e`
* `src/lazy_sat.py`, new opt-in adapter:
  `26a129e71be745510ac951291546f7262fc1590ba6b26a677e9fa77c5de6e005`
* `src/verify.py`, both exact checkers:
  `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c`

The frozen guard, original model, line generator, compact encoder, and separate
build-only preflight retain their previously approved hashes. In particular,
the guard is still `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27`
and the build-only preflight is still
`a4d94e8efe9a9fa33ffc4194b829c85d47a975b0dda6073e1139af19758b280a`.

## Result and witness correctness

The complete compact stream is inserted before any solver call. Its deterministic
header and clause hash match the build-only variant. The optional expected-model
hash is checked before search; for n79 the scheduled command should bind
`909f510443e97c8b909e783115df53f6360f87b18dbce471794ffdf09bb4c2f6`.
A partial stream or mismatched expected hash cannot reach the solver call.

`solve_limited(expect_interrupt=True)` results are compared by identity.
Only Python `True` and `False`, before the deadline and with no timer event,
can support a conclusion. `None`, integer zero, unexpected values, interrupts,
source changes, and errors do not become UNSAT. A false result is explicitly
`restricted_family_unsat_solver_reported`, with `proof_checked=false`.
It concerns exactly the reviewed near-quarter family and is not independently
proof-checked or an unrestricted nonexistence result.

For SAT, every real orbit variable must be present exactly once, with an integer
literal in range and no duplicate or contradictory assignment. The selected
variables must include exactly `(n-1)/2` four-orbits and one diagonal pair.
Expansion uses the frozen orbit map; both independent integer geometry checkers
must approve exactly `2*n` points. The native solver is deleted after obtaining
its model and before geometry validation. Missing, malformed, wrong-family, or
geometrically invalid returned models cannot produce a witness.

The verified certificate, selected orbit IDs, formula hash, six source hashes,
and both checker reports are serialized before a terminal success report.
The file is fully written and fsynced, then linked atomically into a hash-named
destination without replacing an existing file. Existing bytes must match;
the directory is fsynced. The parent checks the saved file digest before
accepting success. A later guard/source failure clears the accepted conclusion
and witness fields, retaining an observed path solely for independent re-audit.
This does not promise protection against arbitrary later external file editing.

## Resource and cancellation audit

The wrapper uses the exact original host guard, with positive finite ceilings
of 120 seconds and 256 MiB. The child receives a deadline set before spawning,
so construction, search, decoding, verification, and persistence share one
budget. Construction checks the deadline and parent/alive marker at publication
points. The host monitor also covers native allocations and all child phases.
It remains a sampled kill gate with possible overshoot, not a hard peak cap.

The solve interrupt timer uses the remaining total budget. Its callback marks
an event before interrupting the native solver. The timer is canceled and
joined before native deletion or reassignment of the solver reference; thus a
late callback cannot race destruction. Boundary results are conservatively
rejected. SIGTERM and SIGINT in the guarded parent unwind the original guard's
process-group cleanup and produce an incomplete cancellation report. An alive
marker and parent-ID checks cover startup/construction cancellation races.
SIGKILL is inherently uncatchable; this is not a general guarantee against
every possible external process termination or escaped descendant.

All six source hashes, including the checker and new wrapper, are checked
before import, after construction, after solving, before witness persistence,
before conclusion, and by the parent before accepting its result. Parent gate
failure, cancellation, source change, or malformed witness clears affirmative
conclusions even if the child had already published one.

Two issues found in the initial design were corrected before this freeze:
the destination directory is now fsynced after linking, and parent SIGTERM
now unwinds worker cleanup. The reviewed tests cover both behaviors.

The earlier n79 build had only 4.265625 MiB of sampled headroom. Search can
allocate additional native memory, and PySAT's full returned model materializes
all auxiliary literals before the native solver can be freed. Both remain
subject to the same gate. Successful construction does not predict whether
this first bounded search or SAT decoding will fit; no cap increase is approved.

## Independent verification and host evidence

An independent geometric census enumerated the exact family-cardinality choices:
n3 has one valid assignment among one candidate; n5 has zero among twelve;
n7 has zero among 252. This supplies known SAT and restricted-family UNSAT
fixtures without relying on the new wrapper.

The reviewer reran the new solve suite and compact build suite together:
23 tests, 21 passes and two real-host `ps` skips, in 0.991 seconds of reported
test time. New tests cover literal validation, immutable file reuse/collision,
actual n3 SAT and n5 UNSAT, witness-before-conclusion order, `None`/integer-zero
handling, timer-fire overriding false and join-before-delete, partial streams,
hash mismatch, source mutation, host failure overriding success, startup parent
loss, expired construction, SIGTERM cleanup, and adapter forwarding.

Separate reviewer worker calls reproduced n3 SAT, n5 and n7 scoped UNSAT. The
n3 saved file was checked by both exact geometry algorithms. Additional fake
SAT returns with missing real variables, duplicate real variables, and a
correct-cardinality but geometrically invalid n5 selection all failed before
persistence, with null solver result/conclusion and no accepted witness.

The Lead reported the full host suite as 152 tests with 151 passes and one
transient startup `EPERM` in the existing compact-preflight test. It failed
closed; this failure must remain in the validation record. An isolated rerun
of all ten compact-preflight tests passed, and all thirteen new solve tests
passed on the real host, including the real SAT/scoped-UNSAT and SIGTERM cases.
The guard was not weakened.

The reviewer independently read `data/near-quarter-compact-solve-n3.json`:
two complete clauses, the same n3 formula hash as preflight, genuine SAT,
0.084539 seconds, two real RSS samples, 55,984 KiB sampled peak, exit zero,
no monitor error, and no fired timer. Its six-point witness file was reread,
hashed, and independently checked by both exact algorithms. File SHA:
`631f4b6f33976acb35068f20231a378c5a084b9c5731550716d369029efbcabe`.
Normalized geometry SHA:
`19dcfc15bc76852b31825b197fd718e36a4914dd7b1b7be468ecf5250e9e7204`.

The source and tiny-host gates are complete. Any n79 outcome still requires
independent report/artifact inspection, precise resource-status interpretation,
and scoped wording. No novelty or global nonexistence claim is authorized.

## First scheduled n79 result: resource-limited, no conclusion

The Lead scheduled `r17-near-quarter-compact-solve-n79`. The reviewer read the
saved report and supervisor receipt and independently compared all six source
hashes and the entrypoint hash to the frozen files. All match. The command
explicitly bound the expected complete formula hash from the successful build.

The worker published 2,300,453 emitted/inserted clauses, 591,304 variables,
12.775870 seconds of construction, and entry into the solve phase. Its saved
prefix hash equals the expected complete preflight hash. It then hit the
unchanged sampled RSS gate: 262,400 KiB (256.25 MiB), 313 samples, 15.191296
seconds guard elapsed, child return code -9. The 0.25 MiB threshold overshoot
is consistent with sampled gate semantics. The supervisor receipt has exit
code 2 and failed execution status. No monitor error was reported.

The parent correctly cleared all run/search/CNF/build completion flags and
the accepted complete model hash. Solver result, conclusion, accepted witness
path/hash, and observed witness path are all null. `search_performed=true`
and `phase=solve` record that the worker reached its search phase; no completed
solve result or search-duration measurement survived. The prefix digest is
diagnostic and does not override the failed run's completion flags.

This is an incomplete memory-limited attempt, not SAT, UNSAT, proof of absence,
or a 120-second completed search. No witness was produced. The result does not
authorize a cap increase, automatic retry, or any stronger mathematical claim.
