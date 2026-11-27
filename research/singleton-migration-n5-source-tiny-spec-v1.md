# Singleton migration: minimal n5 SOURCE/TINY specification

Status: DESIGN/SPECIFICATION ONLY. No source implementation, migration geometry, new fixture or execution is authorized here. The mathematical design `research/singleton-migration-one-cell-design-v1.md` has SHA-256 `9348e40a25c2c57a3bcbc117262cc93901f0b0ea0ff30309346ce240d40809b3`; its separate independent acceptance is `460c964dbeae1e1309fb0586a24b9538759ac9c029ca77df54a31aa96dc5b12e`. Root decides whether this specification becomes a later task. Finishing the current all-row gate takes priority.

## Sole input and question

Use only the already approved n5 fixture, `data/full-complement-row-domain-n5-fixture-v1.json`, SHA-256 `5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37`, exactly 72 ASCII bytes. It contains columns 0 and 1 on rows 0 through 3 and column 0 on row 4. The accepted baseline is 14. Strict canonical identity, nine distinct in-grid integer cells excluding booleans, and row loads `(2,2,2,2,1)` must be checked before geometry.

This fixture already has same-load one-row gains. It can test migration arithmetic and legality, but cannot demonstrate an escape from a no-gain same-load state or justify an actual-state migration. No reflection, alternate state, searched example or old-family continuation is included.

## One complete read-only relocation sweep

Let p be any of the eight current points outside singleton row 4. Let q=(x,4), with x in `(1,2,3,4)`. Delete p and insert q. These are exactly 32 legal moves: total nine points remain, row 4 becomes full, p's source row becomes singleton and every other row is unchanged. The current state is fixed throughout the sweep. No candidate is adopted or used as another input.

Define d(p) as the old conflicting triples containing p; c(q) as the unordered old point pairs collinear with q; and h(p,q) as the old points t other than p collinear with p and q. The exact score is

    U' = U − d(p) + c(q) − h(p,q).

The correction removes from c the pairs that disappear when p is deleted. Strict gain requires d(p)>0, so filtering those removals is safe. Select at most one strict global minimum using the declared total key `(score, source_row, removed_column, inserted_column)`. This is the deterministic move-key order, not a claim about lexical order of complete point sets. A completed negative sweep excludes only these 32 relocations.

The producer counts U and all nine d values in one 84-triple determinant pass. For each of four q values it visits all 36 unordered current pairs once. A successful pair increments c(q) and h at both endpoints. This is 228 determinant tests total. Return only the baseline, bounded d/c/h arrays and sole proposed move (or no strict move); do not retain candidate point sets or build a controller.

## Independent checks and the sole candidate

An independently written primitive direction/intercept line table with distinct endpoint masks supplies a separate formulation. For a line with m current endpoints, add C(m,3) to the baseline and C(m−1,2) to d at each endpoint. For each empty q incident to that line, add C(m,2) to c(q) and m−1 to h(p,q) for every endpoint p. Check all nine d values, all four c values and all 36 h values against the producer. Require both baselines to be 14, sum d=42 and each sum_p h(p,q)=2c(q). The old singleton's h values must be zero. These identities supplement rather than replace the independent line checks.

Independently form the scores of all 32 legal removals/insertions from the verified arrays and compare the producer's strict minimum and complete move-key tie. This uses scalar arithmetic, not 32 geometry evaluations. No current K-positive-block condition is imposed: the destination row need not be in the removed conflict's row triple.

If the selected score is strict, construct exactly that one nine-point candidate. Independently check the exact deleted and inserted cells, unchanged remaining points, total count, distinctness, bounds and swapped singleton/full row loads. A fresh direct triple scorer and a fresh endpoint-line scorer must both equal the predicted score and canonical candidate identity. Do not reuse the producer's determinant routine or its d/c/h score formula as these raw oracles. Any disagreement stops; no other candidate is tried. A zero would need separate witness acceptance; a positive raw score remains diagnostic, not a construction. No strict move means no candidate is constructed.

## Bounded gate proposal and failures

Shared pre-operation hard ceilings can equal these conservative maxima:

| Work unit | Maximum |
| --- | ---: |
| Producer determinants plus sole candidate direct triples | 228+84=312 |
| Current independent plus candidate pair-line constructions | 36+36=72 |
| Current line/empty-cell incidences | 4*36=144 |
| Independent current/candidate multiplicity recoveries | 72 |
| Current-line endpoint visits for d and all h updates | 2*36+4*2*36=360 |
| Producer plus independent scalar move-score evaluations | 64 |
| Producer plus independent move-key comparisons | 64 |

Recover each stored line's multiplicity once and reuse it. Endpoint visits are bounded because m<=2*C(m,2) for m>=2. Report each component separately without resetting shared counters. State buffers are limited to the nine-point input, one nine-point candidate, nine d values, four c values, 36 h values, one best-move record and at most one 36-key line map at a time. No time or RSS guarantee follows from these arithmetic bounds.

A later separately owned proposal is one 10-second/128-MiB tiny gate, including all source/input authentication, independent checks and immutable output. It allocates nothing now. Evidence must be at most 64 KiB; a sole candidate/witness at most 16 KiB; separately preserve any failure. Bind exact source, fixture, reference and runtime identities before and after, cap publications, and use file/directory fsync for durable claims. Deadline, quota, drift, schema, score or persistence failures stop without retry, fixture substitution, wider search or partial acceptance.

Before that gate, freeze a minimal source closure and obtain independent source review. Permitted pregeometry checks would cover malformed/alternate identity rejection, synthetic exhausted counters and failure preservation; they must not evaluate another valid fixture. One successful tiny result would establish this bounded mechanism only. It would grant no actual75 input access, candidate adoption, iteration or new migration experiment.
