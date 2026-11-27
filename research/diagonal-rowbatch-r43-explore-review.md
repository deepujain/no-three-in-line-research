# Independent r43 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after two accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 14,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `a620bbeaf3687f66e6645cec86f1b3557c0eb1495767bc55489281806402eb3a` matches the independently reviewed r42 accepted frontier and 12,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `40ca2a51fcdf9d2b5573bc06d6a5480543e8749649f8cd97d7a7b2aa726c40cf`; its identity, source and orbit hashes, counters and 21 frames were reconstructed with 36 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r42 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.223 | 1.233 | 56,944 | 27 |
| 2 | 1,000 | 1.195 | 1.204 | 57,248 | 28 |

Both guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 64 of 120 seconds; ledger elapsed 2.495 seconds and supervisor elapsed 4.076 seconds.

Ledger SHA-256: `ca7d39d8894f758053a890537c397871be22f540692f0e330e0247d21a2979ba`. Receipt SHA-256: `8a5ea11044f716f170b3c77291bd937fe5798f88d70c93ea0c5f4248a7001049`.
