# n78-to-n80 full-C4 one-orbit repair implementation

Model `gpt-6.1-sol`, reasoning `high`. Implements the independently approved
`n78-to-n80-one-four-orbit-repair-proposal.md` in a new standalone checker;
frozen n71/n73, paired, packed, verifier and guard sources remain unchanged.
No n80 geometry or actual evaluation was run during preparation.

`research/n78_to_n80_orbit_repairs.py` requires exact published n78 bytes, both
complete fixture verifiers,156 points, full quarter-turn closure, and two points
per row/column. It reconstructs every field of the pinned39-case manifest and
its unique diagonal source loop. New even-grid constructors use positive odd
doubled radii around the half-integer center and retain diagonal loops. Existing
odd-grid constructors with excluded diagonals are not reused.

Every loop-inclusive degree factor is retained:230 records. The77 factors
containing the outer corner loop carry an explicit triple. The checker requires
three distinct proof points, their membership in the actual candidate union,
and zero integer determinant. It checks the remaining153 factors with frozen
per-orbit exact filtering, overlap rejection and complete dual verification of
all surviving finals after160-point/cardinality/row/column assertions. Witness
callbacks persist before early return and attach exact full-C4 n80/deletion
metadata without a novelty claim. No n79 neighborhood is used in any prune.

One shared at-most25s soft deadline begins before fixture validation. Reports
preserve completed, partial and unstarted cases, and completed per-case raw and
proof counts must equal the manifest. Root separately supplies owned30s/256MiB
containment. Full validators, final serialization and writes are not interrupted
internally; a hard kill may leave no report. Atomic file fsync/rename inherits
the existing absence of directory-fsync crash guarantees. There is no resume,
new guard or checkpoint protocol.

Fifteen focused tests pass in0.043s, including eight new tests. Complete n4/n6/n8
orbit partitions independently validate the even constructor and loop coverage.
Tiny row/column enumeration confirms both6- and2-factor cases and exact
readdition/outer-loop counts. Tests preserve all raw records with injected
survivors, require both final verifiers, exercise real tiny valid witnesses,
reject absent/noncollinear proof triples, preserve a timed-out filter prefix,
and check full39=230/77 accounting and incomplete/unstarted coverage. The fixed
n78 manifest check uses source coordinates only. Pins and output are in
`data/n78-to-n80-one-orbit-source-pins.json` and
`data/n78-to-n80-one-orbit-tiny-evidence.json`.

After independent source approval, Root may separately allocate one fresh
`python3 research/n78_to_n80_orbit_repairs.py --fixture data/published-n78.json --seconds 25 --output-dir data/n78-to-n80-one-orbit-v1`
under the unchanged owned30s/256MiB gate with no overlap. Only a clean complete
actual report and independent evidence audit can close this narrow fixed-source
full-C4 centered one-orbit repair family. Other sources, more deletions,
unrestricted n80 solutions and the primary n79 problem remain outside its scope.
