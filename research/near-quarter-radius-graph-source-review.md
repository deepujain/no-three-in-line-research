# Independent pure radius-graph source review

Approved as a pure necessary-condition predicate, before integration. This review read the helper, all four tests and the tiny method record, and independently reran the four tests: all passed in 0.025 seconds. It launched no actual-host or n79 computation.

Reviewed hashes:

- Helper `research/near_quarter_radius_graph.py`: `647ae1379eb89711707f9900d68a2aba1861839751bdb22f15e9618d1f5cda66`.
- Tests `tests/test_near_quarter_radius_graph.py`: `8f70bf8b6d78c54060f23f198e4c0a0ac922618559a4f8b37b08c3c73dcd2470`.
- Evidence `data/near-quarter-radius-graph-tiny-evidence.json`: `8a1eed06f612a4507b65e97fc7bcf0932952e12f51380a5a6d32746b9c6d7e07`.
- Method `research/near-quarter-radius-graph-tiny.md`: `d17b7e5dac5f2c6e0f0896e09a402d9b81e47889ee99281806282ac023f2dbfe`.

For a coherent active prefix, reflected rows have equal occupancy. Positive-radius demand is the residual capacity of either row, and center demand is half the center row residual capacity. The wrapper checks these constraints and their sum of twice the remaining orbit count. Every allowed four-orbit gives a distinct edge between its two coordinate radii; the common radius pair is independent of which point of that orbit is used. No diagonal four-orbit occurs in this family. The wrapper reads marked existing coordinates and introduces no geometric probe or mutation.

A completion chooses edges with exactly the requested degrees. An edge incident to a zero-demand vertex cannot be chosen, so filtering these edges before finding components is sound and can strengthen the conditions. In each remaining component the total demand must be even. If that component is bipartite, both sides must have equal demand. The implementation computes precisely these necessary conditions, retaining isolated positive-demand vertices. Adjacency bit deduplication is used only for connectivity/coloring and does not impose a simple-graph capacity test. Odd cycles disable the bipartite equality check without causing rejection. Disconnected components and parallel two-edge cycles remain allowed.

The scan bounds are 40 vertices and 1521 supplied edges. Budget checks cover edge iteration, graph traversal and return boundaries; exceptions propagate, and no mutable caller input is changed. An obstruction is returned only after the whole edge stream is consumed and the relevant component is complete. The helper cannot prove that its caller supplied the complete admissibility mask: this is an explicit integration precondition, not an inferred guarantee from binary values.

The independent degree-subset oracle covers 5913 graph/demand cases including multiedges; 4808 necessary-condition rejections contain no feasible exact degree vector. Explicit examples distinguish component parity and bipartite imbalance and preserve feasible odd cycles, disconnected pairs and parallel edges. Tiny coherent prefixes at n3/n5/n7 number 1/9/63, with graph rejections 0/8/54 and additional rejections over the existing row/orbit relaxations 0/1/7. The independent complete determinant oracle has 1/0/0 completions, so the n5/n7 completion-preservation check is vacuous; nonvacuous preservation is supplied by the abstract feasible instances and the n3 positive instance. Passing-path interruptions are tested at all 19 generic and 12 mapped check positions; rejected-path fault coverage is not claimed.

This approval does not authorize mutating the accepted packed chain or claim n79 runtime benefit. Integration requires Root's chosen boundary, an explicit complete-mask hook, distinct source/policy identity, preservation of existing frontier evidence and focused review of the resulting diff. Passing nodes must retain existing traversal and MRV order, and an interruption must preserve existing scanner rollback semantics.
