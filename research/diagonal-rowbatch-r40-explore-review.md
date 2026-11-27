# Independent r40 exploration chain review

The supervisor reports terminal completion with exit code 0. The ledger ended at `invocation_limit`, incomplete, after three accepted 1,000-node invocations in the declared n=79 main-diagonal-reflection slice (d,t)=(0,1). The cumulative row-batch count is 7,100; witness visits and certificate count are zero. The limit does not establish infeasibility or novelty.

The initial digest `1887a821fe719160774d111f165ed3400ed17b2a213a72d424c2c57e49025911` matches the independently reviewed r39 accepted frontier and 4,100-node count. Receipt identity and limits, current source hashes, report hashes, ordered expected/accepted/published links, counter deltas, empty witness directories and closed owner marker checked out. The final frontier hashes to `c36c8a74608f39dd5e40095e194765f1197e8fe452293e6953f2d7310b412164`; its identity, source and orbit hashes, counters and 21 frames were reconstructed with 37 selected pairs. Intermediate checkpoint bytes were overwritten, so their digest links were checked but those bytes could not be independently rehashed; r39 predecessor bytes were independently checked before replacement.

| Invocation | Nodes | Helper seconds | Wrapper seconds | Peak sampled RSS KiB | RSS samples |
|---|---:|---:|---:|---:|---:|
| 1 | 1,000 | 1.283 | 1.294 | 57,024 | 28 |
| 2 | 1,000 | 1.397 | 1.410 | 57,152 | 26 |
| 3 | 1,000 | 1.260 | 1.270 | 57,232 | 28 |

All guards report exited, clean cleanup, stable sources and return code 0. RSS is sampled, not a kernel hard limit. The chain reserved 96 of 180 seconds; ledger elapsed 4.072 seconds and supervisor elapsed 6.123 seconds.

Ledger SHA-256: `d448ad337187758532bfd7dd910f705e435718a5fbe093a9bf68385494c72928`. Receipt SHA-256: `ef148f4b1fd60d3326bafe4c9c7d4c33952bd79596a19a5231889ad21fccd735`.
