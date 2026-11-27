# Cooling pilot v2: actual review

Accepted one clean execution yielding an invalid 158-point full state with exactly 84 collinear triples. This is fewer than the constant-temperature pilot's 184 triples, but neither state is a valid certificate and the best valid cardinality is unchanged. These are one-run observations with the same seed and initializer; acceptance choices and subsequent RNG trajectories diverge, and wall-time limits affect iteration counts. No general efficacy or statistical conclusion follows.

Independent reconstruction of pi and its reflected matching matches all saved points, confirms 158 distinct in-bounds points, two in each row and column, and half-turn symmetry. An exhaustive integer-determinant count yields exactly 84 triples. The initial score 502 agrees with the separately independently reconstructed baseline initializer. Final-current score 84, 93,002 proposals, 5,751 accepted moves and 12 resets are execution-reported metrics; only the best state is saved for independent reconstruction.

Source pins/current/receipt agree. The owned 30s/256MiB gate exited zero with clean cleanup; outer elapsed approximately 25.1744s and peak sampled RSS 46,032KiB. Final temperature is 0.02 to floating-point precision. The preceding v1 monitor failure remains recorded and charged 21.412821375s; it supplied no state or mathematical result. No further paired-color allocation is approved.

Detailed audit `data/paired-cooling-seed279401-v2-independent-audit.json`, SHA256 `86006f5478c3ab32fe8c7ab9992bd0349375f42276731e71e6fddb9e35ed4883`. Normalized state SHA256 `c8c765b3a70f729d3474519920af3b18ac1a3f3a69ce0cbf34311495c7b9e84f`.
