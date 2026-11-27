# Independent matched 5,000-node reflection comparison

Both v2 invocations used fresh genesis in slice (d,t)=(0,0), exited cleanly and published accepted, structurally reconstructed 5,000-node frontiers. Pinned source hashes, receipts, exact identities, source and orbit hashes, counters, limits, empty witness directories and predecessor links checked out. Neither found a witness. The earlier v1 outer-command interruption is not performance evidence and was conservatively charged separately.

| Variant | Outer seconds | Helper seconds | Sampled peak RSS KiB / samples | Frontier SHA-256 |
|---|---:|---:|---:|---|
| Residual | 10.364 | 10.279 | 53,056 / 243 | `312b38298410bd12a6352e7777fa283e7a99c16b75d1d73ff4f540dbcefd3e2d` |
| Frozen control | 5.803 | 5.690 | 53,040 / 133 | `86461f821e6a611053b92255876d3d77ee3bad4d302821c4ee71ca56c7d59fb5` |

The first 18 frame records match. At the next common incoming batch `[589]`, residual cursor 8 versus control cursor 6 places the residual frontier at a later sibling, but does not quantify skipped work or equalize coverage. Residual recorded 5,000 complete scans and overlapping row shortage 2,063, bipartite 489, parity 201 and component-color 319 rule hits. These cannot be summed as distinct useful prunes or all credited against the control. Residual took about 1.79 times the outer wall at equal logical-node quotas; fixed costs are small relative to these runs, but different search paths prevent interpreting that ratio as a speedup or slowdown per equal coverage.

One bounded equal-time-oriented control measurement from fresh genesis, targeting about 9,000 nodes at the unchanged 30-second/256-MiB cap, is warranted to test whether the 5,000-node residual frontier remains ahead at approximately equal elapsed wall. Record the actual time and compare the first differing common ancestor, not merely the node rates. This is an approximation, not a time-matched experiment if elapsed times diverge materially. If residual is not materially ahead at comparable time, curtail this branch. No witness or impossibility claim follows. RSS is sampled, not a kernel limit.

Receipt SHA-256: residual `f0f24215d720159db5fc04e42d0827a484d763057e6c3c2aa1d1de89901549ea`; control `05e25ea058930d1885d470bca79bd66e1a12445a58ba370bf5ac451ed117f3a9`. Report SHA-256: residual `9b6697036a33a84a1ab2502b7f814c1d1163ab21895c38c2748dd629b85f2b01`; control `141c1cb861ac82094d27a0d7b72b1b17237443b77df91076c929bbcaf5201c5e`.
