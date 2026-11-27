# Chain auditor final source and fixed pilot adapter

This SOURCE-only addendum supersedes the earlier prepared helper binding; historical sources/evidence remain unchanged. No actual pilot artifact was read and no n75 geometry was recounted during this preparation.

The final helper `research/two_row_descent_independent_chain_audit.py` is SHA-256 `d0e558e507f74bb4384ddb582d726235e0518fad61b164cc0e72bac99ddc5f59`. Independent source review requested a stricter accepted-counter condition: each accepted move's kind must have strictly more completed optimizations than at the previous accepted event. This replaces the earlier weaker requirement that its completed count merely be positive. The prior source is preserved at `research/two_row_descent_independent_chain_audit_v2_frozen.py`.

Synthetic evidence `data/two-row-descent-independent-chain-audit-preparation-v3.json`, SHA-256 `f430a684a652a51a1b3a06ef63410716b85769312ebb623b66c3c7f55057e9ea`, includes twelve rejected corruptions. A genuine n4 two-pair chain5-to1-to0 fails when both accepted pair moves reuse completed count1, and passes when the second count advances to2. These are saved-state audit tests, not a claim that this pair sequence follows the production first-improvement policy. The independent review `research/two-row-descent75-independent-chain-audit-source-review.md` has SHA-256 `79f739e3a5c35c93702deab761d8c0aebc081ad193cbe0c998417eeecb78a2c7` and gives helper SOURCE PASS conditional on a separately reviewed actual adapter.

Adapter candidate `research/two_row_descent75_actual_chain_adapter.py`, SHA-256 `df5a6e5521ef0dbb93c995a6c60a5ab4beb8adf85b12fa936bc6808a5fbe38ed`, binds Root-supplied complete pilot report, receipt, manifest and boundary hashes. It checks pilot guard status, source/input/runtime pins before and after, fixed provenance metadata,28 ordered numbered saved improvement files and the initial state. The helper directly recounts29 unique saved states and verifies every strict decrease and declared changed row. The final boundary must equal the recounted last improvement exactly, avoiding an unnecessary duplicate triple scan. Final score65 and normalized identity are checked against Root's supplied artifact claims. These claims remain unverified actual metadata until Root executes the owned audit successfully.

The adapter never replays neighborhood optimization. It labels the32-pair cap partial, declines independent local-minimum claims, and separates saved-state geometry from execution assertions. It preserves a durable success/failure JSON in a new output path, caps its internal soft time at25 seconds and cooperatively checks hashes and triple loops. Root records the separate owned30-second/256MiB guard and binds both audit source hashes. The adapter source was syntax-compiled only; final actual execution requires exact-source independent review PASS.

Proposed invocation, from the research repository root and only under Root's separate owned guard:

```sh
.venv/bin/python research/two_row_descent75_actual_chain_adapter.py --seconds 25 --output data/two-row-descent75-independent-chain-actual-audit.json
```

No audit outcome or149-point witness is claimed by this source preparation.
