# Autonomous research pilot

## Question

Choose as many points as possible from an n × n square grid, with no three chosen points on any straight line, at any slope. Coordinates use integers from 0 through n−1.

The research objective is a new finite construction improving the best documented lower bound at an unresolved size. A valid construction establishes a lower bound. It proves optimality only if it meets an independently justified upper bound. The general asymptotic problem is not the pilot's promised deliverable.

## Pilot and resources

- Start: 2026-11-26T22:59:25Z.
- Deadline: 2026-11-27T22:59:25Z (24 elapsed hours).
- One Research Lead (the shepherd), up to three concurrent workers, ten starting approaches.
- Hourly scheduled continuations, subject to the desktop scheduler, host availability, and account limits. This is not a continuously running external service.
- Each scheduled continuation: at most 15 minutes of local search wall time in total, at most three one-core search processes, no paid compute or new API credentials. Across scheduled continuations, at most 6 search wall-hours. Use short initial experiments to reject ineffective implementations.
- No outbound contact, journal submission, preprint submission, cloud purchase, or claim of publication without a separate user request. Public GitHub repository and Pages updates are authorized.
- Stop searches at the deadline, publish an honest final report, and disable the heartbeat. Do not extend the pilot silently.

## Hourly shepherd loop

1. Read this plan, `state.json`, `approaches.json`, the decision log, literature, and reports. Resume work rather than reconstructing completed tasks.
2. Check the deadline, existing workers, running search processes, and recorded budget before starting anything. Avoid duplicate work and overlapping runs.
3. Assign bounded tasks to at most three workers using real-world research roles. Keep author and reviewer separate for any new claim. Record actual model, reasoning setting, prompt scope, commands, seed, duration, and output paths.
4. Compare results against an explicitly sourced baseline. Prune infeasible assumptions; treat search failures as experimental evidence only. Allocate effort on observed progress, correctness, and cost; retain a limited exploration allocation.
5. Branch only for a concrete new hypothesis. Preserve the parent approach, counterexamples, witnesses, and rejection reasons. Do not invent activity to fill the display.
6. Validate every promoted certificate with both exact checking procedures. Recheck literature before a novelty claim. Never count model agreement as proof.
7. Append real decisions and experiments, update the public visualization from saved evidence, run relevant checks, commit and push completed changes.
8. Report only meaningful developments, failures requiring attention, or completion. Continue autonomously within this plan.

## Evidence labels

- **Published baseline:** sourced external result; imported witnesses also need local checking.
- **Verified construction:** two exact checks pass. This alone does not establish novelty.
- **Experimental evidence:** finite searches and measurements, including failures.
- **Proved:** an explicit mathematical argument, reviewed separately; not proof-assistant formalization unless stated.
- **Conjecture:** unproved statement.
- **New result:** requires verified evidence and a documented, fresh comparison against prior work. A finite literature search cannot guarantee global priority.

## End product

A public Git repository with the problem statement, literature ledger, actual agent roster, ten-approach ledger, reproducible programs, certificates and hashes, mathematical arguments, decisions, tests, and a single-screen visualization. The final report must explicitly state whether a published bound improved. A negative pilot outcome is acceptable; fabricated discovery is not.
