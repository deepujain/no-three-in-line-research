# Conflict-directed sixteen-cycle rebuild157

Status: DESIGN ONLY. No n79 conflict-cover enumeration, matching, domain construction, geometry scoring, candidate generation or search was performed for this proposal. This document requests independent design review; it does not allocate an implementation or actual run.

## Construction question

Use the exact accepted157-point state A from `data/score11-deficiency-walk-seed279157-v1/best-state.json`, byte SHA `3e8c8e0495f2e2cbf99815c7fbc575ccd808d0e6908091eb6f04e268f42a38f0`, normalized SHA `adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c`. Its accepted audit is `data/score11-deficiency-walk-seed279157-v1-independent-actual-audit.json`, SHA `419039ebf5828b8fef5b22a0eac29f63e4da4ff203a263aae14c30f704b4faec`. A equals the fixed158-point invalid source S minus one point, has five collinear triples, and has degree one at each boundary axis78 and degree two elsewhere. Pin S at `data/trades-n79-seed270079-state.json`, SHA `9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26`. Future execution must revalidate these identities, the exact five coordinate triples and A subset S with |S minus A|=1; it must not reconstruct A when saved bytes disagree.

The construction seeks one long alternating-cycle exchange of16 old cells for16 new cells. All new cells must lie outside S. The old cells form a matching and must hit every one of A's five conflicts. After their deletion the141 retained points are valid. Construct replacements using exact secant propagation and MRV, accepting only geometrically valid partial sets. A full endpoint would therefore be a valid157-point certificate rather than an invalid state selected by an energy score.

## Exact macro move and source distance

Let F={(r_i,c_i):0<=i<16} be16 occupied cells of A with pairwise distinct rows and pairwise distinct columns. Index F by increasing row. Require every original conflict triple to meet F. Set R=A minus F. Seek

    M={(r_i,c_sigma(i)):0<=i<16},

where sigma is one cycle of length16, every cell of M is outside S, and R union M has no collinear triple. Replacing F by M is an alternating cycle of32 bipartite edges. Its16 selected old cells and16 new cells are disjoint, because F subset S and M intersect S is empty. All row and column loads are preserved exactly, including the two original deficient axes. Cardinality remains157.

The distance claim is exact: A subset S, |S minus A|=1, F subset A and |F|=16 give |S intersect R|=141. Adding M outside S leaves |S minus (R union M)|=17 and |(R union M) minus S|=16. Every successful endpoint is therefore outside both the at-most-eight and intrinsic9..12 source-deletion scopes. The same retained-source count141 holds at every replacement prefix. At15 added points, a valid156-point diagnostic has17 source deletions and15 additions.

This move is supported on a direct157-point degree pattern. It does not require decomposing a full158-point state into two permutations or respecting a matching color. It changes16 cells at once; the accepted one-step and three-exit two-step censuses do not cover it. A16-cycle can be factored combinatorially into smaller switches, but those intermediate157-point states need not have acceptable geometry or bounded score. Constructing the large replacement directly avoids imposing those intermediate energy constraints. No novelty or connectivity claim is made for alternating cycles.

## Bounded conflict-directed old-edge selection

At future runtime, obtain A's exact five conflict triples from agreeing full validators. Sort the coordinate triples canonically. Enumerate matching conflict-cover kernels C as follows: select the first unhit triple; branch on its three cells in lexicographic order; reject a cell sharing a row or column with C; stop a branch as soon as all five triples are hit. Each choice hits at least one previously unhit triple, so depth is at most5, the raw tree has at most364 nodes and at most243 leaves. Deduplicate identical kernels. No numerical kernel is selected in this design.

Any matching F that hits all five triples contains some kernel explored by this rule: on each unhit triple, choose a member of F. Thus absence of a matching kernel is a genuine obstruction to this particular matching-deletion construction, not to general ejection chains. A kernel need not itself contain16 cells.

Order the kernels by (cardinality, sorted coordinates). Extend each to16 matching cells by repeatedly taking the lexicographically first cell of A whose row and column are unused. Padding is guaranteed to exist at these sizes: since A has axis degrees at most two, each selected edge blocks at most three A edges including itself. After j<16 selections, at most3j<=45 of157 edges are blocked. This argument concerns combinatorial padding only, not geometric feasibility of replacements.

Deduplicate completed F sets and schedule at most the first8 distinct sets in that order. At most243 kernels are considered and at most243*16*157=610416 simple padding-cell checks are needed. The finite8-set selection is part of the proposed family, not evidence that these are the best patches. No random padding, alternate ordering, automatic width increase or second allocation follows if they fail.

## Geometric reconstruction and one-cycle enforcement

For one scheduled F at a time, retain R=A minus F, verify it is valid, and build its complete secant mask with the reviewed primitive integer line mechanism. Root domains have only the16 freed rows and16 freed columns. A cell is allowed exactly when it lies outside S and outside the secant mask. This also excludes every old selected cell. Run a deterministic maximum matching and verify an equal-size vertex-cover certificate. Size below16 rejects this patch only. A size16 assignment is necessary feasibility evidence; it is neither a geometric completion nor evidence of a single cycle.

Maintain a partial injective map sigma. MRV chooses an unassigned row label with the fewest currently safe unused-column choices; row-label ties and column choices are ascending. For a proposed arc i to j, follow already assigned outgoing arcs from j. If this would close a directed cycle before all16 labels belong to that cycle, reject it. With indegree and outdegree at most one, any premature cycle cannot later be connected to the remaining labels. At full assignment, explicitly verify that sigma has exactly one16-cycle. This pruning preserves every admissible full16-cycle completion for the fixed F.

On a safe insertion p, add secants through p and every retained or earlier inserted point, using exact primitive lattice lines. This maintains validity by induction and handles triples containing one, two or three replacement cells. Keep immutable unsafe/used-column masks and restore path/arc assignments in finally blocks on every return, cap, timeout or validation failure. Only one patch's geometry/DFS stack is live; no cache of all grid-pair masks, visited-state set or recursive patch queue is used.

The general exact score identity for a finite exchange is the telescoping sum of negative incidences during sequential removals and positive incidences during sequential additions. A triple involving several moved points is subtracted once at the first removal and added once at its last insertion, so multiplicity is exact, including lines with four points. For this proposed constructive variant, deleting a conflict cover makes the retained score zero, and every accepted new point has incidence zero. A complete valid exchange has exact score change0-5=-5. There is no Metropolis acceptance or invalid-score continuation in the proposed pilot.

## Proposed single measurable gate

Only after independent design and source/tiny review, propose one25-second monotonic soft interval from process entry inside the existing owned30-second/sampled256-MiB guard. Share a cap of1000 STARTED replacement insertions across at most8 scheduled F sets. Include artifact validation, cover enumeration/padding, root propagation, matching/certificate checks, all DFS work and witness validation in the same deadline. Check time inside primitive line traversal, matching augmentation, kernel generation and padding. An insertion interrupted during propagation still consumes its start. No second gate or automatic unchanged retry is authorized.

Arithmetic bounds for this proposal are:

- R has141 points, hence9870 retained pairs per patch and at most9870*79=779730 root line-cell visits. Eight patches give at most6237840 visits.
- Each root domain has at most256 cells; eight graphs give at most2048 domain decisions and32768 augmenting edge inspections under the reviewed16*256-per-graph bound. Cover construction/checking are separately counted, each at most256 edges per graph.
- Before an insertion at most156 points are selected, so at most156*79=12324 candidate line-cell visits are needed.1000 starts give at most12324000; root plus candidate propagation totals at most18561840 visits, excluding validators and simple bookkeeping.
- Each patch has depth at most16. A stack of6241-bit immutable masks and compact16-label arc metadata is bounded. Keep only the8 old-edge sets and one active patch, not all candidate states. The outer RSS guard remains necessary; these arithmetic ceilings are not runtime or peak-memory measurements.

Record started/completed cover nodes, padding checks, root lines/cells/domains, root matching/certificate work, insertions, cycle-pruned choices, wipeouts, rollbacks and maximum added depth. These diagnose a construction attempt and do not form another local-neighborhood histogram or barrier census.

Primary success is one dual-verified157-point endpoint with an explicit16-cycle and direct source-distance checks, immediately saved atomically. At most the first dual-verified156-point prefix at15 additions may be saved as a diagnostic, with no lower-bound improvement claim; continue within the original remaining budget. A first validator must begin before the deadline and the second must not begin after it. Once both agree, persist immediately even if validator two crosses the soft limit; a witness stops the entire pilot. Original inputs, implementation and source hashes are reread before final report publication.

Without a verified156/157 arrangement, stop this pilot without unchanged repetition. A complete matching obstruction or exhaustive replacement search concerns only its specified F. Completing all8 patches excludes only these selected16-cycle families; it does not close all possible conflict-cover extensions, all ejection chains, longer cycles or the global problem. Capped or timed-out prefixes exclude nothing. A156 diagnostic is an arrangement for a separately reviewed question and gives no automatic continuation permission.

## Review and tiny-test gate

Independent review must confirm the conflict-cover tree bound/completeness claim, padding existence, exact degree/source-distance algebra, alternating-cycle representation, premature-cycle pruning, and the distinction between this selected finite family and unrestricted long moves. Feasibility of any actual replacement graph is unknown; no likelihood claim supports allocation.

Before implementation is eligible for one run, tiny tests must compare kernel generation with exhaustive matching conflict covers, including impossible compatible covers; compare deterministic padding and dedup/order; compare primitive secant domains with determinants; and compare all constructed single-cycle completions with brute-force permutations filtered to one cycle. Include a root perfect matching that consists only of prohibited short cycles, empty domains, all premature-cycle lengths, source readdition, source overlap/distance identities, exact telescoping deltas with several moved points, and every rollback path. Exercise shared1000-start counting across synthetic patches, cap/timeouts inside cover/padding/propagation/matching, first156 diagnostic only, late full-witness persistence, pin changes and clean owned-resource receipt handling. These tests remain tiny and make no n79 selection or score evaluation.

## Existing evidence used as context

The accepted initial census `edec993b9493b73d90b879f682fb6624176c75d8796d18f2cce94ea5800f1350` establishes why neutral/descending one-step movement from A cannot help; it is not imported as a pruning rule here. The three-exit design/actual family concerns only two moves and remains source-local. The source-disjoint whole-matching pilot was capped and produced no156/157 artifact; its unchanged search and alternate anchors remain curtailed. This proposal changes the selected state, conflict-directed deletion mechanism, replacement dimension, one-cycle constraint and guaranteed source distance; it does not resume that pilot. The primitive-line/rollback and dual-validation components may later be reused from reviewed frozen code without mutating it.
