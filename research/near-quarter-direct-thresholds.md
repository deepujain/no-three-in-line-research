# Direct small-capacity thresholds: analytical and tiny evidence

Status: separate configurable variant and tiny evidence independently reviewed
and approved. No n79 geometry, CNF, native build or search was run for this
branch. No historical encoder, preflight, solver or helper source was changed. The
separate preflight adapter later adds one isolated CLI route. Model setting: `gpt-6.1-sol`, reasoning `high`.

The preceding supervisor-run row-floor solve reached the expected complete
formula and then exceeded the unchanged RSS gate immediately in native solve:
9.25897 seconds total, 9.08874 seconds construction, 282,640 KiB sampled peak,
211 samples, and clean two-sample 0.062-second cleanup. It produced no result
or witness. More time does not address that observed memory failure, and this
branch adds no cap increase or identical retry. It makes no alternative-backend
recommendation without measured resource evidence.

`src/near_quarter_direct_thresholds.py` keeps the reviewed row floors, exactly
one diagonal pair, full C4 line groups, heavy multiplicity rules and special
main/anti-diagonal omission. It introduces immutable `CapacityThresholds` with
independent `atmost_two` and `conditional_atmost_one` cutoffs, each an integer
from zero through seven. Defaults are `(7,7)`; `(5,5)` exactly reproduces the
historical row-floor clause stream and auxiliary IDs. The independent cutoffs
permit `(6,5)`, `(7,5)`, `(5,6)`, `(6,6)`, etc., without source edits. The
variant metadata and model header bind both explicit thresholds and the new
source hash; its formula identity is distinct from historical headers even
when the clauses happen to match.

## Equivalence argument

Write the common off-diagonal load as `C=sum(w_i*x_i)`. The target remains
`C<=2` and, for every diagonal guard `d`, `d=>C<=1`.

The unchanged heavy rules force every coefficient above two false, exclude
pairs of coefficient-two variables, exclude a coefficient-two variable with
any light variable, and force every coefficient-two variable false when a
diagonal guard is active. It remains only to encode the coefficient-one set.

For light support `L`, `C_light<=2` is exactly the conjunction of one negative
clause for every triple: any violating assignment contains a selected triple,
and an assignment with at most two selected variables violates none. Each
`d=>C_light<=1` is exactly one clause `(-d,-a,-b)` for every light pair `(a,b)`.
If every guard is false all such clauses hold; if any guard is true they
exclude every selected pair. Both direct encodings use zero auxiliaries.

Above either cutoff the variant retains the original existential sequential
construction. For multiple guards its shared gate has implications `d=>gate`
and the gated AM1 counter. An active guard forces the counter active; if all
guards are false, choosing the gate false satisfies that part without
constraining the light variables. Thus direct and sequential branches have
identical projections onto the real indicators for every threshold. Combined
with the previously reviewed row-floor cardinality argument and unchanged
line-group factorization, the complete family remains equivalent.

## Exact changed-support costs

The table shows a common capacity with only light variables, counting AM2 plus
all guarded AM1 requirements together. Heavy/forced-false clauses are identical
between variants and add no auxiliaries.

| Light support | Guards | Baseline `(5,5)` clauses/aux | Direct at this support clauses/aux | Clause delta | Aux removed |
| --- | --- | --- | --- | --- | --- |
| 6 | 0 | 18 / 8 | 20 / 0 | +2 | 8 |
| 6 | 1 | 32 / 13 | 35 / 0 | +3 | 13 |
| 6 | 2 | 34 / 14 | 50 / 0 | +16 | 14 |
| 7 | 0 | 23 / 10 | 35 / 0 | +12 | 10 |
| 7 | 1 | 40 / 16 | 56 / 0 | +16 | 16 |
| 7 | 2 | 42 / 17 | 77 / 0 | +35 | 17 |

For independent choices, direct AM2 costs `binom(L,3)` clauses and zero
auxiliaries. At supports six/seven the baseline AM2 costs 18/8 and 23/10.
Direct guarded AM1 costs `G*binom(L,2)` clauses and zero auxiliaries. At supports
six/seven, the baseline guarded AM1 costs 14/5 and 17/6 for one guard, or 16/6
and 19/7 for two guards (including the shared gate and its implications).

Thus moving only the AM2 cutoff can avoid the more expensive two-guard direct
pair expansion. The per-support data include all nine cutoff pairs in
`{5,6,7}^2`, literal counts and deltas. The local tradeoff is not always a modest
clause increase: support seven with two guards adds 83.3% more clauses for that
group. Variable reduction alone cannot predict Glucose resident memory,
propagation costs or performance.

`research/direct_threshold_estimates.py` computes these algebraic expressions
and compares them to installed PySAT clause emission. The interior observed
sequential patterns are AM2 `5L-12` clauses/`2L-4` auxiliaries for `L>=4`, and
AM1 `3L-4`/`L-1` for `L>=3`, with explicitly handled trivial/near-trivial edges.
There are 1,170 successful algebra/emission cross-checks through support 12,
including guards 0/1/2 and mixed heavy/forced-false coefficients. These finite
checks suffice to confirm the changed supports six/seven; they are not a
source-level audit of the native cardinality encoder for every support size.
The evidence script instantiates no native solver.

## Complete tiny counts and exact assignment checks

| Grid | `(5,5)` clauses/aux | `(6,6)` clauses/aux | `(7,7)` clauses/aux |
| --- | --- | --- | --- |
| n3 | 4 / 0 | 4 / 0 | 4 / 0 |
| n5 | 25 / 0 | 25 / 0 | 25 / 0 |
| n7 | 127 / 2 | 127 / 2 | 127 / 2 |
| n9 | 372 / 75 | 374 / 67 | 438 / 3 |

The n9 values are Python clause counts only, without a native build or solve.
They show that the changed branches can remove auxiliaries, but are not a
large-grid forecast. Full n3/n5/n7 assignment enumeration checks every real
indicator assignment against the frozen baseline and exact integer geometry
for all nine threshold pairs. Those tiny complete grids do not distinguish
the proposed cutoffs, so separate exhaustive synthetic supports 0..8 verify
the changed six/seven branches, inactive/active guards, all threshold pairs,
retained counters, and mixed heavy/forced-false cases. Lower cutoffs also check
trivial support edges. The optional PySAT dependency is present for this run.

Six tests pass in 0.185 seconds. The report
`data/direct-threshold-tiny-estimates.json` binds its generator and all encoder
sources, includes all nine tiny-count configurations and per-support tables,
and records no n79 enumeration/build/search. No total n79 variable reduction,
RSS benefit, completed search, witness, UNSAT or mathematical absence follows
from this evidence. A new independently reviewed, explicitly configured,
source-bound build-only preflight under the same limits is the next possible
measurement; no such large run is authorized to this worker.
