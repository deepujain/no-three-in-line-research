# Exact factorization of near-quarter line constraints

Mathematician agent, gpt-6-astra, high reasoning;2026-11-27. This proves a proposed
replacement encoding, not its performance or n79 feasibility. The original
reviewed compiler remains frozen. New source and tiny tests require independent
review before a later separately scheduled construction preflight.

## Common contribution and exceptional diagonal pair

Let R be quarter rotation and H=R². The model's off-diagonal decision variables
select complete four-point R-orbits O, each disjoint from both long diagonals.
Its diagonal variables select antipodal pairs P on the main diagonal. Exactly
one diagonal variable is true globally, and the anti-diagonal is empty.

For any grid line L, define

    C_L = sum over off-diagonal O of |L intersect O| x_O.

Because R(O)=O, the coefficient of every off-diagonal variable is identical on
L, R(L), H(L), and R³(L). Consequently these lines share the identical weighted
expression C, not merely the same cardinality on a particular assignment.

For a line other than the main diagonal, its intersection with that diagonal
has at most one point. Its diagonal contribution is therefore either zero or
one diagonal-pair variable d with coefficient1. Center intersections contribute
zero because the center is forbidden. Such a line's original inequality is
either C<=2 or C+d<=2. For binary d and nonnegative integer C,

    C+d<=2  iff  C<=2 and (d implies C<=1).

Thus every full quarter-turn orbit of non-diagonal lines can be replaced by:

* one shared weighted capacity C<=2;
* d implies C<=1, for every diagonal-pair variable encountered on any member.

H-partner lines encounter the same diagonal-pair variable. Hence there are at
most two distinct such variables in a line orbit. Repeated IDs can be removed.
The equivalence is assignment-by-assignment and retains every original member's
restriction. It does not assume that the full point configuration is quarter-turn
invariant. A blanket quarter-turn quotient that omits the diagonal guards is
still invalid.

The main and anti-diagonal form one exceptional line orbit. Their off-diagonal
expression is zero. Their capacities are respectively2*sum(d)<=2 and0<=2.
The unchanged global exactly-one-diagonal constraint implies both. This orbit
may therefore be skipped, but only with that global constraint retained.

Rotating a maximal grid line preserves its maximality and number of grid points.
Selecting the lexicographically smallest sorted point-list among its four
rotations therefore produces one representative per full line orbit without
needing a global deduplication set. Real affine lines are not fixed by a quarter
turn, although central lines are fixed by H; both two-line and four-line orbits
must be handled. Relative to the existing half-turn line quotient, this halves
the number of representative line rows before exceptional/tautological handling
and before the required diagonal guards are compiled. It is not a memory forecast.

## Coefficient multiplicities and small direct encodings

A line intersects each four-point square orbit in at most two points, so genuine
off-diagonal coefficients are1 or2. A selected coefficient2 variable consumes
the entire base capacity. Let the coefficient2 variables be called heavy and
coefficient1 variables light. An exact direct CNF for C<=2 consists of:

* negative pairs between any heavy variable and every other heavy/light variable;
* negative triples among every three distinct light variables.

For each diagonal guard d, C<=1 adds negative pairs(d,heavy) and negative
triples(d,light_i,light_j). A generic defensive compiler may additionally force
any coefficient>2 variable false, although such weights do not arise here.

Two essential edge cases: C=2x is itself always<=2, yet needs the clause
(not d or not x). C=x+y is also always<=2, yet needs
(not d or not x or not y). A base-capacity tautology must not cause those
nontrivial diagonal guards to be discarded. If C's total available weight is
at most1, both the base and every guard are tautological.

## Shared forward threshold counter: projected SAT equivalence

For longer supports, a single shared prefix counter can expose the weight>=2
condition to every diagonal guard. Number the positive-weight variables x_i,
with weights w_i in{1,2}. Use fresh a_i,b_i flags and fixed a_0=b_0=false.
The intended minimum values are prefix weight>=1 and prefix weight>=2.
The following implications are sufficient; reverse implications are unnecessary:

    a_(i-1) -> a_i
    b_(i-1) -> b_i
    x_i -> a_i

For w_i=1, also impose

    (a_(i-1) and x_i) -> b_i
    not (b_(i-1) and x_i).

For w_i=2, instead impose

    x_i -> b_i
    not (a_(i-1) and x_i).

Every diagonal guard adds(not d or not b_last).

Soundness follows by induction: actual prefix weight>=1 forces a_i, and actual
prefix weight>=2 forces b_i. The first prefix that would exceed2 violates its
overflow clause. A selected diagonal guard forbids a final weight>=2, so forces
C<=1. Completeness follows by assigning a_i and b_i their exact intended
threshold values whenever the desired base and guard inequalities hold. All
forward and overflow clauses then hold. Thus projecting away the auxiliary
flags gives exactly the intended weighted constraints, even though the flags
need not equal their thresholds in every satisfying auxiliary assignment.

Flags cannot be treated as biconditional definitions by unrelated constraints.
Fresh IDs from one shared allocation pool are required between line encodings
and the unchanged global cardinality counters. Within a line orbit, every guard
must refer to the same final flag; this is compatible because each guard only
adds a negative restriction on that flag. A verified existing cardinality
encoder guarded by an explicit OR of diagonal variables is an alternative,
but internal auxiliary meanings must not be guessed from undocumented IDs.

## Review gates

The separate compact implementation must be compared against the frozen weighted
line model and independent determinant geometry for every small orbit assignment.
Tests must cover both direct and sequential paths, weights2, multiple guards,
the two base-tautology edge cases above, central line orbits, both long diagonals,
and existential auxiliary semantics under assumptions on decision variables.
No performance conclusion or n79 model build follows from this proof alone.
