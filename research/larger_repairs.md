# Round 2: nonuniform embeddings and larger repairs

Date: 2026-11-26. Author role: Mathematician, model `gpt-6-astra`, reasoning
`high`. This is an authored computational derivation, not an independent
review of itself. Hourly review cadence was not treated as an idle gate.

## Result

The published 156-point order-78 witness was tested under **all 6,241 ways**
to insert one empty row and one empty column into the 79-square. Exact source
quarter-turn symmetry reduced this to 1,561 representatives, with a proved
correspondence for the other cases. Only the four ordinary corner embeddings
remain valid 156-point witnesses. Every genuinely nonuniform embedding is
invalid; the lowest conflict count is 16 triples.

For **all 6,237 nonuniform embeddings**, exact repair enumeration rules out
157 or 158 points after deleting at most four of the transformed seed points
and adding arbitrary grid points, including readding deleted points. This
result is specific to this source and this embedding family. It is neither a
global upper bound nor a record claim. No new 157- or 158-point witness was
found.

The earlier guided corner audit separately excludes at most three deletions
for the four corner embeddings. Thus the combined completed results exclude
at most three deletions across the whole 6,241-embedding family. Extending that
combined statement to four deletions also requires the separate corner
four-deletion audit; this document does not assume its outcome.

## Mapping and exact symmetry reduction

For source order m and cuts a,b in {0,...,m}, define

    f_(a,b)(x,y) = (x + 1[x≥a], y + 1[y≥b]).

This map is injective and stays inside the (m+1)-square. It need not preserve
collinearity or noncollinearity. For example the valid partial source
(0,0),(1,2),(2,3) becomes collinear after cuts (0,3): its images are
(1,0),(2,2),(3,4). Every transformed set in the scan therefore receives a new
exact geometry check.

Let R_m(x,y)=(m−1−y,x), the source quarter turn. Direct substitution gives

    R_(m+1) ∘ f_(a,b) = f_(m−b,a) ∘ R_m.

For the first coordinate, this uses

    m−1−y + 1[m−1−y≥m−b] = m−y − 1[y≥b].

The implementation explicitly checked R_78(S)=S by coordinate-set equality
for the actual published source, after both exact geometry validators accepted
it. It follows that cuts (a,b) and (78−b,a) give rotated copies of the same
point set. Rotation preserves all integer collinearity counts, deletion
budgets, and possible inserted points. Consequently it preserves the entire
repair problem, not just the validity of the initial seed.

The 79×79 cut lattice has 1,560 four-element orbits and the singleton (39,39),
for 1,561 representatives total. The four old corner cuts
(0,0),(0,78),(78,78),(78,0) form one orbit. Thus **the four previous corner
repair experiments are equivalent for this explicitly checked source**;
future exact neighborhood audits can run one representative and transport the
result by rotation. This equivalence must be rechecked for a different source.
It does not require the target solution itself to have quarter-turn symmetry.

## Zero-deletion insertion capacity

Every transformed 156-point seed still has two points in each occupied row
and column, one empty row b, and one empty column a. If it is valid, every
new point must lie in both that empty row and that empty column, hence must
be (a,b). Thus there is only one possible zero-deletion addition; two additions
without deletion are impossible by row/column capacity.

The only valid representative is the corner cut (0,0), whose gap has six
disjoint blocking pairs. It cannot accept even that single point. Invalid
embeddings do not inherit this valid-seed argument until their existing
conflicts are removed.

## Exact repair coverage

The second audit first lists every collinear triple in each invalid embedding.
Any deletion set producing a valid retained subset must hit every such triple.
The minimal-hitting-set routine branches on all three endpoints of an uncovered
triple. Every hitting set contains at least one endpoint, so this branching is
complete through the stated deletion bound. Filtering out strict supersets
retains all inclusion-minimal hitting sets. Every admissible deletion set
contains one of these minimal sets; enumerating all additional deletions up
to the bound therefore enumerates all admissible deletion sets, including
nonminimal ones.

For each retained valid subset, the implementation finds rows and columns
with fewer than two points. Every possible new point must lie at an
intersection of such a row and column. At most k deletions from a transformed
full seed create at most k+1 eligible rows and k+1 eligible columns, so only
(k+1)² cells need consideration before geometry filtering. Deleted old cells
are included when individually addable.

Each candidate cell is checked against every pair of retained points via
exact primitive-direction grouping. All addition subsets of size |D|+1 and
|D|+2 are then checked for two-new/one-retained and three-new triples. Triples
entirely in the retained subset were already removed by the hitting set.
These conditions exhaust every possible triple. Any accepted 157/158 set
would be checked by both full certificate validators before being recorded.
None was accepted in this round.

The audit checks deadlines and marks incomplete work as `timeout_incomplete`.
All reported runs here completed. Minimal-hitting-set recursion was used only
at budgets three and four, with at most 1+3+...+3^k branch nodes before pruning;
this is not a promise that arbitrarily larger budgets remain inexpensive.

## Completed computations

| Computation | Exact scope | Result | Wall time |
|---|---|---|---|
| Geometry scan | 1,561 representatives, covering 6,241 embeddings | Four valid embeddings, all corners | 2.840 s |
| Initial repair probe | Ten lowest-conflict invalid representatives, ≤3 deletions | No improvement | 0.156 s |
| Full three-deletion repair | All 1,560 invalid representatives | 310 admissible deletion sets; no improvement | 6.613 s |
| Four-deletion repair, closest two | Cuts (0,1),(0,77), covering eight embeddings | 23,872 deletion sets; no improvement | 14.918 s |
| Four-deletion repair, remaining | Other 1,558 invalid representatives | Only three admissible deletion sets; no improvement | 7.184 s |

These research runs used about **31.71 seconds** of measured wall time in
total, within the 60-second aggregate allowance. Tests and final small
certificate checks added well under one second. The listed intermediate probe
and three-deletion run overlap the final four-deletion scope; their counts
must not be summed as distinct mathematical cases.

At cut (0,1), the unique inclusion-minimal hitting set through four deletions
is source indices {0,1}; at cut (0,77), it is {154,155}. For each, adding zero,
one, or two optional deletions yields 1+154+C(154,2)=11,936 deletion sets.
There were 12 and 315 possible target-157 addition subsets respectively, all
invalid, and no target-158 subsets with sufficient capacity.

Only three other representatives can remove every existing triple with at
most four deletions:

- Cut (0,2): delete indices {0,1,2,3}.
- Cut (0,76): delete indices {152,153,154,155}.
- Cut (1,1): delete indices {0,1,52,88}.

Each admits one such deletion set and too few individually addable cells to
reach 157. Every remaining invalid representative requires at least five
deletions merely to eliminate its existing collinear triples. This lower
bound concerns deletions from that transformed seed, not arbitrary solutions.

## Files and verification

Implementation: `research/embedding_audit.py`. Eight test methods in
`tests/test_embedding_audit.py` passed. Tests compare the conflict counter with
independent cross products over all subsets of size at most six of a 3-square;
check the rotation identity pointwise for small grids; check old-corner
correspondence; compare full and symmetry-reduced scans; disable symmetry for
an asymmetric seed; check timeout labeling; compare hitting sets with full
subset enumeration; and compare complete repair counts against an independent
small-instance deletion/addition enumerator.

Machine-readable results:

- `data/embedding-audit.json`: every representative's exact conflict count,
  equivalent cuts, and valid-seed gap blockers.
- `data/embedding-repair-frontier.json`: initial ten-case repair probe.
- `data/embedding-repair-all-cuts.json`: all nonuniform cases through three
  deletions.
- `data/embedding-repair-four-deletions.json`: the two closest representatives
  through four deletions.
- `data/embedding-repair-four-deletions-remaining.json`: all other nonuniform
  representatives through four deletions.
- `data/embedding-low-conflict-cut-0-1.json` and
  `data/embedding-low-conflict-cut-0-77.json`: full 156-point **invalid** initial
  states with 16 exact conflict triples each, confirmed by both independent
  geometry methods. They are repair inputs, not valid witness certificates.

To reproduce the geometry scan, run
`python3 research/embedding_audit.py --seconds 45` from the workspace. To
reproduce the full nonuniform four-deletion scope in a single bounded call
(the saved run above used two disjoint batches), use:

```python
import json
from pathlib import Path
from research.embedding_audit import repair_low_conflict
seed = json.loads(Path("data/published-n78.json").read_text())
scan = json.loads(Path("data/embedding-audit.json").read_text())
selected = sorted((r for r in scan["records"] if r["conflict_count"]),
                  key=lambda r: (r["conflict_count"], r["cut"]))
scan["lowest_conflict_invalid_representatives"] = selected
result = repair_low_conflict(seed, scan, seconds=45,
                            max_deletions=4, top=len(selected))
Path("data/embedding-repair-four-deletions-rerun.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n")
```

The resulting status must be checked before treating the rerun as complete.

## Next concrete experiment

Before spending a large five-deletion repair budget, enumerate minimal
five-element conflict covers for the first newly repairable nonuniform
embeddings, and rank their individually addable pools by retained count plus
pool size. Only a pool reaching 157 merits subset compatibility search. Avoid
repeating the four corner cases: they are proved equivalent for this source.
An alternative requiring genuinely new work is a second row/column insertion
followed by a different compression, but its geometry must again be checked
without assuming affine preservation.

No further compute is silently scheduled by this document. The shepherd can
choose the next bounded run from these recorded results while research
continues between hourly reviews.

## Round 3: five-deletion frontier, partial large classes

The next separately authorized round added a provenance safeguard before
further research: every repair now validates the source with both full exact
checkers and requires its normalized hash to match the scan. A mismatched scan
or invalid source raises an error. Ten test methods now pass, including this
regression and streamed resume/count comparisons.

All 1,560 invalid embedding representatives were classified for minimal
conflict covers of size at most five in 9.035 seconds. **No new size-five
minimal covers appeared.** There remain exactly the two representatives with
a unique size-two cover and the three representatives with a unique size-four
cover listed above. All other nonuniform representatives require at least six
deletions merely to remove their existing conflicts.

The three size-four-cover classes were fully repaired through five deletions
in 0.372 seconds: 153 deletion sets each (the previous four-deletion set plus
152 exact-five supersets). Four target-157 addition subsets were tested in
total and none was valid; no target-158 subsets had sufficient capacity.
Therefore **6,229 of the 6,237 nonuniform embeddings are now excluded through
five deletions**. This number deliberately excludes the eight embeddings in
the two unresolved size-two-cover orbits, as well as the four corner cases.

Each remaining representative has C(154,3)=596,904 exact-five deletion sets.
Materializing these sets was avoided. `stream_cover_repairs` enumerates the
lexicographic combinations of three non-base source indices, holding one
deletion set at a time. Each call stores only the first independently verified
certificate for each target size, if any, plus counters and a resume offset.

| Representative | Completed exact-five ordinals | Target-157 subsets tested | Valid | Next offset | Status |
|---|---|---|---|---|---|
| (0,1), base {0,1} | 0 through 19,999 | 23 | 0 | 20,000 | `case_limit_incomplete` |
| (0,77), base {154,155} | 0 through 19,999 | 469 | 0 | 20,000 | `case_limit_incomplete` |

These calls took 19.349 and 19.177 seconds. Each leaves **576,904** deletion
sets unexamined; neither class is closed at five deletions. No target-158
addition subsets occurred in these prefixes. Research compute for this round
totaled about **47.93 seconds**, plus well under one second of tests and
validation, within its separate 60-second allowance.

Results are saved in:

- `data/embedding-five-cover-classification.json`
- `data/embedding-five-repair-four-cover-classes.json`
- `data/embedding-five-stream-cut-0-1-offset-0.json`
- `data/embedding-five-stream-cut-0-77-offset-0.json`

The stream offset advances only after every addition subset for a deletion
set has finished. A deadline inside a deletion set leaves its offset unchanged
so it is safely repeated. Counters include completed deletion sets only;
an already independently verified candidate may be retained even if its
deletion set is interrupted. `complete` on a resumed call covers its stated
suffix; earlier offsets still require their saved run records.

Because numeric indices depend on input order, normalized geometric hashes
alone are insufficient for resume safety. Each stream result also records an
order-sensitive hash of source n and its points array. A nonzero resume offset
requires the matching `expected_source_order_sha256`; otherwise execution is
rejected. The present ordered source hash is
`e7678d82888f177d779c4ca250d6cda995645a13e0c102b5727138a835c0c9bb`.
The machine-readable saved value is authoritative if this document and the
input ever change.

The next numerical continuation for either large class is:

```python
from research.embedding_audit import stream_cover_repairs
previous = json.loads(Path("data/embedding-five-stream-cut-0-1-offset-0.json").read_text())
result = stream_cover_repairs(
    seed, scan, previous["cut"], previous["base_deletion_indices"],
    deletion_count=5, start_offset=previous["next_offset"],
    max_cases=20000, seconds=20,
    expected_source_order_sha256=previous["source_order_sha256"])
```

Save this under a new offset-specific filename, preserving the previous
record. The same call applies to (0,77) with its own prior record. Neither a
case quota nor a timeout supports an exclusion of the remaining cases.

## Continuous worker and durable continuation

`research/embedding_worker.py` exposes the existing exact stream as a bounded
CLI. `--previous` accepts an immutable stream record or an existing tip pointer;
`--output` names the durable tip. Defaults are 900 seconds, 20,000 cases per
checkpoint chunk, and a large total case limit. A worker loops through chunks
until its wall-time budget, invocation case limit, or frontier end is reached.
It does not restart the numerical search at zero.

```sh
python3 research/embedding_worker.py \
  --previous data/embedding-tip-cut-0-1.json \
  --output data/embedding-tip-cut-0-1.json --seconds 900

python3 research/embedding_worker.py \
  --previous data/embedding-tip-cut-0-77.json \
  --output data/embedding-tip-cut-0-77.json --seconds 900
```

Run these on separate allocated lanes, never duplicate workers on the same
tip. An exclusive process lock rejects that duplication. Source and scan paths
can be overridden with `--seed` and `--scan`; their defaults are the existing
published source and embedding audit. `--max-cases` bounds total new deletion
sets in the invocation, and `--chunk-cases` changes the checkpoint granularity.

Every completed chunk writes a new immutable, offset-specific result file.
Its predecessor's path and exact file hash are recorded; atomic tip replacement
occurs only after that result is written. Existing records are not overwritten.
At startup, the whole predecessor chain is checked for matching geometry and
input-order hashes, consistent frontier parameters, exact completion counts,
and gapless offsets reaching a zero-offset origin. Passing a stale previous
record while a newer matching output tip exists resumes the newer tip. A suffix
can close the frontier only when this verified chain reaches its declared end.

Any found candidate is verified with both full checkers and immediately written
to its own immutable `embedding-witness-*` JSON before the chunk finishes. A
process interruption can lose uncheckpointed search work, which is repeated
from the previous tip, but cannot turn an incomplete chunk into completed
coverage. `timeout_incomplete` and `case_limit_incomplete` remain explicit in
the saved chunk record. A zero-progress invocation preserves the last offset.

Four worker tests cover subprocess CLI execution, restart, stale-input
protection, ancestry gap/hash rejection, preserving immutable results, and
immediate valid witness files using a small fixture. Together with the ten
embedding tests, all fourteen passed before deployment handoff.

A bounded numerical smoke test used 10.041 seconds and advanced cut (0,1)
from offset 20,000 to **29,851**, saving
`data/embedding-stream-cut-0-1-start-20000-end-29851-e5af25ae.json` and updating
`data/embedding-tip-cut-0-1.json`. It found no witness and remains incomplete.
`data/embedding-tip-cut-0-77.json` was initialized without numerical search at
offset **20,000**. Read the live tips before future work; these documented
offsets are the handoff snapshot, not promises that later workers remain idle.
