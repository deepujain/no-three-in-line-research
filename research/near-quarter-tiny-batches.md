# Tiny full-row batch MRV variant

Status: independently approved as a hard-tiny component only. No production
worker, checkpoint/resume, shared CLI change, native solver or n79 code/run was
added. The approved packed secant state remains unchanged at
`305562c35e305a975ad8232b478c082aa44040b8e6b7bf26a3e99ef1a59e232a`.
Model setting: `gpt-6.1-sol`, reasoning `high`.

The separate `research/near_quarter_tiny_batches.py` permits only n3/n5/n7,
at most 10,000 nodes and a logical timeout of at most five seconds. Its internal
abstract quota test hook is also restricted to those tiny row counts, at most
12 orbits and at most three selected nonfixed orbits. There is no production
host resource gate; logical tiny limits are not RSS guarantees.

For each explicitly ordered main-diagonal pair, the traversal starts the fixed
slice, recomputes admissible unselected four-orbits with exact reversible
push/pop probes, and uses the existing necessary global remaining-orbit and
optimistic top-`r` row-load bounds. It chooses an underfilled row by fewest
individual contributors, then greater deficit, then explicit row order. This
is a cheap contributor-count heuristic; it does not count every jointly legal
batch before choosing a row.

For deficit one, branches are singleton contributors of weight one. For deficit
two, branches are singleton contributors of weight two and all unordered pairs
of weight-one contributors. Pairs are generated once by local permutation rank,
not a global increasing-ID rule. Both members must jointly pass the exact
geometry/axis/family state. A rejected second orbit rolls back the first; an
accepted batch always fills the chosen row. Return, node limit and timeout
unwind complete batches and the fixed pair before reporting.

The uniqueness proof is the analytical argument in
`research/near-quarter-mrv-order-addendum.md`: any fixed full completion has a
unique remaining contributor set filling the chosen row. That is one generated
batch. A different full-row batch cannot reach the same completion or merge
into the same valid partial selected set without overfilling that already
filled row. Induction gives one path per full orbit set within its unique
fixed-pair slice. Every valid completion survives the necessary prunes and its
unique batch is jointly admissible, so projection remains exact. The target
remains exactly `(n-1)/2` four-orbits plus one pair, hence `4*((n-1)/2)+2=2*n`.

The implementation binds batch/state/model/verifier source identities and all
three declared permutations in its order identity. Changed order hashes are
recorded separately from mathematical leaf identity. The result distinguishes
leaf visits from unique sets and explicitly exposes duplicate visits; the tiny
test-only leaf set is bounded by this hard grid cap. No production deduplication
cache or checkpoint identity migration is implied.

Seven tests passed in 0.251 seconds locally, and independently passed in
0.253 seconds. Exact source-bound evidence is
`data/near-quarter-tiny-batches-evidence.json`.

| Real geometry fixture | Exact full sets | Forward nodes | Forward leaf visits | Duplicates |
| --- | ---: | ---: | ---: | ---: |
| n3 | 1 | 2 | 1 | 0 |
| n5 | 0 | 5 | 0 | 0 |
| n7 | 0 | 11 | 0 | 0 |

Forward and reversed diagonal/orbit/row orders reproduce the brute-force
family-cardinality geometry census with exactly one visit per full set and
restored empty state. The differing node counts from the earlier one-orbit
prototype are tiny structural observations, not a performance forecast.

Because those real tiny fixtures have only one positive full set, separate
**abstract row-quota** fixtures exercise richer batch enumeration: a triangle
has one full selection, and a nine-orbit fixture with parallel incidence types
and weight-two singletons has twelve. Both orders visit every expected abstract
selection exactly once. These fixtures are not claimed to be physical
near-quarter point configurations; real geometry projection is tested separately.

Across all valid tiny partial states, 8,870 ordered two-orbit transaction
attempts (8,522 rejections) agree with independently expanded brute-force
geometry/family checks and restore byte-identical prior state after rejection
or successful push/pop. Additional tests cover an injected second-push exception,
quota exhaustion, timeout after a successful pair batch, invalid orders/input,
and hard rejection of n9/n71/n79. A limited run reports incomplete and retains
no accepted exhaustion claim. The evidence writer converts heterogeneous
summary keys to strings before canonical JSON serialization; this is report
serialization only, not an engine change.

| Artifact | SHA-256 |
| --- | --- |
| Tiny batch source | `417afd94483580b4697afc5edfd48b76d2310d5697e2bb44c08fbfe7977559ad` |
| Tiny batch tests | `9ef5c01e07526d602a19afba9b0c9e03d2b2c3d56fa4967bae758563697bb598` |
| Tiny batch evidence | `db9be104029ce58654ffb789c0d2a75a13ced4dfb59564e2958e78eda7d43e69` |
| Unchanged packed state | `305562c35e305a975ad8232b478c082aa44040b8e6b7bf26a3e99ef1a59e232a` |

Next steps require separate Lead allocation. The production plan in
`research/near-quarter-packed-worker-plan.md` still proposes only future packed
layout, checkpoint/commit/replay, immutable witness and host resource gates.
No serializer, resumed frontier or production guard wrapper has passed those
gates. The paused full-CNF branch remains unchanged, and neither this tiny
approval nor packed-payload arithmetic authorizes an n79 worker or run.
