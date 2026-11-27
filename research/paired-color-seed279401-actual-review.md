# Paired-color pilot: actual review

Accepted one clean bounded execution, yielding an invalid 158-point full state with 184 collinear triples. There is no valid witness and no improvement to the best valid cardinality. No unchanged repeat is recommended.

Independent reconstruction from best_pi exactly matches all reported points, gives 158 distinct in-bounds points, two in every row and column, and half-turn symmetry. Exhaustively counting integer-determinant collinear triples gives exactly 184. Replaying only the seeded initializer, without running another walk, and independently counting its triples gives the reported initial score 502. The restricted paired-color representation does not exhaust all half-turn configurations.

The execution reports 87,142 proposals, 17,077 accepted moves and 16 resets to its best state. Those counts are accepted execution metrics, not independently replayed wall-time trajectory evidence. Source hashes remain pinned and unchanged. The owned 30s/256MiB gate exited zero with clean cleanup: outer elapsed 25.381311625s, peak sampled RSS 46,512KiB. Final validators may use O(n^3) storage; current/best walk storage has no growing history.

Independent audit `data/paired-color-seed279401-independent-audit.json`, SHA256 `4b9bbe72900463ed1156febcdb6244f96dd42ceb238de32c2ce4ceb520afc79a`. Normalized state SHA256 `a283aecf79afa3c2858d86d6224d7314814bcb8d9e697665cf6fe1c373c4f109`.
