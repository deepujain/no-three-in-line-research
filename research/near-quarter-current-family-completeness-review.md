# Read-only review of the current family's coverage and pruning

No new mathematical completeness defect or hidden additional restriction was found in the current row-batch source and retained proofs. This is a scoped source/proof assessment, not a machine-checked exhaustive proof or an n79 feasibility result. No geometry, tests, numerical search, source edits, or live-run polling were performed.

The reviewed current implementation has core `f257045276d1247fde814fae01fe0a470233c477e228c37b6d3209fd367439ae`, packed state `860711b8e83d0f3e738ebeedc535e0953e903a01551b1e22ad3bb20f49fa3b11`, cursor `738a545abc1909bc126ca916d225dfef90bea8b974142a5885cb9e2f632e2422`, and checkpoint `88ce7a7a9b3d756427f60382b1b1316f30755e3a1a49a9a51367c6fcb27e6dec`. Core literals bind radius helper `647ae1379eb89711707f9900d68a2aba1861839751bdb22f15e9618d1f5cda66` and readonly admission helper `2b9f51496f80c78881643724029e48cd9987b1428bdffbce7736806d790f5c7d`. Source review covered model construction, admission, scan bounds, row choice, cursor enumeration, batch push/pop, target/leaf checks and radius obstruction.

## Exact scope

For n=79, the family consists of 39 full off-both-diagonals quarter-turn orbits plus one main-diagonal antipodal pair. The anti-diagonal, including the center, is empty. It therefore has 158 points, half-turn symmetry, and an exceptional pair that prevents exact quarter-turn symmetry. This is stricter than arbitrary half-turn symmetry, but it is exactly the declared near-quarter-turn family. The packed orbit builder enumerates the same full off-diagonal map as the reviewed model; it adds no octant, increasing-ID, or single-orientation restriction.

The known n71 fixture recorded in `near-quarter-fixture-review.md` belongs to this same family and independently verifies 142 points. It refutes a blanket claim that the family is vacuous for odd grids or for the n congruent to 3 modulo 4 class. It does not establish any n79 solution or show that a particular n79 diagonal slice is feasible. This review relied on that retained fixture evidence and did not reconstruct its geometry.

This branch directly searches 158-point full targets. It is not an independent unrestricted 157-point search. That limitation is part of the declared family/target, rather than an added pruning rule.

## Why row batches retain every family completion

No-three-in-line implies at most two points per row and column. At the 2n target, summing n row capacities forces exactly two in every row; likewise for columns. Thus requiring each selected deficient row to be filled exactly introduces no additional restriction.

Fix a valid completion F of a selected prefix S. The deterministic row choice depends on S and the frozen orders. Its deficit is one or two. The members of F minus S that touch this row contribute positive integer weights summing exactly to the deficit. They therefore form either a matching-weight singleton or, for deficit two, an unordered pair of weight-one orbits. The cursor generates all these alternatives, once each in local order, subject only to the available remaining-orbit count. Every candidate from F is individually admissible, and its whole batch succeeds because each insertion is a subset of valid F. Induction preserves at least one path to F. Conversely, a different row-filling batch cannot reach F without overfilling that row or selecting an orbit outside F; this establishes uniqueness within a slice without a global ID cutoff.

## Why the implemented prunes are necessary

The readonly predicate checks all triple partitions by zero, one, two, or three candidate points. Existing secant blockers handle two old points, candidate-pair line scans handle one old point, and integer determinants handle three new points. Axis/family checks are the same declared conditions. For a coherent valid prefix, rejected candidate geometry cannot become valid by adding more points. Consequently every valid completion uses only the complete individually admissible mask.

If the mask contains fewer orbits than the remaining target count, completion is impossible. The row-capacity upper bound `2*min(c2,r)+min(c1,max(0,r-c2))` chooses the largest available weights among at most r additions. It may overestimate jointly realizable capacity but cannot underestimate a valid completion's row contribution. MRV merely chooses the next row; it is not an extra acceptance condition.

The radius graph uses reflected row loads, with central demand halved because each central-axis orbit contributes two central-row points. Each admissible four-orbit contributes one unit to two distinct radius vertices, so any completion uses edges summing to the residual demand. Each connected component must have even demand, and each bipartite component must have equal demand sums on its two sides. These are necessary conditions only. The source does not require a connected solution, a Hamiltonian path, or a bipartite solution; odd cycles and disconnected cycles are allowed. Parallel geometric orbit edges remain distinct in the admissibility mask; adjacency bits merge them only for connectivity/coloring. No missing multiplicity assumption was found.

The exact target cap is consistent with 39 four-orbits plus one pair. Full-target row/column equality is implied by valid geometry and cardinality; the explicit leaf checks add validation, not a different target. Capacity overflow or corrupted state raises an error and cannot be accepted as a mathematical prune.

## Remaining interpretation limits

At the last independently audited main frontier, 3,261 nodes had been visited inside diagonal ID 1522, with no leaf or completed slice. Main declaration includes all 39 diagonal choices, but depth-first traversal advances only after fully exhausting the current slice. It therefore has not yet covered the other choices at that audited point. The separate middle-1541 probe explores another declared slice without implying it is more promising. Visited partial-state counts are neither a percentage of family coverage nor evidence that a full solution is nearby.

Retained checkpoint parsing and replay validate the current path and local consistency; compact checkpoints alone do not prove every historically skipped subtree was exhausted. Accepted source-bound execution provenance remains necessary. No unrestricted infeasibility statement, full-family exhaustion, or n79 vacuity conclusion follows from these partial runs. Nothing found in this review warrants stopping the approved frozen-source main window or expanding its protocol.
