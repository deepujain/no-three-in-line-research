# Independent review: readonly n79 250-node continuation

PASS after bounded retained-artifact parsing and hash checks. No geometry replay or numerical search was launched by the reviewer.

- Request: `b9a49fc30ef6e7f7e9f24a8aaa39edc49f991fe37ff714a9a545620e96bbfbfe`
- Stage: `000000000000000000000000000c0f1f`
- Job: `8c3cdd854ee65e947378adb409b7d0088211563d4ab084d9ef789915c0d3ffe8`
- Report: `f6293a3f49af41344aa796f4f4ac75ded92047dc390bcf71d6c8193eb5126f96`
- Receipt: `362ce2551e63b2321b6bb28846dad901d302e22026cf569d117aac56f356c467`
- Exact parent: `4f5a32b89158a3d870dee399e93ea4ee4a36c8eeb704db1e44cf7d4e58c52141`
- Accepted checkpoint: `5b18d26feaf825574e43b61e59ea1adcfa79d6d7314c48a43ac9af7b034dba76`
- HEAD hash at audit: `6233eec3d3b761d6ec7cfd71f66d1e366e04616d4952385f0ba5ed462a1bd8dd`
- Chain: `2006e1d67f79749c6af438c3d5f89a7c1cfb30ce385501ce9241f1377662ab5c`

Current `validate_receipt`, `validate_job`, structural `validate_report`, and `validate_gate` pass. Receipt/report/job hashes and the checkpoint parsed against trusted parent and identity agree. The before/after/current nine-source manifests are equal to the identity recorded in `near-quarter-readonly-n79-root-and-stage11-review.md` (SHA-256 `99be0084064a32364b8193fb657ff6137af241ad00416a991934cd6793377d58`), with core `f257045276d1247fde814fae01fe0a470233c477e228c37b6d3209fd367439ae`. Declaration, policy 2, map, 30-second guard, 256 MiB limit, and 2-second save reserve are unchanged. Structured return is accepted, matches experiment stdout, reports no retained lease, and exit code is zero.

The checkpoint advances 11 prior nodes by exactly 250 new nodes to 261 total. It remains ACTIVE with 13 frames and top ENTER. Logical counters are `(261,0,320,59,0,133,0)`. There are zero completed slices out of 39, no witness, and no exhaustion claim.

Domain/query counters for this invocation: 1,303,566 domain probes; 309 batch probes; 1,406 cursor checks; 34,763 restore probes; zero interrupted scans. Mutation-engine physical totals are 1,106,344 cell increments, 1,051,194 inverse cells, 596 orbit attempts, 163,636 pair lines, 2,203 point attempts, 1,964 points undone, 59 rejected orbits, and zero aborted orbits. Physical scope excludes readonly-query line walks, reads, and determinants, as previously declared.

Child timings: construct/restore 0.213482666 seconds; map check 0.004776042; operation 7.954161875; save/validation/publication 0.228987125; through report preparation 8.409413458. Helper measured 8.472188874991843 seconds with 182 RSS samples and peak 52,448 KiB. Cleanup was clean, one sample, 0.011279083002591506 seconds. Supervisor through durable outcome and lease release measured 8.501624667 seconds; experiment outer time was 8.546957792001194 seconds.

Keep the current quota of 250 new nodes for subsequent bounded stages. This measured stage leaves substantial headroom under the unchanged cap, without assuming future branches have identical costs. One separately allocated manual 250-node stage from this exact accepted checkpoint is suitable while the thin chain runner is prepared. A chain runner must retain explicit parent linkage, source checks, existing worker gates, and stop on rejection, uncertainty, witness, exhaustion, or a retained lease. Root owns launch and aggregate accounting; this audit performs no allocation itself.
