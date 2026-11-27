# Independent corner-anchor mathematical review

**READY / APPROVED** for the unchanged `research/embedding_worker.py` to consume the three size-two origins 10296, 10297 and 10298, each with its separately declared durable tip. No blocking correctness finding remains. The shepherd has since started these approved streams; this review does not certify any of their later numerical outcomes.

Reviewer configuration: `gpt-6.1-sol`, reasoning `high`. No author source was modified. This review performed source inspection, read-only exact metadata reconstruction, tiny correctness tests and zero-case worker/tip exercises. It ran no actual 79-grid deletion or addition cases and no benchmark search.

## Mapping and provenance

The cut map is `x -> x+(x>=cut_x)`, `y -> y+(y>=cut_y)`. With cut `(0,0)` and source coordinates in `0..77`, every point is translated by `(+1,+1)` into the 79-grid. I independently compared this explicit translation with the engine's insertion map for the complete source point list.

Both independent exact geometric verifiers accept the original 156-point n=78 seed. The manifest and every reviewed origin use its canonical n+sorted-points hash `e197d1b41f97df9188b9839a54f0013bbc08b67d202c18d26146a7f377d80ced`. Their ordered-source hash is `e7678d82888f177d779c4ca250d6cda995645a13e0c102b5727138a835c0c9bb`, independently recomputed from compact sorted-key JSON of the original n and point list in input order. Translation preserves those source indices. The canonical hash identifies the geometry while the ordered hash binds numerical resume offsets to the actual indexed source order.

The additional-origins sidecar binds the unchanged manifest by raw-file hash. I independently checked that hash and all three recorded origin-file hashes.

## Exact coverage argument

The translated source is valid. For any empty candidate cell c, directions from c partition old points. Each group contains at most two old points, because three would already be an old collinear triple. Consequently its blocking pairs are disjoint. To insert c, an old deletion set D must hit every blocking pair. If |D|=5, c can therefore have at most five pairs.

Choosing, for each blocker, one endpoint that lies in D yields an endpoint cover C contained in D. The helper enumerates every endpoint choice for every eligible c, deduplicates covers, then retains their inclusion-minimal antichain. Every raw cover contains a retained cover A, so D contains A. The corresponding stream enumerates every exact-five superset of A via lexicographic combinations of increasing non-base source indices. Hence every useful exact-five deletion set is represented. Any cardinality-improving repair must insert at least one genuinely new cell outside the original 156 points, even if it also readds removed old points, so this necessary-anchor argument covers all such repairs.

Being represented by an anchor is only a necessary search condition. It does not assert that the five deletions admit six compatible insertions or yield 157 points. The existing worker still exhausts the appropriate addition subsets and checks their geometry.

## Independent finite metadata checks

I reconstructed all empty-cell direction groups and checked their size-at-most-two property. For every one of the 410 eligible cells, I independently enumerated all old-point pairs and used integer cross products to verify the exact blocking-pair set. Each cell's pairs were also checked disjoint. All 10,440 endpoint covers were regenerated, and inclusion minimality was independently computed by testing every proper subset against the raw-cover set. The resulting antichain agrees exactly with all 10,304 manifest anchors.

The retained sizes are 8 of size two, 224 of size three, 1,936 of size four and 8,136 of size five. Every index is a distinct ordinary integer in `0..155`. Every recorded stream size equals `C(156-|A|,5-|A|)`. The summed 7,682,312 cases are explicitly duplicate-counted, not a distinct-deletion total.

Beyond the author's three focused tests, an independent tiny combinatorial check examined all 1,023 nonempty families of disjoint-pair matchings on four labels, and all 16 deletion sets for each family: 16,368 direct hitting-condition versus antichain-representation comparisons, all agreeing. The author's three frontier tests and the existing worker's five tests passed. The latter include subprocess restart, stale-origin handling, hash/gap/history rejection, relocated chains and immutable records.

## Origins, overlaps and safe resume

The manifest initially prepared only origins 00000..00002, each a one-case size-five frontier. The sidecar adds only the following three size-two frontiers; it does not claim all 10,304 origins have been prepared or searched:

| Origin | Base indices | Exact-five cases | Origin SHA-256 |
|---|---|---|---|
| corner-exact5-anchor-10296 | [40, 52] | 596,904 | `cfe2a8f5c385d7c7678be75c76393898adc2be3d03c868801e7c6047ec9ddeb0` |
| corner-exact5-anchor-10297 | [40, 88] | 596,904 | `9b7e9ce274926002bb475545f86303883fd252351f7c7ae9bff9e87e87ef45a7` |
| corner-exact5-anchor-10298 | [52, 70] | 596,904 | `327798e274d10d6d7eef59fafa2c97ef8d7f57d778c4031c8af82872b6875001` |

All three load successfully through the unchanged `load_gapless_chain`. Each records cut `[0,0]`, exact deletion count five, ordinary-integer `start_offset=next_offset=completed_deletion_sets=0`, the expected enumeration order, and `C(154,3)=596,904` total cases. I exercised `run_worker` on each with zero seconds and zero cases using separate temporary tips, loaded the tip, then resumed from the origin again. Every check retained offset zero with no deletion cases executed. Attempting to reuse one anchor's tip for another frontier was correctly rejected.

The numeric offsets are safe Python integers and all current values are also far below the exact-integer range limit of common JSON consumers. The worker advances an offset only after finishing every addition subset for that deletion set; an interrupted case is retried rather than falsely recorded complete. Immutable offset records form a hash-checked gapless chain from zero, and each declared durable tip has its own nonblocking file lock. Different anchors require different tips.

Cross-anchor overlap is real and explicit. For bases `[40,52]` and `[40,88]`, the exact-five intersection has `C(153,2)=11,628` sets. The same count applies to `[40,52]` and `[52,70]`; the third pair overlaps in `C(152,1)=152` sets, and the triple overlap is also 152. Thus these three complete streams would cover 1,767,456 distinct exact-five deletion sets, while their summed individual counts are 1,790,712. No summed count should be reported as distinct coverage. These overlaps affect efficiency, not completeness or correctness.

## What remains unperformed

I did **not** replay the 7,682,312 duplicate-counted exact-five cases or their addition subsets, execute any of the three 596,904-case frontiers, validate future stream records, or infer absence of a repair. Only the declared limited origins were prepared, and only their zero-work consumption/resume contract was exercised here. Full family closure requires the manifest's complete retained-anchor coverage to be discharged by valid gapless streams, with overlap handled honestly. Active or partial streams do not close the family. Existing checkpoint hash chains protect record integrity and offset continuity; this review is not an independent replay certificate for future numerical enumeration.

## Reviewed artifact hashes

| Artifact | SHA-256 |
|---|---|
| `research/corner_anchor_frontier.py` | `a16090f7f146f1cc9e6b2b93e16795afc3d02b01f07096bb13b1c44488f03916` |
| `tests/test_corner_anchor_frontier.py` | `e897c66a000fd6e990e40df6a320f3debcdc147f50e4383594d4c40fe9f0c879` |
| `research/embedding_worker.py` | `dbb412aa9bd83d56b7ba331f97097b5549bded8131a0811de8cdcba4883a2292` |
| `data/corner-anchor-frontier/manifest.json` | `e45bfeaed19f5b519a8cdda3ab411bbf874ca365903d46c7cadd802ab64137a1` |
| `data/corner-anchor-frontier/additional-size2-origins.json` | `a16ca745b4788a88cb7b0b9a4014fe6f664558c20ea69e7a1a4b20e9ec9aeb3e` |

Approval was sent to the shepherd immediately after origin validation, before this document was finalized. No queue or supervisor file was edited.
