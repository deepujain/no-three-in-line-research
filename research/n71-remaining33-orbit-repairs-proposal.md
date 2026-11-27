# One bounded batch for the remaining33 fixed-fixture orbit deletions

The central547 and first noncentral1,094 actual finite checks completed cleanly
without a witness and passed independent evidence review. Root authorized source
and tiny preparation for one remaining33-case batch. This document proposes one
separate owned30s/256MiB evaluation with a shared25s soft deadline. No actual
batch, n79 geometry or host launch was performed during implementation.
Implementation model `gpt-6.1-sol`, reasoning `high`.

The exact source is still the pinned centered n71 fixture, raw SHA-256
`00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9`.
Coordinate-only grouping gives35 complete four-orbits. The frozen manifest
`data/n71-remaining33-orbit-cases.json`, SHA-256
`b2f8f9d3c49c4d91e72eb2f79473c51744434c39c4323e37c1da813badde4f54`,
contains exactly sorted source indices1..18 and20..34. It excludes index0, the
already checked lexicographically first noncentral orbit
`(0,19),(19,70),(51,0),(70,51)`, and index19, the already checked central orbit
`(10,35),(35,10),(35,60),(60,35)`. Every remaining case has two positive distinct
inner radii. The CLI requires the exact fixture bytes, dual-validates it, and
reconstructs this exact manifest coverage before evaluating any new candidate.

For each deletion, demand is1 at its two positive inner radii and2 at outer
radii36..39. There are30 labeled oriented edges and exactly1,094 selections of
five satisfying that demand vector. All51 exact deleted-orbit readditions are
retained per case. This is36,102 records for33 cases, including1,683 readdition
records that represent already covered zero-deletion sets. Together with the
central547 and first noncentral1,094 records, it completes the proposed37,743
upper enumeration across all35 original four-orbit deletions, if the batch
actually completes and passes its independent result audit.

The new standalone `research/n71_remaining_orbit_repairs.py` imports frozen
arithmetic, geometry, filter and writer helpers. Existing central, noncentral,
packed, verifier and guard sources remain unchanged. Its parameterized
`evaluate_deletion` accepts prepared valid retained geometry, a deadline
callback and an immediate witness callback. It changes no published globals.
`evaluate_batch` evaluates the fixed ordered list once; there is no resume,
scheduler, protocol or new guard. The shared deadline begins before fixture
validation, preventing each case from receiving a fresh25s allocation.

Each candidate orbit is checked for retained-cell overlap and for exact
collinearity involving its new cells. Explicit determinant triples justify
monotone rejection of every full selection containing a blocked orbit. The
other orientation at the deleted pair's radii can be retained and is explicitly
rejected if so. Every full selection surviving those filters gets exact158
point cardinality, uniqueness, row/column loads and both unchanged complete
verifiers. Cross-orbit conflicts remain covered. A verified witness is saved
before returning early with truthful incomplete census status and correct
batch/deletion metadata.

The report preserves each attempted case's filter and candidate records, full
completed-case indices, any partial case, and all unstarted indices. A timeout
therefore cannot imply coverage of the remaining list. A killed process can
lack a final report. Complete validators, final serialization and atomic writes
are not interrupted internally; the existing owned guard controls actual caps.
The imported writer fsyncs files and renames but does not fsync directories, so
no crash-durability guarantee is added. Earlier subsecond filtered cases justify
one bounded batch measurement; they do not prove that all33 cases fit25s.

Twenty-five tiny tests pass in1.206s, including seven new tests. Coordinate-only
manifest tests independently check exact35=33+2 coverage. Prepared valid n13
retained subsets match the frozen first-case checker on all1,094 choices and
all51 readditions. Injected survivors exercise both final verifiers; witness
callbacks run before early return. Tests cover partial orbit filtering,
complete33-case accounting, timeout within a case, timeout between cases,
unstarted coverage and strict source/budget gates. No valid full tiny n5 source
is claimed. Source hashes and output are retained in
`data/n71-remaining33-repair-source-pins.json` and
`data/n71-remaining33-repair-tiny-evidence.json`.

After independent source approval, Root may run only this one proposed batch:
`python3 research/n71_remaining_orbit_repairs.py --fixture data/published-n71-rct4.json --seconds 25 --output-dir data/n71-remaining33-v1`
under the unchanged owned30s/256MiB guard with a fresh absent output directory
and no overlapping numerical worker. Source approval is not an actual outcome.

A complete clean negative batch plus the independently accepted central and
first noncentral negatives would close near-quarter centered extensions of
this one fixed fixture with at most one original complete four-orbit deleted,
including exact readdition. It would not close more deletions, different
fixtures/embeddings, unrestricted extensions, or n79 generally. Partial output
closes only independently verified completed cases, never all33 by inference.
