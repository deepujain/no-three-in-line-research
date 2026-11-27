# Independent design review: singleton migration by one-cell relocation

Verdict: PASS for design only. Reviewed `research/singleton-migration-one-cell-design-v1.md` (SHA-256 `9348e40a25c2c57a3bcbc117262cc93901f0b0ea0ff30309346ce240d40809b3`). This review uses symbolic reasoning and arithmetic only: no point input, fixture, geometry, implementation, allocation or search was examined or performed.

Removing one point p from a full row and inserting an empty q in the singleton row preserves the point count, distinctness and row capacity, while moving the singleton to the source row. There are exactly 2(n−1)^2 legal moves. The score identity U(P')=U(P)−d(p)+c(q)−h(p,q) correctly subtracts the old q-collinear pairs that contain p. Since c−h counts pairs retained after deletion and is nonnegative, pruning d(p)=0 cannot discard a strict gain. The proposed endpoint counts compute h exactly and the stated tie key is deterministic.

A failed same-load singleton test gives c(q)>=d(a), but migration compares c(q) against d(p)+h(p,q); it therefore does not certify this family. Every strict move removes a conflict through its source row, and that conflict occupies three distinct rows; its union with the destination occupies at most four. This is a support bound, not a four-row necessity claim or authorization to run a block optimizer.

For n=75, symbolic operation counts are C(149,3)=540,274 baseline triple tests and 74*C(149,2)=815,924 destination pair tests, totaling 1,356,198 determinant tests, plus at most 2*74^2=10,952 scalar candidate calculations. Independent validation needs separate accounting. These bounds do not imply a time or memory forecast. A stopped sweep cannot certify absence.

A completed negative excludes only this exact one-cell relocation family for the bound state; a strict result is a proposed relocation, with zero requiring independent full witness acceptance. Future work requires a separately reviewed permitted input, identity and source closure, independent score oracle, exact budgets, immutable failure handling, owned resource gate and new authorization. This review selects no fixture and authorizes no execution or old-family continuation.
