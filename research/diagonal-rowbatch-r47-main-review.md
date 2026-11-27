# Independent r47 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 595,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `04100e2a48deb05800b2c228e9af194350733a4e579371ba67e57d17169fa85d` matches the independently reviewed r46 accepted frontier and 555,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `4f21b702c10bd4b6c645aad934f2e198c01474efd0a5d9a92d983c49410729f0`; its identity, source and orbit hashes, counters and 22 frames were reconstructed with 39 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r46 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.112 | 11.122 | 57,504 | 270 |
| 2 | 10,000 | 11.078 | 11.088 | 57,760 | 273 |
| 3 | 10,000 | 11.258 | 11.267 | 57,712 | 262 |
| 4 | 10,000 | 10.947 | 10.956 | 48,896 | 253 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.502 seconds and supervisor elapsed 46.342 seconds.

Ledger SHA-256: `c9dea238182b47ffa605632a7386f95fb1b93e82f14d10b867766b2296749519`. Receipt SHA-256: `b44f89ff65485dee094dab50f6928de1631b5a779de25984b40cfcb33daccf8f`.
