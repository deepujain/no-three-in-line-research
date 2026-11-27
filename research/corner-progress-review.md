# Independent review of three corner-stream prefixes

Reviewed 2026-11-27 at approximately 00:24:42 UTC by gpt-6.1-terra, high reasoning, per assignment. This is an artifact and provenance check, not an independent replay of the numerical computations. No new numerical search or benchmark was run.

The actual published seed and scan were supplied to `load_gapless_chain` for each tip. It checked every predecessor's byte hash, consistent frontier parameters, ordered-source and normalized-source hashes, and gapless offsets from zero. I independently compared each chain's cut, base indices and total to `data/corner-anchor-frontier/manifest.json`, inspected every record's completion count, tested/valid addition counters, and certificate/witness fields, and summed counts only **within** its own chain. The source normalized hash is `e197d1b41f97df9188b9839a54f0013bbc08b67d202c18d26146a7f377d80ced`; its ordered hash is `e7678d82888f177d779c4ca250d6cda995645a13e0c102b5727138a835c0c9bb`. Reviewed worker SHA-256 is `dbb412aa9bd83d56b7ba331f97097b5549bded8131a0811de8cdcba4883a2292`; underlying audit source is `7c0ee4ad6c63f4c0808535a488459a5e59e693a23bed695a172068c146a72bc9`; manifest bytes hash to `e45bfeaed19f5b519a8cdda3ab411bbf874ca365903d46c7cadd802ab64137a1`.

| Anchor and original deletion indices | Reviewed prefix of 596,904 | Linked records | 157 / 158 addition subsets tested | Valid / certificates | Tip SHA-256 |
|---|---:|---:|---:|---:|---|
| 10296: [40,52] | 0–495,953 (next 495,954) | 26 | 509,988 / 2,360 | 0 / 0 | `d1eb04b8cc016afe5dee965a1c83c3a4bea16c484d9656c4808b130d48a0f5af` |
| 10297: [40,88] | 0–497,273 (next 497,274) | 26 | 511,230 / 2,347 | 0 / 0 | `577445790020ce4d001c169c4abbdf70ee763977da38380296321f2c41fb22a7` |
| 10298: [52,70] | 0–491,277 (next 491,278) | 26 | 497,914 / 1,106 | 0 / 0 | `31cdaa9907e877863685e5e86ab863ebdbc32ae26cf04d64982eb8efca18b31d` |

The terminal record hashes, in the same order, are `a00f2791bbc93b3d08d33eb482243aa87933a53a91fc9f2177f095c99d1e51bd`, `c536db66e4c64c8280971dc3b9f250f6f62dc9527fc6640493a254d1b87f5692`, and `dd0489216f388c8656ab747af024c4f7207b9d80d549835edf50baa28ffdf515`. Every terminal record says `timeout_incomplete`. The three receipts `data/experiments/r7-corner-five-10296.json` through `...10298.json` show process exit 0 and `completed` at approximately 00:24:09 UTC; that means the bounded worker finished its slice, not that its frontier was exhausted. No `embedding-witness-*.json` file was present in the frontier directory at inspection.

Conditional on the correctness of the trusted recorded computations, each row excludes valid 157/158-point repairs in **that enumerated prefix** of that anchor. These anchors can overlap, so their counts must not be summed as distinct deletion sets. Most anchor families have not been covered; these partial results do not exclude the full corner family, other embeddings or an unrestricted witness. Record hashes establish chain consistency and provenance, not proof that the computations ran correctly.

## Completed continuations, 2026-11-27

Rechecked after the continuation receipts: all three tips now have `frontier_complete=true`, a `complete` terminal record, and gapless 0–596,904 coverage. Each chain was reloaded with the actual seed/scan; source/order hashes, cut, base indices, total, predecessor hashes and manifest bindings matched. I inspected every record's valid-addition and certificate/witness fields, which were all zero/empty. The frontier directory contained no `embedding-witness-*.json` files at this check.

| Anchor | Linked records | 157 / 158 subsets tested | Tip SHA-256 | Terminal SHA-256 |
|---|---:|---:|---|---|
| 10296 | 32 | 613,314 / 2,756 | `8ff099cb50457866bf06af03b0b7ce6c2e2bd278e36064da0dc1e6d30d07160c` | `41e7a15633740155f09017b7d80f84fd7f6543ccdd7d8a4d9e60315b17ab6faa` |
| 10297 | 31 | 613,218 / 2,740 | `adc57e6229799ff9fec4f2aaf81738d2bceb7237490d53accc41f5ee085ec172` | `a36717cdaf5035a5e4416c3fbe17365d8cb963029ab1d2d4d299b2431085f4e0` |
| 10298 | 32 | 605,880 / 1,496 | `2e557934bb50b701561bfc3df04f012fd651f1cd6061c870488fe770e788fb39` | `f49f676c072d9cb92ab65afe1e7fc18db15db141cee287e25ebef2b15f84ac03` |

`r8-corner-five-10296-resume`, `...10297-resume`, and `...10298-resume` receipts report completed at 00:26:58, 00:26:56 and 00:27:02 UTC respectively. Conditional on trusted recorded computations, these are complete no-witness results for the three named exact-five anchor families, not for the full corner family. The families can overlap, so the row counts are not distinct counts across them. The source and artifact consistency were checked; the computations were not replayed in full.

## Five newly prepared origins

The five remaining size-two anchor origins, 10299–10303, were reviewed before numerical use. Each was loaded through `load_gapless_chain` with the actual published seed and scan. Every origin matches the manifest's cut, base indices, normalized and ordered source hashes, exact-five count and 596,904 total; each has zero start/next/completed offsets, zero tested/valid counters, no certificate and `case_limit_incomplete`. Independently recomputed blockers confirm each base hits both blocker pairs for its manifest cell. The `remaining-size2-origins.json` sidecar's manifest hash and all five recorded origin hashes also match the actual files:

| Anchor | Base | Origin SHA-256 |
|---|---|---|
| 10299 | [70,88] | `14b7a5ff6bb0a3263aa62627b66055087f41788360a6ae282d60f0b62c181d07` |
| 10300 | [106,154] | `a365a103fde85e160a655971d21fb197cfd6e78f47cda2954beb342becc6a6f3` |
| 10301 | [106,155] | `0640bc737b15562feffab4fdca9396b4ffdbccc1808db2c5939892d708034c99` |
| 10302 | [126,154] | `40686f928d498a85731f66ff17e379ea2838658c30c6f31fd000fd0e35c2e40d` |
| 10303 | [126,155] | `fb54ef7fbf36a1d602af0dab65e2dac22421ac42563ae1758bb6f42b84028ff8` |

These are valid preparation-only starting records; their zero offsets establish no deletion-case coverage. The reviewed streaming mechanism is memory bounded, subject to the worker's ordinary process and solver environment. No numerical search was run in this review.

## Additional completed size-two anchors

The completed `r10-corner-five-10299`, `...10300`, and `...10301` chains were independently reloaded against the actual seed and scan after their 2026-11-27 00:41 UTC receipts. Each covers all 596,904 exact-five sets in a gapless 31-record chain; source/order hashes, corner cut and manifest bases match, and every record's valid-addition and certificate/witness fields are zero or empty. Target-157/158 subsets tested were 605,784/1,480, 605,880/1,496, and 605,784/1,480 respectively. Tip hashes are `6935ea7bdb700ec26a7f0ed9f7be6c15c0202a0e7e5c06c956c412cdad8cf673`, `ea3f7ecefc9645b713028048ad34fa2f057b09eca781397c783d92755cf9bfb8`, `e214260c53fc127ded8a58398a6fbae28c6c48a3673b6723b436806abb92c92e`; terminal hashes are `19e0d8dca638b630b1547fe4b59ae2f91b08c94c7b476ec318f8bbdb90072b3f`, `8a7d413a13afdaafc0cc7100d3d98ef5fffb2879b21995afa191805a8ac7c938`, and `00abc276cc8283fca2277f42b83335c43efd0213478b1c55169f0cd9fd1fefd5`. These are trusted-computation conclusions for the three named anchor families; they overlap and do not close the full corner family. No numerical replay was performed.

## All eight completed size-two anchor families

At 2026-11-27 after both r10 continuations finished, I reloaded all eight manifest anchors 10296–10303 against the actual seed/scan and checked 250 linked origin/result records for source/order/cut/base/manifest identity, predecessor hashes, zero-origin gapless 0–596,904 coverage, empty certificate/witness lists and zero valid-addition counters. All eight tips report complete, and no `embedding-witness-*.json` file was present in the frontier directory at inspection. For the final two anchors:

| Anchor and base | 157 / 158 addition subsets tested | Tip SHA-256 | Terminal SHA-256 |
|---|---:|---|---|
| 10302 [126,154] | 613,362 / 2,764 | `546fab3c7043b5229a5833af962c565ca441f889ce7b7b4a2136888b4d718413` | `a5ec37aff052511dbefe3de30779a1a78673a8e2fbbbed7ece540602308c5817` |
| 10303 [126,155] | 613,266 / 2,748 | `a9afe7414c8e13c6db564d1006e118f006961da0d6294a2b0922c020bd9b1537` | `67a43583018d07b9965040cb807de4503bc92c1776efc33fe52fe11b3005e8bb` |

The compact `data/corner-size-two-summary.json` contains all eight separately checked tip/terminal hashes and counters. Conditional on the trusted recorded computations, the eight exact-five anchor families have no valid 157/158 repair. They can overlap: do not add their case counts as distinct sets, and do not treat the eight families as a full-corner exclusion.

## Candidate size-three partition

The frozen manifest contains exactly 224 anchors at zero-based indices `[10072,10296)`, each with three original deletion indices and C(153,2)=11,628 exact-five supersets. The existing size-four selection `[8136,10072)` is disjoint as a set of manifest ordinals. A proposed pair of 900-second batch slices `[10072,10184)` and `[10184,10296)` each contains 112 selected anchors and 1,302,336 anchor cases (selection SHA-256 `5178c8ade1177d6c011d98a0dd534dc5ac24ea9d3a313eaa8d3cf07a96901801` and `058793f89009e3be1cdd8915c7642e29c23a5d23a156746aa24e3337021e2a39`). Use separate fresh cursor and records directories, `--max-anchor-cases 11628`, `--max-cases 1302336`, the reviewed `--batch` entrypoint and the existing process/memory guard. `--chunk-cases 20000` completes at most one 11,628-case anchor per chunk; a crash before publication can cause the current anchor to be repeated, not silently skipped. A 900-second timeout is partial unless all selected chains complete. Different manifest anchors may overlap geometrically even though the ordinal slices are disjoint. This is selection review only; no numerical run was launched.
