# Exact read-only packed admissibility integration

Awaiting independent source/allocation review. Model `gpt-6.1-sol`, reasoning
`high`. Replay-only baseline sources are preserved in commit1d02440; all saved
frontiers retain original bytes. Fresh derivation required, no migration.

Core `research/near_quarter_rowbatch_core.py` SHA-256
f257045276d1247fde814fae01fe0a470233c477e228c37b6d3209fd367439ae.
Codec88ce7a7a, worker7f8c8a16, packed state860711b8, radius helper647ae137 and
pure read-only probe2b9f5149 are unchanged. The core source now transitively
binds both helper literals and bounded import-time/current-source checks. The
seven checkpoint/nine worker source-slot shape remains fixed. Exact admission
preserves policy2 and search behavior; core source hash creates a new identity.

The production diff is26core lines: adapter2 scanner calls the reviewed pure
query rather than temporary push/undo. Histogram weights use the parent row
loads directly. Adapter1 retains temporary push, subtraction and rollback.
Actual incoming-batch commits, inverse-cleanup contract, private replay/full
live snapshot comparisons, final independent verifiers and all lifecycle code
are unchanged. No guards, protocol, caches or neutral/pool sources were edited.

## Explicit accounting scope

Mathematician agreed these semantics before integration. domain_probes and
restore_probes count each exact admissibility query. The pure helper makes no
work-counter writes. state.work fields retain actual mutating push/pop engine
meanings, so state_total/restore_subset/traversal/validation_extra/physical_total
are exact aggregates only of their declared mutation-engine counters. They
exclude read-only line walking, occupied/blocker reads and determinants. A true
physical_counters_complete means those declared counters are known, not that
all processor/geometry operations have been enumerated. Wall timings plus query
totals measure query cost. Do not compare blocker updates alone as total work
or describe removed writes as a measured wall speedup.

## Evidence

63tests passed in5.161s under unchanged10s command ceiling. Evidence
`data/near-quarter-readonly-integration-tiny-evidence.json` SHA-256
ab4f82815c97bee85296f2c97ee82d8e32262a9dd4450d45562f9e0066122404.
Focused tests `tests/test_near_quarter_readonly_integration.py` SHA-256
dc5de8f306a5746a562221c613cab449ee8a591a6db0b5ee40e47643444f4021.

All73coherent below-target n3/n5/n7 prefix scans return the exact same prune or
MRV domain IDs/weights/deficit/order as an actual mutating push/undo admission
oracle. Every forward/reverse tiny frontier/control/logical count and query
counter matches; nodes remain2/4/11, leaves1/0/0. All559query-budget checks in
an integrated root COUNTED scan are individually interrupted with identical
frontier/geometry/logical counters and mutation-work map. The pure prototype's
1310exhaustive extensions,800random-order checks and explicit collinearity/axis/
duplicate cases still pass. Full existing state/replay/lease/fault tests pass.

Full n7 blocker increments are10614with mutating scan probes versus521with the
new scanner. Domain probes stay235; both forward/reverse counts match. The521
remaining increments are real committed geometry. Query reads/walks are absent
from those mutation counts, and host performance is not established here.

Prepared request/proposal `data/packed-readonly-n79-r1-root.request.json` and
`data/packed-readonly-n79-r1-root.proposal.json` bind current manifest, both
transitive helper hashes and counter scope: fresh absent chain, same historical
map/declaration, root operation,max_new_nodes0,30s/256MiB,2s reserve. Preparation
used only source/artifact reads and permutation arithmetic. No actual-host gate
or n9/n71/n79 geometry ran for this integration package. Root/scheduled caller
runs only after independent source/request approval, then separately allocates
a same-declaration measured stage. No large quota follows from tiny evidence.
