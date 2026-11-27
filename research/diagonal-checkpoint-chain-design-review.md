# Independent bounded-chain design review

The proposal `research/diagonal-checkpoint-chain-proposal.md`, SHA
`f5bb2e7d0dc72a4fe5d77eeb1c4298bc0f8756140edd7f1e8d86d9ed77e4c3ed`,
is approved for implementation under the supervisor's selected policy below.
This is design approval only. Exact source review and actual-host tiny tests
are required before any chain run. Reviewer: Mathematical Reviewer,
`gpt-6-astra`, high. No numerical task was run for this review.

The accepted design uses one nonresettable monotonic ceiling of 900 seconds,
at most 26 reservations of 32 seconds, a requirement for 32 seconds remaining
before the 840-second launch-window endpoint, and a final 60 seconds reserved
for cleanup/accounting. Every individual owned-helper interval remains at most
30 seconds and 256 MiB. Reservations are not reclaimed from missing receipts,
and validation/publication time counts toward the same chain clock. These are
operational bounds, not a hard guarantee against delayed filesystem calls or
an uninterruptible process.

The chain owns a separate advisory lock and calls the frozen guard directly;
it must not wrap that guard in an incompatible nested process-group helper.
Each transition uses only an independently trusted initial digest or the
immediately preceding fully accepted digest, with exact source/configuration,
receipt, predecessor and counter checks. Node delta must equal nodes_this_run
and remain within the allocation; witness deltas and per-slice sums must be
consistent. A published but unaccepted checkpoint is never automatically
adopted. Timeout continuation is an explicit policy, defaulting to stop.

The supervisor selected permanent runner refusal to resume a chain after a
crash, missing receipt, rejected receipt or unverifiable cleanup. A separate
fresh root process/ownership audit and explicit new allocation are required
before any replacement. This resolves the lack of a durable early child PID
receipt without extending the frozen helper. A hard-killed guard can leave a
worker in a separate session, so process emptiness must not be inferred from
the guard's death. Graceful SIGTERM and bounded cleanup precede hard kill.

Witness stopping is at the first completed invocation reporting a positive
witness-visit delta or any witness file; no subsequent invocation may launch.
The frozen guard may finish additional nodes within that invocation. Requiring
an immediate stop at the first witness node would change its semantics and is
not part of this approval. Every saved witness must pass both geometry checks,
point-count and reflection checks. Positive witness delta with no saved witness
is a validation failure. Unique hash-filename order is not traversal order;
tiny tests should establish the reference traversal prefix through the
accepted invocation frontier using counts or explicit test instrumentation.

The required tiny tests cover budgeting, exact accepted transitions, source
and receipt tampering, witness/timeout stop policy, lock contention,
cancellation between/during guard calls, child cleanup failures, and crashes
around promotion/ledger publication. Successful design review alone provides
no search coverage, witness, exhaustion, or unrestricted infeasibility result.
