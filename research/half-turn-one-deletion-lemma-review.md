# Half-turn symmetry and one-point deletion

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). This is an elementary
proof review, with no numerical search and no novelty claim.

**Lemma.** Let S be a finite set of distinct planar points invariant under the
half-turn H(x)=2c-x about c, and suppose c is not in S. If S minus one point has
no collinear triple, then S has no collinear triple.

**Proof.** Suppose a line L contains at least three points of S.

If c lies on L, H preserves L and pairs its S-points into two-element orbits:
there is no fixed point because c is absent. Therefore |S intersect L| is even
and at least four. Deleting one point leaves at least three points on L.

If c does not lie on L, the image H(L) is a distinct parallel line. Indeed,
a half-turn preserves a line's direction, and a line fixed by that half-turn
must pass through its center. Invariance of S gives
|S intersect H(L)|=|S intersect L|>=3. The two parallel lines are disjoint, so
deleting one point can affect at most one of their two intersections with S.
The other line retains a collinear triple.

In either case a collinear triple survives every single-point deletion,
contradicting the hypothesis. Hence S contains no collinear triple. QED.

**Exact near-quarter consequence.** A candidate consisting of complete approved
four-point orbits and its approved main-diagonal half-turn pair is invariant
under the board-center half-turn and omits the center. If it has 158 distinct
points, every 157-point subset obtained by deleting exactly one of its points
can be valid only when the entire 158-point candidate is already valid.
In particular, retaining only three points of the final complete four-orbit
cannot produce a valid 157-point escape from an invalid full 158-point candidate.
Restoring that one missing orbit point would necessarily give a valid 158-point
configuration. The argument does not rely on row/column capacity assumptions.

The conclusion applies only to this precise one-deletion completion to a
center-absent half-turn-invariant set. It does not rule out unrestricted
157-point constructions, families with other missing points, or different
symmetry patterns. The absent-center assumption matters: three points on one
line with the middle point as center form a counterexample if it is dropped.
