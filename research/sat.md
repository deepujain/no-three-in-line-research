# Incremental lazy SAT experiment

Research Software Engineer; assigned `gpt-6.1-terra`, reasoning `high` per parent. Date 2026-11-26. This is a finite search experiment, not an asserted new theorem or record. Optional local dependencies are pinned in `requirements-research.txt`: python-sat 1.8.dev24 and six 1.17.0. The parent provisioned the local `.venv`; normal standard-library tests skip the optional SAT tests when the dependency is absent.

## Exact model and interpretation

At n≥2, use one Boolean per cell. Enforce exactly two selected cells in each row and column using `pysat.card.CardEnc.equals`, `EncType.seqcounter`, and an `IDPool` starting above the cell variables. Such a state contains exactly 2n points. After each SAT solution, run the exact normalized-direction geometry verifier on its selected grid cells, add a negative three-literal clause for each actual collinear triple found, and solve incrementally. These clauses are necessary for every no-three-in-line configuration, never heuristic exclusions. Every accepted witness must pass both independent exact geometry verifiers, with the full point count; the script only saves a point list for a double-verified witness.

Solver-reported UNSAT after any collection of correct cuts would imply no full 2n witness, conditional on the model, encoding and solver correctness: the formula is a relaxation containing every valid witness. The program does not currently generate or independently check an UNSAT proof certificate. A timeout, interrupted native solve, or incomplete series of cuts says nothing about nonexistence. Result order and timings can vary by backend and runtime; runs use backend default settings and specify no random seed.

`src/lazy_sat.py` allows Glucose3 and MiniSat22, starts a timer thread that invokes the backend's real interrupt, and calls `solve_limited(expect_interrupt=True)`. It also checks a monotonic deadline between iterations and while adding cuts. Bootstrap/encoding occurs before the interrupt timer starts, so the requested time budget is not an operating-system hard limit if initialization itself stalls. Interrupt can race with a successful solve; a result after the deadline is conservatively treated as timeout. The timer is joined before deleting the solver. All-line triple expansion exists only for tiny validation grids and is explicitly rejected for n>6.

## Validation

` .venv/bin/python -m unittest discover -s tests -p test_lazy_sat.py -v` passes: at n=2,3,4 independent exhaustive combinations establish full-witness existence, then both the lazy solver and a solver initialized with all small-grid line triples find full witnesses checked by the brute-force determinant verifier. The separate line-model test compares all subsets of n≤4 against that verifier. A separate test invokes a real native Glucose3 `solve_limited` on the 19-pigeons/18-holes formula and verifies that timer-driven interrupt returns `None`; it is not a mocked test. `python3 -m unittest discover -s tests -p test_lazy_sat.py -v` succeeds with two expected skips when the optional dependency is absent.

## Executed searches

Run with `.venv/bin/python src/lazy_sat.py --n N --seconds SECONDS --output data/sat-NAME.json`. Data files preserve backend, time budget, counts and witness when present. Measured runs, Glucose3, backend default seed:

| n | seconds budget | elapsed seconds | candidate solves | cuts | outcome |
|---:|---:|---:|---:|---:|---|
| 8 | 3 | 0.001649 | 5 | 28 | 16-point witness, both checkers valid |
| 10 | 3 | 0.064949 | 194 | 1,579 | 20-point witness, both checkers valid |
| 79 | 40 | 40.008595 | 2,358 | 1,047,428 | timeout, no accepted witness or UNSAT |

The n=79 run reached its deadline in Python-side work; `timer_interrupt_fired` was false in that run, so that particular run does not demonstrate an in-solver interruption. The pigeonhole test does demonstrate that the interrupt path works on an active native solve. Counts are executed-run observations rather than deterministic time guarantees. No novelty claim is made for the n=8 or n=10 witnesses. The 79 result supplies no new valid lower bound, optimality proof, or impossibility evidence.

## Resuming geometry cuts

Pass `--checkpoint PATH` to create or append a JSONL file with an n, mapping, source description and source-file SHA-256 header followed by learned three-variable geometry cuts. On resume, the loader independently checks grid identity, integer type, bounds, distinctness and determinant zero before adding **every** saved triple. The hash records provenance, not a trusted proof of correctness: validity comes from rechecking the coordinates. Malformed or noncollinear records are rejected before the solve can report UNSAT; if the budget expires partway through loading, the result is timeout. Timeout accounting includes checkpoint load, although the native solver initialization caveat above remains. The checkpoint records geometry only, not SAT solver state, restart schedule, learnt internal clauses, phases or an exact replay. New writes are buffered; normal shutdown flushes them, while an abrupt process kill can leave a truncated final record that must be repaired or discarded before resumption. A file must be owned by one process at a time; use separate paths for parallel runs. Do not edit a checkpoint concurrently.

`--max-cuts N` stops after at most N new cuts in that invocation, returning `cut_limit` (not UNSAT); previously loaded cuts do not count against this cap. `--progress PATH --progress-interval SECONDS` appends lightweight JSONL status records and a final record. Counters are per invocation except `cuts_loaded`. Progress and checkpoint paths must be distinct and should be unique per worker. The tests exercise stop/resume and malformed, noncollinear, out-of-range and wrong-grid rejection. The first 79-grid run predates checkpointing, so its cuts cannot be resumed.

## Independent review of the 2n−1 target

The target-157 implementation in `src/lazy_sat.py` SHA-256 `467b3d9b3b76ef5bf381723050fe117d6c70705da318b49cfcf73e960f40eab1` was independently reviewed by gpt-6.1-terra, high reasoning, per assignment. One independently selected row deficit and column deficit, with real-cell occupancy plus its own indicator equal to two on each axis, enforce total 2n−1 and capacities ≤2. These indicators do not restrict their intersection, which may be occupied. Variable-pool IDs keep them separate from real cell IDs. Geometry cuts are revalidated real-cell triples and may be reused across targets. The tests exhaust all real assignments on n=2,3,4 for both targets, include an occupied deficit-intersection valid witness, exercise cross-target checkpoint reuse, and verify accepted witnesses with both geometric checkers. Tests were inspected rather than rerun during this review while numerical workers were active; no critical issue was found. This model expresses an exact finite search but does not establish a solution, infeasibility, or novelty without a corresponding verified result and fresh literature check.


## Additional target 2n−1: independent axis-deficit indicators

This extension was implemented by the research software engineer with model `gpt-6.1-sol`, reasoning `high`. The worker remains single-core apart from its timer/interrupt control thread. `--target` now accepts 2n (the default) or 2n−1 only. At n=79 this permits both target 158 and target 157; the latter would improve the separately retained published 156-point baseline even without attaining 158.

For target 2n−1, `axis_encoding(n,target)` allocates one deficit Boolean per row and one per column, all above the n² real-cell IDs in the shared `IDPool`. It enforces exactly one true row deficit and exactly one true column deficit, and enforces `sum(real axis cells)+axis deficit=2` for each row and column. Counter auxiliary IDs use that same pool. Thus one row and one column have exactly one real point, every other row and column has two, and there are exactly 2n−1 selected real cells. Conversely, any cell set with row/column capacities two and total 2n−1 has exactly this deficit pattern, so the encoding is equivalent to those capacities and target.

These are independent axis indicators, not an artificial ghost cell. In particular, the deficient row and column may intersect at an **occupied real cell**. The valid five-point n=3 set `{(0,1),(1,0),(2,0),(1,2),(2,2)}` has deficient row y=1 and column x=0 while (0,1) is selected. The test fixes this complete cell assignment and requires SAT, preventing accidental exclusion by a ghost-cell construction.

Only real variables 1..n² are decoded into candidates and used in geometry cuts. Candidate counts, independent final checks, witness records, progress records and the report use the requested target. Geometry checkpoints remain validated real-cell collinear triples and contain no target-specific cardinality assumptions, so they can be reused sequentially across targets for the same grid. Concurrent file sharing remains prohibited. Solver UNSAT remains solver-reported without an independently checked proof, and timeout remains incomplete for the requested target.

Seven SAT tests pass in the local optional-dependency environment. They exhaust every real-cell assignment on n=2,3,4 for both targets (132,128 assignments in total) under complete assumptions, checking SAT exactly against direct row/column capacities and point count. Other coverage includes disjoint auxiliary ranges, the occupied-intersection example, invalid targets, independently verified witnesses, and reusing the same validated geometry checkpoint in the order target 5→6→5. Existing full-target witness, checkpoint rejection and native interruption tests continue passing.

Known small-instance benchmarks for both targets n=2..8 all yielded witnesses accepted by both independent geometric verifiers. Total measured wall time was 0.018969 seconds, below the allocated ten-second small-benchmark cap. There is no novelty claim. Full artifact: `data/sat-deficit-small-benchmark.json`.

| n | target | candidate solves | new geometry cuts | elapsed seconds | outcome |
|---|---|---|---|---|---|
| 2 | 3 | 1 | 0 | 0.000433 | valid_witness |
| 2 | 4 | 1 | 0 | 0.000151 | valid_witness |
| 3 | 5 | 2 | 1 | 0.000232 | valid_witness |
| 3 | 6 | 1 | 0 | 0.000152 | valid_witness |
| 4 | 7 | 2 | 4 | 0.000324 | valid_witness |
| 4 | 8 | 5 | 9 | 0.000423 | valid_witness |
| 5 | 9 | 13 | 30 | 0.001137 | valid_witness |
| 5 | 10 | 14 | 34 | 0.000955 | valid_witness |
| 6 | 11 | 22 | 51 | 0.002180 | valid_witness |
| 6 | 12 | 24 | 63 | 0.001846 | valid_witness |
| 7 | 13 | 21 | 54 | 0.002669 | valid_witness |
| 7 | 14 | 37 | 182 | 0.003753 | valid_witness |
| 8 | 15 | 19 | 93 | 0.002414 | valid_witness |
| 8 | 16 | 5 | 28 | 0.001159 | valid_witness |

The stable worker source SHA-256 at review/queue handoff is `467b3d9b3b76ef5bf381723050fe117d6c70705da318b49cfcf73e960f40eab1`. Both the mathematician and independent implementation reviewer were notified. The engineer ran no n=79 SAT benchmark in this handoff; the shepherd controls further bounded queue allocations.

```sh
.venv/bin/python src/lazy_sat.py --n 79 --target 157 --seconds 900 --checkpoint data/sat-target157-cuts.jsonl --progress data/sat-target157-progress.jsonl --output data/sat-target157-run.json
```

Each active worker must own distinct checkpoint, progress and output paths. A previously saved geometry checkpoint may be copied or handed off after its writer stops, then independently revalidated on load for either target; its target-free geometry semantics do not make concurrent appends safe.
