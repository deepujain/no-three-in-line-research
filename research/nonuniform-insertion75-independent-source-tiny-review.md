# Independent nonuniform insertion source and tiny review

Verdict: SOURCE/GEOMETRY/TINY PASS for the exact frozen implementation below. Actual n74 work still requires Root's separate allocation and the independent lifecycle/source-identity/prior-scope gates. This review read no actual n74 fixture, performed no actual insertion or census, and invoked no solver.

Frozen identities:

- Worker `research/nonuniform_insertion75.py`: `2ae115db7f54325006f7498673650952bf9c40814e50a884389430fffa9b138b`.
- Author tiny helper `research/nonuniform_insertion75_tiny.py`: `129536fa7df7dbd428227d2b3cc823dfe117b4480f7492ad855d686d9a2cec6c`.
- Independent oracle `research/nonuniform_insertion_independent_tiny_oracle.py`: `3ec2f1f6ad8d97d7d3745ea229249d9833b13ba08da036547b7233cd504cd193`.
- Independent worker comparison `research/nonuniform_insertion_independent_worker_audit.py`: `a9f99f4351ee791ffc18495fdce09bab1aacbb57183ffb75b7bd649159ae9274`.

The two triple classes are exhaustive. The threshold intervals correctly include equality on the shifted side, partition all gaps exactly once, and handle repeated coordinates. Every old rectangle has fixed mapped coordinates. The four uniform-coordinate regions are skipped only after an explicit full source determinant prepass verifies geometric validity in addition to full row/column loads. The new-point class uses exact primitive lattice lines and signed integer clipping; original horizontal/vertical pairs cannot pass through the inserted row/column intersection. The rectangle-mask multiplication occupies disjoint row-bit bands. Coverage removes only included bits, assigns each removed gap once, and independently reconstructs and checks every stored obstruction before returning.

Early full coverage is correctly labeled certificate-complete even when one or both class traversals are unfinished. An uncovered gap is considered positive only after both classes finish. The exhaustive tiny mode disables early stopping and supplies complete separate class masks. Excluded corners are absent from all actual candidate and certificate sets. Canonical source indices refer to lexicographically sorted points, and reversed input order produces the same geometry.

Executed `.venv/bin/python -m research.nonuniform_insertion_independent_worker_audit`. The independent oracle enumerates source row-pairs, creates targets via explicit coordinate alphabets, and evaluates all target triples by integer determinants. It does not reproduce production masks or clipping. All comparisons passed:

- All 14 valid full-axis n=2,3,4 sources, in 56 fast/exhaustive and corner-policy runs; 1,152 target comparisons and 1,080 independently checked returned certificates.
- Both complete class masks, the union, and every uncovered gap matched direct geometry. Twelve runs exercised early certificate-complete stopping; 32 runs with remaining valid gaps required complete geometry.
- All 361 small rectangle masks, 490 threshold cases with repeats/equality, and 54,000 line cases with both orientations, signed slopes, horizontal/vertical directions, single-cell rectangles, boundary points, and endpoints outside the rectangle matched direct enumeration. Equal line endpoints and reversed bounds rejected.
- All 83 invalid but full-axis sources on the tiny grids were rejected before mask precomputation. Eleven additional malformed/domain/cardinality cases rejected.
- Six certificate mutations rejected, including missing, extraneous excluded-corner, invalid-kind, duplicate-index, out-of-range-index and unused-byte corruption. Six injected deadline stops rejected, including a stop after partial coverage rather than returning it as a completed result.

Separately reran all 14 author lifecycle cases using independently generated tiny sources, without overwriting the author evidence. These passed positive/negative completion, rejection of partial-positive and wrong-record claims, candidate-validator disagreement, save failure, pin drift, phase deadlines, final-pin deadline and report-save deadline. A second validator completing late still saves the validated witness before the following deadline check; completion and closure are then false. No witness is saved after validator disagreement or a partial-positive claim. Evidence is `data/nonuniform-insertion-independent-lifecycle-rerun.json`; this is an independent rerun of author lifecycle tests, not independently authored lifecycle logic.

Source inspection confirms actual CLI scope is one pinned record, one gap family, no orientation loop/alternate source/repair/fallback. The run performs two initial source validators plus the kernel source prepass, verifies final pins, and clears completion and closure on deadline or identity failure. A saved witness remains clearly distinguished from whole-run completion. Actual resource feasibility is not inferred from these tiny results: source validation, at most 12*C(148,3) old rectangles, clipped pair lines, certificate verification, dual candidate validation and output all consume the shared budget. Separate owned-process limits and lifecycle review remain necessary. No unresolved geometry defect was found in the reviewed freeze.
