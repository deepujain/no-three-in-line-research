# Independent actual audit of the direct-owned saved proof

Verdict: PASS. The accepted monotonic RUP proof certifies UNSAT for the exact original fixed 64-cell, 246-support, eight-support scaffold CNF. This is a new successful checking receipt for the preserved saved bytes. The earlier strict-checker rejection and the later inner-observer failure remain unchanged historical outcomes; neither earlier attempt is retroactively described as successful.

The independent audit reads and hashes artifacts and checks receipt structure and consistency. It does not rerun the checker, invoke SAT, reconstruct the large-grid pool, regenerate a CNF, or replay geometry. All 135 source-manifest entries, all 32 runtime pins, and all 135 receipt source entries matched. The permanent receipt's source mapping equals the source manifest. The entry, parent acceptance code, checker, encoding reviews, historical actual report, and both saved inputs retain their reviewed identities.

The 1,879-byte worker log is a complete bounded JSON object with a terminal newline. Its parsed receipt equals the parent report's embedded worker receipt; its hash, absolute path, job ID, and command agree with the recorded caller association and permanent receipt. The report's owned gate equals the permanent receipt's gate and matches its recorded canonical hash. This verifies consistency of Root's recorded single-call job/log association. As previously disclosed, the historical guard itself does not cryptographically bind a log path/hash or worker PID.

The gate reports exit 0, clean cleanup, no monitor/cleanup error, 90 RSS samples, 55,168 KiB peak sampled RSS, and 3.9828913750097854 seconds under its five-second/256-MiB limits. Cleanup took 0.010366083006374538 seconds and is included in that wall interval. The worker reports 3.9170680420065764 seconds under its four-second cooperative interval. The permanent receipt reports 4.002580499989563 seconds total, with separate five-second reservations for the owned call and parent validation. Sampled RSS remains sampled evidence, not a continuous memory maximum.

The reviewed checker reports complete parsing of 2,891 proof records: 180 checked RUP additions and 2,711 exact active-multiset deletions, with the checked empty clause at record 2,891. Both expected and observed CNF/proof hashes match the original saved inputs. The receipt records 2,645 variables, 13,294 retained clauses, 34,044 retained literal occurrences, 10,583 active clauses, and 41,899,584 work units within the reviewed limits. The retained/active clause totals agree arithmetically with the original 13,114-clause formula and the recorded additions/deletions. These are audited checker-receipt claims; this audit does not independently replay those 180 inferences.

The mathematical bridge is the already reviewed monotonic entailment argument together with the already reviewed complete fixed-pool encoding and unchanged encoder/orchestrator identities. Every accepted retained addition follows from the original formula, so the accepted empty clause establishes that formula's unsatisfiability. The original actual report binds that formula to its fixed 64-cell pool and 246 supports, with eight selected supports. The finite family described by that exact encoding is therefore closed. No 149-point diagnostic or 157-point witness is produced, no different pool or source is excluded, and no unrestricted grid bound or novelty claim follows.

Primary SHA-256 identities:

- Source manifest: `c23be802dc10b07bd6981f2c6a9c92086cb7d3d5fa280c8f4440311b86aa85d3`.
- Actual report: `4454e8f2dc0d17d96da7b7692dc13ee88aac7fa3cb18027e53486e606649d2ba`.
- Permanent receipt: `bf442b7e7cef96b52ce08e312ff1c25ae3378872f28becb0ec0aa7471a2482a4`.
- Worker log: `9b11bb44925457b3d3ee2e8e888c6c7e1ce24d90292a62f8ea89bbf63a22e8cb`.
- CNF: `855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9`.
- Proof: `4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e`.

Reproducible read-only audit: `research/direct_owned_proof_independent_actual_audit.py`. Its separate evidence is `data/direct-owned-proof-independent-actual-audit.json`. Historical files were not modified.
