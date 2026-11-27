# Paired early-intersection actual review

Decision: accept the complete fixed-neighborhood negative. The valid incumbent remains 156.

The run processed all 144400 raw anchored paired three-cycle combinations: 17190 cross-matching collisions, 5466 old-conflict impossibilities, and 121744 exact empty-intersection geometry rejections. There were zero witnesses. Geometry completed without an early rejection zero times, because every geometry call found a sufficient empty-intersection certificate before its full scan. This is compatible with a complete neighborhood result.

The normal owned gate exited zero, with no trigger or monitor error and clean cleanup. Outer elapsed time was 22.927218 seconds; peak sampled RSS was 47280 KiB under the 30-second/256-MiB gate. All 13 receipt source pins match current files. Report status, counters and artifact listing were independently checked. See `data/score11-paired-early-v1-independent-audit.json` and source review `research/score11-paired-rotations-early-source-review.md`.

Evidence limitation: this review independently verifies source mathematics, tiny exhaustive predicate correctness, execution provenance and count consistency; it does not independently replay the 121744 fixed-source geometry calls. The source-reviewed pinned run supplies that numerical evidence. No further allocation is needed for this closed scope. The result excludes only this fixed source, deterministic matching decomposition, anchors, and 21-row original-conflict pool; it does not exclude all six-deletion repairs or unrestricted 157/158-point configurations.
