# Independent direct-owned proof source and acceptance review

Verdict: PASS for source, mathematical integration, and synthetic parent acceptance, conditional on the caller provenance procedure below and the separate owned-process audit. This is not a saved-proof verdict and does not allocate or execute a saved-proof check.

Reviewed frozen identities:

- Worker `research/direct_owned_saved_proof.py`: `1fa2852218baeb097f34779a1d320958866b88e34edd34f0646484284da0f2ea`.
- Parent `research/direct_owned_proof_acceptance.py`: `460082c237edce3fc90e4f8c7a6c7d2826c3b1a19427246211263e6e00d9558d`.
- Synthetic worker `research/direct_owned_proof_tiny_worker.py`: `13301dcf8b26dbfc5d2e5cdef5ee851c4f2f07f78dff7acddb6906fa7036c3ab`.
- Synthetic tests `research/direct_owned_proof_tiny.py`: `18e39113b12adcfc63f29686f2b4c253308ea661916962685a689311dbc15f58`.
- Unchanged checker `research/monotonic_rup_checker.py`: `09e85dced3d7cf572cad4b75f9b4fab50dd051f4fe9f95ded58981de6ded5c90`.

## Worker and mathematical boundary

The worker directly invokes the unchanged checker once, with no solver invocation, nested observer, or child. Its actual CLI fixes the saved CNF and proof identities; generic tiny helpers do not create an alternate actual CLI. The four-second cooperative deadline starts at module entry and covers manifest loading, source/runtime checks, checker import and execution, and post-check pin verification. Interpreter startup before module entry and final JSON emission are covered by the independent outer five-second guard, not by a claim of cooperative coverage. A failure after checker acceptance clears the worker's accepted and closure fields.

Both runtime and source manifests are byte-hashed before their mappings are trusted. Mandatory checker/input/runtime/entry/parent/interpreter pins are required. The checker is loaded from its exact reviewed path after verification. Post-check verification occurs before worker acceptance; the parent independently repeats context and final-pin checks. Regular-file, byte, pin-count, time, and log limits are explicit and fail closed.

The mathematical theorem is unchanged from the independent monotonic RUP review: original CNF clauses remain in the monotonic database; every accepted addition is entailed by that database; induction makes every retained clause a consequence of the original CNF. A checked empty clause therefore implies the original formula is unsatisfiable. Deletions alter the exact active bookkeeping, not this retained entailment database. Full parsing and both actual input hashes are still mandatory after the empty clause. The worker accepts only the checker's complete checked-empty receipt. This review does not broaden RUP to RAT or infer anything about a different formula, target grid, or candidate pool.

## Independent parent acceptance

The parent requires a completed job with the exact command, a clean independent five-second/256-MiB gate, a successful exit, valid elapsed/RSS evidence, no monitor or cleanup error, and a complete bounded ASCII JSON log. It checks strict booleans, invocation counts, source/checker/runtime identities, owned-root identity shape, cooperative timing, full proof parsing, checked-empty position, both expected and observed proof hashes, and bounded proof counters. The actual entry passes only the fixed saved pair hashes. Worker JSON alone cannot replace the independent final pin check or guard evidence.

Caller provenance condition: the historical guard receipt contains neither the worker PID nor a log path/hash. Consequently `accept_actual(job, log_path, ...)` cannot independently prove that an arbitrary supplied log came from that job. Root must create a fresh unique log for the exact guard call, retain that job and log association, record its path and hash in the dispatch evidence, and pass the same job and log to acceptance. Root explicitly accepted this procedure. Do not describe the historical guard receipt as cryptographically binding the log or worker PID. No historical guard modification is needed for this scoped procedure.

## Executed synthetic verification and limits

All eight author pure tests passed when independently rerun using `.venv/bin/python -m unittest research.direct_owned_proof_tiny.DirectPureTests -v`. They include a real tiny contradiction with a deleted reason retained monotonically, a satisfiable rejected empty clause, identity and receipt falsifiers, pre/post pin mutation, deadline rejection, real tiny context loading, and parent final-pin failure. They do not read the saved actual CNF or proof.

An additional independent temporary-fixture audit performed 32 checks: one accepted tiny baseline and 31 rejection mutations. These covered booleans in integer slots, NaN/infinite time, nonboolean acceptance flags, PID/group/session errors, incomplete parsing, empty-clause line beyond records, wrong expected hashes, failure clauses on purported acceptance, proof byte/counter caps, bad gate evidence, wrong job status/command, a second JSON object, and a missing terminal newline. All passed.

The expanded synthetic fixture source was inspected: it exercises identity, tiny accepted/rejected proof, deadline, pin change, cooperative fork, separate stdout/stderr overflow, concurrent inherited-log overflow, sleeping process, uncooperative fork, and truncation. Root reports its separate 12-mode owned run passed; this reviewer did not rerun it or independently attest its cleanup measurements. The lifecycle reviewer owns that audit. No source census, source decode, SAT run, saved-proof replay, or new mathematical bound was performed or established here.
