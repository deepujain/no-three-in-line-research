# Independent mathematical review

Reviewer role transition: the Literature Researcher became Mathematical Reviewer. Assigned model: gpt-6.1-terra, reasoning effort high (per parent assignment). Review date 2026-11-26.

## Claim 1: odd side length and quarter-turn symmetry

Correct for an invariant set under a 90-degree rotation about the grid center. When n is odd, the center is a grid point. The only orbit of size less than four is that center, of size one: there are no distinct two-cycles because a 180-degree rotation fixes only the center. Thus the cardinality of any invariant set is 0 or 1 modulo 4, while 2n is 2 modulo 4. No such set has size 2n. This cardinality argument needs no non-collinearity assumption and includes n=1, for which 2n points are impossible even without symmetry.

This does not rule out a 2n-point set with half-turn symmetry, with no rotational symmetry, or with the rct4 near-quarter-turn pattern (which is not an invariant quarter-turn set). Nor does it address approximate symmetry or show anything about even n.

## Claim 2: one-hole border extension

Correct under these hypotheses: S is a full 2n-point no-three-in-line set in an n×n square, embedded as a contiguous corner n×n subgrid of the (n+1)×(n+1) square; exactly one old point (a,b) is removed; all other old points are kept; and exactly three points are inserted in the newly exposed row and/or column to obtain 2(n+1) points. Every old row and column of S originally has exactly two points, so all but row b and column a remain saturated. The only possible border cells in the old rows or columns are respectively (new_column,b) and (a,new_row). As the two new lines must each have two points and those two positions contribute one to each line, the corner (new_column,new_row) is also forced. In the top/right embedding this is precisely (a,n),(n,b),(n,n). Conversely these forced points yield a full witness only if all collinearity checks pass; saturation alone does not imply that.

The argument also holds for each of the other three corner embeddings, replacing n by the corresponding boundary 0. It does not cover noncontiguous compression, general reconfiguration, removal of two or more old points, or new solutions that do not contain 2n−1 points of this seed. It does not prove that any full extension exists or that 79 is impossible.

## Independent audit of the published 78 seed

Run `python3 research/review_one_hole.py` from the research workspace. The script independently checks coordinate range, uniqueness, two points in each row and column, and every one of the 620,620 seed triples using exact integer determinants. It then checks all 156 possible deletions at each of the four contiguous corner translations. For each forced triple of new border cells, it separately checks triples with one new and two retained old points, two new and one retained old point, and all three new points. The output is `data/one-hole-audit.json`, including the seed file hash, offset, candidate counts and first failure categories. Result: **624 examined, zero valid**, with all 624 already failing the one-new/two-old check. First failure categories are not counts of all violating triples.

The independent audit gives no new 158-point witness. It exhausts only the explicitly described one-hole family for this particular published 78-point-grid solution. Seed provenance and source-code hash are recorded in `data/published-n78.json`; the witness comprises 156 points, not 78 points. No literature-priority claim follows from this finite negative result.

## Code review

`src/constructions.py`'s one-point generator correctly expresses the forced triple for the particular embedding with new coordinates x=n and y=n, enforces domain and row/column saturation, and explicitly delegates geometry validation. The other corner embeddings are captured by the independent audit, not generated directly by that function. Its parabola and norm-conic modular arguments are appropriate for odd-prime conics; lifted parabola occupies a p×2p rectangle, as documented. A generator is not itself a certificate verifier; independently validate produced sets.

The subsequent proof-language review of `research/mathematics.md` found the odd-quarter-turn and forced-one-hole arguments valid with their stated scopes. The finite-field arguments and the p×2p lift also correctly distinguish modular sufficiency from Euclidean necessity. The odd-grid rct4 exception and the distinction between solver timeout and proof are explicitly maintained. No substantive mathematical correction was identified in this review.
