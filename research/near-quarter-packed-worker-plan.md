# Proposed packed orbit worker: allocation and review gates

This is a design document, not a worker implementation or permission to run a
new numerical job. Shared chain/CLI/helper sources stay frozen. The reviewed
mechanism is separate from the stopped full-CNF Glucose branch. Only the
n3/n5/n7 state/MRV prototype exists; no production checkpoint or large-grid
entrypoint exists. Model setting: `gpt-6.1-sol`, reasoning `high`.

## Branch decision

Prefer a future **row-filling batch** worker, conditional on independent review
and a new tiny implementation gate. The current one-orbit MRV prototype remains
unchanged and is understood to allow multiplicities. The analytical uniqueness
argument and unsafe-global-ID counterexample are in
`research/near-quarter-mrv-order-addendum.md`.

Enumerate declared main-diagonal pair slices in an explicit permutation. For a
fixed pair, select only four-orbits. Recompute current admissible orbit masks
using reversible secant/row occupancy probes. Choose an underfilled row by
fewest individually admissible contributors, then larger deficit, then the
explicit row permutation. Fill its whole deficit with one orbit of the required
weight or, for deficit two, an unordered pair of weight-one contributors.
Generate pairs by two local permutation cursors, never a quadratic stored list;
require joint geometry/axis admissibility. No global increasing-ID restriction
or global visited cache is allowed. The proven remaining-orbit and optimistic
top-`r` row shortfall tests remain the initial prunes.

A full completion determines a unique batch for the chosen row, giving unique
paths under this policy; that argument is analytical and awaits tiny batch
code tests. The first existence worker stops at its first dual-verified,
durably published witness, avoiding an unbounded witness ledger. A stage that
hits any budget records a frontier, not exhaustion or infeasibility.

## Isolated components and identities

Keep four isolated components: packed geometry state, batch domain/traversal,
checkpoint codec/replay, and owned-process wrapper. Do not edit existing DFS,
CNF, preflight, solver or helper sources. Reuse the unchanged owned-process
helper (at most 30 seconds and 256 MiB) after separate wrapper review. No native
Solver or resident CNF is created. Use the frozen exact orbit map and both
integer geometry verifiers; retain the established immutable, fsynced witness
publication semantics with explicit utility source binding.

Bind the family/target/grid, ordered orbit-map digest, full source identities,
diagonal/orbit/row permutations, batch/prune versions and point insertion order.
A compact identity manifest is bounded to 4 KiB; store permutation arrays as
bounded packed payload, not duplicated unbounded JSON lists. The accepted
witness identity is mathematical (family/map plus sorted selected IDs), while
stage/order provenance is recorded separately. No mandatory CNF hash is used:
this worker represents direct geometry rather than a CNF instance.

## Stage report and resource semantics

A worker report should distinguish these states: verified witness; declared
slices fully exhausted; checkpointed node limit; wall/RSS/cancellation limit;
source mismatch; checkpoint/worker/cleanup error. Only an accepted host gate
and stable identities permit accepting a child artifact. Even a full trusted
DFS exhaustion remains restricted to its declared slices and is not an
independently proof-checked UNSAT certificate.

Report `nodes_before`, `new_nodes`, `nodes_total`, domain probes, joint-pair
probes, geometry updates, restore/replay work, declared/completed slices,
frontier parent/output hashes, witness visits, guard peak/samples/cleanup and
elapsed time. Count a node once at entry, before its branching domain; restoring
an already entered node must not increment cumulative search nodes. Restore,
verification and publication time/RSS still count toward the stage gate.
Domain probes are not nodes and should not be hidden in a node-rate claim.

Parent setup and receipt writing remain outside the unchanged helper interval;
the child common deadline is set before launch. SIGTERM/SIGINT set a flag and
reach only consistent boundaries. A killed child may leave no new checkpoint;
the prior immutable parent remains the accepted frontier. Cleanup failure,
source change or failed resource gate overrides any child completion claim.
An observed saved witness may be separately audited, but the failed stage must
not be relabeled successful. No automatic cap increase, unchanged retry or
unreviewed continuation is allowed.

## Checkpoint commit/replay protocol

Use a new family-specific binary envelope with strict wire length at most
1 MiB before allocation/parsing. Include content checksum, schema version,
identity manifest, explicit parent content hash, cumulative node total, current
slice index, selected orbit path and traversal frames. Each batch frame records:
chosen row, domain digest, singleton/pair cursor, selected child batch IDs,
node-entry phase and next-unvisited position. Two-orbit batches must be complete
before checkpoint publication; never serialize a half-applied probe/batch.

Advance the parent cursor before entering a child and retain an explicit child
relation. On restore, rebuild the selected prefix from empty state, verify every
push, reconstruct deterministic domains and check row, domain digest, cursor
range, selected batch and phase. Reject any identity/relationship discrepancy
rather than repairing it silently. Source or permutation migration requires a
new reviewed derivation, not an ordinary resume.

Write/fsync a temporary file, install an immutable content-named checkpoint,
fsync its directory, then publish the atomic stage report naming exactly that
checkpoint and parent. The supervisor accepts continuation only when receipt,
report and child/parent hashes agree and the guard is clean. Duplicate delivery
of an already committed stage is idempotent; an already-terminal frontier may
not be counted as newly searched. A failed/torn publication cannot advance the
accepted chain. This is one linear frontier chain, not a union of cursors from
several unvalidated histories.

## Bounded storage contract and remaining gates

The proposed packed live payload budget at n79 is 68,700 bytes, itemized in
`research/near-quarter-packed-mrv-proposal.md`. Batch cursors/two child IDs fit
within its reserved 64-byte frame metadata. This excludes all Python/native/
interpreter/OS overhead, serialization buffers and temporary allocations. No
RSS or runtime fit follows from that arithmetic. Any implementation retaining
extra cached objects must either bound and account for them or omit them.

The allocation sequence should be:

1. Finish independent review of the frozen tiny state and analytical batch
   uniqueness proof. Preserve that reviewed source checkpoint.
2. With a separate Lead allocation, implement only hard-tiny row-batch and
   codec/replay components. Test exact n3/n5/n7 full sets and leaf multiplicities,
   forward/reverse permutations, synthetic row-quota cases that exhibit
   one-orbit duplicates, and failed second-orbit rollback. No large-grid path.
3. Test uninterrupted versus resumed traversal at every tiny node/batch boundary,
   including one-step budgets, pair-cursor boundaries, terminal reuse, source/
   order/parent corruption, wrong selected child, injected publication errors
   and cancellation. Check cumulative nodes and unique leaf sets exactly.
4. Independently review the wrapper and run actual-host tiny RSS/wall/SIGTERM/
   checkpoint gates against final source/entrypoint identities, under the same
   30-second/256-MiB helper. No native Solver and no CNF allocation.
5. Only after another explicit Lead authorization, implement the larger packed
   engine, replay the accepted n71 fixture as a controlled push/undo regression,
   and measure a modest-size, small-node pilot. That fixture replay is not a
   search or a performance forecast.
6. An n79 code path or run needs its own source review, measured resource evidence
   and explicit Lead allocation. It is not authorized by this document or by
   tiny correctness alone. Existing chain experiments remain separate and their
   scope/results may not be imported into this family's frontier.

The next requested action is review and allocation of tiny batch/codec work,
not another full-CNF/backend run. All scheduling and aggregate-memory accounting
remain with the supervisor, with at most one SAT allocation.
