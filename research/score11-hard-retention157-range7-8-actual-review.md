# Intrinsic deletion-range7..8 actual review

Decision: accept **solver-reported scoped UNSAT** for target157 with intrinsically seven or eight effective source deletions. Geometric clauses, final candidate and formula counts were independently audited. No independent UNSAT certificate or solver replay was performed.

The job completed cleanly in8.441613 seconds at88,256 KiB sampled peak RSS. All35 receipt source pins match current files. The report records177 models and177 complete conflict scans, zero partial scans,7,380 fresh cuts, no imported cuts, no witness and no improved invalid candidate. These full-run counters remain reviewed source-pinned execution provenance: unretained earlier models were not independently replayed.

The independent audit directly checked all7,380 saved cuts by integer determinant. Every cut is a distinct collinear triple of legal distinct board cells; none duplicates the11 independently enumerated original source triples. The last candidate has157 distinct points, row/column counts at most two,8 effective source deletions,150 retained original points and7 new points. Its normalized identity matches, and direct enumeration finds exactly37 collinear triples, all present in the fresh cut artifact. It is explicitly invalid.

A separate construction from the mathematical constraints used the same pinned cardinality library but neither production formula builder. It reproduced58,108 variables,2,542 upper-bound clauses,1,970 lower-bound clauses,103,583 initial clauses and246,087 initial literal entries. After the saved cuts, the formula has110,963 clauses and268,227 literal entries. The canonical final clause-multiset SHA-256 is `40e72779a2fbcba18034d4a1fe70f9c7ffd1c708a363f80642d38efc28842583`. Formula agreement and cut validity support the native result but do not independently prove UNSAT.

The intrinsic range does not assume the earlier D6 result. Conditional on both separate native results, their union excludes target157 configurations with at most8 effective deletions from this fixed source. Each result also conditionally covers target158 in its same deletion scope: any valid158-point set differs from the invalid source and contains a non-source point; deleting that point preserves the retained source count and produces a valid157-point set. This is a source-neighborhood conclusion only, with no global n79 bound.

Audit: `data/score11-hard-retention157-range7-8-independent-actual-audit.json`, SHA-256 `a4a1f15d8990df04b8cdaf3725e8a1d5ffb7c00637c0b8ec8dab6943ae61de29`.

No broader deletion range, second backend, or additional numerical allocation follows automatically from this review.
