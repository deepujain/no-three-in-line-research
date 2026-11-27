# Independent Boolean scaffold encoding/geometry source review

**FINAL PASS for encoding and geometry on the exact versions below.** This is not a native backend/process eligibility PASS or an actual-run allocation. Runtime/lifecycle review belongs to the separate reviewer; native eligibility was unverified when this review began. The engineer has announced a pending orchestrator/runtime contract revision, which requires a separately pinned delta review before this PASS can cover that revised version.

## Reviewed identities

- Encoder `research/boolean_scaffold_cnf.py`: `0697d3367f169e4dd28e3c7a4b061c89037f418aae950d6114160783c3ba08d9`.
- Orchestrator `research/fixed_pool_boolean_scaffold157.py`: `86f24958bae78cab9fffe3e1d92fd66706a22b13c5c43462433bde532b18ca87`.
- Author tests `tests/test_fixed_pool_boolean_scaffold.py`: `91987cb9996814b7c6d5ed9fbe710d044ac1a8d0c6034deea92fd8a459d5ce4c`.
- Independent determinant oracle `research/boolean_scaffold_independent_tiny_oracle.py`: `05b24e11bb8f64e4ec0b1fc1aa4e07182b6ef449f2a77912d1304f950ce0136f`.
- Independent audit helper `research/boolean_scaffold_cnf_independent_tiny_audit.py`: `c2cf4528bfdd7cea19d43d2f7210408ed6c0ba3f3fc4916506dcea2a5a1d7281`.
- Evidence `data/boolean-scaffold-cnf-independent-tiny-audit.json`: `89e1721c8d4b7f2a51bc2f5b0b0ec8ea38a48c2b44d45f39ae3cd8f2e93f0b0d`.

No fixed n79 loader, n79 pool reconstruction, n79 CNF or native solver/checker process was invoked by this reviewer. All executed geometry uses synthetic boards of at most six rows. Native calls in the two orchestrator tests were fully stubbed. The author pure-test subset contains direct in-process proof-parser unit tests; running them does not constitute an independent proof-checker/native eligibility review.

## Independent tests and results

Ran `.venv/bin/python research/boolean_scaffold_cnf_independent_tiny_audit.py` successfully. Its inputs are constructed from coordinates and determinants, without production preprocessing: complete old blocker-pair graphs are partitioned into cliques, support choices are enumerated by coordinates, and pair-table masks/old triples are computed directly. It uses the accepted independent determinant oracle for semantic validity. Frozen scaffold classes provide data containers only.

The emitted projection matched all5320 support subsets across113 tiny formulas, recovering exactly488 valid scaffolds. Rejections exercise all four triple classes:14 old-conflict,20 one-new, four two-new and five all-new failures. On small support catalogs, all3169 Boolean x assignments were checked, including incorrect cardinalities. All488 valid models round-tripped through the production model parser and full clause verifier.

Exhausted17444 assignments to local q/d union identities, including unused cells and both truth values of each output. Each identity admits exactly the OR of its support variables. Independently exhausted44356 complete counter assignments across ten threshold formulas through four inputs, proving exactly one auxiliary extension when the selected count is k and no extension otherwise. Additionally14532 single-bit mutations of valid semantic/counter auxiliaries were rejected. All12241 examined emitted clauses have valid literal domains, no duplicate literals and no remaining tautologies.

Two fully stubbed SAT pipelines each invoke the native-call stub exactly once, produce an independently valid tiny diagnostic, and perform at most one residual gate. One reaches root-ready with individually safe residual cells whose joint addition is invalid; metadata correctly keeps full-witness/improvement/joint-residual claims false. The other has residual matching size one instead of two, preserves the valid diagnostic, emits no root-ready artifact and does not request another model. Both streamed DIMACS files were independently parsed and checked for header, variable range, clause/literal counts, model satisfaction, exact clause agreement and SHA-256 binding.

Separately ran `.venv/bin/python -m unittest tests.test_fixed_pool_boolean_scaffold.PureTests tests.test_boolean_scaffold_independent_tiny_oracle`: all14 tests passed. This includes malformed-model rejection, stream/hash/count checks, write cleanup, pin rejection before a mocked spawn, and saving a late completed diagnostic before a fresh root deadline check. No NativeTinyTests were run by this reviewer.

## Source conclusions

The threshold recurrence implements z iff a OR(x AND b) in all four directions, with correct true/false base constants and exact-k assertions. q and d definitions are bidirectional. Pair incompatibility uses both complete endpoint-row masks and endpoint-column masks, so shared endpoints and distinct supports sharing only an axis are forbidden. The four geometry groups correctly encode old triple hits, old blocker pairs for selected q, forced old deletions on selected q-pair lines, and all-new collinear triples. The k>j condition emits each all-new triple once.

The reverse d implication prevents false free deletions. The reverse q implication fixes exact planted-point semantics and unique assignment extension; without it, extraneous true q values would add restrictions because q appears negatively in geometry clauses, rather than create a false existence witness. The implementation correctly includes both reverses.

The declared maximum layout is2645 variables. Clause/literal/text caps match the accepted conservative bounds89957/237112/1602603. The writer streams a temporary body, writes the exact header, hashes the completed file and cleans partial output on exceptions. The parser requires exactly one signed assignment for every variable and the verifier replays every clause before extracting selected arcs. These checks validate a candidate model; mathematical UNSAT scope still additionally depends on a correct complete encoder, exact immutable input binding and an independently checked proof for that CNF.

Source inspection confirms `load_fixed` takes the64 points from the pinned accepted report, reconstructs only64 partitions, checks their saved L values/histogram, directly verifies the existing matching/cover certificate, reconstructs246 supports/2016 pair tables and requires the accepted canonical hashes. It neither calls whole-grid pool construction nor either DFS constructor. The loader was inspected, not executed during this review.

SAT decoding reconstructs F/Q and all source/count/axis invariants, performs both full validators, and immediately persists the valid diagnostic. The optional root begins with a fresh deadline check and applies complete residual domains, matching/cover and single-cycle checks only to that one scaffold. Root readiness remains a separate label, with no claim that the residual cells are jointly valid. The selected fixed pool remains a restriction; no149 diagnostic improves the156 baseline, and no model here is a157 witness.

No unresolved mathematical or encoding defect was found in these frozen versions. This review does not certify native process containment, solver backend pinning, proof-cap enforcement, independent proof-checker soundness or actual n79 resource behavior. Those gates remain separate, and the announced runtime revision cannot inherit this source pin silently.
