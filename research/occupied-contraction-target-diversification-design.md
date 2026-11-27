# Occupied-intersection contraction for a smaller finite target

Status: DESIGN ONLY, conditional proposal for independent review and literature/scope refresh. No source witness was loaded, cropped, compressed, scored, or searched at75,76,77,78,79. No actual allocation or production implementation is requested by this memo. Synthetic n2..4 tests and scalar operation bounds are the only computation.

## Decision and target

There is one conditional structural alternative to the stalled direct157 frontier: target149 on75 using an authenticated full152-point76 witness. The corresponding78→77 contraction census is **curtailed**: Root relayed the focused literature review that Grey Strand's October30 report explicitly covers all6,084 row/column deletions, with a reported independent replay of all6,084 and only four clean boundary crops. Its code/remapping has not been independently audited here, but that is sufficient overlap to reject an unchanged census recommendation. Counting the same family faster does not justify replaying it. The focused review did not identify a76→75 experiment.

A149 construction may be called a new lower bound only after refreshing the current best documented75 near-miss. The ledger's148/152 bounds are explicitly available bounds, not certified best-known records. This memo establishes no actual candidate score or probability of success. The generic78 arithmetic below is explanatory only and does not reopen that target.

The leverage is exact cardinality and axis feasibility with **no additions or repair search**, plus a bounded simultaneous conflict census. It is not a changed acceptance policy, retention range, larger patch, or renamed n79 SAT/DFS. It can fail for every cut; failure would close only this finite contraction family of the selected source. Do not follow a negative result automatically with repairs, a different source, or more targets.

## Cardinality and axes

Let P be a valid2N-point set on an N-square. Every row and column has two points. Choose an occupied cell(c,r) in P; delete all points in column c or row r, then map every survivor by

    f_(c,r)(x,y) = (x - [x>c], y - [y>r]).

Exactly2+2−1=3 points are deleted, so the image has2N−3=2(N−1)−1 distinct points on an(N−1)-square. The coordinate maps are injective on the remaining levels. Exactly one surviving row loses a point to the deleted column, and exactly one surviving column loses a point to the deleted row; all other loads remain two. The deficient intersection may be occupied. Thus each of the2N occupied cuts gives the direct odd-cardinality axis pattern without any matching choice.

For N=76 the target count is149; for N=78 it is153. This does not produce150 or154, nor imply optimality. Boundary cuts are included but interior compression is piecewise affine, not globally affine, so collinearity is not preserved in general.

## Exact simultaneous conflict counting

For each unordered source triple T, exclude cut columns equal to any x-coordinate of T and cut rows equal to any y-coordinate of T: those cuts remove a member and contribute no surviving triple. The remaining integer cut columns split into at most four intervals between distinct x-coordinates, including possible outer intervals. The remaining rows similarly split into at most four intervals. Empty intervals are omitted.

On any Cartesian product of these intervals, each of the six indicators[x_i>c],[y_i>r] is constant. Therefore the determinant of the compressed triple is constant throughout this cut rectangle. Evaluate it once at the lower-left cut coordinate. If it is zero, add one to that rectangle of cut scores using four signed updates in an(N+1)×(N+1) difference array. Otherwise do nothing. After all source triples, a two-dimensional prefix sum gives the exact number of surviving collinear triples for **every** cut(c,r).

Proof: every surviving source triple belongs to exactly one such interval rectangle for a given cut; its compressed determinant equals that rectangle's tested determinant. Every image triple has a unique surviving source preimage because compression is injective. Summing the rectangle indicators consequently counts each bad image triple exactly once, including multiple triples on a longer line. Removed triples contribute nowhere. This argument works even for an invalid axis-full source, although the proposed experiment requires a dual-verified valid source. Occupied cut cells with score zero yield the desired construction; scores at unoccupied cuts concern2N−4 points and are not improvements.

This is a mathematical operation-count reduction compared with separately checking every occupied contraction. It is not a measured speedup or a claim of algorithmic novelty. No assumption about small source determinants, local blockers, symmetry, or conflict independence is needed.

## Bounded work and storage

For a fixed source, process at most C(2N,3) triples and16*C(2N,3) constant-size rectangle determinant tests. A zero rectangle needs four additions; the final prefix sum uses N² cells. Store the source, the score array, and a constant-size triple/interval workspace; never retain the triple or rectangle list.

| Source order | Source triples | Rectangle-test ceiling | Separate occupied-cut triple checks | Signed64-bit array bytes |
|---|---:|---:|---:|---:|
|76|573,800|9,180,800|82,121,648|47,432|
|78|620,620|9,929,920|91,303,056|49,928|

The separate-check column is2N*C(2N−3,3), before any early exit. The count reduction does not account for differing per-test overhead. These numbers are conservative operation/storage bounds, not host timing or total-process RSS estimates. Signed64-bit entries comfortably cover all updates and prefix intermediates; an implementation should use an actual compact integer array, record processed source triples and rectangle tests, and reject an impossible count. Validation, source pin checks, candidate reconstruction, both final exact validators, reporting, and cleanup are additional work under the same future owned gate.

If Root later considers the76→75 family, propose only one selected76 source and one fresh25-second soft/30-second owned/256-MiB pilot after source/tiny/lifecycle review. The bounds do not establish that the pilot will finish. An interrupted census has no negative conclusion; save a clear incomplete status. A scored-zero cut is not promoted until the reconstructed149-point set passes both exact validators and provenance is retained. Do not start n77 as a fallback from n75.

## Tiny falsifier and verification evidence

Compression can introduce triples even for a full valid source. On the4-square,

    P={(0,0),(0,1),(1,2),(1,3),(2,0),(2,1),(3,2),(3,3)}

has eight points and no collinear triple. Delete the occupied intersection(1,2). Its contracted image is

    {(0,0),(0,1),(1,0),(1,1),(2,2)},

which has the triple((0,0),(1,1),(2,2)). Any implementation that assumes contraction preserves validity must fail this fixture.

The separate tiny audit enumerated **all97 axis-full sources** at n2,3,4, including invalid ones, compared the rectangle result with direct determinant enumeration at **all1,498 cuts**, and checked the predicted cardinality/unique axis deficiencies at **760 occupied cuts**. Fourteen sources were geometrically valid. All comparisons passed;7,416 nonempty threshold rectangles were examined. This is an authored mathematical design with a separate direct tiny oracle, not an independent source-review approval or evidence of a large-grid witness.

Audit source: research/occupied_contraction_independent_tiny_audit.py, SHA2563dd7986048517677763ccdcccf4b3665a72007c40ce15790ef3a7259b5d807fa.

Audit data: data/occupied-contraction-independent-tiny-audit.json, SHA256fe4210b2fb27c7f5eb2041b98e7e8446f9ed35ff9b52c17022c0580bf717ff73.

## Required literature and scope refresh

Read the primary current construction table/history and attributable75/149 reports, not just full150 records. Authenticate and locally validate the proposed full76 source before any large-grid work. Check whether the same contraction census for76→75 is already published. The focused review of the [October30 report](https://thegreystrand.com/office/) relayed by Root supplies the reason to curtail78→77; its reported clean-crop result is not promoted here into an independently checked mathematical exclusion. An existing complete result for the identical76 source/family must not be replayed merely because this memo counts it differently; a documented149 construction changes the improvement target.

Pending those checks, the recommendation is **retain one conditional n75 design candidate; curtail n77; allocate neither**. If literature rules out the benefit or shows the76→75 family already exhausted, stop this branch. No replacement target should be invented to keep it active.
