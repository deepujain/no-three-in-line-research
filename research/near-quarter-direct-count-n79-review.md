# Independent r28 threshold-count evidence review

The recorded count result is accepted within its count-only scope. A selected
`(7,7)` native build under the existing limits is justified as a measurement
experiment. No lower RSS, solver safety or completed search is inferred.
Reviewer: Mathematical Reviewer, `gpt-6-astra`, high. This audit used saved
reports, source hashes and arithmetic only; it generated no n79 geometry,
formula, native solver or search and did not replay the count run.

## Evidence identities and terminal state

| File | SHA-256 |
| --- | --- |
| `data/direct-threshold-count-n79.json` | `04f21439703c082022d0f63e1dd6d6e6a1500de8e8b465c8d89d489cf52a5fea` |
| `data/experiments/r28-direct-threshold-count-n79.json` | `5f81cf61ff1837b73feb2713794c6839898281cc862ab5f7bb53e9bddf968d56` |
| `research/near_quarter_direct_preflight.py` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `src/lazy_sat.py` | `da2bd2585ebe76ac624cfd608b56b7401ad9bfbe8656b49005777c5f8f4b1d03` |

All ten recorded source hashes match their current files and the reviewed
adapter/encoder/helper identities. The receipt binds the final dispatcher,
n79, count mode, explicit `(7,7)` selection, 30 seconds and 256 MiB. Both CLI
and worker returned zero. The helper recorded 96 RSS samples, a peak of
55,808 KiB = 54.5 MiB, elapsed time 4.555947125 seconds, and clean one-sample
cleanup taking 0.013747375 seconds. The supervisor receipt elapsed time was
6.166601459 seconds; these are different timing scopes.

The terminal report marks count/histogram completion and leaves native-solver
construction, CNF completion, build completion and search false. No clauses
were added to a solver. Both full-model and prefix digests are null. This is
consistent with the reviewed count-only path and does not supply a formula
digest for a later solver.

## Independent arithmetic audit

The saved histogram has 187 distinct classes totaling 411,544 weighted groups,
plus one special-diagonal group. Reported totals are 411,545 C4 groups and
1,644,284 represented full lines. The `(5,5)` aggregate reproduces the prior
independently audited r23 build's 2,072,304 clauses and 475,708 variables, as
well as its group and line totals. The prior report's SHA is
`f1c6bc7e104443b0262ec582fb42ee4f6753487819cd320761ac9c2b7fe1ab00`.

I recomputed all nine reported clause, auxiliary and literal totals from the
saved histogram using separate closed-form arithmetic. No encoder or geometry
generator was called. The fixed contribution is 3,157 clauses, 38 auxiliaries
and 234,538 literals, including the diagonal equality and reviewed row floors.
Each group adds its heavy binary clauses, forced unary clauses, and the
applicable direct or sequential light costs. For the sequential supports used
here, AM2 contributes `5L-12` clauses, `2L-4` auxiliaries and `11L-26` literals;
gated AM1 contributes `3L-4` clauses, `L-1` auxiliaries and `9L-12` literals,
plus the two-guard gate when needed. Smaller supports use direct binomial
costs. These totals exactly match every saved candidate row. This arithmetic
cross-check supplements the source-bound installed-emission measurement; it
does not independently re-enumerate the geometry histogram or audit native
counter source for arbitrary support sizes.

| Thresholds | Clauses | Variables | Literals |
| --- | ---: | ---: | ---: |
| `(5,5)` | 2,072,304 | 475,708 | 5,649,431 |
| `(5,6)` | 2,074,205 | 469,019 | 5,655,222 |
| `(5,7)` | 2,078,239 | 464,013 | 5,667,400 |
| `(6,5)` | 2,099,812 | 365,676 | 5,924,511 |
| `(6,6)` | 2,101,713 | 358,987 | 5,930,302 |
| `(6,7)` | 2,105,747 | 353,981 | 5,942,480 |
| `(7,5)` | 2,187,244 | 292,816 | 6,317,955 |
| `(7,6)` | 2,189,145 | 286,127 | 6,323,746 |
| `(7,7)` | 2,193,179 | 281,121 | 6,335,924 |

The histogram contains 13,754 support-six groups and 7,286 support-seven
groups. Their two-guard subsets have only 44 and 38 groups respectively.
Thus the previously noted expensive local two-guard expansions do not dominate
this particular recorded aggregate.

## Selected measurement and limits

I concur with the engineer's `(7,7)` build-only recommendation. It is the
largest variable reduction among the measured alternatives: 194,587 fewer
variables, or 40.9047%, with 120,875 more clauses (5.8329%) and 686,493 more
literals (12.1515%) than `(5,5)`. Moving from `(7,6)` to `(7,7)` removes another
5,006 auxiliaries for 4,034 additional clauses. These are concrete tradeoffs
for a measured native build, not a memory model. `(6,6)` is also a plausible
future alternative, but this review does not schedule or preauthorize retries.

The selected build must retain explicit configuration, the reviewed source
bindings, existing 30-second/256-MiB helper limits and no solve call. Its full
stream should match 2,193,179 clauses, 281,121 variables and 6,335,924 literals
and produce its own header-bound digest. Only that separate result can
establish build-time resource behavior. Even a successful build cannot show
that a subsequent native solve fits memory; the preceding row-floor solve
failed after construction. There is no new witness, exhaustion, SAT, UNSAT,
novelty or unrestricted infeasibility conclusion.
