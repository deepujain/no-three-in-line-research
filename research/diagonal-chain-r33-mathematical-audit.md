# Independent r33 terminal chain audit

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). This audit read saved
reports, receipts, source bytes and final checkpoints only. It performed no
n79 construction, traversal replay, enumeration, search or benchmark.

Both chains terminate at their invocation limit with `complete=false`, zero
witness visits and empty saved witness directories. Neither declared slice is
exhausted. These are bounded incomplete diagonal-reflection search records,
not infeasibility results or estimates of remaining coverage.

| Quantity | Main `(d,t)=(0,0)` | Exploration `(d,t)=(0,1)` |
| --- | ---: | ---: |
| Accepted invocations | 16 | 3 |
| New nodes per invocation | 20,000 | 5,000 |
| Starting cumulative nodes | 47,000 | 6,000 |
| New nodes in chain | 320,000 | 15,000 |
| Final cumulative nodes | 367,000 | 21,000 |
| Reserved / allocated seconds | 512 / 600 | 96 / 180 |
| Chain elapsed seconds | 319.128744042 | 14.247142667 |
| Supervisor receipt elapsed seconds | 320.150182583 | 14.299210958 |
| Helper elapsed range, seconds | 19.366085458–20.860956000 | 4.648237625–4.737805250 |
| Sampled RSS peak range, KiB | 48,256–56,784 | 56,144–56,656 |
| Total RSS samples | 7,568 | 323 |

All 19 report bytes match the ledger's report hashes. Every invocation's
expected/predecessor digest matches the prior accepted digest, and its
accepted/published/worker checkpoint digests agree. The initial digest and
starting counters match the respective r32 predecessor reports. All node
deltas equal the declared cap and worker delta; cumulative and per-slice
counters agree, witness deltas stay zero, and slice index remains zero.
All eight chain source bindings and seven guard-report bindings match the
current frozen files. The CLI arguments, allocations, limits and source hash
match the supervisor receipts, which both record completed exit zero.

Every helper reports normal exit, clean cleanup, no monitor/cleanup error,
stable sources, positive samples, sampled RSS within 256 MiB and elapsed time
below 30 seconds. Each invocation reserves 32 seconds without reclamation;
aggregate reservations and actual elapsed times remain within their allocations.
Launch windows preserve 60 seconds. These are sampled/cooperative observations,
not guarantees against future transient resource overshoot.

Both actual final checkpoint hashes equal the last accepted digest and owner
marker digest; markers are closed and identify the proper ledgers. Checkpoints
bind n79, their declared slices, the frozen branch/order/core-source identities,
the last predecessor, the final counters, and nonempty incomplete frontiers.
Historical checkpoint bytes were replaced by later accepted invocations, so
their recorded digest links were checked but those prior bytes could not be
independently rehashed. Frontier geometry was not reconstructed in this audit.
Hash/counter consistency is an audit of trusted execution, not a proof certificate
of the entire visited tree. The frozen one-orbit DFS may revisit equivalent
selected sets; its node counters are work counts, not unique configurations.

## Artifact identities

| Artifact | SHA-256 |
| --- | --- |
| Main ledger | `a3597ffb5bb7f62bbbdce4881e80ac89d1707c23e92ac915c316ce7d08db13d5` |
| Main supervisor receipt | `f695871c9143ad63b92d651b91ca71c4db83344303be38428759ecb299479ee8` |
| Main r32 predecessor report | `fed44ba27960f0d53dd38de824bec5086178767b9faf25c54e0506c043d47522` |
| Main final checkpoint | `16521df87cdace216f43d06ea0abfe491daa251804070a21a275fbda194ae50c` |
| Exploration ledger | `ff49ddbd6477d25c7a95fb130b2f680d9a7484337a1e6e86a0beb28459955ef9` |
| Exploration supervisor receipt | `f6cf21798da85d34d077cd8a11a0b3a0b57914c2f6854007f8aab2fce052a86f` |
| Exploration r32 predecessor report | `99e0b69ff3e56aa1bac7a2faa7507a685cc0e20514418dd2fa417684c6ddd08d` |
| Exploration final checkpoint | `b5f6d047e1ecda0c0bb0bdd1e79ed25175bdc542f10abbc0b9a252a45d2c5b16` |
| Chain source | `20ee2caeeb820ee1d66a7a437a01218e371179b75bcfda39458142e3c20ddd9a` |
| CLI source | `435d902f50d756b2ee3d40866b9bf814ca7aa8c3a66bcb59cacd8a42d4128784` |

The two hash-bound ledgers enumerate all individually checked invocation report
hashes and continuation links. This reviewer did not independently observe the
past process lifecycle or execute a fresh host process audit.
