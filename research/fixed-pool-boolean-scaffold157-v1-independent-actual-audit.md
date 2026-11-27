# Independent actual evidence audit: fixed-pool Boolean scaffold v1

Decision: the run is **incomplete and does not establish UNSAT or closure**. The native solver reported UNSAT, but the independent checker exited 2 with `ValueError: non-RUP addition`. This evidence does not establish why the addition failed, nor does it establish a SAT witness. No 149-point diagnostic was saved. No solver or checker was rerun in this audit.

The report records one SAT invocation and one checker invocation. The native child exited 0 and both child cleanup records are clean. The outer owned guard reports worker error/exit 1, clean cleanup, no monitor error, 1.616944083 seconds outer elapsed and 80,512 KiB peak sampled RSS under its 30-second/256-MiB limits. Sampled memory and ancestry have the limitations described by the guard; clean cleanup is not proof that an unobserved detached descendant could never exist.

The native response binds the emitted CNF and 44,475-byte proof to the hashes below. Independently hashing the files confirmed these identities; independently counting the CNF gave 2,645 variables in its header, 13,114 clause lines, and 33,466 literal occurrences. The report's 115 file pins all matched their current files when checked, including the frozen executable sources and runtime manifest. The permanent receipt records 81 pre-run sources and `sources_unchanged: true`. This validates the recorded identities, not proof correctness or the geometry encoding. The report explicitly sets `complete: false`, `closure: false`, `diagnostic_saved: false`, and `status: error`.

Evidence SHA-256:

- `data/experiments/shepherd-fixed-pool-boolean-scaffold157-v1.json`: `4d1c9b4f7c4eb13d82ea7322210992e1efef55cd3e8192c380e74506cb57e715`
- `data/fixed-pool-boolean-scaffold157-v1/report.json`: `c18b6e30a2cc56979d616a3f1b9794574afacfa58af1b4f15aef948405fa1814`
- `data/fixed-pool-boolean-scaffold157-v1/scaffold.cnf`: `855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9`
- `data/fixed-pool-boolean-scaffold157-v1/scaffold.rup`: `4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e`
- `data/fixed-pool-boolean-scaffold157-source-pins.json`: `0d0f21894915e3d326f839da3503232f286aa2fc271caf704a836788e6486403`
- `data/fixed-pool-boolean-scaffold-runtime-pins.json`: `1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a`

Any later proof-format investigation or independent recheck must preserve this receipt and distinguish its own evidence from this failed check. Even an accepted proof would concern only this exact restricted fixed-pool formula, not the unrestricted problem.
