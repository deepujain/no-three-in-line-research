# Nonuniform coordinate insertion from a full n74 source: design only

This is a conditional finite-family design, not an experiment allocation or a result. No n74 source has been fetched, read, decoded, embedded, or scored for this proposal. Preserve the historical four-embedding proposal separately; its direct probe is curtailed by the prior fixed-geometry free-cell report. Source attribution, exact record selection, source authentication, independent validity checks, and prior-scope review remain required before an implementation pilot.

## Family and distinction from the curtailed scope

Assume B is a valid 148-point set on coordinates 0 through 73, with two points in every row and column. For gaps c,r in 0 through 74 define

    f(c,r)(x,y) = (x + [x >= c], y + [y >= r])
    T(c,r) = f(c,r)(B) union {(c,r)}.

The map is injective and its inserted row and column are empty before the new intersection is added. Each target has 149 distinct points in the 75-square, two per old row and column and one in each inserted axis. Exclude the four cases with both c and r in {0,74}. The remaining family contains exactly 5,621 gap choices, before any symmetry quotient or coincidence between resulting sets.

A nonuniform insertion changes the geometry among old points. The reported scan of every free cell of a single fixed n74 embedding does not by itself cover this family. This observation is a scope distinction, not a novelty or empirical promise claim. The analogous closed n79 insertion family concerns a different source and target. A later source-specific prior-scope audit could still curtail this proposal.

Every target triple consists either of three mapped old points or of the new intersection and two mapped old points. These two classes are disjoint and exhaustive.

## Old triples become constant-determinant rectangles

For any old triple, partition the 75 column gaps into at most four inclusive intervals on which its three indicators [x_i >= c] are constant. Thresholds are the sorted distinct source x-values: intervals end at a source value and the next interval starts one above it. Do the same for row gaps. On each of at most 16 resulting rectangles, all mapped points are fixed and their determinant is constant. A zero determinant excludes the entire rectangle.

There are C(148,3) = 529,396 old triples, hence at most 8,470,336 rectangle tests. The four rectangles where both coordinate shifts are uniform across the triple preserve the original nonzero determinant and may be skipped after the source is independently certified valid. This gives the sharper ceiling 12 C(148,3) = 6,352,752 tests. Empty intervals must never be emitted. The four excluded both-boundary target cases are thereby never specifically reconsidered.

## A new point and an old pair become clipped lattice lines

For each old pair, the column and row threshold partitions have at most three intervals each. On each of at most nine rectangles, the mapped pair p',q' is fixed. Set

    A = q'_x - p'_x, B = q'_y - p'_y,
    C = B p'_x - A p'_y.

Its determinant with z=(c,r) is A r - B c + C. Original horizontal and vertical pairs can be skipped: their mapped old row or column differs from the inserted row or column. All other pairs have A and B nonzero. With g=gcd(abs(A),abs(B)), all integer solutions on the line are

    (c,r) = p' + t (A/g, B/g), t integer.

Intersect exact integer t-ranges from each coordinate interval, using signed floor and ceiling correctly. An alternative oracle scans column gaps and tests divisibility and row membership. Across all rectangles of a pair, that oracle visits at most 3*75=225 candidate columns: column intervals partition all 75 gaps and there are at most three row bands. Thus primitive enumeration has at most 97,902 rectangle setups and at most 2,447,550 visited line points, using C(148,2)=10,878. Each gap belongs to exactly one rectangle per pair, so a pair cannot contribute twice to one target. Explicitly discard the four excluded both-boundary solutions before storing any obstruction.

## Cover gaps once instead of maintaining full scores

Use bit index 75*c+r in a 5,625-bit integer. Initialize `uncovered` with exactly the 5,621 included gaps. An old zero rectangle removes all uncovered gaps in that rectangle at once. To construct its mask, precompute

    column_repeat[c0,c1] = sum(2**(75*c) for c in c0..c1)
    row_run[r0,r1] = ((1 << (r1-r0+1))-1) << r0
    rectangle_bits = column_repeat[c0,c1] * row_run[r0,r1].

The shifted row runs occupy disjoint 75-bit column bands, so the multiplication has no cross-band carries. Compute `hit = uncovered & rectangle_bits`, remove `hit`, and assign a first old-triple obstruction only to its set bits. New-point line solutions similarly remove a bit and record the responsible pair only if it is still uncovered. Across the whole computation, at most 5,621 first obstructions are stored. There is no scan of all pending gaps for each rectangle and no need for a target-score histogram.

If all included bits become covered at any stage, the stored exact obstruction for every gap proves the finite family negative without finishing all possible score calculations. Report this as certificate-complete exclusion, not a complete score census. If bits remain, they are merely unexcluded until both triple classes have been completely processed. Only then can a remaining gap be a zero-conflict candidate; reconstruct it, independently dual-validate it, and save immediately. A deadline-limited run with remaining bits provides no positive result and no complete exclusion.

## Resource limits and falsifiers before any pilot

At most 2,850 column interval masks are needed. Their conservative logical payload is about 2 MiB (each at most 704 bytes), plus Python object overhead; row masks are small. One uncovered integer and at most 5,621 obstruction records suffice. Compact 32-bit records can encode a kind and two or three 8-bit source indices, about 22.5 KiB of logical certificate data. An implementation using Python tuples must account for their larger footprint honestly. Rectangle construction uses bounded 5,625-bit by at-most-75-bit arithmetic; this is not free or constant-cost CPU work. The operation bounds do not guarantee a 25-second completion.

Required independent tiny falsifiers include exhaustive full-axis valid sources for n=2 through 4 and all gaps; separate old/new class comparisons with an exhaustive full-target determinant oracle; rectangle bit masks against direct enumeration; signed line clipping and divisibility; boundary exclusions; obstruction membership and mapped collinearity; complete-negative early termination; and rejection of incomplete-positive claims. Lifecycle tests must include deadlines during precomputation, triple iteration, pair rectangles, certificate extraction, final pins and saving. The source must be authenticated and valid before the uniform-translation shortcut is used.

If centrally symmetric source structure is later established, the centered insertion c=r=37 is automatically invalid: it preserves half-turn symmetry and adds its center. Any odd-cardinality half-turn-invariant set with more than one point contains its center and an antipodal pair, a collinear triple. This only eliminates that centered case, not arbitrary noncentral gaps.

A separately reviewed implementation and tiny evidence may justify asking Root for one bounded 25-second cooperative / 30-second owned / 256-MiB pilot. This document allocates no worker time and authorizes no source import, census, search, proof replay, or automatic continuation.
