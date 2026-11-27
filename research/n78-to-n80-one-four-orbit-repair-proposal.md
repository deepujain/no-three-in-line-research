# Centered n78 full-C4 fixture to n80 after one orbit deletion

Arithmetic/proposal only. No checker implementation, n80 candidate point-set
construction, geometry verification, secants or host search was performed.
This auxiliary finite n80 exploration preserves n79 as the primary problem.
The reported n80 literature baseline156 and absolute160 ceiling are context;
no novelty claim follows from this proposal. Closed n79 repair neighborhoods
are not used to prune or infer anything about n80.

## Fixed source and family

`data/published-n78.json` has byte SHA-256
`4c13bf3e807885f9e61d00593bb27d060b773e40d887f63d955d962d9890a912`.
It attributes the archived `n78_rot4.few` certificate to Thomas Prellberg and
records previous independent determinant verification. This proposal checked
only existing coordinates, cardinality, row/column loads and rotation closure;
it did not rerun that geometry validation. A future actual checker must first
dual-validate the exact pinned source.

The156 distinct source points have two per row and column and form39 complete
four-orbits under `(x,y) -> (y,77-x)`. All39 source orbits are listed in
`data/n78-to-n80-one-orbit-cases.proposal.json`, SHA-256
`687e33121e0365efe2b6e94ac6dc501c1ab0f3cae55bf20654b7a37ed23a8e4a`.
There are38 distinct-radius orbits and exactly one diagonal loop, source index38:
`(36,36),(36,41),(41,36),(41,41)`, radius2.5 about source center38.5.

Translate by `(1,1)` into n80, preserving center39.5 and saturating old rows and
columns1..78. Delete one complete original four-orbit and add exactly two
complete four-orbits, producing156-4+8=160 points. There is no exceptional
half-turn pair in this full-C4 even-grid family. All other source points remain.
Half-integer radii are represented exactly as positive odd doubled radii; the
new outer radius39.5 is encoded79.

## Occupancy cases, including diagonal loops

Only the new outer radius w=39.5 and the deleted orbit's inner radius endpoints
have any residual capacity. A distinct-radius deletion u,v frees demand1 at
each inner endpoint; w has demand2. Deleting a diagonal orbit u=u frees demand2
at u, and w still has demand2. An ordinary oriented four-orbit is an edge with
two orientations between distinct positive radii. A diagonal four-orbit is a
single loop and contributes degree2 at its radius. Both must be included before
any geometric prune.

| Deleted source type | Source cases | All free-radius labeled orbits | Raw two-orbit subsets | Degree choices | Contain outer loop | Remaining |
|---|---:|---:|---:|---:|---:|---:|
| Distinct u,v |38|9|36|6|2|4|
| Diagonal loop u=u |1|4|6|2|1|1|
| Total |39| |1,374|230|77|153|

For distinct u,v, four choices consist of one w-u edge and one w-v edge with
independent orientations. But two additional occupancy-feasible choices are
the outer loop at w plus either orientation of the inner u-v edge. Inner loops
are individually incompatible with demand1 and produce no other factors.
For a deleted loop, one choice uses both parallel w-u orientations, while the
second readds the inner loop and selects the outer loop. These exhaust the
degree constraints. Exactly one choice in each deletion readds its exact source
orbit, giving39 readdition records, all among the77 outer-loop alternatives.
Thus153 is the count **after** the outer-loop argument below;230 is the raw
occupancy-feasible count. The preliminary at-most156 bound is valid only as a
bound on the remaining candidates, not the raw loop-inclusive enumeration.

Independent integer degree enumeration over every actual source radius pair
agrees. Evidence is `data/n78-to-n80-one-orbit-arithmetic.json`, SHA-256
`353bd42edb20a5d0f4a2b9c6984612a66c77990db8e504c7d6ab02e89d412d3e`.
It constructs labeled doubled-radius edges/loops only, not candidate point sets.

## Exact outer-loop obstruction

The new outer loop consists of n80 corners. For any nonloop deletion, the old
diagonal loop remains, translated to
`(37,37),(37,42),(42,37),(42,42)`. Its two main-diagonal points plus an outer
main-diagonal corner give a collinear triple, so both outer-loop alternatives
are impossible. When the unique old loop is deleted, the only degree-feasible
choice containing the outer loop necessarily readds that same inner loop,
producing the identical obstruction. For example the coordinates
`(0,0),(37,37),(42,42)` are a symbolic exact negative certificate in all77
cases. They are proposed proof coordinates; no candidate geometry evaluation
was executed here.

Consequently all39 exact readditions are rejected. The same old-loop argument
also rejects the zero-deletion centered extension, whose only possible extra
four-orbit is the outer loop. The remaining153 choices contain only outer-inner
orbits. Such new points cannot overlap the retained embedded source, since
every new point has an outer coordinate while every retained point has both
coordinates1..78. A future checker should still assert distinctness and no
overlap defensively.

## Minimal proposed bounded test after mathematical review

Propose a new standalone finite checker and tiny tests only after independent
mathematical/manifest review. Use exact doubled-radius even-grid formulas.
Frozen odd-grid n71/n73 orbit constructors assume integer centers and exclude
diagonal loops, so they are unsuitable without new helpers; do not monkeypatch
or modify them. The generic frozen determinant filter, exact full verifiers
and atomic writer remain reusable. No new guard, resume, queue or protocol is
needed, and paired/packed/frozen previous checks remain unchanged.

For maximum audit clarity, retain all230 degree records, with the77 outer-loop
records linked to the exact proof/triple rather than silently omitted. Check
the remaining153 choices using the same monotone per-orbit filter against the
152 retained points. At most38×4+2=154 individual outer-inner orbits need such
filters across cases, with repeated global orbits allowed across different
retained bases. Record an exact blocking triple for a filtered orbit; reject any
full selection containing it. Every surviving160-point final receives exact
cardinality, distinctness and row/column checks and both full geometry
validators. Conflicts between the two new orbits remain covered. Save a verified
witness immediately with exact fixture/deletion metadata and no novelty claim.

Only after source/tiny approval propose one Root-owned30s/256MiB evaluation,
with one shared25s soft deadline across source validation and all39 cases, a
fresh absent output directory, provisionally `data/n78-to-n80-one-orbit-v1`, and
no overlapping numerical worker. Reports must distinguish complete, partial
and unstarted cases and proof-rejected versus geometrically checked records.
All230 raw degree records, not merely153, define complete declared coverage.
Previous cheap monotone-filter checks support this small measurement but do
not guarantee its runtime. Partial/missing output supports no complete-family
negative result and supplies no implicit retry allocation.

A complete clean negative with independent actual evidence review would close
only this centered full-C4 extension of this fixed n78 fixture with at most one
original complete four-orbit deleted and two added, including readdition. It
would not close more deletions, other fixtures/embeddings, unrestricted n80
solutions, or the primary n79 problem. This proposal authorizes no source or
host evaluation until the requested mathematical review and Root allocation.
