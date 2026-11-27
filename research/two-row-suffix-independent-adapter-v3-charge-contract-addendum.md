# Suffix audit adapter v3: precompletion charge contract

Root's corrective v2 audit rejected the saved result at the exact64-record/unchanged-endpoint predicate. Root reported clean termination in0.150165958 seconds and48736KiB, with failed output SHA256 `d7262a01a455e3a3a6b45c876d4016d0e388c0b63c2e5c4d2db4632ea2c4ea89`. These are supplied metadata, not actual files read during this correction. Both failed actual outputs and all historical reviews/evidence remain preserved.

My adapter mistakenly equated the last started charge with final completed counters. Frozen worker `drive` clones the charge immediately after `plan_start`, then later calls `plan_nonimprovement`; `run` reports that preserved precompletion charge. Therefore the final64th pair has last charge pair_started96/pair_completed95, while the durable completed authority has96/96. Other counters remain308/308 rows and accepted28. The earlier synthetic fixture reproduced my incorrect equality and did not test this timing contract. This is an adapter/test error, not a worker search error.

V2 source is preserved at `research/two_row_suffix75_actual_authority_adapter_v2_frozen.py`, SHA256 `94846c3c4a34b15f46aa76ca701e08ccc14b0562700f3fdff1e6a7d8cc88a5b4`. Corrected current adapter SHA256 is `1957377699f9fa516d74d592994f8120657f9c72b64210ab0aef2c205ee99c8e`. The only logical change declares the exact expected last charge as final counters with pair_completed95 and compares the report against it. All final authority counters still require96/96; all v2 manifest, source, receipt and geometry bindings remain unchanged.

## Complete remaining source-contract inspection

The entire adapter and frozen production `run`/`drive` were reread, including all final predicates rather than only the failed one. No other mismatch was identified:

- Input identities are the four exact Root-provided report/receipt/manifest/authority hashes, with bounded input bytes and post-audit rechecks. They are external associations, not inferred production output values.
- The166-entry manifest gains exactly one self pin, matching production `run`; report and receipt must contain the same167 effective pins. Mandatory worker/kernel/handoff/runtime/verifier bindings and full pre/post byte checks remain strict.
- Method, n/k, ceilings204/64 and512/96, soft/search25/23, positive unwitnessed status and error exclusions match production report initialization and final acceptance. Report/authority uncertainty and identity fields remain required.
- Production publishes initialization, each charged start and completed result, then final stop. For64 nonimproving pairs with no failure this is1+128+1=130. Report byte/hash fields identify that final authoritative wrapper.
- Report `state`, `attempts`, `artifacts` and order hash are copied from `store.last_durable`; exact association with the authenticated authority is appropriate. `run` writes the final stop status into the last snapshot, so `pair_cap` is checked there rather than requiring the internal pre-final `active` status.
- The initial artifact records the fixed65 identity/score, BASE308/308/32/32/28, pair_cursor32, initial order and handoff. With no accepted state change, initial and final order hashes agree. The helper independently recounts the points/rankings and fixed identity, so the captured initial byte hash alone is not the semantic trust anchor.
- `load_handoff` produces metadata_sha256, normalized_sha256, score65, historical_pair_prefix32 and the exact source-supported coverage label required by the adapter.
- No accepted moves means no artifact references or witness, generation remains28 and the independently accepted-state sequence contains exactly the initial65 state. Starts and completions become96 while rows remain308.
- `plan_start` assigns seq1 through64 and consumes the current pair cursor before `plan_nonimprovement` increments it. Thus record cursor=31+seq, final cursor96, phasepair, row coverage true and pair-scan coverage false are the claimed capped partial outcome, independently checked against direct current ranking by the helper.
- `attempted_charge` is the only field that refers to the last precompletion moment:96 started/95 completed. The final record must still be complete and pending must be absent. It is not safe to require only an inequality or to accept arbitrary earlier charges; v3 binds the exact mapping.
- Receipt checks remain the independently reviewed owned-guard contract: exact argv/manifest association, successful exit and clean cleanup, no monitor/trigger errors,30-second/256MiB ceilings, valid samples and ordered finite worker/guard/job timings. These authenticate reported observations; sampled RSS is not a proved unsampled peak.
- Output acceptance still requires all post-audit original pin/artifact/helper/adapter checks plus the soft deadline. File fsync+replace does not claim crash-durable parent-directory publication. Root's separate owned audit completion and reread remain required.

## Corrected and real tiny regression evidence

The synthetic metadata-only adapter preparation now uses last charge96/95 with final authority96/96. One positive association and28 corruption rejections pass, specifically rejecting pair_completed94 and96 in the last charge and pair_started95. It retains the explicit166-manifest/167-effective-pin assertion and165/167 manifest rejection cases. All I/O and direct-chain computation are still disclosed stubs in that metadata test.

- Preparation source: `research/two_row_suffix_independent_adapter_preparation.py`, SHA256 `1574dcb929abac5ace9366a6dd3bcd4220852bc23be519ee3631b2ee4fb6f01a`.
- Evidence: `data/two-row-suffix-independent-adapter-preparation-v3.json`, SHA256 `333ddbca3a7092ec1ccf8097db477a001edb913d3912a6ea7b8a0a44a3119310`.

A separate real n4 production `drive` fixture starts with synthetic95/95 pair provenance, performs one genuine nonimproving pair and stops at96. Its memory start snapshot and returned attempted charge are exactly96/95; completed authority is96/96, no pending move remains, and an independent determinant recount confirms unchanged n4 U1. This bridges the timing contract to real worker control flow without actual inputs or a worker `run` call.

- Tiny contract source: `research/two_row_suffix_independent_charge_contract_tiny.py`, SHA256 `e18468f7be80a9f5d57daa37403f07f093239987b115e6f9a9a48eb8ab66ee00`.
- Tiny contract evidence: `data/two-row-suffix-independent-charge-contract-tiny.json`, SHA256 `53deb5a60acf282352dd71477ac8d0f9d899cb664bb18aff27e10288df5d87c7`.

No actual artifacts, coordinates, geometry or optimizer replay were accessed for this correction, and no third audit was executed here. V3 is ready for independent source/delta review. Root alone may reserve a further verification allocation; no retry, search rerun or cap expansion is implied by these tests.
