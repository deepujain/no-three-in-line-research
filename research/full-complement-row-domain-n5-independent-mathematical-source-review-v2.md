# Independent mathematical SOURCE review: fixed n5 full-complement domains

Verdict: SOURCE PASS on the exact identities below. This is not a normal geometric PASS or permission to execute one. The independent review executed only syntax compilation, trapped rejection-before-geometry checks and synthetic counter checks. No valid fixture geometry, row-placement enumeration, optimizer, actual input, old-family continuation or alternate fixture was executed.

## Frozen scope and identities

All paths are relative to this research workspace. SHA-256:

| Artifact | Digest |
| --- | --- |
| `research/full_complement_row_domain_n5.py` | `36f4639fededa4fd0e239e397acb43478e7131ee4a1d0f798079d73cf34b5b8e` |
| `research/full_complement_row_domain_n5_tiny.py` | `68ed3a3d6039f1c1c2aecce08509a699f5f5ad54840aa46ae16ae87c4a452f3a` |
| `data/full-complement-row-domain-n5-fixture-v1.json` | `5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37` |
| Accepted implementation spec | `9a50e2a36b154a1a3fa0cccde4b221e90e567c4042e0c4611b309697c9f81239` |
| Independent mathematical design review | `151ef0111b4effb501d7d394c4d19919283c2dc8034c8c6a668af9f4ce031d5b` |
| Independent diagnostic design review | `740bae5f2dcb90bae4f0b7f4b1773b02e8c5646dcbda80de70da90abfda5032e` |

The fixture is exactly 72 ASCII bytes without a newline. Strict validation precedes all producer geometry: integer n5, nine distinct in-grid integer cells excluding booleans, fixed row loads, canonical sorted cells, compact JSON identity and digest. A different state with the same loads rejects. Imports contain no geometry invocation.

## Mathematical source findings

The producer counts each baseline triple and each unordered pair in each full row complement once. For a same-load replacement, no conflict contains two new row points and a retained point: their horizontal line has no retained point. At most two new points also preclude an all-new triple. Thus subtracting the current unary sum from the baseline and adding the selected unary sum gives the exact replacement score. Choosing the k cheapest `(cost,column)` pairs and sorting their columns gives the lexical least minimizing tuple. Current and chosen columns fit four columns; ascending fill is deterministic and preserves both assignments.

The independent direct scorer uses adjacent edge vectors rather than calling producer geometry. The line scorer uses exact integer coefficients, gcd normalization and a fixed sign; each unique line carries distinct endpoint sets. Summing C(m,3) counts every collinear triple once. For unary verification, summing C(m,2) on retained lines incident to a candidate counts precisely its retained collinear pairs. These oracles share the budget infrastructure but do not share the producer's geometry or each other's arithmetic implementation.

The harness source enumerates exactly 45 same-load placements, checks all 25 unaries, validates minima with lexical ties, reconstructs domains independently and compares the baseline K census. The expected baseline 14 and singleton unary `(6,6,2,1,1)`, winner `(3,)`, score 9 and domain `(0,1,2,3)` are hand-derived expectations only in this review; they have not been evaluated here.

A strict replacement must remove an old conflict, since preserving every old conflict cannot reduce the count. Old conflicts have three distinct rows. Current inclusion plus winner inclusion therefore supplies a feasible assignment in an eligible K-positive block. The harness selects an independently counted positive block containing each strict winner, preserves other selected rows, verifies individual and total loads, and checks exact equality to the one-row replacement before dual scoring. Choosing any such block suffices because the other rows remain current; the selected block need not identify the particular removed conflict. This establishes the intended existence check, not prefix visitation, a new route beyond the old domains, or a four-row barrier.

Each producer/direct determinant, pair-line construction and candidate-line incidence is charged before its corresponding arithmetic. Static accounting is 644 producer determinants, at most 4,284 direct-oracle determinants, at most 1,948 total line keys and at most 560 incidences. Shared hard limits are respectively 6,000, 2,000 and 600. The harness checks component counts and derived totals. Bounded maps and scalar placement records follow the accepted specification; these are operation/object bounds, not measured time or RSS.

The v2 harness authenticates producer and canonical fixture bytes at entry, records its own digest, then compares a fresh identity snapshot immediately before immutable success writing in `main`. The source check is correctly outside `run_normal`; direct callers of that function would need their own final identity comparison. Evidence is capped at 64 KiB, written with exclusive creation and failures use a separate path. The earlier harness remains preserved. Root's later owned gate must still bind these exact reviewed identities before and after the process and enforce its separately allocated resource limits.

## Independent permitted evidence

Runner: `research/full_complement_row_domain_n5_independent_pregeometry_v2.py`, SHA-256 `f04d223b43d9118f0dd1e8b77e7f20fb22288d772d5cf346f828fd50d98076b5`.

Evidence: `data/full-complement-row-domain-n5-pregeometry-independent-v2.json`, SHA-256 `fa1301ad27f54a011cf8131da6e0d13fe6ec2c197f88e0517119e057865a8d99`.

Results: two syntax compile passes; 10 invalid-input rejections with zero geometric charges; three seeded counter boundary checks; four pure identity-drift rejections; zero calls to trapped producer determinant, direct oracle, line-map or normal-run functions during pregeometry checks. Two additional synthetic calls with unusable coordinate sentinels and already exhausted budgets raised `BudgetExceeded` before coordinate access and left counters unchanged. Exact source/fixture identities match before and after all checks. Real geometric operations: zero.

No mathematical source defect was found. A normal pass remains unrun and separately owned by Root; any later mismatch or failure must be retained and stops the gate without retry, adaptive fixture replacement or scope expansion. This review makes no claim about actual-state improvement, a valid no-three-in-line construction, or reopening the curtailed family.
