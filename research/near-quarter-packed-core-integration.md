# Closed packed adapter integration with the row-batch core

This stage integrates the independently approved packed state into the isolated
row-batch core and fixed checkpoint codec. Adapter1 keeps its hard n3/n5/n7
constructor and first-event/tiny-census modes. Adapter2 has one closed
`PackedRowBatchCore` constructor, checked odd n3..79 bounds and first-event mode1
only. This is source capability; this stage instantiated only n3/n5/n7.
There is no shared CLI/guard/wrapper/report/acceptance-pointer change or broad-
grid execution. Model setting: `gpt-6.1-sol`, reasoning `high`.

The existing v1 wire layout is unchanged. The adapter tag and seven source
slots select a literal class/source bundle, with separate import-time state
hashes for tiny and packed geometry. Class/tag mismatches and adapter2 mode2
are rejected. New core/codec source hashes intentionally differ from the earlier
hard-tiny bundle; old accepted artifacts remain bound to their original source
identities. There is no hash substitution, implicit migration or history merge.

The domain scan retains one current byte admissibility mask and two unsigned
row histograms, rather than contributor lists for every row. MRV cardinality
is c1+c2 and the optimistic top-r load is
2*min(c2,r)+min(c1,max(0,r-c2)). Declared row order still breaks ties, and the
current domain follows orbit order. The reviewed immutable cursor owns bounded
Python domain tuples; their object overhead is not included in packed-array
arithmetic. No ancestor domain cache or quadratic pair list is introduced.

Every packed operation receives the common budget check. Temporary probes and
whole-pair error/rejection cleanup use `rollback_last_orbit()`, which completes
despite an expired budget. Before propagating an original error they clear a
latched cooperative stop only after returning to the unchanged parent geometry.
For DONE frames, the full incoming batch is popped, then the frame/slice state
commits, then `raise_latched()` propagates cancellation. A stop during the pop
therefore leaves the new coherent frontier; stops during insertion leave the
old pending frontier. Point-level inverse faults poison and prohibit adoption.

Before saving, adapter2 must be checkpointable, packed lengths/offsets/cells
must have their declared shapes, and the actual current map digest and source
files must match the executing identities. Private replay still checks all
parent/child/cursor/domain and event-counter relations, then compares the full
replayed/live geometry and frontier before any write. Restore records physical
geometry work separately from logical nodes. Save-validation replay work is
also recorded, including validation performed before a later publication fault.
No stage receipt or acceptance advancement is implemented here.

Combined regression ran23 tests in4.677 seconds: the earlier9 core/codec tests,
9 isolated packed-state tests and5 new integration tests. Both adapters agree
at every reachable tiny phase under forward/reverse orders, with2/5/11 nodes
and1/0/0 leaves, and repeated one-node saves/resumes produce the same result.
Repeated first-event acknowledgment does not add leaves or nodes.

Integration fault tests inject sticky stops at4954 checked step boundaries.
Each result exactly equals either the old full snapshot or the already
roundtripped fully committed snapshot;126 stops occur after a coherent pop/frame
commit. Another587 checked n3 private-restore boundaries return no adopted
partial core. Whole-pair cleanup is separately exercised with actual valid n7
pair[1,6] and rejecting pair[1,2], including stops after the first/second accepted
orbit and during rejection cleanup. Current real tiny MRV trees contain zero
saved two-orbit incoming frames; those pairing helpers and the earlier explicit
abstract12-leaf quota fixture are not mislabeled as physical saved-pair
frontier evidence. Larger physical pair-frontier evidence remains future work.

Actual packed-map mutation, corrupt live rows/counters/point buffers, poison
and latched-stop states are refused before candidate adoption. All five
immutable-save fault boundaries preserve the installed parent/content. The
first unoptimized test command spent its10-second local command budget on
redundant per-fault wire replays; the final harness uses already-roundtripped
templates while preserving all4954 stop locations. All23 tests pass under the
same unchanged10-second command ceiling. This is a test-harness observation,
not a process/RSS gate or numerical-search resource result.

Exact source identities, checks and limits are recorded in
`data/near-quarter-packed-core-integration-tiny-evidence.json`. Independent
integration source approval and separately Lead-scheduled actual-host gates
remain required. No n9/n71/n79 geometry or search ran, and no runtime/memory
fitness or infeasibility claim follows from these tiny tests.
