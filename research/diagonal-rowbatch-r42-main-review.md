# Independent r42 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 395,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `117c09355ab1eb2a373aaacfe015267943713c6a19318743eee919e24718c4b5` matches the independently reviewed r41 accepted timeout frontier and 355,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `ddd13f3ec0e9b405c3a60a2a0d4d04575b3141af29cdeee472904a7696e76595`; its identity, source and orbit hashes, counters and 24 frames were reconstructed with 38 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r41 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.176 | 11.186 | 57,520 | 268 |
| 2 | 10,000 | 11.233 | 11.242 | 57,824 | 271 |
| 3 | 10,000 | 11.214 | 11.223 | 58,016 | 265 |
| 4 | 10,000 | 10.972 | 10.982 | 57,984 | 263 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.702 seconds and supervisor elapsed 46.334 seconds.

Ledger SHA-256: `b5e6c7a0498ed64601c3a335d7b1c2584ef928ef49c2894db287e7985556fcd5`. Receipt SHA-256: `1fa604f5640a3cf93fe313c3f38235cd48281e80a9288a09fdbe7a038da9f6af`.
