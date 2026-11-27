# Independent r48 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 635,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `4f21b702c10bd4b6c645aad934f2e198c01474efd0a5d9a92d983c49410729f0` matches the independently reviewed r47 accepted frontier and 595,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `1c2a0e1eebee61e49baef5e08f96c90448c78402ef16dc26e90233efd8279ef1`; its identity, source and orbit hashes, counters and 21 frames were reconstructed with 35 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r47 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 10.918 | 10.928 | 57,248 | 258 |
| 2 | 10,000 | 10.835 | 10.845 | 50,192 | 259 |
| 3 | 10,000 | 11.161 | 11.170 | 50,864 | 268 |
| 4 | 10,000 | 11.337 | 11.346 | 50,976 | 270 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.396 seconds and supervisor elapsed 46.276 seconds.

Ledger SHA-256: `e03aaeff6a06a8423a1e5560af471f2ad0f390cb8a2ce2dc29680c86f5212f08`. Receipt SHA-256: `b299852b070b0a10f3a706b8325f5b129ccbe412c25d091b4eed32af85d27155`.
