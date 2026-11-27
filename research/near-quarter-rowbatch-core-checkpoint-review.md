# Independent tiny row-batch core and checkpoint review

Approved for the implemented hard-tiny n3/n5/n7 scope. Reviewer: Mathematical Reviewer, `gpt-6-astra`, high. No n79 geometry, construction, search, or benchmark was run. The cursor and exact wire design have separate earlier reviews.

| File | SHA-256 |
| --- | --- |
| `research/near_quarter_rowbatch_core.py` | `51a8fcde5772990be1b0de53ac8e04b30c8254dd4267e335186be8fbd84462a2` |
| `research/near_quarter_rowbatch_checkpoint.py` | `26a31dc66144745a0c3cf0f5a7976eee78e1fcc9abc8844d1c4d039d14e5bb4c` |
| `tests/test_near_quarter_rowbatch_checkpoint.py` | `e3a4d17e194d25b6e8e86a5265ef06711b77f543ed8e2a8301e0502406a2d4c0` |
| `research/near_quarter_rowbatch_cursor.py` | `738a545abc1909bc126ca916d225dfef90bea8b974142a5885cb9e2f632e2422` |
| `data/near-quarter-rowbatch-core-checkpoint-evidence.json` | `eb2d1f54a583194736bf4a1ab1dd213c77356c54ea0449e1431f41e4a0bc68ad` |
| `research/near-quarter-rowbatch-core-checkpoint.md` | `a73c85706cc0e238907560529c3a0410dd20050b0f0807bb31d0934786f5865f` |

## Transition and replay argument

The core replaces recursive traversal with immutable frame values and explicit ENTER, COUNTED, READY, PENDING, WAITING, LEAF and DONE phases. ENTER increments the node count once. COUNTED determines leaf, target closure, justified shortfall or deterministic row domain. READY records one streamed batch as PENDING without advancing the cursor. PENDING computes the successor and replacement parent/child frames before geometry mutation, then commits either an accepted whole batch and WAITING/ENTER frames or a rejection and READY successor. Successful descent fills the selected row exactly. DONE unwinds exactly the incoming batch; root completion advances the declared diagonal slice. A pending leaf is counted once, and repeat acknowledgment is idempotent in stop-on-leaf mode. Tiny enumeration mode retains an explicit acknowledged-leaf closure.

The mathematical row-batch coverage and uniqueness argument is the previously reviewed complete row-cover argument: each completion has one exact contribution to the deterministic deficient row, represented by a singleton of weight two or an unordered pair of weight-one orbits. No global orbit-ID pruning is introduced. Temporary viability probes and the orbit/row shortfall bounds match the frozen tiny state/reference. Cancellation checks occur between complete tiny geometry operations. A batch rollback removes every successfully inserted orbit when a later check/rejection or pre-mutation exception interrupts it; no stronger transaction guarantee for interruption inside a point update is claimed.

Private replay starts with a fresh state, replays the declared incoming path, recomputes deterministic domains, validates each child batch against its origin and the parent's successor, and rechecks leaf or prune justification. It returns a core only after all checks and final source stability succeed. Counted frames are not counted again. Replay cannot independently prove the already completed search history represented by cumulative counters or advanced cursors; those require accepted external provenance.

## Wire and publication contract

The implementation uses the approved fixed 46-byte envelope, 512-byte identity, 704-byte payload prefix and 96-byte frames. Checked arithmetic gives a maximum `46 + 704 + 2*(39 + 1521 + 79) + 96*40 = 7868` bytes for the v1 schema. The outer input cap is 1 MiB. Cursor coordinates are bounded indices rather than flattened pair counts. The schema can represent odd grids through 79, but the actual replay adapter and core reject geometry outside n3/n5/n7.

The trusted external content hash is checked before interpreting fields. The content/parent/chain record, full source/model/order/policy identity, exact permutation lengths, phase union, inactive/reserved bytes, frame/path relations and structural counter bounds are checked. Seven source hashes captured at import are rechecked using bounded reads. File loading refuses symlinks/nonregular files, bounds reads and checks size/mtime/inode stability. These hashes are trust bindings, not authentication against an untrusted party who controls the external expected record.

Three review findings were fixed before approval. First, a live depth-f path requires at least f-1 accepted batches, so the parser now checks `attempts - rejected >= max(0, f-1)`. Second, an active LEAF or DONE event requires a nonzero corresponding leaf/prune/target counter. Third, candidate saving now compares the fully replayed state snapshot, frames, counts, outer phase and slice index with live RAM before any write. Earlier versions could accept the two demonstrated local counter contradictions or publish encoded frames while ignoring inconsistent live geometry. Regression tests now reject all three cases. These are local coherence checks, not claims that the compact checkpoint proves historical traversal.

A candidate writer owns an exclusive nonce/inode/chain/parent lease and never steals an existing lease. Saving fully validates/replays the encoded candidate, writes an exclusive temporary file, fsyncs it, installs the content-named file through a no-overwrite hard link, fsyncs the directory, removes the temporary name and rechecks sources. An existing equal immutable candidate is idempotent; unequal content fails. Faults may leave an immutable candidate, but no accepted-frontier pointer is updated by this component. Stage reports, externally accepted-chain advancement, crash/ownership recovery and a process guard remain separate work. Cooperative checks and bounded data do not establish a hard wall or RSS limit.

## Independent verification

`.venv/bin/python -m unittest tests.test_near_quarter_rowbatch_checkpoint -v` passed all nine tests in 0.618 seconds. I read the complete core/codec and tests, checked the final changes, and verified every source hash in the saved evidence against current files.

Real n3/n5/n7 roundtrips cover all reachable phases under forward and reverse declarations, with exact frozen-reference leaves and node counts (1/0/0 complete sets, 2/5/11 nodes). Repeated one-node stages match uninterrupted final state, counters and leaf sequence. Stop-on-leaf acknowledgment remains idempotent. The explicitly synthetic quota fixture has twelve complete sets and exercises accepted pair paths and every-transition replay in both declaration orders; it makes no physical geometry claim. Pair cancellation after the first and second successful insertion, second-orbit rejection and pre-mutation second-orbit exception restore the original state. Cancellation at every checked replay boundary returns no partially adopted core. Additional tests cover external-hash ordering, parent/chain/phase corruption, active counter contradictions, corrupt rows/blockers/selection in live RAM, stale/colliding leases, immutable duplicate saves and five publication fault boundaries.

The saved method/evidence claims are consistent with this scope. Their 157-point observation correctly applies the separately reviewed half-turn one-deletion lemma only to deletion from the specified center-absent symmetric 158-point family. No 157 search path or novelty claim is added. Production geometry transactions, process lifecycle, actual-host RSS and numerical n79 performance remain untested by this review.
