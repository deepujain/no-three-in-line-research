# Aggregate memory stop, 2026-11-27 00:12:13 UTC

Operational reviewer: gpt-6.1-terra, high reasoning, per assignment. Read-only checkpoint inspection; no checkpoint repair, numerical search, or solver run was performed.

The supervisor status in `data/runner-status.json` reported `aggregate_rss_limit_1536MiB` at 00:12:13 UTC. This is an aggregate process-memory guard, not a per-process measurement or proof of which child caused the threshold. The associated receipts all record exit code −15 (SIGTERM) and the same guard reason:

- `data/experiments/r4-sat-157-minisat22.json`: unrestricted 157-point MiniSat22; 812.43 elapsed seconds. Last `data/run-logs/sat157-progress.jsonl` sample was still `running`, at 809.758 seconds, 23,891 candidate iterations, 1,500,000 loaded cuts and 7,657,533 new cuts. This sample is not a final checkpoint count. Its requested final `data/sat-r4-target157.json` was absent, and the worker log was empty at inspection.
- `data/experiments/r5-sat-diagonal157.json`: main-diagonal-reflection 157-point Glucose3; 154.93 elapsed seconds. Last `data/run-logs/diagonal157-progress.jsonl` sample was `running`, at 150.292 seconds, 6,585 iterations and 2,458,251 new cuts. Its requested final `data/sat-r5-diagonal157.json` was absent, and its worker log was empty.
- `data/experiments/r6-rectangle-barrier14-resume.json`: threshold-14 rectangle-component continuation; 14.41 elapsed seconds. The most recent saved `data/trades-barrier14-cont.json` reports `incomplete`, best conflict score 11, 208 discovered states, 14 pending frontier states and zero recorded improvements. These are scoped checkpoint observations, not an exhausted component.

The two terminated SAT runs have **no final solver result recorded**: neither UNSAT nor a verified new witness is established by their progress samples, empty logs, or interrupted receipts. Absence of a final result is not a proof that no candidate was ever internally encountered. The threshold-14 checkpoint similarly supplies no global infeasibility conclusion; its prior enumeration and continuation rely on trusted, unmodified local checkpoints.

## Checkpoint tails

At inspection, each file below had a parseable `no3-geometry-cuts-v1` header for n=79, a terminal newline and a syntactically valid three-integer final record. The final triple in each also passed distinctness, range, and exact determinant-collinearity checks:

| File | Bytes | Final triple |
|---|---:|---|
| `data/checkpoints/diagonal157.jsonl` | 41,655,030 | [347,2012,4232] |
| `data/checkpoints/glucose3.jsonl` | 111,850,915 | [5959,6139,6229] |
| `data/checkpoints/minisat22.jsonl` | 150,863,045 | [1357,1672,2617] |

No truncated tail was detected by these checks. This is not a full-file parse or validation, and a buffered checkpoint can lose recent unflushed records on SIGTERM even when its last persisted line is complete. The SAT loader must still validate every reloaded triple. Progress `cuts_added` counts should not be treated as the persisted record count. Preserve the original file and document any later repair or derived subset; no repair was needed or performed here.

## Safer future allocation

Use at most one SAT process concurrently, and account for its baseline and other active processes within the shared guard. Prefer a fresh, separately named checkpoint with an explicit modest new-cut cap (for example `--max-cuts 200000`) and a short measured run; monitor RSS and checkpoint growth before raising the cap. Do not assume a cut quota caps the memory of loading a large existing checkpoint: current SAT code streams validation but still adds all accepted clauses to the native solver. Avoid loading the 107–144 MiB existing files until measured, or first implement and test an explicit validated load limit / produce a separately named, provenance-recorded validated subset while preserving the original. Such a subset is a weaker but sound starting relaxation; it is not an exact replay of the former solver state. The guard itself polls and terminates processes, so allow margin for RSS growth between polls and never treat the guard as a predictive memory cap. No old job was restarted by this review.
