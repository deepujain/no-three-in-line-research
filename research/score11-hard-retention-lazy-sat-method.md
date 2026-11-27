# Fixed score11 hard-retention SAT: source handoff

Implementation model: gpt-6.1-sol, high. Source/tiny delivery only; no n79
formula construction or native search was performed by the author. Eleven
tiny tests passed in0.114s; independent source review passed, independently
rerunning11 tests in0.097s. Root owns any actual allocation.

The standalone CLI exposes exactly n79,target157,D6: at least152 of the exact
158-point score11 source must remain. Source bytes and normalized identity
come from the frozen dual-verifying loader. The initial eleven source triples
are freshly regenerated and inserted as necessary negative clauses. No old
geometry-cut file is read. The frozen axis builder returns a shared IDPool;
the hard at-most-six counter over negative original real-cell literals uses
that pool. Real IDs, deficient-axis indicators and all auxiliaries stay
disjoint. The deficient row and column may intersect at an occupied point.

Native SAT candidates are decoded only from complete assignments to all6241
real variables and independently checked for target, axis caps, hard
retention and initial-source clauses. Exact collinear triples stream once by
smallest sorted anchor. Each added clause is checked with an integer
determinant. A model adds at most256 new cuts; the invocation adds at most20000
new cuts in addition to the11 initial clauses. The bounded final new-cut array
is evidence, with resumption_supported=false; no checkpoint loader exists.

After each model, one last-candidate artifact is atomically replaced. It
records exact retention/new counts and normalized identity. Partial or
batch-limited scans contain a conflict lower bound and null exact count.
Only exhausted scans have an exact count. The source reference score11 at
158 points is explicitly separate from best_invalid_score, which stays null
until a target157 candidate is independently accepted. A positive exact score
below11 is saved as best-invalid only after both full validators agree on
count, identity and target, and retention is rechecked. It remains invalid.
No candidate history accumulates.

A complete zero-conflict stream scan triggers both complete validators and
immediate atomic witness save. If the second validator finishes after the
soft deadline, an already dual-verified valid witness is still saved and the
search stops immediately; the outer hard gate bounds that final tail. A
late native SAT answer is timeout/unknown, and a partial decoded real model
is an incomplete invalid_native_model result. Scoped native UNSAT is reported
conditionally with no independently checked UNSAT proof; it is not a global
n79 conclusion. Cut-limit and timeout results make no infeasibility claim.

One shared soft budget at most25 seconds begins before source validation and
formula construction. Initial formula construction must remain below60000
variables,110000 clauses and400000 literal entries before native bootstrap.
The solver receives an interrupt timer for the remaining budget. Cancellation
and timer join always precede native solver deletion. Bootstrap and individual
validators are indivisible. No optional native conflict budget was added.
Use the existing Root-owned30s/256MiB gate; those resource limits are unchanged.

Tests cover exhaustive n2/n3 real-model projections for both targets and hard
retention, all256 assignments of eight source literals at deletion bounds0..8,
auxiliary ranges, rejection of valid geometry outside retention, separator
agreement with every tiny determinant triple and long lines,256/global cut
lower bounds, partial-model rejection, invalid dual-audit mismatch, an actual
n3 scoped witness, late-answer cleanup order, and a real19/18 pigeonhole
native solve interrupted by this loop's own timer. The final test confirms
valid witness persistence after a late second validator.

Prospective fixed command, only inside Root's separately reviewed allocation:

    .venv/bin/python research/score11_hard_retention_sat.py \
      --source data/trades-n79-seed270079-state.json \
      --output-dir data/score11-hard-retention157-d6-v1 --seconds 25

The output directory must be fresh.
No D8, target158, retry, pool or automatic continuation is authorized by this
source handoff.
