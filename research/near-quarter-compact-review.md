# Independent review of the compact near-quarter compiler

Mathematical Reviewer: `gpt-6-astra`, reasoning `high`. Reviewed 2026-11-27.
The reviewed encoding is approved as an exact alternative for the existing
restricted near-quarter family. This approval covers mathematical correctness
and tiny verification, not n79 construction feasibility or search readiness.

## Reviewed identities

* `src/near_quarter_compact.py`:
  `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1`
* `tests/test_near_quarter_compact.py`:
  `a55eaed7f25d8a690763a43bc4d32cdcc48ff681d69055cb714e4823e105ccde`
* Frozen original `src/near_quarter_model.py` remains:
  `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a`
* Frozen line generator `src/line_model.py` remains:
  `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897`

## Mathematical audit

The factorization proof is in `near-quarter-compaction-proof.md`. The actual
implementation uses the direct/safe existing-cardinality alternative described
there, not the optional forward threshold construction.

`line_groups` chooses exactly the least sorted point tuple under four rotations.
It handles two-member central line orbits as well as four-member orbits and
checks equality of the off-diagonal coefficient signatures. It collects all
exceptional main-diagonal pair variables across the orbit, validates at most
two guards outside the long-diagonal orbit, and retains their separate
conditional restrictions. Thus sharing the common expression does not assume
that the whole selected configuration has quarter-turn symmetry.

The shared capacity correctly separates coefficient-two variables from
coefficient-one variables. Heavy-heavy and heavy-light pairs forbid every
overload involving a heavy term. Negative triples, or the existing sequential
at-most-two encoder, handle all-light overloads. Defensive coefficients above
two are forced false. Every diagonal guard forbids each heavy variable and
requires at most one light variable. In particular, the implementations retain
the nontrivial guards for both `C=2*x` and `C=x+y`, whose base capacities alone
are tautologies.

For a long light support, all clauses of one at-most-one encoding are gated.
One guard is used directly; multiple guards imply a fresh gate. If any guard
is true, that gate is true and the complete at-most-one CNF is enforced. When
all guards are false, choosing the gate false disables every conditional
clause and permits arbitrary values for its private auxiliary variables.
Therefore omitting reverse gate implications preserves precisely the desired
existential projection onto decision variables. No internal cardinality flag
is assigned an undocumented meaning.

A single ID pool starts above all orbit variables and is shared by both global
equalities, every line counter, and every gate, so auxiliary variables do not
collide. The global equalities retain exactly `(n-1)/2` full four-orbits and
exactly one main-diagonal pair. The latter makes the skipped main/anti-diagonal
capacities redundant. The resulting family still has exactly `2*n` points,
half-turn symmetry, and an empty anti-diagonal; it is not an unrestricted model.

## Independent verification

Reviewer reran all four author tests using `.venv/bin/python`; all passed in
0.302 seconds. They compare all 4,164 orbit decision assignments at n=3,5,7
between original CNF, compact CNF, cardinalities, and determinant geometry.
They also cover full line partitions and both direct and sequential synthetic
guard encodings. SAT calls here only check fully fixed tiny decision assignments
with existential auxiliary values.

A separate reviewer one-off check generated lines from every pair of grid
points using normalized integer equations, independently of `maximal_lines`.
Its lines of length at least three matched the complete rotation-group
partition: n=3 had 8 lines/3 groups; n=5 had 32/10; n=7 had 108/31; n=9 had
296/80. Each member's common weights were independently recomputed by set
intersection with the actual point orbits. No group overlap or missing line
was found.

Another reviewer check enumerated every coefficient sequence of length zero
through five over `{1,2,3}`, plus longer six/seven-light cases with zero, one,
or two heavy terms and a defensive coefficient-three term. Each was tested
with zero through three guards, exceeding the geometric maximum of two.
Across 1,476 encoded cases and 150,525 fully fixed decision assignments,
projected SAT agreed exactly with `C<=2` and `any_guard => C<=1`. This checks
both direct and sequential paths, disabled gates, multiple simultaneous
guards, empty supports, and the base-tautology edge cases. All passed.

## Scope and remaining gate

The reported complete tiny counts show fewer clauses/auxiliaries at n=5 and
n=7 and equality at n=3. They are not a prediction of n79 RSS or construction
time. No n79 line enumeration, model build, numerical search, or benchmark was
performed by this reviewer. The original compiler and approved preflight were
not modified. A later preflight adapter for this separate variant requires
its own source review and must retain the existing resource gate and explicit
no-search behavior. Any future UNSAT result remains restricted-family only;
this review makes no nonexistence or novelty claim.
