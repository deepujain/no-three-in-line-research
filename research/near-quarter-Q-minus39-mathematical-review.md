# Single Q=main-depth17 minus orbit39: mathematical review

Decision: design/scope PASS for source and tiny tests with the mandatory
literal-bound correction below. Reviewed proposal
`research/near-quarter-pair-unsat-conflict-explanation-proposal.md`, SHA256
`92e46fe686b025fc2399a6e9a5052401c14a3dc70b2a2c61412fef545bc3c2a9`.
Reviewer model gpt-6.1-sol/high. No mask, pair census, formula, native solve,
replay or frontier change was executed for this review.

The corrected proposal SHA256
`137742db6331c507ee643def50f8286fa14e322caaaa615526ec0b91be48c266`
has now been inspected and implements the required15360/117440 correction
and9m/16m/48m dynamic limits. Its design is approved for source/tiny work.

Q contains exactly17 declared IDs: diagonal pair1522 and16 four-orbits. Its
66 retained points require23 more four-orbits for158; residual quotient degree
sum is46. Removing39 is a non-ancestor choice: the depth16 ancestor instead
removes1107. Construct Q from its exact published ordered IDs and pinned
canonical orbit mapping; do not infer it from mutable frontier contents.

For a valid near-quarter completion A containing Q, every newly selected
four-orbit is individually admissible against Q and appears in the complete
mask. Every pair of those orbits must be compatible against Q. Their radius
degrees must exactly equal the residual demands. Thus their Boolean selection
extends to a satisfying assignment of the exact degree-plus-pair formula.
A trusted native UNSAT on that complete relaxation conditionally excludes
every valid completion containing Q. No geometric sufficiency of SAT is
asserted. Incomplete masks/pairs, native unknown, timeout or resource cutoff
provide no exclusion.

The conditional no-good is the disjunction of not-y_v over all17 IDs in Q.
It includes diagonal literal1522. A clause dropping that literal is justified
only inside an explicitly fixed-diagonal1522 search, or after separately
covering every other diagonal; no such global reduction is approved here.
Because Q is a proper subset of the original depth17 retained set, its clause
is strictly stronger as a proposition over unconstrained orbit literals.
Additional useful pruning within the actual search policy is unmeasured.
This is not a minimal core, global n79 exclusion, checked UNSAT proof or
permission to integrate a learned rule into frozen packed checkpoints.

Mandatory arithmetic correction: the proposal's final paragraph states12160
degree literal entries and114240 final entries. These do not follow from the
referenced previously reviewed conservative incidence bound. For m<=320
available edges with two distinct endpoints, total incidence is2m<=640.
Demands are0/1/2. The safe sequential-counter bounds are4 times incidence
auxiliaries,8 times incidence clauses and24 times incidence literal entries.
Therefore the corrected per-stage bounds are:

|Quantity|Dynamic bound|At m320|
|---|---:|---:|
|Auxiliary variables|8m|2560|
|Total variables|9m|2880|
|Degree clauses|16m|5120|
|Degree literal entries|48m|15360|
|Unordered pairs|m(m-1)/2|51040|
|Final pair-only clauses|16m+m(m-1)/2|56160|
|Final pair-only literal entries|48m+m(m-1)|117440|

There are no ternary cuts in this pair-only Q experiment. If a tighter literal
ceiling is desired, it needs a separate derivation; use15360/117440 for the
approved source. Enforce dynamic and absolute bounds before native bootstrap.
Every mask decision and pair must be fresh for Q; earlier prefix cuts cannot
be inherited. Save complete admitted-ID mapping, degree data, binary clauses,
source/model identities and enough evidence for independent determinant/axis
audit. The actual evidence audit may produce independent rejection witnesses;
never label a digest/count match alone an independent geometric proof.

The one proposed Q uses a shared25s soft budget under the unchanged owned30s /
256MiB gate. Stop instead of truncating above320 mask variables. A second
backend or proof checker is not included in this single allocation. No old
cut files, frontier writes, automatic Q minimization, second Q, recurrence
claim or learning integration is authorized. Independently reviewed source
and tiny projections are required before Root can allocate any actual run.
