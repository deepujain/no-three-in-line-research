# Independent r41 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after three accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 10,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `c36c8a74608f39dd5e40095e194765f1197e8fe452293e6953f2d7310b412164` matches the independently reviewed r40 accepted frontier and 7,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `af5449352782d08d91114e8b2c3d60b6941df852b92aeec2ba2ad20525a33704`; its identity, source and orbit hashes, counters and 20 frames were reconstructed with 36 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r40 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.259 | 1.269 | 57,392 | 28 |
| 2 | 1,000 | 1.214 | 1.224 | 57,456 | 28 |
| 3 | 1,000 | 1.278 | 1.287 | 57,552 | 29 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 96 of 180 seconds; ledger elapsed 3.838 seconds and supervisor elapsed 4.088 seconds.

Ledger SHA-256: `702a46045d31e107c7ba9c46f41819573bbcc94334eefb631d2727f7511cd732`. Receipt SHA-256: `7bcb01a166aec207ddca38fcbc5443935ffce59d3556e09434b7c1aacbdbca0d`.
