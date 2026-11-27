# Independent valley batch review: seeds 279107 through 279113

All seven terminal receipts report exit 0. I checked report/log agreement, source pins against current files, receipt identities, deletion/trial/transition arithmetic, final walk floor, and both exact verifiers on each saved best and final walk. All best certificates contain 156 points; no 157/158 improvement was reported. The first three trials use recorded 30-second/256-MiB owned-process guard receipts; the later four use the separate pool's direct-child sampling policy, and their receipts do not record per-job peak RSS or prove owned-tree cleanup. The pool source-pin artifact records the dependency hashes before the batch; unlike the first three receipts, it does not itself contain per-job post-run dependency hashes. Current dependency hashes match those pins. Historical intermediate accepted states were not saved for independent replay.

| Seed | Drawdown | Completed passes | Accepted size deltas | Minimum reported walk | Final walk | Final symmetric difference from seed |
|---|---:|---:|---|---:|---:|---:|
| 279107 | 4 | 93 | -1×3, 0×2, +1×1 | 154 | 154 | 6 |
| 279108 | 4 | 92 | -2×1, +2×1 | 154 | 156 | 0 |
| 279109 | 8 | 92 | none | 156 | 156 | 0 |
| 279110 | 4 | 93 | -2×1, +2×1 | 154 | 156 | 0 |
| 279111 | 4 | 92 | none | 156 | 156 | 0 |
| 279112 | 4 | 93 | -1×1 | 155 | 155 | 3 |
| 279113 | 4 | 92 | none | 156 | 156 | 0 |

The final 154-point state (normalized SHA-256 `49365a7a5ad49d60a5a064c6b39657f1ba6392504e495d3b55e997a599fab777`) and final 155-point state (`45bca883bd3f017ea0a3aed88f4fd90268e247fd175387913cdc099378fd3da1`) are distinct from the seed and independently dual-verified. The other five final walks are the original seed. Accepted delta counts and reported maxima support short-lived movement, not an improved bound or a claim of unique intermediate states. The one drawdown-8 sample provides no meaningful comparison against drawdown 4.

Recommend stopping more identical fresh-seed batches: seven additional seeds produced two distinct below-best final states and no improvement, while most returned or stayed at the seed. A more informative next hypothesis would continue from a retained, independently verified 154/155 walk while separately preserving the 156 incumbent; the current CLI treats its initial certificate as both walk and best, so it does not safely express that experiment without a small separately reviewed interface change. Do not simply restart from the smaller certificate and call 155/156 a new best. A bounded continuation would still be exploratory and should be judged by actual movement or a verified improvement, not cached proposal counts. No numerical launch was performed during this review.
