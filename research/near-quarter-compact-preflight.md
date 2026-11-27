# Compact build-only resource preflight

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. `research/near_quarter_compact_preflight.py` builds the independently reviewed compact near-quarter CNF. The normal scheduling route is the opt-in `src/lazy_sat.py --near-quarter-compact-preflight` adapter. The original SAT path and original `--near-quarter-preflight` adapter remain available; the original compiler, compact encoder and original preflight/host guard are unchanged.

The compact runner imports the exact frozen `guarded_process` function from the original preflight. Its caps remain 30 seconds and 256 MiB; callers may lower them, never raise them. The host samples the guard parent's RSS plus the child session/group and observed descendants, including native solver memory. Empty, malformed, missing or invalid required process rows fail closed. The transient `ps` helper is excluded. This remains a sampled kill gate with possible allocation and timing overshoot, rather than a kernel allocation ceiling. The fixed worker does not spawn or re-session subprocesses; group termination covers its original process group. Streaming does not bound native solver memory.

The new worker is build-only. It counts complete C4 line groups, then streams the compact CNF into free PySAT `glucose3`. It never calls `solve` or `solve_limited`, returns no SAT/UNSAT result and deletes the solver after construction. `clauses_added` counts completed `add_clause` calls before native simplification. Partial counters are last-published lower bounds, not final model sizes. No resume is implemented.

## Reports and provenance

Reports distinguish these counters:

- `c4_line_groups`: full C4 line orbits, including the special main/anti-diagonal group.
- `weighted_line_groups`: non-special groups whose shared off-diagonal/conditional diagonal capacities are compiled. Some can be tautological.
- `represented_full_lines`: sum of full orbit sizes, counting every original maximal geometric line.
- `special_diagonal_groups`: omitted diagonal groups justified by the retained global exactly-one diagonal condition.
- `diagonal_guard_incidence_sum`: distinct diagonal indicators summed across non-special groups; this is not a unique-variable count.
- `clauses`, `clauses_added`, `variables`: observed emitted clauses, completed native insertions and maximum variable ID, including the orbit-variable range.

`c4_line_groups_complete` describes only the first count pass. `cnf_complete` and `build_complete` require full CNF exhaustion and insertion. The line/group generator is visited twice under the same gate. A terminal timeout, RSS limit, monitor failure, worker error or source mutation overrides child completion and clears the final completion flags and complete model hash. Prefix hashes and lower-bound counters remain diagnostic only.

The parent captures five source SHA-256 values: original model, original line generator, compact encoder, reused host guard and new compact preflight. The child checks all five before encoder import and after complete enumeration; the parent checks them again after exit. The successful `model_sha256` hashes the sorted compact JSON header containing compact family metadata, full-C4 off-diagonal quotient and explicit exceptional-guard flag, followed by each ordered compact-JSON clause and newline. The report therefore identifies the actual source and complete formula in addition to the supervisor's separately recorded CLI entrypoint SHA. It does not hash the interpreter or native solver binary.

## Tiny tests and review gates

```sh
.venv/bin/python -m unittest discover -s tests -p test_near_quarter_compact_preflight.py -v
.venv/bin/python src/lazy_sat.py --near-quarter-compact-preflight \
  --n 3 --mode build --seconds 5 --rss-mib 256 \
  --output data/near-quarter-compact-preflight-n3.json
```

Ten tiny tests were prepared. Nine pass in this subagent sandbox; the real host subprocess test skips because `ps` is denied here. Coverage includes exact frozen-guard reuse, ceiling validation, source changes before/after enumeration, host failure overriding completed child output, startup zero counters, complete native n3/5/7 counts and hashes matching the compact stream, executable no-solve assertions, exact CLI forwarding and invalid compact inputs never falling through to ordinary search. A parent/child n3 test mocks only the host RSS sampler; it is construction evidence, not real RSS validation. The separate optional subprocess test runs the scheduling adapter with the real host sampler.

Root observed one transient `EPERM` host startup failure during an earlier full-suite run of the original preflight dispatcher. That report failed closed with zero work and no completion. The original three dispatcher tests then passed in an isolated host rerun. No guard was weakened. Root subsequently passed all 136 host tests and the tiny real compact CLI. The independent mathematician approved this integration in `research/near-quarter-compact-preflight-review.md`. No n79 preflight or search was executed by the author.

The original n79 construction remains saved under its original encoder and guard hashes and stopped at the unchanged memory gate. Root separately scheduled the compact n79 build after approval and host checks. `data/near-quarter-compact-preflight-n79.json` reports complete construction under the unchanged gate: 2,300,453 clauses, 591,304 variable IDs, 14.522 seconds and 257,776 KiB sampled guard-plus-worker peak over 331 samples. It reports no solve. The remaining measured headroom is only 4.265625 MiB; this does not establish that native solving or model decoding will fit. Any search needs a separate reviewed wrapper and separately scheduled guarded allocation.

| Frozen artifact | SHA-256 |
|---|---|
| `research/near_quarter_compact_preflight.py` | `a4d94e8efe9a9fa33ffc4194b829c85d47a975b0dda6073e1139af19758b280a` |
| `src/lazy_sat.py` | `6b2a3409ade12ce10b79247b703b1add1f4c8350642033aace375db75096bf18` |
| `tests/test_near_quarter_compact_preflight.py` | `37b80a3c7b688413663d9f83c87f00ad87d5d256228217e062180711866cc7fe` |
| Unchanged `src/near_quarter_compact.py` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| Unchanged `src/near_quarter_model.py` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| Unchanged `src/line_model.py` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
| Unchanged `research/near_quarter_preflight.py` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
