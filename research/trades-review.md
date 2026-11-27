# Independent review: mixed permutation trades

Reviewer: gpt-6.1-terra, high reasoning, per assignment; 2026-11-26. Inspected `src/trade_search.py` and `tests/test_trade_search.py`; review is of the algorithm and safeguards, not evidence that n=79 is infeasible or that a valid full witness was found.

## Findings

The two-disjoint-permutation representation gives exactly two points in each row and column. Both pair swaps and three-row rotations permute the selected matching's existing columns and check that no replacement collides with the other matching. Consequently row and column degree two is maintained, provided the input permutations already have the stated invariants. Recoloring a complete alternating cycle swaps matching colors without changing the point set, preserving those invariants. The source validates resumed states' range, duplicates and degree two, recomputes its score with two independent verifiers, and decomposes the degree-two graph into matchings.

The score delta removes changed points sequentially, subtracting all triples through each removed point in the then-current set; each affected old triple is removed once. The insertion sequence analogously counts each new triple once. Signed normalized directions correctly group both directions along the same undirected line. The existing tests check every legal ordered triple rotation and pair swap for one sampled state per size through n=7, comparing resulting degree and score with independent brute-force determinants. They do not enumerate every full state or prove move-graph connectivity. The implementation also audits its retained best state with both checkers before returning, and independently validates the pruned or supplied incumbent; a nonzero full state is explicitly labeled invalid.

A resumed run retains its input full state's recomputed score as the starting best, and updates that best only on a strict score decrease. Restarts from the current best when resuming. A supplied valid incumbent is retained unless the pruned best is larger; the valid incumbent has its own grid n and may have come from a smaller embedded grid, so downstream consumers must inspect certificate n. Tabu keys represent point sets independent of matching colors, and repeated accepted keys are rejected unless they strictly improve the global best. Since an earlier accepted key cannot have a lower exact score than the global best, this aspiration appears effectively unreachable under correct scoring; it is harmless but should not be described as providing a normally usable escape. The cache is a search heuristic and does not justify an infeasibility conclusion.

The source's global `seen` set is unbounded, containing full sorted point tuples for every distinct accepted state. In a long-running worker this can dominate memory; even the tuple-reference storage alone scales as roughly 158 pointers per state at n=79, before points and hash-table overhead. A bounded cache or compact approximate counter with clearly labeled telemetry is needed before assuming a long worker's memory stays bounded. This concern was sent to the implementation owner and supervisor. Operation-cap reproducibility requires that no earlier wall-clock cutoff interrupts the run; when both are set, the wall clock can win.

Stopping due to time or an operation cap is a bounded search outcome, not a no-solution proof. The code calls a run a valid full state only on score zero and independently verifies the returned state. Neither a positive best score nor a restricted neighborhood, tabu rejection, or restart yields a global lower bound on conflicts.

## Supervisor safety note

A separate inspection of `src/experiment_pool.py` found that the pilot deadline and worker-time budget are polled, and child termination is sequential with a grace period. A strict wall-clock deadline can therefore be exceeded by polling and cleanup. An unexpected supervisor exception also enters a cleanup path that terminates children without writing their receipts or charging elapsed time, allowing a later restart to undercount the aggregate budget. These issues were reported to the supervisor owner for correction; this review does not approve hard-deadline accounting until resolved.

## Follow-up: bounded history

The implementation owner replaced unbounded `seen` with a configurable fixed-capacity LRU history (default 10,000 states) and added telemetry for capacity and evictions. Inspection confirms insertion evicts the oldest entry when the bound is exceeded and revisits update recency. This resolves the unbounded-history concern above, subject to selecting sensible `history_size` and `tabu_size` for the worker's memory budget. Reported revisits now explicitly cover only the cache, not lifetime distinct states. A test exercises evictions at capacity two. This change does not change the geometric score or certify search completeness.

## Follow-up: uncolored rectangle neighborhood

`rectangle_proposal` uses any two selected edges with distinct endpoints and replaces them with the unique crossed pairing, if neither crossed edge is occupied. This preserves degree two and covers every uncolored simple two-edge switch; reversing the two old edges is the same switch. As with the colored trades, sequential subtraction and addition counts all affected triples once. Tests compare all legal switches for sampled small states with full independent determinant scores. Accepted switches are decomposed anew into disjoint matchings.

For the recorded score-11 state, I reconstructed the source from the audit's stored best neighbor and old edges, checked its normalized hash and independently checked source and best-neighbor scores (11 and 12). Independent enumeration of its 12,403 old-edge pairs reproduced 158 same-axis, 156 occupied-crossing and 12,089 legal switches; I checked 64 sampled legal deltas against full brute-force determinant scores. The saved complete histogram reports all deltas positive, four of them +1. Thus the recorded computation supports a strict local minimum in this **one-state two-edge neighborhood**; I did not independently recompute all 12,089 full scores. A local minimum does not preclude uphill moves, larger switches or a full solution elsewhere.

A further independent complete arithmetic check used a separate short C++ determinant program: for each legal switch it directly counted old and new triples involving either switched edge. All 12,089 delta frequencies matched the recorded histogram exactly, as did all rejection and legal counts. The exact program executed from a temporary file is now retained as `research/independent_rectangle_histogram.cpp`.

## Threshold barrier component

For the fixed score-11 state, an independent C++ breadth-first implementation (the exact source is retained as `research/independent_rectangle_check.cpp`) using direct integer determinants recomputed the entire rectangle-switch component restricted to score ≤12. It found exactly six states (one score 11 and five score 12) and twelve directed within-threshold transitions. This independently corroborates the recorded finite component result; no claim is made about paths that cross score 13, other move classes, or global existence.

The resumable Python worker reconstructs stored nodes through legal parent switches, checks hashes and scores, preserves scan offsets on interruption, and reopens known nodes on threshold increase. Its structural validation cannot establish that an allegedly completed scan actually happened or that a checkpoint did not omit neighbors. Exhaustion after resume is conditional on a complete, unmodified local checkpoint unless completed neighborhoods are independently replayed. This limitation was reported to the worker author.


## Reproducing the independent C++ checks

The two files above are byte-for-byte copies of the exact sources executed in this review. SHA-256: BFS `1ac1fd7e643bec5f0e81291beb6b084f9f9d38e5da571911c951dafc2a5349ec`; full histogram `e7186f3e18b92d6a7520aea8aff77a327edfc8123da5e62dab6be463e1eafa3e`. Both read `/private/tmp/no3-rectangle-input.txt`, consisting of the score-11 state, one sorted `x y` pair per line. Reconstruct that exact input from the saved audit in the research workspace with:

```sh
python3 - <<'PYCODE'
import json
r=json.load(open('data/trades-rectangle-neighborhood-audit.json'))
p={tuple(p) for p in r['best_neighbor_state']['points']}
(a,b),(c,d)=r['best_switch_old_edges']
p.remove((a,d)); p.remove((c,b)); p.update(((a,b),(c,d)))
with open('/private/tmp/no3-rectangle-input.txt','w') as f:
    for x,y in sorted(p): f.write(f'{x} {y}\n')
PYCODE
shasum -a 256 /private/tmp/no3-rectangle-input.txt
```

The reconstructed input's recorded SHA-256 is `db3db9bd91c01995f8658e7776953b64db3e3669fc817306f97d2cf27ea12956`. The source normalized certificate hash is the `source_normalized_sha256` in that same audit; the original review independently checked it and the source's 11 triple conflicts. Compile and run, from this workspace:

```sh
c++ -O3 -std=c++17 research/independent_rectangle_histogram.cpp -o /private/tmp/no3-rectangle-independent
/private/tmp/no3-rectangle-independent
c++ -O3 -std=c++17 research/independent_rectangle_check.cpp -o /private/tmp/no3-barrier
/private/tmp/no3-barrier
```

Observed in the original executions: histogram: 158 axis rejections, 156 occupied-crossing rejections, 12,089 legal switches, all positive deltas matching the JSON histogram; BFS: six states, twelve directed transitions, one score 11 and five score 12. These programs are narrowly scoped checks on the reconstructed 158-point state; the BFS uses its previously independently verified starting score 11.
