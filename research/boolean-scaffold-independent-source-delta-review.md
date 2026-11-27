# Final Boolean scaffold source delta: encoding/geometry review

**FINAL PASS for encoding/geometry on the final orchestrator revision.** This completes the pending mathematical delta gate from `research/boolean-scaffold-cnf-independent-source-review.md` (`a2bc4993e9ce72c668af99a5467291b714f1003ec618c50a47f5f625f3f12372`). Native/backend/process/proof-checker eligibility remains a separate review; this document neither grants that eligibility nor allocates an actual n79 run.

## Final identities

- Encoder unchanged: `research/boolean_scaffold_cnf.py`, `0697d3367f169e4dd28e3c7a4b061c89037f418aae950d6114160783c3ba08d9`.
- Orchestrator: `research/fixed_pool_boolean_scaffold157.py`, `54b3271f388cc144437ba860b7e4641f1e61efe6a4b34d6e61a358ac52c9964d`.
- Native module recorded for binding, not independently certified here: `research/boolean_scaffold_native.py`, `5044156ab6916f227f534487c2291d62557248ce9c0305fc4b43436242a8a61f`.
- Updated author tests: `tests/test_fixed_pool_boolean_scaffold.py`, `f58bad41d05b00e2681a1e445fa9325c9b4116fc3e711970a4bb467417884779`.
- Independent delta helper: `research/boolean_scaffold_independent_delta_audit.py`, `39cef2fd0346850976b6ff609f16b9066fd2d09e11421954dcdec7596cb30c48`.
- Delta evidence: `data/boolean-scaffold-independent-source-delta-audit.json`, `bb0426106603866d60a0d7c2279a29ed8510f371eb6099b0888b2249b2b9b423`.

## Exact change and independent verification

Reversing exactly three announced text replacements in the final orchestrator reproduces the previous reviewed SHA-256 `86f24958bae78cab9fffe3e1d92fd66706a22b13c5c43462433bde532b18ca87`: SAT and checker calls now pass `latest_end=deadline-3` and `latest_end=deadline-1`, respectively, and runtime loading calls `native.runtime_contract(runtime_manifest)` instead of reading arbitrary JSON directly. This hash recovery verifies that no encoding, fixed-pool loader, model-decoding, scaffold-validation or residual geometry code changed.

Source inspection of the new runtime-contract boundary confirms that it requires the reviewed runtime manifest hash and verifies its pins and interpreter/backend identity. Whether native enforcement, import binding, process containment and proof checking are adequate remains with the independent lifecycle reviewer. The mathematical effect of the delta is to preserve reserved wall-clock intervals and strengthen runtime identity, without changing the fixed-pool formula or its result scope.

Ran the new delta helper successfully. It independently checks the exact source recovery, unchanged encoder and three fully stubbed tiny execution paths. A valid root-ready scaffold still saves a separate diagnostic and retains the explicit jointly-unchecked residual label; the supplied residual plan remains individually safe but jointly invalid. A matching-obstructed first model saves its diagnostic, emits no ready artifact and makes no second SAT call. A genuinely contradictory tiny encoding (two arcs required, only one available, hence an empty CNF clause) exercises the UNSAT/checker binding with both native calls stubbed. The call arguments are exactly10 seconds/latest_end22 for SAT and five seconds/latest_end24 for the checker under a25-second synthetic clock. No native process is launched by these tests, and the stubbed checker acceptance is not proof-verifier certification.

Ran `.venv/bin/python -m unittest tests.test_fixed_pool_boolean_scaffold.PureTests tests.test_boolean_scaffold_independent_tiny_oracle`: all17 tests passed. No NativeTinyTests or fixed n79 loader was run. The full earlier independent encoding evidence remains applicable because encoder and geometry bytes are unchanged:113 formulas,5320 support subsets,488 valid models,3169 complete x assignments,44356 counter assignments,17444 union-identity assignments and14532 rejected auxiliary flips.

All prior review/helper/evidence files were preserved byte-for-byte, including independent evidence `89e1721c8d4b7f2a51bc2f5b0b0ec8ea38a48c2b44d45f39ae3cd8f2e93f0b0d`. Its historical stub signature targets the previous API; the separate delta helper explicitly tests the new keyword arguments without rewriting that evidence.

No unresolved encoding or geometry defect was found. This PASS concerns the exact fixed-pool projection and single-model artifact semantics, not native eligibility, actual n79 performance, a149 construction, an improved156 bound, a157 witness or a new exclusion claim.
