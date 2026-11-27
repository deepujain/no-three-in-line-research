# Independent explicit-threshold solve review

Source and final CLI route approved for the supervisor's actual-host tiny
gates. Reviewer: Mathematical Reviewer, `gpt-6-astra`, high. No n79 formula,
build, search or benchmark was run by this reviewer.

## Frozen identities

| File | SHA-256 |
| --- | --- |
| `research/near_quarter_direct_solve.py` | `c2970ad57add2fef5d724ba69e7511db8d2ccc9f8aa7a952dd861b1199478525` |
| `tests/test_near_quarter_direct_solve.py` | `d772d8f5861c5ae1f04ff4eb6541a55cdc53897b78cdc3f3c5a5a46cb220af81` |
| `src/lazy_sat.py` | `abddf7b5c2f440de4fb1e6d82cb7c8e78fdea046ff46f759af6754cadd261b9b` |
| `research/near_quarter_direct_preflight.py` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `src/near_quarter_direct_thresholds.py` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |

The full source was inspected and compared against the previously approved
row-quota owned solver `17aa895edd36cb3da172651b307e6b86e8600599da74b7c08740aee330bd36ed`.
The changes select the explicit threshold configuration, corresponding header
and stream, add threshold provenance and validation, and expose an isolated
CLI route. The existing ownership helper, decoder, witness persistence,
verification and solver-result semantics remain unchanged.

## Acceptance and mathematical scope

Both thresholds must be explicitly selected from `{5,6,7}`. Twelve source
bindings include the threshold encoder, build adapter and actual dispatcher.
The mandatory expected model digest must match the complete ordered CNF and
its configuration/source-bound header before any solve call. Partial streams,
missing/malformed hashes, changed sources and mismatched configurations cannot
start search. The mathematical family is unchanged by the separately reviewed
threshold equivalence proof.

Only the genuine native booleans True and False can produce a conclusion.
None, integer zero/one, other values and interrupted returns cannot establish
UNSAT. The interrupt timer is cancelled and joined before deleting or changing
the native solver. A SAT result materializes the assignment, frees the native
solver, validates the real-orbit assignment, and runs both exact geometry
verifiers. The immutable hash-named witness is fsynced and its directory
fsynced before terminal success is published. The parent verifies its byte
hash before accepting it. A saved valid witness may survive a later failed
invocation; that does not make the invocation complete.

False is reported only as restricted-family solver-reported UNSAT without an
independently checked proof. Helper, source, cancellation or file-validation
failure overrides any worker conclusion and clears accepted result fields.
Native solver deletion occurs within the guarded worker lifetime, so a late
worker failure or cleanup/resource overrun is not accepted from an earlier
worker state alone.

## Resource and integration boundaries

The unchanged owned helper remains bounded to at most 30 seconds and 256 MiB
sampled guard-plus-owned-process RSS, including construction, solving,
verification/persistence in the worker, and helper cleanup. Parent setup and
final receipt serialization remain outside the helper timing interval. These
are sampled/cooperative gates, not hard continuous memory or end-to-end wall
guarantees. Earlier helper ownership/cleanup limitations still apply; cleanup
failure does not imply verified process emptiness.

The new `--near-quarter-direct-solve` dispatcher branch forwards only the
remaining arguments to the new adapter and leaves the existing routes intact.
Historical build reports retain their historical dispatcher source identity;
the formula digest depends on its model header/stream, while this invocation's
full source provenance records the new dispatcher separately.

## Independent validation

Twenty tests passed independently in 0.309 seconds; one explicit actual-host
test was skipped. Final source, test and dispatcher hashes were checked.
Coverage includes real n3 SAT and n5 restricted-family UNSAT; dual-verifier and
witness-publication ordering; malformed SAT assignments; timer/free ordering;
nonboolean and interrupted results; incomplete streams; missing/wrong expected
hashes; source changes; parent failure overrides; and final CLI forwarding.
Separate n9 cases exercise changed support branches for `(5,5)`, `(6,6)` and
`(7,7)`, matching their exact clause/variable totals and configuration-bound
digests. A wrong-pair digest is rejected before solve.

Actual-host tiny gates and any n79 allocation remain with the supervisor.
A preceding successful build does not guarantee solve-time memory safety.
No new witness, search exhaustion, SAT, UNSAT, novelty or unrestricted
infeasibility result follows from this source review.
