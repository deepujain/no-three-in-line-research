# Isolated tiny residual-graph reference

`research/diagonal_residual_graph_tiny.py` implements only the reviewed necessary-condition proposal on n2..5. Its pure assessor receives a complete edge list, deduplicates reversed endpoint occurrences, excludes zero-demand endpoints and retains isolated positive-demand vertices. It checks every row's available degree, component demand parity, bipartite side balance and global/component anti-diagonal color capacities. Its scanner uses the frozen exact mirror-pair predicate once per canonical orbit and never mutates geometry. Any interrupted scan or graph pass raises before a verdict is returned.

The separate tiny census keeps the frozen MRV row and canonical batch order. It can disable the new bounds to establish equivalence with the existing reference. A failed bound closes only that coherent prefix. A full row state still receives both exact witness checks. Named rule hits may overlap; their sum is not a count of uniquely pruned states. This component has no checkpoint format, resume logic, worker wrapper or shared dispatcher route.

Six tests passed in 0.181 seconds on the initial run and 0.160 seconds when collecting the saved evidence. The independent determinant oracle enumerates every raw off-diagonal subset in each slice at n2..5: 8, 72, 1024 and 25,600 selections. It identifies 6, 31, 184 and 1091 valid partial states, independently enumerates all full sets and checks every possible full superset of each valid prefix. Every admissible graph edge agrees with direct determinant/axis testing. No rejected prefix has a valid full completion; full certificate counts and dual-verifier hashes are 2, 4, 10 and 16.

Tiny abstract coverage includes all 2746 graph/even-demand cases at n2..4, with 641 exact-degree feasible cases and 602 color-distinct feasible cases. Every ordinary exact-degree factor passes the graph-only bounds, and every color-distinct factor passes all bounds. Specific tests cover n5 bipartite imbalance, color strictness, isolated positive demand, duplicate/reversed edges, colors shared across components, zero demand and a satisfiable odd cycle. All 283 injected scan/assessment interruption boundaries return no partial verdict and preserve the state snapshot.

The integrated tiny witness sequence exactly matches the frozen reference, with node counts changing from 6/20/66/205 to 6/19/64/192 for n2/n3/n4/n5. Across all valid n5 prefixes, 71 rejected states would still have a nonempty batch domain at the frozen chosen row; 16 of those pass every row-degree check and are rejected by the graph/color strengthening. These are tiny logical pruning observations, not a wall-time improvement claim or evidence of n79 throughput. The fixture records concrete extra-rejection examples so later independent review can inspect them.

Frozen SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| `research/diagonal_residual_graph_tiny.py` | `56aa4158a56b675722e70b2241c0b4d54c1d26a890c536728d451c0fb19a9387` |
| `tests/test_diagonal_residual_graph_tiny.py` | `97f5c26c57b1515f3675dcba99299e9c015690914df17adc5043e921004aed2b` |
| `data/diagonal-residual-graph-tiny-evidence.json` | `74c7f6a583095514d836ea4ffdaa198dc5658b4a16d26a992cda100fd708812e` |

Independent source review is pending. No frozen reflection source or accepted frontier was modified, and no n79 geometry or numerical experiment was run. Any future integration requires source-identity and continuation review, plus separate measured cost/host gates. Retain the open hypothesis of useful larger-prefix pruning and a separately allocated exploration slice; this tiny reference does not establish or close either reflection157 or near-quarter158 existence.
