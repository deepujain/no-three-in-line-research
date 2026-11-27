# Intrinsic deletion range7..8: source handoff

Implementation model gpt-6.1-sol/high. Source/tiny only: no n79 formula build,
source-candidate geometry or native search was executed by the author. Eight
adapter tests plus eleven unchanged frozen-helper tests pass,19 total in0.486s.
Independent source review passed and reran19 tests in0.445s. Root independently
reran the eight adapter tests in0.374s. Any actual allocation remains Root-owned.

The CLI exposes exactly n79,target157,7<=|S minus A|<=8, with the same pinned
158-point invalid source. This hard intrinsic range does not depend on the
earlier D6 solver-reported UNSAT. Seven deletions retain151 old cells and add
six; eight retain150 and add seven. Readded original cells count as retained.
No model with six or fewer deletions is included in this scope.

The frozen D6 source223406 remains byte-identical. The new module explicitly
reuses its source loader, axis builder, upper-counter helper, real-model
decoder, exact streaming separator and dual-validator/atomic witness helper.
Because the frozen builder/loop have no lower-bound hook, the new module owns
a small range-aware builder and loop carrying the reviewed lifecycle. It
does not monkeypatch the frozen implementation or change imported globals.
At runtime the CLI verifies the frozen helper source hash before loading S.

The builder receives one axis IDPool, adds at-most-eight and at-least-seven
over the158 negative source-cell literals with that same pool, then freshly
regenerates the eleven original triple clauses. The decoded real model and
each saved candidate independently recheck both deletion bounds. No old
geometry-cut file or D6 actual artifact is loaded. Axis deficits remain
independent; their intersection may already be occupied.

Independently approved expected n79 counts are58108 variables and103583
initial clauses:55851/99060 from the157 axis formula,1200/2542 for at-most-eight,
1057/1970 for at-least-seven, and11 source triple clauses. The former source's
construction ceilings remain60000 variables,110000 initial clauses and400000
initial literal entries. No measured n79 build count is claimed in this handoff.

The separator streams each real triple once, checks its exact determinant,
adds at most256 new clauses per candidate and20000 per invocation beyond the
11 initial clauses. It retains bounded final new-cut evidence with no resume
input. Partial scans expose only conflict lower bounds. Only complete scans
give an exact score. The source158 score11 reference stays separate from an
initially null best observed target157 score. A saved score improvement must
be positive, below11, fully scanned, and accepted by both full validators with
matching count/hash and direct range checks. It is explicitly invalid.

A completely conflict-free candidate receives both full validators and
immediate atomic witness persistence. A valid witness already accepted by both
validators survives a soft-deadline crossing during the second validator, then
search stops. The outer guard bounds this tail. Native answers arriving after
timer firing/deadline remain unknown. Timer cancel/join precedes deletion.
The shared soft budget at most25s includes helper identity/source validation,
formula construction, solving, separation and saved-best audit. Bootstrap and
individual validators are indivisible. Use the unchanged owned30s/256MiB gate.

New tests exhaust all eight-source and ten-source bit assignments under
range7..8, plus smaller endpoint ranges. A fixed n4 source is checked over all
65536 real-cell assignments against target7, both axis caps and direct d7/d8.
The decoded lower check rejects an axis-valid d6 model even though the frozen
upper-only decoder accepts it; an axis-valid n5 d10 model is rejected by the
upper bound. Tests also check saved-candidate lower-bound rejection, exact
sequential counts on interior tiny bounds, a dual-verified tiny range witness,
late-answer cleanup confined to the new adapter namespace, real native
interruption and unchanged frozen helper identity. Eleven reused tests cover
separator/determinant equivalence, partial counts, invalid dual-audit mismatch,
shared-variable projection and late valid-witness persistence.

Prospective command, requiring a separate reviewed Root allocation and fresh
output directory:

    .venv/bin/python research/score11_retention_range7_8_sat.py \
      --source data/trades-n79-seed270079-state.json \
      --output-dir data/score11-hard-retention157-range7-8-v1 --seconds 25

No native UNSAT proof certificate is produced. A solver-reported UNSAT remains
conditional and applies only to this exact range/source. No automatic repeat,
larger range, target158 run or global n79 conclusion follows.
