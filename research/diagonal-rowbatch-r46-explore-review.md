# Independent r46 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 20,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `fdf771006868ce0e7cffe0c24eff4ad4bed539f3c07a96f1a5b2e5679d09547d` matches the independently reviewed r45 accepted frontier and 18,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `1f98e3b4d861bd12f96c2206605000ce477a8181f3bd97a2ee2920f9377640cd`; its identity, source and orbit hashes, counters and 23 frames were reconstructed with 41 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r45 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.337 | 1.351 | 57,200 | 19 |
| 2 | 1,000 | 1.284 | 1.293 | 49,520 | 28 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.705 seconds and supervisor elapsed 4.095 seconds.

Ledger SHA-256: `82a34c102b4cf172b22d60517a4a77087008951adfd9da6be1da1e9c056f80be`. Receipt SHA-256: `4e84818e02a5f37eea897065783b2d83aa26bbdc2f7b91e4e2d07fe8db9c1d83`.
