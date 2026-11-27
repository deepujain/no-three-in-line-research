# Independent checkpoint guard and dispatcher review

Source and dispatcher approved for the supervisor's actual-host tiny gates.
Actual-host validation remains the supervisor's responsibility.
Reviewer: Mathematical Reviewer,
`gpt-6-astra`, high. No n79 construction or search was performed.

## Frozen identities

| File | SHA-256 |
| --- | --- |
| `research/diagonal_secant_checkpoint_guard.py` | `84559f6a195d3a27db6e0bae718e84d82e70e27be5826562b7004fc47680ea0e` |
| `tests/test_diagonal_secant_checkpoint_guard.py` | `4d67f03e0c062b50acd545d8cd7163e0ae7c6ee8e2081aabfbd14cc7b580c2bd` |
| `src/lazy_sat.py` | `9dc1e86ce827ca5b4534696162a5696eb07c19a3f250d4c4155324592caf1fb7` |
| `research/diagonal_secant_checkpoint.py` | `48f49f36a7f99bc3d42bc5c4376c3267c5d0f0b05ba9af27f4619403e20f6721` |
| `research/owned_process_guard.py` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

## Reviewed behavior

The guard uses the previously reviewed owned-process helper, with unchanged
maximum limits of 30 seconds and 256 MiB. A nonblocking exclusive flock covers
the checkpoint transaction for cooperating callers. An existing checkpoint
requires a trusted external byte hash; the worker receives a private staged
copy rather than the accepted file itself.

The worker checks source identities, runs the reviewed iterative DFS core,
and performs both exact geometry checks before atomically saving each witness.
The witness filename is its normalized geometry digest, and metadata binds the
seven guard sources. Witness publication precedes progress publication; replay
can repeat witness visits without losing solutions. Unique per-invocation
directories keep diagnostics separate.

Before checkpoint promotion, the parent requires a clean successful owned
worker exit, stable sources, no cancellation or expired wall gate, matching
checkpoint/result digest, exact grid/slice/source/orbit/branch-order identity,
predecessor digest, and agreeing counters. Completion additionally requires an
empty frontier after every declared slice. An existing accepted checkpoint is
reread before replacement; a new file appearing unexpectedly also fails.
The source-bound worker is trusted to perform the traversal: matching counters
and predecessor links are not independent proof of search coverage.

## Publication and rejection boundary

The initial revision retained an accepted digest when a wall, cancellation or
source failure was detected after checkpoint promotion. The revised design
separates `published_checkpoint_sha256` from `accepted_checkpoint_sha256`.
A detected late failure clears acceptance and completion, retains only the
published digest for diagnosis, and returns CLI code 2. It also checks after
temporary-directory cleanup and after the first final receipt write, rewriting
that receipt as rejected when necessary.

Before promotion, a failed invocation leaves the prior checkpoint intact.
After promotion, failure can leave new but unaccepted bytes in its place;
this is intentionally not rollback. The old expected digest then fails on
resume. Recovery requires a separate explicit trusted inspection of the new
identity, frontier and predecessor and adoption of its actual digest. A
published digest or predecessor link alone does not authorize accepting
coverage or automatically resuming rejected work. If interruption occurs
between promotion and the final receipt, the initial receipt remains
incomplete and recovery follows the same rule.

## Timing, cleanup and filesystem limits

The real CLI passes its process-start timestamp; explicit `main(argv)` calls
use a fresh timestamp. The new route is opt-in and dispatches before the
ordinary parser. Cooperative DFS time reserves the greater of one second or
one quarter of the remaining budget for checkpointing and cleanup. The owned
helper checks remaining wall time and sampled RSS including its cleanup.
The parent also checks its overall elapsed time around promotion and receipt
publication. No hard wall-clock or hard RSS cap is claimed: monitoring,
filesystem operations and the final receipt/lock-release tail are cooperative.
RSS evidence covers the helper's sampled interval, not an atomic continuous
bound across every parent finalization operation.

The owned helper's prior limitations remain: the fixed worker and descendants
must retain their spawned session/group; sampling cannot guarantee detection
of unobserved detachment; cleanup failure does not prove all processes exited.
Flock is advisory, not protection from an uncooperative writer. Atomic files
are fsynced before replacement but parent directories are not fsynced, so
power-loss durability is not established. Witness files remain independent
valid certificates even if invocation progress is rejected, subject to their
individual bytes and geometry being verified.

## Independent validation

All twelve checkpoint core/guard tests independently passed in 6.054 seconds
on the revised implementation before the final diagnostic-only correction.
After that correction, the promotion-fault and dispatch tests passed again
in 0.861 seconds; the fault test also verifies false source-stability metadata
when promotion detects changed sources. Final source/test/dispatcher hashes
were independently checked against the identities above.
They use real tiny DFS subprocesses with the resource helper mocked, and cover
n3/n5 slice/resume and CLI paths, hash and lock rejection, identity tampering,
guard failure, cancellation, interruption before/after promotion, and injected
wall/source/cancellation failures during publication. The original seven core
and fast-predicate tests also passed independently in 0.916 seconds.

These are correctness and integration checks, not actual-host resource gates.
No large frontier, n79 run, throughput estimate, coverage fraction, witness
novelty, unrestricted infeasibility or proof-checked UNSAT follows from them.

## Standalone route under the later combined dispatcher

The existing standalone checkpoint route is approved under dispatcher SHA
`435d902f50d756b2ee3d40866b9bf814ca7aa8c3a66bcb59cacd8a42d4128784`.
Removing only its new five-line opt-in chain dispatch branch exactly recovers
the previously approved dispatcher SHA
`abddf7b5c2f440de4fb1e6d82cb7c8e78fdea046ff46f759af6754cadd261b9b`.
Independent mocked checks passed for unchanged argument forwarding, the real
CLI process-start timestamp and explicit-main fresh timestamp. The chain
module is not imported on the standalone checkpoint route. This narrow
approval permits the supervisor's renewed tiny standalone gates and excludes
execution of the new chain route pending its full source and host review.
