# Reuse the immediately preceding validated replay domain

Read-only proposal; no source, manifest, checkpoint or protocol was changed.
Inspected radius core2f758f63 and codec46e5a2db. Baseline source/11-node frontier
remains recoverable from commit26fec70. Model `gpt-6.1-sol`, reasoning `high`.

The largest exact duplicate in private checkpoint replay is the second full
scan of each WAITING ancestor at unchanged geometry. `_restore` first calls
`core._domain(frame)` while validating that ancestor. At the next loop iteration
it calls `core._domain(parent)` again before pushing the child. Both rebuild
the complete admissibility mask with reversible geometry probes, repeat row/
radius checks, choose MRV and hash the identical bounded domain.

A12-frame path ending ENTER therefore runs22scans for11distinct parent prefixes.
Both `read_checkpoint` and save_candidate's mandatory private `loads` use this
same function. This cost grows with depth even when no new nodes are counted.
The measured old n79stage10 had operation10.740s/save7.314s and left12frames;
its next restore would incur this duplication again. These are Root's existing
host measurements, not new geometry or profiling in this proposal.

Keep only the immutable Domain already validated for the immediately preceding
WAITING frame. At the next iteration use it for child-origin validation, exact
batch comparison and successor comparison, then discard it before pushing the
child/reconstructing its domain. The parser already requires every interior
frame WAITING, and the replay mutates no geometry between that frame's domain
validation and the next child-edge check. Domain stores immutable tuples. A
missing expected saved domain fails private replay. This needs one bounded
current-domain reference, with no per-ancestor domain cache.

Keep the original domain reconstruction/digest/deficit/length/current-cursor
check once per ancestor, child origin/batch/successor checks, actual incoming
batch push and row cover, terminal/prune validation, source checks, external
content/parent/chain hashes, final frontier/counter adoption and complete live
versus replayed state comparison on save. Budget checks remain before using
the carried domain and during cursor successor/push. A stop still adopts no
partial core. Physical counters describe the reduced actual replay work;
logical node/leaf counts and wire data do not change.

Tiny instrumentation only, current radius policy, one deepest ENTER frontier
at each n3/n5/n7 (all two frames):

| n | Full restore ns | Scan calls | Unique prefixes | Repeated probe counts | Paired scan ns |
| --- | ---: | ---: | ---: | --- | --- |
| 3 | 673375 | 2 | 1 | 1+1 | 53875+47041 |
| 5 | 972125 | 2 | 1 | 4+4 | 184042+179333 |
| 7 | 1466375 | 2 | 1 | 9+9 | 421125+417042 |

These single tiny observations establish duplication, not stable timing or a
broad-grid speedup. Removing the duplicate halves scan/probe work for these
ENTER-ended paths; construction, source checks, real selected-path pushes and
filesystem I/O remain. A roughly half replay wall-time reduction is a hypothesis
until separately guarded same-frontier measurements, not an allocation promise.
Traversal also rebuilds domains across COUNTED/READY/PENDING, but cross-step
reuse has more invalidation cases; this proposal targets only the local replay
loop and changes no search path or prune policy.

After Root releases the current manifest, implement a small codec-local change
as a new source identity. Required focused checks: unchanged parsed/frontier/
geometry/logical outputs at every tiny saved phase, exact expected scan/probe
reduction, every replay budget interruption, malformed origin/successor/domain
rejection, and full save-validation fault suite. Independent source review
precedes another fresh derivation or any measured comparison. No code was
implemented and no n9/n71/n79 geometry or host process monitor ran here.
