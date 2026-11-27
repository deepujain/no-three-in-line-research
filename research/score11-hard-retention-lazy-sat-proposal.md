# Design only: hard-retention lazy SAT around the fixed score11 source

Implementation model for this design: gpt-6.1-sol, high. No new SAT source,
formula construction, native solve, source-candidate geometry or host trial
was executed. All frozen SAT, paired, connected-path and packed sources remain
unchanged. This proposal requests mathematical scope/count review first; it
does not authorize implementation or an actual run.

## Exact local scope

Let S be the pinned158-point score11 source at
`data/trades-n79-seed270079-state.json`, byte SHA256
`9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26`,
normalized SHA256
`f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d`.
It is invalid, with eleven independently audited triples; valid incumbent156
is retained separately.

Use one real Boolean X_p for each of6241 board cells, the reviewed exact axis
encoding for target T in {157,158}, and the hard cardinality constraint

    sum(p in S, not X_p) <= D,  D in {6,8}.

This is equivalent to retaining at least152 or150 original source points.
It constrains the solved formula, rather than only choosing initial phases.
For an actual model let d=|S minus A| be its effective original deletions.
Then |A minus S|=d-1 for target157 and d for158. Readded original cells count
as retained, so no raw patch-size interpretation is imposed.

|Target|D|Minimum retained source|Maximum new cells|Scope relation|
|---:|---:|---:|---:|---|
|157|6|152|5|Subset of target157,D8|
|158|6|152|6|Subset of target158,D8|
|157|8|150|7|Includes every target157 repair through8 effective deletions|
|158|8|150|8|Includes every target158 repair through8 effective deletions|

Freshly regenerate exactly the eleven negative three-real-cell clauses from
the dual-validated source conflicts. No old cut file is loaded. These clauses
are necessary for every valid final
configuration. No symmetry, connected-patch, fixed cover, fixed deficient axis,
matching-decomposition or incident-row-pool restriction is added.

The157 axis encoding uses independent deficient row and column indicators.
Their intersection may already be occupied. All real IDs, deficit IDs and
every counter auxiliary must share the returned axis-encoding IDPool.
The retention at-most counter is over the158 negative real source literals.
No auxiliary variable is decoded as a point or used in a geometry clause.

## Prior work and redundant scope

Inspected current `src/lazy_sat.py`, SHA256
`b71eb696b1a181886f745ec27d9d6e7ad2a47e5d22380c1ecdef7038ed0e5db2`,
`research/sat.md`, `research/sat-157-review.md`,
`research/symmetry-sat.md`, `research/memory-stop.md`, current SAT tests,
the accepted cap-five combined review and recent connected-path proposals.
No saved old geometry-cut file was opened or loaded for this proposal.

The unrestricted157/158 attempts impose no hard retention inequality.
Symmetry variants restrict diagonal or half-turn families. Neither route
contains a source-local exclusion result. Prior unrestricted timeout with
millions of geometry cuts supplies no scoped infeasibility evidence. The
aggregate-memory stop recorded a157 worker with1500000 loaded and7657533 new
cuts at its last progress sample, and no final result. The largest inspected
old checkpoint was150863045 bytes; loading it adds all accepted clauses to a
native solver even if the new-cut cap is small. None is reused here.

The accepted through-five repair negative overlaps every proposed scope.
For minimal new-model proof dependencies, the first version would still
include those already closed models; no cap-five-dependent lower bound on d
is proposed. Any benefit or waste must be measured, never counted as disjoint
coverage. A later explicit lower bound d>=6 would require separate evidence
linkage and review before being used.

Paired three-rotations inspect only one fixed decomposition and selected row
rotations, not all repairs of effective deletion6. Their157 outputs can have
effective deletion7 after a final drop. The six path8 completions and the
32 length10/12/16 capacity cases cover only exact connected windows containing
one three-edge cover. Their negatives do not cover arbitrary disconnected or
other connected source-local repairs. This SAT model includes those cases and
many others. Overlap is explicit; no candidate-count speed comparison follows.

D6 is nested in D8 for each target, so a four-job batch would repeat scope.
Furthermore, any valid158-point A in one retention scope contains a new cell:
otherwise A=S, which is invalid. Dropping one new cell produces a valid157
set in the same retention scope. Thus existence at158 implies existence at157
for the same D; an accepted157 UNSAT conclusion would cover158 in that D,
subject to the same solver/encoding/proof limitations. These implications
favor one initial157,D6 gate. A verified witness stops work for independent
validation; any158 or D8 follow-up needs a separate concrete decision. Timeout
at D6 does not justify treating D8 as a disjoint unexplored family.

## Bounded construction and memory proposal

Reuse the frozen `axis_encoding` function and exact validators through a new
standalone source only after approval. The existing `search(extra_clauses=...)`
API admits real literals only, so it cannot carry fresh retention auxiliaries.
Do not relax that interface or modify the frozen runner. The new loop would
create the axis formula, append one CardEnc.atmost sequential retention
counter using the same pool, append11 original triple clauses, then bootstrap
one Glucose3 instance. No generic dispatcher, scheduler, checkpoint loader,
resume protocol or broad SAT retry is needed.

Current retained evidence for n79,target158 records54905 variables and97328
axis clauses. The same encoding arithmetic for target157 gives55851 variables
and99060 clauses (including158 deficit indicators and two exactly-one families).
These157 counts are proposed arithmetic to verify independently before source;
no n79 formula was built to measure them. The conservative158-input at-most-D
counter bounds are158D auxiliaries and3*158D+158 clauses. Using D8 for the
largest-case estimate gives1264 auxiliary variables and3950 clauses. Thus
the larger157 formula has at most57115 variables and103021 initial clauses
including the11 source triples. A fresh20000-new-geometry-cut limit excludes
those11 initial clauses, so at most20011 geometry clauses exist. This yields
at most123021 total explicit clauses and369215 literal entries, allowing the
two length79 deficit-family clauses in the axis literal count. Actual
construction counts must be emitted and checked before native bootstrap;
reject above60000 variables,110000 initial clauses or400000 initial literal
entries. These are design ceilings, not measured RSS guarantees.

Keep no growing candidate history. The old full verifier materializes all
triples and conflict dictionaries of each invalid candidate, so it should not
be the lazy separator. Instead, stream unique triples by their smallest
point index using the frozen exact normalized-direction primitive. One
anchor stores at most157 later points. Emit a negative clause only for an
actual three-distinct-real-cell collinear triple and check its determinant
before adding it. Stop a candidate's scan after at most256 added cuts and
solve again, or after the remaining global20000-cut budget is exhausted.
An interrupted or batch-limited scan is never a geometry-valid candidate.
Only complete triple-stream exhaustion with no conflict triggers both full
validators and immediate atomic witness saving. This avoids retaining a
potentially large invalid candidate conflict list; no implementation is
included here.

Persist bounded progress even without a valid witness: atomically replace one
last-candidate artifact containing target, retained/new counts, normalized
point-set hash, model number and whether its geometry scan exhausted. A
batch-limited or interrupted scan records only a conflict-count lower bound;
256 emitted cuts never imply an exact score of256. A complete stream scan
gives the exact conflict count without retaining its whole triple list. If
this exact count is positive and below the source's11, consider it a best
invalid candidate. Its separately bounded saved-best audit runs both full
validators, requires matching exact conflict counts and normalized identities,
checks the hard retention again, then atomically saves it explicitly as an
invalid state. A partial audit supplies no accepted improvement. Those few
low-conflict states materialize at most10 triples per validator; keep only the
best score and last candidate, with no accumulating history. A score improvement
is search progress, not a valid157/158 construction.

The accumulated20000 new triples may be retained as a bounded final evidence
array; no old-cut input or resumption is offered. A formula with roughly123000
short clauses is plausibly much smaller than the earlier multi-million-cut
runs. This does not bound native learned clauses, allocator overhead or peak
RSS. The old half-turn200000-cut trial reported about86.8MB peak process RSS,
but its family and formula differ, so it is context only. A future first
measurement must preserve the existing256MiB sampled guard and stop on any
rejection; no resource-cap increase or repeated identical trial follows.

Start one shared soft deadline at most25 seconds before source validation and
formula construction; use the existing Root-owned30s/256MiB outer guard. Native
bootstrap is indivisible. Start an interrupt timer with the remaining budget,
use the backend's interruptible solve_limited call, then cancel and join the
timer before deleting the solver. Optionally propose a100000 native-conflict
budget for the entire invocation, reporting its exhaustion as incomplete;
its correctness/lifecycle requires source review and it is not an RSS bound.
Any SAT answer received after timer firing or the shared deadline is treated
as unknown. Formula construction,11 initial clauses and saved-best audits all
consume this shared budget; no separate extra audit allocation is implied.

## Required tiny/source review before any allocation

Current tests already exhaust all real-cell assignments on n2/3/4 for both
axis targets, test an occupied deficit intersection, tiny exact witnesses,
cut rejection and live native interruption. They were inspected, not rerun
for this design. They do not test the proposed retention counter or new loop.

Future tiny tests must independently compare retention projection with direct
|S minus A|<=D on all small source assignments, combine both targets with hard
retention, verify distinct auxiliary ranges, and demonstrate that a model
outside retention is rejected even if its geometry is valid. Compare streaming
triples with every determinant triple on small and long-line fixtures, verify
the256/20000 limits and partial-scan semantics, test late timer/cleanup races,
require both final validators, and reject any attempt to load old cuts.
Also test that partial conflict lower bounds never become exact-score records,
and that an invalid saved-best state cannot appear as a valid witness.
Any actual-source measurement follows mathematical approval, separate source
review and a concrete Root allocation. No global SAT actual is approved here.

Reports must identify exact source, target, D, actual retained/new counts,
formula variables/clauses/literals, initial11 and new geometry counts,
candidate scan completion, native answer/interrupt/budget status, elapsed time
and the existing gate receipt. Verified witness, solver-reported scoped UNSAT,
cut_limit, conflict_limit and timeout remain distinct. No independent UNSAT
proof certificate is proposed, so solver-reported UNSAT is conditional and
does not establish global n79 nonexistence.
