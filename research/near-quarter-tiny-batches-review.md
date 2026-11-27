# Independent tiny near-quarter full-row batch review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Approved as a separately
versioned tiny-only correctness prototype. No production worker, checkpoint,
large-grid allocation, resource forecast or novelty claim is approved. This
review ran only tiny correctness tests and read source/saved evidence; it ran
no n79 construction, enumeration, search or benchmark.

| Artifact | SHA-256 |
| --- | --- |
| `research/near_quarter_tiny_batches.py` | `417afd94483580b4697afc5edfd48b76d2310d5697e2bb44c08fbfe7977559ad` |
| `tests/test_near_quarter_tiny_batches.py` | `9ef5c01e07526d602a19afba9b0c9e03d2b2c3d56fa4967bae758563697bb598` |
| `data/near-quarter-tiny-batches-evidence.json` | `db9be104029ce58654ffb789c0d2a75a13ced4dfb59564e2958e78eda7d43e69` |
| Reused tiny state | `305562c35e305a975ad8232b478c082aa44040b8e6b7bf26a3e99ef1a59e232a` |
| Frozen model | `b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a` |
| Frozen verifier | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |

## Proof and implementation

The full-row batch uniqueness/completeness proof in the independently reviewed
order addendum `431dfcf8ffae435d4a771a2109b2f60597f1e9070cfbdf7b5380b7acadb1b76f`
applies. For fixed diagonal choice, a valid completion has a uniquely determined
remaining set of contributors to the deterministically chosen row. With deficit
one it is one weight-one orbit; with deficit two it is one weight-two orbit or
an unordered pair of weight-one orbits. The generator includes each possibility
once in local order, subject to the remaining total orbit count. It imposes no
global increasing-ID rule. Distinct row-filling choices at a divergence cannot
later merge into an admissible selected set, since their union overfills that
row. The full set uniquely fixes its diagonal slice.

The same optimistic top-r row and global viable-count shortfall bounds remain
necessary conditions. Viability is recomputed by exact probes against the
reviewed transactional state. Batch push records successful orbits and unwinds
them if a later push returns false or raises; the state itself owns any rollback
inside its failing push. The injected exception test raises before mutation and
does not assert recovery from arbitrary corruption inside state methods.
An accepted batch must fill the selected row, and recursive exit always pops
the whole batch. Snapshots check restoration after probes, rejected/accepted
batches and complete slices. Full leaves undergo the frozen dual validation.

The public traversal rejects grids outside n3/n5/n7, limits its node parameter
to 10,000 and its positive time parameter to at most five seconds. Time checks
are cooperative and do not establish a hard wall/RSS bound. Node or timeout
termination is incomplete and unwinds active batches. The internal synthetic
fixture interface is likewise limited by grid label, orbit count and target.
The identity binds source/model/verifier/state plus explicit diagonal/orbit/row
permutations and batch policy. It is not a serialized or resumable frontier.

## Independent verification

All seven supplied tests passed independently in 0.253 s. Every saved evidence
field, including all order identities, exactly matches the independent test
results, and all five evidence source hashes match disk.

Real n3/n5/n7 exact full-family geometric censuses have 1/0/0 full sets. Forward
and reversed diagonal/orbit/row orders find each exactly once, with 2/5/11 nodes,
1/3/11 batch attempts, 0/0/3 rejected batches and 1/20/99 domain probes. Every
run exhausts its tiny slices and restores empty state. These tiny fixtures alone
have too few full solutions to provide a broad empirical uniqueness test.

Two abstract quota fixtures strengthen the branching check: the three-orbit
fixture has one full set and the nine-orbit fixture has twelve. Both forward
and reversed orders visit every such set exactly once (3 and 21 nodes). These
are expressly abstract incidence fixtures, not geometric witnesses.

The full tiny valid-subset transaction test performs 8,870 ordered two-orbit
attempts, including 8,522 rejections, in both insertion orders. Expected validity
uses independent determinant collinearity and family caps; each rejection or
accepted-batch pop restores the original snapshot. Other tests cover row-cover
weights/local order, insufficient remaining count, exception unwind, node-limit
unwind, timeout immediately after a successful batch, invalid order/parameters,
and rejection of n9/n71/n79.

Production integration still needs a separately reviewed packed representation,
bounded identity/wire schema, batch/singleton cursors, node-entry phases,
reconstructed parent-child/domain checks, tiny interrupted/resumed equivalence,
publication fault tests, guarded resource tests and explicit lead allocation.
Old one-orbit frontiers cannot be silently continued under this algorithm.

The subsequent method document `research/near-quarter-tiny-batches.md`, SHA
`f0d365f0dea976d800e68f31cdc69b820a7e447deff28b33c5497758b06c03eb`,
was also reviewed. Its evidence, uniqueness/completeness explanation, separation
of abstract fixtures from geometry, logical-limit caveat and tiny-only approval
scope agree with this review. Its future worker/checkpoint references convey no
implementation or resource approval.
