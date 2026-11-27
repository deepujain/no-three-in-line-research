# Single Q pair-only probe: independent source review

Decision: source/tiny PASS after requested boundary fixes. Reviewer model
gpt-6.1-sol/high. No Q n79 mask, pair census, degree formula, native solve or
replay was performed by this reviewer. Actual allocation remains Root-owned.

Approved source `research/near_quarter_q_pair_probe.py`, SHA256
`2d8f357f434b357b3a1b516c78d0e686cd052f6faf8808a577c080c123a150e0`;
tests `tests/test_near_quarter_q_pair_probe.py`, SHA256
`50b2424016532de1358b12e0e279a440caa83cb02c452755568fd06bfd2395ef`;
method SHA256
`dc050e1c49d68573447f1d81b5afbf41e147b99ff4140ea1bd1fa82a45a62dd5`.
All23 files in the supplied source-pin manifest
`data/near-quarter-q-pair-probe-source-pins.json`, SHA256
`b2f4b8304f0c3050b8969b5d21ffd37e803c131748d6519ed5de536759add10d`,
match the current files. The final source review artifact may be added to a
new manifest without changing this approved source/test pair.

The source contains exactly the published17-ID Q: diagonal pair1522 and16
four-orbits, with66 retained points and23 remaining four-orbits. It checks the
canonical mapping digest before any Q ID push, reconstructs the retained
state and records its normalized hash before calling the complete mask helper.
That checked private state is reused for the fresh pair census. No checkpoint,
receipt, prior mask, inherited cut or accepted frontier is an input. Imported
historical path constants are not called on this production path.

The initial draft interpreted IDs through the mask helper before checking the
canonical map, and lacked explicit incidence/counter boundary checks. The
author corrected both before this approval. The complete mask must have1521
bits and every bit is an integer0/1. A mask above320 stops incomplete without
truncation or solver construction. For admitted variables, the source checks
one edge per variable,40 demands in0..2 summing46, and two distinct in-range
integer endpoints per edge. Every pair_started and pair_completed count must
equal m*(m-1)/2; cuts must be unique with1<=a<b<=m. These gates precede degree
formula generation and native solver construction.

The frozen pair helper freshly probes and rolls back every pair against Q.
The exact degree helper uses one IDPool for primary orbit variables and all
counter auxiliaries. Dynamic9m/16m/48m variable/degree-clause/literal ceilings
are enforced. At m320 they imply2880/5120/15360 and, with all51040 binary
exclusions,56160 total clauses and117440 literal entries. No ternary cuts or
geometric-completion loop is present.

SAT models are checked independently for residual degrees, selected count23
and every pair clause, then labeled sat_relaxation_only. They are not geometric
witnesses. Unexpired native UNSAT is labeled trusted native without proof.
Unknown, interrupt, incomplete census, shortage, mask cutoff or error cannot
justify a no-good. The single absolute25s deadline covers private construction,
mask, pairs, formula and native solve. Late native answers become unknown;
timer cancellation/join precedes solver deletion. Final source integrity and
atomic report publication remain under the unchanged owned30s/256MiB gate.

Independently ran:

    .venv/bin/python -m unittest tests.test_near_quarter_q_pair_probe \
      tests.test_near_quarter_prefix_pair_sat -v

All22 tests passed in0.023s. Nine Q-specific tests cover320/321 capacity stops,
no private checkpoint-loader call, SAT degree/pair model checks, late UNSAT
after interrupt, timer join, fresh tiny pair rollback, full mocked report flow,
incomplete pairs, and corrupt incidence/cut identities blocking native work.
The thirteen unchanged kernel tests provide determinant/axis pair oracles,
cardinality projection, rollback, cut/model checking and cleanup cases. All
Q n79 control-flow tests mock private geometry/state, avoiding a hidden actual
census during source review.

Only the separately audited complete necessary relaxation can support the
conditional disjunction of not-y_v over all17 Q IDs, including diagonal1522.
This source does not emit or integrate that rule. No checked UNSAT proof,
global n79 exclusion, minimal-core claim, learned-rule integration, second Q,
capacity increase or automatic numerical retry is approved here.
