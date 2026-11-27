# Guarded diagonal-reflection DFS

The opt-in `--diagonal-secant-guard` route in `src/lazy_sat.py` starts a separate DFS process group. The wall budget starts at entrypoint module startup, covering imports and job setup. The guard samples parent plus child group and descendants using the existing reviewed `process_rss_kib`, with ceilings of 30 seconds and 256 MiB. RSS sampling can overshoot and excludes the transient `ps` helper; polling and process creation or cleanup can also exceed the nominal wall deadline. It is not a kernel resource cap. Monitoring errors, host cutoff, source changes and SIGTERM override a child exhaustion report. On SIGTERM the guard kills and reaps its child process group. The fixed DFS worker does not create descendants or new sessions.

The guard records hashes of the core, verifier, guard, shared RSS monitor, and CLI entrypoint, checks them in the worker before import and before publishing each witness and terminal state, and checks them again in the guard. These are change checks, not immutable execution snapshots: changing a source and restoring its bytes between checks cannot be detected. Verified certificates are atomically published as individual files in a unique run directory with source hashes in their metadata; the report is atomically replaced. The initial report names the witness directory, permitting witness recovery on interruption. An interrupted or unvisited slice cannot establish exhaustion, and completed slices only cover the declared reflection family.

Validation: `.venv/bin/python -m unittest tests.test_diagonal_secant_dfs tests.test_diagonal_secant_guard tests.test_near_quarter_preflight_dispatch tests.test_near_quarter_compact_preflight tests.test_near_quarter_compact_solve tests.test_lazy_sat -q` ran 41 tests successfully, with three skips. The guard tests include n=3 and n=5 child searches with mocked RSS readings, independently reverified certificates, monitor denial and RSS cutoff, SIGTERM reaping, expired setup deadline, limits and dispatcher forwarding. A real n=3 CLI attempt failed closed with `monitor_error` because this sandbox denies `ps`; real host RSS and CLI validation remain outstanding. No n=79 execution or benchmark was performed. Independent guard review is pending.

Frozen SHA-256 for review:

- guard: `073bd74fd2eb200c86b5effb5e7b4baea8712a354913604d0a7d3ba395ce3328`
- guard tests: `3683f472c915e305f2f764685128c881ca6196b7b36e426edfc4a111d7b86847`
- `src/lazy_sat.py`: `845d6b0ff1f7617e2469d07c7cf4dddb875c80f709fb3511ec4676514359a327`
- unchanged core: `6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7`

Review-driven revision: imported `run` starts a fresh clock; CLI passes its startup clock. The first detected external failure is retained, and source stability is separately recorded. Eleven core and guard tests passed after adding source mismatch before import and after search, verified witness publication before terminal state, and RSS, monitor, wall and source failures overriding an already published completion. The entrypoint hash above predates a separately coordinated dispatcher change and must be refreshed after integration.
