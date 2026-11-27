# n73 boundary verifier: source and arithmetic review

Approved one Root-owned 30s/256MiB gate with a 25s soft checker budget, fresh output, fixed pinned fixture verification and eight extensions. No retry or broader numerical allocation is implied.

Source SHA256 `e93d9025e1b77fedb96dfde0f868d959414620dc93994c9d1041726a37f65dfa`; tests SHA256 `c4a2714ac08a2b77e21bd802b346d029ec9dc1ab26af52201f29b48537c69c69`. Independently ran three small tests: passed in 0.074s. Raw and decoded pins match. Independent raw decoding agrees exactly with all 146 distinct in-bounds fixture coordinates and gives two points in every row and column. This source review did not run n73/n79 geometry.

Translation by (3,3) saturates rows and columns 3..75. An extension within the stated near-quarter-turn family must add three four-orbits using outer radii 37,38,39. Degree two at each of three vertices forces one edge for every radius pair; each edge has two orientations. Therefore all eight orientation choices are enumerated, with no missing row-feasible extension in this fixed zero-deletion family.

The checker first dual-verifies fixture geometry and checks the normalized hash, then dual-verifies every final candidate. Valid witnesses are saved atomically immediately. Soft deadline is checked between candidates; the owned outer guard remains responsible for hard resource bounds. Atomic rename is not a crash-durability claim. Any negative closes only these eight centered zero-deletion extensions of this fixture.
