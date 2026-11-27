# Remove the global four-orbit counter using exact row loads

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. The separate variant is `src/near_quarter_row_quota.py`. It retains the approved compact line capacities and exactly-one diagonal-pair condition, replacing only the large global four-orbit equality. All original model, compact, guard, preflight and solve sources are unchanged. There is no scheduling adapter, large preflight or search path for this variant yet. No n79 enumeration, model count, build or search was performed during this work.

## Concrete trigger

Root's first compact n79 solve trial, `data/near-quarter-compact-solve-n79.json`, stopped at the unchanged sampled RSS gate after 15.1913 seconds and 262,400 KiB peak sampled guard-plus-worker memory over 313 samples. Its complete 2,300,453-clause build had taken 12.7759 seconds and matched the approved formula hash before entering solve. The terminal report correctly cleared accepted build/search completion and model hash, retaining the complete formula hash only as a prefix diagnostic. It has no result or witness. Repeating that branch or increasing its cap is not part of this proposal.

## Equivalence proof

Write `n=2m+1`. Keep exactly one selected main-diagonal pair and every compact geometric line capacity. Every original row therefore contains at most two selected points. Every allowed orbit is half-turn invariant, so row `i` and row `n-1-i` have identical occupancy. It suffices to add a lower bound of two to each representative row `0..m`, including the center.

These lower bounds and the existing upper bounds force exactly two points on every row, hence exactly `2n` selected points. If `F` is the number of selected off-diagonal four-orbits, the unchanged exactly-one diagonal pair gives `4F+2=2n`, so `F=m`. This recovers the omitted global four-orbit equality.

Conversely, the original `F=m` and exactly-one diagonal pair give exactly `2n` points. With `n` rows each bounded above by two, every row must contain exactly two points and hence meets every new floor. The two encodings have precisely the same projected orbit assignments. The special main/anti-diagonal omission remains justified by the unchanged exactly-one diagonal-pair condition. No new blanket quarter-turn quotient is introduced.

The independent mathematician gave explicit proof-level approval before implementation. The underlying family and capacity formulation remain those documented in [Prellberg, arXiv 2602.07751 §3](https://arxiv.org/html/2602.07751#S3); the row-counter replacement is the engineering inference proved here, not a reported novelty claim.

## Zero-auxiliary positive clauses

A noncentral representative row contains `n-2` distinct four-orbit variables and its one diagonal-pair variable, all with coefficient one. Distinctness follows because two cells of the same four-orbit can share a noncentral row only on one of the excluded long diagonals. Thus the row has `n-1=2m` light indicators. At least two must be true.

For light variables `u_1..u_k`, the exact CNF for at least two is one positive clause omitting each variable: `OR(U minus {u_i})` for each `i`. Zero selected variables violate every clause; exactly one selected variable violates the clause omitting it; two or more satisfy every clause. No auxiliary is needed.

The center row has `m` off-diagonal orbit indicators with coefficient two and no diagonal variable, so its floor is one positive OR. The implementation also has an exhaustively tested general positive-weight helper: coefficients at least two appear in every clause as heavy alternatives; fewer than two light variables require a heavy alternative. This handles empty supports and unit clauses exactly.

For n79 the row-floor arithmetic is therefore exactly 3,043 clauses and 234,273 literal occurrences, with zero auxiliaries. This is a closed-form calculation, not a measured n79 model count.

## Tiny complete evidence

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_row_quota.py -v
```

Four tests pass: all weighted-helper assignments for support lengths zero through five with coefficients one/two/three; every n3/5/7 orbit assignment checked against actual representative/full row loads and half-turn symmetry; arithmetic equivalence to the original cardinalities plus every full line capacity; and projected CNF equivalence to the frozen compact model and an independent exact determinant checker on every n3/5/7 assignment. Tiny SAT calls only fix complete real decision assignments to check existential auxiliary semantics; they do not search for new configurations.

Complete counts for n3/5/7/9 are saved in `data/near-quarter-row-quota-tiny-counts.json`. The n9 case counts clauses only. Counts precede native solver simplification.

| Grid | Compact clauses | Row-quota clauses | Compact auxiliaries | Row-quota auxiliaries |
|---|---|---|---|---|
| 3 | 2 | 4 | 0 | 0 |
| 5 | 32 | 25 | 8 | 0 |
| 7 | 180 | 127 | 38 | 2 |
| 9 | 531 | 372 | 171 | 75 |

The n3 increase is recorded explicitly: replacing a unit global equality by row floors introduces duplicate necessary units. The intended benefit is removal of the larger equality counters. For n7, the global four-orbit equality alone has 72 clauses and 36 auxiliaries; its replacement has 19 clauses and no auxiliaries. The remaining two auxiliaries belong to the unchanged diagonal-pair equality.

The approved published n71 fixture was also evaluated as a fixed assignment in `data/near-quarter-row-quota-n71-fixed.json`: its 35 four-orbits and one diagonal pair expand to the same 142 points, every row has load two, and all 2,451 new row-floor clauses pass. This check constructed no line groups or full n71 CNF and performed no decision search. Existing independent fixture geometry verification remains separately documented.

## Algebraic cost forecast and remaining gate

The installed PySAT `CardEnc.equals` delegates both lower and upper bounds to the requested sequential encoding. Its installed documentation cites Carsten Sinz, *Towards an Optimal CNF Encoding of Boolean Cardinality Constraints*, CP 2005. On the measured tiny interior cases, an equality over `N` variables at bound `K` uses `4K(N-K)` clauses and `2K(N-K)` auxiliaries. This formula has special-case exceptions at bounds zero, one, `N-1` and `N`; it is not asserted without qualification.

Conditional on that interior sequential-counter cost formula for the installed native encoder, removing the n79 `N=1521, K=39` equality saves 231,192 clauses and 115,596 auxiliaries. Adding the 3,043 row-floor clauses to the prior complete compact counts gives an **algebraic forecast** of 2,072,304 clauses and 475,708 total variable IDs. This is not an observed n79 count or RSS result; the native encoder's general implementation has not been independently audited here. The saved tiny report separates observed tiny counts from algebraic n79 row-floor arithmetic.

The independent mathematician approved the frozen source and tests in `research/near-quarter-row-quota-review.md`, independently reran all four tests, recomputed the tiny complete costs for n3/5/7/9 and checked another 231 interior sequential-equality cases for sizes 4 through 24. Those additional tiny cases agree with the stated formula; the general native-implementation caveat remains. No source correction is outstanding.

This should reduce stored formula and variable state, but long positive row clauses change propagation and may change learned-clause growth or solve time. Neither the tiny reductions nor the forecast establishes that a solve fits 256 MiB. The same 30-second/256-MiB guarded complete-build preflight, then separate reviewed solve allocation, remains required. No alternate backend or cap increase is proposed. Source approval does not replace the separate preflight-integration review and measured large-build gate.

| Frozen artifact | SHA-256 |
|---|---|
| `src/near_quarter_row_quota.py` | `dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704` |
| `tests/test_near_quarter_row_quota.py` | `4f50dcc697eb520e3a49cce69d9fdc25a6d948b63e048dacf64548d92ce66a7c` |
| `data/near-quarter-row-quota-tiny-counts.json` | `afb048b7390a82bc06b109ab39263832651e218b5526e6ef7f39c70da89c83e1` |
| `data/near-quarter-row-quota-n71-fixed.json` | `df38f66a80735e362a23b2c1ca773818db7060d6fff438944032a75a5585b115` |
