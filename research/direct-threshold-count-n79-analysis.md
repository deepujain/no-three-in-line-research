# r28 threshold census: first native-build recommendation

Recommend explicit thresholds `(7,7)` for the first separately guarded native build.
It removes the most auxiliaries among the nine reviewed choices while adding
5.8329% clauses. This is a count tradeoff, not a native-memory or search prediction.

The supervisor-owned count-only run completed with exit zero, 4.555947 seconds
inside the guard, 55,808 KiB sampled peak, 96 ordinary RSS samples and clean
one-sample cleanup (0.013747 seconds). It enumerated 411,545 C4 groups representing
1,644,284 full lines; the 187 support classes sum to 411,544 nonspecial groups.
No native Solver, full CNF, formula hash, search result or witness was constructed.

| AM2 / guarded AM1 cutoff | Clauses | Auxiliaries | Variables | Literals |
| --- | ---: | ---: | ---: | ---: |
| 5 / 5 | 2,072,304 | 474,148 | 475,708 | 5,649,431 |
| 5 / 6 | 2,074,205 | 467,459 | 469,019 | 5,655,222 |
| 5 / 7 | 2,078,239 | 462,453 | 464,013 | 5,667,400 |
| 6 / 5 | 2,099,812 | 364,116 | 365,676 | 5,924,511 |
| 6 / 6 | 2,101,713 | 357,427 | 358,987 | 5,930,302 |
| 6 / 7 | 2,105,747 | 352,421 | 353,981 | 5,942,480 |
| 7 / 5 | 2,187,244 | 291,256 | 292,816 | 6,317,955 |
| 7 / 6 | 2,189,145 | 284,567 | 286,127 | 6,323,746 |
| 7 / 7 | 2,193,179 | 279,561 | 281,121 | 6,335,924 |

Relative to `(5,5)`, `(7,7)` adds 120,875 clauses (+5.8329%) and 686,493
literals (+12.1515%), while removing 194,587 variables (-40.9047%) and the same
number of auxiliaries (-41.0393%). The 1,560 real orbit variables are unchanged.
The `(5,5)` histogram totals exactly reproduce the previous complete row-floor
build: 2,072,304 clauses and 475,708 variables.

The locally expensive two-guard direct expansions are uncommon: 44 groups
at light support six and 38 at support seven. Moving from `(7,6)` to `(7,7)`
therefore adds only 4,034 clauses while removing another 5,006 auxiliaries.
`(6,6)` is a lower-clause alternative (2,101,713 clauses / 358,987 variables),
but the recommendation prioritizes the larger variable reduction after the
prior encoding failed immediately upon native solve allocation. This does not
authorize a fallback, repeat, cap increase, search, or concurrent SAT allocation.

All ten report source hashes match the current files; the receipt entrypoint
hash matches the report. The helper and adapter source remain unchanged.

| Bound source | SHA-256 |
| --- | --- |
| `cli_entrypoint_sha256` | `da2bd2585ebe76ac624cfd608b56b7401ad9bfbe8656b49005777c5f8f4b1d03` |
| `compact_source_sha256` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| `guard_source_sha256` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |
| `line_generator_sha256` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
| `model_source_sha256` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| `original_guard_utilities_sha256` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
| `preflight_source_sha256` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `row_quota_source_sha256` | `dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704` |
| `threshold_source_sha256` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |
| `verifier_source_sha256` | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |

| Saved evidence | SHA-256 |
| --- | --- |
| `data/direct-threshold-count-n79.json` | `04f21439703c082022d0f63e1dd6d6e6a1500de8e8b465c8d89d489cf52a5fea` |
| `data/experiments/r28-direct-threshold-count-n79.json` | `5f81cf61ff1837b73feb2713794c6839898281cc862ab5f7bb53e9bddf968d56` |

The next measurement is build-only `(7,7)` using the approved preflight,
at most 30 seconds and 256 MiB, owned by the supervisor with one SAT/native
allocation maximum. Its actual peak, cleanup, complete counts, source bindings
and full formula hash must be inspected before any solve is considered.
Count-only resource usage does not forecast that native build or solve footprint.

Analysis: Research Software Engineer, `gpt-6.1-sol`, reasoning `high`.
This worker performed only saved-report inspection and arithmetic; no new
large-grid enumeration, build or search.
