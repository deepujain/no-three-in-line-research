# Main-depth-19 pair SAT actual review

Decision: accept **conditional solver-reported UNSAT for this fixed near-quarter prefix**. No independent UNSAT proof or solver replay was performed.

The guarded job completed cleanly in 0.533485 seconds at 58,416 KiB sampled peak RSS. All 34 receipt source pins, the current packed manifest, local source hashes, and the two accepted checkpoint heads match. The prefix matches previously independently audited main-depth-19 evidence.

Independent quarter-turn orbit generation and exact integer geometry reproduced the 78 retained points, complete 102-orbit admissibility mask, and its SHA-256 `2f18269cb333278f6b6d6459eb653ce886544f797e4adabbbf8f5cab472b3173`. All 5,151 pair decisions were independently recomputed, without packed geometry or readonly probe helpers. Exactly 1,445 pairs are incompatible and 3,706 are compatible. Every rejection has an explicit saved witness: 380 row-capacity violations and 1,065 integer-determinant collinear triples. The independently derived exclusion list equals the reported list exactly.

Independently reconstructed radius demands and incidence yield the reported 555-variable, 982-clause, 2,282-literal degree formula using the same pinned cardinality library. Adding all binary exclusions gives 2,427 clauses and 5,172 literal entries. The native solver returned UNSAT without a model, ternary cut, or witness. Thus pair geometry adds an effective rejection at a prefix where the previous pure degree-factor relaxation was satisfiable. This is a useful local result, not evidence that broad integration pays off everywhere.

Audit: `data/main19-pair-sat-v1-independent-actual-audit.json`, SHA-256 `4c736f3cce8914d23a9b687cb810880b57cb13498cda23b0a944407729cfe9b4`.

The scope remains all near-quarter completions retaining this exact main-depth-19 prefix. No frontier was mutated and no unrestricted board bound follows. Further ancestor exploration requires its own bounded implementation and source/tiny-test review.
