# Independent r44 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 16,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `40ca2a51fcdf9d2b5573bc06d6a5480543e8749649f8cd97d7a7b2aa726c40cf` matches the independently reviewed r43 accepted frontier and 14,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `365d98e16b651432a5092b6ad849d6a17e56ca02701794778343f40546119ed6`; its identity, source and orbit hashes, counters and 21 frames were reconstructed with 37 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r43 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.244 | 1.254 | 57,264 | 29 |
| 2 | 1,000 | 1.208 | 1.217 | 57,456 | 27 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.526 seconds and supervisor elapsed 4.082 seconds.

Ledger SHA-256: `664f0c51a480d571621b10827d278c9ac59c28c1908340acf6fad1295774f6ea`. Receipt SHA-256: `4907525bf183425ade1fff1dac3649b66aa077fe25ce82c72c2b627ab9442fab`.
