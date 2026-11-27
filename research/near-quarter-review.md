# Independent near-quarter-turn mathematical and encoder review

**READY / APPROVED for the orbit map and streamed weighted-line/CNF compiler.**
No blocking mathematical or encoding finding remains at the source hashes below.
This is not approval of an unmeasured n79 solve or a claim that the family has
an n79 solution. The planned large-fixture regression and resource preflight
remain separate gates before such a run.

Reviewer: Mathematician agent, gpt-6-astra, high reasoning;2026-11-27. I read
[Prellberg, arXiv:2602.07751v1, section3](https://arxiv.org/html/2602.07751#S3)
directly and compared the proposal and code with its orbit map and weighted
line formulation. I did not change the author's implementation or tests.
No n79 model build, solver search, or benchmark was performed in this review.

## Correct family and target

Let n=2m+1. The main and anti-diagonal together contain2n-1 grid points. Their
complement therefore has(n-1)^2=4m^2 points. It is partitioned into m^2 disjoint
four-point orbits of the quarter turn. The main diagonal, excluding the center,
has m antipodal pairs; the complete anti-diagonal, including the center, is
forbidden. These orbits partition all n^2-n permitted cells. This is precisely
the domain represented by the implementation. At n79, m=39, giving1,521
four-point variables and39 two-point variables.

Selecting m four-point orbits and one diagonal pair gives4m+2=2n points. Every
orbit is separately half-turn invariant. The selected diagonal pair rotates
onto the forbidden anti-diagonal, so the full selected set is not quarter-turn
invariant. Thus the exact-quarter-turn parity exclusion does not eliminate
this family. Half-turn invariance does exclude the odd157 target, as already
proved in `research/symmetry-next.md`.

Conversely, within this orbit domain a valid2n-point set has at most one selected
diagonal pair, since two pairs would give four collinear main-diagonal points.
Writing its count as4A+2B=4m+2 then forces B=1 and A=m. Therefore the compiler's
two cardinality equalities precisely encode the full-target cardinality for
geometrically valid assignments in this family.

The primary paper's rectangular fundamental domain is another representation
of exactly these orbits. I independently constructed it at n3,5,7 and checked
equality with the implementation's orbit sets, rather than relying only on
their counts. The n3 six-point fixture in the proposal expands from its sole
four-point orbit and sole main-diagonal pair and passes both geometric checkers.

## Weighted lines, symmetry quotient, and CNF

For an affine line L and disjoint selected orbits O, the number of selected
points on L is exactly sum_O |L intersect O| z_O. Thus all weighted capacities
<=2 are equivalent to the absence of three selected collinear grid points.
Lines containing fewer than three grid cells cannot violate the capacity.
Rows and columns are included among the generated lines. With exactly2n
selected points and all n row capacities<=2, each row must contain exactly2;
the same argument applies to columns. The implementation therefore obtains
exact row/column occupancy implicitly, without separate redundant equalities.

Each four-point orbit is the vertex set of a nondegenerate square. No line
meets it in more than two vertices; the pair orbits also have size2. Actual
coefficients in this family therefore belong to{1,2}. The proposal originally
requested a genuine coefficient>=3 test; the author corrected this to a
synthetic defensive compiler test, since such a genuine line cannot occur.

For H the half turn, H(O)=O for every orbit separately. Consequently
|H(L) intersect O|=|L intersect O| for every orbit variable. A line and its
half-turn image have identical weighted vectors. The lexicographically smaller
of their sorted point lists is therefore a sound representative; central lines
fixed by H remain present. Quarter-turn quotienting would not have this proof
because of the exceptional diagonal pair. The code does not do it.

The CNF lowering is exact for its nonnegative, distinct-variable weighted rows.
A coefficient above2 forces its variable false. A coefficient2 variable cannot
coexist with another coefficient2 or coefficient1 variable. Coefficient1 terms
use an at-most-two sequential counter. These conditions are jointly necessary
and sufficient for the weighted sum<=2. The cardinality and line counters share
one IDPool beginning above every orbit decision variable, so their auxiliary
IDs cannot collide with decisions or with previous counters. Branch-specific
clauses stay inside this compiler and are not written to unrestricted geometry
checkpoints.

The generator retains only one line's weighted dictionary and one emitted
cardinality encoding at a time, alongside the finite orbit map. It does not
cache all lines or all CNF. This is a structural description, not a claim that
a caller accumulating clauses in a solver meets any particular memory limit.

## Independent checks and limitations

The standard-library test run passed its three applicable tests, with two PySAT
tests skipped because system Python lacks that optional dependency. I then ran
the complete five-test suite using the existing research virtual environment;
all passed in0.556 seconds. The suite checks all4,164 orbit assignments across
n3,5,7 against determinant geometry, both without and with the line quotient.
Its CNF checks use all decision-variable assumptions for those assignments in
both quotient modes, plus all64 assignments of a synthetic weighted row
containing a coefficient3 term.

As a separate independent check, I generated all affine grid lines from
unordered grid-point pairs, normalized their integer line equations, and kept
those containing at least three grid points. Their complete point sets agree
with the compiler at n3,5,7:8,32,108 lines respectively. Direct orbit/line set
intersections agree with every weighted vector. The half-turn quotient retains
6,20,62 representatives and preserves every vector's partner. These checks
avoid using the production primitive-direction generator as their oracle.

The n71/n73 published-fixture decoding has not been performed by this reviewer.
Nor have n79 line/CNF size, peak RSS, build time, or solve behavior been measured.
Those planned gates remain outstanding. UNSAT, if later obtained with a correct
solver certificate, would concern only this restricted family; timeout provides
no exclusion. None of this review is a novelty or unrestricted nonexistence claim.

## Optional derived structural check

Any full target in this family selects exactly one four-point orbit on the
horizontal/vertical central axes: only such an orbit can occupy the middle row,
and it contributes exactly two points there. Write j for its positive coordinate
distance from the center and t for the selected diagonal pair's distance. The
remaining m-1 selected four-orbits have two distinct positive coordinate
distances. Represent each as an edge on the m positive-distance classes; there
are two possible orbit orientations per unordered pair, so this is a multigraph.
Its vertex i has degree2-1[i=j]-1[i=t]. If j=t, that vertex is isolated and the
others form cycles; otherwise there is a path from j to t plus cycles. Parallel
edges can form a two-edge cycle and must not be accidentally forbidden. This
is an optional necessary condition, not an extra restriction implemented here.

## Exact reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `src/near_quarter_model.py` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| `tests/test_near_quarter_model.py` | `7a6c77363155e1958a17eddadd38ec3cd1d9a6a938bca1469c8e85f72a4243b4` |
| `src/line_model.py` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
