# Tiny iterative row-batch core and checkpoint implementation

This implements the first bounded components of the approved design in
`near-quarter-rowbatch-core-checkpoint-design.md`. The frozen secant and batch
references are unchanged. Sources are isolated in `near_quarter_rowbatch_cursor.py`,
`near_quarter_rowbatch_core.py` and `near_quarter_rowbatch_checkpoint.py`.
Model setting: `gpt-6.1-sol`, reasoning `high`.

The core replaces recursive control with explicit counted, pending, waiting,
leaf and completed frames. A complete row-filling singleton or unordered pair
is the unit of branching. Parent cursor advancement commits with child entry;
restoring an entered frame does not count it again. Deterministic MRV and the
reviewed orbit/row shortfall bounds are preserved. The cursor streams pairs and
never stores their potentially quadratic list or a uint16 flattened pair count.

The fixed codec binds source, map, order, policy and leaf-mode identity. It
requires trusted content, parent and chain hashes, checks the external raw-byte
hash before parsing, strictly validates the phase union, and reconstructs all
geometry privately before returning a core. An interrupted replay returns no
partial core. Source hashes captured at import must still match bounded local
source reads. `save_candidate` compares replayed geometry/frontier/counts with
live state before writing, owns a chain lease, and installs an immutable,
fsynced content-named candidate. It does not advance supervisor acceptance.

Nine focused tests passed in 0.610 seconds. All real n3/n5/n7 phases roundtrip;
repeated one-node stages equal uninterrupted traversal in final state, logical
counters and leaves. They match the frozen reference's 1/0/0 complete sets and
2/5/11 nodes under forward/reverse declarations. Repeated first-event delivery
and acknowledgment preserve one counted leaf. An explicit abstract quota
fixture with twelve complete sets tests accepted pair paths and every-transition
replay under forward/reverse orders, without a physical geometry claim.

Tests also cover pair rollback after first/second-orbit cancellation and a
second-orbit rejection or pre-mutation exception; every replay check's
cancellation boundary; external/source/parent/chain/phase corruption; active
logical-event counter contradictions; corrupt live geometry; writer collision;
stale-lease refusal; immutable duplicate saves; and five write/fsync/link fault
boundaries. Details and exact source hashes are in
`data/near-quarter-rowbatch-core-checkpoint-evidence.json`.

The schema supports checked identity arithmetic up to n79, with a maximum
7,868-byte v1 envelope and forty frames. The implemented geometry adapter is
hard n3/n5/n7. The production adapter, point-loop cancellation contract, stage
report/supervisor acceptance and owned-process wrapper remain separate work.
There is no shared dispatcher route or n79 geometry run for these modules.
No RSS or hard process wall-time measurement is claimed. Historical counters
need accepted external provenance: compact frontier replay does not prove past
subtree exhaustion or provide an independently checkable UNSAT certificate.

The proposed 157-point escape retaining only three points of the last orbit of
an invalid 158-point candidate is closed by the reviewed elementary lemma in
`half-turn-one-deletion-lemma-review.md`: for a center-absent half-turn-invariant
set containing a collinear triple, a collinear triple remains after any single
deletion.
Thus a valid such 157-point subset already extends to the valid full 158 set.
No callback or implementation was added and no novelty is claimed. This says
nothing against other 157-point configurations or less symmetric constructions.
