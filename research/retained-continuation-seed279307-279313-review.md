# Independent four-job retained-walk continuation audit

All four pool receipts report terminal exit 0. I checked the pinned source/input hashes against current files, exact arguments and initial-walk/incumbent provenance, report/log agreement, transition and deletion accounting, walk floors, and both exact verifiers on each starting walk, original incumbent, final best and final walk. Every best remains the original valid 156-point seed. The pool records direct-child resource policy, not a per-job peak RSS or owned-tree cleanup receipt; the saved dependency manifest is a pre-run pin and current dependencies still match. Intermediate accepted states are report evidence and were not independently replayed.

| Seed | Starting walk | Final walk | Accepted size deltas | Final symmetric difference from initial walk | Final symmetric difference from original seed |
|---|---:|---:|---|---:|---:|
| 279307 | 155 | 153 | -2×1, -1×2, 0×5, +1×2 | 8 | 5 |
| 279308 | 155 | 156 | -1×1, 0×1, +1×2 | 3 | 0 |
| 279312 | 153 | 153 | 0×6 | 8 | 5 |
| 279313 | 153 | 153 | 0×10 | 4 | 5 |

The three 153-point final walks have distinct normalized hashes `8dee540963933b87aa83d3b77827839bc47d9fdfe4f4c905bae9afea583d039d`, `0852bbb72f32ba9060940298e656f54b9f27e1cef8ccb7eb816f4f26a83b9d89`, and `bc44e6a42c4fe817d1f6c13c1f7a3cd236fe09f79b188db5541f0047646e95c1`; all are independently valid. The fourth returned to the seed. The accepted moves demonstrate actual path movement, but the retained results did not increase the best count or exceed the prior final state's five-point symmetric difference from the original seed. Different hashes are not evidence of a bound improvement or novelty.

Recommend stopping this continuation tree for now and preserving the three valid states. This bounded sample shows movement but no improvement toward 157, while the separately measured primary work has a stronger empirical signal. It does not prove that deeper walks cannot succeed. A future continuation would need a concrete new hypothesis or evidence, rather than another automatic repeat of the same policy. No numerical work was launched in this review.
