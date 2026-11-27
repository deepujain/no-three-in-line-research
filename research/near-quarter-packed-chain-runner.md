# Thin packed-chain caller implementation

Implementation model `gpt-6.1-sol`, reasoning `high`. This implements the approved
thin caller design in `near-quarter-packed-chain-runner-design.md`, using the
existing pool and `near_quarter_packed_worker.run_stage`. No packed worker,
codec, core, guard or unrelated worker source was changed. The only pool change
adds `research/near_quarter_packed_chain.py` to `ALLOWED`.

The closed canonical template is externally SHA-256 checked before parse and
contains the exact initial accepted record, declaration/map, nine fixed packed
sources and fixed stage limits. The CLI accepts only template path/hash, a new
32-hex run ID and the whole caller's integer seconds allocation (1..900). There
are no per-stage overrides. Each exclusive mode0700 run directory has two
content-addressed immutable records published through the existing publisher.

Before every call, the runner checks current caller/packed source identity,
exact remembered HEAD, lease absence, persistent cancellation and at least32s
remaining for the fixed30s stage plus2s reserve. Each stage ID derives from the
run ID and uint64 index. Existing stage lease/parent checking closes the writer
race. Returned acceptance must be newly accepted with lease_retained exactly
false and no lease path. Bounded existing job/report/receipt/checkpoint validators
bind returned stage ID, returned receipt hash, exact previous full HEAD, parent,
identity, map, declaration, source manifest and fixed quota/limits. Only that
validated successor can become the next parent. Rejection, uncertainty, error,
unexpected writer, any lease retention, source change and terminal search
status stop without retry, adoption or reconciliation.

The caller's nonblocking non-inherited wakeup pipe remembers SIGTERM/SIGINT even
while the inner stage temporarily installs its own flag handlers. No async
exception interrupts accepted commit. Existing wakeup-fd ownership is rejected
before any stage, with its original fd and handlers restored. All exit paths
restore caller-owned handlers/wakeup state and close the two descriptors.

The final immutable summary records attempts, validated acceptances, exact
accepted new-node sum, last validated HEAD hash, last attempted stage/validated
receipt, sources, template/caller hashes and monotonic timing through summary
preparation. The returned stdout object additionally measures complete caller
time through final durable publication and handler cleanup. An artifact cannot
include the time required to fsync itself; these scopes are explicit. The
existing pool accounts the complete child invocation once. Inner stage evidence
must not be charged as additional pool experiments. Stage fsync coordination may
exceed its nominal cutoff; the existing pool TOTAL+30s remains containment.
Abrupt SIGKILL can leave only the start record and stage evidence; there is no
resume mode or automatic lease repair.

## Focused evidence

`data/near-quarter-packed-chain-tiny-evidence.json` retains all source hashes and
36 passing runner/worker/read-only-integration tests in3.053s. Ten new focused
tests cover exact full sequential parents, n3 witness, n5/n7 exhaustion, strict
template limits, duplicate run IDs, both caller budget cutoffs, rejected/
uncertain/idempotent stages, accepted results with retained or unexpected lease,
source/self changes, returned stage/receipt mismatch, changed HEAD and real
SIGTERM delivered at the inner `after_head_replace` boundary. That signal test
observes one newly accepted stage, caller cancellation and no second call. The
incompatible-wakeup-fd test checks the prior fd/handlers and closed new pipe fds.
These synchronous fake-guard tests provide no host RSS/ownership evidence.

The final runtime template `data/packed-readonly-n79-r1-chain-template.json` is
7071 canonical bytes, SHA-256
`243775d2aaa74c29171d0f5771c197b797bcc97c611f8e047678b5acb7d01df4`.
It binds exact audited HEAD SHA-256
`9039fdd3607dafd5cab0ab4d4fa88ea83aca748d25e774fd3f0be39bad11b8d5`,
checkpoint `71d9ea2f977c6bdc50aa5da2907d439eff8637cb2f1d103bae59f7a4ec1da01b`,
receipt `b411cfdf2ae643ed15ca8050555ad5760a048ac82574ae440c77feb717c17787`,
511 accepted nodes, quota250 and30s/256MiB. Its bounded audit rereads the existing
artifacts and constructs no grid geometry. Source review and Root's independent
host gate precede the intended existing-pool allocation. Packed-only windows
must use max_concurrent1 because the inner guard measures the nested tree while
the outer pool measures its direct child. No host search was launched by this
implementation work.
