# Independent r45 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 18,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `365d98e16b651432a5092b6ad849d6a17e56ca02701794778343f40546119ed6` matches the independently reviewed r44 accepted frontier and 16,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `fdf771006868ce0e7cffe0c24eff4ad4bed539f3c07a96f1a5b2e5679d09547d`; its identity, source and orbit hashes, counters and 23 frames were reconstructed with 41 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r44 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.221 | 1.232 | 57,040 | 27 |
| 2 | 1,000 | 1.237 | 1.247 | 57,456 | 28 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.535 seconds and supervisor elapsed 4.086 seconds.

Ledger SHA-256: `357da202dee0891f416d98c3678abe7e5cdcbb6d94c683ba76bdebc5d690924b`. Receipt SHA-256: `eb3a0c6d95d41f9eb09683532f899fb0ca03554a1dd728eab93199cac41ea655`.
