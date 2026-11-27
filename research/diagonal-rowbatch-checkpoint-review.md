# Independent reflection row-batch checkpoint core review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Approved as a checkpoint
core for separately reviewed guarded integration. This does not approve any
large-grid run, shared dispatcher, automatic chain, host resource enforcement
or recovery after an uncertain publication. Reviewer execution was tiny only.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_rowbatch_checkpoint.py` | `b162073f64d8190e7f97e6a06c96f2f7607b1419bce9e01a0f73c572d346f289` |
| `tests/test_diagonal_rowbatch_checkpoint.py` | `615afec265cdfdacb5c3d4d03a30bf0ebddc3c65d49ac1fc197618b1ceeb2608` |
| Approved tiny reference | `27d74e27fa29557cf867ba7f9591e0a349427def5a0a017f4fc9b7a88b36e0e2` |
| Tiny reference tests | `7298693129d43a20843e05d8104734dd5b2f8406fa7d70f395f91ac516cbf47c` |

## State and continuation proof

The approved full-row unordered-batch completeness and uniqueness proof applies.
The core keeps an iterative DFS path. A root has no incoming batch; a child
stores its sorted one- or two-orbit incoming batch. A null next cursor means
the top node is pending and has not consumed a node count. An integer cursor
means the node has been entered and identifies its next candidate batch.

Before attempting a candidate, the parent cursor advances once. A rejected
batch undoes all its successfully pushed orbits and creates no child. An
accepted batch produces a pending child. On restore, the deterministic domain
and full row-filling batch list are rebuilt at every entered ancestor; the
child must equal the candidate immediately preceding its parent's next cursor.
Exact joint insertion revalidates the child, and null/pending frames can occur
only at the top. Thus accepted publications distinguish a pending child from
an already-entered parent and avoid repeating or skipping branches on normal
resume. Reconstructed prefixes consume no new node counts.

Candidate generation completes before a pending node is counted. A timeout
inside candidate generation leaves that node pending. A full leaf is dual
verified and its callback returns before witness/node counters advance and the
frame is popped. A callback exception prevents a new checkpoint publication;
previously published traversal can replay, so callbacks must be idempotent.
The standalone callback writes a normalized-hash-named certificate atomically.
It does not by itself establish the immutable/directory-durable witness policy
required of a future guard.

Each checkpoint binds exact sorted slice domains, grid, branch policy, orbit
order and six source identities in a distinct format. It stores cumulative and
per-slice counts, checks their arithmetic and frontier terminal consistency,
and requires an externally trusted exact hash. This is trusted-execution
continuation, not an independently checkable proof of all prior search.
The old one-orbit schema is rejected. Relocation with identical trusted bytes
is allowed; exclusive ownership remains the caller's responsibility.

## Bounded parsing and timing corrections

Initial review identified unbounded checkpoint reads/JSON parsing and unchecked
reconstruction/pair-list work. The final source restricts n to 2..79, consumes
at most n+1 values from each supplied slice iterable, reads at most 1,000,001
checkpoint bytes and rejects more than 1,000,000 before JSON parsing, requires
an object, and bounds stack length by n before reconstruction. Candidate lists
are finite quadratic lists per frame, not a materialized search tree. They are
not packed storage, and no RSS conclusion follows from these bounds.

Restore now checks time at every frame, after batch insertion, within row/orbit
scans and at every candidate combination. Other pushes, hashing, validation,
callbacks and file operations remain cooperative work that can overrun a time
parameter. There is no owned-process resource gate in this core.

If initial resume reconstruction times out, it rechecks source identity and
the trusted file hash, returns timeout with zero new nodes and the unchanged
checkpoint hash, and does not publish partially reconstructed state. Its old
predecessor field consequently remains historical. **A new guard must either
recognize this exact unchanged-timeout case or reject it safely; it must not
pretend these bytes are a newly published child with the current hash as parent.**
The partial reconstruction has not validated all remaining frames. On a new
initial run, reconstruction timeout may publish only the initial unentered root.
Later-slice setup timeout publishes a consistent unentered root for that slice.

Normal publication rechecks source bytes and the expected original checkpoint,
then writes the new predecessor and atomically replaces the file. The utility
fsyncs the file but not its directory. Source/path changes or exceptions before
publication fail closed; changes/crashes after replacement require external
review, since the old trusted hash then fails. No lock or hard deadline is
provided by this core. A mid-batch unexpected exception aborts the invocation;
the old checkpoint remains authoritative rather than the abandoned in-memory
state being resumed.

## Independent tiny verification

The final six core tests plus two tiny-reference tests independently passed in
1.003 s. The final hashes were checked after the run and the author's sole last
delta (explicit JSON-object validation and its test) was inspected. The earlier
four-test version independently passed in 0.560 s before requested corrections.

For every n3/n4/n5 slice, repeated quotas 1, 2 and 5 reproduce the approved tiny
reference's exact ordered certificates and cumulative/per-slice node/witness
counts, with no duplicate full sets. Quota one exercises a publication/resume
boundary after every entered-node step. Tests cover hash/config/cursor errors,
old-schema rejection, relocation, source change, cutoff, oversize/non-object
input, excessive frame depth, reconstruction timeout with byte-identical file,
deadline expiry during pair-list materialization, publication interruption
before/after replacement, callback failure and replay with both validators.

This core approval is a prerequisite for guard work, not a substitute for its
source review, publication/cancellation/failure tests and actual tiny host gates.
