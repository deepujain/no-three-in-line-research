# Hard-retention target 157, deletion cap 6: actual-result review

Decision: accept the terminal result as **solver-reported scoped UNSAT**, with independently checked geometric clauses and reconstructed formula counts. No independent UNSAT proof or second-backend confirmation was performed. This is stronger empirical evidence for this fixed source neighborhood, not a global upper bound.

The run completed cleanly in 2.182904 seconds at a sampled peak of 76,336 KiB. All 28 receipt pins match their current files. The report records 87 candidate models and 87 complete conflict scans, zero partial scans, 2,655 new cuts, zero loaded old cuts, and no witness or improved invalid candidate. These full-run counters retain reviewed source-pinned execution provenance; prior models were not retained or independently replayed.

The independent actual audit checked every saved cut directly using integer determinants, without production geometry helpers. All 2,655 cuts are distinct collinear triples of distinct legal board cells, with no overlap with the 11 independently enumerated original source triples. Thus every geometric clause excludes only an invalid configuration. The final saved candidate was independently checked: 157 distinct points, axis capacities at most two, 152 retained source points, 6 effective source deletions, 5 new points, and exactly 21 collinear triples. All its triples appear in the saved new cuts; it is explicitly invalid.

A separate construction from the mathematical constraints, using the same pinned sequential-counter library but no production formula helpers, reproduced 55,851 axis variables and 99,060 axis clauses, then 56,763 total variables, 1,970 retention clauses, 11 source clauses, 101,041 initial clauses, and 239,663 initial literal entries. The final formula has 103,696 clauses and 247,628 literal entries. Its canonical clause-multiset SHA-256 is `b0ec345e31c74fff30ea208d3cd8043b242704f30080e10fc262c4d3e9b4a270`. Counts and valid clauses support the encoding audit, but do not independently establish native UNSAT.

The scope is every 157-point subset of the 79 by 79 board with at most two points per row and column, retaining at least 152 of the fixed invalid 158-point source. It has no symmetry or patch restriction. Conditional on the reported UNSAT result, valid 158-point sets with at most six effective source deletions are also excluded: any such set differs from the invalid source, so it contains a new point; deleting that point yields a valid 157-point set with the same retained source count. This implication does not expand the deletion cap or establish a board-wide bound.

Audit: `data/score11-hard-retention157-d6-independent-actual-audit.json`, SHA-256 `51bd1bfdb9f23a1c1f50829d3bcd007e0e742e88d326c99c66fde27f2165785d`.

No experiment allocation follows automatically from this review. A larger deletion neighborhood or a second-backend confirmation requires a separately bounded allocation from the coordinator.
