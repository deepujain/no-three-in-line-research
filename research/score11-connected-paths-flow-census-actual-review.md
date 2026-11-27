# Connected paths 10/12/16 actual review

Decision: accept the complete negative for all 32 declared connected patches and curtail further expansion of this branch on the present evidence. No automatic length-18 or larger allocation is justified.

The source-pinned run completed 1668 cell checks and all 32 cases, with zero eligible patches. Normal 30-second/256-MiB gate: zero exit, clean cleanup, no trigger/monitor error, outer elapsed 0.1914315 seconds, peak sampled RSS 47392 KiB. Source pins and complete counters were independently verified.

Independent geometry recomputation tested all 1668 freed cells against retained-point pairs by integer determinants. There are 360 safe cell records and 1308 blocked records; explicit retained-pair proofs are saved for every blocked cell. For each deletion length k, exactly k-2 cells are safe, of which precisely one is outside the original source and k-3 are original readditions. Thus the elementary bound (158-k)+(k-2)=156 already excludes both targets.

Every saved primal flow was also independently checked for unique safe-cell membership and row/column capacities. Each saved cut capacity was recomputed directly from original network capacities and its reachable row/column sets, and equals the feasible flow value k-2. This independently verifies maximality without rerunning the implementation's flow algorithm. All final cardinality upper bounds are exactly 156.

Evidence: `data/score11-connected-paths-flow-census-independent-actual-audit.json`, SHA-256 `457b6f113e3e0c6bb16683bfb040be5613aaad630962b680faaf0cec1173b418`. Independent audit took 0.294 seconds. Earlier incidence arithmetic proves coverage of all 8/10/14 windows containing the chosen cover at lengths 10/12/16. The result closes only those 32 patches of the pinned source, not other covers, lengths, arbitrary deletions or unrestricted n79. The valid incumbent remains 156.
