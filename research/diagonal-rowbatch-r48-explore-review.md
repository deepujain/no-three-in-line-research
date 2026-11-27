# Independent r48 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 24,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `d3c792c866533d4368677518d6322d7869a3e7659d912949605c2bbee56985be` matches the independently reviewed r47 accepted frontier and 22,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `0f24c6f62e7cf2d213ba19e1686d59e020139c0c880272718133ec259637a57b`; its identity, source and orbit hashes, counters and 23 frames were reconstructed with 41 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r47 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.267 | 1.277 | 56,992 | 32 |
| 2 | 1,000 | 1.190 | 1.200 | 57,552 | 30 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.522 seconds and supervisor elapsed 4.035 seconds.

Ledger SHA-256: `4b5f3c65e52bab68d4b99f38ca7418d01daa3c42f1d5450483e5de666c0eae04`. Receipt SHA-256: `b5b63e783e29413fd216c575ac8a14f9812c999c56493d051e34b4bde6e93d7b`.
