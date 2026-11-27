# n73 all36 finite one-orbit repair implementation

Implements the independently approved arithmetic and fixed manifest in
`n73-one-four-orbit-repair-proposal.md`. Model `gpt-6.1-sol`, reasoning `high`.
Only new standalone `research/n73_one_orbit_repairs.py`, its tiny tests and
supporting evidence were added. Frozen n71, paired, packed, verifier and guard
sources remain unchanged. No n79 geometry or actual evaluation was run during
implementation.

The CLI checks both original archive and decoded fixture byte pins through the
frozen n73 loader, then requires n73, dual fixture geometry validation and its
approved normalized hash. It reconstructs all36 original four-orbits and every
field of the exact case manifest before evaluating anything. Translation is
`(3,3)`, source diagonal pair remains intact, and one complete original
four-orbit is deleted while four new four-orbits are added. The existing pinned
manifest remains unchanged at `ca6147bee2ae9bcde4118f2ccdfb855af87c44cd5dd49e2aa3ec60580fbeabae`.

New arithmetic helpers use precisely three outer radii and four selections.
The central case has16 oriented edges and62 choices; each other case has20
edges and124 choices. Zero has quotient demand1 and one edge orientation.
Positive inner radius36 is accepted below outer37..39. Each case retains all
eight exact readditions, yielding4,402 total records and288 readdition records.
The checker does not reuse frozen n71 five-selection/four-outer assumptions.

Prepared-case evaluation uses the frozen exact per-orbit filter. Retained overlap
is rejected explicitly, including a possibly retained opposite inner-inner
orientation. Each geometric rejection records an exact determinant triple;
filtered selections point to that orbit. Every selection surviving the filters
gets exact158-point distinctness and row/column assertions and both complete
verifiers. A verified witness is persisted before early return, with correct
n73/case metadata. A witness return is not an exhaustive census.

One shared positive budget at most25s begins before fixture dual validation.
Each attempted case retains its records; complete case counts must equal its
pinned manifest count. Batch reports name complete, partial and unstarted
cases. No resume, new guard or checkpoint protocol is introduced. Root must
separately apply the unchanged owned30s/256MiB guard with no overlapping worker.
Individual verifiers, serialization and atomic writes are not interrupted
internally; a hard kill can leave no final report. The reused atomic writer
fsyncs files and renames but adds no directory-fsync durability guarantee.

Seventeen focused tests pass in0.393s. Seven new tests cover actual row/column
loads for every subset on n9/n11 prepared retained subsets, both exact counts
and eight readditions, real exact filters, dual checking of injected survivors,
retained opposite overlap, inner radius36, early witness callbacks, strict
inputs, timeout during filtering and between cases, and exact complete/partial/
unstarted accounting. Fixture decoding and manifest checks use existing source
coordinates only. These tests make no n79 geometry claim or valid full tiny
n5 fixture claim. Pins and full test output are in
`data/n73-one-orbit-repair-source-pins.json` and
`data/n73-one-orbit-repair-tiny-evidence.json`.

After independent source review, the proposed one actual invocation is:
`python3 research/n73_one_orbit_repairs.py --raw data/published-n73-rct4.raw --fixture data/published-n73-rct4-candidate.json --seconds 25 --output-dir data/n73-one-orbit-repair-v1`
under Root's existing owned30s/256MiB guard, with a fresh absent output directory.
Only a complete clean report and independent actual audit can close this fixed
fixture's at-most-one-full-orbit centered near-quarter repairs. Partial output
closes only independently audited complete cases. More deletions, other
fixtures/embeddings, unrestricted extensions and n79 generally remain outside
that conclusion.
