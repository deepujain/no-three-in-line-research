# Pure radius-graph predicate and tiny checks

Not integrated with the live core/worker. Implementation model `gpt-6.1-sol`,
reasoning `high`. Implements only the independently approved mathematical
proposaldb7bdf4c; no process protocol, source manifest or policy is changed.

Frozen helper `research/near_quarter_radius_graph.py` SHA-256
647ae1379eb89711707f9900d68a2aba1861839751bdb22f15e9618d1f5cda66.
Tests `tests/test_near_quarter_radius_graph.py` SHA-256
8f70bf8b6d78c54060f23f198e4c0a0ac922618559a4f8b37b08c3c73dcd2470.
Evidence `data/near-quarter-radius-graph-tiny-evidence.json` SHA-256
8a1eed06f612a4507b65e97fc7bcf0932952e12f51380a5a6d32746b9c6d7e07.

The caller must supply a complete admissibility mask from a coherent active
prefix. The wrapper derives quotient demands from reflected row loads, checks
the central row's even occupancy and demand sum2*remaining, then reads only
marked existing orbit coordinates. It constructs no geometry and makes no
candidate push. The generic predicate uses adjacency bits only for connectivity
and coloring; parallel edge capacity is never collapsed in the original mask.
It retains isolated positive-demand vertices. Odd component demand rejects;
bipartite side-demand imbalance rejects. Odd cycles and disconnected feasible
solutions do not reject. Budget exceptions propagate without a partial verdict
or mutation of inputs. Bounds are40vertices/1521edgeIDs; there is no matching
solver, general graph framework or state/cache history.

Four tests passed in0.026s. The independent edge-subset degree oracle checks5913
abstract graph/demand cases, including parallel edges;4808 necessary-condition
rejections preserve every feasible degree vector. Explicit tests include the
two-triangle parity obstruction, K(2,3) imbalance, an admissible odd cycle,
parallel two-edge cycles, disconnected feasible components and an isolated
positive-demand vertex. All19generic and12mapped passing-path budget checks
are individually interrupted with unchanged inputs.

The geometric test uses only n3/n5/n7 and the frozen tiny secant state. Every
coherent diagonal-containing prefix below the four-orbit target is checked:
1/9/63 prefixes. Complete independent determinant enumeration yields1/0/0
full-family completions. The helper rejects0/8/54 prefixes, including0/1/7
that pass the existing independent per-row optimistic and total-orbit bounds.
These8extra tiny prefix rejections show strictness on actual tiny geometry;
they do not measure saved tree nodes, overhead or n79 usefulness. The n5/n7
completion oracle is negative throughout, so nonvacuous feasible preservation
also relies on the abstract degree-subset oracle and positive n3 witness.

Live core27beb803, worker7f8c8a16 and codecac57fd57 hashes are unchanged. No
actual-host gate, n9/n71/n79 geometry or numerical search ran in this package.
Integration waits for Root's explicit baseline-release boundary, then requires
a new source identity and independent review before a fresh-chain comparison.
