# Independent tiny reflection row-batch review

Reviewer: Mathematical Reviewer (`gpt-6-astra`, high). Approved as a tiny-only
proof/correctness prototype. No production engine, frontier/resumer, host guard,
larger-grid execution or performance conclusion is approved by this review.
No n79 run, construction, enumeration or benchmark was performed.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_rowbatch_tiny.py` | `27d74e27fa29557cf867ba7f9591e0a349427def5a0a017f4fc9b7a88b36e0e2` |
| `tests/test_diagonal_rowbatch_tiny.py` | `7298693129d43a20843e05d8104734dd5b2f8406fa7d70f395f91ac516cbf47c` |
| `research/diagonal-rowbatch-tiny.md` | `a6ea75d6729f2526422497b590b8719425dd0d11f5a44604595ff9d74a66d73a` |
| Frozen fast core | `38ec5044a8db85f046be24feb97c51adb6a95825afccac375d078195a57022a3` |
| Frozen verifier | `e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c` |

For fixed deficient row d and singleton (t,t), each unselected off-diagonal
mirror pair contributes exactly one point to each of two different rows. A
chosen row's remaining deficit k is one or two. Every valid full extension
therefore supplies one uniquely determined unordered k-subset of its remaining
incident orbits. Its individual admissibility and transactional joint insertion
follow from monotonicity of occupancy, capacities and forbidden collinearities.
Enumerating all combinations includes that batch. Two distinct batches cannot
lead to the same later state: their union overfills the row completed at their
first divergence. Deterministic row choice consequently gives exactly one path
per full set. There is no global increasing-ID restriction.

Across slices, an odd-size reflection-invariant set has an odd number of
diagonal fixed points. At most two can lie on the diagonal, hence exactly one;
its singleton index is unique. With 2n-1 points and row capacities at most two,
exactly one row has load one and all others two, uniquely fixing d. Thus the
same full set cannot occur in different (d,t) slices.

The implementation uses the already-reviewed exact mirror-pair predicate,
fresh occupied sums, deterministic row/domain order, `itertools.combinations`,
and transactional state pushes. A failed later orbit breaks the batch and the
finally block undoes every successful earlier orbit in reverse order. A full
leaf checks axis counts, symmetry, size and both geometry validators. Inputs
are hard-limited to n2 through n5. No file output or continuation exists.

The two supplied tests independently passed in 0.053 s. For every n3/n4/n5
slice, complete full-set output equals both the unique full-set output of the
frozen fast DFS and an independent exhaustive geometric census; no duplicate
full set appears within or across slices. The explicit d!=t n3 case is reached.
The reference census enumerates all grid subsets for n<=4 and reflection orbits
for n5, testing collinearity by determinants.

A separate reviewer-only in-memory instrumentation pass checked exact state
snapshots and determinant-rebuilt secant counts after every push and pop across
all n3/n4/n5 batch traversals: 382 accepted pushes, two rejected pushes, and
332 pops. Every rejected push preserved its snapshot; every pop restored the
matching prior snapshot. The 50 retained singleton pushes correspond to the
9+16+25 independent slices. This pass made no source changes. It reproduced
20/66/205 nodes and 4/10/16 unique full witnesses. These are tiny correctness
counts only, not evidence of larger-grid throughput or memory bounds.

A production checkpoint must separately represent batch cursors, parent-child
relations and consistent post-batch node phases. The frozen one-orbit frontier
cannot be resumed under this rule. New resource, interruption, serialization,
resume and durable-witness gates remain necessary before any such integration.
