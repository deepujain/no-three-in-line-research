# Independent r42 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 12,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `af5449352782d08d91114e8b2c3d60b6941df852b92aeec2ba2ad20525a33704` matches the independently reviewed r41 accepted frontier and 10,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `a620bbeaf3687f66e6645cec86f1b3557c0eb1495767bc55489281806402eb3a`; its identity, source and orbit hashes, counters and 22 frames were reconstructed with 37 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r41 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.388 | 1.398 | 57,344 | 29 |
| 2 | 1,000 | 1.247 | 1.257 | 57,488 | 28 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.712 seconds and supervisor elapsed 4.086 seconds.

Ledger SHA-256: `aa423e7ee2a192bff2d87f9f5d2620c2c1760adb267523d640df32f7a334d233`. Receipt SHA-256: `5c7ab0c71794c18f17bf0f0dd35d27125a781bea1ab7115c9dd2bfe69ea5cc00`.
