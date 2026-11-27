# Independent owned-guard row-quota preflight review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
Approved for the lead's actual-host n3/n5 CLI gate, followed only by a separately
scheduled bounded n79 build. No reviewer n79 model construction, solve or
benchmark was performed. The source adds no new mathematical restriction.

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_row_quota_owned_preflight.py` | `1fe62197cbd420713ab2152a9a1e24cd556d26a6ef7d130ea2e6597de86edf0e` |
| `tests/test_near_quarter_row_quota_owned_preflight.py` | `cabad0e73a6767aa0a504198c870326898e60a289ba7f05b43b3c8756e8b8564` |
| Shared `src/lazy_sat.py` | `77520504b5d65431a259926b8306db5f2ffd53e979a29b2a49749747b90e4a9d` |
| Owned-process helper | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

I compared the complete diff against the frozen prior row-quota preflight.
The worker's line pass, ordered clause stream, native insertions, model header,
counter meanings, deadline checks and source checks are unchanged. The changed
integration imports the approved separate owned-process guard, binds ten project
sources including both the helper and historical utility/preflight files, uses
a separate CLI flag and temporary directory prefix, and changes parent signal
handling to a cancellation flag. The flag is passed to the helper rather than
raising inside cleanup; its original handlers are restored afterward.

The parent still loads worker diagnostics and then applies the enclosing gate.
Every non-exited gate, including cleanup/launch errors and cancellation, clears
complete/CNF/build flags and the full model digest. Source mutation also clears
completion. The helper itself requires verified clean cleanup before emitting
an exited gate. A child publication cannot override either failure. The alive
marker is removed on return or exception, preserving the original parent-loss
contract. The guard clock includes both expensive worker passes and cleanup,
while preliminary CLI/setup work remains outside its elapsed time; this wrapper
does not claim a whole-CLI 30-second hard limit.

The unchanged mathematical equivalence, header/digest semantics and tiny model
checks remain documented in `research/near-quarter-row-quota-review.md` and
`research/near-quarter-row-quota-preflight-review.md`. The helper's restricted
session/group contract and possible live-process remainder on cleanup failure
are documented in `research/owned-process-guard-review.md`. Historical sources
and failed r22 artifacts remain intact.

I independently ran the adapter tests together with the separate fast-DFS
wrapper tests: 15 passed and one actual-host adapter test skipped, in 0.720
seconds. Nine passing tests belong to this adapter. They cover actual native
n3/n5 builds with solve methods forbidden, exact stream hashes/counts, all ten
source bindings, source mutation, parent failure overriding completed state,
parent-loss/deadline behavior, cancellation flags, and isolated CLI routing.
The actual-host n3/n5 CLI gate remains the lead's responsibility; mocked guard
tests are not RSS or process-cleanup measurements. I independently inspected
the shared dispatcher and verified both new routes preserve the earlier routes.

No SAT/UNSAT or witness claim follows from a complete build. Any later observed
n79 count, full formula hash and sampled RSS must come from a successfully
completed guarded run, not from the existing algebraic cost forecast.

## Successful lead-run r23 build

The lead reports that all four helper actual-host gates and all ten owned-row
adapter tests, including n3/n5 CLI builds, passed before the separately queued
r23 build. I subsequently read `data/near-quarter-row-quota-owned-preflight-n79.json`
and its receipt `data/experiments/r23-row-quota-owned-preflight-n79.json`.
The report byte SHA-256 is
`f1c6bc7e104443b0262ec582fb42ee4f6753487819cd320761ac9c2b7fe1ab00`.
All ten report source hashes match the current frozen files. The receipt
records exit zero and 14.104401500 seconds of enclosing elapsed time.

The accepted build reports 2,072,304 emitted and inserted clauses, 475,708
variables, 411,545 C4 line groups, and 1,644,284 represented full lines.
All complete-build and preliminary-group flags are true. The clause/variable
counts match the earlier independent forecast: 2,300,453 - 231,192 + 3,043
= 2,072,304 clauses and 591,304 - 115,596 = 475,708 variables.
The line counts agree with the previously reviewed unchanged line grouping.

The guard records ordinary exit zero, 12.775648125 seconds, 311 RSS samples,
223,712 KiB = 218.46875 MiB sampled peak, and clean cleanup after one fresh
sample in 0.011896125 seconds. There is no monitor or cleanup error and no
earlier failure trigger. Sampled headroom below 256 MiB is 37.53125 MiB;
this does not guarantee the peak between samples or future solving memory.

The full model digest and final prefix digest both equal
`397546bb8cbd65a7bb9ebfb1c22d14e41dc1a4092e25d310a00bdaeff7344b3d`.
I accepted that digest from the reviewed stream and saved report; I did not
independently reconstruct the n79 formula. `search_performed` is false and
`solver_result` is null. This is complete construction evidence only. The
historical r22 host failure remains recorded separately and is not retroactively
reclassified. Any separate bounded solve needs its own reviewed integration.
