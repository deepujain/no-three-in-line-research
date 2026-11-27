# Thin bounded packed-chain caller for the existing experiment pool

Design only. No runner, pool edit, source change or launch yet. Current packed
coref2570452/codec88ce7a7a/worker7f8c8a16 remain frozen. Model `gpt-6.1-sol`,
reasoning `high`. Root requested continuous counted work after the actual
matched eleven-node improvement, without another scheduler/guard/protocol.

## Caller and fixed authority

Add one small `research/near_quarter_packed_chain.py`. It runs in the existing
pool child and directly calls the existing reviewed `run_stage`; it copies no
worker, publisher, guard or accepted-HEAD logic and creates no subprocess,
monitor, background thread or second queue. It never changes packed files.
Only add its literal path to experiment_pool.ALLOWED after the current pool
finishes and Root releases that file. Existing pool timing/receipts stay.

CLI is --request-template PATH --template-sha256 SHA --run-id32HEX --seconds
TOTAL. The pool supplies TOTAL as its existing integer seconds (at most900).
It is the whole caller budget, not an override of per-stage time. There are no
node/RSS/per-stage/source override flags. Direct script execution uses only a
fixed repository-root import bootstrap for the existing worker API.

The canonical strict <=16KiB template is externally hash-checked before parse.
Its exact fields are schema,chain_dir,start_accepted_record,n,declaration_b64,
expected_map_json_sha256,source_manifest,stage_nodes,stage_seconds,rss_mib.
start_accepted_record is the exact already reviewed HEAD object. The nine source
slots and full source-bound identity must match current files/accepted receipt.
The core's helper hashes remain transitively bound as before. stage_seconds is
exactly30, rss_mib exactly256; stage_nodes is one fixed declared reviewer-approved
quota, proposed250 only if Root's running250-node trial passes. No adaptation.
Template shape/bounds use the existing strict readers/validators. The template
has no worker stage_id/parent fields to override: each invocation derives those
explicitly from the authorized previous accepted record.

A new mode0700 chain/runs/RUNID directory is exclusive. Existing run IDs fail;
there is no recovery/retry mode. An immutable bounded start record binds caller
source SHA, template raw SHA, run ID, exact initial HEAD and total deadline.
The pool's ordinary outer receipt also records caller entrypoint SHA and argv.
This caller provenance is separate from the unchanged nine-source stage
manifest, so the already accepted packed chain remains usable without source
migration or another fresh root.

## Single bounded loop

Before every stage, recheck caller/current packed sources, cancellation, exact
expected HEAD, no retained writer lease and total monotonic budget. Do not start
unless at least32s remain (30s stage plus2s caller reserve). Stage limits remain
30s/256MiB with existing28s child deadline/2s eligibility reserve. No sleeps.
Filesystem coordination retains the existing possible-overrun limitation; TOTAL
is not a new hard I/O guarantee. Existing pool timeout TOTAL+30 remains outer
containment and is not replaced.

For index0,1,... derive a fixed32hex stage ID from a domain-separated SHA-256 of
run ID and uint64 index. Call run_stage with the exact previous accepted
checkpoint hash and the fixed template declaration/map/quota/limits. Its normal
lease acquisition/expected-parent equality closes any race after caller reads.
There is no whole-run lock or second lease. After an accepted result, bounded
validate the resulting HEAD/receipt/source/status binding and parent relation,
and remember that exact record as the only next authority. An unexpected other
writer's HEAD stops the caller; it does not adopt a newly discovered frontier.

Stop immediately on rejection, exception, acceptance_uncertain, source/HEAD/
lease discrepancy, cancellation, total-budget cutoff, verified_witness or
slices_exhausted. Require a newly accepted stage, not idempotent redispatch.
Never retry, steal a lease, reset the chain, skip an artifact failure or enqueue
a replacement. At most one stage is active. Accepted stage reports supply exact
logical deltas; rejected work never increases the chain total.

Keep only O(1) totals and the last record in memory. Existing immutable per-stage
artifacts already supply the chain history. Write one immutable bounded final
caller summary: status, start/end HEAD hashes, attempts/acceptances, exact
accepted new-node total, last stage/receipt, source/template/caller hashes and
complete caller elapsed time. Abrupt termination may leave only the start
record plus existing stage artifacts; ordinary pool reservation semantics apply.

## Cancellation across existing nested handlers

run_stage temporarily installs its own flag-only SIGTERM/SIGINT handlers. A
signal during late accepted coordination could otherwise disappear from an
outer caller flag and allow an unintended next stage. Do not monkeypatch the
worker or its handlers. The caller uses a standard nonblocking signal wakeup
pipe, with non-inherited descriptors, plus flag-only handlers between stages.
Python's wakeup-fd notification remembers TERM/INT even while the inner reviewed
handler is installed. Drain/check it before and after each run_stage; any
recorded stop prevents another stage. Restore handlers/wakeup-fd on exit; reject
an incompatible existing wakeup-fd. No asynchronous exception interrupts a
commit. This is cancellation bookkeeping, not another process monitor/guard.
A SIGKILL retains the existing inability to unwind; never infer safe automatic
resumption from an absent final caller record.

## Existing pool and review gates

Use an exclusively packed window with max_concurrent1 after the current valley
cohort finishes. The pool accounts root child PIDs while the existing inner
owned guard measures its supervisor plus owned worker tree; avoiding concurrent
pool jobs prevents hidden nested-worker overlap in that aggregate worker budget.
Pool elapsed time counts the entire chain caller once. Inner stage summaries
are evidence, not additional data/experiments runtime charges. A caller process
completion alone is not an accepted frontier or mathematical conclusion.

Independent design approval precedes implementation. Focused tiny/mock tests
must cover exact sequential parent links, fixed argv/template limits, unique
IDs/no repeated run, source/HEAD change, all terminal/failure stops, total-budget
boundary/no next stage, and cancellation during inner accepted commit via the
wakeup pipe. Then source review and Root allocation follow. No host launch or
larger numerical allocation follows from this design alone.
