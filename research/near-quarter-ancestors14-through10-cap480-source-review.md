# Fixed ancestors 14 through 10, capacity 480: source review

Decision: PASS for one separately allocated bounded five-stage job. No prospective n79 mask, pair census, formula or solver computation was performed by this reviewer.

Source `research/near_quarter_ancestors14_through10_cap480.py`: SHA-256 `697b101b078389da3b5466cb6f90d26d4f534680137e5fd5d8826b22d8726e98`.
Tests `tests/test_near_quarter_ancestors14_through10_cap480.py`: SHA-256 `177c3b0242122dfd40b0fda6aed405e98693fb1b0b165d60a609d11fcf1c3b3b`.
All 33 combined kernel, ancestor and adapter tests independently passed in 0.076 seconds.

The adapter verifies the accepted depth-16/15 actual audit and immutable checkpoint identity. It pins the frozen predecessor and directly reuses the reviewed solve/coordinator and pair/degree/cleanup functions. It permits exactly depths 14, 13, 12, 11 and 10, with new-orbit targets 25 through 29. Every stage gets a freshly computed full mask, private prefix state and pair census; masks above 480 stop without truncation. Both pair counters must equal C(m,2), with distinct valid binary cut IDs, before native solver construction.

Radius incidence is checked for distinct endpoints and demands in 0..2. Formula construction enforces the proved dynamic bounds of 9m variables, 16m clauses and 48m literal entries, plus absolute ceilings 4,500/8,000/24,000. The explicit final formula is bounded by 123,640 clauses and 255,960 literals per stage, with at most 1,000 fresh ternary cuts. Five stages require at most 574,800 pair checks. The external RSS guard remains necessary for native learned clauses.

One deadline starts before evidence reads and covers all stages. The unchanged lazy solver loop may refine native SAT models using necessary geometric cuts; only a verified witness or non-UNSAT stage outcome stops the batch, and only unexpired native UNSAT advances. Each timer is cancelled and joined before solver deletion. A later cutoff preserves completed earlier stage evidence and leaves later stages unstarted. Input and source identities are checked again before atomic final reporting. No sixth stage, retry, frontier mutation or cut-file reuse is introduced.

The six new adapter tests cover five prefix/count pairs, frozen function identity, cap behavior, exact capacity arithmetic and dynamic formula rejection, all five forwarded targets, a common absolute deadline with shrinking timer remainders, five distinct states and cleanup sequences, pre-solver rejection of incomplete pair/formula work, preserved evidence after later capacity/timeout stops, and stopping on every non-UNSAT status. The unchanged earlier tests exercise independent tiny geometry and cardinality projections, interruption/rollback, exact model-loop cuts and errors, and immediate persistence of late dual-verified witnesses.

Approval is restricted to the proposed 25-second shared soft / 30-second owned / 256-MiB job. Any negative outcome remains solver-reported and conditional on its exact retained prefix. No independent UNSAT proof, global board bound, automatic integration, below-depth-10 continuation or capacity widening follows.
