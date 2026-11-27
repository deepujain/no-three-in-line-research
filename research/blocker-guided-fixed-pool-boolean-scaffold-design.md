# Exact Boolean projection of the audited fixed scaffold pool

Status: DESIGN ONLY; no solver, CNF generation, new n79 scoring, search, domain construction or allocation. Root requested a new formulation after accepting the capped DFS audit. This document uses the already audited64-cell/246-support-arc pool, its saved L histogram and its frozen preprocessing identities. It does not reopen the stopped DFS. Independent engineer and adversarial design reviews are required before implementation; source/tiny review and a separate Root allocation remain necessary afterward.

## Decision and distinctness

Recommend the formulation for independent design review. Its logical and encoding bounds fit a compact feasibility gate; actual solver behavior and resource compliance remain unknown. It replaces ordered support insertion with one Boolean assignment per unordered set of eight support arcs. Fully equivalent auxiliary variables have a unique extension for each selection. Thus the formulation removes factorial traversal-order copies rather than renaming an attempt cap. It can express the entire fixed-pool scaffold family, although an interrupted solver does not decide that family.

The question is exactly: does the audited pool contain eight planted points whose16 old matching supports can be deleted to leave a valid149-point scaffold? It does not ask whether the eight residual additions are jointly valid, whether another pool works, or whether a157 witness exists. A single returned scaffold may undergo the same residual matching/single-cycle readiness gate. Failure there does not imply every scaffold in this pool fails that gate.

## Immutable inputs and reuse boundary

Use the original A=S minus(78,78), complete five old conflicts, audited pool order and original support ordering. Never change the64-cell pool, scores, tie-breaking,246 support choices or source set.

- Original source `research/blocker_guided_eight_arc_scaffold157.py`: `5af488fa4f857cb91325677eff67034bb2fcf6f7ed30a32e97ec018808e11b39`.
- Completed report `data/blocker-guided-eight-arc-scaffold157-v1/report.json`: `b98c5d0b4b228d3bba4f625bd1f5e40891db178cd63296f2bb0cffefedb8aea9`.
- Accepted audit `data/blocker-guided-eight-arc-scaffold157-v1-independent-actual-audit.json`: `828ae6c503a4fe37d8d84b39b9cddf531e747cad7fbf1adc340fdbd108b7564c`.
- Audit helper `research/blocker_guided_eight_arc_scaffold_independent_actual_audit.py`: `c2e712976923f4b04e3a292682b2a848e404d7cca2ef1f34d8a86bda6105a3e3`.
- Canonical support descriptors `(L,q,a,b)`, in original order: `78f575d75e81f2de64bb95fbf411540a0fc57bb1ac8d17d469cefbc549a06d88`.
- Canonical pair tables `[i,j,hex(old_mask),hex(other_pool_mask)]`, in increasing pair order: `d901f6448c3910cfd3ebc32c16288871fa224223b87ef1e339bf299addc2d104`.

The actual run did not save bucket/support/table bytes. A future allocated worker must take the64 coordinates and L values directly from the pinned accepted report, reconstruct only those64 bucket partitions, their246 supports and their2016 pair tables once using pinned pure helpers, and require the two canonical hashes above. Recomputed L values must match the saved64 entries. The accepted audit supplies the ranking proof: do not rescan the6083 outside cells, rerank the64 entries, replay the4096-record DFS, rebuild an alternative pool, reuse an old search checkpoint or infer saved table bytes from a hash. The already saved pool matching/cover certificate can be checked directly without a new matching search. A mismatch stops as error. The fixed A/S bytes, normalized identities, old conflicts and degree profile receive their existing validation and pin checks.

The saved pool's L histogram is two cells at2,24 at3 and38 at4. The pool has a certified maximum matching24; this is only a necessary capacity fact. The current design reads that saved metadata and evaluates arithmetic bounds only; no fixed preprocessing is reconstructed here.

## Variables and exact constraints

Assign variables in deterministic order:246 support-selection variables x_e;64 planted-point variables q_i;157 old-deletion variables d_v. These are467 semantic variables.

For a support arc e=(a,b) at point p=(row(a),column(b)), encode both directions of each union identity:

1. q_i iff the OR of x_e over all support arcs for pool cell i. Emit each `not x_e or q_i`, and one `not q_i or x_e1 or ...` per pool cell. An empty support list emits `not q_i`.
2. d_v iff the OR of x_e over arcs having v as either endpoint. Emit `not x_e or d_a` and `not x_e or d_b` for each arc, and one reverse OR clause per old point. An unused old point emits `not d_v`.

These reverse implications are essential: arbitrary d_v values must not serve as free deletions, and arbitrary q_i values must not plant cells without supports.

Require exactly eight x_e to be true. For every unordered pair of distinct support arcs whose two endpoint-row sets intersect or whose two endpoint-column sets intersect, emit `not x_e or not x_f`. This covers shared old points, distinct old points sharing an axis, and two support choices for the same planted point. Checking only endpoint identity would be insufficient. Every individual arc already has two distinct matching old endpoints, as certified by the fixed preprocessing.

Encode all four geometric triple classes:

- For each of the five complete old conflict triples(a,b,c), emit `d_a or d_b or d_c`.
- For every pool point i and every old blocking pair(a,b) in its complete bucket cliques, emit `not q_i or d_a or d_b`.
- For each distinct pool pair i<j and every old point a on their line, emit `not q_i or not q_j or d_a`.
- For each collinear triple of distinct pool points i<j<k, emit `not q_i or not q_j or not q_k`. Generate each once using the fixed pair table's other-pool mask and k>j.

No residual domain, matching, cycle variable or completion constraint belongs to this projection. No increasing support-index constraint is imposed on the selected set beyond canonical enumeration of clauses; this is not the invalid increasing-arc restriction in requirement-driven DFS.

## Cardinality encoding with a unique extension

Use a fully equivalent threshold counter, rather than a one-way encoding with unconstrained auxiliary completions. For i=1..246 and j=1..min(i,9), let z(i,j) mean at least j of x_1..x_i are true. Constants are z(i,0)=true and z(i,j)=false for j>i, including i=0. Define

    z(i,j) iff z(i-1,j) OR (x_i AND z(i-1,j-1)).

Writing a=z(i-1,j), b=z(i-1,j-1), z=z(i,j), the four clauses are:

    (not a or z)
    (not x_i or not b or z)
    (not z or a or x_i)
    (not z or a or b)

Simplify constants, omit tautologies and remove repeated literals deterministically. Assert z(246,8) and not z(246,9). Induction on i proves the threshold meaning, exact-eight condition and unique auxiliary assignment. There are sum_i min(i,9)=2178 counter variables and at most4*2178+2=8714 clauses, with at most11*2178+2=23960 literal occurrences before simplification.

## Soundness, completeness and result scope

Exactly eight compatible selected arcs have16 distinct old endpoints forming a matching. Two selected arcs cannot share a pool point because they would share its row. Thus the equivalences give exactly eight q values and16 d values, with F precisely the selected supports and Q precisely the planted cells. All Q lie outside S. Each of the four triple classes is excluded by its corresponding clause, so P=(A minus F) union Q has149 valid points,141 retained source points,17 source deletions and eight new points. The original scaffold axis identities follow from the supports.

Conversely, any valid eight-arc scaffold from this exact pool satisfies every clause under its x selection, induced q/d assignments and threshold values. Thus the formula is equisatisfiable with the full fixed-pool scaffold family. The selected old matching also makes each q's row and column supports unique within F, so identical F/Q data do not create extra assignment copies through alternate support attribution. Different planted Q on the same F remain different solutions.

A decoded SAT result is accepted only after independent reconstruction of F/Q, all set/axis/source invariants, exact geometry and both existing full validators. Immediately atomically save the valid149 diagnostic after validator two, before any root work or further deadline check. Then perform a fresh deadline check: if validator two crossed the soft deadline, preserve the diagnostic and do not begin the optional root. Otherwise run one complete residual secant graph, maximum-matching/cover check and explicit single8-cycle test on that one scaffold if the shared deadline permits. A candidate passing these gates may receive a separate root-ready149 artifact. If either gate fails, preserve its exact obstruction and valid149 diagnostic but do not request a second SAT model, add a blocking clause, restart or claim a pool-wide readiness obstruction. Neither label improves156 or asserts a157 witness.

An UNSAT claim closes this precise scaffold family only after independent validation of a proof for the exact emitted CNF. It says nothing about other pools or all exact-D17 cycles. Raw solver UNSAT without a completed checked proof is an unverified solver result, with `closure=false`. Timeout, memory/file cap, malformed model, incomplete proof or failed proof verification yields no closure. A geometry-validator disagreement is an error, not a lazy-cut opportunity.

## Encoding bounds and construction cost

The following are conservative integer upper bounds, not claims about actual uncomputed CNF counts. They use only audited pool sizes, the saved L histogram and the existing degree/five-conflict premise.

| Constraint group | Maximum clauses | Reason |
|---|---:|---|
| Exact-eight threshold counter | 8714 | 2178 fully equivalent thresholds plus two units |
| Support-axis incompatibility | 30135 | At most C(246,2) pairs |
| q equivalences | 310 | 246 forward plus64 reverse clauses |
| d equivalences | 649 | 492 forward plus157 reverse clauses |
| Old conflict hits | 5 | Complete fixed five triples |
| One-new blockers | 416 | 2*3+24*6+38*7 |
| Two-new/old blockers | 8064 | At most four old collinear points per C(64,2) pair |
| All-new triples | 41664 | At most C(64,3), emitted only when collinear |
| Total | 89957 | Sum before simplification |

For the one-new bound, bucket size is at most four. At deletion lower bound L, each bucket of size s consumes s-1 units and supplies C(s,2) pairs. For L=2,3,4 the maximum pair counts are3,6,7 respectively. This gives416, tighter than the generic2*sum(L)=456. The old-point count on any new-pair line is at most four because five old collinear points would create ten old triples, contradicting the exact-five input.

Total variables are467+2178=2645. Summing clause widths yields at most237112 literal occurrences:23960 counter,60270 incompatibility,802 q identities,1633 d identities,15 old hits,1248 one-new,24192 two-new/old and124992 all-new. A deterministic DIMACS file with one space after each signed integer and `0\n` per clause is therefore at most6*237112+2*89957+17=1602603 bytes, including the longest header `p cnf 2645 89957\n`. This is less than1.53MiB. The semantic union clauses are bounded in aggregate even though a single old-deletion reverse clause may be longer than three literals.

Use eager clauses; this formula is small enough that streaming/lazy geometric cuts add avoidable correctness and proof-state complexity. Stream the body to disk while counting clauses, then write the final header and copy the body once; remove the temporary body after completion. Simultaneous body/final-CNF storage is below3.21MB. Keep only the frozen pool/buckets/supports/pair tables, variable maps, one clause and a small copy buffer in parent memory. Avoid a Python object per emitted clause. Binary literal storage alone would take948448 bytes, but this is not a solver RSS bound: learned clauses, watches, proof machinery, interpreter state and process overhead remain subject to the outer memory guard.

The limited fixed preprocessing uses64*157=10048 point-direction visits, at most256 support choices (audited actual246), and445536 pair-table determinant checks. It does not repeat the original955031-visit whole-grid scan. Construction adds at most30135 support-pair compatibility checks,2178 counter recurrences,2016 old-mask scans and41664 pool-triple membership checks, plus at most237112 literal emissions and one CNF byte copy. All loops use the same deadline and started/completed counters. Actual clause/literal counts and the exact CNF SHA-256 must be recorded. The previous0.704-second preprocessing-plus-capped-DFS result establishes feasibility of that earlier path only; no SAT runtime/RSS estimate is inferred.

## Proposed future gate, still unallocated

If both design reviewers accept, implement in new files without editing the frozen DFS, then complete independent tiny/source validation. Before any actual run, select and pin one available proof-capable SAT backend, its version/binary, deterministic options, model format and proof format; inspect its license/invocation and demonstrate tiny proof verification. Do not install a solver, download binaries or run a benchmark as part of this design. Backend/proof-checker availability is an implementation prerequisite, not an assumed fact.

The proposed actual scope is one25-second shared soft interval inside the unchanged owned30-second/sampled256-MiB guard. Include all input validation, fixed-preprocessing reconstruction/hash checks, encoding, solver, model/proof checks, at most one residual root check and publication. Invoke at most one fresh SAT process, once, with one immutable CNF: no incremental solve calls, warm starts, old checkpoints, portfolios, seed retries, assumption loops or model enumeration. Bound native SAT time by the lesser of10 seconds and the remaining soft time minus a three-second validation reserve; if there is no positive interval, do not launch. The reserve is a scheduling choice, not a claim that validation always completes in three seconds; all subsequent checks still obey the shared deadline.

Use an8MiB hard proof-file cap,64KiB stdout and64KiB stderr capture limits per native process, and a32KiB parsed model-text limit. The accepted model must contain exactly2645 unique nonzero signed variable assignments in range (or the exact smaller declared variable count after an explicitly reviewed variable-elimination policy); reject duplicates, omissions and conflicting assignments. No new variable-elimination policy is proposed here. A reader reaching a stream cap terminates the native process and marks the attempt incomplete/error; it must not silently truncate a required model/proof or continue unbounded buffering. The proof must go to its capped file, not an unbounded output pipe. A proof cap stops this attempt rather than triggering a retry or dropping certification requirements. The backend must demonstrate hard file-cap enforcement in tiny tests before allocation, including a child that attempts to exceed the cap.

Both the SAT backend and any proof checker must inherit the already owned worker PGID and SID: no new session, detached process group, daemonization or checkpoint service. Native children are tracked; after exit or termination, the parent must reap the child and verify no tracked descendant remains before launching any next native process. Termination permits at most0.1 seconds of TERM grace followed by KILL and at most0.4 additional seconds for reaping/descendant cleanup, all inside the existing owned guard. If cleanup is not demonstrably complete within that0.5-second bound, report cleanup failure and launch no checker or further native work; the outer guard retains responsibility for final owned-group cleanup. Never kill unrelated process groups. These inheritance, timeout, fork/descendant and cleanup-failure cases require tiny lifecycle tests.

A pinned independent proof checker may run once after UNSAT, only after the SAT process is fully reaped. Bound its native wall slice by the lesser of5 seconds and remaining soft time minus a one-second reporting/cleanup reserve. If no positive slice remains, preserve unverified UNSAT and do not launch. It shares the same process-group, stream caps, termination/reaping procedure and outer memory/time envelope; it is not a second SAT process. Its proof parsing/deletion behavior, exact CNF/proof binding and cap handling need separate source/tiny review. No checked proof means no closure. Proof text size does not by itself bound checker memory, so the outer guard remains authoritative. Avoid optional proof compaction or a second converter process in this gate. Backend/checker selection, pinning and demonstrated hard8MiB proof enforcement remain prerequisites to any actual allocation.

Save complete independently validated evidence immediately, including if validator two finishes just after the soft deadline; never begin validator two after the deadline. A valid149 diagnostic and a root-ready149 artifact must have different explicit labels and separate completeness flags. Pins are checked before acceptance and again at report publication. Exit status preserves incomplete versus ready versus checked-UNSAT versus error, with no automatic continuation after any outcome.

## Required independent tests and rejection conditions

On small synthetic pools, exhaustively compare satisfying semantic selections with a determinant-based enumeration of all support subsets, including all four triple classes and same-F/different-Q cases. Enumerate threshold-counter assignments for small input lengths to prove exact cardinality and uniqueness. Deliberately remove each reverse equivalence in a test copy to exhibit why free deletions or unsupported q values are wrong. Test support pairs that share only an axis, not an endpoint. Verify clause-count/literal-count bounds and exact emitted CNF/header hashes.

Require tiny SAT and UNSAT fixtures, malformed/incomplete models, contradictory assignments, invalid proofs, truncated proofs, native/proof timeouts, proof cap, process cleanup, pin changes, write failures and deadline boundaries. Include a valid scaffold whose first residual graph fails matching/cycle, and a root-ready scaffold whose proposed residual cells are jointly invalid; neither permits a second model or full-witness label. Proof-backed fixed-pool UNSAT must be distinguishable from proof-incomplete UNSAT. No n79 solver run is part of these tests.

Reject or revise this proposal before allocation if the chosen backend cannot fit the one-process proof/model contract, a proof checker cannot be reviewed/pinned, or exact fixed-pool equivalence or bounded artifact handling fails review. Native search has no useful deterministic runtime bound here; failure within the declared caps remains an honest bounded failure, not grounds to enlarge them automatically.
