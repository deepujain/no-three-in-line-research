# Residual incidence and anti-diagonal bounds for reflection row batches

Status: mathematical proposal only, prepared by the Mathematical Reviewer (`gpt-6-astra`, high). No frozen source, checkpoint or search history is changed. No numerical experiment or n79 model construction was run. Independent proof review, tiny oracle tests and measured cost evidence are required before integration or allocation. This proposal concerns the current diagonal-reflection 2n-1 family only.

## Necessary residual graph

Fix a coherent partial state S in slice (d,t), including its single diagonal point (t,t), and define the remaining demand of row r by `b_r = target_r - rows_r`. Each b_r is 0, 1 or 2. Reflection makes column demands identical. The off-diagonal orbit `{(x,y),(y,x)}`, with x<y, contributes one unit to each of rows x and y.

Construct a simple graph G on the rows with positive demand. Include edge {x,y} exactly when that unselected mirror orbit is individually admissible with S, using the current exact mirror-pair predicate. Let `B = sum b_r` and `R = B/2`. At a coherent state B is even: each future orbit supplies two points. For n79 there are at most 79 vertices and 3081 possible edges; this is a small per-state graph, not a search-history cache.

Every valid completion determines an edge subset F of G with degree `deg_F(r)=b_r`. Indeed, every future orbit in a completion is already individually admissible with S: deleting other future points cannot create a collinear triple or violate occupancy/axis caps. G is therefore a relaxation of the remaining geometry. Edges that are individually admissible may still conflict with one another; nothing here treats the relaxation as sufficient.

This gives the following concrete rejection checks, all on one completed admissibility scan:

1. **Row shortage.** Reject if any `deg_G(r) < b_r`. Check every deficient row, rather than relying on which row wins the existing minimum-domain tie.
2. **Component parity.** For every connected component C of G, reject if `B_C = sum_{r in C} b_r` is odd. All future edges incident to C lie inside C, so a completion supplies exactly twice its number of selected C-edges.
3. **Bipartite component balance.** If C is bipartite with sides A and D, reject if `sum_{r in A} b_r != sum_{r in D} b_r`. Every selected edge supplies one endpoint to each side. Run the test only after checking bipartiteness; an odd cycle is not itself a rejection.

Components are computed on the complete current admissibility graph, including every declared candidate edge, not a sampled or truncated graph. An interrupted scan is unknown and cannot justify any rejection. Rows of zero demand have no available incident edge and are excluded. An empty graph at B=0 is the existing full-state case, not a failed component test.

## Anti-diagonal capacity

Assign edge {x,y} the integer color `s=x+y`. Both points of its mirror orbit lie on the anti-diagonal line of equation X+Y=s. A full valid set can contain at most one selected mirror orbit of a given color: two distinct such orbits would put four distinct points on that line. A color already occupied by any point of S cannot be used by a future mirror orbit, because that orbit adds two points on the same line. The existing exact admissibility predicate already removes those occupied colors, including 2t for the initial diagonal point.

Let K be the set of colors among G's edges and K_C the colors among edges of component C. The same scan yields two additional necessary checks:

- Reject if `|K| < R`.
- For each component whose demand parity passed, reject if `|K_C| < B_C/2`.

The proof is direct: a completion needs exactly R edges globally and B_C/2 in C, with distinct colors. The global test matters because components can share colors. The individual component tests do not establish that different components can simultaneously obtain disjoint colors. Full matching or subset-of-components capacity algorithms are not part of this initial proposal.

These color bounds incorporate a definite line-blockage constraint beyond row degrees without materializing arbitrary line catalogues or pairwise orbit-conflict graphs. Available sums range from 1 through 2n-3, so at n79 a 155-bit set suffices. Count bounds are small Python integers; there is no numerical tolerance.

## Why the checks can add information

The following are abstract residual graphs, not claims of reachable geometric states. They demonstrate strictness over degree checks and delineate the test cases needed:

- Two disconnected triangles with demand one at every vertex pass every local degree test and have even global demand six. Each component has odd demand three, so component parity rejects.
- K(2,3), with demands (1,1) on the two-vertex side and (1,1,2) on the three-vertex side, has even total demand six and enough degree at every vertex. Its side demands two and four differ, so bipartite balance rejects.
- K(2,2) on sides {0,1} and {2,3}, with demand two at every vertex, passes degrees, parity and side balance. Four future edges would be required but their sums are only {2,3,4}, so the color bound rejects.

The proposal is not an exact b-factor solver and does not solve the remaining no-three-collinear problem. Passing all checks leaves the original row-batch branching and exact insertion checks responsible for geometry.

## Narrow implementation shape, after approval

Initially implement only a pure scratch predicate in a separate tiny research module. It consumes an exact residual demand vector and complete admissible edge list and returns either pass or a deterministic named necessary-condition failure. It changes no geometry and chooses no branch. Retain canonical orbit IDs and row order; do not add forced-edge insertion, global ID pruning, new search objectives or learned state.

The existing row-domain computation already evaluates every candidate mirror orbit from its incident rows. A later approved implementation could build each edge once in canonical order, retain per-row edge IDs for the unchanged MRV choice, and compute the connected-component/bipartite/color summaries in O(n+|E|) extra work. Use bounded scratch arrays or row bitsets; avoid persistent per-depth caches. Work and deadline checks cover construction and all graph passes. On failure return an empty candidate list only at a coherent counted node; a full-state result retains the current leaf handling. Named prune counts must be distinguished from logical node/witness counters.

Any integration changes branch-tree pruning and source identity even if survivor order is unchanged. Existing accepted frontiers cannot be silently rebound to the new sources. Start from a separately authorized genesis or design and review explicit compatibility semantics; this proposal supplies neither migration nor authority to edit the active frozen reflection chain.

## Tiny exhaustive oracle plan

Before any larger execution, enumerate every off-diagonal orbit subset for every slice (d,t) at n2, n3, n4 and n5. This is at most `n^2 * 2^(n(n-1)/2)` raw selections for each n (25,600 at n5), before filtering. Use direct point expansion, exact determinant triples and independent row/column/type checks to identify valid partial states and full completions. Do not obtain validity or completion existence from the new graph predicate.

For each valid partial state, independently build admissible edges by testing the expanded S plus each orbit with the determinant oracle, and cross-check the frozen fast predicate. Determine whether at least one independently enumerated valid full set contains S. Assert that every rejected state has no full completion. For every full set and every partial orbit subset of it, require all bounds to pass. Compare exact full certificate sets and their existing dual-verifier digests, not just aggregate visit counts.

Separately exhaust tiny abstract graphs/demands and enumerate all exact-degree edge subsets. Graph checks must not reject any graph with an exact b-factor; color checks must not reject any instance with a color-distinct exact b-factor. Include the three abstract examples above, non-bipartite satisfiable graphs, two components sharing colors, zero demand, empty graph, isolated demand, and swapped bipartition sides. Test interrupted graph construction as unknown, and verify state snapshots are unchanged by every evaluation.

Only after proof/source approval should a tiny integrated traversal compare full witness sets and first-witness order with the frozen row-batch reference. It may legitimately visit fewer nodes, so assert equality of leaves rather than equality of traversal counters. Count per-rule prunes and physical edge checks, and measure total tiny runtime including reconstruction; a lower node count alone does not establish a speed improvement. No n79 timing claim is made here.

## Open exploration hypothesis

The concrete hypothesis is that component separation or anti-diagonal color scarcity exposes geometrically dead late prefixes before the existing row-batch DFS reaches an empty selected-row domain. Their frequency and net wall-time benefit are unmeasured and remain open. Keep at least one separately allocated exploration slice and the frozen unmodified search available as a control; do not collapse all exploration into this pruning proposal. The separate near-quarter 158-point approach also remains open. Failure or low benefit of these tests would reject an optimization hypothesis, not establish nonexistence in either family or on the unrestricted grid.
