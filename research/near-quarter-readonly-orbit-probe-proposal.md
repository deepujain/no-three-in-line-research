# Exact read-only orbit admissibility probe

Read-only proposal, not implementation or a changed source identity. Current
codec88ce7a7a, core2f758f63 and worker7f8c8a16 stay frozen. Model
`gpt-6.1-sol`, reasoning `high`. No host monitor or geometry above n7 ran.

The next concrete hotspot is temporary blocker construction and inverse cleanup
merely to ask whether an orbit is admissible. `_scan` currently calls push,
reads the row weights, then fully undoes each successful probe. Failed partial
probes also undo their completed updates. Actual incoming batches still need
push/pop; their state updates are necessary. Most probe state writes are thrown
away immediately.

One cProfile run of the current n7 full tiny tree, construction excluded, with a
monotonic-clock budget check and a fixed5s profile deadline, measured:

| Item | Observation |
| --- | ---: |
| Tree | 11nodes,8batch attempts,no leaves |
| Profiled elapsed | 33.294458ms |
| `_scan` | 27calls,30.974623ms cumulative |
| Domain probes / all orbit attempts | 235 / 246 |
| Blocker increments / inverse writes | 10614 / 10614 |
| `line_span` | 5750calls,9.511985ms cumulative |
| Budget checks | 52562calls,8.400302ms cumulative including clock |
| `_work_inc` | 25987calls,2.795792ms own |

Times overlap and must not be summed. Profiling overhead and tiny geometry
prevent broad-grid speed extrapolation. Nevertheless, the source and counters
identify an exact avoidable operation: producing every old/new secant's grid
blockers, then removing them, during each current-domain membership test.

## Proposed primitive

For coherent valid selected points S and a candidate orbit C (four points for
scanner probes), implement a bounded read-only admissibility query:

1. Apply the same usability, strict ID, selected/family cap and point-cap checks.
2. Read at most4candidate cells; require no occupied duplicate and exact current
   row/column load plus candidate contribution <=2.
3. Require blocked[c]==0 for each candidate cell c. Since c is unoccupied, this
   excludes exactly the triples consisting of two selected points and c.
4. For each of at most6unordered candidate-point pairs, generate its maximal
   grid line and reject if any cell is occupied by S. This excludes exactly
   triples consisting of that pair plus one selected point. Candidate endpoints
   are already known unoccupied, so no endpoint special case is needed.
5. Check the at most4candidate-only triples by integer determinant (or prove the
   trusted quarter-turn orbit is a square; retaining4checks avoids that extra
   implementation assumption). Return admissible only after all budget checks.

All triples in S union C are partitioned by the number of candidate points.
Zero-candidate triples are absent because S is valid; the remaining three cases
are exactly steps3..5. Thus this is an exact admission predicate, not a weaker
relaxation. Axis/family/occupancy constraints also match push. It can replace
only scanner push/undo without changing MRV masks/order or committed geometry.
Current `_scan` row-histogram arithmetic must then use parent rows directly,
rather than recovering parent load by subtracting a temporary contribution.

The query needs no mutation transaction, inverse rollback, global cache, line
catalogue or matching solver. It uses the existing occupied and blocked arrays
and at most one current pair-line span. At n79 it queries at most6lines, each
at most79cells, for a four-orbit; this arithmetic bound is not a geometry run.
Existing push constructs4*|S|+6new pair-lines for an accepted four-point probe
and recomputes them during inverse removal. The new query cost is independent
of |S| except for existing array state and early rejection behavior.

Budget checks remain before/within bounded loops. A stop returns no admission
verdict; because the query does not mutate geometry, no partial inverse is
required. Physical accounting must retain honest meanings: point_attempts and
pair_lines can count actual query checks/line construction; cell_increments and
inverse_cells remain actual writes. Any finer read-query metric is optional and
must not be mislabeled as a blocker update. No guard, receipt, lease or accepted
HEAD protocol changes are part of this optimization.

## Validation and release boundary

Before any implementation, independently review the exact triple partition and
axis/family semantics. Root must release the active source manifest. Then use
an isolated primitive/tiny tests: every n3/n5/n7 coherent prefix and every
candidate compared with current push+full undo and independent determinant
checking; budget interruption at every query boundary with identical snapshots;
then integrated masks/histograms/MRV/cursors, replay/live equivalence and full
existing tests. Commit pushes and both independent witness verifiers stay.
Only after source review does Root allocate a fresh same-declaration guarded
comparison. No speedup, larger quota or continuation is assumed from this note.
