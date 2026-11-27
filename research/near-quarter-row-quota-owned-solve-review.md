# Independent owned-row-quota bounded solve review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
Approved for the lead's actual-host n3/n5 CLI gates and a subsequent separately
scheduled bounded solve. No n79 model construction, search or benchmark was
performed by this reviewer. Historical model, guard, preflight and solve
implementations remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_row_quota_owned_solve.py` | `17aa895edd36cb3da172651b307e6b86e8600599da74b7c08740aee330bd36ed` |
| `tests/test_near_quarter_row_quota_owned_solve.py` | `296e5e4423998959e48aaf35ecd10a60180c5fec874d047cbb15cc2c8c6b56db` |
| Shared `src/lazy_sat.py` | `f05d541900b39aee817663c3ac694d72e8d06d58bc8da08a6d44d0090c358de5` |
| Owned-process helper | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

The solver uses the independently approved row-quota clause stream and the
exact header function used by the successful r23 preflight. A mandatory
64-character lowercase hexadecimal expected model digest is checked before
construction and compared after complete stream exhaustion and every native
clause insertion, before any search. Partial formulas, missing/malformed
expected hashes and complete digest mismatches cannot reach the solve call.
For n79, the independently audited r23 expected digest is
`397546bb8cbd65a7bb9ebfb1c22d14e41dc1a4092e25d310a00bdaeff7344b3d`.
This review did not independently rebuild that large formula.

The source binds eleven project files, including the exact header provider,
row/compact/original encoders, line generator, verifier, helper, historical
atomic and decode/persistence utilities, this solver and actual dispatcher.
Checks occur before model imports, after construction and solving, around
witness handling, and at parent acceptance. These identify project sources,
not all interpreter or native-library binaries.

The worker calls `solve_limited(expect_interrupt=True)` only after a complete
matching build. It interprets literal Python True or False only; None means
no result and integer/string substitutes are rejected. Timer firing or elapsed
deadline overrides even a False return. The timer is cancelled and joined
before freeing the native solver. On SAT, the full assignment is retrieved,
native memory is freed, and the original reviewed decoder requires exactly
one in-range assignment for every real orbit and the exact four/pair counts.
The candidate must then pass the family check and both exact geometry
verifiers before persistence.

The unchanged persistence utility fsyncs a temporary file, publishes an
immutable byte-hash-named hard link, fsyncs the directory, and verifies any
preexisting destination's contents. Publication precedes a worker result
containing the witness and precedes terminal acceptance. The parent rereads
the saved file hash. A resource/source/cleanup/cancellation failure clears
accepted conclusion, solver result and witness fields while retaining an
observed witness path diagnostically. A valid independently rechecked file can
outlive an incomplete run; this does not make that run complete.

This separate first solve uses the unchanged helper's maximum 30 seconds and
256 MiB, including construction, solve, verification and cleanup within the
guarded worker interval. Initial parent CLI/setup is outside that guard clock.
Native RSS is sampled, and transient overshoot is possible. Flag-based
SIGTERM/SIGINT handling lets bounded cleanup run. The construction deadline and
parent PID/alive-marker checks are retained. Cleanup failure means removal was
not verified and can leave a live process, as documented in the helper review;
such a run cannot be accepted. Any claimed UNSAT is restricted-family,
solver-reported, and not independently proof checked.

I read the complete solver source and final tests, checked exact hashes, and
independently ran all nineteen tests: eighteen passed in 0.746 seconds and
the opt-in actual-host test skipped. Checks include actual native n3 SAT and
n5 restricted-family False; mandatory/wrong/partial model identity preventing
search; strict None/nonboolean handling; interrupted False; timer-join and
native-free ordering; malformed/wrong-family/invalid-geometry SAT rejection;
immutable witness persistence before terminal state; all parent resource,
monitor, cleanup, launch, cancellation and source failure overrides; witness
tamper rejection; startup/deadline/parent loss; signal flags and isolated CLI
delegation. These tests do not replace the lead's actual-host n3/n5 gate or
establish n79 solve feasibility.

## Lead's actual-host gate and r25 result

The lead reports all nineteen actual-host tests passing, including real n3/n5
CLI execution, before scheduling r25. I independently inspected the stable
`data/near-quarter-row-quota-owned-solve-n79.json` report and its
`data/experiments/r25-row-quota-owned-solve-n79.json` receipt. The report bytes
hash to `706e372b9882f09d38cf984896de9ff1fdf5669270408886802973463e7b04ff`;
all eleven recorded source identities match the current frozen files.

The run entered solve after emitting and inserting 2,072,304 clauses with
475,708 variables. The retained prefix digest matches the required complete
397546bb digest above, and diagnostic build time is 9.088743041 seconds.
The enclosing guard then hit the sampled RSS limit: 282,640 KiB = 276.015625
MiB from 211 samples, with 9.258971167 seconds of guard elapsed time. Cleanup
was verified clean after two samples in 0.062094833 seconds; the child was
killed with return code -9. The enclosing receipt reports CLI exit two and
10.060303500 seconds.

The parent correctly clears every acceptance flag, full model digest,
conclusion, solver result and accepted witness path. The actual r25 witness
directory `data/near-quarter-row-quota-owned-witnesses` exists and contained
zero JSON files when independently inspected. This is an incomplete,
memory-limited attempt with no SAT, UNSAT or witness result. Its full emission
counters and matching prefix remain diagnostics, not an accepted solve.

The sampled peak exceeded the 256 MiB threshold by 20,496 KiB = 20.015625 MiB;
this illustrates sampling overshoot. The peak is 57.546875 MiB above the earlier
r23 separate-build peak, but that cross-run parent-plus-worker comparison is
not a direct measurement of a particular native allocation. No larger cap,
unchanged retry or infeasibility inference follows from this review.
