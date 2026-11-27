# Central-orbit finite repair: actual review

Accepted complete negative for the pinned centered n71 fixture after deleting `(10,35),(35,10),(35,60),(60,35)` and adding five four-orbits. This closes only that deletion case, including exact readdition, not other deletions or global n79 existence.

Independent arithmetic reconstructed all 25 oriented radius edges on 0,25,36,37,38,39. Enumerating all 53,130 five-edge subsets reproduced the exact 547 reported degree-feasible choices, including 51 readditions. For every one of the 24 blocked edges, its three distinct reported points belong to the retained set plus that orbit, at least one is newly added, and the integer determinant is zero. Every reported candidate contains its named blocked edge. Thus all 547 are invalid without further final geometry calls.

Current source pins equal the experiment's sources-before map; sources were unchanged. The 30s/256MiB owned gate exited zero with clean cleanup in 0.342129542s (outer 0.342153875s), peak sampled 47,024KiB. Output contains only the complete report, no witness.

Detailed audit: `data/n71-central547-independent-audit.json`, SHA256 `98e894799ea7ff4d3bdb6d5e8e17504bbf22dbe712989182929a5a2c2eea29a3`. Report SHA256 `4997583e953a8130bab1273878a3ae98ecfbeaee76dd238df1aa021746a44fa1`.
