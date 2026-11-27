# Independent bounded checkpoint-chain source review

Chain source and dispatcher approved for actual-host tiny validation. The
supervisor retains responsibility for host gates and any later allocation.
Reviewer: Mathematical Reviewer, `gpt-6-astra`, high. No n79 run was performed.

## Frozen identities

| File | SHA-256 |
| --- | --- |
| `research/diagonal_secant_chain.py` | `20ee2caeeb820ee1d66a7a437a01218e371179b75bcfda39458142e3c20ddd9a` |
| `tests/test_diagonal_secant_chain.py` | `4916c8790978a0f70f2c142653c35c7d5abf10d3a191d67d135506d2a23daf92` |
| `src/lazy_sat.py` | `435d902f50d756b2ee3d40866b9bf814ca7aa8c3a66bcb59cacd8a42d4128784` |

The checkpoint guard/core, fast/original core, verifier and owned-process
helper remain frozen and independently reviewed. The chain records their
identities together with its own source and actual dispatcher, and rechecks
them across transitions. A source-read OSError is treated as failed stability.

## Budget and serial execution

One process-start clock covers the real CLI chain; explicit API/main calls use
a fresh clock unless a trusted start is supplied. The aggregate maximum is
900 seconds, at most 26 reservations of 32 seconds, and no launch without 32
seconds remaining before the 840-second launch-window endpoint. A smaller
aggregate allowance shrinks that window by preserving the final 60 seconds.
The ledger records elapsed time and nonreclaimed reservations. Each direct
call to the frozen guard is limited to at most 30 seconds and 256 MiB sampled
RSS. Validation and ledger work count toward the aggregate clock.

Guard calls are synchronous and sequential; no nested process-group guard is
introduced. The existing guard samples the chain parent and owned worker,
including its cleanup. Neither the aggregate ceiling nor the sampled memory
gate is a hard bound against delayed filesystem operations or uninterruptible
processes. Terminal corrective publication, lock release and return retain a
cooperative tail. The outer supervisor must use graceful cancellation and
bounded cleanup before hard kill.

## Checkpoint transition and failure semantics

A separate nonblocking chain lock complements each guard's checkpoint lock.
The ledger directory is single-use. A checkpoint-specific owner marker blocks
another chain when the prior chain is running or rejected. Resuming such a
chain is unsupported: a separate fresh root process/ownership audit and new
explicit allocation are required. The frozen helper exposes no durable early
child identity, and a hard-killed chain can orphan its separately-sessioned
worker. Guard death does not prove worker-group emptiness.

The initial digest must be trusted externally. Every next digest comes only
from the preceding accepted guard result after source, finite time/RSS,
cleanup, report-file equality, exact identity, predecessor and counter checks.
Node delta equals nodes_this_run and does not exceed the cap; witness delta
and per-slice changes are nonnegative and consistent. Hashes and counters
bind trusted execution records; they are not independent proofs of traversal.

Any saved witness is checked by both exact geometry verifiers, point count,
reflection symmetry, filename and source metadata. Positive witness delta
without persisted files rejects the invocation. The chain stops after the
first completed invocation with witnesses, after accepted exhaustion, after
timeout, or on any failure or budget limit. The frozen guard may visit further
nodes within the witness-producing invocation; no later invocation launches.
Timeout means an accepted incomplete frontier, never exhaustion.

Review findings concerning publication were corrected: rejected ledger items
remove accepted_sha256 and retain only published_unaccepted_sha256; terminal
receipt/marker writes are followed by source/cancel/deadline rechecks and
corrective rejection; source-read errors cannot bypass that rejection; each
iteration initializes its own report rather than reusing a previous one.
Crashes leave unknown state requiring explicit review. Advisory locks do not
protect against uncooperative writers. File fsync and atomic replacement do
not establish directory-fsync/power-loss durability.

## Independent tiny verification

All fourteen chain tests passed independently in 3.099 seconds and final hashes
matched the table. Tests exercise n3/n5 continuation against the reference
frontier through a witness-producing invocation, witness-stop behavior,
timeout and invocation limits, reservation exhaustion, CLI argument/clock
routing, trusted digest/identity and lock rejection, missing receipts/witnesses,
counter and nonfinite numeric tampering, first/later guard exceptions,
cancellation, interruption around accepted-ledger publication, and late
terminal source/read/cancel/deadline failures. The helper is mocked for these
tests; the DFS subprocesses are real tiny instances.

The proposed host lifecycle test is reviewed separately. Actual-host validation
must establish normal acceptance and cancellation with clean owned-process
cleanup before any large chain allocation. This source approval supplies no
search coverage, witness novelty, unrestricted infeasibility or proof-checked
UNSAT result.

## Proposed actual-host lifecycle gate

`tests/host_diagonal_chain_gate.py`, SHA
`d1f4bbb8673fda0e8e30dfb5bd525685103779ab76c95d43b5b2f84b20503372`,
is approved for supervisor execution. It performs real n3/n5 witness-stop
chains, checks both geometry verifiers and accepted report/frontier digests,
and separately sends SIGTERM after observing an n5 owned worker. Cancellation
must produce a cancelled guard report, clean owned cleanup, rejected chain
marker and disappearance of the observed worker PID. Merely losing the PID
would not establish the cleanup gate. Timeout and hard-kill paths remain
failed/unknown, with bounded communicate calls and preserved reports. This
review inspected the full script and hash but did not execute the host gate.

## Revised host gate and independent saved-artifact audit

The v2 script is `d3336b111d32f4f375a75f2540f015008c13dfe3a9b255710ecc5e3f2e099102`.
Its sole functional change from v1 is a 1,000-node cap for the n5 success case;
n3 stays at five and the separate cancellation case stays at one. This fixes
v1's safe reservation-limit exit before any n5 witness. It does not change the
production sources, per-invocation time or RSS caps.

The supervisor executed v2. Independently audited saved summary
`data/diagonal-chain-host-gate-v2/summary.json` has SHA
`a0c541a4d942f598d0c3c39a5812f262055ebdcf27694d2b468a0866420f1aab`.
Its recorded ledger/report/checkpoint hashes match the files, source bindings
match the frozen files above, predecessor links and node/witness deltas agree,
and accepted terminal markers are closed. The n3 chain has two accepted
invocations, 11 cumulative nodes, one visit and one saved certificate. The n5
chain has one accepted invocation, 415 cumulative nodes, 35 visits and 16
distinct saved certificates. Both exact geometry validators independently pass
all 17 certificates, with count 2n-1, reflection symmetry and matching filename
normalized hashes. Visits must not be described as unique certificates.

The separate n5 cancellation report records cancelled guard status and clean
cleanup; the chain and owner marker are rejected. Accepted/published checkpoint
fields are null, no certificate was saved, and the actual checkpoint remains
the initial accepted digest. Its worker's staged progress was not adopted.
The summary records observing a worker before SIGTERM and verifying its PID's
absence afterward. This reviewer audited those recorded artifacts and the test
source, but did not rerun the host gate or independently observe that past
process lifecycle. The supervisor also reports a later fresh process audit.
