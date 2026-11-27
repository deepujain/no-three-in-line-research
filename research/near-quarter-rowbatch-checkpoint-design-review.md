# Independent near-quarter row-batch checkpoint design review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Design
`research/near-quarter-rowbatch-core-checkpoint-design.md`, SHA-256
`4fec375ec0530186506f2a968567d2dd847094b6dcd22eedd76cd938d04369f1`,
is approved for the Lead's staged component implementation and tiny correctness
tests. No implementation, production adapter, host guard, shared dispatcher,
n79 geometry instantiation or numerical run is approved by this design review.
No numerical experiment was performed for this review.

The full-row batch completeness/uniqueness proof remains sound. Every full
extension determines its sole singleton or unordered pair filling the chosen
row. Distinct valid paths cannot merge because their first divergent batches
fill the same row and their union overfills it. The streaming local-index cursor
enumerates all permitted singletons then weight-one pairs once, without a
global orbit-ID ordering restriction or quadratic candidate list.

The explicit state machine separates uncounted ENTER from counted unfinished
COUNTED work. READY/PENDING retain parent geometry. A PENDING outcome commits
its logical attempt/cursor update once; success also atomically installs a
WAITING parent and an ENTER child. The child records the origin cursor and
incoming batch, allowing replay to verify that the parent's saved next cursor
is exactly its successor. All lower frames are WAITING and only the top runs.
Prepared bounded metadata and latched cancellation are necessary to prevent
half-committed parent/child changes or partially undone geometry. An aborted
stage cannot publish an intermediate mutation as a coherent frontier.

LEAF delivery and acknowledgment are distinct. Logical leaf count changes once
on entry, repeated delivery does not recount, and first-event FOUND retains the
same verified LEAF path with WAITING ancestors. Tiny census acknowledgment
instead closes that leaf with an explicit DONE reason. Named prune/closure
reasons have replayable conditions and canonical layouts. Physical probes,
reconstruction and aborted work are separate from accepted logical counts.

Initial review requested concrete byte layouts rather than deferring struct
offsets. The revised design provides them: a 46-byte envelope; 512-byte identity
with seven fixed source slots; parent and chain hashes; 128-byte control area;
exact bounded permutations; and 96-byte phase-union frames. Identity source
slots occupy bytes80..303 and its remaining208bytes are reserved. Frame phase,
incoming/origin, domain/next, pending, leaf and reason fields fit bytes0..95;
inactive fields and padding have explicit zero requirements. The FOUND/LEAF
layout, root NONE cursor and DONE reasons are now explicit.

The maximum wire arithmetic is
46+704+2*(39+1521+79)+96*40 = 7,868 bytes, independently checked. The larger
1MiB read cap is a defensive outer ceiling, not a v1 extension mechanism.
Grid validation, derived permutation lengths and frame/path bounds precede
count-dependent allocation. Pair cursors store two uint16 indices rather than
a flattened pair count that could exceed uint16. These are format/storage
bounds and do not predict Python/native RSS or throughput.

Load requires a trusted record containing content hash, parent hash and nonzero
chain ID, plus expected identity. It checks bounded regular-file input and the
external raw-byte hash before parsing declared fields. Private replay verifies
every prefix's deterministic domain, chosen row, cursor, batch admissibility,
full row fill, parent-child successor, top phase, closure/leaf condition and
source/permutation identity. Only a completely validated reconstruction that
passes the deadline check is adopted. Interrupted replay yields no partial core
or candidate; historical accepted counters remain provenance claims rather
than proofs of every prior subtree.

Candidate publication uses an exclusive chain lease, same-directory temporary,
file fsync, no-overwrite content-hash installation and directory fsync, followed
by a durable stage report. It preserves immutable parent bytes and leaves
acceptance advancement to the supervisor after independent source/resource/
cleanup checks. Orphan candidate files cannot authorize continuation. Stale
leases are not automatically stolen and stale-parent reports cannot advance
the accepted chain. The stated source binding, lease and publication semantics
must be verified in actual code and fault tests; prose approval is not evidence
that the filesystem behavior already exists.

Implementation review must cover exact golden bytes and malformed inputs,
all reachable tiny phases, one-node and interrupted stages, counter stability,
repeated leaf acknowledgment, private reconstruction failure, writer collision
and publication faults. The separate generalized state adapter must support
rollback even when cancellation arrives during secant updates; the frozen tiny
state's ordinary rejection rollback is insufficient to establish that property.
No further generic feature is required before starting the approved components.
