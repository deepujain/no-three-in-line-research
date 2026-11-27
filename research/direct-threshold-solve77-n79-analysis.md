# r31 direct (7,7) solve: negative resource outcome

The supervisor-owned first `(7,7)` solve ended at the unchanged RSS gate.
It is incomplete, with no SAT/UNSAT conclusion, no accepted model digest,
no saved or observed witness, and no mathematical absence claim. The requested
witness directory is empty. No identical repeat, larger time/cap, or alternate
threshold fallback follows from this result.

The worker published 2,193,179 emitted/inserted clauses, 281,121 variables and
8.960148 seconds of construction, then the solve phase. Its retained prefix
digest equals the required complete r30 digest
`0db9f90c8b76e6b25d071598d156964e600b0b047c4c50b03cd4fe5c31ef931a`.
Thus the report supports entry into the solve phase after the complete expected
CNF; it contains no completed solve result or solve-duration measurement.

The guard recorded 9.125634 seconds, 217 ordinary samples and 298,384 KiB
sampled peak (291.390625 MiB), return code -9, no monitor error and clean
two-sample cleanup in 0.072794 seconds. The outer receipt failed with exit 2
after 10.074332 seconds. The peak exceeded the 256 MiB sample threshold by
35.390625 MiB; this is a sampled kill gate and permits between-sample jumps.

This observed peak is 68 MiB above the preceding `(7,7)` build-only peak,
and 15.375 MiB above the previous row-floor solve attempt despite 194,587 fewer
variables. These are whole guarded-run samples, not a decomposition of native
solver data structures. They refute using the smaller variable count alone as
evidence of fit. Increasing wall time cannot resolve this observed RSS stop.

The parent correctly cleared all run/search/CNF/build completion flags and
accepted model/conclusion/result/witness fields. The full retained prefix is
diagnostic and cannot override the failed gate. All twelve source hashes match
the current frozen files; the receipt entrypoint hash matches the report.

| Bound source | SHA-256 |
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

| Saved evidence | SHA-256 |
| --- | --- |
| `data/direct-threshold-solve77-n79.json` | `876c862962bf8d5c93d2238b7217a0fecb3d7a83411dfcd5fd0d3e3d53561c41` |
| `data/experiments/r31-direct-threshold-solve77-n79.json` | `611ebbb5d2256192326cae583eb1b89e4e6058eec68fee171eac70f1c4d5fd13` |

Allocation recommendation: stop the full near-quarter Glucose encoding branch
unchanged. Retain one SAT maximum and preserve every historical source/result.
The next proposed mechanism is incremental orbit/secant state with bounded
live arrays and depth-first rollback, without a resident full CNF or learned
clause database. Only analytical and tiny state-equivalence work is currently
authorized for that mechanism; a production worker/search needs a separate
review and Lead allocation. No alternate backend is proposed without specific
resource evidence.

Analysis: Research Software Engineer, `gpt-6.1-sol`, reasoning `high`.
Only saved evidence inspection and arithmetic were performed in this audit.
