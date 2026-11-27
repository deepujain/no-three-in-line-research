# Fixed main ancestors16/15 with capacity320: source handoff

Implementation model gpt-6.1-sol/high. Source/tiny preparation only; the author
did not execute a new n79 mask, pair census, formula build or native solve.
Six new adapter tests and21 unchanged pair/ancestor tests pass,27 total in0.073s.
Independent source review passed, rerunning27 tests in0.067s. Any actual gate
still requires a separate Root allocation.

The new adapter retains exactly the first17 or16 IDs, respectively, of the
accepted main19 selected path, including the initial diagonal orbit. Depth16
retains66 points and needs23 new four-orbits; depth15 retains62 and needs24.
Only an unexpired native UNSAT at16 advances to15. Every other result stops.
No depth14, DFS integration or original frontier write is exposed.

The adapter directly reuses the frozen three-ancestor solve_models and
adaptive_loop functions from44b9fce, and the fixed-main19 incompatible_pairs,
degree_clauses and dispose_solver helpers from08c5b853. Both exact source
hashes are checked before and after. No imported mutable globals are modified
and no solve loop is copied. Masks and every pair exclusion are recomputed
for each current prefix, using fresh private state. No cut file or former
depth's clauses are reused.

The complete mask is never truncated. More than320 variables is an incomplete
capacity stop. Depth16's fresh mask must match the independently accepted
224-orbit complete-mask hash from the prior capacity-stop audit; that prior
run did no depth16 pair/solver work. Depth15's full mask is unknown before the
new gate. Mask length/hash and the full local-variable-to-orbit mapping are
recorded, allowing independent mask reconstruction.

For m admissible variables, each stage requires exactly m*(m-1)/2 completed
pair decisions; pair_started and pair_completed must both match before any
solver construction. Binary cut IDs must be unique and in range. The frozen
pair routine rolls back each first-orbit push and validates state restoration.
At320, there are at most51040 pairs and319 first pushes; two stages have at
most102080 pairs. No new mask or pair census was run during this handoff.

Every orbit is an edge with two distinct radius endpoints. With residual
degrees in{0,1,2}, the exact degree CNF has conservative dynamic limits9m total
variables,16m clauses and48m literal entries. The adapter enforces these as
well as absolute3000/5200/16000 construction ceilings. At320 the mathematical
bounds are2880/5120/15360; all possible binary cuts and1000 ternary cuts give
57160 final explicit clauses and120440 literal entries. These limits do not
bound learned native memory; use the existing owned30s/256MiB sampled gate.

Each stage receives fresh native solver, timer and ternary-cut set. Models
independently check residual degrees, chosen orbit count23/24 and158 distinct
points. Any remaining conflict must involve three distinct new orbit
variables; exact triples and their cut IDs are saved. A stage adds at most1000
new ternary clauses. A valid candidate receives both full exact validators
and immediate atomic saving even if the second validator crosses the soft
deadline, then stops. Native answers after deadline/interrupt remain unknown.
Timer cancellation/join precedes native deletion before the next stage.

One absolute soft deadline at most25s covers pinned evidence, source checks,
both private reconstructions, masks, pairs, formulas, solving and validation.
Completed earlier evidence survives later timeout/capacity/unknown outcomes.
The final immutable-source/evidence reread and atomic report publication tail
run under the unchanged outer hard gate. Native UNSAT remains conditional and
prefix-scoped, with no independently checked proof certificate.

New tests verify exact depth/prefix/target counts and direct frozen-function
reuse;320/321 cap handling; dynamic algebraic/formula rejection boundaries;
mocked two-stage absolute deadlines and timer cleanup; fresh state identity;
incomplete pairs and excessive formula bounds blocking solver construction;
preserved first-stage evidence after second-stage mask or timeout; and stop
after every non-UNSAT result without a third stage. The21 unchanged kernel
tests cover exact tiny geometry/cardinality projection, rollback on interrupt,
cut-limit/repeated-cut rejection, late native results, dual witness mismatch,
valid-witness persistence and timer join before solver deletion. Mocked
adapter tests do not perform n79 geometry.

Prospective command only after source review and a concrete Root allocation:

    .venv/bin/python research/near_quarter_ancestors16_15_cap320.py \
      --output-dir data/main-ancestors16-15-cap320-pair-sat-v1 --seconds 25

The output directory must be fresh. No automatic capacity widening, deeper
ancestor, retry, old-cut load or accepted-chain modification follows.
