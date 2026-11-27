# Connected-path retained-secant and flow census

Implementation model: gpt-6.1-sol, high. Eight tiny tests pass in 0.053 seconds.
Mathematics and exact32case incidence manifest are independently approved.
Source review is pending; no actual-source safe-cell census, completion search,
or host run was performed for this delivery. All existing sources stay frozen.

The new source reconstructs all8/10/14 connected paths of lengths10/12/16
containing the approved three-edge conflict cover. Their rectangles have
30/42/72 cells,1668 candidate/template records total. Their retained sets have
148/146/142 points and are valid because every original triple intersects the
deleted cover. The frozen source loader runs both complete validators, pins
the exact source bytes/normalized identity, and checks all11 original triples.

The census tests each candidate cell against all retained pairs via the frozen
exact normalized-direction helper. Deleted original cells can be readded if
they pass the same filter. Every completed case retains its complete safe-cell
list and counts safe original readditions and safe new cells separately.
No two-added/one-retained or three-added geometry is evaluated in this census.

Each safe-cell set induces a bipartite integral-capacity flow network. Residual
axis capacities are derived independently from retained source degrees and
compared with the pinned case manifest. A deterministic BFS augmenting-path
algorithm computes maximum cardinality. Selected safe-cell edges and the
residual-reachable row/column sets form the certificate. A separate arithmetic
checker validates primal axis capacities, cut capacity and equality of their
values. Thus retained_count+flow_value is an exact axis-capacity upper bound
on final cardinality. Values at most156 close only that patch; larger values
save an eligible patch with unresolved geometry, never a witness.

The network has at most19 vertices and89 forward arcs; each unit augmentation
increases flow and total flow is at most16. At most424 augmentations span all
32cases. The census holds one small network at a time. No cap-five proof,
factor enumeration, completion solver, scheduler, guard, checkpoint or resume
protocol is added. Frozen path8 helpers are imported only for source-cycle
incidence traversal and clock checks; no length-eight case is enumerated.

One shared soft deadline of at most25 seconds begins before source/evidence
validation. It is checked between cell tests and during flow BFS/augmentation.
One source validator or cell test is indivisible; the existing Root-owned
30s/256MiB guard remains the outer gate. Every case is unstarted,
partial_safe_census, partial_flow or complete. Started and completed cell
checks differ if interrupted, and a case completes only after its whole safe
census and certified flow bound finish. A timeout saves any completed bounds
and unresolved status for the rest; no pending case is closed.

Tests compare1296 small networks against exhaustive subsets, exercise reverse
residual reassignment, reject corrupted primal/cut certificates, reconstruct
the32cases without source geometry, compare retained-secants to direct tiny
integer determinants, and cover prevalidation/cell/flow timeout accounting.
The complete-run report tests use mocked geometry, for both all-safe eligible
and all-blocked closed families. Any future actual evaluation remains owned
by Root and requires accepted independent source review.
