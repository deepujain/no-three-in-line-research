# Packed n79 ten-node stage review and baseline boundary

Accepted retained-artifact audit. This review launched no geometry or numerical worker. It checked the exact request/job/report/receipt/HEAD/return links, all nine source pins, structural candidate parsing, unchanged source evidence, exact 1+10=11 node accounting, helper limits, cleanup and absent lease.

The first outer invocation, `data/experiments/resume-packed-n79-stage10-v1.json`, failed in `main` at strict JSON parsing before `run_stage` because the request contained a trailing newline. It exited one after 0.054496084 seconds, with no stdout and unchanged source pins. Independent inspection before correction found no stage directory, no writer lease and the accepted one-node parent unchanged. Canonicalizing the still-unattempted input and preserving a separately named v2 record was an input correction, not a numerical retry.

The corrected canonical request hash is `8f220bc5659f38fbe95f15436a4da82dbcd7064d322a74740e31262bd47fe5b2`. Stage `000000000000000000000000000c0df3` uses unchanged chain `668986647657b0b0dbad0039e413265d9cee5f5267a3d83e9c097d2cc23260e3`, parent `e567d12e1b583b2a71c682985ce51b53e71f91fa92d26099308fb46bc495ab3c`, ten new nodes, 30 seconds, 256 MiB and a two-second precommit reserve. The declaration and map digest match the accepted root. Worker `7f8c8a166d4e79f881a644b69b6f0bb0c949ef524c97eb792f81b09c0e835738` and all other approved sources are unchanged.

Accepted evidence:

- Checkpoint: `802d69d07a9ab44b452621043a00ec1f64351c6412e62fdaac2752424bea038e`.
- Receipt: `376031bdf20262c81e9ae92efa50a9e6425429c5cbf1880131ef3a85fd5de499`.
- Job: `b76c738b29dd26ab18e719d3f36823ed39a3f8a6985cb9bb4df3dad8c8fd3184`.
- Report: `ea3c42acaf48ede078f8d65db35d201b801a8882acffadfca093cd9e994b97b4`.
- HEAD at audit: `0d2567ddff4986c418e6b85ec7fc12d79b3b9215453e870487e4e63ff527db3e`.

The frontier has 12 frames, top ENTER, ACTIVE outer state, counts `(11,0,11,0,0,0,0)` and zero completed of 39 slices. The node_limit_checkpointed report has one before, ten new and eleven total nodes. There is no witness/event or exhaustion claim. Domain counters are 45,330 domain probes, ten batch probes, 316 cursor checks, zero interrupted scans and 36,304 restore probes. Physical counters are complete.

Helper elapsed was 18.474600083 seconds with 440 RSS samples and peak sampled 52,368 KiB. Cleanup was clean, one sample and 0.012316208 seconds. The full supervisor interval was 18.509217208 seconds and the outer experiment `resume-packed-n79-stage10-v2.json` reports 18.560539417 seconds. Child construction/restore took 0.334478375 seconds, map check 0.004513334 seconds, operation 10.740329792 seconds and save/validation/publication 7.313952791 seconds. These timing scopes are distinct; the resource gate is sampled rather than an absolute instantaneous RSS guarantee.

Recommend preserving this accepted eleven-node frontier as the baseline-release boundary for the independently approved pure radius predicate. Restore cost at the next deeper frontier will grow: the previous save replay is relevant empirical evidence, so simply repeating ten nodes under the same cap is not supported by these measurements. If Root elects one more old baseline allocation first, three new nodes under unchanged limits is a bounded experimental choice, not a guaranteed completion. No further old baseline stage is a prerequisite for integration. Integration must receive a distinct source/policy identity, preserve the old frontier evidence, use only a complete admissibility mask, pass focused review, and begin a separately allocated fresh-chain comparison. No runtime benefit or n79 feasibility conclusion follows yet.
