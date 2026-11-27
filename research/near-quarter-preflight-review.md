# Independent near-quarter construction preflight review

**CODE REVIEW, REAL-HOST GUARD TESTS, AND TINY CLI GATE APPROVED.** No blocking
source finding remains at the hashes below. The construction preflight is ready
for a separately scheduled, capped n79 build after a numerical lane is free.
The n71 fixture gate is independently approved in
`research/near-quarter-fixture-review.md`. This review itself does not run or
authorize a search, and does not establish a measured n79 memory requirement.

Reviewer: Mathematician agent, gpt-6-astra, high reasoning;2026-11-27. I inspected
the driver, worker, tests, and resource/status documentation. I independently
reran the ten tiny tests in the existing research virtual environment: nine
passed and the actual-host process-monitor test skipped because `ps` is denied
in this sandbox. No author source, queue, supervisor, or active stream was edited.
No n79 model build, numerical search, or benchmark was run.

## Guard and native-memory accounting

The parent starts its monotonic deadline before spawning a fresh-session worker.
It samples operating-system process RSS, including native solver allocations,
and sums the guard parent, the worker group, and observed worker descendants.
The transient `ps` helper is explicitly excluded. RSS exceeding the configured
ceiling, wall expiration, or monitoring failure stops the original worker group.
The normal CLI rejects ceilings greater than30 seconds or256 MiB; lower values
are allowed for small tests.

This is a sampled kill gate, not a kernel allocation limit or proof of the true
instantaneous peak. The25 ms sleep, up-to0.5-second `ps` query, and scheduling/
termination latency permit overshoot. The report names its measurement
peak_sampled_rss_kib and documents those limits. The256 MiB allowance includes
the persistent guard parent, but host planning must still leave room for the
excluded helper and overshoot. Streaming alone does not bound native memory.

I found and requested correction of one fail-closed issue in the initial source:
empty or partial successful `ps` output could produce a zero or incomplete sum.
The approved revision rejects malformed rows, duplicate PIDs, negative RSS,
and missing/nonpositive samples for either the guard parent or worker PID.
A worker-exit race may conservatively reject a completed child instead of
silently accepting an unmeasured run. Monitoring exceptions are fatal and have
no fallback to Python-only estimates or mocked values in production.

Cleanup is correctly scoped to the original process group. The fixed construction
child does not spawn or re-session other processes. Although the sampler can
account for descendants in another group, killpg does not promise to kill arbitrary
escaped descendants; the documentation now explicitly says so. A future child
that spawns such processes would require renewed guard review.

## Construction and completion semantics

The child builds the orbit map, exhausts the half-turn-quotiented weighted-line
iterator to count it, then exhausts the frozen streamed CNF iterator. Count mode
keeps counts and a rolling hash. Build mode additionally submits every emitted
clause to a fresh native Glucose3 object. There is no solve, solve_limited,
enumeration, or model-extraction call. Internal clause insertion or simplification
does not yield any SAT/UNSAT claim; solver_result remains null and
search_performed remains false.

The line pass and CNF pass share the same parent time/RSS budget. Full completion
requires exhausting the CNF stream, submitting its clauses in build mode, stable
encoder/line-generator sources, and successful worker termination under the
guard. The solver object is deleted afterward; this tool does not export a model
or prepare a resumable solver state.

The child atomically publishes startup counters, phase changes, and progress
checkpoints. Until complete, counters are last-published lower bounds, not final
model sizes; a kill may lose uncommitted progress. weighted_lines_complete refers
only to the first line-count pass. prefix_sha256 identifies an emitted CNF prefix
and is never promoted to a full model hash before stream exhaustion. The variables
field is the maximum variable ID observed, with the orbit-ID range also included.

The parent treats an observed timeout, memory limit, monitor error, nonzero worker
exit, or source change as overriding a child completion message. It clears
complete, cnf_complete, build_complete, and model_sha256 while retaining observed
counters and the reason. Thus an incomplete formula cannot be reported as a
completed construction, let alone used here for an UNSAT conclusion. An exit0
report means successful construction only.

## Provenance and tests

Encoder and line-generator SHA-256 values are captured before spawn, checked by
the child before import and after enumeration, and checked again by the parent
after exit. The report also records the preflight source hash. Successful model
hashes cover a deterministic family/quotient header and every ordered emitted
clause. Count and build modes are tested to produce the same hash. These are
local source/model identities, not hashes of the interpreter or solver binary.

The tiny tests cover synthetic OS-tree/parent accounting; malformed/missing RSS;
actual process termination with a mocked RSS sampler; monitor failure; terminal
gate failure overriding child completion; startup zero counters; source mismatch;
maximum ceiling validation; and actual n3 count/build agreement with the frozen
encoder. Their mocks do not establish real OS RSS accuracy. The native n3 model
is genuinely constructed in the test, but its RSS values are mocked.

Independent rerun result:10 tests in0.401 seconds,9 passed,1 host-monitor test
skipped. The author reported an attempted escalation failing with an invalid-hook
payload; I did not treat that failure or the skipped test as successful host
validation. Separately, after this inspection, the parent reported a permitted
real-host rerun of these exact source/test versions: all10 tests passed, no skips,
in0.529 seconds. This includes the unmocked process RSS/time enforcement test.
That parent-run evidence clears the real-host guard-suite gate; it is distinct
from my sandbox run. The tiny construction test still mocks its RSS sampler,
so the parent must additionally run a tiny guarded n3 CLI with the real sampler,
inspect its terminal status and measurements, and reserve a free lane before a
capped n79 count/build. No large build should be inferred from source approval
alone.

The parent subsequently ran the real guarded n3 CLI build and saved
`data/near-quarter-preflight-n3.json`. I read that artifact and checked its
source hashes and fields. It reports built/complete/cnf_complete/build_complete,
2 clauses submitted,6 weighted lines, guard exit0 after0.101327834 seconds,
2 RSS samples and51,696 KiB peak sampled guard-plus-worker RSS. It records
search_performed=false and solver_result=null. These parent-executed results
clear the remaining tiny real-CLI gate. They are not an n79 performance estimate.

## Approved opt-in lazy-SAT CLI adapter

The explicit `--near-quarter-preflight` adapter is also **APPROVED** at the
hashes below. It copies argv, removes only the opt-in token, lazily imports the
preflight entrypoint, and forwards all remaining arguments. Without that token,
the ordinary lazy-SAT parser and search path are unchanged. The added
sys.exit(main()) preserves normal None-to-exit0 behavior and correctly propagates
preflight failure return2, preventing an incomplete build from looking like a
successful CLI exit.

I independently reran the seven ordinary lazy-SAT tests and three dispatcher
tests:9 passed, the actual-host subprocess dispatcher test skipped in this
sandbox, total0.675 seconds. Unit delegation checks preserve the caller's argv
and return code; the ordinary CLI help test retains existing options. The real
preflight CLI gate above covers the unchanged driver itself. The optional host
dispatcher subprocess test additionally checks the same construction report
and transitive source hashes through this adapter.

| Adapter artifact | SHA-256 |
| --- | --- |
| `src/lazy_sat.py` | `fe34d22eaeb6f62086b877942ee5330e432e47775e386c97d8b7b2fee42af629` |
| `tests/test_near_quarter_preflight_dispatch.py` | `f69b81a4afb57844e5a918cdf5c337b8699c25ec767a30b6d769dd3b4a4695a3` |

## Exact reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_preflight.py` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
| `tests/test_near_quarter_preflight.py` | `2429f09db056add1e92978501e90f3e18d6e3558260db059f6035efa564788a7` |
| `src/near_quarter_model.py` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| `src/line_model.py` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
