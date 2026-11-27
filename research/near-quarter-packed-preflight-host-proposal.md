# Narrow packed actual-host preflight proposal

Prepared only; no host gate has run. Worker7f8c8a16 and codecac57fd57 await the
final bound independent approval record. The separate prepare/audit script is
`research/near_quarter_packed_preflight.py`, SHA-256
81d16d57cd6575b5103d0fe1e7016c7ad417ff9fcbdeb2150fbaea54657ba5c5.
The script never launches a worker or constructs geometry. It uses explicit
tiny ordered-map fixtures; independent review must compare them to the frozen
oracle before host allocation. Source changes fail rather than refresh hashes.

Run each command from the repository root. Root schedules one gate at a time,
inspects its audited receipt, and decides whether the next gate may run. Every
request has a separate fresh chain, zero expected parent, max_new_nodes0,
5s/256MiB, and an absolute worker deadline2s before its precommit deadline.
No loop, retry, sample-padding sleep, counted search or larger-grid option exists.

Prepare the four requests once, using a previously nonexistent output directory:

```sh
python3 -m research.near_quarter_packed_preflight prepare data/packed-preflight-r1
```

After script/source approval, execute and audit n3 construction:

```sh
python3 -m research.near_quarter_packed_worker --request data/packed-preflight-r1/n3-construct.request.json > data/packed-preflight-r1/n3-construct.return.json
python3 -m research.near_quarter_packed_preflight audit data/packed-preflight-r1 --gate n3-construct
```

After Root inspects that result, use the same two commands separately for
n3-root, then n5-construct, then n5-root, replacing only the gate name. All four
chains are independent. Root does not run an existing request again or reuse
its chain on failure. An absent/invalid return, insufficient RSS sampling,
monitor/cleanup/resource/source failure, expired eligibility deadline or
retained lease stops this sequence. Preserve artifacts for diagnosis; never
steal/remove a retained lease or silently substitute a new identity.

The audit requires exact current sources, original request/job hashes, nonce/
device/inode lease-token shape, fixed operation/declaration/limits/deadlines,
strict report and candidate structure, immutable receipt/accepted HEAD binding,
zero counted nodes and zero traversal domain/batch/cursor probes, no witness,
and absent owner lease after successful durable coordination. Full private
geometry/save replay remains inside the measured child; the later audit does
only bounded reads/hashes/structural checks. It writes an exclusive gate audit
receipt with source and artifact hashes and the unmodified helper measurements.

The helper measures guard-parent plus owned process-group/observed descendants
with native heap, cleanup included, possible sampling overshoot, transient ps
excluded. Its returned seconds_limit is at most5s after setup is deducted.
The supervisor's complete_invocation_ns extends through receipt/HEAD durability
and lease release; setup/postprocessing and later audit are outside sampled
helper RSS. Final filesystem coordination can exceed the eligibility deadline;
no hard5s end-to-end filesystem promise is made. CLI-return capture and the
exclusive audit file preserve these separate timings.

## Consolidated n79 allocation recommendation

Root reported all four individually audited tiny host preflights passed. The
n71 fixture and n9 pilot offer optional additional validation; they are neither
mathematical necessities nor process-containment prerequisites. Root directed
removing that size ladder, subject to independent allocation review.

Propose one fresh n79 operation=root at30s/256MiB, max_new_nodes0, absolute
worker deadline28s from invocation start and2s precommit reserve. This existing
operation constructs the full packed state, compares its ordered map with the
frozen oracle inside the measured child, pushes exactly one diagonal, and
privately save/replays rootENTER with nodes0. It therefore consolidates the
construction/root preflight without a new operation or source change.

Exact prepared request is data/packed-n79-r1-root.request.json, SHA-256
3475fc3c390b391eecc3bf2f25abc08028359aebe15306db19d4cf0e8312859d.
Source-bound proposal data/packed-n79-r1-root.proposal.json, SHA-256
4977e34b757f29c0091d68e2611aa553d065fbb519754feba9eb81f4577bac3c.
The chain data/packed-n79-r1-root.chain was absent at preparation. The declaration
was generated arithmetically (3282bytes); map identity
78054420e2f53dde1ea7d1d3823b220d7bf1b8e6e0edb5f05ea6210786528032
was copied from an existing frozen-model artifact, without geometry generation.
This agent has not run it. After independent approval, Root executes:

```sh
python3 -m research.near_quarter_packed_worker --request data/packed-n79-r1-root.request.json > data/packed-n79-r1-root.return.json
```

After independent inspection of that receipt, propose exactly one n79 stage
from its explicitly accepted root: max_new_nodes1,30s/256MiB and the same28s
child deadline/2s reserve. This measures restore, first real root MRV/domain scan,
one counted node and private save replay. No throughput or absence-of-witness
claim follows. A failed stage preserves the accepted root or explicitly reports
uncertain acceptance and retains the lease. Preserve the attempted-stage record
and stop; no second node, continuation, retry or larger cap is implicit.
