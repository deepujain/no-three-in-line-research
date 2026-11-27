# Bounded exterior unimodular extension proposal: design only

This final finite-work proposal strengthens, without rewriting, `research/n74-unimodular-extension-design-assessment.md` (`80cbdc44f4e3520e15b06f91ef84d8b5d2e821da0d9ef4dca85f65dd9cc6583c`). It proposes source/tiny review of one exact finite family. No production worker, selected-source width inventory, affine embedding, or actual extension check is authorized. Only synthetic n4 falsifiers were executed. Root retains all actual allocations.

## Exact family and prior boundary

Use the same authenticated full 148-point source B in {0,...,73} squared. An allowed target is A(B)+t together with one new integer point z, contained in {0,...,74} squared, where A is an integer matrix of determinant +1 or -1. Its preimage is q=A^-1(z-t). Require q not in B and, conservatively, q outside the protected box U=[-1,74] squared. Exclude ordinary coordinate-axis frames. Matrices differing by signed row permutation are equivalent under a target-board reflection/transposition and are represented once.

The protected box is the union of all original-coordinate preimages of the75-square under the four ordinary boundary embeddings of the74-square. Consequently a q outside U cannot belong to a fixed75-square free-cell scan of any such embedding of this same decoded source. This conservative filter avoids reopening those cells even though the forum report leaves the exact source record and offset uncertain. It is a scope exclusion, not proof that every q inside U is obstructed for this selected source. Any final negative must say **the selected-source exterior unimodular family** is excluded, not all affine extensions or the unrestricted problem. If later reliable prior evidence identifies additional equivalent exterior preimages, curtail them explicitly before evaluation. No novelty follows from the current prior-scope distinction.

Nonuniform insertion changes old geometry piecewise; an affine map preserves all old collinearities and may place an original-coordinate exterior q into the target board. This is the construction hypothesis. It is not an alternate source, larger repair cap, permutation restart, orientation loop, or automatic fallback after the insertion result. All increasing coordinate injections from74 levels into75 levels are already the closed insertion family; reflecting/transposing them adds no new family.

## Lemma 1: every nonzero integer direction has width at least73

For u=(a,b), let W(u)=max_{p in B} u.p - min_{p in B} u.p. The level sets of any nonzero u are parallel lines. No three source points are collinear, so148 points occupy at least74 distinct integer levels. Therefore W(u)>=73. More precisely W(u)>=73*gcd(|a|,|b|). To fit one target coordinate, W(u)<=74, so every admissible direction is primitive and has width73 or74.

Width is homogeneous and subadditive: W(k*u)=|k|W(u), and W(u-v)<=W(u)+W(v). These statements follow directly by comparing maxima/minima of linear forms and do not assume convex-hull enumeration.

## Lemma 2: at most eight signed admissible directions

Suppose distinct admissible integer vectors u and v have the same coordinate residues modulo3. Then u-v=3w for a nonzero integer w. Lemma1 gives W(u-v)=3W(w)>=219, while subadditivity gives W(u-v)<=148, a contradiction. The same conclusion holds if one vector is zero: its width is zero. Thus the set consisting of zero and all admissible vectors injects into the nine residue classes modulo3. There are at most eight nonzero admissible vectors, in at most four opposite-sign pairs.

This bound does not depend on favorable source widths. It is the key finite-work bound. In the general2n-point analogue it uses 2n<3(n-1), hence is justified for n>=4; a tiny n2/n3 check must not apply it without a separate proof.

## Exhaustive direction inventory

Let H be the maximum separation of the source pair in a common row, and V the maximum separation of the source pair in a common column. Both are positive. A same-row pair gives W(a,b)>=|a|H; a same-column pair gives W(a,b)>=|b|V. Hence all admissible vectors satisfy

    |a| <= floor(74/H),  |b| <= floor(74/V).

Enumerate every nonzero integer vector in this exact rectangle, discarding gcd>1 and canonicalizing sign by requiring its first nonzero coordinate to be positive. For each remaining vector, project every source point or stop once the observed width exceeds74. A stop above74 is a complete rejection certificate; a surviving direction requires all148 projections and exact width/min/max verification. Equality74 is retained. Do not stop simply because four unsigned directions have already been found: all coefficient candidates must be exhausted or certified rejected.

Without any source measurements, each coefficient bound is at most74. The conservative enumeration ceiling is22,200 nonzero vectors and3,285,600 source-point projections before sign/gcd reductions. Canonical sign halves that loose coefficient count. The H/V witnesses and source validity justify the coefficient cutoff; observed performance or arbitrary coefficient caps do not.

For reviewable negative evidence, each rejected canonical vector can retain two source indices whose projection difference exceeds74. Each accepted vector retains its complete width and extreme witnesses, and its width is independently checked against all source points. This requires at most11,100 rejected-direction records before gcd reduction, eight accepted signed directions, and modest bounded memory. All direction candidates must appear in exactly one admitted/rejected category; nonprimitive and sign exclusions have arithmetic justifications.

## Lemma 3: at most five nonordinary canonical frames

Choose each admissible vector's canonical sign and sort the resulting at most four vectors. Examine every unordered pair u,v, using that sorted order as matrix rows. Keep exactly those with det(u,v)=+1 or -1. There are at most six pairs. The ordinary pair {(1,0),(0,1)} is always admitted because the full source has width73 on both axes; exclude that pair. At most five nonordinary canonical frames remain.

This six-pair scan replaces the initial assessment's unnecessary extended-GCD partner enumeration. It is exactly exhaustive after the eight-direction theorem. Any allowed ordered signed frame is a signed row permutation of one canonical pair. The corresponding reflection/transposition of the75-square maps all its translations and added cells to a representative with the same original-coordinate q. Thus canonicalization loses neither an exterior preimage nor an existence result; it avoids an orientation loop.

## Lemma 4: at most four candidate cells across all translations of one frame

For one row vector, write its projected interval as [m,M], of width w. All fitting integer translations are exactly t=-m+delta with delta in {0,...,74-w}. If w=73, the source occupies all74 projected levels twice, there are two translations, and each has exactly one deficient target level (its empty boundary level). If w=74, there is one translation; the75 target levels have aggregate spare capacity two, so there is either one empty level or two singly occupied levels. There are at most two deficient levels.

Therefore, for either coordinate, the total number of `(translation, deficient level)` choices is at most two. Taking their Cartesian product gives at most four `(translation vector, candidate cell)` choices across **all** placements of one frame, not four per placement. Discard any candidate cell already occupied by A(B)+t. This distinctness check is necessary when two singleton axes meet at an old point.

Every valid added point must be at the intersection of deficient axes, since adding to a level already holding two points creates an axis triple. Thus this enumeration is exhaustive for distinct valid additions. Recover q using the exact inverse of a determinant +/-1 matrix, verify the forward identity, discard q inside U, and deduplicate equal q across frames while retaining all or a canonical witnessing frame.

There are at most5*4=20 preimages before these exclusions and deduplication. Test each distinct eligible q against the C(148,2)=10,878 old pairs using exact determinants. This is at most217,560 pair tests. A first collinear pair certifies rejection for every affine frame sharing q. Since B is valid and affine maps preserve collinearity, these pairs exhaust all possible new triples. No old-triple census or SAT solver is required by this construction phase.

## Explicit tiny matrix and inverse examples

Consider the valid synthetic n4 source

    B4={(0,0),(1,0),(2,1),(3,1),(0,2),(1,2),(2,3),(3,3)}.

For A=[[0,1],[1,-1]], det(A)=-1 and A^-1=[[1,1],[1,0]]. The coordinate widths are3 and4. With t=(0,2), the two eligible cells are z=(4,0) and (4,4), with preimages q=(2,4) and (6,4). With t=(1,2), they are z=(0,0) and (0,4), with q=(-3,-1) and (1,-1). All four translations/cells together respect the four-candidate bound. Relative to the tiny protected box [-1,4] squared, (6,4) and (-3,-1) are exterior; the other two are conservatively excluded. These are candidate arithmetic examples, not claimed valid nine-point extensions.

For C=[[1,-1],[1,0]], det(C)=+1 and C^-1=[[0,1],[-1,1]]. With t=(2,0) and z=(0,4), q=(4,6); applying C to q and adding t returns z exactly. Signed row permutations give equivalent frame descriptions with the same q and need not be searched separately.

## Synthetic falsifiers and resource contract

The independent design helper `research/unimodular_extension_independent_design_tiny.py` exhausts all11 full-axis valid n4 sources. It compares the coefficient-bound inventory with all vectors in [-4,4]^2; checks the mod3 injection and eight-direction bound; compares canonical frame/preimage sets with every determinant +/-1 matrix in the full coefficient box; compares deficient-axis candidates with all distinct target cells; checks exact inverses; and compares original-pair obstructions with all target triples. All72,171 matrix coefficient cases,16 canonical non-axis frames and56 candidate geometry checks passed. Evidence is `data/unimodular-extension-independent-design-tiny.json`. This is a pure design falsifier, not a production worker or an actual-source inventory.

Production source/tiny work, if separately accepted, must test rejected-width equality boundaries, source-invalid rejection before the width theorem, H/V cutoff completeness, exhaustive inventory completion, duplicate/sign/frame normalization, both determinant signs, missing translation, occupied singleton intersection, protected-box boundaries, repeated q, exact rejection witnesses, and interruption during each phase. Independently verify any saved negative certificate rather than trusting enumeration counters alone.

The hard construction ceilings are22,200 coefficient vectors,3,285,600 projections, six canonical pair determinants, at most five nonordinary frames, at most20 distinct-cell preimages before filters, and217,560 new-pair determinants. Source authentication/dual validation, certificate checks, hashes, target validation and I/O are additional bounded work and must share the same proposed25-second cooperative /30-second owned /256-MiB envelope. These counts are not a timing guarantee. Keep deadlines inside projection and pair loops and throughout final identity/certificate checks. A validated149 candidate is saved immediately; deadline or pin failure clears whole-family completion/closure while preserving an already saved artifact for independent assessment.

There is one family and one possible future allocation, with no coefficient expansion, source change, retry, repair, nonunimodular fallback, or alternative target. A completed negative closes only the exact selected-source exterior family above. Partial inventory or unchecked candidates establish no exclusion. The proposal remains DESIGN ONLY until independent mathematical/scope review and an explicit Root source/tiny implementation decision; actual selected-source measurements remain separately unallocated.
