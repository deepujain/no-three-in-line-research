# Independent review of the row-quota compact variant

Reviewer: Mathematical Reviewer, `gpt-6-astra`, reasoning `high`, 2026-11-27.
The separate encoding is approved as exactly equivalent to the previously
reviewed restricted near-quarter family. This is source and tiny-correctness
approval, not an n79 resource or search approval.

Frozen source `src/near_quarter_row_quota.py`:
`dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704`.
Frozen tests `tests/test_near_quarter_row_quota.py`:
`4f50dcc697eb520e3a49cce69d9fdc25a6d948b63e048dacf64548d92ce66a7c`.
The original model, compact line encoder, original host guard, compact
build-only preflight, and compact solve wrapper remain unchanged.

## Exact equivalence

Write `n=2*m+1`. Retain exactly one diagonal pair and every approved compact
line capacity. The line constraints include every horizontal row and therefore
bound each row by two selected points. The new clauses require at least two
points in each representative row `0,...,m`. Every model assignment has
half-turn symmetry, so the opposite rows have the same loads. Consequently
every row contains exactly two points and the total is `2*n`.

Disjoint selected four-orbits and the single diagonal pair contribute `4*F+2`
points. Hence `4*F+2=2*n` forces `F=m`, exactly the omitted global four-orbit
cardinality. Conversely, the original cardinalities yield `2*n` points; with
all n row capacities at most two, every row must already have exactly two.
Thus the original constraints imply every new floor and the new constraints
imply the omitted cardinality, assignment by assignment. No extra symmetry
restriction or relaxation is introduced. The long-diagonal omission retains
its original justification because exactly one diagonal pair is still explicit.

For a positive weighted sum, split variables into heavy coefficients at least
two and light coefficients one. If there are fewer than two lights, the sum
is at least two precisely when some heavy variable is true, encoded by one
positive heavy clause (possibly empty). Otherwise emit, for each light, the
positive clause containing all heavies and all other lights. A true heavy
satisfies every clause; with no heavy, zero selected lights fails every clause
and exactly one fails the clause omitting that light, while any two satisfy
all clauses. This proves `at_least_two`, including empty and singleton cases.

The implementation computes actual per-row orbit multiplicities and uses this
exact lower-bound encoding. It leaves the diagonal cardinality and shared
line-capacity compiler intact. Fresh line-counter variables still use one
ID pool above all real orbit IDs. The omitted global counter cannot cause
collisions because subsequent counters allocate from the same fresh pool.

## Tiny verification and counts

All four author tests passed independently in 0.101 seconds. They exhaust
weighted lower bounds of lengths zero through five over coefficients 1,2,3;
all 4,164 n3/n5/n7 orbit assignments for row floors, symmetry, cardinality
equivalence, and projected CNF equivalence against the prior compact encoder
and exact determinant geometry. The reviewer independently recomputed every
reported n3/n5/n7/n9 full tiny CNF cost from the frozen stream.

| n | Prior compact clauses / auxiliaries | Row-quota clauses / auxiliaries |
|---|---:|---:|
| 3 | 2 / 0 | 4 / 0 |
| 5 | 32 / 8 | 25 / 0 |
| 7 | 180 / 38 | 127 / 2 |
| 9 | 531 / 171 | 372 / 75 |

The author's saved fixed published n71 row-floor check was inspected. It binds
the previously reviewed fixture and new source and reports exact expansion,
35 selected four-orbits plus one pair, all row loads two, and satisfaction of
2,451 positive clauses with 169,085 literals. That artifact concerns only the
fixed fixture and row arithmetic, not a full n71 formula or decision search.

## Algebraic n79 projection and limits

Each noncentral row has `n-2` distinct off-diagonal coefficient-one variables
and one main-diagonal pair variable. Two cells in such a row could belong to
the same four-orbit only on an excluded long diagonal. Thus there are `2*m`
light variables and `2*m` positive clauses of length `2*m-1`. The central row
has m heavy coefficient-two variables and needs one positive clause. At n79
this gives exactly 3,043 added floor clauses and 234,273 literal occurrences,
with no new auxiliary variables. These counts follow from geometry/algebra;
no n79 line or CNF enumeration was needed.

The installed `CardEnc.equals` delegates to both lower and upper cardinality
encoders. For interior bounds, the reported sequential-counter cost formula
is `4*K*(N-K)` clauses and `2*K*(N-K)` auxiliaries. The reviewer tested all
231 interior `(N,K)` cases with `4<=N<=24`, and each matched. Boundary cases
have special handling; the formula must not be applied universally (the n3
four-orbit equality has one clause despite the product being zero).

Conditional on that interior native-encoder cost formula at `N=1521,K=39`,
the omitted counter saves 231,192 clauses and 115,596 auxiliaries. Starting
from the prior measured compact n79 formula, the arithmetic forecast is
2,072,304 clauses and 475,708 variables after adding the floors. This is a
version-dependent algebraic forecast, not an observed complete n79 count or
an independent audit of the native encoder's source. A later guarded build
must establish the actual formula identity and resource use.

Fewer clauses/auxiliaries do not establish measured RSS savings or search
feasibility. Any runner integration requires separate review and a tiny host
gate before the Lead schedules a build under unchanged limits. No n79
enumeration, construction, search, cap increase, novelty claim, or global
nonexistence claim was performed or approved by this review.
