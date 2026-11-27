# Mathematical synthesis of completed corner repair families

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.

**Conditional on the correctness of the audited recorded computations, no
157- or 158-point no-three-in-line set can be obtained from any of the four
corner translations of this specific 156-point n78 source by deleting at
most five original points and adding arbitrary grid points.** This closes
that repair family. It does not exclude configurations from another source,
repairs deleting more than five original points, or unrestricted n79 sets.
It supplies no novelty claim or independently replayed proof certificate.

## Evidence joined by this review

The reviewed manifest is
`data/corner-anchor-frontier/manifest.json`, SHA-256
`e45bfeaed19f5b519a8cdda3ab411bbf874ca365903d46c7cadd802ab64137a1`.
The normalized source identity is
`e197d1b41f97df9188b9839a54f0013bbc08b67d202c18d26146a7f377d80ced`
and the ordered source identity is
`e7678d82888f177d779c4ca250d6cda995645a13e0c102b5727138a835c0c9bb`.
The concrete search embedding has cut (0,0), hence translation (+1,+1).

I read the four completed audit summaries and their independent review notes,
checked their common manifest/source/order identities, and independently
recomputed the manifest size classes, ordinal partition, and binomial totals.
All 10,304 manifest anchors are accounted for exactly once as anchor IDs:

| Base size | Manifest ordinals, half-open | Anchors | Cases per anchor | Overlapping anchor-case sum | Tested 157 / 158 addition subsets |
| --- | --- | ---: | ---: | ---: | ---: |
| 5 | [0,8136) | 8,136 | 1 | 8,136 | 8,136 / 0 |
| 4 | [8136,10072) | 1,936 | 152 | 294,272 | 303,968 / 1,672 |
| 3 | [10072,10296) | 224 | 11,628 | 2,604,672 | 2,680,200 / 12,672 |
| 2 | [10296,10304) | 8 | 596,904 | 4,775,232 | 4,876,488 / 16,960 |

The case count per anchor A is C(156-|A|,5-|A|). Their sum is 7,682,312.
Different anchors may contain the same exact-five deletion set, so this sum
is a workload count, never a distinct-deletion count. Overlap does not weaken
coverage: union coverage requires every anchor, not disjoint anchor families.
All four audits report zero valid addition subsets and no saved witnesses.

The size-three audit was independently performed by the Literature Researcher;
its final script additionally rejects unexpected record witness references.
I did not repeat its 13,664-file I/O. The other audit reviews separately
checked their full histories. Their source/manifest/selection bindings,
gapless offset coverage, counters and byte hashes establish record consistency.
The numerical deletion/addition computations were not independently replayed.
Later archival packaging is a separate artifact-preservation check, not a
stronger mathematical certificate.

| Completed audit summary | SHA-256 read for this synthesis |
| --- | --- |
| `data/corner-batch-small-summary.json` | `3bfde4dbdad954a1cd525f0c277e1cfa25a7967f8262c5728af2acdad13c0b01` |
| `data/corner-batch-four-summary.json` | `f463f620aeb50eb7cece9968d1001941e302ed4de748f63f7a3320386b1b4679` |
| `data/corner-batch-three-summary.json` | `0bd50f9dcb770871099829b41b8ba2b44d78d351bee6b18f58e3eb29f9c4c1ae` |
| `data/corner-size-two-summary.json` | `2b392fb1f8e0a549db8441872e0fe503c83fd136b3636306e3491bc99b02dd67` |

The prior independent mathematical and worker reviews are
`research/corner-anchor-review.md` and `research/corner-batch-review.md`.
The completed history reviews are `research/corner-batch-small-review.md`,
`research/corner-batch-four-review.md`, `research/corner-batch-three-review.md`
and the final size-two addendum in `research/corner-progress-review.md`.

## Why all exact-five repairs are covered

Let S be the translated valid 156-point source and F a proposed valid target.
Since |F|>|S|, F includes a genuinely new cell c outside S. Relative to S,
the pairs blocking c are disjoint: three old points in one direction group
would already contradict S's validity. Any deletion set D making c available
must hit every blocking pair. For |D|=5, c has at most five blockers.

Selecting one deleted endpoint from each blocker yields an endpoint cover
C contained in D. The independently reconstructed manifest enumerates every
such cover for every eligible c and retains its inclusion-minimal antichain.
Every C contains a retained anchor A. Hence D contains A and is visited by
that anchor's complete exact-five superset stream. The worker then enumerates
every possible six- or seven-point insertion set for targets 157 or 158.
Its prefilters and exact checks exclude precisely the possible old/old/new,
old/new/new and new/new/new collinear triples. Therefore a valid repair would
be found in at least one of the now-completed streams.

## Why the result covers at most five deletions

Suppose F deletes only d<5 points from S. Enlarge the actual deletion set
S minus F arbitrarily to a five-element D subset of S. This is possible
because |S|=156. Then S minus D is still contained in F, and F is obtained
by adding exactly six points for target 157, or seven for target 158, to
S minus D. The extra padded deletions are simply readded.

The independently reviewed worker allows such readdition: it marks retained
source points occupied and permits removed source points in the addition
pool. Thus exact-five closure already implies closure for every d<=5.
This padding argument avoids any need to reinterpret or sum earlier
smaller-budget run counts. It depends on the verified readdition semantics.

## Why the result transfers to all four corners

I independently reread the actual 156-point source and checked the exact set
identity R78(S)=S for R78(x,y)=(77-y,x). For u,v in {0,1}, the 79-grid quarter
turn R79(x,y)=(78-y,x) maps the translated source S+(u,v) to
S+(1-v,u). I checked all four of these set identities directly. The map cycles
all four corner translations and preserves integer collinearity, cardinality,
grid membership and the number of original points deleted. Consequently a
repair of any corner would rotate to a repair of the completed (+1,+1) corner.

This symmetry belongs to this checked source. It does not justify transferring
the result to an arbitrary n78 seed. Other insertion cuts require their own
prior audit; any synthesis with those results retains their separate evidence
and trusted-computation qualifications.

## Corollary for all 6,241 insertion embeddings of this source

The separate completed nonuniform result in `data/embedding-five-summary.json`
has SHA-256
`0b9cac2176464f13dea0e2ce2c6c0b8695decfb6fad5f5dbd4951c23b4e1a41e`.
Its independent review, `research/embedding-review.md`, has SHA-256
`8c318a90a64bf3155319d18274e53dc356c4f22fe55d2f79ffb95088244d4c78`.
I read both, checked the shared normalized source identity, target sizes
157/158 and deletion budget five, and matched the classification's 1,560
representative cuts to the invalid representatives in the original scan.
Their recorded rotation-orbit union is exactly 6,237 cuts, disjoint from
{(0,0),(0,78),(78,0),(78,78)}. Adding these four corner cuts gives exactly
{0,...,78} squared, with 6,241 insertion choices.

I additionally reread and byte-hash checked the two final nonuniform streamed
tips and their terminal records against the summary. Both terminal records
bind the same normalized and ordered source hashes as this corner review,
exact deletion count five, completed offset 596,904, and zero valid counters
for targets 157/158. The summary itself does not carry the order-sensitive
hash; that binding comes from these records and the previous full-chain audit.
Non-resumed classification and finite repair reports use the common normalized
source identity. I also inspected the repair enumerator: only retained points
are marked occupied, so removed source cells are eligible for readdition;
the insertion size is deletion_count plus one or two. Its semantics therefore
match the corner proof. I did not repeat the prior complete chain audits or
the underlying repair/classification computations.

It follows, conditional on both sets of audited recorded computations, that
**none of the 6,241 embeddings formed by inserting one grid row and one grid
column into this particular 156-point n78 source admits a valid 157- or
158-point repair after at most five original-point deletions, with arbitrary
grid-point insertions and readdition allowed.** The embeddings may be invalid
before deletions; the prior nonuniform audit explicitly handles their conflict
triples. This is a result for this finite repair family and this source. It is
not a global n79 infeasibility result, a novelty claim, or a proof established
by independent numerical replay. The four corner completion audits provide
new scope beyond the older summary's corner budget of four; the historical
summary remains unchanged.
