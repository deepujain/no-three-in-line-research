# Isolated exact read-only orbit probe

Prototype only, not imported by the live core. Implementation model
`gpt-6.1-sol`, reasoning `high`. Implements the independently approved triple
partition in proposala1bcdfb6; integration/new source identity is not authorized
by this prototype evidence. Live core2f758f63, codec88ce7a7a, worker7f8c8a16 and
packed state860711b8 remain unchanged.

`research/near_quarter_readonly_probe.py` SHA-256
2b9f51496f80c78881643724029e48cd9987b1428bdffbce7736806d790f5c7d.
`tests/test_near_quarter_readonly_probe.py` SHA-256
381e3d64e1deb53183836fbbc4a97634e605211a883a53663fadcbef07f89809.
Evidence `data/near-quarter-readonly-probe-tiny-evidence.json` SHA-256
9a6efc3ff478a401cee7879c6adf9eec618a717be73aa9974d28371a1e09d502.

The query matches actual push admission on coherent valid states. It propagates
unusable/poisoned/latched errors, rejects strict-ID and selected/family failures,
reads candidate occupancy/blocker/axis loads, checks full candidate row/column
contributions, checks candidate-only determinants, and queries occupied cells
on candidate-pair maximal lines. Duplicate candidate cells reject before any
pair-line call. It mutates no geometry, transaction flag or work counter. The
claim does not cover corrupt capacity-fault poisoning behavior. Committed
push/pop and final verifiers are unchanged and unused by the new predicate.

Four tests passed in0.356s. Every coherent n3/n5/n7 orbit subset was considered:
4/17/100 valid states, all8/102/1200 candidate extensions, compared against both
actual push+undo and independent integer determinant/axis checks. Admissions
were4/26/224. An additional800checks use deterministic random insertion orders
and repeated candidate IDs. Dedicated generic-cell cases isolate row/column
capacity, old-pair/new-point, new-pair/old-point, internal triple and duplicate
candidate failures. The generic-cell routine is test-accessible to cover
internal triples even though the fixed four-orbits themselves are squares.

165individual budget boundaries along three representative query paths were
interrupted with byte-identical full state snapshots and unchanged work maps.
This is not a fault sweep of all1310candidate cases. Poisoned state fails;
latched PackedStop propagates exactly as the existing `_usable` contract. An
initial test wrongly expected PackedStateError for a latched stop; its expected
exception was corrected without changing production state code.

Physical accounting is intentionally separate: this prototype updates no work
counters, unlike actual mutating push/undo. It therefore cannot be integrated
by silently presenting query work as blocker mutations or claiming equal
physical totals. Future integration needs explicit reviewed counter semantics
while preserving actual cell_increments/inverse_cells as writes. No new guard,
lease, report protocol, scheduler, cache or numerical allocation is included.
No host run or n9/n71/n79 geometry occurred, and no speedup is claimed yet.
