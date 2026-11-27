# Analytical addendum: MRV duplicates, exact target and row-batch uniqueness

This addendum makes no source change and runs no numerical experiment. The
review checkpoint remains prototype `305562c35e305a975ad8232b478c082aa44040b8e6b7bf26a3e99ef1a59e232a`,
tests `24406fb3660c2c6822e613023ed07996ca2aa904de16fde8feb6b24a4918954e`,
evidence `ce40a8fb1651afc755516ea9ec09710b8d68dd287aeb1822a721d583504c0a00`.
The shared CLI is untouched. Analysis: `gpt-6.1-sol`, reasoning `high`.

## Exact target and diagonal-slice identity

Approved four-orbits are pairwise disjoint, have four points and avoid both
diagonals; a chosen main-diagonal half-turn pair has two points, with the
anti-diagonal empty. For odd `n=2m+1`, selecting exactly `m` four-orbits plus
one pair gives `4m+2=2n` distinct points. Conversely, exactly one pair and row
load two in every row imply `4F+2=2n`, hence `F=m`. Type-count caps and exact
row/column checks at a leaf are consistent safeguards, not different targets.
A full set contains one uniquely identified diagonal pair, so separate fixed-
pair slices cannot duplicate a full orbit set across slices.

## The current one-orbit MRV prototype is not a unique enumerator

For a partial selected orbit set `S`, all geometry counters and axis loads are
functions of the set, even when insertion stacks differ: counters sum unordered
point-pair incidences and addition order does not change that sum. With fixed
row tie order and prune policy, the chosen row `R(S)` is likewise a function of
`S`. Its remaining load is one or two.

Fix a valid full extension `F` and consider the remaining orbits of `F` touching
`R(S)`. If the row deficit is one, exactly one such orbit contributes one. If
the deficit is two, either one orbit contributes two or two different orbits
contribute one each. In that last case the current prototype branches first
on either orbit. Both branches retain the valid completion `F`: every prefix
of `F` is geometrically admissible and the reviewed prunes are necessary
conditions. Thus **the same final set is visited at least twice whenever this
case occurs on its path**. Subsequent MRV choices can cause more multiplicity.
The two paths may merge to the same partial selected set if their next choices
reverse the two additions; even without an early merge they end at the same
full set. Nothing in the current rule proves unique visitation.

More precisely, the multiplicity for a particular completion obeys

`M(S,F) = sum(M(S union {o},F) for o in F minus S touching R(S))`,

with `M(F,F)=1`. Every sum has at most two terms because the row deficit is at
most two and each contributing orbit has positive integer load. A coarse bound
for a fixed diagonal slice with `m` four-orbits is at most `min(m!,2^m)` paths
per full set (the final choice is in fact forced). This is only an analytical
upper bound, not a measured or useful runtime estimate. The number of duplicate
states or paths depends on the family and row-choice policy.

Changing only the orbit permutation changes traversal order, not this complete-
tree recurrence: it reorders the same sums. Changing the diagonal permutation
reorders disjoint slices. Changing the row tie permutation can change `R(S)`,
the tree and multiplicities. All three can change the prefix reached under a
node/time limit and must be part of continuation identity.

The tiny n3/n5/n7 complete fixtures have only 1/0/0 valid full sets, so their
forward/reverse agreement does **not** empirically establish uniqueness in
larger cases. The tiny result separately reports `full_leaf_visits` and
`unique_sets` using a tiny bounded test-only set. A production implementation
of the current rule must label visits as visits, not unique full configurations.
The recommended first existence search stops after its first dual-verified,
durably published witness rather than retaining an unbounded deduplication set.
If later enumerating witnesses, use a deterministic mathematical identity
(family/orbit-map identity plus sorted selected IDs), distinguish visits from
unique artifacts, and separately cap any disk deduplication ledger. Do not put
node number, insertion order or timestamps into that mathematical identity.

## Why a global increasing-ID prune is unsafe

A chosen row can need an orbit `B` from a valid completion while another row
later needs an orbit `A` with `id(A)<id(B)`. If `B` is the only completion orbit
touching the first chosen row, every path to that completion must start with
`B`. A global rule allowing only larger IDs thereafter forbids `A` and loses
that completion. MRV does not promise an orbit ordering compatible with IDs.
Such a restriction needs a separate completeness proof; it is not a valid
way to remove the duplicates described above. Merely marking a state visited
is also insufficient for a resumable limited traversal: an earlier occurrence
may not have finished exploring its descendants. A proven-exhausted-state
memo is a different mechanism, needs exact policy/state identity, and can
violate the bounded-memory goal if it grows globally. None is proposed here.

## Analytical alternative: fill one row as a complete unordered batch

A concrete future variant can remove multiplicities without a global ID rule.
Keep the same deterministic row-selection function, but branch on **all ways
to fill its entire remaining load**, not just one orbit:

- Deficit one: each admissible orbit contributing exactly one is one batch.
- Deficit two: each admissible orbit contributing two is a singleton batch;
  each unordered pair of distinct individually admissible orbits contributing
  one each is a candidate two-orbit batch. Require their joint push to succeed.

Skip batches containing more than the required number of remaining four-orbits.
Enumerate unordered pairs once with `i<j` in the frozen *local candidate*
permutation, push both in that order, and roll the whole batch back if either
fails. Individually valid orbits need not be jointly valid. Finish and undo
one complete batch before publishing a frontier checkpoint. There is no
cross-row or global increasing-ID restriction. The current top-`r` row and
remaining-orbit shortfall bounds remain necessary and safe.

For a particular full extension `F` of `S`, the set
`U={o in F minus S : o touches R(S)}` is uniquely determined. Its positive
integer contributions sum exactly to the row deficit, so it is exactly one of
the singleton or unordered-pair batches above. Because `F` is valid, its joint
push succeeds. No other row-filling batch can lead to `F`: it would select an
orbit outside `F` or omit a required contributor while leaving the row full.
Induction over successive filled rows therefore gives exactly **one path to
each full orbit set** within its unique diagonal slice, provided that the row
choice depends only on the restored set and each batch is generated once.

The argument also excludes merging distinct valid partial paths. At their first
divergence, two different batches fill the same chosen row. A common future
selected set would have to contain both batches; their union has strictly more
row load than the deficit, violating capacity. This is stronger than deduping
at the leaves and needs no global visited-state table.

Batching trades duplicate paths for potentially quadratic candidate-pair work.
It does not predict a speedup. The first row choice can still use the existing
cheap count of individually admissible orbits; exact MRV over legal batches
would require many joint probes. Stream unordered pairs with a pair cursor
rather than materializing a quadratic pair list. Memory remains bounded, but
actual time and RSS still require later reviewed measurements.

This row-batch variant is **analytical only**. It is not in the frozen prototype,
not tested or approved yet, and must not be silently substituted during review.
A follow-up tiny revision should independently compare its full set census
and path multiplicities against brute-force geometry under several frozen
permutations, test every failed/successful two-orbit rollback, and then test
interrupted/resumed boundaries before any production authorization.

## Frontier implications

The existing proposal's one-orbit frame cannot be reused unchanged for batches.
A separately versioned schema must identify singleton versus pair cursors,
ordered candidate-domain digest, selected child batch IDs, node-entry/count
phase, and parent-child relation. Rebuild each prefix and verify that the
selected batch fills its recorded row before accepting continuation. A changed
row/orbit/diagonal permutation changes the declared frontier identity even if
its eventual unique mathematical solution set is the same. Old frontiers stay
preserved; no implicit conversion or merging is justified by equal selected
sets. These requirements are proposals, not evidence that a serializer or
resumer already exists.
