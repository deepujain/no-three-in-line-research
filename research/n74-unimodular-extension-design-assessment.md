# Conditional unimodular re-embedding extension: design assessment only

This is a possible structurally distinct hypothesis after the current insertion branch, not a second active experiment or an automatic fallback. No source coordinates were read, no directional widths were measured, no affine embeddings were generated, and no new computation is allocated here. Actual eligibility would require a separate Root decision, source-specific prior-scope review, implementation review and synthetic evidence. There is no empirical promise or novelty claim.

## Construction hypothesis and scope distinction

Keep the same authenticated 148-point n74 source B. Seek an integer affine map p -> A p + t with det(A)=+1 or -1 that places B inside the 75-square, then add one lattice point z without creating a triple. Unimodularity preserves the integer lattice bijectively and all old collinearities. Thus no old-triple census is needed: only the new point against old pairs requires checking.

An added target point corresponds to an original-coordinate lattice point q=A^-1(z-t). A fixed-geometry free-cell scan covers q only within the specific original-coordinate board region it scanned. A non-axis unimodular frame may fit B together with q even when q was outside that region. This is the precise possible distinction from ordinary translation/reflection and from nonuniform insertion, which moves old points piecewise and changes their collinearities. It does not prove disjointness from every prior experiment or literal target set. Ordinary axis frames and their board symmetries must be excluded, and any prior equivalent affine frame or candidate must be curtailed rather than rerun.

The hypothesis uses the same source and an exact finite affine family, not another source record, larger repair cap, walk restart, SAT pool expansion, or alternate orientation loop. It should not be implemented merely because the insertion family ends negatively.

## Necessary width filter with exact finite bounds

For integer direction u=(a,b), define its source width W(u)=max(a*x+b*y)-min(a*x+b*y). A valid 148-point source has at most two points on each parallel line, so it occupies at least 74 distinct levels of any nonzero integer linear form. Hence W(u)>=73. To fit a target coordinate range 0..74, an admissible direction must have W(u) in {73,74}. A nonprimitive direction has level spacing at least two and width at least146, so every admissible direction is primitive.

Let H be the largest horizontal separation of the two source points sharing any source row, and V the largest vertical separation of the two sharing any source column. Both are positive because the source has exactly two distinct points on every axis. For any admissible direction,

    |a| H <= W(u) <= 74,  |b| V <= W(u) <= 74.

Thus |a|<=floor(74/H), |b|<=floor(74/V). Even without reading B, each bound is at most74 and there are at most22,200 nonzero direction pairs before primitive/sign reductions. At most3,285,600 source-point projections suffice to test this loose set. In the common conditional situation H,V>=38, the coefficients lie in {-1,0,1}, leaving only axes and diagonals before sign reduction. If every non-axis direction then has width above74, the proposed nontrivial family is empty and must stop without an extension scan. Whether this condition holds for the selected source is unknown here.

Two admissible directions u,v form an allowed frame only when det(u,v)=+1 or -1. Avoid a quadratic scan of all direction pairs: an extended-GCD solution v0 of det(u,v0)=1 generates all partners v=v0+k*u; coefficient bounds give an exact integer k interval. Handle determinant -1 by sign or an explicitly canonical frame convention. This is a suggested arithmetic reduction requiring separate tiny tests, not an implemented enumerator.

## At most four eligible added cells per placed frame

For a coordinate of width73, the 148 source points occupy all74 levels twice; there are exactly two placements in a75-level target. For width74, there is one placement, and the total spare capacity over75 levels is two: either one empty level or two singly occupied levels. Therefore each placed frame has at most two deficient rows and at most two deficient columns. An added point must lie at an intersection of those deficient levels, leaving at most four eligible cells. Each frame has at most four translations because each coordinate width is73 or74.

For each such cell, invert the affine map to its exact integer preimage q, deduplicate q across frames, and test q against old pairs. A rejected q has one compact original-coordinate collinear-pair obstruction that applies to every frame sharing q. A surviving q plus a witnessed frame yields a concrete149-point candidate, requiring immediate dual validation and saving. Successful extension of the same source is not itself a priority claim.

## Why this is not yet a pilot proposal

The direction bound is concrete, but no useful bound on the number of admitted frames or distinct q values has yet been established for this source. The loose partner/translation/cell ceilings can be too large for the resource envelope. Deduplication may help but must not substitute for a bounded work argument. A source-specific admissible-direction inventory would be a new geometry-dependent computation requiring its own explicit small allocation; it could establish that the family is empty or that enumeration is tractable. No such inventory is authorized by this document.

If Root considers this hypothesis after the current branch, the next design gate should ask whether the width filter alone supports a tightly bounded exact family, and whether prior work already scanned the equivalent original-coordinate candidates. Do not progress to a frame search without those answers. As a separate exclusion of superficial follow-ons: every increasing map from74 coordinate levels into75 levels omits exactly one level and is already the current insertion family, and board reflections/transposition merely relabel its gaps. Those changes do not constitute another construction hypothesis.
