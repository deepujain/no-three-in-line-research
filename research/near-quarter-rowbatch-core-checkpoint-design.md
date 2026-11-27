# Near-quarter row-batch core and checkpoint design

Status: proposed state machine and wire contract for independent design review.
No production core or checkpoint is implemented by this document. The separate
frozen tiny secant and batch references remain unchanged. This is a direct
geometry engine; no Solver, resident CNF, shared DFS/chain/CLI or owned-process
helper change is proposed. Model setting: `gpt-6.1-sol`, reasoning `high`.

The Lead allocation covers a production-capable core/checkpoint prototype after
design approval. The schema and checked arithmetic support odd grids 3..79,
rejecting larger/even grids before model allocation. First component tests and
geometry instantiations remain n3/n5/n7. A separate wrapper/actual-host gate is
required before n79 execution; this design is not a numerical-run allocation.

## 1. Bounds and component ownership

New separate modules are `near_quarter_rowbatch_cursor.py`,
`near_quarter_rowbatch_core.py`, `near_quarter_rowbatch_checkpoint.py`, and,
when needed, a separate packed-state adapter. The reviewed tiny sources are
references and the first test adapter, not files to generalize in place.

For n=2m+1 <=79: m<=39; there are m²<=1521 four-orbits, m<=39 main-diagonal
pairs, <=1560 total orbit IDs, <=158 selected points, and <=40 node frames
(the diagonal root plus at most m nonempty batches). These limits are validated
before constructing arrays or following declared counts. Every ID, row and
local index fits uint16; a flattened count of candidate pairs does not and is
never stored as uint16. Frame storage is fixed at 96 bytes per frame on wire,
not a claim about Python object size or the earlier live-payload estimate.

Wire bytes are capped at 1,048,576 before read/allocation/parsing, identity bytes
at 4,096 (v1 uses exactly 512), frame count at 40 and at m+1, and selected path
at 40 IDs including its diagonal. Actual permutation lengths must equal the
bounds derived from n, never caller-declared arbitrary lengths. No quadratic
pair array, full tree, leaf dedup cache or set of visited states is retained.
Only one O(m²) current domain/scratch buffer is live; ancestor frames retain
hashes/cursors and reconstruct domains when revisited. This may repeat work.

Each core instance and chain writer has one owner and is not thread-safe. An
exclusive chain-directory lease (O_CREAT|O_EXCL, random nonce, no automatic
stale-lock stealing) excludes concurrent writers. Read-only checking does not
acquire a writer lease. A writer releases only its own matching inode+nonce;
preexisting/symlink/unrecognized lease data fails closed. Local POSIX regular
files are the supported storage contract; remote-filesystem durability is not
claimed. Accepted-frontier advancement belongs to the supervisor after its
resource gate, not the codec. Candidate checkpoint installation cannot itself
advance the accepted chain or authorize a second branch from an old parent.

## 2. Exact state and deterministic row choice

Geometry is the selected orbit set expanded in the frozen map/point order.
The adapter provides reversible complete-orbit push/pop, exact selected/type
counts, row/column loads and primitive-integer secant blockers. A failed push
or a cancelled/raising push restores its entry state. The generalized adapter
must add cancellation-safe point transactions rather than assuming the tiny
reference handles an exception during a counter-update loop. Pair counters
are <=C(158,2)=12403, within uint16. Any underflow/overflow is fatal, not a prune.

For each declared diagonal pair, push that pair once and branch on four-orbits.
The exact target is m four-orbits plus one pair: 4m+2=2n. A leaf additionally
requires every row and column load two, distinct points and both independent
integer geometry checks. A target-sized nonleaf closes without extension.

At a nonleaf, scan the entire frozen four-orbit permutation. Selected orbits
are skipped. Test every remaining orbit transactionally against current state.
For every underfilled row record its positive weight (one or two) among
individually admissible orbits. Count all admissible remaining four-orbits.
Choose row by (domain cardinality, minus deficit, frozen row-permutation rank).
Probe timing, cursor position and insertion history cannot break ties.

Only these initial prunes are permitted: fewer than r=m-selected_four
admissible distinct orbits; or some row's sum of its largest at most r weights
is below its deficit. This optimistic sum can be computed using counts of
weight-two/weight-one entries. No global increasing-ID condition is imposed.
Domain digest is SHA-256 of a versioned byte encoding of chosen row, deficit,
r, and the ordered sequence of (uint16 orbit ID, uint8 positive weight).

## 3. Streaming candidate cursor

A cursor is `(kind,i,j)`: SINGLE, PAIR or END, with canonical sentinels.
Indices refer to the full ordered chosen-row domain, not global IDs. SINGLE
starts at the first entry of weight equal to deficit. Its successor skips
nonmatching entries and then moves to the first pair if deficit=2 and r>=2.
PAIR enumerates only weight-one indices i<j in lexicographic (i,j) order.
Its successor advances j to the next eligible index, then i; exhausted pairs
become END. A pair is omitted when r<2. END has i=j=0; SINGLE has j=0.
Canonicalization rejects unused/nonmatching/out-of-range coordinates rather
than silently skipping a malformed restored cursor. No pending list is built.
Cursor initialization/successor and their skip loops check the common deadline
and cancellation flag. An interrupted successor leaves the old cursor intact.

A pending batch is exactly the one or two IDs named by its cursor, in local
index order. Singletons precede all pairs. Every batch fills the chosen row's
whole deficit and is generated exactly once. Pair application uses the same
point order as ordinary orbit insertion, rolls back the first orbit when the
second rejects or stops, and checks that the row ends full on success.

## 4. Iterative frontier and atomic RAM transitions

Outer phase is BETWEEN, ACTIVE, EXHAUSTED or FOUND. Slice index names the next
unstarted slice in BETWEEN, current slice in ACTIVE/FOUND, and equals the
permutation length in EXHAUSTED. Completed slices are exactly the prefix before
that index, not an unrelated counter. BETWEEN has empty geometry and no frames.
Starting a slice atomically pushes the diagonal, appends root ENTER, and enters
ACTIVE. Finishing its root atomically pops the diagonal and enters BETWEEN at
the next index. Empty declared slice subsets are permitted and immediately
exhausted; the declaration itself is part of identity.

A node frame has phase, incoming batch (empty only for root), incoming origin
cursor, chosen-row metadata/domain digest where applicable, next cursor,
pending batch where applicable, close reason for DONE, and leaf digest where applicable:

| Phase | Meaning and next transition |
| --- | --- |
| ENTER | Complete selected prefix exists; node is not counted. If quota permits, increment nodes once and enter COUNTED atomically. |
| COUNTED | Node has been counted; deterministic leaf/prune/domain work is unfinished. Interrupted scratch scans are discarded. Reentry cannot recount the node. |
| READY | Full deterministic row/domain metadata and next cursor exist; parent geometry is unchanged. END becomes DONE. Otherwise select that cursor's batch and enter PENDING without advancing. |
| PENDING | Candidate and origin cursor are recorded; geometry is still the parent prefix. Apply the whole batch transactionally. |
| WAITING | The parent cursor has advanced once and there is exactly one consistent child frame above it. Only the child may run. |
| LEAF | A full candidate was counted once and has a deterministic mathematical event digest; delivery/ack is pending. |
| DONE | This node is fully explored. Pop its complete incoming batch and frame atomically, return its parent to READY, or finish the slice for a root. |

PENDING rejection atomically increments committed batch/rejection counters,
advances the cursor once, clears pending data and becomes READY. Acceptance
atomically increments committed batch counters, computes successor, changes
parent to WAITING, and appends child ENTER with the full incoming batch and
origin cursor. If an operation stops before this commit, rollback the whole
batch and retain PENDING. No checkpoint is taken mid-push, mid-pop, mid-probe,
or between parent advance and child append. Before any destructive transition,
prepare bounded metadata/successor so cancellation/allocation failure can leave
the old frontier coherent. DONE records why it closed: exhausted (retain its
END cursor/domain), a named sound prune, target-nonleaf, or acknowledged tiny
census leaf (retain leaf digest). Those reasons have disjoint canonical layouts. An unexpected consistency error invalidates the
stage; it is never converted into an exhausted node.

A WAITING frame is valid only if its immediate child names the batch at the
child's origin cursor and its saved next cursor is exactly successor(origin).
The child's incoming batch is part of geometry until that child is popped.
Only the top frame may be ENTER/COUNTED/READY/PENDING/LEAF/DONE; every lower
frame must be WAITING. Root has no incoming batch/origin. The selected path is
reconstructed from the diagonal and each nonroot incoming batch; no independent
selected-ID list is trusted. Depth increases by one per nonempty batch, and
selected_four increases by one or two, so the stated bound is sound.

## 5. Leaves, counters and stopping

Production leaf mode is `first-verified-event`: dual-check the exact candidate
and enter LEAF before delivery. Mathematical digest binds family, n, ordered
orbit-map digest and sorted selected orbit IDs; it excludes time/node/order.
An explicit ack naming that digest changes outer phase to FOUND and retains
its reconstructible leaf path. Duplicate delivery/ack is idempotent; FOUND
resume returns the same terminal event and enters no nodes. Durable witness
publication and host acceptance are separate future wrapper responsibilities;
a LEAF or FOUND core object alone is not an accepted experiment witness.
A separate identity-bound `tiny-census` mode (n3/5/7 only) acks a leaf to DONE
for uniqueness tests. No production witness ledger is introduced.

`nodes_before` is the accepted parent's cumulative count, `new_nodes` counts
ENTER->COUNTED transitions this invocation, and `nodes_total` is their sum.
Restore never increments these counters. A one-node quota may stop with an
uncounted ENTER child; the quota is checked before counting it. Leaves count
once when COUNTED->LEAF commits, not on event delivery. Committed batch attempts
count once per PENDING outcome; a transaction aborted before commit remains
pending and does not increment that logical counter.

Operational counters separately record this invocation's domain probes,
physical batch/point work including aborted attempts, cursor work, restore
probes/geometry updates, and interrupted scans. These are actual work, not
search nodes. Recomputed READY/ancestor domains charge operational work but
cannot change logical node/prune/leaf/batch counters. Logical cumulative prune,
leaf and committed batch totals are uint64 and overflow is a fatal stop.
Operational stage counters and elapsed wall time describe only this process;
rejected/discarded stages must not be silently added to an accepted search
chain's logical totals or hidden from its experiment receipts.

A common monotonic deadline/cancellation predicate is established before load,
and checked before every orbit probe, pair-cursor advance, frame transition,
restore step, bounded I/O chunk and geometry point/secant loop. A timeout during
restoration discards the entire private provisional core: never expose/adopt a
partial replay and never emit a child frontier from it. The accepted parent
remains authoritative. Hashing/source checks/replay/publication time and RSS
all belong to the future stage resource gate; node quotas do not exempt them.
Cancellation is latched during mutation: an interrupted push first completes
rollback; a pop/rollback finishes its bounded inverse before acknowledging the
stop. Inverse cleanup cannot itself throw a cancellation exception halfway.
A hard kill may prevent that RAM cleanup but cannot alter an immutable parent.
Cooperative checks are not a hard process time/RSS bound; that requires the
separately reviewed unchanged owned-process wrapper.

## 6. Canonical binary envelope and source identity

No JSON/pickle/eval is used. V1 begins with 8-byte magic `NQRBCK01`, uint16
schema version, uint32 exact total wire length, and 32-byte SHA-256 of the
remaining payload; integers are unsigned big-endian. Payload has exactly a
512-byte identity, 32-byte parent-content hash (all-zero only for genesis),
32-byte chain ID, fixed control/counter header, exact-length permutation
sections, and frame_count fixed 96-byte frames. Reserved/padding bytes must
be zero. Each phase has one exact allowed field layout; all inactive fields
are zero, and tags/lengths/trailing bytes outside v1 are rejected. Exact offsets are specified below; golden-byte fixtures will be included in
codec review before adoption.
The 4KiB identity cap is a future envelope ceiling, not an extension mechanism
within v1: a different identity length requires a new reviewed schema.

The fixed identity binds n,m,target,family version, adapter kind, leaf mode,
batch/MRV/prune/point-order versions, ordered orbit-map digest, combined
permutation/declaration digest and exactly seven SHA-256 source slots:
core, state adapter, cursor, checkpoint, model, verifier and line-model source.
Source slot names/order are fixed by schema; no names/paths come from a file.
At import/initialization, bind executing modules to their source digests;
before load/save/adoption recompute from trusted local source paths and require
that they match those executing identities, then verify the ordered model. Changes require a new reviewed frontier derivation;
there is no migration or hash-repair fallback. Direct geometry requires no
CNF hash. The schema source itself is bound through the checkpoint slot.

Permutations contain exactly m² four-orbit IDs, n row IDs and a bounded declared
ordered subset of the m diagonal IDs with no duplicates. Their byte lengths
are checked from n and the declared diagonal count before constructing lists.
The full four/row permutations must be bijections of their exact domains.
Store arrays once; do not duplicate them inside every frame or manifest.
Each frame encodes phase/incoming count/IDs, origin cursor, chosen row+deficit,
domain length+digest, next cursor, pending count/IDs and leaf digest in 96 bytes.
No selected path, geometry counters, domains or resource-monitor state are
serialized as independent authorities. The tiny mode tag cannot masquerade as
a production adapter or change on resume.

### Exact v1 offsets and canonical field layouts

Every offset below is zero-based; multi-byte integers are unsigned big-endian.
Raw digest/chain/source slots are exactly 32 bytes, not hex text. All reserved
bytes are zero and all enums outside those listed are rejected. Binary integer
fields cannot represent booleans/floats/negative values; construction APIs
reject those Python types before encoding. No implicit defaults are decoded.

| Envelope offset | Bytes | Field |
| --- | ---: | --- |
| 0 | 8 | ASCII magic NQRBCK01 |
| 8 | 2 | schema=1 |
| 10 | 4 | exact total length, including 46-byte envelope |
| 14 | 32 | SHA-256(payload bytes starting at46) |
| 46 | remainder | payload |

| Identity offset (payload+0) | Bytes | Field |
| --- | ---: | --- |
| 0 | 2 | identity_version=1 |
| 2 | 2 | n |
| 4 | 2 | m=(n-1)/2 |
| 6 | 2 | point_target=2n |
| 8 | 1 | family=1 (near-quarter main-diagonal pair) |
| 9 | 1 | adapter:1 frozen-tiny,2 separate-packed |
| 10 | 1 | leaf_mode:1 first-verified-event,2 tiny-census |
| 11 | 1 | batch_policy=1 |
| 12 | 1 | MRV_policy=1 |
| 13 | 1 | prune_policy=1 |
| 14 | 1 | point_order=1 (frozen map tuple order) |
| 15 | 1 | reserved |
| 16 | 32 | ordered orbit-map digest |
| 48 | 32 | permutation/declaration digest |
| 80,112,144,176,208,240,272 | 32 each | source digests:core,state,cursor,checkpoint,model,verifier,line-model |
| 304 | 208 | reserved |

Adapter1 requires n3/5/7; tiny-census requires adapter1. Adapter2 is a separately
reviewed implementation, not an alias that instantiates frozen tiny state on a
larger grid. Policy1 digests use SHA-256 with distinct ASCII prefixes terminated
by NUL: NQRB-MAP-v1, NQRB-PERMS-v1, NQRB-DOMAIN-v1 and NQRB-LEAF-v1. Map bytes
are n:u16 followed by orbit_count:u16, then for each model orbit in exact ID
order point_count:u8 followed by (x:u16,y:u16) per ordered point. Perm bytes are
n:u16, diagonal_count:u16, all diagonal IDs:u16, all four-orbit IDs:u16, all row
IDs:u16. Domain bytes are n:u16,row:u16,deficit:u8,r:u16,length:u16 followed by
(ID:u16,weight:u8) entries. Leaf bytes are family:u8,n:u16,map_digest:32,
selected_count:u16,sorted IDs:u16; exactly m+1 IDs are required. The prefix is
prepended to each stated sequence. No Python repr/native-endian encoding enters
these identities. Manifest permutation digest includes the ordered subset
rather than assuming all diagonal pairs were declared.

| Payload offset | Bytes | Field |
| --- | ---: | --- |
| 0 | 512 | identity above |
| 512 | 32 | parent content hash; zero only for genesis |
| 544 | 32 | nonzero chain ID |
| 576 | 128 | control below |
| 704 | 2d | declared diagonal IDs in slice order |
| 704+2d | 2m² | four-orbit permutation |
| 704+2d+2m² | 2n | row permutation |
| 704+2(d+m²+n) | 96f | frames, root to top |

Here d=control.diagonal_count and f=control.frame_count. No other section or
trailing byte exists. The total must equal
46+704+2(d+m²+n)+96f, <=7,868 bytes at n79/d39/f40, as well as satisfying the
1MiB outer cap. Validate n/m/counts first, then this exact length, before any
count-dependent section decoding or grid/frame allocation.

| Control offset (payload+576) | Bytes | Field |
| --- | ---: | --- |
| 0 | 1 | outer:1 BETWEEN,2 ACTIVE,3 EXHAUSTED,4 FOUND |
| 1 | 1 | reserved |
| 2 | 2 | slice_index |
| 4 | 2 | d:diagonal_count,0..m |
| 6 | 2 | four_count, exactly m² |
| 8 | 2 | row_count, exactly n |
| 10 | 2 | f:frame_count,0..m+1 |
| 12 | 8 | cumulative nodes |
| 20 | 8 | cumulative leaf visits |
| 28 | 8 | cumulative committed batch attempts |
| 36 | 8 | cumulative rejected batches, <=attempts |
| 44 | 8 | cumulative orbit-shortfall prunes |
| 52 | 8 | cumulative row-shortfall prunes |
| 60 | 8 | cumulative target-nonleaf closures |
| 68 | 60 | reserved |

BETWEEN requires slice_index<d and f=0. ACTIVE requires slice_index<d and f>=1.
EXHAUSTED requires slice_index=d and f=0. A zero-slice genesis is EXHAUSTED.
FOUND requires first-verified-event mode, slice_index<d, f>=1, exactly LEAF at
the top and WAITING below. FOUND keeps the same leaf path/digest as ACTIVE LEAF;
outer FOUND is its durable core ack marker. Repeated ack must match that digest.
No separate mutable acknowledgment flag or selected-path list exists.

Cursor enum is NONE=0,SINGLE=1,PAIR=2,END=3. NONE/END require i=j=0. NONE is
allowed only in inactive fields. SINGLE requires 0<=i<domain_length,j=0 and a
weight equal to deficit. PAIR requires deficit2,r>=2,0<=i<j<domain_length and
both weights1. An origin must be SINGLE/PAIR for nonroot, NONE for root; END
can only be a next cursor. FIRST/SUCCESSOR return canonical cursors only.

| Frame offset | Bytes | Field |
| --- | ---: | --- |
| 0 | 1 | phase:1 ENTER,2 COUNTED,3 READY,4 PENDING,5 WAITING,6 LEAF,7 DONE |
| 1 | 1 | incoming_count,0 root else1/2 |
| 2,4 | 2 each | incoming IDs; unused slot zero |
| 6 | 1 | incoming-origin cursor kind |
| 7,9 | 2 each | origin i,j |
| 11 | 2 | chosen_row |
| 13 | 1 | deficit |
| 14 | 2 | domain_length |
| 16 | 32 | domain digest |
| 48 | 1 | next cursor kind |
| 49,51 | 2 each | next i,j |
| 53 | 1 | pending_count,0/1/2 |
| 54,56 | 2 each | pending IDs; unused slot zero |
| 58 | 32 | leaf digest |
| 90 | 1 | close_reason; zero except DONE |
| 91 | 5 | reserved |

Every frame always retains its incoming fields (bytes1..10). ENTER/COUNTED
zero bytes11..95. READY retains row/deficit/domain/next (bytes11..52) and zeros
53..95. PENDING retains the same plus its nonempty pending batch (53..57),
zeroing58..95; pending batch must equal next cursor and geometry is unchanged.
WAITING retains exactly READY fields; its next may be END, and its child's
origin/incoming fields identify the already consumed batch. LEAF zeros11..57,
retains58..89 leaf digest, and zeros90..95. Row0 is valid when its phase/layout
activates chosen_row; zero is not a standalone row sentinel.

DONE close_reason is 1 exhausted,2 orbit-shortfall,3 row-shortfall,
4 target-nonleaf,5 acknowledged-tiny-leaf. Reason1 retains row/deficit/domain
and END next, zeroing pending/leaf. Reasons2/4 zero all bytes11..89. Reason3
retains chosen_row+deficit only (11..13), zeroing14..89; it names the first
underfilled row in declared row order whose optimistic bound fails, and replay
checks that exact witness. Reason5 requires tiny-census mode and keeps only
its leaf digest (58..89), zeroing11..57. All DONE layouts keep reason at90 and
zero91..95. Reconstruct/recheck reason1's END domain, reason2's count, reason3's
row bound, reason4's exact target/nonleaf, or reason5's full leaf/digest before
adoption. A COUNTED->DONE transition increments its named closure counter
exactly once. A drained node closing by reason1 increments no prune counter.

## 7. Strict load/replay and commit protocol

`load(path, *, trusted_record, expected_identity, deadline, cancel)` requires
a trusted record containing exactly `content_sha256` (32 raw bytes),
`parent_content_sha256` (32 raw bytes), and `chain_id` (32 raw nonzero bytes)
from the accepted supervisor record. Its SHA-256 hex transport, if used by a
caller, is decoded strictly to these fixed-width fields before this API. Check record field types, exact lengths and nonzero content/chain values
before opening the checkpoint. Open a no-follow regular file, reject stat size
above the wire cap (and undersized header), read bounded chunks with deadline
checks and reject extra bytes/size change. Compute external SHA on raw bytes
and compare **before parsing any declared field**. Internal payload checksum
is only an extra corruption check; possession of a self-consistent file is
not external frontier authority. Parent hash/chain ID must also match the
trusted expected record; the caller cannot omit these checks for continuation.

Only then parse bounded fixed fields, validate lengths/enum/zero padding and
all identities, then privately reconstruct. Rebuild the diagonal and successive
incoming batches from empty geometry. At each ancestor reconstruct the complete
deterministic domain and verify row/deficit/domain digest, cursor validity,
child membership, exact row fill and parent-child successor relation. Recheck
recorded leaf/prune/terminal conditions, path/depth/type bounds, top phase and
outer/slice relation. READY/PENDING/WAITING must not actually be a leaf or a
sound-pruned node. COUNTED has no trusted unfinished scratch. Historical
counters are trusted only through external accepted provenance; replay cannot
re-prove past exhausted subtrees from a compact frontier. This is a resumable
DFS record, not an independently checkable UNSAT proof.

Adopt the reconstructed core only after every check and the final deadline
check succeeds. Errors/timeout return an explicit load failure and no partial
core. A failed restore cannot advance the accepted frontier or be described as
an exhausted slice. Restore has no implicit larger budget/retry path.

`save_candidate` first validates one coherent in-memory frontier and serializes
it within cap under the matching chain lease and expected accepted-parent hash.
Write an exclusive same-directory temporary file with bounded chunks, fsync it,
then install at `<raw-content-sha256>.nqrb` with no overwrite (hard-link commit).
If that name exists, require exact bounded bytes/hash equality; never replace
it. Fsync the directory, remove the owned temporary name, and fsync as needed.
Publication failure may leave a harmless orphan immutable blob or temp file,
never an advanced accepted parent. A report is written/fsynced to an exclusive
temporary then installed without overwrite at its stage-unique destination
using the same link-and-equality rule, with its directory fsynced; it names chain, exact parent and candidate content hashes.
Report publication occurs after durable checkpoint install. The future
supervisor alone checks report/receipt/hash/source/resource/cleanup agreement
and advances its accepted pointer atomically while owning the chain lease.
The codec provides no helper that advances acceptance before those checks.

A repeated delivery of the same accepted content/stage ID is idempotent; a
candidate with a stale parent cannot be newly accepted. A report or checkpoint
from a failed resource/cleanup gate remains unaccepted even if its bytes are
valid. No checkpoint replaces its immutable parent. Faults after each write,
fsync, link and report-rename point must preserve these claims.

## 8. Duplicate-free argument and implementation gates

For a valid full extension F, the deterministic chosen row has exactly one set
of remaining contributors from F filling its deficit. It is one generated
singleton or unordered weight-one pair, and joint insertion succeeds because
it is a subset of F. Every other batch excludes F. Induction gives one path to
each F in its unique diagonal slice. At the first divergence both different
batches fill the same row; a common future set would contain their union and
overfill that row. Distinct valid paths cannot merge. Restoring exactly the
same domain/cursor and committing the parent cursor with the child preserves
that uniqueness across checkpoints. No global ID ordering/cache is needed.

After Reviewer design approval, implement and review small components in order:

1. Bounded cursor and strict fixed-format identity/codec with malformed-input,
   canonical order, external-hash-before-parse, n79-boundary arithmetic and
   rejection-above-79 tests. Boundary arithmetic does not instantiate a grid.
2. Iterative core with frozen tiny adapter; compare complete n3/5/7 full sets,
   logical nodes and leaf multiplicities with independent tiny references and
   abstract quota fixtures, using forward/reverse declarations/permutations.
3. Roundtrip every reachable tiny phase, including PENDING, WAITING/ENTER,
   LEAF repeated delivery/ack, DONE and between slices. Test uninterrupted
   versus arbitrary one-node stages, pair boundaries, repeated COUNTED scans,
   timeout/cancellation during replay/cursor/push/pop and no partial adoption.
4. Source/order/parent/chain/cursor/child/batch/counter corruption, terminal
   resume, writer collision/stale lease, and every publication fault boundary.
   External-hash changes alone never bypass full structural replay validation.
5. Review the separate production state adapter's strong transactional and
   cancellation behavior before integrating it. Actual-host wrapper/gates and
   n79 numerical execution remain separate Lead-scheduled work.

This design does not turn tiny census results into an n79 completeness or
resource claim. The existing full-CNF branch remains stopped.
