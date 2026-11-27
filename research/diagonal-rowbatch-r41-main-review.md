# Independent r41 main chain review

The supervisor reports terminal completion with exit code 0; the chain stopped at `timeout`, incomplete, after five accepted invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). Four reached 20,000 nodes; the fifth reported cooperative timeout at 19,810. The cumulative row-batch count is 355,410; witness visits and certificate count are zero. This timeout does not establish infeasibility or novelty.

The fifth guard reports normal exit, clean cleanup, stable sources and return code 0; its accepted worker result is `timeout`, not an external guard wall-limit or resource rejection. The guard reserves one quarter of remaining time for publication and cleanup, explaining why cooperative timeout can occur before the outer 30-second gate. Do not infer a future safe 20,000-node quota from these measurements.

The initial digest `a56122200f318f54ff6c17ab5f3df56863c4d29b99b2820986cf05667f509f04` matches the independently reviewed r40 accepted frontier and 255,600-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `117c09355ab1eb2a373aaacfe015267943713c6a19318743eee919e24718c4b5`; its identity, source and orbit hashes, counters and 22 frames were reconstructed with 39 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r40 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Result | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---|---:|---:|---:|---:|
| 1 | 20,000 | node_limit | 21.667 | 21.677 | 57,408 | 506 |
| 2 | 20,000 | node_limit | 21.579 | 21.589 | 51,456 | 506 |
| 3 | 20,000 | node_limit | 21.863 | 21.872 | 51,584 | 501 |
| 4 | 20,000 | node_limit | 22.359 | 22.368 | 51,360 | 538 |
| 5 | 19,810 | timeout | 22.587 | 22.602 | 49,888 | 525 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 160 of 480 seconds; ledger elapsed 110.190 seconds and supervisor elapsed 110.727 seconds.

Ledger SHA-256: `267daf977b8dc02b13d746d634c40981f0f04fab71d6f2d1662677364f554178`. Receipt SHA-256: `1950047db838a851c89852fe9b301ce46ce7b5781599c0d563db1f6419e25717`.
