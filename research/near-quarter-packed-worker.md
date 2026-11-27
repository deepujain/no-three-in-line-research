# Standalone packed worker and acceptance protocol

Implementation awaiting independent source review; no actual-host allocation.
Implementation model `gpt-6.1-sol`, reasoning `high`. Scope is the approved
worker/receipt design414623cb, with the declaration arithmetic correction below.
The separate reflection implementation and shared CLI are unchanged.

## Frozen files

| File | SHA-256 |
| --- | --- |
| `research/near_quarter_packed_worker.py` | `7f8c8a166d4e79f881a644b69b6f0bb0c949ef524c97eb792f81b09c0e835738` |
| `research/near_quarter_rowbatch_checkpoint.py` | `ac57fd572e85d0653efc72b9cda73bc8274a96f154d37150ec3e6419c27c4770` |
| `tests/test_near_quarter_packed_worker.py` | `128f24be6d156e5892e5855e6e29243cfcd12c640256c9dc02c51a8dbc9cfce3` |
| `data/near-quarter-packed-worker-tiny-evidence.json` | `1c8bc5133f00407ef91beef586bf6e24befc390938f953e71f90198be9b90b37` |

Core27beb803, state860711b8, cursor738a545a, both frozen verifiers/model sources,
and helperc119b58f remain unchanged. The codec change intentionally changes the
source identity of newly derived checkpoints. Existing source-bound files are
preserved and cannot be relabeled or silently migrated.

## Execution and acceptance

`python3 -m research.near_quarter_packed_worker --request REQUEST` from the
repository root executes one explicit request. Its exact canonical JSON keys
are chain_dir,stage_id,operation,n,declaration_b64,expected_map_json_sha256,
expected_parent,max_new_nodes,seconds,rss_mib. `_guard` is an internal Python
unit-test seam, never a request/CLI field. Production uses only the unchanged
owned-process helper, without a copied process monitor or another scheduler.

Construct performs no step/run. Root performs exactly the first diagonal push
and leaves root ENTER, without node count/domain/MRV. Stage has an explicit
1..10000 node quota, mode1 only, and no automatic continuation. The arithmetic
`declaration` builder does not create grid geometry. The caller supplies the
approved historical ordered-JSON map identity; the frozen oracle and packed
map order are compared inside the child interval before publication.

The supervisor creates a mode0700 chain/stage subtree. It continuously owns the
same nonce/device/inode-bound lease through child cleanup, receipt and accepted
HEAD coordination. The child borrows a read-only descriptor; it cannot acquire
or release/unlink the owner's lease. Borrow close only closes its descriptor.
Every candidate/publication write checks lease authority. Changed/truncated
records or replacement inodes fail closed. Unknown/failed cleanup retains the
on-disk lease. There is no stale-lease stealing or automatic retry.

Strict canonical byte-bounded JSON rejects duplicates, nonfinite values, extra
keys, excessive nesting and bool-as-integer fields. Source paths/nine slots are
fixed; reads are bounded/O_NOFOLLOW/regular-file checked. The parent validates
its previous accepted receipt, including all nine source hashes, before resume.
A changed worker/helper requires a fresh source-bound derivation even if the
seven core checkpoint source slots still match. The job's raw SHA is passed to
the child out of band. Child and parent check current source identity around
the operation; the worker also captures its executing file identity at import.

Full geometry reconstruction/save validation and both independent integer
verifiers run only in the child. A canonical immutable witness must finish its
file/directory durability protocol before exact leaf acknowledgment. Candidate
installation precedes the stage report. Orphan files cannot consume the parent.
The supervisor does only bounded structural/hash/counter/point-shape checks;
this is trusted source-bound execution, not a geometric proof certificate.

An immutable receipt records an eligible proposal or rejection. Its last
eligibility check explicitly handles cancellation and the precommit deadline.
Only a later same-directory atomic accepted.json replacement plus directory
fsync commits acceptance. Failures before replacement preserve the old HEAD;
uncertainty once replacement is attempted yields acceptance_uncertain and
retains the lease for explicit reconciliation. A committed identical stage is
recognized before launch. Different duplicate stage requests and stale parents
fail without a new worker.

SIGTERM/SIGINT handlers set flags only. Packed budget stops do not bypass the
save budget; inverse cleanup remains the unchanged core's responsibility.
Failed private restore reports unknown physical counters as null/incomplete.
Successful physical work is checked uint64 state_total,restore_subset,
traversal,validation_extra,physical_total with disjoint/sum relations.

## Resource and timing scope

The actual helper is unchanged: sampled guard-parent plus owned group and
observed descendants, native heap included; cleanup included in wall gate;
possible sampling overshoot; transient ps excluded. It is neither a hard OS
memory limit nor proof that an unobserved detached descendant cannot exist.
No helper invocation or process snapshot ran for this implementation package.

Invocation setup/postprocessing are separately measured outside helper RSS
sampling. Absolute worker deadline reserves at least2s before the <=30s
precommit eligibility deadline. Immutable receipts stop at the explicit
precommit cutoff. Later receipt/HEAD fsync coordination has no hard end-to-end
30s I/O guarantee. The returned summary measures through durable HEAD outcome
and lease close/release; return serialization/caller receipt writing follow.

## Declaration bound correction

The approved design414623cb stated3278 decoded bytes/4372 base64 characters.
That omitted the4 bytes for n and diagonal-count in permutation_bytes. At n79,
2*(2+39+1521+79)=3282 bytes and4*ceil(3282/3)=4376 base64 characters.
Root authorized the routine correction; the independent reviewer was notified.
The original approved design is preserved as historical evidence.

The checkpoint wire maximum stays7868:46+704+2*(39+1521+79)+96*40.
The counts/header occupy the existing fixed control section there; no extra
four bytes are missing. The n79 test constructs declaration bytes only, never
orbits, blockers, geometry or a search state.

## Tiny/fault evidence

The source-bound evidence records46 passing tests in7.802s, below the unchanged
10s command ceiling:23 new worker/lease tests plus23 existing checkpoint/state/
core tests. Actual geometry is n3/n5/n7 only. The fake guard runs the private
worker synchronously and supplies synthetic helper measurements; those values
are explicitly not host RSS/process-ownership evidence.

Checks include construct/root zero nodes at all tiny sizes, empty declaration
constructor, n3 one-node resume to the sole witness, same-stage idempotence
before launch, terminal redelivery without node recount, and n5/n7 declared
exhaustion with5/11 nodes. Physical arithmetic and uint64 overflow are checked.
Faults cover strict job/report/witness/log bounds, source change before/after
child execution, raw job SHA mismatch, changed candidate/witness bytes,
missing report, cleanup/RSS/monitor/no-sample rejection, late cancellation,
precommit expiry, worker budget stop without a new save, failed private restore
with unknown work, orphan witness before acknowledgment, immutable publication
boundaries, original-inode ownership checks, borrowed release refusal, close/
write failure, and before/after HEAD replacement/directory-fsync uncertainty.

No n9/n71/n79 geometry, broad-grid search, host ps, Solver/CNF import, scheduler,
cap increase or retry of a stopped branch occurred. Independent source review
is required next; Root alone schedules separately guarded host gates afterward.

## Independent review corrections

Review of initial worker53e83500 found two blocking failure-path issues. The
corrected worker retains the lease before entering HEAD coordination, so even
errors in final temp cleanup cannot release ownership after an uncertain
replacement attempt. It conservatively also retains on pre-replace commit
failures. A separate physical_complete flag stays false throughout save, so
an interrupted private validation clone cannot report unknown work as exact
zero. Regression tests inject replace-plus-temp-unlink failure and stop a private
save replay after positive work. Mathematician independently reran both in0.041s
and closed both findings. These remain tiny/mock-helper checks, with no host
allocation or broad-grid work.
