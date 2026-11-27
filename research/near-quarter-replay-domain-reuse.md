# Immediate private replay-domain carry

Implementation awaiting independent review. Model `gpt-6.1-sol`, reasoning
`high`. Old baseline26fec70 and radius-only baselineb4ab783 preserve their
sources, receipts and accepted11-node frontiers. No checkpoint migration.

Codec `research/near_quarter_rowbatch_checkpoint.py` SHA-256
88ce7a7a9b3d756427f60382b1b1316f30755e3a1a49a9a51367c6fcb27e6dec.
Core2f758f63, worker7f8c8a16, radius helper647ae137, state860711b8, cursor738a545a
and owned guardc119b58f are unchanged. The codec source slot changes the whole
source-bound core/worker identity. Pruning policy2 and all wire layouts remain.

The local replay loop retains only the immediately validated WAITING Domain.
For a non-root frame it requires that domain, checks child origin/batch/successor,
then clears both carried/local references before the actual child push. The
parent's full domain scan/digest/row/length/deficit/current-cursor check already
ran at unchanged geometry in the previous iteration. Every other replay,
certificate, source and complete live-versus-replayed save snapshot check stays.
Budget checks before reuse, in successor and geometry operations remain. There
is no ancestor cache, cross-step cache, new field or protocol. Physical replay
work decreases; logical search behavior does not change.

Focused tests `tests/test_near_quarter_replay_domain_reuse.py` SHA-256
d87bcbeecf64b48b1f663148bc98e3c992a413cfbff86466839ff935d5c25b4e.
Full56tests passed in4.708s with the unchanged10s command ceiling. Evidence
`data/near-quarter-replay-domain-reuse-tiny-evidence.json` SHA-256
7dc9ed5213591b021bb62ced8ea29b405c841e35af8adfcbf005979968369011.

85actual n3/n5/n7 frontiers covering every phase match their live state and a
repeat-scan replay in geometry/control/logical counters. Repeat-scan mode adds
the former discarded full parent-domain reconstruction before each child push;
it is not a separate independent geometry implementation. Exact removed work
is34scans/244probes, with every physical state-counter difference checked.
433replay budget interruptions adopt no provisional core. Malformed domain
digest/length, child origin and parent successor reject at the expected checks.
Existing private save, source binding, transaction rollback, publication,
uncertainty and abstract-pair tests pass. Actual tiny geometric paths have at
most2frames; the arbitrary-depth invariant is supported by the loop/parser
argument, not a new deep or broad-grid geometry test.

The approved design predicts22->11full scans for a12-frame ENTER-ended path,
but no host timing or broad-grid speedup is claimed. New actual n79 construction/
root and any counted comparison remain Root-allocated after source review.
Prepared fresh root request/proposal are
`data/packed-reuse-n79-r1-root.request.json` and
`data/packed-reuse-n79-r1-root.proposal.json`:30s/256MiB,2s worker reserve,
max_new_nodes0, same declaration/historical map, absent fresh chain. Preparation
used source/artifact reads and permutation bytes only. No actual-host monitor,
n9/n71/n79 geometry or numerical search was run for this implementation.
