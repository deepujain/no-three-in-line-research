# Independent review of diagonal-reflection secant DFS

Reviewer: Mathematical Reviewer, `gpt-6-astra`, reasoning `high`, 2026-11-27.
Core mathematical correctness is approved at the frozen identities below.
This does not approve an unguarded n79 run: a separate resource/artifact runner
and measured preflight remain necessary. Only tiny correctness checks were run.

* `research/diagonal_secant_dfs.py`:
  `6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7`
* `tests/test_diagonal_secant_dfs.py`:
  `d49010fd93b2b9379e915acc2701e5d5332d13569aa7b7d03765dc8887c8540a`

## Family and traversal completeness

Every reflection-invariant no-three set of size `2*n-1` has exactly one
diagonal singleton: parity requires an odd number, while the main-diagonal
capacity permits at most two. Its remaining points form `n-1` off-diagonal
reflection pairs. Row capacities imply exactly one deficient row; reflection
gives the identical deficient column index. Enumerating the declared singleton
index `t` and deficit index `d` therefore covers exactly those declared slices.
The implementation permits both `t=d` and `t!=d` and does not silently impose
half-turn or quarter-turn invariance.

For each slice the singleton is inserted first. All later candidates are the
complete list of distinct pairs `((i,j),(j,i))`, with `i<j`. The exact row and
column targets are `2-[index=d]`. At an unfinished node, every valid completion
must add some unselected pair touching the chosen underfilled row. Any pair
belonging to such a completion is currently admissible: adding points can
only consume capacity and create additional secants. Enumerating every
admissible pair for that row is therefore complete. Choosing the row with the
fewest candidates only changes order. A row with zero candidates safely ends
the branch. The implementation imposes no unproved increasing-ID restriction
across dynamically selected rows; different insertion orders can revisit the
same final set and are explicitly counted as duplicate witness visits.

Each accepted pair adds two points, so depth is finite. A filled row-target
vector supplies exactly `2*n-1` points; the code separately checks columns,
point count, and reflection. Every leaf is checked by both exact integer
geometry algorithms before callback publication. No leaf is accepted merely
because row targets were met.

## Secant invariant and rollback

`blocked[p]` counts every unordered selected-point pair whose complete grid
line passes through `p`. `grid_line` divides by the exact gcd, walks backward
to the grid boundary, then forward along the entire primitive direction.
Horizontal, vertical, negative-slope, and reversed endpoint orders are covered.

A candidate point is rejected if occupied, at an axis limit, or on an existing
secant. Otherwise each newly formed pair contributes one increment at every
cell on its full line. Inserting the second point of a reflection orbit after
the first therefore also detects a triple containing both new points and an
old point. Removing the last inserted point subtracts exactly its pair-line
contributions with all remaining points. This is the inverse update; it cannot
affect a pair of older points. Failed tentative orbit insertion removes all
points inserted by that attempt, leaving existing frame lengths unchanged.
Successful insertion records one frame, and `pop` removes that frame in reverse
point order. Recursive branches use `finally` to restore the selected pair set
and the state. No secant approximation or omitted slope was found.

The current implementation uses Python integer lists, not the packed uint16
arrays hypothesized in the proposal. Its correctness is not dependent on a
16-bit overflow assumption, and the proposal's packed-array byte figures must
not be presented as measured implementation RSS.

## Independent verification

All three author tests passed independently in 0.662 seconds. They compare
complete witness sets at n3/n4 with independent cell-subset enumeration and at
n5 with reflection-orbit enumeration. Their exhaustive reachable-state tests
reconstruct every cell's secant count using determinants after accepted and
rejected pushes and after undo, comparing occupancy, points, row/column loads,
frames, and exact restoration. They also exercise node/time cutoffs and invalid
inputs.

A separate reviewer test compared `grid_line` in both endpoint orders with
direct determinant membership for every pair at n2 through n6: 2,184 ordered
pair checks all passed.

Another independent reviewer enumerator constructed reflection edges directly,
chose exactly `n-1` edges plus each singleton, and classified determinant-valid
sets by the actual deficient row. Every individual `(d,t)` slice matched the
DFS callback results, not just their union. Counts were:

| n | Distinct valid sets | DFS nodes | Witness visits including duplicates |
|---|---:|---:|---:|
| 2 | 2 | 6 | 2 |
| 3 | 4 | 26 | 5 |
| 4 | 10 | 108 | 17 |
| 5 | 16 | 415 | 35 |

Separate cutoffs of 1, 2, 3, and 5 nodes respected their global budget and never
reported all slices exhausted unless every declared slice had been processed.
Timeout/node-limit states remain incomplete; unstarted slices are not silently
marked exhausted. Completed traversal is always restricted to the declared
reflection slices, and witness visits must not be reported as unique sets.

## Operational limits before n79

The core has cooperative time and node checks, not a host RSS or hard wall-time
guard. Candidate expansion, verification, and callbacks can run between time
checks. Its CLI writes witness/result files directly and checks the source hash
only at completion. These are acceptable for the reviewed tiny correctness
exercise but insufficient for a killable production research worker that must
preserve trustworthy artifacts and provenance.

A separate reviewed wrapper should bind source and verifier identities before
execution, apply the unchanged real host resource guard, atomically persist
verified witnesses before terminal reporting, and make host interruption
override exhaustion claims. It should distinguish restricted-slice exhaustion,
cutoff, invalid artifacts, and resource failure. A successful tiny host test
and a separately scheduled measured preflight remain required before n79 use.
No measured n79 feasibility, search result, proof of nonexistence, or novelty
claim follows from this core review.
