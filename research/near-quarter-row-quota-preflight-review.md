# Independent row-quota build-only preflight review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
The frozen source is approved for the lead's real-host tiny gate and a
separately scheduled bounded build. No n79 construction, solve, or benchmark
was performed by this reviewer. Approval does not itself schedule a run.

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_row_quota_preflight.py` | `4c94335e07f93357ef153fe3582892e1918af45faa80d3d66ca441e9cd8a7244` |
| `tests/test_near_quarter_row_quota_preflight.py` | `8c2187d5040d9c4ddca854fa0182820de515727508000d2025733c82de521656` |
| Combined `src/lazy_sat.py` | `ac1b568303153c7c39f3d01fff1df7cbce36d0bfcf36951df2fe24419f73c509` |

The underlying row-quota equivalence proof and independent exhaustive tiny
checks are in `research/near-quarter-row-quota-review.md`. This wrapper adds
no model restriction. It first enumerates the complete C4 line groups and
then inserts every emitted clause into a fresh Glucose3 instance. It invokes
neither solve method. The variant-specific sorted JSON header and ordered
clause stream define a separate full model digest. Partial digests remain
prefix diagnostics; a failed parent gate clears the complete model digest.

The exact original `guarded_process` function is reused by identity. Its
ceilings remain 30 seconds and 256 MiB sampled parent-plus-worker/group RSS,
including native memory; sampling can overshoot. The guard clock starts at
guard invocation, rather than at Python CLI process startup. Both expensive
worker passes share this one guard budget, and the child construction deadline
is set slightly earlier. Preliminary CLI import, argument parsing, source
hashing and output setup are outside that guard elapsed time. No whole-CLI
30-second guarantee is inferred. The separate SIGTERM/SIGINT context unwinds
the original process-group cleanup; the child checks a live-parent marker and
parent PID before import and on construction publication. General SIGKILL
or escaped-descendant guarantees are not supplied.

Eight project/entrypoint sources are captured before spawn, checked before
encoder import and after stream exhaustion, and rechecked by the parent.
They identify project files, not all Python dependencies or native binaries.
Source changes, monitor/resource/worker failures, host errors and cancellation
cannot preserve a completed build. A child-published completion remains
provisional until normal guarded exit. Partial counters are diagnostics;
the algebraic floor counters are explicitly labeled as such. Clause insertion
counts describe emitted insertions, not the solver's simplified internal size.

I independently reran all nine focused tests in 0.162 seconds: eight passed
and the real-host monitor test skipped because `ps` is denied in this sandbox.
The passing checks include actual native n3/n5 construction (4/25 clauses),
patched solve-method rejection, independently assembled header/stream digest,
line/group and floor counts, all source bindings, mutation before/after stream,
parent failure overriding completed child state, startup/parent-loss/deadline
handling, cancellation and CLI routing. The combined dispatcher had already
passed four independent targeted route/legacy tests. No original encoder,
preflight, solve wrapper or monitor source was changed by this review.

The lead subsequently reported nine actual-host tests passing, including the
n3/n5 subprocess gate. I independently read the saved n3 report: built complete,
four clauses, two variables, eight represented full lines, normal child exit,
0.088893292 guard seconds, 54,512 KiB sampled peak from two samples, matching
eight source identities, and no solve. The saved full model digest is
`fb227c558b46d418ebbbf4e82e6bd12929f1c7712297dda2cf52c9666660d04e`.

The lead's later r22 n79 build attempt failed with host EPERM. I read its
saved report and receipt: process exit two, parent status `host_error`, all
completion flags false, no full model or prefix digest, and no accepted clause,
variable or line counts. Receipt elapsed time was 14.080131209 seconds.
The zero counters are initial fallback state, not evidence that the worker
performed no construction. The lead diagnosed intermittent EPERM in the
original guard's final unconditional process-group signal. The recorded run
does not supply accepted n79 resource/count evidence or a mathematical result.
Historical implementations remain frozen while a separate cleanup variant
receives independent review.

The n79 cost savings remain a conditional algebraic forecast until a guarded
complete build supplies observed counts and RSS. This review makes no SAT,
UNSAT, witness, or global nonexistence claim.
