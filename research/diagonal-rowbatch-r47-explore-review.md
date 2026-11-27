# Independent r47 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 22,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `1f98e3b4d861bd12f96c2206605000ce477a8181f3bd97a2ee2920f9377640cd` matches the independently reviewed r46 accepted frontier and 20,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `d3c792c866533d4368677518d6322d7869a3e7659d912949605c2bbee56985be`; its identity, source and orbit hashes, counters and 19 frames were reconstructed with 35 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r46 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.290 | 1.300 | 57,024 | 28 |
| 2 | 1,000 | 1.296 | 1.306 | 57,424 | 29 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.659 seconds and supervisor elapsed 4.081 seconds.

Ledger SHA-256: `cfad8024cc2cdd118d1a85850c46e6d8d891a3be18bbb2a25386ee5c25593620`. Receipt SHA-256: `e877e3a49d916ea2950be4ee6aac1aac187cc4168bf16745709795ed60cfd7df`.
