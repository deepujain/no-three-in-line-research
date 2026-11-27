# Explicit-threshold support census and build preflight

Status: separate adapter independently approved; final isolated CLI route under
review before the supervisor's tiny actual-host gate. No n79 census, build or
search was run by this worker. Model setting: `gpt-6.1-sol`, reasoning `high`.

The adapter `research/near_quarter_direct_preflight.py` binds ten sources:
original model, line generator, verifier, compact and row-floor encoders,
reviewed threshold variant, unchanged owned-process helper, original atomic/hash
utilities, this adapter, and shared CLI entrypoint. Every historical encoder,
preflight, solver and helper is unchanged. The CLI adds only the opt-in route
`--near-quarter-direct-preflight`, preserving checkpoint/fast DFS and all
previous near-quarter routes.

Both `--mode` and the two threshold flags are required. Each cutoff must be an
explicit integer 5, 6 or 7. Modes are `count` and `build`; neither searches.
The unchanged helper permits at most 30 seconds and 256 MiB sampled parent plus
owned native RSS, including its bounded cleanup and possible sample overshoot.
The helper interval excludes parent setup and final receipt writing, matching
the historical preflight; the child deadline is set before worker launch.
Cancellation is a flag through cleanup, and any gate/source failure invalidates
completion and accepted count/CNF flags while retaining diagnostic counters.

## Count before native allocation

Count mode streams the full C4 line-group census and stores a small histogram
of `(light variables, coefficient-two variables, coefficient-above-two variables,
diagonal guards)` with group multiplicities. Special main/anti-diagonal groups
remain separate and omitted from capacities under the reviewed exactly-one
pair condition. C4 group and represented full-line totals are retained.

After the census, the adapter emits one small synthetic capacity per support
class and threshold configuration using the installed reviewed encoder. This
measures exact clause/literal/auxiliary costs without assuming universal
sequential-counter formulas. Renaming distinct real variable IDs leaves these
costs unchanged; all sequential auxiliaries and shared gates receive fresh
IDs, so their counts add across groups. Coefficients above two each produce
the same forced-false unit regardless of their exact value. Fixed diagonal
equality costs are measured with the installed encoder; fixed row-floor counts
and literal totals use the previously reviewed algebra.

Multiplying these measured local costs by histogram frequencies yields exact
whole-formula clause, literal and variable counts for all nine threshold pairs
in `{5,6,7}^2`. This is concrete count evidence for selecting a later native
build. Count mode never instantiates `pysat.solvers.Solver`, never streams or
hashes a full formula, and never claims CNF/build completion. A successful count
sets `complete`, `counts_complete` and `support_histogram_complete`, while
`cnf_complete`/`build_complete` stay false and `model_sha256` stays null.
`clauses_added=0`, `native_solver_constructed=false`, and `search_performed=false`
make those distinctions explicit. A failed gate invalidates accepted totals;
remaining histogram/candidate rows are diagnostic only.

A small count example is:

```sh
.venv/bin/python src/lazy_sat.py --near-quarter-direct-preflight \
  --n 9 --mode count --atmost-two-direct-limit 7 \
  --conditional-atmost-one-direct-limit 7 --seconds 5 --rss-mib 256 \
  --output data/near-quarter-direct-preflight-n9-count.json
```

The explicit pair selects top-level counters/header; all nine candidate rows
are still emitted. The next large allocation belongs to the supervisor and is
count-only under the unchanged caps. Neither this adapter nor this worker
chooses a pair automatically or schedules a retry/native build.

## Selected native build

Build mode first performs the same census/count comparison, then streams the
chosen complete formula into Glucose3 without calling either solve method. Its
header binds the exact threshold configuration and reviewed variant identity.
The worker hashes the header and every clause, checks actual clause/literal/
variable totals against the histogram prediction, rechecks all sources and
its deadline, and only then publishes completion. The parent must accept the
helper's final resource/cleanup gate and stable bindings. A mismatched count,
partial stream, cancelled worker, source change or gate failure cannot provide
an accepted complete model digest.

## Tiny verification and host gate

Ten tests pass; one explicit actual-host case skips. Count mode is checked
against full independently emitted tiny clause streams for all nine candidate
pairs at n3/n5/n7/n9, while a Solver constructor spy ensures no native solver
is created. Native n3/n5/n9 builds at `(5,5)`, `(6,6)` and `(7,7)` match exact
formula digests/counts under no-solve spies. n9 exercises the changed direct
branches: `(7,7)` has 438 clauses and 23 variables (three auxiliaries).

Tests also reject aggregate/native mismatches, pre/post source changes, all
parent resource/cleanup/monitor/cancel/launch/worker failures, parent loss,
expired deadlines, invalid/missing mode or thresholds, and solve fallthrough.
Worker and parent failure paths clear accepted count flags consistently.

After final CLI review the supervisor runs:

```sh
DIRECT_THRESHOLD_HOST_TESTS=1 .venv/bin/python -m unittest \
  tests.test_near_quarter_direct_preflight -v
```

That enables tiny actual n9 count/build CLI checks with source identity, exact
438/23 totals, no search and clean cleanup. Only after those gates may the
supervisor obtain a count-only large-grid histogram. Aggregate cost changes
still do not establish native RSS savings or search behavior; a selected
native preflight requires its own measured resource outcome.
