# Independent r39 exploration chain review

The terminal supervisor receipt reports completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after three accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 4,100, with zero witness visits and no certificates. This limit does not establish infeasibility or novelty.

The pinned initial digest `b0a57450d1707c126add258450272c96c5b99e3baa910358c40a6f616102a599` matches the r38 predecessor report and its 1,100-node count. The receipt identity, limits, current source hashes, invocation report hashes, ordered expected/accepted/published digest links, counter deltas, empty witness directories, and closed owner marker checked out. The final frontier bytes hash to `1887a821fe719160774d111f165ed3400ed17b2a213a72d424c2c57e49025911`; its identity, source and orbit hashes, counters, and 22-frame stack were structurally reconstructed, with 38 selected pairs. Intermediate checkpoint bytes have been overwritten, so their recorded hash links were checked but their bytes could not be rehashed independently; the r38 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.329 | 1.398 | 57,328 | 25 |
| 2 | 1,000 | 1.495 | 1.501 | 57,888 | 23 |
| 3 | 1,000 | 1.405 | 1.434 | 57,840 | 22 |

Each guard reports exited, clean cleanup, stable sources, and a successful return. RSS was sampled and is not a kernel hard limit. The chain reserved 96 of 180 seconds; ledger elapsed 4.439 seconds and supervisor elapsed 6.210 seconds.

Ledger SHA-256: `be88c1167ce3fdc4af1a3bf442566c07d168f4ce131b3998d9cea05c061f5d1c`. Supervisor receipt SHA-256: `84c8e7f4861307964f1c87b20b99a6e76ab7233b860ffd9585925100f6f5eeb5`.
