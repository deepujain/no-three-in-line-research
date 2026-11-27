# Standalone packed worker, owned guard and acceptance receipt

Status: design only, following approved packed integration core27beb803 and
codecd5001ad5. No guard/worker/CLI source or grid geometry is created here.
Model setting: `gpt-6.1-sol`, reasoning `high`. Frozen reflection work is separate.

## Files and closed operations

Add one `research/near_quarter_packed_worker.py` containing the standalone
supervisor and its private worker entrypoint, plus one focused test file.
Use only the unchanged `research/owned_process_guard.py`, SHA
c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48,
for launch/ownership/RSS/wall/cleanup. Do not copy its monitor or signal loop,
introduce a scheduler, call a Solver or add a shared dispatcher route.

A narrow codec lease extension is needed for explicit parent-to-child borrowing;
its new source hash must be independently reviewed before any host gate. All
existing wire fields and adapter semantics remain unchanged. This intentionally
changes codec-bound source identity before creating a new guarded frontier;
previous source-bound checkpoints are preserved, not migrated or relabeled.

The only operations are:

| operation | Core activity | Permitted output |
| --- | --- | --- |
| construct | Construct/hash adapter2 only. Do not call step/run. | Empty BETWEEN or zero-slice EXHAUSTED checkpoint; nodes0; search_performed=false. |
| root | Fresh adapter2, exactly one BETWEEN->ACTIVE transition pushing its first declared diagonal, leaving root ENTER. No domain scan, counted node or run. | Root ENTER checkpoint; nodes0; search_performed=false. Requires nonempty slices. |
| stage | Fresh or accepted-parent adapter2 continuation, run with the fixed node quota and common budget, stop at first verified event or declared exhaustion. | Node-limited coherent candidate, verified-witness terminal, or declared-slice exhaustion; no global infeasibility claim. |

Construct/root are independent no-search preflights. Their jobs require fresh
chains; they cannot relabel or reset an existing search frontier. Mode stage
has max_new_nodes in1..10000 and mode1 only. The wrapper never enlarges node,
time or RSS limits or automatically schedules a continuation. Root resumption
uses an explicit accepted checkpoint, never a discovered file or newest mtime.

## Bounds, job authority and source binding

All stage directories are newly created by the supervisor with mode0700;
filenames are fixed or derived from fixed-width stage/content IDs. The child
receives only `--worker JOB_PATH EXPECTED_JOB_SHA256`, via an argument vector
and the trusted Python executable, no shell. The public standalone supervisor
entrypoint is separate from any existing shared CLI. Path controls below apply
before following any artifact supplied by a report.

Job wire is canonical strict JSON, <=16KiB before reading/parsing, depth<=5,
fixed keys only, no duplicate keys or NaN/Infinity, strict integer types (bool
is forbidden for numeric fields), UTF-8 strings bounded before use. A small
bounded depth scanner precedes JSON parsing. JSON decoding is data only.
The supervisor writes/fsyncs an exclusive immutable job and passes its raw SHA
out-of-band; worker checks raw bounded bytes before parsing declared fields.
Worker verifies before construction and again before final publication that its
executing/source digests agree with the job. Each source file read is <=1MiB,
chunked with the common deadline and no caller-selected source paths.

The exact job fields are:

- schema=1; stage_id=32 lowercase hex characters; chain_id=64 lowercase hex.
- operation in construct/root/stage; n strict odd3..79; target must equal2n;
  adapter=2; leaf_mode=1; max_new_nodes (0 for construct/root,1..10000 for stage).
- chain_dir: one supervisor-trusted absolute path <=1024 UTF-8 bytes, no symlink
  component within its newly owned stage/chain artifact subtree. Reports may
  only name constant-basename artifacts or content hashes under this directory.
- accepted_record: null only for a fresh zero-parent chain, otherwise exactly
  checkpoint_sha256, checkpoint_parent_sha256, chain_id, identity_hex (512bytes
  encoded as1024 lowerhex characters) and preceding receipt_sha256.
- declaration: n-derived exact permutation byte string, base64 <=4372 characters
  decoding to <=3278 bytes, with d<=m and exact orbit/row lengths/bijections;
  digest must match the accepted identity for resume. No extra order defaults
  are inferred on continuation. Fresh construction uses the declared bytes.
- expected_map_json_sha256:64hex. For a fresh chain this is the approved frozen
  oracle's historical ordered-map digest; for continuation it is copied from
  the accepted receipt. The first constructor gate computes the frozen oracle
  and packed map under the same child resource interval, comparing full order
  and both map encodings. No parent-side broad-grid allocation is needed.
- sources: exactly nine SHA-256 slots, fixed names/order: core,state,cursor,
  checkpoint,model,verifier,line-model,worker,owned-helper. The core's seven
  slots and literal adapter2 tag must match the checkpoint manifest. Publisher
  code lives in worker, adding no unbound utility import or old solver module.
- lease_token: owner_nonce=32raw bytes in64hex, device:uint64,inode:uint64 and
  expected_parent=64hex, matching the supervisor-owned lease described below.
- timing: invocation_started_ns, worker_deadline_ns and precommit_deadline_ns
  are positive monotonic-clock integers on this host, with strictly increasing
  deadlines and <=30s from invocation start to the precommit deadline. Worker
  deadline is earlier, reserving at least2s for cleanup/validation. The sampled
  resource gate remains the helper interval, with coordination scope below.
- limits: guard_seconds in(0,30], rss_mib in(0,256], fixed at the reviewed gate's
  parameters; child time cannot exceed its absolute job deadline. No overrides
  or fallback backend/scheduler fields exist.

For n79 the existing accepted historical map digest is
78054420e2f53dde1ea7d1d3823b220d7bf1b8e6e0edb5f05ea6210786528032
in the source-bound count record; this is an identity, not new geometry work.
The n71 fixture map digest is82c1fcb850886b2d837860512a29ec7274da5739d480bb8b07ac460e76cb019b.
Tiny constructor gates establish their approved source-bound identity records
before stage continuations. A new source/configuration requires a new reviewed
fresh derivation, not an edited accepted manifest.

## One parent-owned lease and borrowed worker access

The supervisor owns `ChainLease` continuously from accepted-record inspection
through child cleanup and acceptance commit. It compares the accepted HEAD
with the expected parent before launch while holding that lease. A child may
write immutable candidates but never create/release the owner's lease or
advance HEAD. This avoids a gap allowing concurrent acceptance from one parent.

Add narrowly scoped codec operations `borrow_for_worker` and
`close_keep_lease` to the existing literal ChainLease class, not a lock framework:

1. Owner acquisition remains existing O_CREAT|O_EXCL with96-byte nonce+chain+
   parent record and fsynced directory. Owner records dev/inode and a random
   nonce. Existing leases are never stolen or automatically repaired.
2. Borrower opens that existing file read-only with O_NOFOLLOW, verifies regular
   file, exact96bytes, expected dev/inode, nonce, chain and parent. It has a
   borrowed flag and cannot invoke owner acquisition/release or unlink. Its
   close only closes its descriptor. `save_candidate` may use the matching
   verified borrowed lease; every write still checks ownership.
3. Supervisor keeps ownership while the unchanged guard runs. A killed worker
   cannot leave a new independently owned stale lease. The owner releases only
   after the guard proves clean owned-tree cleanup, and only its original
   matching inode/nonce. Any cleanup error conservatively leaves the lease on
   disk and closes the owner's descriptor via close_keep_lease, for explicit
   supervisor diagnosis. This is not automatic stale-lock stealing.
4. With clean cleanup, the supervisor validates source/report/artifact hashes
   and expected HEAD again under that same lease, then may commit acceptance.
   No second writer can enter that chain during this interval.

SIGTERM/SIGINT handlers in the supervisor and worker only set cancellation
flags; they do not raise asynchronous exceptions during counter updates or
lease/file commits. The supervisor passes its flag to the unchanged helper.
Worker budget checks raise PackedStop; inverse cleanup completes and latched
stops propagate only after coherent frontier commits. No descendant changes
SID/PGID or daemonizes. Monitor/signaling permission failures fail the stage;
absence of a usable host ps is not treated as successful cleanup.

## Measured interval, deadlines and counters

Record invocation start before job/source/lease setup. Set one host-monotonic
precommit deadline <=30s from that start, with at least2s validation reserve,
and an earlier absolute worker deadline. Immediately before launch pass
`seconds=min(configured_guard_seconds, remaining_precommit_seconds)` to the
unchanged helper, never above30, rss<=256. The child's deadline includes its
imports, source/job checks, model construction, restore, new traversal, both
verifiers, checkpoint/witness validation, fsync and report publication.

The helper's interval measures parent+owned-tree sampled RSS and includes its
cleanup. Its possible sampling overshoot and excluded transient ps are stated
verbatim in the receipt. Parent setup/postprocessing are outside that sampled
interval: record their elapsed values and the complete invocation elapsed
separately. Reject if the precommit deadline expires before all candidate
validation/source/resource checks finish and before deciding eligibility.
Do not claim setup or final receipt/HEAD writing was inside helper RSS sampling
or turn its30s gate into a hard end-to-end I/O deadline. Fsync can block: no
promise is made that later durable coordination finishes within30s. The final
source-bound supervisor return summary measures through receipt/HEAD durability
and lease release, and the caller records it in the experiment receipt. The
immutable acceptance receipt names its precommit timing cutoff explicitly;
it cannot truthfully contain a duration measured after its own write. Summary
emission/caller receipt writing are outside that final measured cutoff. All heavy model/geometry replay and both verifiers run in the
child under the helper, not as unmeasured parent postprocessing. Parent only
reads bounded artifacts and performs hashes/strict decoding/cheap shape checks.
The receipt makes these scopes explicit rather than presenting helper time as
complete invocation time or a hard OS memory limit.

`nodes_before/new_nodes/nodes_total` retain exact core semantics. For adapter2
physical counters use checked uint64 arithmetic and report these disjoint sets:
state_total (the live state's work), restore_subset (captured at successful
private adoption), traversal=state_total-restore_subset, validation_extra
(private save-validation clones), physical_total=state_total+validation_extra.
The subset relation and every sum are checked for overflow/type failure.
Core domain counters are separately labeled, since restore_probes includes
both load reconstruction and private save-validation probes. No probe or
replay is counted as a new node. Constructor/hash/verification time is real
cost even when logical nodes are0.

A failed private restore returns no provisional core/counters. Its report marks
physical_counters_complete=false; unknown work is not reported as exact zero.
A killed worker may expose only last published lower bounds or no report.
Attempted stages remain in experiment receipts even though their work cannot
be added to the accepted chain's logical node total. No per-node progress log,
full witness ledger or unbounded counter history is kept.

## Worker execution and witness transaction

Before any expensive work, validate job/source/declaration/accepted authority,
borrow the lease and establish flag-only signals/common budget. For continuation,
read the exact parent content path with mandatory external content,parent,chain
hashes and private replay; reject mismatches rather than repairing. Construct/
root jobs have no parent and may not manufacture a resume from their snapshot.

In stage mode, let the core stop at LEAF. Decode exactly the selected orbit set,
require m four-orbits+one pair,2n distinct in-grid integer points and the exact
bound map. Run both frozen independent integer verifiers inside the child
interval; require both valid and identical normalized certificate hashes. Any
failure is fatal, with no witness or terminal claim. Canonical witness points
and orbit IDs are sorted; mathematical event digest excludes stage/time/order.

Publish a strict <=16KiB witness JSON with exactly schema,n,points,sorted orbit
IDs,family/map digest,mathematical event digest and the two successful verifier
summaries. Each summary has its fixed algorithm name,valid=true,point_count and
normalized SHA; never dump an invalid triple list. Write/fsync exclusive temp,
link to a raw-content-hash name without overwrite, compare bounded existing
bytes on collision, fsync directory. The bounded publisher lives in worker,
following the already reviewed immutable protocol, not importing old SAT code.
Only after durable witness bytes exist does the core ack that exact event,
become FOUND and install its checkpoint via save_candidate. Repeated terminal
delivery uses the same canonical artifact/event rather than recounting a leaf.

For all eligible outcomes, candidate installation and its directory fsync precede
worker-report publication. Report is a stage-unique immutable file: exclusive
write+fsync+link, equality on duplicate, directory fsync. No accepted pointer is
written by the worker. A stop during verification/publication can leave an
orphan witness/checkpoint; it cannot consume the accepted parent. After a
common deadline/cancel, do not bypass checks to save a new frontier. A small
failure report may be attempted, but it cannot make the stage eligible.

## Bounded report and receipt validation

Worker report <=16KiB, depth<=5, exact schema/keys and fixed enums; paths are
hash-derived basenames, not arbitrary paths. Error detail <=512UTF-8 bytes.
The fixed fields are schema,stage_id,job_sha,chain_id,operation,n,adapter,mode,
source_manifest,identity_sha/identity_hex,expected_parent,candidate_sha,
status,phase,node counters,completed/declared slice counts,event/witness hashes,
physical counters and completeness flags,phase elapsed values. At most one
candidate and one witness. Log writes are one bounded status/error summary,
no per-node output; log size<=64KiB and tail read<=4KiB. Larger/unparseable
report/log is a stage error, never an invitation to read/print it unboundedly.

Statuses eligible for acceptance are constructed,root_ready_no_search,
node_limit_checkpointed,slices_exhausted,verified_witness. Every eligible status
requires worker exit0 and a fully installed matching candidate. Source mismatch,
checkpoint/replay/publication/worker error,soft deadline,cancel and absent report
are ineligible. `search_complete` is true only for declared slices_exhausted,
not constructor/root/node-limit/witness. No status asserts proof-checked UNSAT.

After helper completion require gate_status=exited, returncode0, positive RSS
samples, no monitor error, clean cleanup, limits/elapsed passing, unchanged
sources and no supervisor cancellation. Read report/job/candidate/witness with
O_NOFOLLOW, regular-file and size checks before bounded chunks/parsing. Require
job/stage/chain/parent/identity/source/status/counter relations to agree. Use
codec parse's strict external hash/structure checks on the <=7868-byte v1
candidate; the child has already performed full private live/replay validation
under the gate. Verify terminal/root/constructor phase and logical count deltas.
No unmeasured parent broad-grid model/replay is performed.

For a reported witness, parent verifies raw content hash, exact bounded schema,
2n unique in-grid integer coordinates, normalized point hash, selected-ID/type
counts, expected map/event digest and both exact successful verifier summaries.
Both actual geometric algorithms already ran in the measured source-bound
child. This is trusted execution, not an independent proof certificate; any
later independent rerun is itself separately guarded/scheduled. Missing,
changed or inconsistent witness bytes forbid verified_witness acceptance.

Supervisor writes a canonical <=32KiB immutable receipt with job/report/parent/
candidate/witness hashes, the prior accepted record, full source manifest,
unchanged helper result, explicit setup/helper/postprocessing-through-precommit timings,
physical counter completeness, proposed result and rejection reasons. Source
checks are before and after child execution. The receipt's result is eligible
or rejected, not an unsupported assertion that HEAD already advanced. Failure
receipts clear accepted witness/conclusion/completion claims, while preserving
observed/orphan artifact IDs as unaccepted diagnostics. Worker completion never
overrides resource, cleanup, source or publication failure.

## Atomic accepted-parent advance

`accepted.json` is supervisor-owned, strict <=4KiB, with schema,chain ID,
checkpoint content+parent hashes,identity512hex,last stage/job/receipt hashes,
map-oracle hash and optional witness content/event hashes. Fresh state is an
explicit zero-parent/null-identity genesis, only under a newly owned chain.
Report/candidate presence alone is never authority to replace this record.

Under its still-held original lease, supervisor rechecks the exact accepted
record read before launch, durably installs the eligible receipt, then writes/
fsyncs a same-directory exclusive accepted-record temp, atomically replaces
accepted.json and fsyncs its directory. Only this completed transition advances
the chain. Prior checkpoint/receipt/witness files are immutable. The receipt
retains the prior accepted record so a torn HEAD publication cannot silently
rewrite history. If receipt succeeds but failure occurs before HEAD replacement, the receipt
remains an eligible proposal and the old accepted parent remains authoritative.
If replacement occurs but directory fsync or its outcome is uncertain, return
acceptance_uncertain, retain the owner lease on disk, and require explicit
supervisor reconciliation from the prior receipt and actual HEAD bytes. Do not
assert either durable promotion or unchanged HEAD and do not resume/retry that
chain automatically. There is no transactionally safe claim that every failure
after an atomic rename leaves the old pointer in place. Resource/source/cleanup
failures are all decided before this coordination commit and cannot authorize
its entry. An already committed same stage/job/receipt is idempotent and
must not launch a second search. Stale parent, different duplicate stage bytes
or existing different child is rejected under the lease.

## Proposed first host gates, with no search before construction/root checks

After independent wrapper/lease-extension source approval, Lead schedules fresh
n3 construct then n3 root gates, each proposed5s/256MiB and a2s earlier worker
deadline. They do no MRV or DFS and prove final source/job/borrowed-lease/report/
receipt/HEAD plumbing before a numerical stage. Next n5 construct/root exercise
zero-leaf sizing without search. Positive samples and clean cleanup are required;
no fixed sleep or relabeling rescues a worker that exits before a sample.

Then separately schedule n3 mode-stage witness and one-node resume/terminal
idempotence, bounded malformed-job/hash/source/parent/chain cases, SIGTERM during
restore/push/report, and publication/cleanup failure gates. Use isolated test
chains for negative tests. No guard-cap increase or automatic retry follows a
failed gate. The caller records the final full-invocation summary alongside the acceptance
receipt; their timing cutoffs and sampling scopes must be explicit.

Only after those gates may Lead schedule the approved n71 fixed-fixture
push/dual-check/undo and n9 modest pilot, then n79 construct and root-only
preflights (no MRV,0new nodes) under<=30s/256MiB with explicit model identities.
An n79 counted-node/MRV stage needs its own subsequent source-bound allocation
and measured evidence review. No current host/large-grid execution is authorized
by this design. Existing reflection stage scheduling and source remain untouched.
