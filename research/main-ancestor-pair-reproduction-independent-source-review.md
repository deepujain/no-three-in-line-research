# Checkpoint-free main18/17 reproduction: independent source review

Decision: source/tiny PASS. Reviewer implementation model gpt-6.1-sol/high.
No n79 mask, pair census, formula construction or native replay was executed
for this review. Actual replay still requires Root's explicit allocation.

Reviewed source `research/reproduce_main_ancestor_pairs.py`, SHA256
`637edc3bc3cba0f36ec8ee17d8d789274006fa95c9ff33a60d94bb1bcf54236a`;
tests `tests/test_reproduce_main_ancestor_pairs.py`, SHA256
`e4354bf47f45688f45518774aeaebb0c48d4c3b759905404bb0d35b7f82d02bb`;
recipe `research/main-ancestor-pair-reproduction.md`, SHA256
`5ca17b80d7cb5e74572f106fb1d3d39887085870488f602bfc08764fbfa7a72f`.

The production call path rebuilds both prefixes from embedded ordered IDs and
repository orbit code. It calls mask_and_bounds, PackedOrbitState, the frozen
complete incompatible-pair census and degree builder directly. It never calls
prefix_paths or reads a checkpoint, receipt, actual report, prior mask, cut
file or solver state. Imported modules contain historical input constants,
but those unused constants cause no private-data I/O on this call path.
The public source dependencies and pinned optional library must ship together.

Independently compared every embedded expected value with the saved original
report whose bytes hash to
`1e3cc59e60b3e989a41cf46f84a372d1f993891f27048a2cb79db4c959447014`.
For both depths18/17, selected prefix IDs, complete mask hashes, compact
variable-order hashes, compact pair-list hashes, cut counts2307/3697 and degree
CNF counts754/1338/3124 and1129/2004/4702 agree. This was a saved-artifact
identity comparison, not a fresh n79 geometric calculation.

All pair decisions finish before formula solving. A rebuilt digest/count
disagreement raises an error. Each fresh solver receives exact degree and
binary pair clauses for that prefix only; a SAT answer is correctly just a
relaxation result. Only unexpired native UNSAT advances from18 to17. The single
absolute deadline covers both reconstruction stages and solves. Native None,
interrupt or late answer is unknown. Timer cancellation/join precedes native
deletion, including early exits. Exceptions/timeouts make no negative claim.

Independently ran:

    .venv/bin/python -m unittest tests.test_reproduce_main_ancestor_pairs \
      tests.test_near_quarter_prefix_pair_sat -v

All17 tests passed in0.028s. The four reproduction tests exercise n3/5/7 rebuilds
and native relaxation solves, prohibit the private checkpoint-loader call,
reject invalid/interrupted prefixes, and verify timer-fired late UNSAT becomes
unknown with join before solver deletion. The13 unchanged kernel tests add
independent determinant/axis pair checks, complete-census and rollback gates,
tiny cardinality projection, model/cut checks and witness-validation behavior.

The recipe accurately labels native UNSAT as conditional, without an
independently checked UNSAT proof. Expected hashes reproduce a saved solver
observation; they do not establish a global n79 exclusion. A fresh clone must
contain all listed public source dependencies and install the pinned optional
research environment; this review did not perform a clean-clone n79 replay.
