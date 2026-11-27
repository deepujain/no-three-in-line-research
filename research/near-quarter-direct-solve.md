# Explicit-threshold owned solve adapter

Status: independently approved; all 21 supervisor-run actual-host tests passed
in 0.703 seconds. Sources are frozen for the first supervisor-owned n79 trial. No n79 solve was performed by this worker. Model setting:
`gpt-6.1-sol`, reasoning `high`.

`research/near_quarter_direct_solve.py` is a separate adapter. Every historical
encoder, preflight, solver and the owned-process helper remains unchanged. The
new isolated CLI route is `--near-quarter-direct-solve`; all previous routes
are preserved. Both direct cutoffs (each 5, 6 or 7) and an expected full model
SHA-256 are required. The default/maximum guard interval remains 30 seconds
including worker construction and cleanup, with a 256 MiB sampled parent plus
owned native RSS ceiling. Preliminary parent setup and final receipt writing
are outside the helper interval, as in the reviewed preflights. The child
receives its common build/search/verification/publication deadline before launch.

The r30 supervisor-owned `(7,7)` build completed 2,193,179 clauses, 281,121
variables and 6,335,924 literals with full formula hash
`0db9f90c8b76e6b25d071598d156964e600b0b047c4c50b03cd4fe5c31ef931a`.
Its build peak was 228,752 KiB (223.390625 MiB), about 4.921875 MiB *higher*
than the preceding row-floor build. Remaining measured headroom was
32.609375 MiB. The 194,587-variable reduction does not establish that native
solve allocations or returned-model materialization fit. The build performed
no solve; its actual resource audit is saved in
`research/direct-threshold-build77-n79-analysis.md`.

The new adapter streams the exact reviewed threshold header/CNF into Glucose3
and checks the mandatory complete digest before any solver call. It omits the
preflight's preliminary support census; its own construction duration must be
measured rather than copied from the census-plus-build report. Twelve bindings
cover the original model and line generator, compact and row-floor encoders,
threshold variant, owned-process helper, old atomic/hash and decoder/witness
utilities, reviewed threshold preflight (explicit validation), verifier, new
solver source and shared entrypoint. Sources are checked before encoder import,
after build, after solve, before witness persistence, before conclusion and by
the parent before acceptance.

Result and witness semantics transfer from the independently reviewed row-floor
owned solver. Only genuine Python True/False before the deadline, with no timer
interrupt event, can support a conclusion. None is no result and integer/string
substitutes are errors. False is only restricted-family solver-reported UNSAT,
with `proof_checked=false`, not an independently checked proof or unrestricted
nonexistence result.

True requires a complete, unique, valid real orbit assignment with exactly
`(n-1)/2` four-orbits and one diagonal pair. The reviewed decoder expands the
family and both independent integer geometry checkers must accept exactly
`2*n` points. The native solver is freed after extraction and before geometry
validation. The remaining-budget timer is canceled and joined before native
destruction or changing its reference.

The immutable hash-named witness is fully written and fsynced, linked without
replacement, checked on byte-identical reuse, and its directory fsynced before
terminal publication. The parent rechecks the saved digest. A later source,
cleanup, monitor, wall, memory, cancellation or worker failure clears accepted
conclusion/result/model/witness fields, retaining only an observed witness path
for separate re-audit. SIGTERM/SIGINT remain flags through bounded cleanup.
Persistent denied monitoring/signaling can leave a live process, and the guard
never interprets that failure as success. SIGKILL cannot unwind Python.

Twenty local tests pass; one explicit host case skips. Coverage includes actual
n3 SAT/n5 scoped UNSAT, full witness re-verification and publication order,
immutable collisions, malformed models, wrong family/geometry, missing/wrong
hashes, partial streams, source changes, unexpected/None/interrupted native
returns, timer join/native free ordering, parent failure overrides, tampered
witnesses, cancellation flags, and startup/deadline checks. Extra n9 tests use
no-result stubs to exercise `(5,5)`, `(6,6)` and `(7,7)` formula counts/identity,
and verify that a mismatched threshold-pair hash cannot reach solving. API and
CLI both require explicit valid cutoffs.

After independent approval the supervisor runs:

```sh
DIRECT_THRESHOLD_SOLVE_HOST_TESTS=1 .venv/bin/python -m unittest \
  tests.test_near_quarter_direct_solve -v
```

Only after source review and those final-combined-identity tiny gates may the
supervisor allocate one n79 solve with explicit `(7,7)`, required full r30 hash,
30 seconds, 256 MiB, output path and witness directory. This adapter schedules
no run, retry, fallback or cap increase. Any actual solve outcome still needs
independent report/artifact and resource-status inspection.

## Bound implementation identities for the first n79 trial

| Source binding | SHA-256 |
| --- | --- |
| `build_preflight_source_sha256` | `4b9a4d0d07a46a9a572a54c6f6ec01b83a18ac1c6af53c01d81b4db92c9c6b92` |
| `cli_entrypoint_sha256` | `abddf7b5c2f440de4fb1e6d82cb7c8e78fdea046ff46f759af6754cadd261b9b` |
| `compact_source_sha256` | `f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1` |
| `decode_witness_utilities_sha256` | `6eac77e957bb47f69118c3f70f5530c7d4bed84621f7309359b6f466c96f1ef5` |
| `guard_source_sha256` | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |
| `line_generator_sha256` | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
| `model_source_sha256` | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| `original_guard_utilities_sha256` | `1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27` |
| `row_quota_source_sha256` | `dcd3468bcea630848a2743c7450ec5027a0df640fb9495b701f68352c23ca704` |
| `solve_source_sha256` | `c2970ad57add2fef5d724ba69e7511db8d2ccc9f8aa7a952dd861b1199478525` |
| `threshold_source_sha256` | `57a00fe19b711a184e89f6fc31ae429671d34cef42c4c21bc974dce58e0825eb` |
| `verifier_source_sha256` | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |

The approved tests are `d772d8f5861c5ae1f04ff4eb6541a55cdc53897b78cdc3f3c5a5a46cb220af81`. The first trial requires full r30 model hash `0db9f90c8b76e6b25d071598d156964e600b0b047c4c50b03cd4fe5c31ef931a`. This source-bound method record does not establish a terminal numerical result; the saved report and supervisor receipt must be audited separately.
