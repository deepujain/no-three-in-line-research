# Independent review of blocker-guided repair

Date: 2026-11-26. Role transition: the Mathematician became Mathematical
Reviewer of the Research Software Engineer's guided-repair implementation.
Reviewer model: `gpt-6-astra`, reasoning `high`. This is a separate author's
review of the engineer's method and code, not an independent review of the
reviewer's own earlier baseline-construction proofs.

**Disposition: approved for the stated finite neighborhood and current
completed audit.** No global nonexistence conclusion follows. The sole code
correction requested concerned deadline checkpoints; the engineer implemented
it and added a deterministic timeout test before this review was finalized.

## Reviewed artifacts

SHA-256 hashes at review:

- `research/guided_repair.py`:
  `b600019246b2490a565094b7a28eabe402e69ae72748e23dcd881d22c5cd245c`
- `tests/test_guided_repair.py`:
  `d727fb1408d4fcfd98c540b10eb3fb0e8655f6abde57eb439eaa752d324cb57c`
- `data/guided-repair-audit.json`:
  `0fafd14e17cd3bea57eebdee5879ee9d573183efcecea2be301dc8ea2d433670`

The engineer produced the actual order-79 audit. This reviewer inspected its
full scope and summary counts, reviewed the algorithm, reran its small-instance
tests, and performed an additional independent exhaustive small-instance
comparison. The reviewer did not independently rerun the full order-79 audit.

## Completeness argument

Let S be the validated old seed, let c be a grid cell outside S, and partition
S by unoriented primitive direction from c. Since S has no collinear triple,
each part contains at most two points. The parts of size two are exactly the
old pairs that obstruct insertion of c. They are pairwise disjoint: each old
point belongs to exactly one part.

For a deletion set D, insertion of c into S\D is individually valid if and
only if D meets every blocking pair. In particular, if |D|≤k, the number of
blocking pairs is at most k. Thus the implementation loses no useful new cell
by retaining only those with at most k pairs.

Every improving repair must contain at least one point outside S; readding
only deleted old points cannot increase cardinality. Choose such a new point
c. For each of its disjoint blocking pairs, choose an endpoint in D. These
choices form a subset B of D. The endpoint Cartesian product enumerates B,
and optional extra deletions enumerate D\B. Therefore the union of generated
deletion sets contains every D of size at most k that can support an improving
repair. Sorting and deduplication change neither coverage nor validity.

For zero blocking pairs, Python's Cartesian product of zero iterables yields
one empty tuple. This correctly generates D=empty and its optional supersets.
Budget zero is therefore covered. If no cell has zero blockers, there can be
no zero-deletion improvement, so omitting the empty deletion set is sound.

For each generated D the candidate pool includes every new cell whose blockers
are hit, and **also every deleted old point**. Deleted seed points are
individually valid for readdition because S was valid. Hence all possible
addition sets for this D are present, including repairs that readd some old
holes. The code enumerates every subset of size |D|+1 and |D|+2.

For any such subset Q, all possible triples in (S\D) union Q fall into four
classes:

1. Three retained seed points: valid because S is valid.
2. One insertion and two retained points: excluded by blocker filtering, or
   by original-seed validity for a readded seed point.
3. Two insertions and one retained point: excluded by the integer
   `seed_points_on_pair` bit mask intersected with the retained-point mask.
4. Three insertions: excluded by direct integer determinant checks.

These checks are collectively necessary and sufficient. Pair compatibility
alone would not suffice, but the implementation includes the all-new triple
test. Pools contain distinct cells and omit retained seed cells, so uniqueness
is preserved. Both certificate verifiers check each first discovered target
before it is emitted through the callback.

An alternative implementation could omit readded old points when claiming
coverage over all budgets up to k: cancel their deletion and reinsertion to
obtain a smaller effective D. That cancellation argument is not needed here,
because the reviewed implementation includes them explicitly. It would need
qualification for a claim about exactly k deletions.

## Tests and timeout semantics

The six guided-repair test methods passed in review. They cover small exact
repair counts, optional extra deletions, invalid inputs, first-discovery
validation, an immediate timeout, and a timeout during pair preprocessing.

The reviewer additionally enumerated every one of the 16 possible subsets of
the 2×2 source grid, for each budget 0,1,2,3: 64 source/budget cases. For each
case, a separately written direct determinant enumerator considered every
old deletion set through the budget and every size-|D|+1/|D|+2 subset of all
cells outside the retained seed in the 3×3 target. Exact valid-addition counts
matched the guided implementation separately for every deletion set, treating
omitted deletion sets as having zero improving repairs. This includes empty
and partial seeds, zero-blocker anchors, readdition of old holes, and triples
consisting entirely of newly added cells.

Initially, the deadline was checked only once per anchor while generating
optional deletion supersets, and not during pair preprocessing. This could
overshoot the declared runtime substantially on larger candidate families.
The engineer added checks inside optional-combination enumeration and pair
preprocessing, plus a deterministic mock-clock regression test. The reported
order-79 audit finished in about one second, well within its budget.

The deadline is cooperative rather than a hard process kill: an individual
geometry operation, sorting, or validation can finish between checks. A
timeout result is explicitly incomplete. `deletion_sets_completed` advances
only after both target-size subset searches for that D finish. Other counters
can include work on an interrupted D; they must not be interpreted as a
completed-neighborhood proof. A top-level `complete` requires all four
translations to complete.

## Current finite result and its limits

The reviewed report states `complete` with maximum three original-seed
deletions. Each of the four translations has:

- 30 eligible genuinely new cells.
- 1,456 relevant deletion sets: 8 of size two and 1,448 of size three.
- All 1,456 deletion sets completed.
- Exactly one individually addable genuinely new cell for each deletion set.
- 1,456 tested target-157 addition subsets and zero valid ones.
- No target-158 addition subsets because the pools are too small.

The one-new-cell pool count also explains the negative result directly. For
|D|=d the pool consists of that one new cell plus the d deleted old points.
Reaching 157 would require reinserting every deleted point and adding the new
cell, restoring S plus that cell; original blockers make this invalid.
Reaching 158 requires d+2 additions from a pool of size d+1 and is impossible.

The precise justified conclusion is: **for this verified published 156-point
seed, embedded by each of the four contiguous corner translations in the
79-square, no repair deleting at most three original seed points can produce
a valid 157- or 158-point set, even when deleted seed points may be readded.**
This does not exclude four-or-more-deletion repairs, internal row/column
insertions or other coordinate deformations, different seeds, unrelated
constructions, or a global order-79 solution. No new extremal witness was
found and no literature-priority claim is made.
