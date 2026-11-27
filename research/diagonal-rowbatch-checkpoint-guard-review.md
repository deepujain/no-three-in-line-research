# Independent reflection row-batch checkpoint guard review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Source approved for
actual-host tiny validation only. No n79 execution, dispatcher integration or
automatic chain is approved by this source review. No such run was performed
by the reviewer.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_rowbatch_checkpoint_guard.py` | `9b84eb89e009d32a2daa3cdfa6b3b5df9d63daa48ff2565c6f4572a682fb5d2f` |
| `tests/test_diagonal_rowbatch_checkpoint_guard.py` | `4ca51bf0694ab845f1baa64171db3e2061d331d89d9e67e667216c85936bc117` |
| Approved batch core | `b162073f64d8190e7f97e6a06c96f2f7607b1419bce9e01a0f73c572d346f289` |
| Owned-process helper | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |
| Unchanged shared dispatcher | `435d902f50d756b2ee3d40866b9bf814ca7aa8c3a66bcb59cacd8a42d4128784` |

The full source and its diff from the frozen single-orbit checkpoint guard were
reviewed. Changes bind the new core, tiny reference and checkpoint utilities,
use the new schema/branch identity, enforce n2..79, bound checkpoint reads to
1,000,001 bytes with rejection above 1,000,000, and handle unchanged-frontier
reconstruction timeout explicitly. The owned helper and its caps remain unchanged.

The parent exclusively locks the checkpoint and requires an external digest on
resume. It writes an incomplete receipt before launch, stages the old checkpoint
in a private directory, and launches the fixed worker with source bindings.
Each call permits at most 30 seconds and 256 MiB sampled RSS, with a cooperative
worker reserve for publication/cleanup. Real process-start and explicit-call
clock semantics match the reviewed standalone guard. These are sampled and
cooperative gates, not hard guarantees against transient overshoot or blocked
filesystem work.

Only a normal, clean helper exit with matching source, worker result, staged
hash, exact family/order/configuration identity, counters and predecessor can
promote the frontier. The original checkpoint is rechecked before promotion.
Complete status additionally requires terminal slice index and empty frames.
Other helper/cancellation/time/source outcomes retain no accepted checkpoint.
After promotion and after final report writing, late failure clears acceptance
and preserves a separate published hash for audit. An exception after replacement
can leave a new file with an incomplete receipt; that is unknown/unaccepted
state requiring explicit recovery review, not automatic adoption.

The core's special resume reconstruction timeout can return the unchanged old
hash and zero nodes. The guard recognizes that exact staged-byte case and
returns `reconstruction_timeout`, with no promotion or accepted digest. It
therefore does not claim that an old predecessor field represents a new child.

The worker dual-verifies each certificate and its point count, checks source
stability, and atomically saves a normalized-hash-named file with guard source
metadata before core frontier progress. Each invocation has a fresh witness
directory. A witness may remain valid and saved even when the invocation's
frontier is rejected. File fsync/replace does not establish directory-fsync
power-loss durability; the same limitation applies to checkpoint/report writes.
The helper's bounded cleanup and advisory lock semantics remain as previously
reviewed; a crash or hard kill is not proof that workers are absent.

All fifteen guard/core/tiny-reference tests independently passed in 3.528 s,
and the final source hashes match the table. The helper is mocked in these tests
while real tiny workers execute. They cover n3/n5 staged continuation and dual
certificates, unchanged reconstruction timeout, bounded input, all major helper
failure statuses, lock/hash rejection, SIGTERM propagation, identity tampering,
pre/post-promotion exceptions, and late source/cancel/deadline/report failures.
The core/reference tests additionally cover uniqueness and exact staged counts.

Actual tiny host gates must still establish sampled owned-process success,
multi-invocation continuation, witness publication and cancellation with clean
cleanup. Any shared-dispatcher route requires its own source/clock review.

## Isolated shared-dispatcher route approval

The later combined dispatcher is
`da18b0ac8e7fbd59583fd551bf17eca141fba0b94e60d07ff624b84b884cb2ee`;
the guard remains `9b84eb89...`. Updated guard tests are
`0e546dd38a41a8aea655f233396b4319fc73e1c332253c5c92f34c91736c2fae`.
Removing exactly the five newly added row-batch routing lines from the current
source recovers the complete previous dispatcher hash `435d902f...`; all prior
routes therefore retain their exact code. The new selector forwards only to
the new guard after removing its selector flag.

All nine updated guard tests independently passed in 3.735 s, including actual
tiny CLI subprocesses for initial/resumed n3/n5 runs with the helper mocked.
Separate reviewer-only mocks verified that a real CLI forwards `_PROCESS_STARTED`
while an explicit API argument list gets a fresh monotonic start. The route is
approved for the supervisor's actual tiny host gates. No real host lifecycle
or n79 numerical claim follows from this source/dispatch approval.
