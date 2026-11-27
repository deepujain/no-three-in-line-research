# Retained-secant and flow bounds for connected paths of lengths 10, 12 and 16

Design and source-incidence arithmetic only. No candidate geometry, safe-cell
census, flow evaluation on actual safe cells, or geometric completion has been
executed. Implementation model: gpt-6.1-sol, high. Preserve all frozen checkers.

Use the exact score11 source at
`data/trades-n79-seed270079-state.json`, bytes SHA256
`9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26`,
normalized SHA256
`f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d`.
The source has 158 points and exactly eleven independently audited conflicts.
Its row/column incidence graph has cycles of lengths 4, 12 and 142. The cover
`C={(33,78),(78,78),(78,0)}` consists of three consecutive edges on the large
cycle and intersects every original conflict triple.

Enumerate every length-k interval of that 142-edge cycle containing C for
each k in {10,12,16}. For these lengths there are exactly k-2 distinct windows.
The path endpoints lie in one axis partition, so freed axes have sizes
k/2+1 and k/2. No retained source point lies inside the freed rectangle:
every interior vertex already has its two source edges in the path, and the
endpoint vertices cannot connect back into the path in this 142-cycle.

|Deleted path length|Cases|Freed rectangle|Cells per case|Cell records|Retained points|
|---:|---:|---:|---:|---:|---:|
|10|8|6 by 5|30|240|148|
|12|10|7 by 6|42|420|146|
|16|14|9 by 8|72|1008|142|
|Total|32|||1668||

Exact deletion sets, axes and residual capacities are frozen in
`data/score11-connected-paths-flow-census-cases.proposal.json`, SHA256
`68415d1e67a99fc90c7ca3c0f47db4de8e0c2f9bf9f9fc8d2313ec10857abbe5`.
This manifest was derived only by traversing the source incidence graph and
counting axes. No length-eight case is included or reevaluated.

For a patch D, let R be the source minus D. R is valid because D contains C.
Any feasible added point must be in a row and column freed by D; other axes
are saturated at two source points. Enumerate this entire rectangle, excluding
retained points explicitly, and keep a cell p exactly when the frozen
`point_conflicts(p,R)` is zero. Original source cells in D are eligible for
readdition under the same test. Record total safe cells, safe original
readditions, safe new cells and the complete sorted safe-cell set. This filter
tests two-retained/one-added triples only.

Build a bipartite integral-capacity flow network on these safe cells. The
source-to-row capacity is `2-retained_row_count`, each safe row-to-column edge
has capacity one, and each column-to-sink capacity is
`2-retained_column_count`. An integer max flow F is the maximum number of safe
cells that can be added while respecting both axis capacities. It is an upper
bound on geometrically valid insertions, since triples containing two or three
added points are deliberately ignored in this census.

The final-cardinality upper bound is exactly `158-k+F`. Record both a primal
flow assignment (selected safe-cell edges) and a residual-reachable minimum
cut; independently check capacity feasibility, flow conservation and equality
of flow value and cut capacity. At most k augmentations are needed because
each augmenting path uses a unit-capacity safe-cell edge and total row
capacity is k. Use a small deterministic exact augmenting-path algorithm,
with deadline checks during BFS and augmentation; no solver dependency.

If the bound is at most 156, this patch has no 157/158 completion, including
completions that readd deleted original points. If the bound is at least 157,
save the complete safe-cell set, capacities, bound and certificates as an
eligible patch for a separately reviewed geometric-completion proposal.
Eligibility proves no geometric completion and makes no witness claim.
No cap-five evidence or effective-deletion pruning is needed for this bound.

Prospective bounded state: at most 150 retained points (148 for the actual
length set), 72 cells, 19 flow vertices and 89 forward arcs per case. Across
all 32 cases the direct normalized-direction filter needs at most 239976
point-direction records; these are operation counts, not measured runtime.
There are at most 424 unit augmentations across the entire family. Stream one
case at a time; the complete small output can retain all 1668 safe-cell records.
No numerical evidence or benchmark has been obtained for this proposal.

After mathematical approval, prepare a new standalone source and tiny tests,
reuse frozen exact source/geometry and atomic helpers, and request independent
source review. Tiny tests should compare safe-cell filtering against direct
determinants on small fixtures, compare flow with exhaustive subsets on small
networks, check primal/cut certificates, reconstruct all 32 manifest windows,
and verify timeout accounting. Only then propose one fresh Root-owned
30-second/256MiB allocation with a shared soft deadline at most 25 seconds,
including source validation, census and flow. No automatic retry, scheduler,
checkpoint, resume protocol or concurrent numerical worker is introduced.

Every case reports unstarted, partial-safe-census, partial-flow or complete.
Cell checks and whole cases have separate started/completed counters. A
timeout cannot close the pending case or unstarted cases. Completed bounds
close only their exact original connected patches of this pinned source;
they do not exclude other connected trades, other lengths, other sources,
all k-deletion repairs or n79 existence.
