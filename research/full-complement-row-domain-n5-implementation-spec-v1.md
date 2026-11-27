# Full-complement row domains: minimal n5 SOURCE/TINY specification

Status: DESIGN ONLY. This file specifies possible later source and tiny work; it implements and executes none of it. No fixture enumeration, geometry evaluation, numerical allocation, actual input access, production change or retry is authorized here. The unchanged K-positive/four-column three-row family remains curtailed. The preceding exploration assessment is `research/four-row-overlap-predetermined-fixture-assessment-v2.md`, SHA-256 `f03402515dd7f8c0fcd4669a9052b69806e14e802de00b2193128a4b776e3673`.

## One fixed diagnostic and the question

The sole proposed tiny input is n5 with these nine (column,row) cells, listed by row then column:

    ((0,0),(1,0),(0,1),(1,1),(0,2),(1,2),(0,3),(1,3),(0,4))

Rows0..3 contain columns{0,1}; row4 is the singleton{0}. This is a fixed mathematical construction, not the result of an executable search. Its only conflicting lines are the two verticals: five points at column0 and four at column1 give C(5,3)+C(4,3)=14. A nonvertical line cannot contain three of these points, since there are only two distinct columns and two points sharing a column determine a vertical. This baseline14 also satisfies the frozen production selector's65 ceiling, although no production selector is needed for this diagnostic.

Question: does the source construct deterministic current-inclusive domains of at most four columns containing an exact best same-load one-row replacement against the **full fixed complement**, and do two independent tiny oracles verify the costs, ties and existence-preservation claim on this input? The input need not be a barrier or expose a new route. No second state, reflected/rotated variant, seed, alternative singleton, alternate block or adaptive replacement is allowed. Row-placement candidates within this one state are the specified finite oracle, not additional fixtures.

The stronger original-production comparator is **unnecessary and excluded**. It tests whether a diagnostic demonstrates a new route beyond the old policy, which is a different claim. This implementation claim concerns domain correctness and preservation of an existing one-row improvement. It does not require failure of old production neighborhoods or common-domain three-active faces. No four-row optimizer, face oracle, production triple optimizer, full candidate-list scan or comparison to the actual64 state belongs in the minimal work.

## Proposed pure source contract

After separately explicit SOURCE/TINY authorization, a minimal proposed source path is `research/full_complement_row_domain_n5.py`. It must be independent of actual loaders, workers, controllers, indexes and persistence. No command-line input reader, discovery, imports of production search modules, randomness, clock-based search, alternate input or actual adapter is required. Only the tiny entry point below may invoke it in the authorized work, on the exact literal state above. Any broader input API or use needs another review; no n6..8 or n75 execution is included.

The pure operation returns a baseline raw score, current K-positive row triples, five length-five full-complement unary vectors, the five lexical best row assignments, their full raw scores and five domain tuples. A caller supplies the strict operation-budget object. Validate strict integers (reject booleans), n==5, the exact nine distinct in-grid cells, row loads2,2,2,2,1 and canonical identity before any geometric operation. Arrays/results contain no executable callbacks or filesystem objects.

For each row r let A_r be its current columns, k_r=|A_r| and R_r=P without row r. For each column x in0..4 compute

    u_r(x) = number of unordered pairs {p,q} in R_r
             for which (x,r), p, q are collinear.

Use the entire current complement R_r, including points in rows that a later triple block might select. This is different from the old retained-only unary after removing three rows. Count each retained pair once with exact integer determinants. There is no row-placement enumeration in this producer.

The exact identity for every legal k_r-column replacement X is

    U(R_r union {(x,r):x in X}) = U(R_r) + sum_{x in X} u_r(x).

Two replacement points lie on the horizontal row r. No retained point has that row, so a triple containing both replacement points cannot conflict. Three replacement points are impossible because k_r<=2. Thus no pair interaction between chosen columns or missing geometric term remains in this one-row problem.

Choose B_r as the k_r columns with smallest pairs (u_r(x),x); sort the chosen columns increasingly for its output tuple. This minimizes the exact full score, and choosing the smallest columns at tied boundary costs gives the lexical least minimizing tuple. Set the seed domain to A_r union B_r; append missing columns in increasing column order until its size is exactly4; return the sorted tuple. Current2 plus best2 uses at most4 columns, while singleton1 plus best1 uses at most2. Never drop a current or best column. No unary tie may depend on iteration order or point order. Fill does not call another oracle or rank by an unstated criterion.

Compute one direct raw baseline score U(P), also collecting current conflicting row triples. Derive each best full score as U(P)-sum_{x in A_r}u_r(x)+sum_{x in B_r}u_r(x), using the same-row identity. Do not claim to have independently validated that identity merely because this formula agrees with itself; the separate tiny oracles below must check it.

## Existence-preservation claim and its limits

If row r admits any strict replacement preserving k_r, its exact best B_r is strict. At least one **old** conflicting triple is removed: if none were removed, every old conflict would persist and any new conflicts could only increase the score. This persistence argument corrects the preceding assessment's too-strong wording suggesting that no removed conflict would imply zero old conflicts involving the row. The conclusion, not that intermediate wording, is retained.

Every old conflict uses three distinct rows, since row-valid states have at most two cells per row and horizontal lines contain no other-row point. A removed conflict containing row r therefore supplies a current K-positive triple (r,s,t). In the new domains, B_r in row r and the unchanged assignments in rows s,t are all present. Preserving their individual loads preserves total5 or6, hence gives a legal three-row assignment with the strict one-row score. The guarantee is existence of a strict best replacement in some eligible triple; it does not preserve every arbitrary strict replacement, require the optimizer to choose it or ensure a finite prefix visits its block.

This theorem establishes neither a local minimum nor necessity of changing three/four rows. It offers no conclusion if all rows lack a strict same-load replacement, and excludes changing which row is singleton. No actual64 property, new domain-route separation, zero construction, unrestricted minimum or reason to reopen the curtailed algorithm follows.

## Independent tiny oracle and predetermined checks

A proposed later tiny entry point is `research/full_complement_row_domain_n5_tiny.py`, with one immutable aggregate evidence path `data/full-complement-row-domain-n5-author-tiny-v1.json`. These paths are reserved names in this specification only; they are not created here.

The test must not call the producer's scoring or collinearity routine as its oracle. Independently enumerate the10 two-column sets on each of rows0..3 and the five one-column sets on row4, always holding every other row fixed:45 placements. Include a separately scored baseline. Use a direct determinant raw scorer written independently of the producer, and a second exact canonical-integer-line scorer built from unordered point pairs and endpoint sets. For every one of the46 scored states require equality of both raw scores, valid row structure and canonical point identity. Compare every producer B_r and reported best full score to the independent minimum and lexical tie over that row's enumerated candidates.

Independently check **all25 unary cells**, rather than trusting only minimizing columns. For each row complement, construct canonical retained-line endpoint sets using its unordered pairs. For every candidate column, sum C(m,2) over retained lines through that candidate. This line-incidence result must equal the producer's determinant pair count. Canonical lines use normalized integer coefficients and exact gcd/sign conventions, with no floating-point tolerance. The independent implementation must not reuse producer determinant or cost code.

The singleton supplies hand-derived expected values: its retained base is8, and u_4 across columns0..4 is (6,6,2,1,1). The first two counts are vertical pairs. For column2 the cross-column pair equation is2*y_1-y_0=4 and has two retained solutions; for column3,3*y_1-2*y_0=4 has one; for column4,4*y_1-3*y_0=4 has one. Thus lexical B_4 is(3,), its full score is9, and the new filled domain is(0,1,2,3). These are mathematical expected values, not results of an executed evaluation.

For each strict row winner (at most five), choose the lexically first original conflicting row triple containing it from the independent baseline census. Require positive current K for that triple, complete current assignments in every new domain, the winning B_r contained in its row domain and legal preserved individual/total loads. Construct only that embedded point set, verify that it equals the independent one-row replacement, and score it with both independent raw oracles. It must have the same strict score. This tests the promised feasible assignment; do not optimize the remaining triple assignments. The known singleton gain ensures this diagnostic exercises at least one positive existence case, with no barrier claim.

Schema/typing/duplicate/out-of-grid/identity mutations must reject before geometry. Budget boundary injections use synthetic counter/thunk callbacks and must not re-evaluate valid geometry. A successful normal pass is executed once; no retry follows a fault or mismatch. Do not substitute another input because expected gains or ties differ.

## Exact work, storage and failure contract

One normal producer invocation has exactly84 baseline determinant tests and at most560 unary determinant tests: four full-row complements give4*5*C(7,2)=420 and the singleton gives5*C(8,2)=140. Producer maximum is644 determinants. The independent direct oracle scores46 states plus at most five embeddings, each with C(9,3)=84 triples, hence at most4,284 determinants. Combined real geometric determinant maximum is4,928; require a shared hard cap of6,000, checked before each operation.

The independent raw line oracle constructs at most51*C(9,2)=1,836 pair-line keys. Independent unary verification adds4*C(7,2)+C(8,2)=112 pair-line constructions, giving at most1,948 total. Use a shared hard cap of2,000, checked before each construction. Independent unary verification has at most560 candidate-line incidence checks; cap these at600. No equivalent geometric calculation may escape the relevant counter by an alternate function name. Report producer, direct oracle, raw-line oracle and unary-line checker counts separately as well as shared totals. Synthetic quota-boundary tests are labeled and never charged as successful geometric work.

Retain at most the one nine-point source state, one nine-point candidate at a time, five current/best/domain tuples,25 unary integers, at most45 scalar placement records, at most five scalar embedding records and at most10 K-positive row-triple records. Per-assignment raw line maps have at most36 keys; a row-complement line map has at most28 keys and is released before the next row. No list of all point-set candidates, full-grid state family, historical graph, index or search controller is retained. These are explicit object/count bounds, not a physical-memory proof. Evidence must fit64KiB and be written immutably only after the single test pass; preserve any failed output separately. Source and fixture literal identities must be frozen and independently reviewed before execution. A later expressly authorized owned SOURCE/TINY check may use a proposed10-second/128-MiB ceiling; this document reserves none of it and predicts no runtime/RSS.

PASS requires every fixed-input/score/unary/tie/domain/current-inclusion/embedding/independence/count check, the singleton expected values and rejection-before-geometry/quota guards. Any exception, unexpected source/fixture drift, exceeded cap, malformed result, mismatched count/score, missing current/best column or unaccounted geometry rejects the entire evidence. Stop immediately; no partial success, fallback, wider domain, extra fixture or automated retry. Existing production comparator and four-row experiments remain outside scope. Only after independent DESIGN acceptance, explicit implementation authorization, exact-source review and a separately allocated tiny gate could the implementation be evaluated.
