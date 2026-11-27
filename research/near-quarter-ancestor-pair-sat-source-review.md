# Three-ancestor pair SAT source review

Decision: PASS for one separately allocated bounded main-depth18→17→16 job. No actual ancestor geometry or solver experiment was performed by this reviewer.

Reviewed source: `research/near_quarter_ancestor_pair_sat.py`, SHA-256 `44b9fce2379ad35ce96aab54dae42d4f68a3800f0ef07e47849760ec8f1ae8c3`.
Reviewed tests: `tests/test_near_quarter_ancestor_pair_sat.py`, SHA-256 `64b008da98582edae546765c8c054e785de72e2630bbd82019734cfc8555fae2`.
Frozen base helper remains `08c5b8532666145cb890fae7daf4b62960a09a28e6f8c17536984c6c4b4c70f3`.
Independent combined tests: all21 cases passed in0.060 seconds.

The worker verifies the accepted main19 pair audit and immutable checkpoint path before slicing exactly three parent prefixes. Each stage recomputes its own complete mask, rejects rather than truncates masks above200, reconstructs a fresh private state, and completes all m(m-1)/2 pairs before solver construction. Degree demands and retained point counts are checked dynamically, and target orbit counts21/22/23 are explicitly forwarded. Dynamic degree construction has fail-closed ceilings2000 variables/4000 clauses/10000 literal entries. Old pair cuts are not imported.

One absolute deadline starts before evidence reads and is shared by every stage and its timer. Each solver is destroyed only after its timer is cancelled and joined. Only an unexpired native UNSAT response advances to the next stage; unknown, mask capacity, degree shortfall, cut limit, timeout, or witness ends the job. The report preserves previous completed stage evidence and leaves untouched later stages unstarted. A later timeout cannot upgrade an earlier partial stage. No fourth depth or original-frontier mutation is possible through this CLI.

The new model loop checks exact degrees, selected orbit count, distinct points and target158, uses streamed exact determinant cuts mapped to three distinct primary variables, rejects repeated cuts, and imposes1000 cuts per depth. Both exact validators must agree before immediate atomic witness persistence. A verified witness is saved without a later soft-deadline check, under the external hard guard. Input hashes and source manifests are checked again before the report is saved.

The inherited tests cover independent tiny geometry and degree projection, rollback/interruption, pair completeness, and timer cleanup. Added adapter tests exercise the actual new solve loop for unknown/late results, bad triple followed by UNSAT, cut limit, repeated cut, malformed model, late witness persistence and dual-validation failure. A mocked end-to-end worker run uses real pinned checkpoint parsing but no large geometry: it checks three distinct private states, target counts21/22/23, common deadline25 with timer remainders25/24/23, all timer/solver cleanup sequences, and rejection of an incomplete pair census before any solver construction. Coordinator tests cover every non-UNSAT stop and retained earlier evidence.

Any successful negative result remains solver-reported and conditional on the exact per-depth retained prefix. No independent UNSAT proof, global board bound, automatic DFS integration, or broader allocation is implied.
