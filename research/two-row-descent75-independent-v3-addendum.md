# V3 scan-completion state: independent addendum

Decision: PASS for the narrow v3 source delta and independently rerun mathematics/controller suite. This addendum supersedes the v2 source binding for those conclusions; it does not replace or modify v2 evidence. No actual input coordinates or n75 geometry were read.

Bindings:

- Frozen v2 `research/two_row_descent75_v2_frozen.py`: `e122a497bf2da967c4b35cc043f4a13febbd781a8e7baca9d81cda7f2dfcda41`.
- V3 `research/two_row_descent75.py`: `0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c`.
- Supplemental helper `research/two_row_descent_independent_v3_audit.py`: `1e19a82fe9f98921dcc5a37fd0578401bb36de273d5f4062a6eb3d43c4505504`.
- Supplemental evidence `data/two-row-descent-independent-worker-audit-v3.json`: `31fb5234b299a9ef27a02a4ff449747a0f847d5d1faa044e6d30121a0c551689`.
- Preserved v2 review: `288f89059aefaf273e4ce395a81e5c66163428544c64da393767b70327472be5`.

An exact source transformation assertion confirms the sole delta: both positive and zero acceptance updates now set `row_sweep_complete=False` and `pair_scan_complete=False` before invoking commit. The event retains its old-state scan fields. Therefore a save callback failure cannot return a newly accepted state's identity with an old-state completed-row-sweep claim. A final zero similarly receives no stale scan claim. Geometry, minimum ordering, caps, validation and handoff source are unchanged by this delta.

The supplemental helper reran the complete frozen independent suite bound to v3:3541 states and policy traces,14075 row optima,20983 pair optima,874573 direct assignments,333979 cross entries,672 partner minima,27 shared-cap traces, and404 cooperative-check interruptions all pass. The original helper is not edited; its source hash remains the nested comparison identity, while this supplemental helper records the explicit v3 rebinding. Both v2 and v3 source hashes were checked before and after execution.

Three focused regressions compare v2 and v3 events and results. A genuine n4 two-row escape ending at zero was run both normally and with an `OSError` commit callback. The accepted pair and score were identical; v3 clears scan flags on the new state while preserving the event's old-state `row_sweep_complete=True`.

The third case uses the n4 state `{(0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3)}`, raw U5. A disclosed Stage1 control stub returns current to reach Stage2. Real pair optimization chooses rows0/1 and obtains U1, and the production full-index rebuild verifies that positive improvement. When commit raises `OSError`, v3 returns `status=error`, U1, accepted1, exact newly accepted points and both scan flags false. V2 retains the incorrect row-complete flag. The recorded event still truthfully describes the old state's completed row sweep under that stubbed orchestration. This is not a genuine full-policy positive pair trace; only Stage1 selection is stubbed, while pair geometry and rebuilding are real.

The original positive completed-no-improvement terminal remains control-stub-only. No genuine positive full local-minimum fixture, actual endpoint recount or neighborhood exclusion is established. A positive incumbent remains an invalid construction; actual receipt, lifecycle and owned-resource acceptance are separate gates. The independently recounted trajectory design protocol remains unchanged.
