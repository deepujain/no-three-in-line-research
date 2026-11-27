# Main ancestors18/17/16 actual review

Decision: accept depth18 and depth17 as **conditional scoped native UNSAT**, and depth16 as an **incomplete capacity stop with no verdict**. No solver replay or independent UNSAT certificate was checked.

The job ended cleanly in1.128913 seconds with61,344 KiB sampled peak RSS. The guard's `worker_error`/return2 is the expected CLI exit for the reported mask-capacity cutoff; there was no monitor error, trigger, cleanup failure, or resource-limit violation. All40 receipt pins, current local/packed manifests, the parent audit, and accepted checkpoint heads match.

All three complete masks were independently regenerated from quarter-turn orbits and exact integer slope/determinant geometry, without packed-state or readonly-probe helpers. Depth18 retains74 points and has136 admissible orbits; depth17 retains70 and has181; depth16 retains66 and has224. The last full mask exceeds the reviewed200-variable limit, so no pairs or solver work were attempted there and the overall report correctly remains incomplete.

Every completed pair decision was independently recomputed. Depth18 has9,180 pairs,2,307 exclusions and6,873 compatible pairs; the exclusions have649 row-capacity and1,658 explicit determinant witnesses. Depth17 has16,290 pairs,3,697 exclusions and12,593 compatible pairs; the exclusions have902 row-capacity and2,795 determinant witnesses. Both exclusion lists match exactly.

Independently reconstructed degree formulas match their reported counts: depth18 has754 variables,1,338 clauses and3,124 literal entries; depth17 has1,129 variables,2,004 clauses and4,702 literal entries. Adding binary cuts gives respectively3,645/5,701 final clauses and7,738/12,096 final literal entries. Both native solvers reported UNSAT with zero returned models and zero ternary cuts. Formula reconstruction uses the same pinned cardinality encoder but independent incidence construction; it is not a second solver or proof check.

Audit: `data/main-ancestors18-17-16-pair-sat-v1-independent-actual-audit.json`, SHA-256 `3a7452a2e56219ee94da2b9a3d2d6286ca3805299313872af6fa3228345d376c`.

The successful negative conclusions apply only to their exact retained near-quarter prefixes, conditional on native solver correctness. Depth16 remains open at this resource cutoff. No frontier was modified, and no global bound or automatic broader run follows.
