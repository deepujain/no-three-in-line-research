# Alternating-trade experiments

Research software engineer configuration: `gpt-6.1-sol`, reasoning `high`; Python 3.14.7, standard library only. All work was local and single-core. Pilot deadline: 2026-11-27T22:59:25Z. No novelty or global nonexistence claim is made.

## Representation, moves, and exact score

`src/trade_search.py` represents a full 2n state as two disjoint permutations, giving every row and column exactly two points. A pair move swaps two entries of one permutation. A triple move cyclically rotates three entries of one permutation. Either move is rejected if a replacement overlaps the other matching. Legal moves preserve row and column degrees exactly. Periodic alternating-cycle recoloring exchanges the two matchings on a complete cycle without changing any grid points.

Axis triples are excluded by the degrees. The score counts all other collinear triples through primitive unoriented integer directions. Exact score deltas remove changed points sequentially, subtracting triples through each removed point, then add replacements sequentially, adding their new triples. This handles triples containing multiple changed points exactly once. Every final full-state score is recomputed by both the normalized-slope checker and the independent cross-product enumeration. Degree invariants are also rechecked.

Annealing allows uphill moves. The temperature cools quadratically in each configurable proposal cycle, with a floor of 0.03. Default periods are 5,000 proposals per cooling cycle, 200 proposals between matching recolorings, and 20,000 proposals without improvement before a restart. Resumed runs restart from their strongest saved full state. A configurable fraction of proposals takes its first row from current conflict incidences; the remaining rows are sampled uniformly. Conflict rows refresh every 200 proposals by default. Mixed mode chooses pair and triple moves with equal probability.

Optional tabu control rejects recently accepted point sets unless a proposal improves the global best score. The tabu queue has an explicit capacity. Revisit telemetry now uses a separate bounded exact least-recently-used cache, default 10,000 point-set keys, controlled by `--history-size`. It records current tracked keys, evictions and cache-relative revisits; it does not claim a lifetime distinct-state count. This fixes the original unbounded telemetry collection noted during independent review. Old run records from before the fix retain their original lifetime-count field; later records state the bounded scope explicitly.

The strongest full state is retained during uphill moves and restarts. A nonzero minimum score is a heuristic search result, never an impossibility proof.

## Seed completion and checked resume

The published 156-point n=78 seed fits n=79 but leaves one row and column empty. To construct a full degree-two state, initialization removes two existing edges in distinct rows and columns, then inserts four edges joining those rows and columns through the missing row and column. This yields 158 distinct points with the required degrees, generally with collinear triples. The resulting bipartite degree-two components are even cycles; alternating edge colors produce two permutation matchings.

This invalid-state initialization can subsequently alter arbitrarily many seed points and does not repeat the closed valid repair neighborhood with at most three deletions. The original independently verified 156-point seed remains a separate valid incumbent. Greedy pruning of a best full state replaces that incumbent only if it produces a larger valid set, accepted by both exact verifiers.

`--resume-state` takes a full-state JSON file. Claimed score and validity fields are ignored: schema, n, coordinates, duplicates, degree two and both exact geometry scores are checked afresh, followed by matching decomposition. An independent valid baseline can still be passed through `--initial`; resuming an invalid full state does not replace that baseline.

Search-state files explicitly contain `state_kind`, `valid` and `collinear_triple_count`, and are separate from valid incumbent files. An invalid state is labeled `invalid_full_search_state`. Canonical hashes follow the shared n+sorted-points contract.

## API and CLI

`search(n, seconds, seed, max_iterations=None, initial=None, temperature=2.5, cooling_period=5000, recolor_period=200, restart_period=20000, resume_state=None, move_kind="pair", focus_probability=0.0, tabu_size=0, focus_refresh_period=200, history_size=10000)` returns `{incumbent, search_state, run}`. With `seconds=None`, an operation cap is required. Operation-capped runs with the same inputs and settings are deterministic; wall-clock stopping can change iteration counts and outputs. Search loops obey the requested budget; initialization, pruning and independent audits add measured overhead. n must be at least two; triple and mixed modes require n at least three. Rectangle mode also works for n=2.

```sh
python3 src/trade_search.py --n 79 --seconds 15 --seed 270079 --temperature 0.5 --initial data/published-n78.json --output-prefix data/trades-example
python3 src/trade_search.py --n 79 --seconds 17 --max-iterations 50000 --seed 271079 --initial data/published-n78.json --resume-state data/trades-n79-seed270079-state.json --move-kind mixed --focus-probability 0.85 --tabu-size 500 --temperature 0.5 --output-prefix data/trades-resume-example
```

The CLI writes separate `-incumbent.json`, `-state.json` and `-run.json` files and emits the run record as JSON. `--cooling-period`, `--restart-period` and `--history-size` support continuous worker configuration. No worker subprocesses or threads are created.

## Initial bounded benchmarks

The first allocation used 45.612261 measured aggregate seconds, below its 60-second allowance. Small grids used 0.2-second loop budgets and a 5,000-proposal cap. Each n=79 run used a 15-second loop budget and the published seed. Totals include initialization, pruning and independent audits. Summary: `data/trades-summary.json`.

| n | seed | moves | temperature | proposals | accepted / uphill | best triples | incumbent | elapsed s |
|---|---|---|---|---|---|---|---|---|
| 2 | 270002 | pair | 2.5 | 0 | 0 / 0 | 0 | 4 | 0.000139 |
| 3 | 270003 | pair | 2.5 | 0 | 0 / 0 | 0 | 6 | 0.000124 |
| 4 | 270004 | pair | 2.5 | 19 | 8 / 4 | 0 | 8 | 0.000268 |
| 5 | 270005 | pair | 2.5 | 80 | 28 / 8 | 0 | 10 | 0.000658 |
| 6 | 270006 | pair | 2.5 | 1635 | 598 / 202 | 0 | 12 | 0.013860 |
| 7 | 270007 | pair | 2.5 | 1671 | 593 / 215 | 0 | 14 | 0.016844 |
| 8 | 270008 | pair | 2.5 | 2716 | 795 / 265 | 0 | 16 | 0.031802 |
| 9 | 270009 | pair | 2.5 | 5000 | 768 / 259 | 2 | 17 | 0.063377 |
| 79 | 270079 | pair | 0.5 | 124832 | 36 / 4 | 11 | 156 | 15.172489 |
| 79 | 270080 | pair | 1.5 | 120661 | 107 / 33 | 19 | 156 | 15.137136 |
| 79 | 270081 | pair | 3.0 | 120302 | 9359 / 3482 | 19 | 156 | 15.175563 |

The benchmark reached the known 2n target for n=2 through n=8. The short n=9 run yielded a valid 17-point subset and a full-state score of two; no maximality claim is made. All these small results are already known. The best n=79 full state has exactly 11 collinear triples and remains invalid. It is stored at `data/trades-n79-seed270079-state.json`, normalized hash `f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d`. All n=79 valid incumbents remain the published 156 points.

## Resumed pair/triple/mixed comparison

The second allocation used 42.765166 measured aggregate seconds, below its separate 60-second allowance. All trials began from the same audited score-11 state, preserved the 156-point baseline, used conflict-row probability 0.85, tabu capacity 500, cooling period 5,000 and restart period 20,000. The first three trials share seed 271079, temperature 0.5 and exactly 50,000 proposals; all completed before their 17-second caps. Two warmer trials then used 40,000 proposals and 14-second caps. Summary: `data/trades-resume-summary.json`.

| n | seed | moves | temperature | proposals | accepted / uphill | best triples | incumbent | elapsed s |
|---|---|---|---|---|---|---|---|---|
| 79 | 271079 | pair | 0.5 | 50000 | 8 / 4 | 11 | 156 | 7.630018 |
| 79 | 271079 | triple | 0.5 | 50000 | 0 / 0 | 11 | 156 | 9.960464 |
| 79 | 271079 | mixed | 0.5 | 50000 | 2 / 1 | 11 | 156 | 9.408785 |
| 79 | 271080 | mixed | 2.0 | 40000 | 82 / 29 | 11 | 156 | 7.374432 |
| 79 | 271081 | triple | 4.0 | 40000 | 3107 / 1260 | 11 | 156 | 8.391466 |

Every resumed trial retained minimum score 11. The cold triple run accepted no moves, showing that temperature 0.5 was insufficient for useful excursions in the sampled neighborhood. Warming triple moves to temperature four accepted 3,107 moves, including 1,260 uphill moves, without improving the saved minimum. This does not prove local or global optimality. No 157- or 158-point certificate was found. Every persisted state and incumbent was independently re-audited after the runs.

## Validation and next concrete experiment

Thirteen trade tests pass. Coverage includes every legal pair move on generated states across n=2..7 and every legal ordered triple rotation across n=3..7, comparing exact deltas and resulting scores with independent determinant enumeration while checking degrees. Further tests cover alternating recoloring, graph decomposition, seed completion, deterministic resumed runs, ignored misleading resume metadata, best-state retention, separate valid baseline preservation, bounded telemetry eviction, invalid-state labeling and input bounds. The separately owned experiment-pool process tests require host permission to spawn `ps` for the resource guard. The shepherd reports those tests pass with that permission; no guard was suppressed and no out-of-scope pool code was edited. Trade tests pass in the sandbox.

A larger and concrete next neighborhood is **uncolored alternating rectangles**: choose any two old edges with distinct rows and columns, replace them with the opposite rectangle edges if absent, and redecompose only after acceptance. The current matching-specific swaps can miss legal rectangles using opposite-colored edges in the same alternating cycle, because recoloring that whole cycle exchanges both colors together. Exhausting all unordered edge pairs of the 158-point score-11 state requires at most 12,403 proposals and can reveal improving or plateau moves outside the present matching-restricted neighborhood. A bounded annealing run using those broader rectangles would then be better motivated than simply lengthening these repeated temperature trials. This proposal has been sent to the shepherd; no additional unassigned search was run.


## Uncolored rectangle audit and comparison

The CLI now accepts `--move-kind rectangle`. This samples edges from either matching without a color constraint and crosses their columns, rejecting an occupied replacement. After an accepted switch, the full degree-two graph is decomposed again into two matchings. The score delta is the exact two-removal/two-insertion value. Bounded revisit and tabu caches remain in force.

For two bipartite edges with distinct rows and columns there are two row-to-column pairings: the identity pairing (the old edges) and the crossed pairing (the only nontrivial degree-preserving replacement). Reversing old-edge order yields the same crossed point set. The exhaustive audit checks unordered old-edge pairs once, so it covers both choices without duplicate switches.

`audit_rectangles(state, seconds=60)` validates the source with both exact checkers, then enumerates old-edge pairs. A timeout is explicitly incomplete. The complete score-11 audit is saved as `data/trades-rectangle-neighborhood-audit.json`. It examined all 12,403 unordered pairs in 1.487478 seconds: 158 share a row or column; 156 have an occupied replacement; 12,089 are legal switches. Every legal switch raises the score. There are four switches with delta +1, and the minimum neighboring score is 12. This establishes a **strict local minimum for this one fixed state's uncolored two-edge rectangle neighborhood**. It proves nothing about larger trades, other states, or global existence.

The recorded best neighbor replaces old edges (58,22) and (78,78) with (58,78) and (78,22). It is an invalid score-12 full state, saved separately as `data/trades-rectangle-best-neighbor-state.json`; its score and degrees pass both independent audits.

Three rectangle-annealing trials then used the same RNG seed 272079, the original score-11 resume state, exactly 50,000 proposals, focus probability 0.9, tabu capacity 1,000, cooling period 10,000 and restart period 100,000. Each completed under its 15-second loop cap. All preserve the independently verified 156-point seed. Summary: `data/trades-rectangle-summary.json`.

| temperature | proposals | accepted | uphill accepted | tabu rejected | best triples | valid incumbent | elapsed s |
|---|---|---|---|---|---|---|---|
| 0.75 | 50000 | 10 | 4 | 80 | 11 | 156 | 7.727579 |
| 2.0 | 50000 | 1030 | 353 | 6 | 11 | 156 | 8.209328 |
| 5.0 | 50000 | 8515 | 3555 | 0 | 11 | 156 | 9.597724 |

These trials took 25.534631 aggregate measured seconds; including the exact one-neighborhood audit gives 27.022109 seconds so far in this allocation, below its 60-second allowance. No improved full state or certificate was found. All three final full-state scores and valid incumbents were independently re-audited after persistence.

The thirteen trade tests include every legal uncolored switch on generated states for n=2..8, checked against independent determinant counts and degree invariants; edge-order reversal equality; exhaustive-audit histogram agreement; checked redecomposition; deterministic resumed rectangle search; and explicit partial timeout. The implementation is ready for the shepherd's bounded continuous queue, subject to the independent review already requested.

A more targeted next experiment is to follow all four delta-+1 exits from score 11, exhaust their rectangle neighborhoods, and then beam-search low-score states (initial threshold 12). This uses the exact landscape evidence to test a small energy barrier rather than extending another blind temperature sweep. The proposal was sent to the shepherd immediately after the measured runs.


## Exact low-barrier component search

The separate module `research/rectangle_barrier.py` performs breadth-first search in the graph of full degree-two states connected by uncolored rectangle switches, retaining only states whose exact score does not exceed a chosen threshold. Canonical n+point hashes deduplicate matching/color representations. Every node retains its parent hash and actual removed edges; replacement edges follow from the rectangle. Any new best state is independently checked by both verifiers and its complete source-to-state move path is saved immediately. Valid incumbents are independently checked and the published 156-point baseline is preserved unless improved.

At threshold 12, the source score-11 component was **completely exhausted** in 9.934555 seconds. It contains exactly six distinct states: the original score-11 state and five score-12 states. All four direct delta-+1 exits are included; the fifth score-12 state is reached at depth two. All six neighborhoods were fully scanned: 74,418 unordered edge pairs and 72,534 legal switches. There are 12 directed transitions staying within the threshold, and the final frontier is empty. This establishes that every uncolored-rectangle path from this fixed state to a lower score must visit a state of score at least 13. It is a finite energy-barrier result for that state and move family; it says nothing about global n=79 nonexistence. Full artifact: `data/trades-barrier-audit.json`.

The threshold-13 pilot resumed those six state records, reopened all their neighborhoods because the threshold increased, and ran a 28-second bound. It stopped **incomplete** after 28.000046 measured seconds with 31 discovered states: one score 11, five score 12 and 25 score 13. Sixteen threshold-13 neighborhoods were completed (the report's 22 cumulative completions also include the prior six threshold-12 scans). Fifteen states remain in the frontier, including an active score-13 state whose next pair offset is 10,303 of 12,403. Best score 11 and incumbent size 156 are unchanged. Artifact: `data/trades-barrier13-pilot.json`.

The raised phase began with six known states and discovered 25 more while exhausting 16 neighborhoods. Thirteen newly discovered states are direct score-13 neighbors of the source. The other 15 completed scans added 12 more states, suggesting that a modest exact continuation is better supported than another blind temperature sweep. This is scheduling evidence, not a prediction of total component size.

## Stable resumable worker contract

The worker CLI is now frozen for the shepherd's process queue:

```sh
python3 research/rectangle_barrier.py --resume data/trades-barrier13-pilot.json --threshold 13 --seconds 900 --max-states 1500 --output data/trades-barrier13-long.json
```

`--seconds`, `--threshold`, `--max-states`, `--output`, `--source`, `--baseline`, `--resume` and `--checkpoint-every` are supported. Checkpoints are atomically replaced after every completed neighborhood by default, on time/state cutoffs and immediately after improvements. They retain the pending frontier and each node's exact next pair offset, so timeouts do not discard a partly scanned neighborhood. Nodes store source-relative parent moves; on resume their full point sets are reconstructed and move legality, hash, score, depth, offset range and frontier consistency are checked. Increasing the threshold reopens all known neighborhoods. Decreasing it is rejected. Source geometry and every reported better state receive both independent exact audits.

Resume is intended for **trusted, unmodified local checkpoints**. It checks reconstructed states but does not independently replay previous enumeration or completion records. Every new report explicitly states this trust model and its completeness basis. A same-threshold continuation relies on those trusted prior scan records; a threshold increase reopens all known scans. Corrupted state geometry, scores, hashes or inconsistent frontier/offset structure is rejected, but the checkpoint is not an adversarially authenticated proof object. The independent reviewer requested this distinction and it is now explicit in the module, reports and tests.

Six barrier tests pass: full threshold components are compared with an independent all-state graph enumeration for n=2,3,4; better-state paths are replayed against determinant scores; time and state cutoffs remain incomplete; a mocked mid-neighborhood timeout resumes with exactly the same total pair count as a fresh run; capped runs and threshold raises resume correctly; corrupted scores are rejected; and a subprocess CLI test writes and resumes a checkpoint. The source code hash at queue handoff is `81a7cda9dae241bec65c9c9d50bfea2f3feb53b014628ba1f5f1fc85236aa46f`.

The shepherd was given the resumable threshold-13 command, observed branching and the frozen worker contract immediately. No additional unassigned numerical work was run, and the stable trade engine was left unchanged while the queue is prepared.
