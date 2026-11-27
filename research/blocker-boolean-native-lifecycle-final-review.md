# Fixed-pool Boolean native lifecycle and checker review

Decision: PASS for eligibility for a separately allocated, guarded fixed-pool run, subject to the stated boundaries below. This is a source and tiny-fixture review, not an allocation or an n=79 run. Geometry and encoder projection are outside this review.

Frozen SHA-256 identities reviewed:

- `research/boolean_scaffold_native.py`: `7e5afb50a90cfd89c3ccde5a7eff5c672b636f9cb7601ab710c20287a65f8efb`
- `data/fixed-pool-boolean-scaffold-runtime-pins.json`: `1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a`
- `research/boolean_scaffold_native_tiny_fixture.py`: `d3aacd15285aa561190daad7527d7071511ca184bbfc9dff0a178d8af6ffdba9`
- `tests/test_fixed_pool_boolean_scaffold.py`: `7ef77ae2237af66f71725e975a40772b7ef2eb64928728a428de05421a007c25`
- `research/fixed_pool_boolean_scaffold157.py`: `54b3271f388cc144437ba860b7e4641f1e61efe6a4b34d6e61a358ac52c9964d`
- `research/bounded_rup_checker.py`: `7f67d1b6be21c6e70e49b98e4d5c834678490e06579a1ef7b2816f608b21d152`
- `research/boolean_scaffold_cnf.py`: `0697d3367f169e4dd28e3c7a4b061c89037f418aae950d6114160783c3ba08d9`

The supervisor binds its runtime manifest by embedded digest, verifies pinned dependencies and loaded PySAT module origins, rejects unexpected optional backend imports, and rejects unknown solver results. The interpreter, standard library and OS dynamic libraries remain part of the trust boundary. The child inherits the worker session and group; signals target observed, identity-checked descendants rather than the process group, and an already reaped direct PID is not signalling authority. Cleanup uncertainty makes the child response ineligible, including before a checker launch. Sampling ancestry cannot establish absence of a detached descendant never observed; the pinned children are trusted not to detach, and the separately owned outer guard is required. Neither sampled monitoring nor the tiny run is a proof against all possible process races or memory sampling overshoot.

The child file-size limit is set before native proof creation and inherited by forks; a trace at the 8 MiB limit is incomplete. Output streams are capped at 64 KiB and the model at 32 KiB. Launch preparation is accounted for in the deadline reserve; a monitor timeout is classified as a child timeout only at the child deadline, with its observation recorded. The checker independently parses and hashes the exact CNF and proof, verifies each addition by unit propagation, and requires a checked empty clause. A raw solver UNSAT cannot establish closure. Checker limits may make an otherwise valid proof incomplete. A validated diagnostic is atomically saved immediately after the second validator, before optional root work and its fresh deadline check.

Validation: final pure suite passed 11 tests locally. The lead's approved final host tiny suite reports 14 tests passed with the frozen native, runtime, fixture and test identities above. `data/fixed-pool-boolean-scaffold-author-tiny.json` SHA-256 `419f3fc7268e3fa33afb53ee194bf2f03ef0ac862bf460d9627673ecaf34d1c6` records clean fixture cleanup and tiny SAT, UNSAT and independently checked proof binding. Its owned guard `data/fixed-pool-boolean-scaffold-author-tiny-owned-guard.json` SHA-256 `0368f2aca1cc2c14305011ddd048b97074798455bee8950c12e25858d6103e8a` records exit 0, clean cleanup, 1.856279417 seconds and 78,896 KiB peak sampled RSS under 30 seconds and 256 MiB. Host-specific tests skip only when the exact manifest is absent; a present mismatching manifest or dependency fails.

An accepted UNSAT proof applies only to the exact immutable fixed-pool formula and its restricted scaffold family. A SAT diagnostic is not a 157-point witness. Optional root readiness does not establish joint residual geometry. No actual fixed-pool SAT run was performed by this reviewer.
