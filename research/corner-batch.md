# Memory-bounded corner-anchor batches

Implementation configuration: `gpt-6.1-sol`, reasoning `high`. The new worker is `research/corner_batch_worker.py`. The existing `embedding_worker.py` entrypoint now has an explicitly authorized CLI-only `--batch` opt-in; ordinary CLI parsing and execution are unchanged. Existing origins, queue and supervisor were not edited. No numerical benchmark or additional 79-grid search was run during this preparation. Only tiny correctness tests ran.

## Prepared source and exact search contract

The worker loads the reviewed corner-anchor manifest and validates the source independently once per invocation. Its context binds the canonical geometry hash, ordered-source hash, target grid, exact deletion count and the cut `(0,0)`, meaning translation by `(+1,+1)`. The translated source is therefore valid, and every retained subset after old-point deletions is valid.

The prepared streaming routine uses the same exact algorithm and result schema as `stream_cover_repairs`: lexicographic exact-size supersets of one anchor, axis-capacity filtering, exact old-pair blockers for candidate additions, exact pair compatibility against retained points and determinant checks for triples of additions. A numeric offset advances only after all addition subsets for both target sizes finish for that deletion set. An interrupted case is retried.

The new routine is separate because the existing function independently validates the source on every call. This avoids a fresh process and repeated expensive source verification for every one-case anchor. No running process is monkeypatched. Existing geometry helpers and atomic-file utilities are reused. Tests compare every result field, count and first witness against the existing exact stream on a tiny source at every possible start offset.

## Selection and counting

The full reviewed manifest contains 10,304 retained anchors. `--max-anchor-cases 1` selects the 8,136 size-five anchors, each with one exact-five deletion case. `--start-anchor` and exclusive `--stop-anchor` optionally restrict manifest ordinals; `--max-anchor-cases` can select other small frontiers. The unfiltered default selects all anchors. The exact selected ordinal sequence is hashed into the batch identity.

All counters are labeled as sums across potentially overlapping anchor frontiers. `distinct_deletion_sets` is deliberately null. Completing a filtered batch closes only its selected frontiers; it does not close the whole manifest family. Unselected counts and the scope limitation are included in every cursor record. Existing separately running size-two streams are neither assumed complete nor silently skipped. A new records directory creates honest separate streams; using an existing compatible tip requires its complete hash-checked history.

## Persistence, locks and restart

Every anchor gets an immutable zero-work origin, immutable offset-specific stream records and its own durable tip. These retain the existing embedding stream schema, source/order hashes, base indices, exact deletion count, enumeration order and gapless parent references. The unchanged `embedding_worker.py` can load the resulting chains. Additional anchor/manifest metadata does not alter that contract.

The batch cursor is atomically replaced and bound to the raw manifest hash, source hashes, batch implementation hash, selection parameters and records directory. The batch implementation SHA-256 is captured from `corner_batch_worker.py` when that module is imported and recorded as `batch_source_sha256` in the cursor identity, final reports, origins, immutable per-anchor results and error output. This records the transitive implementation when the existing entrypoint delegates to it. A changed implementation hash requires a separate cursor. An exclusive batch lock prevents competing writers. The active anchor also uses the same tip-lock convention as the existing worker. All previously passed anchors are checked to have complete gapless chains on restart, so changing a cursor alone cannot skip a partial or missing anchor.

Before any progress publication, including a zero-new-budget restart, the worker loads the current durable tip. It recovers partial offsets and also handles a tip that reached completion just before a crash prevented cursor advancement. This avoids regressing reported progress. Case totals are derived from completed selected-frontier prefixes plus the validated active offset, rather than trusting an independently incremented aggregate counter.

The cursor advances only after the entire current anchor frontier completes. A single global wall-clock deadline and a single maximum of newly completed deletion cases apply across the batch. Atomic writes, source validation, chain checks and independent witness audits add control overhead; this is not an operating-system hard-preemption mechanism. The external supervisor remains responsible for hard resource limits.

Resume validates local file hashes, identities, gaps, offsets and completeness counters. As with the reviewed existing worker, it trusts prior local enumeration records and does not independently replay their numerical cases.

## Immediate witnesses and bounded memory

Every reported witness is checked by both exact geometric verifiers, against the target grid and the permitted point counts. Its immutable hash-named file is published before either a stream offset or batch cursor advances. The batch then records the durable witness while keeping the old case coverage, so an interruption cannot turn witness discovery into false enumeration progress. Existing same-hash witness files are checked before reuse.

The worker retains only a prepared source, the input manifest/selection, one active anchor chain and one deletion/addition working set. It never materializes all deletion sets across anchors. Each chunk retains at most its first witness per target size, matching the existing contract. The batch cursor retains only the last 16 witness paths and an event count; full proof artifacts remain on disk. Case generators and checkpoint reads are streamed. Memory therefore grows with the finite input manifest and active chunk, rather than with all completed numerical cases.

## Tests and independent review

Eight focused tests pass:

- Prepared-stream results match the existing exact engine at every tiny offset, including counts and witnesses.
- Source validation occurs once per invocation, with a global case cap across partial and complete anchors.
- Restart preserves partial progress, recovers a tip ahead of its cursor and remains compatible with the unchanged worker's chain loader.
- Zero-second and zero-case restarts cannot regress the durable active offset.
- Witness files exist and independently validate before tip coverage advances.
- Changed manifest bytes, source order, selection, forged cursor skips and tampered history are rejected.
- Batch and per-tip locks reject competing writers.
- Interruption within a deletion case does not advance its offset.

```sh
python3 -m unittest discover -s tests -p test_corner_batch_worker.py -v
```

The independent mathematician approved the frozen implementation in `research/corner-batch-review.md`, independently reran all eight tests and added a one-off 12-case direct determinant differential. No correction remains outstanding.

The original approved batch core had SHA-256 `bfd9471d4e42b592fe5fb20bdd8aceade98af4d9b9a449b80ee3d6a81e635853`. The subsequent CLI integration added only opt-in dispatch, batch implementation provenance fields and a tiny subprocess delegation test. The current frozen artifacts are:

| Frozen artifact | SHA-256 |
|---|---|
| `research/embedding_worker.py` | `6955a097338ab133ed8d8172e0b285cc0856f52653a25d26f6f9c72bf4cc29d6` |
| `research/corner_batch_worker.py` | `32d97a4eafbca596cd2dedce42742dfd6e3316c8f5ff474d7b3844a8e85c61e3` |
| `tests/test_corner_batch_worker.py` | `9bc8a67178953c40e63e1c071f03c12409e36665d0f0079333b8d32d94968385` |
| `tests/test_embedding_batch_dispatch.py` | `b8db747f2c2cfaf41662031709f6843072d203e2cc61b064ca1bd1b75ab14624` |

The five existing normal-worker tests, eight batch tests and one subprocess delegation test pass. The delegation test forwards `--seconds` and the case limits, then checks a zero-case invocation, one tiny completed case and a zero-budget restart, including durable offsets and transitive source hashes.

```sh
python3 -m unittest discover -s tests -p 'test_embedding*worker.py' -v
python3 -m unittest discover -s tests -p test_embedding_batch_dispatch.py -v
```

Suggested first bounded command for the shepherd, through the existing allowlisted entrypoint and using a separate cursor and records directory:

```sh
python3 research/embedding_worker.py --batch \
  --manifest data/corner-anchor-frontier/manifest.json \
  --max-anchor-cases 1 --seconds 600 --max-cases 8136 --chunk-cases 200 \
  --output data/corner-batch-small.json \
  --records-directory data/corner-batch-small-records
```

`--batch` alone selects delegation; all remaining arguments are passed to `corner_batch_worker.main`, including `--seconds`. Direct invocation of `corner_batch_worker.py` remains available. Repeat the identical command to resume; implementation, selection or records-directory changes require a separate cursor. The first numerical allocation, any benchmark and queue/supervisor changes remain with the shepherd after review.
