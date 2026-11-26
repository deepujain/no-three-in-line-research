# Engineering record

Research software engineer configuration: model `gpt-6.1-sol`, reasoning `high`.
Runtime: Python 3.14.7; standard library only. Work is local, single-process, single-core; no remote publication and no subprocess workers.

## Exact certificate interface

A certificate is a JSON object with `n` (positive integer) and `points` (array of `[x,y]` integer pairs in `0..n-1`). Additional metadata is permitted. Booleans, floats, duplicate points, malformed pairs and out-of-grid coordinates are rejected. There is no tolerance or floating-point geometry.

`src.verify.verify_certificate(certificate)` returns a JSON-compatible report with `valid`, `n`, `point_count`, `errors`, `conflict_count`, `conflicts`, `normalized_sha256`, and `algorithm`. Every conflict contains its three input-order indices and their point coordinates. Schema errors suppress geometry checking and return a null hash. Collinear certificates with valid schema retain a hash and list all conflicting triples. An empty point set is valid.

The primary checker groups primitive unoriented integer directions at each anchor, covering every rational slope. The second checker, `verify_certificate_bruteforce`, directly evaluates the integer determinant for every triple and does not call the slope checker. Shared parsing/hashing is intentional; geometric decisions are independent.

Canonical hash input is compact sorted-key UTF-8 JSON, no final newline, containing only `{"n":n,"points":sorted_points}`. Sorting points lexicographically makes the hash independent of point order. Metadata never contributes. The `n=78` published witness independently passes both checkers with 156 points and normalized hash `e197d1b41f97df9188b9839a54f0013bbc08b67d202c18d26146a7f377d80ced`.

Examples, from the repository root:

```sh
python3 src/verify.py data/published-n78.json
python3 src/verify.py data/published-n78.json --brute-force
python3 src/search.py --n 8 --seconds 2 --seed 42 --output data/example-n8.json
python3 src/search.py --n 79 --seconds 30 --seed 42 --initial data/published-n78.json --delete-count 3 --output data/example-n79.json
```

Verifier exit codes are 0 valid, 1 invalid certificate, 2 unreadable/malformed JSON. Its stdout is a JSON report, including input read/parse failures; argparse usage errors follow standard argparse conventions. `-` reads stdin. The search CLI writes a certificate only after both checkers accept it, then emits the primary verifier report on stdout.

## Search behavior and limits

`src.search.search(n, seconds, seed, initial=None, delete_count=2)` returns a certificate. The random-start method puts two points in each column (one for n=1), moves a highly conflicted point within its column using seeded min-conflicts choices, allows random walks, and restarts on stagnation. At timeout a deterministic greedy conflict deletion returns a valid subset. The target is `min(n*n, 2*n)`.

With `initial`, both verifiers first audit that certificate and its fit in the target grid. The incumbent is retained throughout. The first pass tries direct additions. Subsequent passes remove between one and `delete_count` points from a copy, then test vacant cells in shuffled order, greedily adding compatible cells. Only strictly larger valid subsets replace the incumbent. This is a small heuristic neighborhood, not a completeness claim or an impossibility proof.

Metadata records method, seed, requested seconds, actual elapsed seconds, iterations, restarts, target, stopping reason, validation algorithms, and normalized hash. Initial runs also record initial size and hashes. For random starts, iterations counts point moves; for incumbent repair, iterations counts candidate-cell tests. Time-limited runs can produce different iteration counts/results from the same seed on different runs or machines. The budget stops the search loop; setup, pruning, independent audits, and output add overhead. There is no claim of exact deterministic time reproducibility.

## Actual local smoke runs

All artifacts below were independently validated before writing. Total recorded elapsed time for actual search calls was 20.982043 seconds, below the 60-second task cap. Tests use zero-time budgets or a mocked deterministic clock, so do not add sustained local-search spending.

| n | valid count | seed | iterations | elapsed seconds | artifact |
|---|---|---|---|---|---|
| 1 | 1 | 20261127 | 0 | 0.000081 | smoke-n1-seed20261127.json |
| 2 | 4 | 20261128 | 0 | 0.000148 | smoke-n2-seed20261128.json |
| 3 | 6 | 20261129 | 5 | 0.000478 | smoke-n3-seed20261129.json |
| 4 | 8 | 20261130 | 7 | 0.000347 | smoke-n4-seed20261130.json |
| 5 | 10 | 20261131 | 5 | 0.000859 | smoke-n5-seed20261131.json |
| 6 | 12 | 20261132 | 11 | 0.000943 | smoke-n6-seed20261132.json |
| 7 | 14 | 20261133 | 409 | 0.040382 | smoke-n7-seed20261133.json |
| 8 | 16 | 20261134 | 1669 | 0.207773 | smoke-n8-seed20261134.json |
| 9 | 18 | 20261135 | 1669 | 0.259972 | smoke-n9-seed20261135.json |
| 10 | 19 | 20261136 | 1562 | 0.300420 | smoke-n10-seed20261136.json |
| 79 | 156 | 2026112600 | 127907 | 5.043468 | smoke-repair-n79-dx0-dy0.json |
| 79 | 156 | 2026112601 | 126105 | 5.043600 | smoke-repair-n79-dx0-dy1.json |
| 79 | 156 | 2026112610 | 123226 | 5.042329 | smoke-repair-n79-dx1-dy0.json |
| 79 | 156 | 2026112611 | 128295 | 5.041242 | smoke-repair-n79-dx1-dy1.json |

The first nine sizes attained the trivial row upper bound (n=1 uses the grid-size bound). The n=10 short smoke run attained 19; no maximality claim is made. All small-n results are already known and carry no novelty claim.

The four n=79 initial artifacts translate the published n=78 witness by `(0,0)`, `(0,1)`, `(1,0)`, `(1,1)`. Their repair runs used five-second budgets and maximum deletion count three. Every run retained 156 points; none improved the baseline. These results say only that these specific seeded, bounded heuristic runs did not find an improvement. They neither prove nonextendibility nor rule out other neighborhoods or constructions. Published source attribution remains in `data/published-n78.json`; the translated and repair artifacts derive from that witness.

`data/smoke-summary.json` is the machine-readable run summary. Each `data/smoke-*.json` certificate preserves measured run metadata, except summary which is an array of run records.

## Validation

`python3 -m unittest discover -s tests -v` passed 26 tests at the engineering handoff, including the theory worker's six construction tests. Engineering coverage includes every 3x3 subset (512 differential comparisons), 200 seeded random subsets, positive/negative oblique slopes in every input order, all conflict multiplicities, huge integer near-collinearity, malformed schemas, bool/float rejection, canonical hashing, CLI error behavior, independent candidate-cost checks, deterministic-clock repair paths, and incumbent preservation. No theorem or novelty claim is inferred from these tests.


## Exact blocker audit follow-up

`python3 research/blocker_audit.py` exhaustively audited all 6,085 empty cells in each of the four n=79 translated published seeds (24,340 seed/cell cases), after validating the original seed and every translation with both exact checkers. The final recorded audit elapsed 1.070707 seconds. The script and its full machine-readable output are `research/blocker_audit.py` and `data/blocker-audit.json`. This is finite structural analysis of these seeds, not an additional stochastic search.

For a candidate cell c, primitive unoriented directions from c partition old points. The validated absence of old collinear triples ensures each direction group has size at most two. Size-two groups are disjoint blocking pairs; at least one old point must be removed from each pair before c can be added, and deleting one member of each is sufficient. Thus the number of such groups is exactly the minimum old deletions for that single candidate cell. This is a direct finite certificate observation, not a new theorem or a global extremal bound.

All four translations have the same histogram (minimum old deletions: number of empty cells): 2: 2; 3: 28; 4: 122; 5: 258; 6: 525; 7: 776; 8: 920; 9: 942; 10: 898; 11: 676; 12: 434; 13: 262; 14: 136; 15: 66; 16: 28; 17: 8; 18: 4. The minimum is **2**, attained at two cells per translation; the maximum is 18. Consequently deletion budgets zero and one cannot insert any genuinely new cell into any of these translated seeds. The maximum-three deletion neighborhood used in the earlier smoke runs is **not excluded** by this audit. The evidence does not justify pruning budgets two or three solely on this individual-cell criterion.

The saved first minimum witnesses are c=(77,78), (0,0), (0,77), and (0,78) for translations (0,0), (0,1), (1,0), and (1,1), respectively. Each witness records its two disjoint blocking pairs, point indices and coordinates, and an example choice of one deletion per pair. Both exact checkers accept the resulting 155-point certificate after the two deletions and one insertion; those hashes are recorded. This demonstrates individual addability after two deletions, not a cardinality improvement.

Independent validation checked 23 selected cells, including every saved minimum witness, by enumerating all old-point pairs and testing cross-product collinearity; exact pair sets agree with the slope grouping. A separate full four-translation n=2 square-seed audit also passed and checked histogram totals against all five empty cells per n=3 translation. Disjointness and size-at-most-two assertions ran for every audited empty cell. No external publication or remote writes were made.
