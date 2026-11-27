# Distinct next mechanism: packed near-quarter orbit MRV traversal

Status: analytical proposal plus a hard-limited n3/n5/n7 prototype. There is no
production worker, large-grid code path, CLI route, checkpoint implementation
or n79 run. The full near-quarter Glucose encoding branch is stopped unchanged
after the source-bound negative r31 result. No new backend, wall-time increase,
threshold fallback, cap increase or identical retry is recommended.
Model setting: `gpt-6.1-sol`, reasoning `high`.

The mechanism follows the existing local literature proposal in
`research/near-quarter-next-literature.md`: choose complete approved near-quarter
orbits directly and reject new collinearities with reversible cell/secant state.
It is an implementation proposal, not a novelty or runtime claim. It differs
from the failed full-CNF branch by retaining no full line-constraint table,
cardinality auxiliaries, resident CNF, learned clause database or global visited
set. The existing diagonal-reflection DFS/checkpoints target a different family;
their numerical frontier must not be imported as a near-quarter frontier.

## State invariant and transactional operations

Use the frozen orbit map, an unsigned 16-bit `blocked[cell]`, a byte occupancy
array and byte row/column loads, the selected complete-orbit stack, and actual
selected point indices. A cell counter is the number of unordered selected
point pairs whose entire maximal grid line contains that cell, including pair
endpoints. An unoccupied prospective point is blocked exactly when it completes
a collinear triple with an existing pair.

Push the points of one orbit in fixed order. Before each point, reject occupied
or blocked cells and row/column load above two. Add the new pair lines against
all previously selected points with primitive integer directions. This catches
old-old-new, old-new-new and new-new-new triples. If any point rejects, remove
all points inserted by this orbit in reverse order and decrement exactly the
pair lines involving each removed point. Pop repeats that operation for the
last accepted orbit. Type counters allow at most `(n-1)/2` four-orbits and one
diagonal pair. Rejection must preserve the entire prior state byte-for-byte.

For a valid target, at most `2*n` selected points yield at most `binom(2*n,2)`
pair contributions to any cell. At n79 this is 12,403, below 65,536. Therefore
uint16 counters suffice under exact updates, the target/type caps and checked
nonnegativity. This is a logical width bound, not permission to ignore overflow
or an actual process-memory measurement.

## Concrete branch choice and necessary pruning

The proposed first production traversal would enumerate the 39 main-diagonal
pairs as explicit independent slices. Start each slice by pushing its fixed
pair, then add only four-orbits; the anti-diagonal remains empty by construction.
This avoids interleaving diagonal choices and gives a clean declared scope.

At every node, recompute admissible unselected four-orbits against the current
state. The first implementation uses transactional push/pop probes, so every
MRV domain and axis occupancy comes from the same exact state. It deliberately
has no mutable cached domain counts needing an additional undo proof.

For each underfilled row, collect all admissible orbit IDs contributing to it
and each orbit's row multiplicity. Choose the row minimizing domain size, then
prefer larger deficit, then the frozen row-order rank. Visit **every** domain
orbit in the frozen orbit permutation. Do not impose a global increasing-orbit
ID rule together with MRV: a later underfilled row can require a lower ID, so
that combination can silently lose valid sets. Different insertion orders may
visit the same set; duplicates are allowed in the first correct traversal.

Let `r` be the required number of remaining four-orbits. Two sound prunes are:

- Fewer than `r` distinct admissible four-orbits remain anywhere.
- For an underfilled row, the sum of its largest at most `r` admissible orbit
  contributions is below its remaining load. This ignores interactions among
  orbits and therefore is an optimistic upper bound, suitable only for proving
  a shortfall. An empty domain is included as a special case.

A full extension must use only currently admissible orbits: invalidity under
adding selected points is monotone. It has exactly `r` remaining four-orbits,
so both shortfall prunes are necessary conditions. It must fill the chosen
underfilled row, hence contains at least one of its domain orbits. Branching
through all such choices preserves at least one path to every full extension.
At a full leaf require exactly `2*n` points and row/column load two, then the
same frozen family decoder/dual geometry checks and durable witness-before-
terminal publication. A limited tree traversal is incomplete; even trusted
restricted-family exhaustion is not a global or proof-checked UNSAT claim.

## Permutation and checkpoint identity before any production resume

A distinct near-quarter checkpoint schema must bind grid/target/family, exact
orbit-map digest, ordered diagonal slices, four-orbit permutation, row tie
permutation, prune-policy version, point insertion order, and all engine/model/
verifier/guard/entrypoint source hashes. Hashing only an unordered selected set
cannot establish the identity of a DFS frontier. User parameters may not
silently alter any of those fields on resume.

A proposed checkpoint records the current selected path and one frame per
ancestor/current node: chosen row, next domain cursor, domain digest, selected
child ID, and explicit node-entry/branch phase. Advance a cursor before entering
its child; record the entered child separately so the ancestor continuation
cannot replay or skip it accidentally. Publish only at documented consistent
boundaries after complete push/pop operations. A resume must reconstruct every
prefix state, rebuild each deterministic MRV domain, verify row/domain digest,
cursor range and parent-child relation, and reject any mismatch before visiting
a new node. Numeric node totals and phase flags must distinguish reconstitution
from newly entered nodes, so staged node limits do not double count prefixes.

Static orbit/permutation data may be regenerated only if their complete identity
matches. Keep old checkpoints untouched and use one linear parent-content-hash
chain, not a union of unvalidated frontiers. Bound identity metadata to 4 KiB
and the wire payload to 1 MiB before allocation/parsing. Persist atomically and
bind each receipt to parent/checkpoint hashes. Before any real continuation,
exhaustively test tiny uninterrupted versus staged runs at every node boundary,
including cancellation, corruption, reordered permutations, changed parameters,
already-terminal reuse and interrupted publication. **That serializer/resumer
is not implemented or approved by the current tiny prototype.**

## Proposed packed storage budget, not Python RSS

Using only accepted r28/r30 algebraic family sizes at n79: 1,521 four-orbits,
39 diagonal pairs, 1,560 variables, at most 6,162 stored point incidences, grid
6,241 cells, and depth at most 40 selected orbits. A uint16 suffices for grid
indices, orbit IDs, incidence offsets and row/domain cursors. Reserve 41 frames
including an outer/root frame. One explicit proposed layout is:

| Packed payload | Bytes at n79 |
| --- | ---: |
| Flat orbit point indices and offsets | 15,446 |
| By-row orbit IDs and offsets, incidence upper bound | 12,484 |
| Four/diagonal/row order permutations | 3,278 |
| Secant counters, occupancy, axis loads, selected points and orbit IDs | 19,277 |
| 41 frames: 195-byte admissibility bitmap plus 64-byte metadata each | 10,619 |
| One candidate scratch list and two row scratch arrays | 3,436 |
| Fixed numeric counters/phase flags | 64 |
| Explicit bounded identity manifest reserve | 4,096 |
| **Proposed packed live payload total** | **68,700** |

The budget excludes Python object headers, lists/dicts/tuples, interpreter and
imports, native/runtime/OS allocations, code, stacks, allocator fragmentation,
checkpoint serialization buffers, temporary geometry work and the host monitor.
The prototype uses Python containers around its packed geometry and does not
implement this complete packed layout. The 68,700-byte arithmetic is **not** an
RSS forecast, a proof of meeting 256 MiB, or a time/performance prediction.
Avoid retaining per-depth Python candidate objects, global histories or
unbounded caches merely because the packed payload is small. Recomputing pair
lines on pop avoids retaining a secant-update log; the conservative path update
work bound is `n*binom(2*n,2)`, or 979,837 cell increments at n79, with comparable
undo work. Traversing repeated nodes can still be prohibitively slow.

## Exact tiny evidence and allocation recommendation

`research/near_quarter_tiny_secants.py` permits **only n3/n5/n7**, with at most
10,000 nodes for its tiny traversal, and rejects n9/n79. It has no file writer,
production checkpoint, host guard integration or CLI route. Four tests pass in
0.748 seconds. The saved evidence is
`data/near-quarter-tiny-secants-evidence.json`.

Every pair of tiny grid points is checked against independent determinant line
membership. All 4/64/4,096 orbit subsets at n3/n5/n7 are compared against exact
brute-force geometry and family/type caps. Every valid partial state is freshly
rebuilt by pair/cell determinants after accepted pushes and pops; all 8/102/1,200
extensions are checked, and rejected mutations restore the prior snapshot.
There are 4/17/100 valid partial subsets and 1/0/0 full family subsets.

The tiny diagonal-first MRV traversal with both shortfall prunes matches a
separate complete family-cardinality geometric census under forward and reverse
diagonal/orbit/row permutations. It visits 2/5/17 tiny nodes, finds 1/0/0 full
sets, and changes its explicit order identity when permutations change. Tiny
node-limit status remains incomplete. These facts check the proposed branch
and prune mechanism as well as the state representation, but do not validate
production checkpoint/resume or predict large-grid progress.

Recommendation: independently review these frozen tiny sources/evidence first.
Then, only under a separate Lead allocation, implement the production packed
engine and checkpoint semantics, validate the published n71 fixture through a
controlled push/undo sequence, run tiny guarded witness/resource and resume
fault gates, and measure a bounded moderate-size pilot. No n79 implementation
or trial, full CNF/backend retry or resource-limit change is authorized here.
Retain the same 30-second/256-MiB host gates for any later initially authorized
pilot and at most one SAT allocation; all actual scheduling remains with the
supervisor. Exact geometry remains family-scoped and every witness requires
both independent validators and durable publication.
