# Independent audit of size-three anchor histories

Both selected partitions reached `status=complete` and `selected_frontiers_complete=true`. Their 224 disjoint anchor ordinals cover 10072–10295, with 112 anchors and 1,302,336 recorded completed cases per partition. Each anchor has a 11,628-case frontier; the combined 2,604,672 anchor cases overlap and are not a count of distinct deletion sets.

`research/audit_corner_three_records.py` checked both terminal cursors against the manifest, source identities, exact ordinal selection hashes and batch-source hash; checked all 224 tips and the full hash-linked chains, their identity fields and contiguous offset coverage from zero to 11,628; checked nonnegative per-target counts and valid counts no larger than tested counts; inspected witness files; and rehashed all 13,664 referenced files, the cursor files and inputs at the end of the audit. All 13,664 directory JSON files were referenced, with no extra JSON or witness files. The two cursors reported no witness events. No numerical repair cases were replayed, so the counters and their execution remain trusted computation, not an independently proved enumeration. The observed embedding-worker file hash is recorded as an input snapshot; the record chains bind the batch source, not the embedding-worker file.

The records sum to 2,680,200 tested addition subsets for target 157 and 12,672 for target 158. Both valid counters are zero. These facts concern the two selected size-three anchor partitions of the recorded source and corner; by themselves they do not establish a whole-family or unrestricted impossibility result. Synthesis with other audited anchor families and the mathematical completeness argument is separate.

Audit artifacts:

- Script SHA-256: `18e3f8713ffd7a68e2c7dda79bb2380a8b7e8bef3ec1fa55e4e2623cfe5bda6d`
- Summary SHA-256: `0bd50f9dcb770871099829b41b8ba2b44d78d351bee6b18f58e3eb29f9c4c1ae`
- Combined sorted relative-path and file-hash index SHA-256: `4f221573d1c5b512641ccbf2e9a770863515260c3f64b67f2157c9212a95f5fc`
- Cursor hashes: partition a `10f2e36f1438d77e47581860aa8bb2de0abb746fc525b32b1f7553bbeb18502b`; partition b `7d5e64d41220f031903721f206ee424db5d101744419eab6a9198f507a0b4d3e`.

The original records and cursors remain in place. The script refuses to write a completion summary unless both cursors are complete and its checks succeed.
