# Row-batch chain tiny host gate

`tests/host_diagonal_rowbatch_chain_gate.py` exercises the standalone row-batch chain with the real owned-process helper, without changing the shared dispatcher. It creates a fresh output directory and retains all reports, witnesses, checkpoints, markers, stdout/stderr and `summary.json`. It runs only n=3 and n=5.

The n=3 success case starts from a one-node checkpoint and uses three-node slices, requiring at least two accepted chain transitions before stopping on a witness-bearing invocation. The n=5 success case uses a 1,000-node slice and requires all 16 distinct full-census witnesses. Every emitted witness in both cases is independently checked by both verifiers, count, reflection, normalized filename and bound source metadata; final checkpoint schema, ordering and source identities are checked. A separate n=5 run observes an actual worker before SIGTERM and requires a cancelled report, clean helper cleanup, rejected marker, no new checkpoint promotion and absence of the observed PID. Timeouts or unverifiable cleanup fail the gate and preserve an unknown state rather than claim successful cleanup.

After independent source and gate-script review, run on the host from the research workspace with a new path:

```sh
.venv/bin/python tests/host_diagonal_rowbatch_chain_gate.py --output-dir data/rowbatch-chain-host-gate-v1
```

Do not reuse a prior directory or treat a failed/missing summary as success. This script has not been run in the sandbox; real OS process monitoring requires the host. Gate SHA-256 `cb3c3d66396280325c9b508be462489738255004e3f7dcfaff3c6cf2a4673a82`; chain SHA-256 `7dc712554cc2e66beb82860a6482d620769f4125bc4c92d297733dd197598787`. The Lead has since added a dispatcher route at combined entrypoint SHA `b71eb696b1a181886f745ec27d9d6e7ad2a47e5d22380c1ecdef7038ed0e5db2`; it requires separate exact-hash review and route smoke validation. This standalone lifecycle gate does not validate that route. No n=79 chain is authorized by this gate alone.
