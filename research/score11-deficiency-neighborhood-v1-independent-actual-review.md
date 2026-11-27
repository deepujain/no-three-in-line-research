# Independent fixed deficiency-neighborhood actual review

PASS. The exact157-point input has score5 and is a strict local minimum under the three specified one-step moves. All12247 legal neighbors have score at least6. This is independently certified by six explicit integer collinear triples per neighbor. The entire reported delta histogram was also independently reproduced; it need not be treated only as execution provenance.

The audit regenerated the complete catalog in grouped row/column/rectangle lexicographic order:157 row attempts,157 column attempts and12246 unordered rectangle pairs,12560 total. Independent legality gives155/155/11937 legal and2/2/309 illegal attempts. Fixed-source symmetric differences uniquely identify neighbors. Each candidate preserves157 points and the single deficient row/column pattern. Source identity, its five triples and deficient indices78/78 were independently checked. All17 manifest files and all27 receipt source/runtime files match current bytes. The owned run exited0 with clean cleanup in5.243485 seconds and50896KiB sampled RSS.

The independent scorer calls no production move, incremental-delta or census scorer. It partitions each neighbor's triples by zero, one or two newly added cells. Zero-new-cell triples are the five source triples that survive deletion. For each new cell, independent primitive integer directions enumerate all source-point secant pairs, with every emitted pair checked by determinant. Two-new-cell triples are checked directly against every retained source point. These cases are disjoint and exhaustive because each move adds at most two points. This reproduces every histogram entry in about1.01 seconds without checking all C(157,3) triples afresh for every neighbor.

A separate3,320,732-byte certificate lists six distinct explicit triples in every legal neighbor, establishing the strict-local-minimum claim even without trusting full score reconstruction. A small standalone checker reparses that certificate, independently regenerates all legal catalog entries and verifies membership/distinctness/zero determinants using integers only. It passes for all12247 neighbors. Its scope is this fixed one-step neighborhood.

Exactly three exits have score6 (delta+1); both full validators agree on all157 points, six coordinate triples and normalized hashes for each:

- Column relocation (77,33) to (77,78), catalog index312; normalized hash `91f2a80c3ff59ab83137a3b832e363634fd5fd2e818f64ca94337d7906d959e5`.
- Column relocation (77,51) to (77,78), index313; normalized hash `2c9f4420ac528de393158bde2bc5b7dac7acff0d3d7edc813125f6dd92093963`.
- Rectangle removal {(33,78),(78,0)} and addition {(33,0),(78,78)}, index8644; normalized hash `de8f1f09df58c234b5243585b28e819e8e8d140393389f90bbd49b101c6d2ab5`.

These are independently verified invalid score6 states, not witnesses. No second neighborhood, descent, solver or new search was executed. The result does not close neutral/uphill multi-step paths, the surrounding component, other move classes, all157-point states or the global board problem.

Audit: `data/score11-deficiency-neighborhood-v1-independent-actual-audit.json`, SHA-256 `edec993b9493b73d90b879f682fb6624176c75d8796d18f2cce94ea5800f1350`.
Exit manifest: `data/score11-deficiency-neighborhood-v1-independent-plus1-exit-manifest.json`, SHA-256 `717c6c1fb2debc0d446cb67922670c4ad97643b34a54aaaae653e6d1b0f0b71b`; includes standalone artifact hashes and both full reports.
Certificate: `data/score11-deficiency-neighborhood-v1-independent-local-minimum-certificate.json`, SHA-256 `b935c722509697efe5b11a309c79cf8a83d8d4218b5a1e1f9de3ae011b8edf11`.
Integer checker: `research/check_deficiency_local_minimum_certificate.py`, SHA-256 `c3c349a2c44fa7709ad0aa063fe3f080add85b34042b0830955a25d791d07566`.
Independent audit source: `research/deficiency_neighborhood_independent_audit.py`, SHA-256 `03d7197ec354b5acf9ba2603bde3163d536573024c42f2c59d0ffc5c7e0d1a8f`.
Implementation/review model: gpt-6.1-sol, high.
