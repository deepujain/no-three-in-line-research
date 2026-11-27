# Independent review: readonly n79 root and eleven-node stage

The fresh root and eleven-node continuation pass the retained-artifact audit. This review performs structural parsing and byte comparisons; it does not launch geometry reconstruction or numerical search. Both stages use 30 seconds, 256 MiB, and a 2-second save reserve, with unchanged canonical n79 declaration, policy 2, diagonal order 1522..1560, orbit order 1..1521, and rows 0..78.

## Bound artifacts

- Chain: `2006e1d67f79749c6af438c3d5f89a7c1cfb30ce385501ce9241f1377662ab5c`
- Map: `78054420e2f53dde1ea7d1d3823b220d7bf1b8e6e0edb5f05ea6210786528032`
- Root request: `c068a3f70c326ff6287e163b850ae87f5a7917c21120e3373ebc73b5996f794c`
- Root proposal: `b80b3b1f01c8bb80db0c5a554dda2c108c1cabca848077ca03b0af996b014fc5`
- Root stage: `000000000000000000000000000c0f1d`
- Root job: `70cedaa5d7f5a4b58f5f85586854a32cb351db5132bf50c7d201bd3f40e6f64a`
- Root report: `696af824804edb4507a3bc742e40acea4dc108f50d4ccddeec727be4037f5a58`
- Root receipt: `99d76481ec344fdc4b02fe9d21821536ab6f5e2b570033f224fdc1eaac6520f4`
- Root checkpoint: `d67735783b6fde5b606404d81e333c6959fbaba96ec0d1c865b46dd51ec141cf`
- Root accepted-record hash at audit: `f62ca4b28e646f86be5d24b7f70a0665f3a83c7d5827d839c92ea47ba1be7868`
- Eleven-node stage: `000000000000000000000000000c0f1e`
- Eleven-node job: `79b6b98534752172fd5ba6c79abd9cd6abff6b938c93236655938824782f35ce`
- Eleven-node report: `5aca91d97128b727d241c8dbd7de3c0828736d3b0c5dfaba815c882c7a367caa`
- Eleven-node receipt: `ec1d976c9c05fb75f70502516ff0e2ff34c4a0b8b891f5d097788495f89be391`
- Eleven-node checkpoint: `4f5a32b89158a3d870dee399e93ea4ee4a36c8eeb704db1e44cf7d4e58c52141`
- Eleven-node accepted-record hash at audit: `8acb4e5f7aeebc561cabb94aa5c1c4e4126c0ed3e65b4fc70f503705793ad86a`

The root checkpoint is the exact parent of the eleven-node checkpoint. Receipt, job, report, checkpoint, accepted-record and source links were checked using current `validate_receipt`, `validate_job`, structural `validate_report`, and `validate_gate`, plus direct hashing. Both experiment records have matching before/after/current source manifests, exit zero, stdout equal to saved structured return, accepted outcomes, and no retained lease.

## Frozen source identity

| Component | SHA-256 |
| --- | --- |
| core | `f257045276d1247fde814fae01fe0a470233c477e228c37b6d3209fd367439ae` |
| state | `860711b8e83d0f3e738ebeedc535e0953e903a01551b1e22ad3bb20f49fa3b11` |
| cursor | `738a545abc1909bc126ca916d225dfef90bea8b974142a5885cb9e2f632e2422` |
| checkpoint | `88ce7a7a9b3d756427f60382b1b1316f30755e3a1a49a9a51367c6fcb27e6dec` |
| model | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| verifier | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |
| line-model | `d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897` |
| worker | `7f8c8a166d4e79f881a644b69b6f0bb0c949ef524c97eb792f81b09c0e835738` |
| owned-helper | `c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48` |

The core also binds radius helper `647ae1379eb89711707f9900d68a2aba1861839751bdb22f15e9618d1f5cda66` and readonly helper `2b9f51496f80c78881643724029e48cd9987b1428bdffbce7736806d790f5c7d`.

## Exact retained frontier comparison

Root has one ENTER frame and zero logical/domain counters. The continuation reports `node_limit_checkpointed`, 0 prior / 11 new / 11 total nodes, 12 frames with top ENTER, ACTIVE state, counters `(11,0,11,0,0,0,0)`, no completed slices and no witness/event.

After independently hashing retained reuse checkpoint `2e16b2fd41145310dd0678a01ee91e4a7c5d09e6bacbe793c7bad82eb9b7e46e`, the bytes from absolute offset 622 onward match the new checkpoint exactly. This starts at control and includes counters, orders, and all frames while excluding changed identities, parent, and chain. No old-source replay was used.

Query counters match exactly: domain probes 49,893; batch probes 11; cursor checks 320; interrupted scans 0; restore probes 16,631.

## Measured costs and scope

| Measurement | Readonly eleven nodes | Prior reuse eleven nodes |
| --- | ---: | ---: |
| Operation seconds | 0.562944208 | 14.702255583 |
| Save/validation/publication seconds | 0.209046375 | 3.681973833 |
| Outer seconds | 0.9688707080058521 | 18.605715999991 |

Readonly construct/restore took 13,738,042 ns, map check 4,511,834 ns, and child through-report time 800,967,917 ns. Supervisor time was 0.920437959 s; helper elapsed time 0.9000426249986049 s with 19 samples and peak 52,256 KiB. Cleanup was clean in one sample / 0.012405500 s. Root outer time was 0.176170583 s, supervisor 0.133729333 s, helper 0.101630958 s with two samples and peak 49,456 KiB; clean cleanup took one sample / 0.010953958 s.

Physical counters describe the declared mutation engine only. They omit readonly-query line walks, memory reads, and determinants, so their completeness is not a statement that every CPU operation is counted. The traversal records 22,876 increments, 20 orbit attempts, 3,320 pair lines, and 80 point attempts. State total and validation extra each record 22,955 increments, 21 orbit attempts, 3,321 pair lines, and 82 point attempts. Restore subset records 79 increments, one orbit attempt, one pair line, and two point attempts. Physical total records 45,910 increments, 42 orbit attempts, 6,642 pair lines, and 164 point attempts. Inverse increments, undone points, rejected orbit attempts, and aborted orbit attempts are zero throughout these records.

## Next allocation recommendation

Recommend one separately allocated 250-new-node continuation from exact accepted checkpoint `4f5a32b89158a3d870dee399e93ea4ee4a36c8eeb704db1e44cf7d4e58c52141`, retaining 30 seconds / 256 MiB / 2-second reserve and the current frozen source identity. Linear extrapolation of operation time alone is approximately 12.8 seconds, but branch/depth costs can vary and this is not a completion guarantee. The bounded stage may checkpoint earlier. This recommendation authorizes no implicit retry or further allocation; Root owns launch and aggregate accounting.
