# Independent r43 main chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after four accepted 10,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,0). The cumulative row-batch count is 435,410; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `ddd13f3ec0e9b405c3a60a2a0d4d04575b3141af29cdeee472904a7696e76595` matches the independently reviewed r42 accepted frontier and 395,410-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `00509116c301f87ab5784b5e5f2bc2e701dd8a9fc054bd1502b2b2758cf45a68`; its identity, source and orbit hashes, counters and 24 frames were reconstructed with 40 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r42 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 10,000 | 11.121 | 11.131 | 57,488 | 253 |
| 2 | 10,000 | 11.120 | 11.130 | 50,352 | 264 |
| 3 | 10,000 | 11.231 | 11.240 | 50,608 | 261 |
| 4 | 10,000 | 11.069 | 11.079 | 50,880 | 260 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 128 of 180 seconds; ledger elapsed 44.653 seconds and supervisor elapsed 46.340 seconds.

Ledger SHA-256: `7420e08f879913a0d2f1671676414a503e13c7a107094d33d259d52e7aa71293`. Receipt SHA-256: `6714a4a7d1931d2b32c9b8e7a8c291a0a3455d74aedfff2b3c3746ac9e1a1042`.
