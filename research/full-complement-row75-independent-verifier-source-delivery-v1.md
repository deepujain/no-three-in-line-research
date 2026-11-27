# Independent verifier SOURCE delivery

The separately authored verifier is `research/full_complement_row75_independent.py`, SHA-256 `6bad0b8ec41e4068d5015f719895949278f4ddad867f5d989ea543e79ccab1a1` (9,463 bytes). This is an implementation delivery, not self-approval of the verifier. Independent lifecycle/source review has been requested. Driver integration and any normal tiny or actual gate remain separately owned by Root.

The governing mathematical design acceptance is `research/full-complement-row75-independent-mathematical-design-review-v3.md`, SHA-256 `81404fb1eef56f420245dbb155130c1da1212b732221e42f07e432cce2a56856`, binding design `c51d400b6b61c8296560330914455ae1e246fee9a1a52a53fe810e8aa10dd397` and Root's complete cached recovery-call interpretation.

## Implemented boundaries

The verifier uses its own strict canonical shape checks and its own primitive signed direction/intercept line keys `dy*x−dx*y=intercept`. Endpoint bits use local indices for the exact complement or candidate. It does not import producer geometry, pair multiplicities or occupied-cell correction. Its only core import is the shared normalized-identity helper; the caller supplies the shared budget.

`verify_profiles` independently reconstructs each retained complement, compares every unary, checks its retained baseline, certifies selected columns against every unselected `(cost,column)` pair and checks the reported best full score. It returns coordinate-free summary counts. A line's multiplicity is recovered by one charged popcount and reused for both raw and unary contributions. Retained maps are cleared and their local owners deleted in `finally` before proceeding.

`verify_candidate` independently checks individual row loads, exact unselected points, selected columns and strict types. It then calls an adjacent-edge determinant census and the independently normalized endpoint-line census. Both must equal the prediction. It returns the normalized candidate identity and both scores. The driver must separately establish that the prediction is below the freshly authenticated baseline, choose the single globally tied winner, and bind the fixed input. The verifier neither adopts a candidate nor schedules another one.

The shared API is `Budget.charge(kind,component)`, `checkpoint()` and `check_graph(...)`. Every determinant, pair-line key, target-row intersection, popcount and cost-key comparison is charged before its arithmetic. The core combines local graph roots with bounded driver-owned roots, so a local line map cannot hide a still-live driver matrix or manifest. The verifier makes no final deadline check after both candidate validators return: Root's driver owns immediate validated-zero persistence and subsequent receipt checks.

## Permitted source evidence

Core used by the checks: `research/full_complement_row75_core.py`, SHA-256 `228a9d0dd2e52bf98f7aa8fcb50a785a15f0e4b72b7f2f66c9d7d2c1a13061b7`.

Runner: `research/full_complement_row75_independent_pregeometry_v1.py`, SHA-256 `854b4475e312cd0eb6fca3534c403fd4b5fffb0e856f72a75fd44638142bd034`.

Immutable evidence: `data/full-complement-row75-independent-pregeometry-v1.json`, SHA-256 `050063b96e03179dd927fd42f6d3f7c948cfd9ccc7fe207de1c2caafd76fa0a2`.

Results: two syntax/AST compile passes; 14 malformed profile/candidate requests rejected with zero budget charges and zero geometry-trap calls; four already-exhausted synthetic counters refused before pair coordinates, line intersection coordinates, mask popcount or raw determinant coordinates were accessed. The raw determinant sentinel test deliberately bypassed shape validation with opaque unusable objects, not a valid point state. Exact core/verifier digests match before and after. The only point literal used for schema checks was the already approved fixed n5 literal, whose canonical identity was checked without geometry. Real geometric operations: zero.

No valid n5 producer/verifier path, actual point file, optimization or alternate fixture was evaluated. These checks establish rejection and quota ordering, not normal numerical correctness or resource compliance.

## Independent primary-source finding

I separately inspected the engineer-authored `research/full_complement_row75_primary.py`, SHA-256 `2780666ac7f2a1d31e4b735135164fd4f0baf6c06b1424fb6eff405d01006e0e`. Its source correctly constructs canonical integer pair lines, recovers exact triangular multiplicities once per line, reuses m for baseline and all-grid row intersections, skips horizontal lines, corrects occupied candidates by one endpoint and clears the line map before return. Its two-best streaming selection implements the declared lexical minimum within the comparison ceiling. No mathematical source defect was found in that exact primary file. This statement does not approve the still-pending driver, source closure, normal execution or this author's own verifier.
