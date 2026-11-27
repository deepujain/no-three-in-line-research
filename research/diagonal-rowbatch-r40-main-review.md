# Independent r40 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after twelve accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 255,600; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `9fec85b074fdb9edb1b27663a533e1d9104690ef0f0bb6044c211b6a2201b078` matches the independently reviewed r39 accepted frontier and 135,600-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `a56122200f318f54ff6c17ab5f3df56863c4d29b99b2820986cf05667f509f04`; its identity, source and orbit hashes, counters and 21 frames were reconstructed with 36 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r39 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.125 | 11.136 | 57,360 | 245 |
| 2 | 10,000 | 11.052 | 11.062 | 52,848 | 260 |
| 3 | 10,000 | 11.076 | 11.085 | 52,752 | 260 |
| 4 | 10,000 | 10.790 | 10.799 | 52,752 | 248 |
| 5 | 10,000 | 10.962 | 10.971 | 53,040 | 255 |
| 6 | 10,000 | 10.977 | 10.994 | 52,816 | 250 |
| 7 | 10,000 | 11.028 | 11.039 | 52,320 | 256 |
| 8 | 10,000 | 10.880 | 10.890 | 49,168 | 258 |
| 9 | 10,000 | 10.912 | 10.921 | 49,088 | 261 |
| 10 | 10,000 | 11.032 | 11.041 | 49,104 | 261 |
| 11 | 10,000 | 10.785 | 10.794 | 49,056 | 256 |
| 12 | 10,000 | 10.657 | 10.666 | 49,200 | 247 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 384 of 480 seconds; ledger elapsed 131.553 seconds and supervisor elapsed 132.876 seconds.

Ledger SHA-256: `9a09e78b6bb79c9fc61ac23ba6b86b522e45b75df01c19ce49c9e4c064985a2c`. Receipt SHA-256: `ca0c4e2732659708e4904f00b2efa72a708ada5b551fc6806dd3403886b5525b`.
