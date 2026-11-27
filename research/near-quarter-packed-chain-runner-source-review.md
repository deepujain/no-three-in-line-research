# Independent source and signal review of the packed-chain caller

PASS. Source review and an independent run of all ten focused tests (1.416 seconds) support one Root-allocated 120-second caller invocation through the existing experiment pool, in a packed-only single-worker window, with fixed 250-new-node stages and existing 30-second / 256 MiB / 2-second-reserve stage limits. A unique run ID is required; there is no implicit retry. Ordinary pool reservation is 150 seconds. This reviewer performed only tiny correctness tests and structural artifact checks, not an n79 search launch.

| Artifact | SHA-256 |
| --- | --- |
| Caller source | `a5fcb6ad8ee5777fa8d2c44cca5e595c617c1c221fe1ac04bb57b067fd9ea182` |
| Focused tests | `87752dd65be53d2e6dac98561fe045fb73c5ca6504f3f2ea1f8df2615d75344c` |
| Experiment pool | `8a347e711616dc54a68aaadd2c2c3e87d30dcf7f826e0a34414e64d10457ce29` |
| Author tiny evidence | `e682436784563ee4d8ada24547d69d1b5c9a22bcc395b9a87626fd3876236ce3` |
| Author method | `d1c732aebb8cc6604d7cc1ac42e1989f91a0e6c4a9059a1ac738b0744e5aab6b` |
| Runtime template | `243775d2aaa74c29171d0f5771c197b797bcc97c611f8e047678b5acb7d01df4` |

The 7,071-byte runtime template independently passes strict loading and accepted-HEAD audit. It fixes quota 250 and the exact 511-node HEAD `9039fdd3607dafd5cab0ab4d4fa88ea83aca748d25e774fd3f0be39bad11b8d5`, checkpoint `71d9ea2f977c6bdc50aa5da2907d439eff8637cb2f1d103bae59f7a4ec1da01b`. All nine packed source slots remain the previously reviewed identity; the new caller remains separately pinned. Pool diff is solely addition of the caller path to ALLOWED.

The implementation preserves exact previous accepted authority, checks returned stage ID and receipt hash, validates resulting job/report/checkpoint binding, and stops on retained or unknown lease, rejection, uncertainty, idempotent redispatch, changed source/HEAD, terminal result, cancellation, or insufficient remaining time. It never follows an unrelated newly discovered HEAD. The current caller source is checked before every stage and after an accepted return. At least 32 seconds must remain before dispatch. Existing `run_stage` handles actual stage guarding, writer ownership, validation and publication; no packed worker or checkpoint protocol changed.

The independent tests exercised sequential exact parents to a tiny verified witness, n5/n7 exhaustion, fixed template limits and hash, budget boundaries, rejected/uncertain/idempotent/retained-lease returns, source/self changes, returned authority mismatches, and writer-lease refusal. The real SIGTERM test delivers the signal at the worker's `after_head_replace` boundary while its nested cancellation handler is active. One stage is accepted, the caller reports cancelled, and no second stage starts. Original handlers and the prior absence of a wakeup descriptor are restored. A separate incompatible-descriptor test verifies restoration of the pre-existing descriptor and handlers and closure of the caller's own pipe. No asynchronous exception interrupts a commit.

Timing scope remains explicit: immutable final evidence measures through summary preparation; the returned complete caller time also includes durable summary publication and handler cleanup. Pool outer elapsed time is the single aggregate charge. Inner stage timing is evidence, not an additional charge. The total budget is not a hard guarantee against unbounded filesystem coordination; unchanged pool timeout/reservation semantics remain the outer containment. Abrupt termination may leave only the immutable start and stage artifacts. These are preserved limitations, not reasons for another protocol expansion.
