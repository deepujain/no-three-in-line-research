# Independent r44 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 475,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `00509116c301f87ab5784b5e5f2bc2e701dd8a9fc054bd1502b2b2758cf45a68` matches the independently reviewed r43 accepted frontier and 435,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `c4561a520d35b3d824a1d3b849d980614591381917a22b5880a56f1a56631002`; its identity, source and orbit hashes, counters and 20 frames were reconstructed with 36 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r43 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.123 | 11.133 | 57,136 | 256 |
| 2 | 10,000 | 11.206 | 11.216 | 57,504 | 266 |
| 3 | 10,000 | 10.977 | 10.986 | 57,648 | 247 |
| 4 | 10,000 | 11.131 | 11.139 | 50,800 | 260 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.544 seconds and supervisor elapsed 46.353 seconds.

Ledger SHA-256: `ee71397ddabc72297f67461725bbe8627e6bf0c17da67db3a5191b6c9dcb77ba`. Receipt SHA-256: `dc465aa949ab73a6f4f8a3afdc0fb23a004f3d45903a0b1b123c30c9f65c7f3f`.
