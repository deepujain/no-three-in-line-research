# Independent scaffold geometry and tiny-source review

**FINAL PASS**, restricted to the frozen implementation's scaffold-feasibility gate. This is readiness for Root to consider one separately allocated actual gate, not an allocation, actual n79 result, completed157 witness, improved lower bound, or broader exclusion.

## Frozen identities and reproduction

- Source `research/blocker_guided_eight_arc_scaffold157.py`: `5af488fa4f857cb91325677eff67034bb2fcf6f7ed30a32e97ec018808e11b39`.
- Author tests `tests/test_blocker_guided_eight_arc_scaffold157.py`: `74ea9f8c40be605cca051fe3516ecb0a5ae5eaf7be72b7cdf356fb993ff8e690`.
- Independent helper `research/blocker_guided_eight_arc_scaffold_independent_tiny.py`: `1856e2b9fece991238ab39464a3020b48f33dd55333896c9de299d7d3f4ead9f`.
- Evidence `data/blocker-guided-eight-arc-scaffold-independent-tiny-audit.json`: `9a3acc17d7fd05e75b256297fa62c2175e2dd6f4ec297d171adff4e043323ae9`.

Run `.venv/bin/python research/blocker_guided_eight_arc_scaffold_independent_tiny.py`. Separately ran `.venv/bin/python -m unittest tests.test_blocker_guided_eight_arc_scaffold157 tests.test_conflict_directed_sixteen_cycle_rebuild157 tests.test_source_disjoint_matching_rebuild157`: all48 tests passed in0.328s. The independent helper used only explicitly generated n3..6 fixtures; no actual n79 source was loaded, decomposed, scored or searched, and no completion DFS ran.

## Geometry and exhaustive tiny evidence

Independently computed collinearity with an expanded determinant formula, and computed the minimum blocker-deletion count by exhaustive deletion subsets rather than direction normalization. Compared6340 outside points and14 four-point buckets. This verifies exact blocker-pair equality and L=sum(|B|-1), including larger buckets. The pool's retained entries equal direct (L,coordinate) sorting, complete supports equal coordinate enumeration, and8525 pair tables agree with determinants.

Across383 complete tiny fixture families, exhaustively enumerated23546 arc subsets and recovered exactly the implementation's717 unique scaffolds. The constructor emitted2282 traversal orderings, including1596 nonincreasing orders. The oracle counted rejected triples in all four classes:18 old-only,30 one-new,8 two-new and22 all-new occurrences. Full determinant validity, rather than the production clause logic, decided each expected family. This exercises requirement-driven ordering, forced deletions, matching compatibility and the maximum-across-anchors bound without imposing an invalid increasing-arc shortcut. No tested family hit the4096 cap; completeness refers only to these tiny families.

For every accepted tiny family, direct sets confirm |F|=2k, |P|=|A|-k, |S-P|=2k+1 and |P-S|=k. All3565 residual-cell decisions matched outside-S checks and determinants against every scaffold pair. Residual maximum-matching sizes matched independent exhaustive injective assignments. All2476 tested component permutations expanded to old-edge cycles of precisely twice their lengths; plan coordinates restore the original axis counters and remain outside the source. Root cycle results also matched exhaustive permutations on every directed graph of orders1,2,3 (530 graphs).455 tiny scaffolds passed their residual-cycle gate.

The recorded counterexample makes the output limitation concrete: A is the four diagonal points on4x4; planted P={(1,2),(3,0)} is valid; residual domains are(2,1), with tau=(1,0) and residual plan{(0,1),(2,3)}. Each residual cell is safe against P, while their joint addition produces the collinear triple(0,1),(1,2),(2,3). Thus a complete residual matching and cycle establish only a root-ready scaffold. The implementation correctly records `is_full_witness=false`, `improves_verified_lower_bound=false` and `residual_plan_joint_geometry_checked=false`.

## Source findings and boundaries

No unresolved geometry defect found. The four exhaustive triple classes are enforced before root geometry; support matching implies distinct planted axes; F is exactly the selected supports; forced U is mandatory; and the residual full-cycle reduction is correct. The bounded top64 pool,4096 shared examined arcs and four distinct support-arc keys remain explicit restrictions. Each examined record is charged before immediate compatibility rejection. The full key includes Q's support assignment, so identical F with different Q is not silently deduplicated.

Read the final accounting revision: `save_ready` passes the shared counters into its repeated matching-cover validation; root cover traversal remains bounded by256, and certificate-edge checks including the final save are bounded by320. This supersedes the initial256 certificate-check estimate without changing geometry, selection or search caps. Detailed lifecycle findings are recorded separately by the lifecycle reviewer; the48-test run here includes interruption, rollback, cap, pin, error and late-save regression tests.

The mathematical specialization remains conditional on the fixed input gate validating A=S minus one, the exact five old conflicts and original degree profile. With k8, the scaffold has149 points,141 retained source points, eight new points and17 source deletions. Its valid149 points do not improve the verified156 baseline. Actual runtime/RSS and whether the restricted pool yields any scaffold remain unmeasured by this review. No retry, pool widening, additional root checks, completion search or automatic continuation is authorized by this PASS.
