# Independent r45 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 515,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `c4561a520d35b3d824a1d3b849d980614591381917a22b5880a56f1a56631002` matches the independently reviewed r44 accepted frontier and 475,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `f7446aff442cdd123043fe2dd0838421eae44af57ed09e35569b0a35957f06cf`; its identity, source and orbit hashes, counters and 25 frames were reconstructed with 41 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r44 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.231 | 11.241 | 57,408 | 263 |
| 2 | 10,000 | 11.186 | 11.196 | 57,872 | 267 |
| 3 | 10,000 | 11.052 | 11.062 | 58,032 | 261 |
| 4 | 10,000 | 11.288 | 11.297 | 58,080 | 273 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.869 seconds and supervisor elapsed 46.326 seconds.

Ledger SHA-256: `4da3e9dc2c8a7a28512ed09ba1ff2416b9b42c4c10c367acac7d7f142dc44d6f`. Receipt SHA-256: `5a26dc5f5befc0911d407c720b8c5efe00e35d8bb04c45053c3e9c7a79e7c3d6`.
