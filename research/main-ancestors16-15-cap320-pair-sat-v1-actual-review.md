# Main ancestors16/15 capacity320 actual review

Decision: accept both stages as **conditional scoped native UNSAT**. Full masks, pair decisions and formula counts were independently audited; no solver replay or independent UNSAT certificate was checked.

The job completed cleanly in1.618275 seconds with68,976 KiB sampled peak RSS. All49 receipt pins, local and packed manifests, parent actual audit and accepted checkpoint heads match. Both stages are complete, with zero returned models, ternary cuts or witnesses.

Independent quarter-turn orbit generation and exact integer geometry reproduced all mask decisions. Depth16 retains66 points and has224 admissible orbits; depth15 retains62 and has256. All57,616 completed pair decisions were independently recomputed without packed geometry or readonly-probe helpers. Depth16 has24,976 pairs,5,185 exclusions and19,791 compatible pairs; exclusion witnesses comprise1,201 row-capacity violations and3,984 determinant triples. Depth15 has32,640 pairs,6,146 exclusions and26,494 compatible pairs; witnesses comprise1,375 row-capacity violations and4,771 determinant triples. Both exact exclusion lists equal the reports.

Independent incidence construction with the same pinned cardinality library reproduced depth16's1,451 variables/2,581 degree clauses/6,068 literal entries and depth15's1,749/3,107/7,316. Including binary cuts yields respectively7,766/9,253 final clauses and16,438/19,608 literal entries. These checked formulas support the reported native results but do not independently certify UNSAT.

Audit: `data/main-ancestors16-15-cap320-pair-sat-v1-independent-actual-audit.json`, SHA-256 `819a813869d14441c3f00b119478cb42d4c3564de90249b4489a9709d7542c27`.

The exclusions apply only to the corresponding exact retained near-quarter prefixes, conditional on native solver correctness. No global bound, frontier mutation, automatic integration or broader allocation follows.
