# Independent fast diagonal DFS guard integration review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
Approved for the lead's actual-host n3/n5 CLI gates. No n79 traversal or
benchmark was performed by this reviewer. Any later bounded numerical work
requires the lead's scheduling and final source identity check.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_secant_fast_guard.py` | `f36c0a86f75567ad3e8706d2470d107209584f1fe6724eb4ed11a59e0782e98d` |
| `tests/test_diagonal_secant_fast_guard.py` | `797d730ccfd852ac34e681ec295e5c0ae579a36a8bb78bb97f63552e6f4b8b10` |
| Shared `src/lazy_sat.py` | `77520504b5d65431a259926b8306db5f2ffd53e979a29b2a49749747b90e4a9d` |
| Owned-process helper | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

The wrapper imports only the separate reviewed fast core for traversal.
Its source binding captures the original and fast cores, original and current
wrappers, verifier, owned-process helper and actual dispatcher. These hashes
are checked before importing the search, before every witness publication,
after search and at parent acceptance. The earlier mathematical proof remains
in `research/diagonal-secant-fast-review.md`; historical core/guard files are
unchanged.

Each invocation creates a persistent run-specific witness directory. Every
leaf has already passed both exact geometry verifiers and core family/count
checks. The callback attaches bound source hashes, writes a temporary sibling,
closes it, and uses atomic replacement of the normalized-geometry filename
before worker terminal state is written. Repeated visits can replace the same
normalized witness; visit counts are not distinct-file counts. This protects
against partially written published files during interruption. It does not
provide fsync-backed power-loss durability or immutable storage. A failed
enclosing run may leave valid files that require independent re-audit.

The shared CLI captures process start before heavy imports and passes that
timestamp. The wrapper subtracts elapsed setup time before invoking the helper
and rechecks total elapsed time afterward, including source validation and
cleanup. Imported `run` starts a fresh clock. I identified an inherited stale
clock in imported `main(argv)`; the author corrected it to use a fresh timestamp
for explicit arguments while preserving actual CLI startup and explicitly
supplied timestamps. The regression passes at the frozen version above.

The helper receives the remaining deadline and unchanged 256 MiB maximum,
with a parent SIGTERM flag supplied as its cancellation predicate. Completion
requires normal guarded exit, clean verified cleanup, stable sources, no
cancellation and no overall time failure. A completed diagnostic worker result
cannot override wall/RSS/monitor/cleanup/cancellation failure. Only the exact
`all_declared_slices_exhausted` worker status marks the parent complete;
node-limited and timed-out traversals stay incomplete. All conclusions remain
restricted to the declared deficit/singleton reflection slices.

The owned-process helper's fixed session/group contract, sampled RSS limits,
and inability to guarantee removal on cleanup errors apply unchanged. The
lead reports its four tiny actual-host gates passed. I independently reran
nine final fast-core/wrapper tests in 1.046 seconds, all passing. These include
actual n3/n5 DFS worker processes with mocked resource guard, both geometry
verifiers on every saved witness, source binding before/after search and at
parent exit, cancellation propagation, completed-child failure overrides,
atomic witness-before-terminal ordering, dispatcher forwarding, fresh imported
clock and original/fast complete ordered tiny traversal equivalence.

The wrapper-specific real-host CLI tests remain separate from mocked monitor
checks. The lead should reread their saved reports and normalized witness files
with exact source identities before numerical promotion. Any new shared CLI
route changes its bound hash and requires a final dispatcher review.

## Final dispatcher and actual-host evidence

The subsequent isolated owned-row solve route changes only the shared
dispatcher identity to
`f05d541900b39aee817663c3ac694d72e8d06d58bc8da08a6d44d0090c358de5`.
I inspected that route and the preserved fast clock forwarding, then ran
three targeted dispatch/fresh-clock tests successfully in 0.009 seconds.
This dispatcher approval does not approve the separate solve implementation.

The lead reran actual-host fast CLI gates under that final identity. I
independently inspected `data/diagonal-secant-fast-guard-n3-current-cli.json`
and its n5 counterpart, matched every source hash, and reread all four n3
and sixteen n5 saved witnesses. Both geometry verifiers, target point count,
normalized filename hashes and source metadata all pass. Both reports have
complete exhausted tiny traversals, 26/415 nodes and 5/35 witness visits,
normal exit, clean cleanup and source stability. Sampled peaks are 33,296 KiB
and 53,488 KiB from one/two ordinary samples. Their report byte hashes are
`57aae8ef875430e0b2d885774d7c8dd8274c4a076eeaac46ccf05fdf3b463d35`
and `d55e9da8af28e12c3642e7205553c0d1d9f7d6bab6c3011a6298945470f9ae6e`.

I also inspected the lead's r24 n79 100-node preflight report and receipt,
without running any n79 computation. It reports `node_limit`, complete false,
exactly 100 visited nodes and no witnesses in the sole declared (d=0,t=0)
slice. The helper exited normally with clean cleanup, stable sources, four
RSS samples and a 55,552 KiB = 54.25 MiB sampled peak. Worker elapsed time is
0.115218583 seconds; enclosing wrapper time is 0.221277291 seconds; the
supervisor receipt records 2.013586709 seconds. These have different scopes
and must not be conflated as one per-node timing measurement.

The r24 CLI exit two and receipt `failed` encode the incomplete node-capped
search. The resource/cleanup report itself has no failure. This supplies
accepted bounded cost evidence, not slice exhaustion, a meaningful coverage
fraction, a witness, or an infeasibility conclusion. Tiny and early traversal
costs do not establish whole-search feasibility.
