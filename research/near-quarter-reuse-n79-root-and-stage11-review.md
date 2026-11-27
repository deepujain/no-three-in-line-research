# Immediate-domain reuse n79 root and eleven-node comparison

Both operations pass retained-artifact audit. Immediate-domain reuse removes half the replay probes on the matched eleven-node frontier and approximately halves measured save/validation time. The complete logical frontier and physical traversal work remain unchanged. No n79 geometry or worker was launched by this review.

Root stage `000000000000000000000000000c0eb9` accepted checkpoint `b87a6b5cdcdb2980361fefb7e6f76adbe0a80d0880894dc20d09b5a49429e011` in fresh chain `bb9bcfca2c612a111dbf1590605f3d56d39c69dc52d07ae2781deaa299217bec`, through receipt `1167b5958198c2b9d148008c28424c8bc0b9078aeecb851864ee9ff46beb4541`. Root job hash is `bb3ba781d85e98c348f9f7f1cea1d02fbda260ca6fb9c0c652f4ad9023f2c760`, report `7eca461b31f80d405af858914de2f155738d9f008623e33d00bb6a19d6ccd16f`, and HEAD at root audit `565b16b31ca6004fa6c99fd2224a07aa3d36c0c18a502ed47827222d340f165d`. It has one ENTER frame, policy2 and zero logical/domain counters. Root helper time is 0.110563958 seconds, two RSS samples and peak sampled 49,248 KiB; supervisor time 0.151168167 seconds and outer time 0.195191959 seconds. Cleanup is clean and no lease remains.

Counted stage `000000000000000000000000000c0eba` accepted checkpoint `2e16b2fd41145310dd0678a01ee91e4a7c5d09e6bacbe793c7bad82eb9b7e46e` through receipt `f227cf0d75ab7c84ac94cb5a86c779d191f30b3c9eba32a8ba61269e1d4cbae3`. Job hash is `bdc0827f20e49ef53309267d17337ffb105eebd5f1e869cd752623a53fd0514f`, report `dee5b1ae3133e226fba452bdc07e589d974354da3cde976f9fd06c3aa560543a`, and HEAD at audit `a2d98f6386d64c86d458d19e787ba4335ebbc796af9875e8a386755f35d38911`.

For both operations, request/job/report/receipt/HEAD/public return agree. Experiment stdout matches the return, exit is zero, current and before/after nine-source manifests match, structural checkpoint checks pass and the existing helper resource/cleanup checks pass. Limits remain 30 seconds, 256 MiB and a two-second precommit reserve. The root parent is zero; counted-stage parent is exactly the accepted fresh root. Sources are reviewed core2f758f63, codec88ce7a7a, worker7f8c8a16 and the remaining unchanged approved sources. There is no old-frontier migration, witness/event, completed slice or exhaustion claim.

The counted result has twelve frames with top ENTER and counts `(11,0,11,0,0,0,0)`. Its bytes from absolute offset 622 onward are exactly equal to the previously hash-verified radius-policy frontier `4d1c5a31bb1407a8cb8242d96057fcff414bfa1b3e2069e86c7e06b0a1a017ec`. This region includes control, counters, declared orders and all frames, excluding the identity and parent/chain binding. Every physical traversal counter is identical, including 10,613,959 cell increments and 49,913 orbit attempts. Domain work is unchanged at 49,893 probes, eleven batch probes, 320 cursor checks and zero interrupted scans.

| Measurement | Radius policy before reuse | Immediate-domain reuse |
| --- | ---: | ---: |
| Restore probes, including private save replay | 33,262 | 16,631 |
| Private-validation cell increments | 7,083,677 | 3,553,316 |
| Private-validation orbit attempts | 33,283 | 16,652 |
| Operation seconds | 11.753322250 | 14.702255583 |
| Save/validation/publication seconds | 7.377646875 | 3.681973833 |
| Outer invocation seconds | 19.385505458 | 18.605715999991 |

Replay probes halve exactly. Selected-path reconstruction work remains, so the entire physical validation total is not exactly halved. Measured save/validation time falls about 50.1 percent. Unchanged operation work took longer in the reuse invocation; these observations do not identify the cause or establish a stable speed estimate. The approximately 4.0 percent outer-time improvement is a single observation with that variation, not a general speedup promise.

Reuse counted-stage helper elapsed is 18.503894708 seconds with 369 RSS samples and peak sampled 52,336 KiB. Cleanup is clean, one sample and 0.011239208 seconds. Full supervisor time is 18.555181166 seconds. Child construct/restore and map check took 0.014510209 and 0.004919083 seconds. Physical counters are complete and no lease remains.

Recommend Root separately allocate exactly three new nodes from accepted checkpoint `2e16b2fd41145310dd0678a01ee91e4a7c5d09e6bacbe793c7bad82eb9b7e46e` under unchanged caps and reserve. The measured replay savings support useful progress beyond the eleven-node baseline; do not first require another fresh-root comparison or source change. This allocation is bounded, with no completion guarantee or implicit retry. A deeper result should be audited before choosing its next quota.
