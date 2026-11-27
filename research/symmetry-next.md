# Symmetry restrictions and the next bounded frontiers

Mathematician agent, gpt-6-astra, high reasoning; 2026-11-26.
These proofs restrict particular invariant families. They do not establish
existence or nonexistence of an unrestricted 157- or 158-point set at order79.
Independent review is requested separately.

## Half-turn and quarter-turn invariance

Write c=(39,39) and H(p)=2c-p. Every noncentral orbit has two points. An
odd-cardinality H-invariant set must contain c. If it has any other orbit,
its two points and c are collinear. Consequently **no half-turn invariant
no-three-in-line set has odd cardinality greater than one**. This excludes
target157 under half-turn, quarter-turn, or any larger group containing H.

For target158, H-invariance requires c absent and exactly79 antipodal pairs.
No two selected antipodal pairs may lie on the same unoriented line through c:
otherwise at least four selected points would lie on that line. There must be
two points in every row and column. The middle row therefore contains one
antipodal pair, and the middle column a different one. Each other reflected
pair of rows contains two selected antipodal orbits; the same holds for columns.
These necessary conditions are consistent, but do not prove feasibility at79.
At n=3, {(0,0),(0,1),(1,0),(1,2),(2,1),(2,2)} is a valid half-turn invariant
six-point example.

A quarter turn has four-point orbits apart from its singleton center. Thus its
invariant cardinalities are0 or1 modulo4; target158 is excluded independently.
Neither target can have exact quarter-turn invariance.

## One diagonal reflection and target157

Let T(x,y)=(y,x). Off-diagonal orbits have size2 and fixed points lie on y=x.
Odd cardinality and the bound of two points on that line imply **exactly one
selected fixed point**, say (t,t). Row i and column i have equal counts under T.
Since a157-point set has one deficient row and one deficient column, both have
the same index d. The diagonal point need not equal the deficit intersection:

* At n=3, {(0,0),(0,1),(1,0),(1,2),(2,1)} is valid, with t=0 and d=2.
* At n=4, {(0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,3)} is valid, with t=d=3.

An off-diagonal orbit {(x,y),(y,x)} lies on the line x+y=s. At most one such
orbit can be selected for each s. None can be selected for s=2t because (t,t)
would be a third collinear point.

Represent each off-diagonal orbit as a simple undirected edge between indices
x and y. Vertex i has degree 2-1[i=d]-1[i=t]. If d=t, vertex d is isolated and
the remaining graph is a union of cycles. If d differs from t, the graph is one
path with endpoints d,t and a union of cycles. These are useful necessary
conditions; they do not replace geometric checks on other slopes.

Main- and anti-diagonal reflection families are conjugate by a quarter turn,
so searching both is redundant for unrestricted existence in the family
"invariant under some diagonal reflection." Requiring both diagonal reflections
would impose the forbidden half-turn for157.

## One axial reflection and target157

Under V(x,y)=(78-x,y), parity and the two-per-column bound give exactly one
point on the fixed column x=39. The unique deficient column must be this fixed
column. Every nonfixed row orbit consists of two points in the same row, so
the row containing the singleton fixed point has odd count and must be the
unique deficient row. Thus its deficit intersection is occupied. Horizontal
reflection is conjugate to vertical reflection. Axial and diagonal reflections
are different conjugacy classes; testing a diagonal family does not test axial
invariance. Requiring both axial reflections again imposes a half-turn.

## Safe SAT scope

The next distinct restricted branches are diagonal reflection for157 and
half-turn for158. The real-cell equivalences X[p] iff X[T(p)] or X[H(p)] impose
these families. The necessary orbit restrictions above may strengthen them.
In the diagonal157 branch, reflection already implies equal row/column deficit
indices when the existing axis encoding is correct; additional deficit-variable
equivalences are optional. Do not require t=d or its negation.

Symmetry equivalences, orbit exclusions, and binary clauses obtained by
collapsing a triple under symmetry are **branch constraints**, not unrestricted
geometric facts. Shared geometry checkpoints may contain only actual
three-real-cell collinearity clauses. A restricted UNSAT result says nothing
about solutions outside that symmetry family; a timeout is incomplete.

## Memory bound for corner repairs through five deletions

This calculation only reads existing audit metadata and evaluates binomial
coefficients. No five-deletion set collection was generated. The translated
valid seed has156 points. For an empty cell with q disjoint blocker pairs, the
number of k-point deletions admitting that cell is

    A(q,k) = sum_r C(q,r) 2^(q-r) C(156-2q,k-q-r),

where 0<=r<=min(q,k-q). Here r counts pairs with both endpoints deleted; every
other pair has one of two endpoints deleted. Remaining deletions are outside
the2q blocker endpoints. This counts that cell's deletions without duplication.

The existing blocker audit has counts (q,count)=(2,2),(3,28),(4,122),(5,258).
Their A(q,5) values are respectively2,341,256;91,206;2,400;32, and sums through5
are2,388,385;92,426;2,416;32. A union bound therefore gives at most7,667,706
distinct deletions through5.

For translation(0,0), the two q=2 cells have pairs
[(67,103),(85,115)] and [(0,1),(29,49)]. All eight endpoints are distinct.
Their common exact-five deletion sets hit four disjoint pairs, giving
A(4,5)=2,400. Their union therefore contains4,680,112 exact-five deletions.
The completed guided-four audit separately counts130,290 deletions of size<=4,
so **4,810,402 <= number through5 <= 7,667,706**. The corresponding corners
are equivalent under the verified quarter-turn symmetry of this specific seed.

On the local Python used for sizing, a five-element tuple is88 bytes. Exact-five
tuples alone therefore require at least392.77 MiB. The implementation also
holds the hash table, the output list, per-element sort-key tuples, key pointers,
sorting scratch, and allocator overhead concurrently. At the proven lower
bound, just one list of pointers is36.70 MiB and two-element sort-key tuples
are293.60 MiB. These are component estimates, not an RSS prediction. A second
worker or SAT allocation shares the1536 MiB guard. **Do not queue the existing
materializing deletion_sets implementation at budget5 under that guard.**

## Streamed cover family

For each eligible genuinely new cell, enumerate one endpoint from each blocker
pair; there are only10,440 raw anchor covers across the410 cells. Deduplicate
these covers and remove any cover containing another retained cover. This is a
small antichain computation, not enumeration of the millions of five-point
supersets. Every deletion set permitting a new cell contains one original
endpoint cover, hence a retained cover. Conversely, every superset of a retained
cover permits its associated new cell. Thus the union of exact-five supersets
of retained covers is exactly the relevant exact-five deletion family.

The unchanged embedding worker can stream these supersets independently, with
numeric offsets and immutable hash-linked records. Duplicate deletion sets
across cover streams are harmless for completeness but must not be counted as
distinct coverage. Before antichain reduction the exact-five workload, counting
those duplicates, is at most

    2*4*C(154,3) + 28*8*C(153,2) + 122*16*C(152,1) + 258*32
    = 7,684,864.

The implementation must derive blockers after applying its own embedding:
cut(0,0) means translation(+1,+1), whereas guided translation(0,0) leaves the
seed unchanged. Prepared origins use cut(0,0), the original ordered point list,
its hash, distinct tip names, and zero completed cases. Finishing a few covers
does not close the corner family. Closure requires all retained cover streams,
plus the already-completed <=4 audit. No numerical search is part of preparation.

A future deduplicated iterator can assign a deletion set to its earliest retained
cover. Since a five-set has only32 subsets, checking cover ownership requires a
small bounded number of dictionary lookups without a global set of deletions.
That optimization would require separate review; the existing worker does not
implement it.
