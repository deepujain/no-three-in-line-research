# Independent checkpointable diagonal DFS core review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
The core is approved for a separate resource-guard and persistence integration.
This is not approval to schedule its standalone CLI at n79. No n79 model,
traversal or benchmark was executed by the reviewer.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_secant_checkpoint.py` | `48f49f36a7f99bc3d42bc5c4376c3267c5d0f0b05ba9af27f4619403e20f6721` |
| `tests/test_diagonal_secant_checkpoint.py` | `40363cd4386a8701406babf92e0534a634742ac4941f23a7ddcff660dc6bbfb1` |
| Frozen fast core | `38ec5044a8db85f046be24feb97c51adb6a95825afccac375d078195a57022a3` |

Each active slice has one iterative DFS stack. An entered frame records the
next candidate cursor; a pending last frame has a null cursor. The parent
cursor advances before the candidate child is pushed, so the pending child
is represented explicitly rather than lost if a budget expires. On restore,
the singleton is inserted, every ancestor's identical MRV candidate list is
recomputed, and each child must be the candidate just selected by its parent's
cursor. Orbit duplication, inadmissible insertions, invalid cursors, nonfinal
pending frames and incorrect root frames are rejected. The imported exact
state push/pop retains the previously reviewed secant and axis invariants.

An entered node is counted only after candidate enumeration completes. A
timeout during that enumeration leaves the node pending, so it is retried
instead of skipped or double-counted. A leaf's callback and both exact
verifiers finish before its count is committed. Exhausted frames are popped;
the slice index advances only after its stack empties. All later slices are
represented by their unvisited index range. At completion no stack remains
and all declared slices have been consumed. This preserves the fast core's
deterministic MRV/tie/orbit traversal, including repeated visits arising from
different insertion orders.

The checkpoint binds grid size, sorted declared slice lists, all four relevant
source hashes, exact orbit-order digest and a branch-order version. Existing
bytes require a caller-supplied expected SHA; current bytes and source hashes
are rechecked before replacing the checkpoint. Paths can change without
changing the byte identity. Counters are typed, nonnegative, sum consistently
and do not attribute work to future slices. These are structural consistency
checks, not a proof that all prior computations occurred. The expected SHA
must originate from trusted local execution; an attacker or mistaken caller
who substitutes both state and its expected hash can forge coverage.

One frontier is published per invocation. A failure before replacement leaves
the previous checkpoint intact, so uncommitted work and callbacks replay.
The callback must therefore persist verified witnesses atomically and be
idempotent. A failure after replacement can lose the return value but leaves
new bytes naming the previous expected SHA; recovery must inspect the trusted
new state and explicitly adopt its current digest. It must not blindly retry
using the obsolete digest. File contents are fsynced before replacement; the
directory is not fsynced, so no power-loss durability guarantee is made.

The read/check/replace sequence is not an atomic compare-and-swap or lock.
One exclusive owner is required. The integration must enforce that ownership,
bind this core and its full checkpoint identity, retain/recover trusted digest
anchors, and keep witness publication before checkpoint progress. Cooperative
checks do not bound state restoration, individual push/verification/callback
operations or checkpoint I/O. The external wrapper must enforce total elapsed
time and sampled RSS and reject accepted completion after any cleanup,
resource, source or cancellation failure. A surviving checkpoint can be useful
after an incomplete run, but its existence does not make that run complete.

I independently ran the five focused tests plus two fast-core tests: all seven
passed in 0.703 seconds. These cover complete n3/n4/n5 three-node resumes with
identical ordered witnesses and counts, relocation, identity/hash mismatch,
malformed cursor rejection, source change, timeout, callback failure and
interruption immediately before/after replacement.

I additionally performed 90 tiny resumed invocations across n2/n3/n4,
per-invocation budgets 1/2/5, and selected first/last deficit and singleton
indices supplied in reverse order. Every combination matched the fast core's
complete ordered witness visits, per-slice and total node counts. Every saved
SHA and predecessor SHA matched its returned identity; new node increments
matched the per-run budget and counters. No guard, large-grid performance,
unique-coverage percentage or unrestricted infeasibility claim follows.
