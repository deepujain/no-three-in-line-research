# Restricted exact three-row descent: bounded design

Status: DESIGN ONLY. No production implementation, source-point selection, actual input/geometry, neighborhood computation, fallback run or cap change is performed. Existing workers, inputs, manifests, reports and receipts remain frozen. Root reports the single suffix completed cleanly in7.499464625 seconds/56448KiB with all166 pins unchanged:64 new pairs completed, no accepted moves, U65 unchanged, cumulative96 pairs and308 rows,130 authority publications, no pending optimizer and `pair_cap`. Independent suffix actual acceptance is pending at design time. These are reported observations, not geometry independently inspected here. Root curtails unchanged pair-prefix expansion; this proposal does not reopen it.

Recommendation: obtain independent mathematical and engineering/resource DESIGN review of one new restricted three-row worker, before any SOURCE/TINY authorization. If that stage is later accepted, the sole proposed first actual allocation remains25soft/23search/30owned/256MiB and16 TOTAL started three-row block optimizations. There is no row/pair followup stage, no fourth-row move, domain widening, random restart, neutral/uphill step, automatic continuation or allocated fallback.

## Active input and scope

Reuse the original independently audited immutable65 coordinate handoff, rather than resume the suffix cursor. Its coordinate-free metadata is `data/two-row-suffix75-input-identities.json`, SHA `f966e46cdd62fc22f48e0415a8b851b6f5dc021bd19b798ca3c2e6526cca910e`, normalized current identity `25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c`, n75,149 distinct cells, exactly one singleton row and74 full rows, exact raw U65. Future actual loading must authenticate the complete metadata/source/report/checkpoint/accepted receipt/independent29-state audit and guard/helper chain before coordinates enter geometry, then freshly dual-validate65 and build the current complete index inside its own allocation. A reviewed reuse of the fixed65 authentication helper is preferable to a new unreviewed chain parser; never invoke old optimizer/controller/resume entry points.

The latest suffix may be pinned as curtailment provenance once its independent actual acceptance is available. Its unchanged normalized state/no accepted moves are not a new coordinate source or a requirement to import pair-cursor machinery. Old row/pair counters and source-supported failed prefixes remain historical provenance. They are not independent pair-local-minimum certificates and are not active allowances for this new method. The new active counter is `blocks_started=0` with a fixed ceiling16 across the whole proposed allocation. Preserve prior accepted ordinal28 as provenance; new accepted block count is separate and at most16.

The tested three-row family is structurally different from a single two-row replacement: it permits simultaneous coordinate changes in three rows, and its exact objective has a nonzero all-three-new interaction. Actual U65 is not established to be pair-stuck:only96 pairs were reported tested. No genuine positive full two-row-local-minimum fixture exists in the independently exhausted row-valid n2..4 states. This proposal claims neither such a fixture nor evidence that a third row is necessary for the actual65 state.

## Deterministic block selection

At each committed current state P, use its complete integer pair-line index and raw U≤65. Hard row loads exclude horizontal violations, so a violated line contains at most one point per row. For every violated line with row set L and t points, accumulate:

- I_r += C(t−1,2) for each r in L;
- J_rs += t−2 for each distinct row pair in L;
- K_rst +=1 for each distinct ordered row triple r<s<t in L.

K_rst counts old conflict triples meeting all three rows. It may exceed one when different point triples on different lines have the same row labels. Its sum over row triples equals U. Construct candidate blocks only from keys with K_rst>0; at most65 distinct keys exist. Do not enumerate all C(75,3)=67525 row triples. For each candidate compute the exact number of old triples removed by deleting those rows:

    M_rst = I_r+I_s+I_t−J_rs−J_rt−J_st+K_rst.

This is a triple-incidence union by inclusion/exclusion. Order candidate blocks by `(-M_rst,r,s,t)`. K controls eligibility, not a further tie-break. Candidate domains below are computed only when that block actually starts. A block with K=0 is outside this chosen family even if it could improve; do not portray its omission as mathematical impossibility. M orders removed incidence, not achievable minimum.

Keep one current-state candidate list/hash and completed-prefix cursor. Its identity binds the normalized current point set, ranking policy and exact `(r,s,t,M,K)` records. Start at cursor0 on the initial65 state. Nonimprovement advances one completed cursor on the same state. A strict acceptance atomically installs the new state, resets cursor/coverage and discards old ranking/domain identities, then selects from a freshly computed current candidate list at cursor0. Previously tested row labels on another state are different neighborhoods. The global16-start count never resets. Do not perform optional list construction after zero or when the16th start has already consumed the allowance.

## Four-column domains and legal loads

For a selected block r<s<t remove all its five or six points and retain R, with |R|144 or143. From the complete current pair-line index, mask out all three rows and compute retained U_R and insertion unary vectors u_r,u_s,u_t on all75 columns. A retained line of occupancy k contributes C(k,3) to U_R and C(k,2) at each exact in-grid intersection with a selected row. Horizontal lines contribute no unary insertion. Use signed integer divisibility, not floating point; no new retained-line census is needed.

For each selected row i, its domain D_i begins with every current column in that row, even when its unary cost is high. Add the least `(u_i[x],x)` missing columns until D_i has exactly4 distinct columns, then sort D_i. A singleton row thus adds3 missing columns; a full row adds2. The finite tiny analogue uses `min(4,n)` columns. A fixed-size streaming minimum selection suffices; do not retain all candidate outcomes. The domain is determined once for this exact state/block/retained set and is fixed throughout that block optimization.

The unchanged current assignment is eligible. If the selected rows are all full, their total6 forces loads2/2/2. If the selected rows contain the singleton, their total5 allows ALL three orientations1/2/2,2/1/2,2/2/1, regardless of where the deficiency began. A selected row never receives zero or three points. A changed deficiency stays inside the selected block, preserving the global one-singleton pattern. Equal columns across rows are legal.

These are restricted four-column neighborhoods. No claim of a full-grid three-row optimum or a full three-row local minimum is valid, even if every induced candidate is completed. Domain bias can miss useful high-unary choices whose mixed interactions are favorable; the exact restricted calculation does not remove that limitation.

## Exact objective with the mandatory ternary term

For selected sets X⊆D_r,Y⊆D_s,Z⊆D_t of the legal loads, define C_ij[a,b] as the number of retained q∈R collinear with new points(a,i),(b,j), for each of the three selected row pairs. Define

    T[a,b,c] = 1 if (a,r),(b,s),(c,t) are collinear, else0.

The exact completed raw score is

    U_R + Σ(x∈X)u_r[x] + Σ(y∈Y)u_s[y] + Σ(z∈Z)u_t[z]
        + Σ(x∈X,y∈Y)C_rs[x,y]
        + Σ(x∈X,z∈Z)C_rt[x,z]
        + Σ(y∈Y,z∈Z)C_st[y,z]
        + Σ(x∈X,y∈Y,z∈Z)T[x,y,z].

The terms count triples with zero, one, two and three new points. A triple with two new points on the same row and an off-row third point is impossible. Three distinct new rows can form a line, so omitting T is unsound. Compute each C entry by exact determinant against every retained point and count all such points; use three at-most4×4 byte tables. T is an at-most4×4×4 byte/boolean table computed by direct determinant. Cross-table diagonal entries remain legal; T[a,a,a]=1 is essential for vertical three-new triples. For a line containing k retained points and one new point in each selected row, the contributions C(k,3)+3C(k,2)+3k+1=C(k+3,3) illustrate why every term and multiplicity is needed.

A static n3 ternary falsifier for future independent tests is the completed five-point set `{(0,0),(0,1),(1,1),(0,2),(1,2)}` after all three rows are emptied/reinserted. R is empty, so base/unary/pair-retained terms vanish. The three new column0 points form one vertical triple, and the ternary sum is1. An implementation omitting T would falsely score0. This is a proposed tiny algebraic test, not an actual-source run or a claim of pair-stuck behavior.

Enumerate all legal `(X,Y,Z)` in global tuple-lexical order and retain the minimum `(score,X,Y,Z)`. For total6 use sorted size-two combinations in each domain. For total5 use the merged lexical union of singleton and pair X; for each X use the merged lexical union of singleton/pair Y filtered to leave `1≤5−|X|−|Y|≤2`; enumerate Z of that remaining size in ordinary lexical order. This interleaves all three orientations rather than scanning them as separate batches. It contains216 total6 assignments or432 total5 assignments at four columns/domain. Nonnegativity and this order permit an immediate first fully scored zero with the specified global tie. Record `optimum_established` separately from `enumeration_exhausted` when zero exits early.

Before streaming replacements, check the formula on the current assignment equals current U; a mismatch stops with error. At completion, a nonimproving optimum must equal current U because current was eligible. No strictly positive partial minimum commits or advances coverage. A positive strict optimum reconstructs the full proposed point set, verifies row/cardinality/change support and rebuilds its complete index/raw score before any acceptance.

## Controller, started charges and durable boundaries

The complete proposed controller is three-row-only: authenticate65; build the current index and induced ordered candidates; start the next candidate; solve its exact restricted neighborhood; commit the first strict optimum and reset the current-state candidate list; otherwise advance the failed prefix. There is no intervening exact single-row sweep, pair suffix, penalty, RNG, neutral motion or widening. If all current induced candidates complete without improvement, stop `restricted_candidate_list_exhausted`. If16 total starts are used first, stop `block_cap`. A deadline/interruption, source/table/invariant error or uncertain publication stops immediately without another block.

Charge each started block durably before retained-line/unary/domain/cross/T/assignment work begins. Selection-list construction is separately charged time and has a finite bound; interruption there claims no block start or covered optimization. A pending start identifies state/order/cursor and selected rows; domain/result metadata are added at completion without a third publication. An interrupted block stays charged and uncovered. No general checkpoint-resume CLI or automatic retry is proposed.

Use a new authority schema with current points/U/state hash, current candidate identity/cursor, global block starts/completions and accepted count, pending attempt, at most16 bounded attempt records and at most16 immutable accepted artifacts. Old row/pair history is read-only provenance, not active cursor fields. The durable start and exact completion require at most2 authority publications per block, plus initialization and final stop:34 total, each≤1MiB. Cap attempt records at2KiB, candidate list at8KiB, move/witness files at16KiB and fixed provenance/header at64KiB; retain only current/pending geometry, one selected block's225 unary integers,48 cross bytes,64 ternary bytes,12 domain columns and streaming best candidate. No432-outcome cache or trajectory indexes are needed.

Reuse the already reviewed file/directory-fsync, artifact-before-reference, single-authoritative-state and orphan semantics; do not replace them with separately persisted point/cursor files. A positive move artifact is immutable and durable first. One atomic authority replacement then installs points, score, global counts and reset candidate cursor/flags together; only afterward adopt it in memory or start further work. A failure before replacement keeps the old charged-pending authority and perhaps an orphan. Uncertain durability fails the receipt and stops writes; no orphan is promoted. Direct tests must cover the last suffix fixes rather than duplicating their bugs.

A fully scored zero bypasses optional candidate metadata/hash/event, next-list/index and ledger/report work. Validate structure, start validator one timely, start validator two only after a timely check, and save immediately after successful validator two even late. Mark the durable witness reference immediately using its already checked identity. A later metadata or zero-authority publication failure preserves the witness and fails overall acceptance. Incomplete validation may save a raw fallback afterward and leaves the old positive authority plus charged pending attempt. Final source/runtime/pin/deadline/report failures likewise clear acceptance without deleting witness files.

## Finite cost and proposed reservation

For each of at most16 blocks:

- At most11026 complete-index retained-line visits and3×11026 exact row-intersection attempts compute base/unaries.
- Three4×4 cross tables with at most144 retained points need at most6912 determinant tests.
- The4³ ternary table needs64 determinant tests.
- At most432 complete assignments are scored. At most6 unary,12 pair-cross and8 ternary entries occur in any score, giving a conservative26 table terms/assignment, plus base. Current-assignment checking adds one such score.
- Each domain scans75 columns and selects at most3 missing minima with fixed-size storage.

Across16 starts these give176416 retained-line visits,529248 row-intersection attempts,110592 retained-point cross determinant tests,1024 ternary determinant tests,6912 full candidate assignments and at most179712 assignment table terms, plus at most416 current-assignment terms. No n75 geometry was computed to obtain these arithmetic ceilings.

Priority selection scans one complete index per needed committed state. With U≤65, each violating line has at most8 points (C(9,3)>65), total triple-row enumeration is U≤65, total violated-line row incidences≤3U≤195, and row-pair updates≤3U≤195. At most65 candidate K keys are ranked, and at most65 M values use fixed sparse I/J/K lookups. Conservatively allow17 current-state selection censuses, at most187442 line visits,1105 induced-triple enumerations and3315 pair updates, plus sorting lists of at most65 entries. A straightforward literal conflict-union cross-check may be used in independent tiny review, not silently added as actual replay.

There are at most17 complete index-build attempts:one initial and at most one candidate rebuild per started block, including any interrupted pending rebuild. No separately cached retained index or extra geometry rebuild is necessary. Accepted block count is at most16, so a complete run has at most17 active point states, not65 row-followup stages. Full input hashes, dual validators, bounded JSON/artifact work and at most34 atomic publications are additional charged costs.

A separately reviewed25soft/23search/30owned/256MiB first gate is proposed only after SOURCE/TINY and owned artificial memory/persistence evidence. The earlier suffix's7.50 seconds for64 pairs does not forecast this algorithm. The new assignment family is small, but input authentication, priority construction, table setup, Python overhead, validation and filesystem latency still count. Keep the2-second shutdown reserve, never spend leftover time beyond16 starts, and fail acceptance if main/owned limits or pins fail. Sampled RSS is an observation rather than a proved process maximum.

## Evidence, curtailment and review obligations

If all16 starts complete with zero accepts, or the current induced candidate list exhausts earlier with zero accepts, curtail this unchanged four-column/induced-triple family. Do not authorize a second16-block chunk, four-to-five-column widening, alternate seed or untested row-triple selection on leftover time. A positive strict reduction is evidence only for that saved restricted block/current state; even several reductions do not justify an automatic next allocation. Stop at zero and independently audit any saved witness. A capped scan is incomplete; a completed chosen restricted list is not a full-grid three-row exclusion, full pair-local minimum or global impossibility statement.

Independent SOURCE/TINY review must compare base/unaries/all three C tables/T, every restricted assignment and global ties against direct determinant enumeration on finite row-valid n2..4 fixtures. Verify sparse I/J/K and removed union against literal triples, K multiplicity across different lines, candidate eligibility/order, current inclusion despite high unary cost, all total5 orientations/deficiency changes, vertical T and multiple retained points, lexical first zero, no positive partial selection, started cap across multiple accepts, stale-list invalidation and old-state event coverage. Test zero before optional work, before/after replacement failures, pending charges, metadata errors, source drift and the34-write/component caps. Kernel/loader reuse requires exact source pins and review of the new call boundaries.

The independently exhausted n≤4 state family contains no genuine positive full pair-local minimum, so it cannot demonstrate a pair-stuck-to-three-row escape. State that limitation prominently. Real tiny three-row scores/transitions can verify the reduction and legal three-row support; an example changing all three rows distinguishes one three-row move from one two-row move without proving two-row necessity. Any positive completed terminal or selection-route stub must be labeled control-only. An independently found larger-order falsifier would require its own bounded SOURCE/TINY design/allocation before computation; do not launch one automatically to fill the missing fixture.

The current request ends at this design and independent reviews. No implementation, actual source-point selection, active loader call, geometry run or fallback allocation is authorized by the memo.
