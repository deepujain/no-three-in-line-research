# Independent r46 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 555,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `f7446aff442cdd123043fe2dd0838421eae44af57ed09e35569b0a35957f06cf` matches the independently reviewed r45 accepted frontier and 515,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `04100e2a48deb05800b2c228e9af194350733a4e579371ba67e57d17169fa85d`; its identity, source and orbit hashes, counters and 23 frames were reconstructed with 39 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r45 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.356 | 11.367 | 57,408 | 251 |
| 2 | 10,000 | 11.073 | 11.082 | 49,936 | 269 |
| 3 | 10,000 | 11.299 | 11.308 | 50,368 | 257 |
| 4 | 10,000 | 11.614 | 11.623 | 50,176 | 255 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 45.457 seconds and supervisor elapsed 46.359 seconds.

Ledger SHA-256: `dc360c069420de3ded1c1fa54ae6668ef66a1855f7e6a88e47098828ab1fca79`. Receipt SHA-256: `b5862c7cfdad8ad6a056c775a4003ebecf524632bd7e000ea237c9264f6a9642`.
