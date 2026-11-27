# Centered n73 fixture: one four-orbit deletion proposal

Arithmetic/proposal only. No checker implementation, n79 candidate geometry,
secants, validator execution or host search was performed for this proposal.
The previously accepted zero-deletion check independently dual-validated this
n73 fixture and rejected all eight centered near-quarter extensions. The
completed n71 one-orbit cases remain closed and must not be repeated.

## Fixed source and finite scope

The decoded source is `data/published-n73-rct4-candidate.json`, byte SHA-256
`0c99133e2025005e99a702a8538752aa58ee763f4a01d6531f8015c423db29ae`,
normalized hash
`2e7f40e3be9a53dda71ee01ee076b30f8ad632707d14cc51616afbeb752b798b`.
Its146 points comprise36 complete four-orbits and the diagonal pair
`(17,17),(55,55)`. Translate by `(3,3)` to center39, retaining that same pair
at `(20,20),(58,58)`. Delete exactly one original complete four-orbit and add
exactly four complete off-diagonal four-orbits, allowing exact readdition.
The resulting cardinality is146-4+16=158. No other original point or exceptional
pair changes are in scope.

The coordinate-only case list in
`data/n73-one-orbit-repair-cases.proposal.json`, SHA-256
`ca6147bee2ae9bcde4118f2ccdfb855af87c44cd5dd49e2aa3ec60580fbeabae`,
contains all36 source orbits in lexicographic order, their exact coordinates,
inner radii and arithmetic counts. The unique central case is index3:
`(1,36),(36,1),(36,71),(71,36)`, with inner radii0,35. Uniqueness also follows
from two points in the central row and a noncentral diagonal pair. All other
35 cases have two positive distinct inner radii. The future checker must verify
this exact coverage against the pinned dual-validated source.

## Completeness and counts

Retained old rows/columns stay saturated except those freed by the removed
orbit. New points can therefore use only its two inner absolute radii and the
three positive outer radii37,38,39. Each positive inner radius has residual
quotient demand1, while each outer radius has demand2. A central-radius orbit
contributes two points to the central row, so its quotient demand is likewise1,
not2. Total quotient demand8 requires four new four-orbits.

Each candidate orbit is a labeled edge between distinct radii. There are two
orientations between positive radii and one for an edge incident to zero.
Equal radii would lie on excluded diagonals. Full row loads imply corresponding
column loads by quarter-turn symmetry. Degree feasibility is necessary and
complete only for these occupancy conditions; it is not geometric validity.

| Deleted orbit endpoints | Labeled edges | Raw four-edge subsets | Degree choices | Exact readdition |
|---|---:|---:|---:|---:|
| Both inner radii positive |20|4,845|124|8|
| One inner radius zero |16|1,820|62|8|

For positive endpoints a,b, classify by the inner-inner edge. Selecting either
of its two orientations leaves an outer triangle, giving2×8=16 choices.
Otherwise a,b each attach to an outer vertex. Attaching both to the same outer
vertex gives3×2²=12 possibilities; the other two outer vertices require both
parallel edges. Attaching to distinct outer vertices gives3×2×2²=24 attachment
choices; the remaining outer degrees1,1,2 force two edges through the degree-two
vertex with2² orientations, giving96. Thus16+12+96=124.
When a=0, the inner-inner orientation count and the a-outer orientation count
both halve, yielding8+6+48=62. If the exact removed edge is readded, the three
remaining edges form the outer triangle, giving exactly2³=8 readditions in
every case.

Independent arithmetic enumeration of every four-edge subset for each actual
source radius pair agrees. Evidence is
`data/n73-one-orbit-repair-arithmetic.json`, SHA-256
`946851d055372c5d41e231be3cbca647f5afd441ef535d19ada4c828ccbeeb59`.
Totals are35×124+62=4,402 records from171,395 raw subsets. Of these,36×8=288
readdition records recreate the same eight already checked zero-deletion sets;
4,114 records do not readd the removed orbit, before retained-overlap and
geometry filtering. These are upper enumeration counts, not valid solutions.
A nonoverlapping set missing exactly one original orbit identifies its deletion;
that uniqueness must not be applied to malformed overlapping selections.

## Minimal proposed evaluation after mathematical review

The current monotone per-orbit filter applies unchanged in principle. At most
35×20+16=716 candidate orbits require filtering across all cases. A candidate
already overlapping retained source points is rejected explicitly. In a
positive-endpoint case the opposite inner-inner orientation may be a retained
source orbit; do not silently merge it with the removed orientation or assume
it is absent. All other candidate edges touch a previously empty outer radius.
For each disjoint orbit, exact determinant checks against retained points and
within that orbit retain an explicit collinear triple if blocked. Such a triple
persists in any superset, soundly rejecting every degree choice containing the
orbit. If the remaining graph admits no required degree factor, no complete
158-point verification is needed for that case. Every surviving selection
still receives exact cardinality, distinctness and row/column assertions plus
both unchanged complete geometry validators, covering cross-orbit conflicts.

After independent mathematical approval, prepare a minimal standalone checker
and tiny arithmetic/filter tests. Frozen n71 enumeration helpers hardcode four
outer radii and five selections, so they cannot be silently repurposed. A new
parameterized pure helper may express three outer radii/four selections while
reusing frozen point construction, exact filtering, verification and atomic
publication. Do not monkeypatch published globals or modify paired/packed or
previous finite-checker sources. There is no resume, new guard, queue or
checkpoint protocol.

Propose only one Root-owned30s/256MiB evaluation, with a single25s soft deadline
covering all36 cases including source validation. Use a fresh absent output
directory, provisionally `data/n73-one-orbit-repair-v1`, and no overlapping
numerical worker. All4,402 choices, including all288 readdition records, remain
in the declared coverage. Reports must identify complete, partial and unstarted
cases, preserve negative triples/overlap evidence, dual-check every final
survivor, and persist any verified witness immediately before early return.
A timeout or hard kill cannot support a complete-family negative conclusion.

The previous n71 monotone filters were cheap, and this arithmetic batch has
fewer degree records and individual orbit filters than the completed n71 batch.
However the retained n73 base has142 points and different conflicts; surviving
edge distributions and final-validation cost are unknown. No wall-time fit is
promised. A partial invocation closes only independently audited completed
cases, with no implicit retry allocation.

A complete clean negative with independent evidence review would close only
near-quarter centered extensions of this particular n73 fixture with at most
one original complete four-orbit deleted, including exact readdition. It would
not close more deletions, other fixtures/embeddings, unrestricted extensions,
or n79 generally. This proposal alone authorizes neither source implementation
nor an actual allocation before the requested mathematical review.
