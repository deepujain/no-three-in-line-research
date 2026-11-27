# Build-only preflight for the row-quota variant

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. `research/near_quarter_row_quota_preflight.py` is a separate build-only wrapper for the independently approved `src/near_quarter_row_quota.py`. Existing models, the compact encoder, both earlier preflights, the compact solve wrapper and the original host guard are unchanged. No n79 work was executed by the author.

The shared scheduling adapter is `src/lazy_sat.py --near-quarter-row-quota-preflight`. The dispatcher change was coordinated with the literature agent and preserves its `--diagonal-secant-guard` route, including process-start timing, as well as all previous SAT/near-quarter routes. The final combined entrypoint hash is recorded below; it is also part of this preflight's source binding.

## Guard and complete-build semantics

The wrapper directly reuses the frozen original `guarded_process` function. The maximum ceilings remain 30 seconds and 256 MiB, and CLI values can only lower them. RSS sums the guard parent and child process group/observed descendants, including native solver allocations; the transient `ps` helper is excluded. Invalid, missing, malformed or denied required monitoring fails closed. This is a sampled kill gate with possible overshoot, not a kernel peak-allocation bound. Streaming does not bound native solver memory.

The fresh child counts full C4 line groups, then streams the entire frozen row-quota CNF into free PySAT `glucose3`, calling only `add_clause` and `delete`. There is no solve or witness path. The line-count pass and CNF pass share one budget. Child deadline checks occur between generator yields; an independent host deadline covers a generator/native call that does not yield promptly.

The separate parent SIGTERM/SIGINT context unwinds the original guard's process-group cleanup. A private alive marker plus parent-PID binding prevents startup after cancellation, and construction heartbeats recheck both. This follows the already reviewed separate compact-solve cancellation pattern without editing the original guard. SIGKILL remains uncatchable; no general guarantee is made for killing only the guard parent. The fixed child spawns no subprocesses or new sessions.

Only full CNF exhaustion, every completed insertion, stable sources and successful guarded child exit allow `complete`, `cnf_complete`, `build_complete` and a complete `model_sha256`. Native clause simplification does not change emitted/insertion counters. A host gate/exit failure, source mutation or host error clears final completion and full hash even if the child published completion first. Partial counters and a prefix hash remain diagnostic lower bounds. Construction cancellation/time expiry is explicitly incomplete. CLI exit zero means a complete build only; every incomplete/error state exits two.

## Counters and identities

`c4_line_groups` counts complete quarter-turn line orbits, including the special diagonal group; `weighted_line_groups` excludes that special group. `represented_full_lines` sums each actual orbit size, counting all original maximal geometric lines. `special_diagonal_groups` records the explicit omission justified by the retained exactly-one diagonal pair. `diagonal_guard_incidence_sum` sums distinct relevant indicators across non-special groups. These are measured generator counters; their completion flag describes only the preliminary pass.

`clauses`, `clauses_added` and `variables` count emitted clauses, completed native insertions and maximum emitted variable ID, including orbit IDs. `row_floor_clauses_algebraic` and `row_floor_literals_algebraic` are labeled closed-form metadata, not partial enumeration counters. They are respectively `m*(n-1)+1` and `m*(n-1)*(n-2)+m`, with `m=n//2`, as established in the row-quota proof.

Eight project source hashes bind the original model, line generator, verifier module, compact encoder, row-quota encoder, original guard, this preflight and shared CLI entrypoint. They are captured before spawn, checked by the child before encoder import and after full enumeration, then rechecked by the parent. The verifier module is included transitively even though build-only mode does not verify a candidate. The hashes identify project source files; they do not hash all interpreter/stdlib files or native solver binaries.

The variant-specific model hash covers sorted compact JSON containing row-quota family metadata, the full-C4 off-diagonal quotient, exceptional guards, representative row range and weighted-row-floor semantics, followed by every ordered compact-JSON clause and newline. It is deliberately distinct from earlier encoding identities and never appears as a complete hash for a partial formula. `model_header(model)` defines that exact format for future independently reviewed consumers.

## Tiny verification and host commands

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_row_quota_preflight.py -v
.venv/bin/python src/lazy_sat.py --near-quarter-row-quota-preflight \
  --n 3 --mode build --seconds 5 --rss-mib 256 \
  --output data/near-quarter-row-quota-preflight-n3.json
```

Nine tiny tests were prepared: eight pass in this sandbox and the real host subprocess test skips because `ps` is denied here. Coverage includes frozen-guard identity and limit validation; all project/CLI source identities; real native n3/n5 builds with no-solve assertions and exact 4/25-clause counts; exact formula-hash agreement with an independently assembled header/stream; full-line/group counts and algebraic floor counts; source changes before/after construction and at parent exit; host failure overriding child completion; startup zeros; cancellation/parent-loss/deadline states; CLI argument/exit forwarding; and invalid modes never falling through to SAT search. One parent/child construction test mocks only the RSS reader, so it is not actual host memory evidence.

The optional real-host test runs n3 and n5 through the combined dispatcher with the actual monitor. Root owns that host rerun, independent integration approval and any later separately scheduled 30-second/256-MiB n79 build. No larger allocation or search follows merely from the prepared command or tiny source checks. The expected large-model savings remain an algebraic forecast until the lead records an actual complete guarded build.

| Frozen artifact | SHA-256 |
|---|---|
| `research/near_quarter_row_quota_preflight.py` | `4c94335e07f93357ef153fe3582892e1918af45faa80d3d66ca441e9cd8a7244` |
| `tests/test_near_quarter_row_quota_preflight.py` | `8c2187d5040d9c4ddca854fa0182820de515727508000d2025733c82de521656` |
| Combined `src/lazy_sat.py` | `ac1b568303153c7c39f3d01fff1df7cbce36d0bfcf36951df2fe24419f73c509` |
| Unchanged row-quota encoder | `dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704` |
| Unchanged compact encoder | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| Unchanged original guard/preflight | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
