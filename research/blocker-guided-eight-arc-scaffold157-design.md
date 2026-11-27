# Blocker-guided eight-arc scaffold for an exact-D17 sixteen-cycle

Status: DESIGN ONLY. No fixed n79 input validation, cell scoring, blocker enumeration, cover selection, domains, matching, scaffold generation or search was performed. The reported eight-patch root failure is supplied by Root and is being audited separately. This design does not alter or repeat the frozen sixteen-cycle implementation. Implementation/review model: gpt-6.1-sol, high.

Recommendation: consider only a bounded scaffold-feasibility gate after independent design and source/tiny review. Do not allocate another157-completion DFS merely to try different old-edge padding. A useful output here must already contain eight jointly safe new cells, verified capacity for every remaining axis, and an explicit single-cycle plan in its complete residual root graph. Existence or yield of such an output is unknown.

## Why one anchored new cell is insufficient

For an empty p outside the original source S, partition the157 points of A by primitive unoriented direction from p. Let the nontrivial buckets be B. A deletion set F makes p safe against A minus F exactly when every bucket retains at most one point:

    |B minus F| <= 1 for every bucket B.

Equivalently F hits every pair contained in every bucket. The unrestricted minimum number of deletions for p alone is L(p)=sum_B(|B|-1). Matching and old-conflict requirements can only increase this minimum. Since A has exactly five collinear triples, no bucket has more than four points: five collinear old points would already yield ten triples. Thus the buckets here need not be disjoint blocker pairs, as in the older valid-source blocker audit; size-three/four buckets must be handled exactly.

Choosing F to admit one p guarantees only one root edge. It does not address a16-row matching obstruction and does not justify another completion allocation. The proposal below plants eight compatible edges and derives F from their supports rather than filling arbitrary old edges.

## Eight arcs determine all sixteen old deletions

For each prospective new cell q_i, select an old row-support cell a_i in A on q_i's row and an old column-support cell b_i in A on q_i's column, so

    q_i = (row(a_i), column(b_i)), with q_i outside S.

Require all sixteen cells a_0,b_0,...,a_7,b_7 to be distinct and to form a matching in the old row/column graph. Set F to exactly these sixteen supports and Q to the eight q_i. There is no old-edge padding step. Each chosen q_i has at most four support choices, because A has degree at most two on either axis. Its two supports are distinct and compatible individually: equality or a shared old row/column would put q_i in A, contradicting q_i outside S.

In the old-edge label representation, q_i is a directed arc a_i->b_i. The eight arcs have disjoint endpoints. A full16-cycle always contains a set of eight such disjoint alternating arcs (choose every second arc around the cycle); therefore this scaffold representation alone loses no16-cycle endpoint. Pool truncation and bounded search below deliberately lose completeness.

Let R=A minus F. To make R union Q valid, impose all of the following exactly:

1. F hits every one of A's five complete old conflict triples. This makes R valid.
2. For each q in Q, F hits every old blocking pair through q, equivalently each direction bucket retains at most one point. This removes all triples with one new point.
3. For every pair q,q' in Q, every old A point on their line lies in F. These are forced deletions and remove all triples with two new points.
4. No three points of Q are collinear.

These four classes exhaust all triples in R union Q. This149-point set is a valid construction scaffold, not an improved lower bound. Q has distinct rows and columns automatically from the matching of all sixteen supports. Each selected row and column has at most its original A load during this prefix.

Since A=S minus one cell, R retains exactly141 source points. Every q is outside S, so the scaffold already has exactly17 source deletions and eight new points; a completed157 endpoint has the same17 deletions and sixteen new points. Direct set/degree checks and both independent validators remain mandatory before any artifact is accepted.

## Exact remaining-axis and cycle reduction

Index components by the sorted q_i. The eight unfilled row labels are b_i and the eight unfilled column labels are a_i. Remaining replacement cells must be

    t_i = (row(b_i), column(a_tau(i))).

Here tau is a permutation of the eight components. The complete old-edge permutation traverses

    a_i -> b_i -> a_tau(i).

Consequently its cycles have twice the lengths of tau's cycles. One16-cycle is equivalent to one8-cycle tau. At a full endpoint, one removal/insertion at every selected old row and column restores A's exact axis counters and both original deficiency locations.

For each completed scaffold, check the four exact triple-class invariants above, then build its complete secant mask and the8 by8 residual domain graph. A residual cell is allowed only if it lies outside S and is safe against all149 scaffold points. Require both:

- A verified maximum-matching/vertex-cover certificate of size eight. This guarantees residual capacity on every unfilled row and column, beyond merely counting eight planted edges.
- An explicit single8-cycle tau using allowed root edges. Enumerate at most7!=5040 orders beginning at component zero, inspecting at most40320 domain edges. This supplies a concrete16-cycle plan whose eight remaining cells are individually safe against R union Q.

The explicit cycle certificate already implies an eight-edge residual matching; retaining the independently checked matching/cover exposes a precise failed capacity gate and reuses reviewed code. Neither certificate establishes joint compatibility among the eight remaining cells: triples with two or three of those cells still belong to a future exact completion. No full157 arrangement is inferred or scored here.

A scaffold passing both gates gives eight actual valid additions and a complete-axis/single-cycle root plan. This is a material construction milestone beyond one admitted anchor or a perfect matching split into short cycles. Only after such an artifact exists should Root consider a separately reviewed eight-addition completion kernel; no automatic continuation is proposed.

## Deterministic, bounded geometric scaffold selection

At future runtime, reuse the same byte/normalized pins and full validators for A, S and the accepted audit as the frozen sixteen-cycle method. No source reconstruction on mismatch is permitted.

Scan the6083 cells outside S one at a time. Compute each exact direction partition against A, discarding cells with L(p)>16. Keep only the first64 cells by (L(p), coordinates), together with their nontrivial bucket and blocker-pair masks. A bounded sorted buffer suffices; no all-grid pair-mask cache, histogram or source-neighborhood census is retained. A p with L(p)<=16 has at most32 pair blockers: for bucket sizes at most four, C(k,2)<=2(k-1). Thus the pool stores at most2048 binary blocker masks and1024 nontrivial bucket masks.

Before pair-table construction, require a verified matching/cover of size at least eight in the pool's own row/column graph. A smaller maximum cannot contain any Q of the required eight distinct rows and columns: stop this restricted-pool gate without widening or reranking the pool. This is a cheap necessary filter, not evidence that eight compatible support arcs exist. For each pool cell enumerate its at most four row/column support choices, sorting records by (L(p),p,a,b). There are at most256 arc records. Precompute for each unordered pair of pool cells (i) the157-bit mask of collinear old points and (ii) the64-bit mask of other collinear pool cells, excluding the two endpoints. These tables enforce the two-new and all-new triple conditions without rescanning A during recursive choices.

Run a depth-eight search over support-arc records. State consists of selected arc IDs, the selected pool-cell mask Q, the old deletion mask F, old row/column masks and a forced-old-deletion mask U accumulated from new-cell pairs. An extension always adds two distinct old supports on unused old axes; all new points remain outside S. Every arc record examined in a state's branch loop consumes one globally shared started-arc-attempt, even if immediately incompatible. The total cap is4096; neither a new first anchor nor a failed root check resets it.

After an extension, reject an all-new triple using the precomputed masks. Let T=F union U. Reject if |T|>16 or T is not a matching, since future F must contain T. For each already selected q, compute its remaining exact per-anchor bound sum_B max(0,|B minus T|-1); reject if |T| plus the maximum of these per-anchor bounds exceeds16. Do not sum these bounds across q, because their required deletions may overlap.

Choose a branching requirement deterministically: first the least forced old point in U minus F; otherwise the first unhit pair blocker, ordered by pool rank then pair; otherwise the first unhit canonical old conflict triple. An arc can satisfy a requirement only by putting at least one point of it into F. If all current requirements are satisfied and fewer than eight arcs are selected, try further geometric support arcs in the same static order. These are new planted cells with their full blockers, never lexicographic padding of old F. At depth eight, reject any unmet requirement.

Do not apply a global increasing-arc restriction to requirement-driven branching: the first required clause need not be hit by the least arc of a valid final scaffold. Repeated orderings are charged to the4096 cap. Only up to four final scaffold keys need storage to prevent duplicate expensive root checks; no unbounded visited-state set is used. Each key contains the sorted eight support-arc IDs, not merely F, because different planted Q sets on the same F have different residual graphs.

Root-test at most four distinct completed scaffolds. For the first scaffold passing both full-capacity and single-cycle gates, directly recheck its set/axis/source-distance invariants and run both full validators on R union Q. Then atomically persist its exact A/S identities, F, Q, forced blockers, dual validation, residual domains and capacity/cycle certificates, and stop immediately. Placing this final dual validation after the capacity tests permits immediate persistence when validator two finishes late; it never labels an untested-capacity149 set root-ready. Any validation disagreement stops as error. If all four root tests fail, the4096 attempts end, or the shared deadline expires first, curtail this design without trying a larger pool, another ordering, additional root checks, a different width or a completion DFS.

## Proposed feasibility gate and arithmetic cost

This is a proposed gate, not an allocation: one25-second monotonic soft interval from process entry, inside one unchanged owned30-second/sampled256-MiB guard, including input validation, preprocessing, all4096 arc attempts, at most four root checks and publication. No157-completion insertions are included. All loops check that one deadline; started/completed counters distinguish interrupted work. Completed dual validation may cross the soft deadline and must still be persisted immediately, while validator two must never begin after it. Input/source pins are reread before final acceptance/report publication.

Conservative bounds, excluding full validators and ordinary bookkeeping, are:

- Whole-grid candidate preprocessing:6083*157=955031 point-direction visits. Pool ordering uses at most64 retained candidates; no all-candidate blockers remain live.
- The pool's necessary eight-row capacity filter has at most64 edges on79 rows/columns: at most79*64=5056 augmentation-edge inspections, with cover construction and checking each at most64 additional scans.
- Pool-pair tables: C(64,2)*157=316512 old-point determinant checks plus at most C(64,2)*64=129024 pool-point checks,445536 total.
- At most4096 examined support arcs. Per attempt at most seven pair-table lookups, sixteen forced-point axis checks and128 bucket-bound checks; respectively28672,65536 and524288 total. Finding the next clause scans at most256 blocker pairs plus five old triples per entered state, at most261*(4096+1)=1069317 clause checks. Membership/row/column bit operations and constant-size branch control are additional bookkeeping.
- Each root has149 points, hence11026 retained pairs and at most11026*79=871054 lattice line-cell visits. Four roots give at most3484216 visits and256 residual-domain decisions. Eight-row augmentation is at most2048 edge inspections across four roots; cover and cover-check scans are each at most256.
- Four explicit root-cycle tests inspect at most4*5040*8=161280 domain edges. This is an exact finite graph test, not a geometry search over complete157-point candidates.

Keep only the64-cell pool, at most256 support records,2016 pair-table entries, depth-eight state and one149-point root's geometric state. All masks are fixed157-,64-,79- or6241-bit integers. These counts are representation/operation limits, not a measured RSS or runtime prediction; the outer guard is still required.

Primary measured outcome is one verified root-ready149 scaffold with eight jointly valid planted additions, residual matching eight, an explicit residual8-cycle and exact D17. Record phase counters, actual pool/arc counts, depth reached, root-check count and each root's capacity/cycle result. Do not turn the preprocessing into a local-barrier histogram exercise. No ready scaffold means this bounded construction failed, not that exact-D17 cycles or broader repairs are impossible.

## Scope relative to closed work and review requirements

The older valid published-seed blocker audit had disjoint blocker pairs and closed translated-source repairs through three original deletions; separate embedding work closed only its stated small-deletion classes. The score11 source S has a separately accepted complete repair closure through five original deletions. This proposal's completed endpoints delete exactly17 points of S, include no source readditions, preserve the direct157 deficiency locations and require a single16-cycle. It lies beyond those <=5 and <=8 neighborhoods and outside the timed9..12 attempt; that timed attempt is not an exclusion. It does not alter any historical closure or claim all larger repairs open/closed uniformly.

Blocker-guided selection itself is established prior work here. The substantive change is joint selection of an eight-edge valid scaffold, whose sixteen distinct matching supports determine all deletions, followed by a certified residual capacity and long-cycle gate. It is not a new theorem claim, a new ordering of arbitrary padding, or evidence that this restricted pool will succeed.

Before any implementation/run: independently check the bucket/clique identity and size-four bound, support distinctness, eight-arc representation and full-cycle reduction, all four triple classes, exact-D17 counts, lower-bound overlap rule, deterministic branching/repetition scope, caps and operation arithmetic. Tiny source review must compare direction partitions to determinants including four-point lines; compare complete small scaffold families and residual completions against exhaustive old-deletion/permutation oracles; verify no bad pruning of alternating scaffold orders; and cover all deadline/cap/rollback/identity/late-persistence paths. Root alone allocates any later source or actual gate. This design performs none of them.
