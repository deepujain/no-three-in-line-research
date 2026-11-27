# Independent matched 100-node reflection comparison

Both independently pinned, fresh-genesis (d,t)=(0,0) invocations completed with clean guards and accepted, structurally reconstructed frontiers at their 100-node limits; neither found a witness. The residual and control sources/receipts, initial-null predecessor, report/frontier hashes, limits, exact schema and branch order, counters, source identities and empty witness directories checked out. No numerical work was launched by this review.

| Variant | Outer seconds | Helper seconds | Sampled peak RSS KiB / samples | Frames | Frontier SHA-256 |
|---|---:|---:|---:|---:|---|
| Residual | 0.3885 | 0.3061 | 52,720 / 7 | 21 | `e68a185d896ab83c153d0ee5a550158b53970ed08d79c1d1d6c2d07a5e1a28af` |
| Frozen control | 0.2859 | 0.2028 | 52,464 / 4 | 25 | `195dd6d921fd2d4f4bbffb76c72e66fa71ccb6f0c7968c0d1f27e9162741c60f` |

Their first 17 frame records match; at the next shared incoming batch `[1799]`, the residual parent cursor is 2 while control's is 1, placing the residual frontier in a later sibling of that common prefix. This is evidence of different advancement, not a quantified coverage ratio: the pruned subtrees and per-node cost differ. Residual recorded 100 scans and overlapping rule hits: row shortage 35, component parity 3, bipartite imbalance 4, component color shortage 1; overlaps mean these counts cannot be summed into distinct prunes or attributed as gains over control. Residual's elapsed time was higher at this small quota, which includes fixed process and publication overhead; this one pair does not establish a throughput or useful-coverage advantage.

A single bounded fresh equal-quota pair at 5,000 nodes under unchanged 30-second/256-MiB guards is a proportionate next measurement. Compare saved frontier ordering and actual elapsed, diagnostic work, witness/terminal outcomes, and resource receipts, without assuming equal node counts cover equal subtrees. Retain the 100-node artifacts. If the larger sample shows no useful advancement or excessive cost, curtail this pruning branch rather than scale by node count alone. Neither limit proves infeasibility. Sampled RSS is not a kernel hard limit.

Receipt SHA-256: residual `d388f6769e02527f5d50e2d2257722ae74af04d3b8373999a96215971d733107`; control `dd06cf4f5c8b4f6e8c0ab27a2479498e8718cfeb884a6bdd7c114160a3c0a5c1`. Report SHA-256: residual `178d16787851dfc3598ac6968cc483cd9f5d1774208f8002a6ab80c5ca166144`; control `5e309c3b67d1692b0e0b1d13166a79cf6cd3e5c543c36de68de7a11972d746a7`.
