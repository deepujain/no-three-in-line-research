# Fixed-prefix pair SAT source review

Decision: PASS for one separately authorized bounded main-depth-19 experiment. This review does not allocate or run that experiment.

Reviewed source: `research/near_quarter_prefix_pair_sat.py`, SHA-256 `08c5b8532666145cb890fae7daf4b62960a09a28e6f8c17536984c6c4b4c70f3`.
Reviewed tests: `tests/test_near_quarter_prefix_pair_sat.py`, SHA-256 `72e0a106b17d1e726c5a3712bb28ac7f59aaa36e1f32ef34a9be0c9a270ab03c`.
Independent verification: all 13 unittest cases passed in 0.160 seconds; both byte hashes match.

The 78-point retained prefix and complete 102-orbit mask are pinned and freshly reconstructed. All 5,151 pair checks must finish before constructing a solver. Pair probing restores private geometry; an interrupted push cannot return a completed pair census. Exact radius demands use one shared auxiliary-variable pool and the expected 555-variable, 982-clause degree formula. Primary-variable model decoding checks degrees, 20 selected orbits, distinctness, and 158 points.

Pair cuts exclude conflicts involving at most two new orbits. The streamed exact determinant separator maps every remaining conflict to three distinct new-orbit variables and adds only its necessary negative ternary clause. Duplicate cuts are errors; 1,000 cuts is an incomplete cutoff. Native UNSAT is solver-reported and restricted to this fixed retained prefix; it is not a global bound or independently checked proof.

Timer firing, deadline exhaustion, or a None solver response cannot become UNSAT. Cleanup cancels and joins the timer before deleting the native solver. A candidate passing both exact validators is immediately persisted atomically without another soft-deadline check, as explicitly required; the external hard guard bounds this tail. Pinned inputs and source manifests are checked again before final reporting. No original frontier is mutated.

The tests cover tiny independent pair geometry, cardinality projection, rollback and push interruption, incomplete pair-census rejection, actual pinned prefix parsing, bad-triple cut insertion, repeated cuts, invalid model degrees, cut limits, interrupted/unknown solver results, late valid witness persistence, dual-validation failure, and timer teardown ordering. No actual large-prefix pair enumeration or solver run was performed by this reviewer.
