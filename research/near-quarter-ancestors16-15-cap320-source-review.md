# Fixed ancestors16/15 capacity320 source review

Decision: PASS for one separately allocated bounded16→15 job. This review does not launch that job or alter its predecessors.

Source `research/near_quarter_ancestors16_15_cap320.py`: SHA-256 `e9ef1770fc88da3698246240dc3716fbd777a255f6c4f4c44f361c3edb8a40c4`.
Tests `tests/test_near_quarter_ancestors16_15_cap320.py`: SHA-256 `62433283fe08bf6db1723df614efaacf6f8bccdcda271b04c17a485fe7f7ec71`.
All27 combined kernel/ancestor/adapter tests independently passed in0.067 seconds. The numerical run was not replayed and no new n79 mask, pair census or solver experiment was performed.

The adapter directly reuses the frozen44b9fce ancestor solve/coordinator functions and08c5b853 pair/degree/cleanup functions, verifying those source identities. It verifies the accepted parent audit and immutable checkpoint path, reconstructs fresh prefixes, and checks the new depth16 full mask against its independently accepted224-orbit identity. The mask cap320 rejects oversized masks without truncation. Exactly depths16/15 are accessible;23/24 new orbit counts are explicitly forwarded.

Each stage recomputes its own pair exclusions. Both started and completed counters must equal C(m,2), and every binary exclusion must be distinct with valid ordered primary-variable IDs before solver construction. Radius incidences are checked for distinct endpoints and residual degrees0..2. The dynamic formula limits9m variables,16m clauses and48m literals match the mathematical bounds, with additional ceilings3000/5200/16000. For m320 the final explicit formula remains bounded by57,160 clauses and120,440 literals including at most1000 ternary cuts; native learned memory remains governed by the external RSS guard.

One absolute deadline covers evidence loading and both stages. The coordinator advances only after unexpired native UNSAT, with no third stage. Timeout, unknown, witness, degree shortage, cut limit or oversized mask stops. Cleanup cancels and joins a timer before native deletion. Earlier completed evidence survives a later cutoff, and immutable evidence/source hashes are reread before final reporting. The inherited solver loop retains exact model checks, necessary distinct ternary cuts, dual witness verification and immediate atomic witness persistence.

New tests check exact bounds and rejection of invalid radius incidence, cap320 without truncation, frozen function identity, fixed prefix/count arithmetic, targets23/24, one absolute deadline with shrinking timer remainders, separate private states, cleanup order, incomplete pair/excess-formula rejection before native construction, previous-stage evidence after capacity/timeout stops, and every non-UNSAT advancement stop. Existing tests cover independent tiny pair geometry/cardinality projection, interrupt/rollback behavior, model-loop failure modes, and late verified witness persistence.

Approval is restricted to the proposed shared25-second soft/30-second owned/256-MiB job. Any UNSAT result remains conditional and prefix-scoped, with no independent proof certificate, global upper bound, original-frontier mutation, or automatic further widening.
