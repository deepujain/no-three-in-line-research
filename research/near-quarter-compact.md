# Shared off-diagonal capacities for the near-quarter family

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. This separate encoding variant was coordinated with the independent mathematician before implementation. Its source is `src/near_quarter_compact.py`; the original `src/near_quarter_model.py` and guarded preflight stay frozen. No n79 enumeration, construction or solver search is part of this work.

The original n79 construction stopped safely at the unchanged 256-MiB sampled RSS gate. Its saved report, `data/near-quarter-preflight-n79.json`, records a complete preliminary count of 823,090 half-turn weighted lines, then partial construction of 2,560,687 clauses using 1,086,443 variable IDs. The guard stopped it after 8.3027 seconds at 263,440 KiB sampled guard-plus-worker RSS. It has no complete CNF hash or solver result. Those partial counts do not estimate the full model size.

## Exact factorization

Let `C(L)` be the selected contribution from off-diagonal four-point orbits on maximal line `L`. Every such orbit is invariant under quarter turns, so rotating the line preserves its coefficient for each four-orbit. Thus `C(L)=C(RL)=C(R²L)=C(R³L)` as weighted expressions in the orbit variables.

Every line other than the main diagonal meets that diagonal in at most one cell. Its exceptional contribution is either zero or one diagonal-pair indicator `d`. The line constraint is exactly `C+d<=2`, equivalent to the shared `C<=2` plus `d=>C<=1`. Across a full C4 line orbit the half-turn partners use the same diagonal-pair indicator; at most two distinct indicators remain. These conditions retain each exceptional contribution even though the off-diagonal expression is shared. They do not identify the entire near-quarter assignment under quarter turns.

The main and anti-diagonal form one special line orbit. Off-diagonal four-orbits avoid both. The anti-diagonal is empty; the main diagonal has contribution `2*sum(d)`, exactly two under the model's global exactly-one diagonal-pair condition. Its capacity is therefore redundant only together with that global cardinality condition.

## Implemented CNF

Let `H` contain coefficient-two off-diagonal variables and `U` coefficient-one variables. Any coefficient above two is forced false defensively. A common capacity emits all negative pairs within `H` and between `H` and `U`, plus an at-most-two constraint on `U`. For at most five light variables, direct negative triples require no auxiliaries. Longer supports use the existing audited sequential cardinality encoding.

For every relevant diagonal indicator `d`, every heavy variable gets `not d or not h`. Conditional at-most-one on light variables uses direct guarded negative pairs for at most five variables. For longer supports it gates a single existing sequential at-most-one CNF. With one indicator that indicator is the gate; with two, a fresh gate receives `d=>g` for both. Every at-most-one clause receives the negative gate literal. Reverse gate equivalence is unnecessary for projected satisfiability: a true indicator forces the counter active, while with no selected indicator the gate may be false.

Guard constraints remain even when the common at-most-two constraint is tautological: `C=2*x` still needs `not d or not x`, and `C=x+y` still needs `not d or not x or not y`. A support with total possible contribution at most one has tautological conditional capacity.

`line_groups` streams the lexicographically least full-line representative in each complete C4 line orbit without a global deduplication table. It explicitly checks that off-diagonal multiplicities agree across all rotations, non-special lines contain at most one diagonal cell and the orbit has at most two distinct diagonal guards. The special diagonal orbit is marked explicitly. `streamed_cnf` retains both global cardinality equalities before using that special-case omission. All conditional counter clauses receive the gate literal, with fresh auxiliaries from the common ID pool.

## Complete tiny comparisons

Four tests pass in `.venv`, exercising all orbit assignments for grids 3, 5 and 7 against the original CNF and an independent exact determinant geometry checker. The geometry-only factorization check includes all assignments with exactly one diagonal pair, even when the global four-orbit cardinality is wrong. The CNF check includes every assignment and both global cardinality conditions. Additional synthetic supports test coefficients one, two and three; zero, one and two diagonal guards; the tautological-common-capacity edge cases; and longer supports that activate the gated sequential counter. A line-partition test independently checks all full-geometry lines, multiplicities and special diagonals.

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_compact.py -v
```

The reproducible complete counts are saved in `data/near-quarter-compact-tiny-counts.json`. Variables include orbit IDs and cardinality auxiliaries. Auxiliary counts subtract the orbit-ID count. Clauses are counted before native solver simplification.

| Grid | Half-turn lines / C4 groups | Original clauses | Compact clauses | Original auxiliaries | Compact auxiliaries |
|---|---|---|---|---|---|
| 3 | 6 / 3 | 2 | 2 | 0 | 0 |
| 5 | 20 / 10 | 60 | 32 | 24 | 8 |
| 7 | 62 / 31 | 270 | 180 | 102 | 38 |

The independent mathematician approved the frozen source and tests in `research/near-quarter-compact-review.md`, independently reran all four tests, reconstructed full line groups from pair-generated integer equations for grids 3, 5, 7 and 9, and checked 1,476 synthetic encodings across 150,525 fixed decision assignments, including coefficients one/two/three, long counters and zero through three guards. No correction remains outstanding.

These tiny reductions do not establish that a complete n79 model fits the unchanged 30-second/256-MiB gate. A separate build-only preflight integration is documented in `research/near-quarter-compact-preflight.md`; its independent source review and real-host tiny gate precede a separately scheduled allocation for any n79 build. There is no solver search path. The original failed build remains reproducible under its original source and report hashes.

| Frozen artifact | SHA-256 |
|---|---|
| `src/near_quarter_compact.py` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| `tests/test_near_quarter_compact.py` | `a55eaed7f25d8a690763a43bc4d32cdcc48ff681d69055cb714e4823e105ccde` |
| `data/near-quarter-compact-tiny-counts.json` | `80a853fa936434052673daacf449aa273eb33225b79065f7fdca6f34874863fb` |

The mathematical factorization and counter reasoning are also recorded independently in `research/near-quarter-compaction-proof.md`.
