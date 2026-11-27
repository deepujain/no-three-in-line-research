# Independent actual audit: blocker-guided scaffold v1

**PASS for the bounded run and its reported failure. Curtail this declared gate.** The run stopped at4096 examined arc records, before any eight-arc scaffold or residual root check. It produced no149-point artifact, no157-point witness, no improvement over156 and no exclusion of the restricted pool or broader exact-D17 family.

## Fixed artifacts and identities

- Report `data/blocker-guided-eight-arc-scaffold157-v1/report.json`: `b98c5d0b4b228d3bba4f625bd1f5e40891db178cd63296f2bb0cffefedb8aea9`.
- Receipt `data/experiments/shepherd-blocker-guided-eight-arc-scaffold157-v1.json`: `1f38a57a8f0d223a2606e17a8e1bfa570c4a61bea77dedcebbee07e66975c516`.
- Audit `data/blocker-guided-eight-arc-scaffold157-v1-independent-actual-audit.json`: `828ae6c503a4fe37d8d84b39b9cddf531e747cad7fbf1adc340fdbd108b7564c`.
- Audit helper `research/blocker_guided_eight_arc_scaffold_independent_actual_audit.py`: `c2e712976923f4b04e3a292682b2a848e404d7cca2ef1f34d8a86bda6105a3e3`.

Verified all27 receipt pins,26 manifest pins, seven report pins, both historical manifests (21 and15 entries), and both accepted chain heads. Independently checked exact A/S membership, normalized hashes, degree profiles and the five complete old conflict triples. Frozen source remains `5af488fa4f857cb91325677eff67034bb2fcf6f7ed30a32e97ec018808e11b39`.

## Independently reconstructed completed preprocessing

Reconstructed outside-point blockers by solving each old-pair determinant equation at integer coordinate slices, independently of the source's normalized-direction partition.961272 slices recover55445 outside-cell/old-pair incidences and55307 nontrivial clique buckets across6083 outside cells. Their exact L values and coordinate order reproduce the saved first64 pool entries. An additional783744 direct pair determinants validate every selected point's complete blocker-pair set and direction buckets.

The saved pool matching contains24 pairwise distinct rows/columns and uses only pool edges. Its19-row plus five-column vertex cover covers all64 pool edges. Equal primal/cover cardinalities prove maximum size24 without replaying the matching algorithm. This is a necessary pool-level capacity fact, not a compatible-support or geometric-scaffold certificate.

Coordinate enumeration reproduces all246 support records. Independently checked all2016 pair-table entries using445536 old-point and pool-point determinant checks. The reconstructed supports' canonical SHA-256 is `78f575d75e81f2de64bb95fbf411540a0fc57bb1ac8d17d469cefbc549a06d88`; reconstructed pair tables' canonical SHA-256 is `d901f6448c3910cfd3ebc32c16288871fa224223b87ef1e339bf299addc2d104`. Buckets, supports and pair tables were not persisted by the run: this audit compares independent reconstruction to the pinned pure helpers and reported preprocessing counts, not to nonexistent saved table bytes.

No scaffold search was replayed, and no additional scaffold, root domain, continuation or completion search was constructed. Search counters therefore remain source-attributed, rather than independently replayed trajectory facts:4096 started/completed examined arcs,20 admissions and20 rollbacks, maximum depth seven, zero complete scaffold orderings, zero root checks and no ready artifact. Started/completed phase counts agree, the root is reported restored, and the output directory contains only `report.json`.

## Guard and interpretation

Owned wall time was0.704472249999526 seconds, sampled peak RSS49552KiB, cleanup clean. The original guard status is `worker_error` with returncode2, the implementation's expected cooperative incomplete-cap exit. It is not a normal returncode0 success. Resource/cleanup validation passed using a local copy with only status/returncode substituted for the validator; the original receipt was preserved. The25-second soft and30-second owned/256-MiB limits were not approached.

The report correctly marks `complete=false`, `closure=false` and `scaffold_search_exhausted=false`. No full pool search, matching obstruction or cycle obstruction was established.

## Continuation assessment

Recommend honoring the accepted design's stop-at-cap decision. Depth seven is a partial support prefix: old-conflict clauses, one-new blockers or forced deletions may remain unsatisfied until the eighth arc. Consequently it is not a verified150-point arrangement and does not quantify distance to an admissible149 scaffold. The20 admissions are traversal events, may include repeated orderings, and do not identify20 distinct surviving partial families. No depth-seven coordinates or resumable frontier were saved.

The subsecond run establishes resource headroom only. An unchanged deterministic rerun would reproduce the same capped prefix; raising the cap would alter the reviewed allocation without new evidence of an attainable eighth arc. Moreover, even a completed eight-arc scaffold must still pass residual matching and single-cycle gates, and these gates themselves do not establish joint residual geometry.

A separately reviewed algorithmic proposal could be legitimate new work if it supplies a concrete structural reason to improve coverage, such as a proved complete way to avoid repeated orderings while preserving requirement-driven branching. That is a design avenue, not support for allocating it now. The present7/8 counter and low runtime alone do not justify cap escalation, pool widening, reranking, extra root checks or completion work. Root retains all allocation authority; this audit grants none.
