# Independent corner batch worker review

**READY / APPROVED** for bounded numerical use with the reviewed corner manifest.
No blocking finding remains in the source hashes below. Approval concerns the
worker's enumeration and persistence contract, not any future numerical result.

Reviewer: Mathematician agent, gpt-6-astra, high reasoning;2026-11-26. I did not
modify the author's source, tests, queue, or running streams. I inspected the
source, reran its eight tiny tests, and independently checked twelve tiny
deletion cases against unrestricted integer-geometry enumeration. I ran no
n79 deletion search or benchmark.

## Coverage and geometric enumeration

The approved input is the independently reviewed10,304-anchor antichain whose
manifest hash appears below. Its coverage proof is in
`research/corner-anchor-review.md` and `research/symmetry-next.md`. The batch
loader checks source geometry and point-order hashes, cut(0,0), translation
(+1,+1), grid size, deletion count, unique anchor IDs, valid sorted distinct
base indices, and each exact binomial stream size. It does not reconstruct
the full mathematical antichain on every invocation. Approval of whole-family
coverage therefore depends on using the reviewed manifest, not an arbitrary
new manifest with matching source metadata.

The default selection visits every manifest position once in order. Range or
case-count filters select a declared subfamily; their completion is reported
as selected-frontier completion and does not close the entire corner family.
The selected positions and their order are bound by a selection hash, as well
as the raw manifest-file hash. Each retained cover A generates all size-five
supersets by choosing5-|A| indices from the increasing non-base source list.
There are no repeated deletion sets within that anchor stream.

For each deletion, the translated source remains valid. The addition pool
contains exactly the unoccupied cells with row and column capacity that do not
form a triple with two retained source points. Pair checks exclude two added
points collinear with one retained point, and addition-triple checks exclude
three added collinear points. These exhaust the ways a triple can occur.
Removed source points may be readded because only retained points are marked
occupied. Enumerating5+gain additions therefore covers both157 and158 targets.

The prepared kernel preserves the existing stream's enumeration, screening,
counts, and witness semantics. The author tests compare it with the existing
engine at every tiny offset. Independently, I enumerated every candidate final
set directly in the complete3-by-3 grid for each of twelve anchor/deletion
cases arising from the four-corner2-by-2 seed. Determinants were checked for
every triple without the kernel's row, blocker, or pair prefilters. All target5
and target6 valid-addition counts agreed with the new kernel.

## Resume, interruption, and accounting

The batch cursor is an index into the selected-anchor sequence. It advances
only after the current per-anchor stream reaches its exact total. Every anchor
preceding a resumed cursor must have a validated complete chain. Changing the
cursor to skip a partial or missing anchor therefore fails. A cursor lagging
behind a completed tip is recovered by loading that tip and advancing through
completed anchors before new work begins.

The current anchor's offset is loaded from its durable tip, rather than trusted
from the cursor summary. The chain checks source/order/base/cut/deletion-count/
enumeration identity, integer offset bounds, completed=end-start, immutable
predecessor hashes, gapless predecessor-end/current-start links, and a zero-start
origin. New records bind the manifest hash; compatible older individual-worker
records can be reused because their full frontier identity is checked. A batch
does not infer completion merely from an origin or tip existing.

One initial finding was corrected by the author before approval: zero-budget
restarts initially republished an active offset of zero before loading its tip.
The frozen source now loads and validates the active tip before publication,
even when seconds or max_cases is zero. A focused regression verifies both
zero-budget cases preserve the previous partial offset and completed sum.

Within a deletion case, addition counters and next_offset are committed only
after all its addition subsets finish. Deadline interruption retries that case;
it cannot record a partially tested deletion as complete. Immutable chunk
publication precedes tip publication, which precedes cursor publication. A
crash can leave an unreferenced chunk or a cursor behind its tip; it cannot
legitimately skip unfinished work. The global case budget subtracts newly
completed cases across anchors, rather than restarting its allowance per anchor.

The reported completed_cases_sum is the prefix sum for completed selected
anchors plus the validated active offset. It is explicitly a sum over overlapping
anchor streams, not a distinct-deletion count; distinct_deletion_sets is null.
The full manifest totals7,682,312 such cases. Separate batches or existing
individual streams may repeat work if separate record directories are used;
their sums must not be added as disjoint coverage. Different selections sharing
the same record directory can reuse the same validated per-anchor completion.

Both cursor and active anchor tip have nonblocking exclusive file locks. Cursor
identity binds its records directory, source, manifest, and selection. Running
individual streams must keep separate tips or respect the same tip lock. This
review does not authorize simultaneous writes that bypass those locks.

## Witness persistence and memory scope

Each discovered witness passes both exact validators in the kernel and again
in the callback. The callback also checks the expected grid and target size,
then writes an immutable witness atomically before progress can advance. An
existing file with the same canonical name is checked for matching valid
geometry. The witness survives even if the enclosing deletion later times out
before its offset or counters are committed. The recent-witness list is bounded
to16 paths; losing an uncommitted event count does not remove the witness file.

Memory holds the finite manifest, selected-position/prefix arrays, one anchor's
working geometry, and its loaded history. It never materializes millions of
deletion sets or an unbounded cross-anchor pair cache. This is a structural
memory assessment, not a measured RSS guarantee. Existing supervisor memory
limits still apply. Source validation occurs once per invocation rather than
once per anchor.

## Verification and exact reviewed versions

The eight author tests independently reran successfully in0.250 seconds. They
cover old/new stream differential behavior, global budgets and partial restart,
zero-budget recovery, witness-before-progress persistence, provenance/selection/
cursor rejection, lagging-cursor recovery and chain tampering, both locks, and
interrupted-case offsets. My additional twelve exact-grid differential cases
all passed. No numerical search performance claim follows from these tiny tests.

| Artifact | SHA-256 |
| --- | --- |
| `research/corner_batch_worker.py` | `bfd9471d4e42b592fe5fb20bdd8aceade98af4d9b9a449b80ee3d6a81e635853` |
| `tests/test_corner_batch_worker.py` | `9bc8a67178953c40e63e1c071f03c12409e36665d0f0079333b8d32d94968385` |
| `data/corner-anchor-frontier/manifest.json` | `e45bfeaed19f5b519a8cdda3ab411bbf874ca365903d46c7cadd802ab64137a1` |

Hash chains establish local artifact identity and gapless coverage claims. They
are not an independent replay certificate for future numerical computations.
No repair exclusion or unrestricted nonexistence result is asserted here.

## Approved opt-in CLI dispatcher and source-provenance addendum

The subsequent dispatcher revision is **READY / APPROVED** at the hashes below.
`embedding_worker.main` copies the supplied argument list, checks for the explicit
`--batch` token, removes that token, and delegates the remaining arguments to
`corner_batch_worker.main`. Without the flag it uses the same normal parser and
worker path as before; no batch import occurs on that path. The sole normal-path
parser change is passing the already-copied argument list instead of the original
optional argument object. Existing running processes retain their loaded code.

The batch source changed only to capture its file SHA-256 at import and record
it in cursor identity, prepared origins, immutable chunks, and error reports.
Geometry and enumeration are unchanged. The cursor binds this transitive source
hash across resume, so changing the batch implementation cannot silently resume
that cursor under a different recorded implementation. The dispatcher test checks
the hash in the subprocess report, durable cursor, and every emitted chunk.
This records the batch implementation in addition to the supervisor's entrypoint
hash; it does not claim to hash every Python dependency transitively.

I independently reran all five normal embedding-worker tests and the new real
subprocess dispatcher test; all six passed in0.566 seconds. The subprocess test
exercises zero-budget preparation, one tiny completed case, and zero-budget resume,
verifying argument forwarding and preserved progress. This approval introduces
no numerical search or benchmark. The eight core batch tests had already passed
on the unchanged geometry/enumeration logic.

| Artifact | Updated approved SHA-256 |
| --- | --- |
| `research/embedding_worker.py` | `6955a097338ab133ed8d8172e0b285cc0856f52653a25d26f6f9c72bf4cc29d6` |
| `research/corner_batch_worker.py` | `32d97a4eafbca596cd2dedce42742dfd6e3316c8f5ff474d7b3844a8e85c61e3` |
| `tests/test_embedding_batch_dispatch.py` | `b8db747f2c2cfaf41662031709f6843072d203e2cc61b064ca1bd1b75ab14624` |
