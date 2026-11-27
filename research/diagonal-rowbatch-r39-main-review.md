# Independent r39 main chain review

The terminal supervisor receipt reports completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after twelve accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 135,600, with zero witness visits and no certificates. This limit does not establish infeasibility or novelty.

The pinned initial digest `da8a67ae72536a91f0ac27224e9dd23ddf1554619d2b0aef5553bbb827c66d7b` matches the r38 predecessor report and its 15,600-node count. The receipt identity, limits, current source hashes, invocation report hashes, ordered expected/accepted/published digest links, counter deltas, empty witness directories, and closed owner marker checked out. The final frontier bytes hash to `9fec85b074fdb9edb1b27663a533e1d9104690ef0f0bb6044c211b6a2201b078`; its identity, source and orbit hashes, counters, and 28-frame stack were structurally reconstructed, with 46 selected pairs. Intermediate checkpoint bytes have been overwritten, so their recorded hash links were checked but their bytes could not be rehashed independently; the r38 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.334 | 11.355 | 57,472 | 198 |
| 2 | 10,000 | 11.876 | 11.908 | 57,648 | 238 |
| 3 | 10,000 | 12.528 | 12.565 | 50,736 | 221 |
| 4 | 10,000 | 11.962 | 12.023 | 50,928 | 224 |
| 5 | 10,000 | 12.112 | 12.122 | 51,088 | 277 |
| 6 | 10,000 | 11.769 | 11.801 | 51,008 | 251 |
| 7 | 10,000 | 11.234 | 11.252 | 48,352 | 257 |
| 8 | 10,000 | 11.510 | 11.518 | 48,528 | 228 |
| 9 | 10,000 | 11.565 | 11.628 | 48,608 | 213 |
| 10 | 10,000 | 11.408 | 11.432 | 48,624 | 260 |
| 11 | 10,000 | 11.482 | 11.496 | 48,544 | 249 |
| 12 | 10,000 | 10.862 | 10.878 | 48,096 | 249 |

Each guard reports exited, clean cleanup, stable sources, and a successful return. RSS was sampled and is not a kernel hard limit. The chain reserved 384 of 480 seconds; ledger elapsed 140.377 seconds and supervisor elapsed 141.863 seconds.

Ledger SHA-256: `48f421791e265d4de98f0f4db642294c1f7ef19d98675ee10e0228583792576c`. Supervisor receipt SHA-256: `cd08b3e31e1b4ab7b734acc2d9c2bb73c77d27fc4de668e8fafc1ed0bccf1924`.
