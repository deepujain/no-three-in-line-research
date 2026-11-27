# Final suffix v4 mathematical/source binding addendum

Decision: PASS by exact source equivalence for the mathematical controller previously independently tested at v2. The final frozen worker is `research/two_row_suffix75.py`, SHA256 `fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1`. This addendum preserves the original v2 review and does not relabel its executions as v4 runs.

The source-only comparison pins frozen v2 (`11fc0200742a14f5baa8cfffe85c91b34353b4990608f70efba66cc20dd750a2`) and final v4 before and after comparison. Exactly two function ASTs differ: `preserve_zero` and `run`. After excluding `preserve_zero` and removing exactly one `witness_metadata_error not in report` acceptance conjunct from v4, the entire remaining module AST is identical. Thus the exact kernel linkage, rankings, minimization, decision controller, state/cursor ledger, cap accounting, fixed handoff and persistence implementation retain the v2 source. No new geometric assumptions are introduced.

The complete textual delta was also inspected. `preserve_zero` initializes its durable reference before validation/persistence, records the already validated normalized hash instead of recalculating it after save, and returns an existing durable reference if subsequent metadata bookkeeping raises. Raw fallback remains reserved for the case with no durable reference. The added `run` conjunct rejects overall acceptance when this metadata failure is recorded. The change separates preservation of a saved zero witness from acceptance of a complete run; it cannot advance a mathematical cursor or change an optimizer result. Lifecycle behavior is separately reviewed and is not independently fault-executed by this addendum.

Bindings:

- Prior logical review: `research/two-row-suffix-independent-source-tiny-review.md`, SHA256 `1d468e6a925bf83a1d110fa1464d5a7b387c8c07863386079c626945b6329bcd`.
- Prior v2 evidence: `data/two-row-suffix-independent-worker-audit-v2.json`, SHA256 `1b33fda5f5e154e154bdaf8443f0f7cad917f6294b95de5ae2b44085a3f7cd79`.
- Source comparison: `research/two_row_suffix_independent_v4_source_binding.py`, SHA256 `495a528c24ea720502ea798804b834f445cc50beb162e293e2636c538e3ca3e8`.
- Source comparison evidence: `data/two-row-suffix-independent-v4-source-binding.json`, SHA256 `38406a030f1bc1dd73e67294d34fefe498720e14e4dcda4067583eaf81f3e65c`.
- Preserved kernel: `research/two_row_descent75.py`, SHA256 `0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c`.

The prior 87-fixture, 88-decision, 175-split and 576-cooperative-interruption logical results support the unchanged code by this explicit equivalence proof; that full suite was not rerun for this addendum. The intermediate v3 runner stopped at its initial source pin after the live source had changed and produced no successful v3 evidence. No wrong-pin execution is counted as passing.

No actual inputs, coordinates, geometry, loader or worker `run` were read or executed here. Historical row coverage and the first 32 pairs remain source-supported execution, not independently certified minimum exclusions. This SOURCE PASS neither allocates an actual run nor establishes actual receipt/resource acceptance or a valid 149-point construction. Root's exact-v4 owned tests and the lifecycle review are separate evidence and are not claimed as independently reviewed numerical results here.
