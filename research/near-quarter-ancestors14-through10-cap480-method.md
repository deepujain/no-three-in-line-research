# Main ancestors14 through10, capacity480: source handoff

Implementation model gpt-6.1-sol/high. Source/tiny only: no prospective n79
mask, pair census, formula or solver run was executed by the author. Six new
adapter tests plus27 unchanged predecessor/kernel tests pass,33 total in0.068s.
Independent mathematical/source review passed, rerunning33 tests in0.076s.
Any actual gate remains separately allocated by Root.

The new adapter exposes exactly depths14,13,12,11,10 of the accepted main19
ordered prefix, at most five stages. Retained points are58/54/50/46/42, and
target158 requires25/26/27/28/29 new four-orbits. No depth below10 is included.
Only unexpired native UNSAT advances to the next stage. Preserve the frozen
solve_models helper unchanged: native SAT may trigger exact geometry checks
and up to1000 necessary distinct ternary cuts within its stage. The first
verified witness or other non-UNSAT stage outcome stops the entire batch.

The adapter directly reuses unchanged44b9fce solve_models/adaptive_loop and
08c5b853 incompatible_pairs/degree_clauses/dispose_solver. Both and predecessor
capacity320 sourcee9ef1770 are verified by source hash before and after. No
imported mutable global is changed. The accepted16/15 independent actual audit
819a8138 is pinned as predecessor evidence. Its clauses and masks are not
inputs to any new formula; each new stage recomputes its complete mask and
every pair on fresh private reconstruction. No old cut file is loaded.

More than480 admitted orbit variables stops incomplete without truncation.
For m admitted variables, exactly m*(m-1)/2 pair_started and pair_completed
decisions must finish before solver construction, and exclusions must have
unique in-range local IDs. At480, each stage has at most114960 pairs and479
first-orbit pushes; five stages have at most574800 pairs. The pair helper
restores and snapshot-checks the retained state after each first-orbit push.
Complete-mask length/hash, admitted IDs, selected prefix IDs and all binary
exclusions are preserved per stage for independent reconstruction.

Each radius edge has two distinct endpoints; demands are0/1/2. Dynamic degree
CNF limits are9m total variables,16m clauses and48m literal entries. Absolute
ceilings4500/8000/24000 are also enforced. At480 the conservative bounds are
4320 variables,7680 degree clauses and23040 degree literal entries. Every
possible binary exclusion and1000 fresh ternary clauses give123640 explicit
clauses and255960 literal entries per stage. These bounds do not constrain
native learned memory; preserve the existing owned256MiB sampled RSS gate.

All stages share one absolute soft deadline at most25s, including pinned
evidence/source reads, fresh states, complete masks, pair censuses, formulas,
solving and witness audits. One live private state/solver is used at a time.
Each stage owns its new cuts and timer. Timer cancellation/join precedes
native deletion. Models independently check degrees, chosen count25..29 and
158 distinct points. Necessary ternary clauses record exact point triples.
A witness accepted by both full validators is immediately saved and stops,
including if the second validator crosses the soft deadline. The existing
owned30-second hard gate bounds indivisible work and final integrity checks.

Completed stage evidence survives a later timeout, mask cutoff, shortage,
unknown or cut limit. Per-stage reports remain bounded by the declared mask,
pair and cut limits; no candidate history or scheduler is added. Final immutable
input/source rereads and atomic report publication happen on cooperative
timeout too, inside the outer gate. Native UNSAT remains conditional and
prefix-scoped, without an independently checked proof certificate.

New tests cover five fixed prefix/target counts;480/481 capacity boundaries;
exact dynamic bounds; incomplete pairs and formula overflow blocking native
construction; fresh state identity at all five stages; forwarded counts25..29;
one absolute deadline with remaining budgets25/24/23/22/21; cleanup order;
previous evidence after a later mask or timeout; every non-UNSAT stop; and
absence of a sixth stage. Predecessor tests independently cover tiny geometry,
rollback, complete-pair gates, cardinality projection, model/cut validation,
late native unknown, dual-witness mismatch and late valid persistence. Adapter
geometry is mocked in these tests; no prospective n79 census is performed.

Prospective command requires a fresh output and separately reviewed Root gate:

    .venv/bin/python research/near_quarter_ancestors14_through10_cap480.py \
      --output-dir data/main-ancestors14-through10-cap480-pair-sat-v1 --seconds 25

No below10 continuation, capacity widening, automatic repeat, accepted-chain
write, learned-rule integration or global n79 conclusion follows.
