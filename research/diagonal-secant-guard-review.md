# Independent review of the guarded diagonal DFS

Reviewer: Mathematical Reviewer, `gpt-6-astra`, reasoning `high`, 2026-11-27.
The guard source and final shared dispatcher are approved for a separately
scheduled bounded preflight. The tiny real-host CLI gate is complete, as
documented below. The reviewer performed only tiny tests, with no n79 execution.

* `research/diagonal_secant_guard.py`:
  `073bd74fd2eb200c86b5effb5e7b4baea8712a354913604d0a7d3ba395ce3328`
* `tests/test_diagonal_secant_guard.py`:
  `3683f472c915e305f2f764685128c881ca6196b7b36e426edfc4a111d7b86847`
* Unchanged approved core `research/diagonal_secant_dfs.py`:
  `6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7`

## Source and artifact audit

The wrapper binds the core, verifier, wrapper, original RSS monitor, and actual
CLI entrypoint hashes. The child checks them before importing the DFS, before
each witness publication, and after search; the parent compares them again
before accepting the terminal result. The core remains the independently
approved complete reflection-slice search. Its callbacks contain only leaves
that passed exact count/reflection checks and both integer geometry verifiers.

Each run creates its own persistent witness directory. A callback writes the
verified certificate to a temporary sibling file, closes it, and atomically
replaces the destination named by normalized geometry hash. Publication occurs
before the child terminal state. Duplicate visits may replace the same
geometry-named file; the directory is not a unique-visit counter. This provides
complete-file replacement across worker interruption, not fsync-backed
power-loss durability or immutable file storage. The parent result and job
files also use atomic replacement.

A failed enclosing run can leave verified witness files for independent
re-audit. Neither a saved file nor a nested worker result overrides the parent
status. Before promoting any future witness, the Lead must reread its file,
check its provenance and exact geometry, and distinguish it from the run's
completion status. The returned `worker_result` is diagnostic evidence if the
parent reports a resource/source failure.

## Resource and cancellation audit

The wrapper reuses the exact approved `process_rss_kib` reader and implements
its own reviewed polling loop. Positive finite ceilings are 30 seconds and
256 MiB. The CLI passes a process-start timestamp before heavy imports, so
setup is included. An imported `run` call starts a fresh clock by default;
this was corrected during review to avoid an old module-import timestamp
causing spurious immediate timeout.

The worker starts in a fresh session. Host RSS includes the guard parent,
worker group, observed descendants, and native memory, excluding the transient
`ps` helper. Monitor exceptions and absence of any sample fail closed. The
loop checks time before/after sampling and after cleanup, kills the worker
group on terminal paths, and waits for it. SIGTERM sets a cancellation flag,
which is checked before spawning, during monitoring, and before acceptance;
the group is killed and reaped. Outer cleanup also protects exception exits.
This is not a guarantee against uncatchable SIGKILL or arbitrary escaped
descendants. The fixed DFS worker does not create such descendants.

RSS is sampled, so overshoot is possible; no kernel cap or exact peak is
claimed. The first external failure is preserved, while `source_stable` is
recorded separately. A late source failure, resource failure, monitor error,
or SIGTERM prevents completion even if the child has already published
`all_declared_slices_exhausted`. The parent marks complete only for a normal,
source-stable, within-gate child result with that exact status. Node-limit and
timeout results remain incomplete, and exhaustion concerns only declared
reflection slices. It supplies no unrestricted infeasibility conclusion.

## Independent checks and completed host gate

All eleven revised guard/core tests passed independently in 1.141 seconds.
Tests cover tiny n3/n5 complete searches with mocked RSS; saved certificates
checked by both geometry algorithms; monitor and RSS failure; actual SIGTERM
cleanup and reaping; setup deadlines; fresh imported-call clocks; capped
inputs; dispatch; source mismatch before import and after search; atomic
witness-before-terminal ordering; and a previously published child completion
overridden by RSS, monitor, wall-time, and source failures. The core's exhaustive
geometry and rollback tests also passed again.

Mocked RSS tests establish behavior, not physical memory use. The author's
sandbox CLI attempt failed closed because `ps` access is denied. The first
real-host n3 CLI attempt also failed closed with EPERM; its retry succeeded.
These failed attempts remain part of the validation history.

The final combined `src/lazy_sat.py` SHA-256 is
`ac1b568303153c7c39f3d01fff1df7cbce36d0bfcf36951df2fe24419f73c509`.
I independently inspected its process-start timing and both new routes, then
ran four targeted dispatch/legacy tests successfully in 0.121 seconds.

I independently inspected the lead's saved actual-host reports
`data/diagonal-secant-guard-n3.json` and
`data/diagonal-secant-guard-n5.json`. Both report normal exit zero,
`all_declared_slices_exhausted`, complete traversal, stable matching source
hashes, positive actual RSS samples, and no monitor error. The n3 run records
26 nodes, five witness visits, 0.082622917 seconds, and 28,832 KiB sampled
peak RSS from one sample. The n5 run records 415 nodes, 35 witness visits,
0.128877292 seconds, and 51,696 KiB from two samples. These are sampled
measurements for tiny runs, not resource forecasts for n79.

I reread all four distinct n3 and sixteen distinct n5 saved witness files.
Every certificate has the required 2n-1 points, matching normalized geometry
filename hash and report-bound source metadata; both exact integer geometry
verifiers pass. Witness visits count repeated search paths, whereas these
file counts describe distinct normalized geometries. The host gate is complete.

No n79 numerical task, measured resource claim, witness novelty claim, or
global nonexistence inference is part of this review.

## Later lead-run failure retained as historical evidence

I subsequently inspected the lead's r21 one-node n79 preflight report and
receipt without performing any n79 work. The process exited two after
2.021004084 seconds of receipt elapsed time; the durable report remains its
initial incomplete state, with no accepted traversal/resource counters.
The lead reports host EPERM during process-group cleanup. This attempt
therefore establishes neither a completed declared slice nor a measured
accepted setup result. The initial report's absence of counters does not
show that the child did no work. A separate cleanup variant is being reviewed;
the source identities approved above and this failed historical attempt
remain unchanged.
