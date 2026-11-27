# Score11 exact completion of six connected eight-edge patches

Read-only incidence/quota design; no implementation, candidate geometry,
secant calculation, new scoring or host run was performed. The preserved source
is `data/trades-n79-seed270079-state.json`, byte SHA-256
`9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26`,
normalized identity
`f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d`.
It has158 points, two per row/column, and the independently audited11 triples.
The valid incumbent remains156.

## Pruned alternatives and a distinct small scope

The source's degree-two bipartite row/column graph has components of4,12 and142
edges. Only the142-edge component intersects every old conflict triple. Deleting
that whole component would free71 rows and71 columns:5,041 candidate cells and
142 removed points. That is a much larger search without a justified reduction;
prune the whole-component route.

The audited minimal cover
`C={(33,78),(78,78),(78,0)}` consists of three consecutive edges on that large
cycle. It hits all11 original triples. A connected source-cycle path containing
C therefore leaves valid retained geometry. There are exactly k-2 such paths
of length k for the small lengths considered. Six-edge paths give only four
patches, with a4×3 freed rectangle. Their158 completions have effective source
deletions at most4, and157 completions at most5. Once the combined cap-five
negative is independently accepted, this branch repeats closed scope and
should be pruned.

The first useful larger choice is all six eight-edge paths containing C. Each
frees exactly a5×4 or4×5 rectangle:20 cells, versus up to64 for arbitrary eight
point deletions. The retained150-point set is valid by the complete old-triple
census. Fill exactly eight cells for158 or seven for157. This is an exact
completion of one connected original patch, rather than merely a score move.
A simple alternating cycle alone need not remove both shared-column anchors;
no claim is made that the final symmetric difference must be one simple cycle.
It may contain several alternating cycles meeting at a vertex. The scope is
connectedness of the *original deleted patch*, not all connected trades.

## Exact quota counts and effective deletions

Ignoring geometry, the source path's residual demands are1 at its two endpoint
vertices and2 at its interior vertices. For a5×4 orientation the row vector is
(1,2,2,2,1) and all four column demands are2; transpose gives the same counts.
Independent binary-matrix enumeration gives:

| Effective deletions from original source |158 factors/path|157 factors/path|
|---|---:|---:|
|0|1|0|
|1|0|8|
|2|15|36|
|3|24|174|
|4|62|412|
|5|56|584|
|6|36|424|
|7|8|148|
|8|2|26|
|Total|204|1,812|

Effective deletion is `D minus readded original cells`, not the raw eight-point
patch. For157, seven insertions can leave effective deletion eight. All7-cell
subsets respecting residual capacities are included, including those that
cannot extend to an8-cell completion. Restricting to full factors minus one
point would be incomplete.

After independently accepted cap-five closure, each path has46 new158 factors
and598 new157 factors,644 combined. Across six templates there are at most3,864
raw candidate/template records before duplicates or geometric filtering. Without
that prerequisite, retain all12,096 records and make no cap-five prune.
Exact six deletion sets and full arithmetic are in
`data/score11-connected-patch-arithmetic.json`, SHA-256
`e42e0dfb86c46f11b59b74fb7b0f858ba88439e66455b3da762ca3a2674c3610`.
They were derived from source incidence and quota arithmetic only.

Requiring effective deletions to hit all eleven stored original conflict triples
is another purely combinatorial prefilter. After the cap-five prune it leaves
80 full158 and1,226 partial157 records,1,306 total across six templates, before
duplicates or new geometry. Full survivors at effective deletion6/7/8 number
44/24/12; partial survivors number582/488/156. The per-template full counts are
19,11,10,10,11,19; partial counts are266,176,171,171,176,266.

## Relation to the paired three-rotation proposal

The paired proposal has144,400 simultaneous-rotation tuples in one fixed
matching decomposition and21 incident rows. Raw effective deletion is at most6
for its158 outputs, and at most7 after deleting a retained source point for157.
Each path8 template has ten158 factors with effective deletion7 or8, and 26 157-point
factors with effective deletion8. Thus60 full-size and156 partial-size raw
records across the six patches are outside those cardinality limits. Additional
path factors can also involve rows outside the paired row pool. The scope is
therefore distinct, though smaller-effect factors may overlap other work.

The arithmetic count reduction is at least144,400/3,864≈37.4 in candidate
records under cap-five closure, but these are different restricted scopes and
there is no success-probability or runtime comparison. No safe-cell census or
new geometry was measured. Retained secants may reject all factors. This is a
bounded complementary branch, not evidence that it is more promising than
paired rotations or that the source is globally repairable.

## Minimal future check after mathematical review

After independent mathematical/manifest approval, prepare a standalone checker
and tiny tests, preserving all frozen sources. Dual-check source identity and
all11 conflicts, reconstruct the six exact source-cycle intervals and require
the approved cap-five combined evidence before omitting effective deletion≤5.
Stream exact20-cell quota factors; no large solver, visited history, new guard
or resume protocol is needed. One patch needs only20 Boolean cells and small
row/column counters, with150 retained points. The bounded structural state is
well below256MiB; actual process RSS remains a host measurement.

Filter each candidate cell exactly against retained secants, then check new-new
conflicts and row/column capacities. Every surviving157/158 final receives both
complete exact validators and immediate atomic witness persistence with exact
source/patch metadata. The report must distinguish declared, filtered and
completed factors, complete/partial/unstarted patches, and any duplicate
candidate/template records. A timeout cannot imply closure.

Propose one separate Root-owned30s/256MiB evaluation with a shared25s soft
budget including source/evidence validation, fresh output and no concurrent
numerical worker, only after source/tiny review. This proposal authorizes no
implementation or run before the requested mathematical review. A complete
clean negative would close only these six connected eight-edge patches of this
fixed score11 source. It would not exclude all eight-deletion repairs, all
connected trades, other sources, or global n79 existence.
