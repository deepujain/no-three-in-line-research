# Autonomous research pilot

**RESUMED by the human on 2026-11-27T06:02:57.120374+00:00.** Prior pause is preserved in the decision log. Original deadline and resource cap remain unchanged. Prioritize measured improvement from new methods; do not resume unchanged unpruned loops.

## Question

Choose as many points as possible from an n × n square grid, with no three chosen points on any straight line, at any slope. Coordinates use integers from 0 through n−1.

The research objective is a new finite construction improving the best documented lower bound at an unresolved size. A valid construction establishes a lower bound. It proves optimality only if it meets an independently justified upper bound. The general asymptotic problem is not the pilot's promised deliverable.

## Pilot and resources

- Start: 2026-11-26T22:59:25Z.
- Deadline: 2026-11-27T22:59:25Z (24 elapsed hours).
- One Research Lead (the shepherd), up to three concurrent workers, ten starting approaches.
- Human correction on 26 November: keep workers assigned and useful numerical work progressing between reviews. Do not deliberately wait idle for the next hour. Formal synthesis remains hourly; a separate five-minute dispatcher checks for finished workers and refills useful work without duplicating active tasks.
- A bounded local experiment pool keeps numerical jobs running between model turns. It is a process supervisor, not a permanently running AI model or an external service. Desktop scheduling and model work still depend on the host and account availability.
- At most three concurrent one-core numerical processes, including experiments started directly by agents. Each queued job requests at most 15 minutes and has a separate shutdown allowance. Across all rounds, cap aggregate numerical worker time at six hours, including reservations and early experiments. No paid compute or new API credentials. Useful proof, review and literature work may continue within the pilot after numerical budget exhaustion.
- `data/runner-status.json` is local transient process status; `data/experiments/` contains permanent receipts. Inspect actual PIDs and agents before starting work. Never start a second supervisor. Its file lock and conservative launch reservations prevent ordinary duplicate work; unresolved crash reservations require reconciliation.
- After the recorded aggregate memory stop, do not restart large SAT checkpoints without a memory review. Future SAT allocation: at most one SAT process, a fresh exclusive checkpoint and a modest new-cut quota (initially 200,000), with measured RSS before expansion. Loading old cuts also consumes native solver memory. Use independently reviewed bounded-memory geometric searches. The audited seed repair family through five deletions is closed and must not be repeated.
- Checkpoints and progress logs stay local and are ignored by Git. Preserve hashes, receipts, result summaries, source code, and accepted certificates in the repository. Keep validated geometry cuts and numeric resume offsets between chunks; do not restart completed experiments simply to show activity.
- No outbound contact, journal submission, preprint submission, cloud purchase, or claim of publication without a separate user request. Public GitHub repository and Pages updates are authorized.
- Stop searches at the deadline, publish an honest final report, and disable both the hourly shepherd and five-minute dispatcher using their IDs in `state.json`. Do not extend the pilot silently. Supervisor timing is conditional on normal host/process operation, not a crash-proof hard real-time guarantee.

## Continuous dispatch and hourly synthesis

1. Read this plan, `state.json`, `approaches.json`, the decision log, literature, and reports. Resume work rather than reconstructing completed tasks.
2. Check the deadline, existing workers, running search processes, and recorded budget before starting anything. Avoid duplicate work and overlapping runs.
3. Assign bounded tasks to at most three workers using real-world research roles. Keep author and reviewer separate for any new claim. Record actual model, reasoning setting, prompt scope, commands, seed, duration, and output paths.
4. Compare results against an explicitly sourced baseline. Prune infeasible assumptions; treat search failures as experimental evidence only. Allocate effort on observed progress, correctness, and cost; retain a limited exploration allocation.
5. Branch only for a concrete new hypothesis. Preserve the parent approach, counterexamples, witnesses, and rejection reasons. Do not invent activity to fill the display.
6. Validate every promoted certificate with both exact checking procedures. Recheck literature before a novelty claim. Never count model agreement as proof.
7. Append real decisions and experiments, update the public visualization from saved evidence, run relevant checks, commit and push completed changes.
8. Report only meaningful developments, failures requiring attention, or completion. Continue autonomously within this plan.
9. On a worker finishing, assign a concrete next task promptly. Do not wait for the hourly synthesis to dispatch useful work. The five-minute dispatcher is a recovery/check-in mechanism; the numerical queue should already have useful bounded work when possible. Avoid repeating proved-dead neighborhoods or lengthening a weak algorithm without evidence.

## Evidence labels

- **Published baseline:** sourced external result; imported witnesses also need local checking.
- **Verified construction:** two exact checks pass. This alone does not establish novelty.
- **Experimental evidence:** finite searches and measurements, including failures.
- **Proved:** an explicit mathematical argument, reviewed separately; not proof-assistant formalization unless stated.
- **Conjecture:** unproved statement.
- **New result:** requires verified evidence and a documented, fresh comparison against prior work. A finite literature search cannot guarantee global priority.

## End product

A public Git repository with the problem statement, literature ledger, actual agent roster, ten-approach ledger, reproducible programs, certificates and hashes, mathematical arguments, decisions, tests, and a single-screen visualization. The final report must explicitly state whether a published bound improved. A negative pilot outcome is acceptable; fabricated discovery is not.
