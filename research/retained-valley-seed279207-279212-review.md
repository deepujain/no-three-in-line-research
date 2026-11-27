# Independent retained-walk continuation audit

Both 25-second continuations completed with exit 0, unchanged recorded source/input pins and clean owned-process cleanup under the 30-second/256-MiB guard. I independently checked receipt/report/log bindings, provenance, transition and pass accounting, floor and both exact validators on both input certificates and both retained best/walk outputs. Both best certificates remain the original embedded 156-point seed. Sampled RSS is not a kernel hard limit.

| Seed | Starting walk | Final walk | Accepted size deltas | Final symmetric difference from starting walk | Final symmetric difference from original seed | Peak sampled RSS KiB |
|---|---:|---:|---|---:|---:|---:|
| 279207 | 154 | 155 | 0×4, +1×1 | 5 | 3 | 48,512 |
| 279212 | 155 | 153 | -3×1, 0×1, +1×1 | 8 | 5 | 48,592 |

The independently verified final normalized hashes are `3a8f83b97d48509526a7ff27b252ca4f654e2857e03631a4d7e801f8a5c66b63` and `13a8b0a4e132bf5768214ff5e1059fec0b94452607bcada8316d783fc63f307e`, respectively. These are actual retained distinct valid states, although intermediate accepted transitions are report evidence, not independently replayed. No best improvement or novelty was found.

The movement justifies at most one further fixed four-job batch: two fresh seeds starting from each independently verified final walk, retaining the separate original 156-point incumbent, drawdown 4, 25-second loops and one concurrent worker. Suggested seed pairs are 279307/279308 from the 155 state and 279312/279313 from the 153 state, with unique best/walk/report paths and exact source/input pins. Audit the terminal certificates and distances from the original seed, not only from each new initial walk. Stop or redirect if this batch fails to yield further useful movement or a verified improvement; changing a hash or dropping points alone is not a new bound. Fixed queue behavior must be explicit, including whether a witness or failure stops later jobs. No numerical work was launched for this review.

Receipt hashes: `4f926010349f3111a0f134ba1254f5f5812875aa6eadc5fc48ad0ac4d37370a6` (279207), `016f9e7617a8629223efc5930a2ecf95efe451be5753eb874503d88e336bf3e6` (279212). Final walk file hashes: `2b029475209b9690b6236e801a95a72715f59e54d18202afb4a553c0d1b9bd18`, `5d06bb9b1a4fbd3bfda6884527c54d45b8055a09ef4fcd49b77e6514078fd439`.
