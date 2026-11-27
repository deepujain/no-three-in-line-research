# Near-quarter CNF construction preflight

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. This separate tool leaves the reviewed encoder, supervisor, queue and active workers unchanged. It prepares or builds the restricted near-quarter-turn CNF using free PySAT `glucose3`. It never calls a solver search method, reports a solver result or claims UNSAT. No n79 geometry enumeration, model construction or numerical search was run during implementation.

## Guard and budget meaning

The normal CLI launches a fresh Python worker in its own process session. The host guard starts its wall clock before launching that worker, samples operating-system RSS using `ps`, and kills the worker's original process group on a deadline, excessive RSS or monitoring failure. Group cleanup also runs after worker exit. The fixed construction worker does not spawn or re-session subprocesses. The sampler accounts for observed descendants even if their group differs, but `killpg` does not promise cleanup of arbitrary descendants that escape the original group; such worker changes would require a revised guard. The default ceilings are 30 seconds and 256 MiB; command-line values may lower either ceiling but cannot increase it.

RSS is the sum of the guard parent and the child process group/descendants. Native solver allocations are part of the worker's process RSS. The transient `ps` helper is excluded. This is a measured kill gate, not a kernel-enforced peak allocation cap: allocations can overshoot between samples, the `ps` query can take up to 0.5 seconds, and termination has scheduling latency. Leave host memory margin for those effects and concurrent work. Streaming clauses does not bound native solver memory. A missing or denied monitor fails closed; production never substitutes a Python-only estimate or mock sampler. Empty, malformed, duplicate or negative-RSS monitor rows are rejected. Both guard-parent and worker PID rows must exist with positive RSS; a worker-exit race can therefore conservatively refuse a completed child.

Terminal timeout, RSS, monitoring, source-stability or worker-exit failure overrides any child completion publication. Partial counters survive, while the final report clears `complete`, `cnf_complete`, `build_complete` and `model_sha256`. Construction can simplify a formula internally; even an empty clause does not cause this tool to claim UNSAT.

## Counts, hashes and partial work

The worker creates the orbit map, counts the weighted-line generator to exhaustion, then consumes the frozen encoder's exact `streamed_cnf` generator. The second phase visits geometry again through that generator; the combined work shares one wall/RSS gate. Count mode hashes/counts clauses without retaining a solver. Build mode also adds every clause to a native `glucose3` solver and deletes it after recording the construction result. There is no model export or retained solver to resume.

Every successful report includes orbit/family metadata, source hashes, orbit-map hash, weighted-line count, total observed variable IDs, emitted clause count, added clause count, and a deterministic `model_sha256`. The latter hashes a compact sorted JSON header containing family metadata and the half-turn quotient choice, followed by each exact ordered compact-JSON clause and newline. Count and build modes produce the same model hash. `variables` includes orbit IDs and every auxiliary ID observed in the emitted stream, including variables a solver may simplify away.

The parent captures encoder and line-generator source hashes before spawn. The child checks them before import and after complete enumeration; the parent checks them again on exit. Changed sources invalidate completion. The report separately records the preflight tool's source hash. These identify the actual local source files; they do not assert a hash of the interpreter or native solver binary.

Atomic child checkpoints publish at phase changes and at most every 0.05 seconds of generator progress. After a kill, counters are the last published lower bounds, potentially behind work that actually occurred. `weighted_lines_complete` describes only the independent line-count pass. Only full clause-stream exhaustion, completed clause insertion in build mode and successful host guard termination establish a successful preflight. Partial stream hashes are explicitly `prefix_sha256`; they are never presented as a complete model hash. No partial formula is solved. No restart or coverage exclusion is claimed.

## Validation and future scheduled use

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_preflight.py -v
```

Ten tiny tests were prepared: nine pass here and the real-host RSS monitor test skips because this sandbox denies `ps`. Passing cases cover native/tree/parent RSS accounting against synthetic OS rows, rejected malformed/missing/invalid monitor output, actual child timeout/kill with a mocked RSS reader, monitor failure, gate-versus-completion races, explicit startup zero counters, source mismatch, ceiling validation, and tiny real n3 count/build agreement with the frozen stream. The n3 construction test mocks only the host RSS reader, so it does not establish actual native RSS measurements.

The sandbox escalation attempt for real `ps` validation was rejected with `invalid hook payload: permission request does not match the recorded tool call ''`. Root subsequently reran all ten core tests on the host with real `ps`; all passed without skips. The independent mathematician approved the frozen core in `research/near-quarter-preflight-review.md`. Root also ran a guarded tiny n3 CLI build, saved as `data/near-quarter-preflight-n3.json`, which the reviewer independently inspected: complete construction, 2 clauses, 6 weighted lines, 0.1013 seconds and 51,696 KiB peak sampled guard-plus-worker RSS over two samples. `search_performed` is false and `solver_result` is null. This clears the tiny host CLI gate; it provides no large-model performance estimate. A free lane and separate allocation are still required for large execution.

The tiny host validation command is:

```sh
.venv/bin/python research/near_quarter_preflight.py --n 3 --mode build \
  --seconds 5 --rss-mib 256 --output data/near-quarter-preflight-n3.json
```

The separately scheduled n79 construction, after review and a free lane, can use `--n 79 --mode build --seconds 30 --rss-mib 256` with a fresh output path. The final JSON status and CLI exit code distinguish complete construction (exit 0) from any partial/failure state (exit 2). Neither result initiates a search.

## Existing-entrypoint integration

An explicitly authorized CLI-only adapter in `src/lazy_sat.py` recognizes `--near-quarter-preflight`, removes that opt-in flag and delegates every remaining argument to `near_quarter_preflight.main`. The ordinary SAT parser and search path remain unchanged. The delegated return code propagates to the process exit code. This permits the existing scheduling allowlist to use the guarded build-only route without changing the supervisor or queue. Its entrypoint SHA is recorded by the supervisor; the delegated report records the preflight, encoder and line-generator hashes plus the complete CNF hash when successful.

```sh
.venv/bin/python src/lazy_sat.py --near-quarter-preflight --n 3 --mode build \
  --seconds 5 --rss-mib 256 --output data/near-quarter-preflight-n3.json
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_preflight_dispatch.py -v
```

The adapter has a unit test for exact argument/return-code forwarding, an ordinary-CLI help subprocess test and a tiny real n3 build subprocess test checking complete counters, hash provenance and actual host RSS. The first two pass in this sandbox; the last requires host `ps` and skips here. The independent mathematician approved the adapter at the hashes below, reran the seven ordinary SAT tests and three dispatcher tests with nine passes and one sandbox skip, and independently inspected root's real tiny CLI artifact. The frozen approved guard and encoder were not changed for integration.

| Artifact | SHA-256 |
|---|---|
| `research/near_quarter_preflight.py` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
| `tests/test_near_quarter_preflight.py` | `2429f09db056add1e92978501e90f3e18d6e3558260db059f6035efa564788a7` |
| `src/lazy_sat.py` adapter | `fe34d22eaeb6f62086b877942ee5330e432e47775e386c97d8b7b2fee42af629` |
| `tests/test_near_quarter_preflight_dispatch.py` | `f69b81a4afb57844e5a918cdf5c337b8699c25ec767a30b6d769dd3b4a4695a3` |
| Unchanged `src/near_quarter_model.py` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| Unchanged `src/line_model.py` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
