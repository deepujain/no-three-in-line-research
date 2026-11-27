# n73 one-four-orbit proposal: arithmetic review

Approved the finite scope and arithmetic for minimal standalone source/tiny implementation, subject to Root's authorization. No host allocation is approved until source review. No n73/n79 geometry was run for this arithmetic review.

Proposal SHA256 `4cceeb61a9799afb599a2a51dee63369773b7829f54e497d1fb34a5db8933ef9`; manifest `ca6147bee2ae9bcde4118f2ccdfb855af87c44cd5dd49e2aa3ec60580fbeabae`; author's arithmetic evidence `946851d055372c5d41e231be3cbca647f5afd441ef535d19ada4c828ccbeeb59`. All hashes and manifest fields match.

Independent repeated quarter-rotation partitioning confirms exactly 36 original full four-orbits and diagonal pair (17,17),(55,55). The unique central orbit is sorted index3, (1,36),(36,1),(36,71),(71,36), with radii0,35. The manifest gives every original orbit exactly once and all expected counts. Positive inner radii can reach36, distinct from outer37,38,39 after translation by (3,3).

Deleting one four-orbit leaves142 points. Four new full four-orbits produce158. Saturation of retained rows and columns restricts candidate endpoints to the two freed inner radii and three outer radii. Their quotient demands are1,1,2,2,2, also when the first inner radius is zero because a zero-incident orbit fills two central-row positions. Positive radius pairs have two orientations; zero-incident pairs one. Equal-radius edges would lie on excluded diagonals.

Independent enumeration of all171,395 raw four-edge subsets over every actual source radius pair found35 positive cases with124 degree choices each and one central case with62. Exact removed-orbit readdition appears8 times in every case. Totals are4,402 candidate/deletion records,288 readditions and4,114 nonreadditions before overlap/geometry checks. The positive combinatorial split16+12+96 and central split8+6+48 are correct.

For implementation, a new three-outer-radius/four-selection pure helper is required; existing n71 helpers hardcode different counts. Reject retained overlap explicitly and retain exact blocking triples for monotone per-orbit filtering. Every surviving final union needs cardinality, distinctness, row/column checks and both final geometry validators. A shared25-second soft deadline must include initial validation; an owned30s/256MiB guard remains Root's proposed outer bound. Preserve partial coverage and save any verified witness immediately. All frozen source identities remain unchanged.

Only a complete clean independently audited result could close at-most-one-original-full-orbit repairs of this fixed centered near-quarter n73 fixture with its exceptional pair unchanged. It cannot establish global n79 nonexistence or closure of other embeddings, fixtures or larger deletions.
