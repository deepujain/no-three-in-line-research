# Literature and finite baseline, checked 2026-11-26

Let D(n) denote the maximum number of points of {0,…,n−1}² with no three collinear. Every row contains at most two, so D(n) ≤ 2n (for n≥2). A 2n witness immediately proves that finite value optimal. It does not establish that 2n is achievable for every n, arbitrarily large n, or any asymptotic density. The latter questions are separate research problems.

## Most current primary construction sources found

- [Flammenkamp's construction database and history](https://wwwhomes.uni-bielefeld.de/achim/no3in/readme.html), accessed 2026-11-26, page last dated 2026-11-22. Its history attributes the 78×78 quarter-turn witness to Thomas Prellberg on 2026-10-28, and the 76×76 witness to Marijn Heule on 2026-08-10. It records Heule's odd-grid 71 and 73 successes on 2026-08-17 and 2026-08-19.
- [Database table](https://wwwhomes.uni-bielefeld.de/achim/no3in/table.html), accessed 2026-11-26, updated 2026-10-28, displays at least one 2n configuration for each 2≤n≤74 and n=76,78, while its n=75 and n=77 rows are blank. This is a database observation, not a proof of global absence or exhaustive search. The table stops at 78.
- The actual [78-grid encoded witness](https://wwwhomes.uni-bielefeld.de/~achim/no3in/download/configurations/n78_rot4.few) and [76-grid witness file](https://wwwhomes.uni-bielefeld.de/~achim/no3in/download/configurations/n76_rot4.few) are from the primary archive, accessed 2026-11-26. `data/published-n78.json` reproduces the 78 witness, alphabet, source, hash, and decoding. The page says that the first symbol encodes symmetry and subsequent pairs give columns in successive rows. An independent exhaustive integer cross-product check of all C(156,3)=620,620 triples found no collinear triple, and all coordinates are distinct and within range. Every row and column has exactly two points. The source pages reviewed did not state a data license; permission to redistribute is not established.
- [Queen Mary University of London, 20 November 2026](https://www.seresearch.qmul.ac.uk/ccs/news/5792/a-120-year-old-puzzle-a-new-world-record-and-a-student-project/), accessed 2026-11-26, independently reports the 156-point 78-grid October record and notes the unresolved general problem. 78 is therefore already an optimal finite value, not a fresh 2n target.

## Candidate finite targets

| n | rigorous available lower bound | upper bound | status and rationale |
|---|---:|---:|---|
| 75 | 148 | 150 | Delete an edge row and column from a 152-point 76 witness; at most four points removed. Table has no full witness. |
| 76 | 152 | 152 | Primary database supplies a full witness. |
| 77 | 152 | 154 | Embed 76 witness, or crop an edge row and column from 78 witness. Table has no full witness. |
| 78 | 156 | 156 | Verified published 78 witness. |
| 79 | 156 | 158 | Embed 78 witness. 157 improves this verified baseline; 158 proves finite optimality and exceeds the largest full grid recorded in the cited database. |
| 80 | 156 | 160 | Embed 78 witness. 160 proves finite optimality and would exceed the database's largest full grid. |

These are valid *available* lower bounds, not certified best-known near-miss records: database scope does not establish sub-2n records, and later or unindexed work may exist. A search for published 157-point n=79 near misses found no attributable explicit witness; that search cannot prove no such result exists. Recheck publications and construction archives before any novelty or priority claim. A 157 witness establishes only D(79)≥157, not optimality. A verified 158 witness establishes D(79)=158 independently of novelty. The 75 and 77 full configurations are plausible open targets relative to the cited table, not proven globally unsolved.

We checked the published n=78 seed translated at all four offsets into 79 and all nine offsets into 80: in each case no additional point can be inserted while retaining the full seed. This diagnostic excludes only direct single-point extension of that seed; it does not rule out a different configuration or repair after deletions. An independently reported [October 30 experiment](https://thegreystrand.com/office/) examined 77 crops/repairs of this seed and reported 152 as its best valid arrangement, with no 154 found in a limited search. Its search failure is not an impossibility proof; we did not audit its code or underlying report.

## Relevant research and scope

- [Prellberg, *Constraint Satisfaction Programming for the No-three-in-line Problem*, arXiv:2602.07751](https://arxiv.org/abs/2602.07751), accessed 2026-11-26, exhibits full configurations for all n≤60 using constraint programming. This paper's original frontier of 61 is superseded by later database records. It gives concrete solver and symmetry approaches; the archived 78 solution supplies a more recent starting point.
- [Prellberg, *No-three-in-line sets on the checkerboard grid*, arXiv:2605.09215v2](https://arxiv.org/abs/2605.09215), accessed 2026-11-26, concerns the monochromatic restriction, with an upper bound about 1.5768n+O(1) for that variant. It is not an unrestricted-grid upper bound.
- [Guy and Kelly, *The no-three-in-line problem* (1968)](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/B126DA7E4957722BAC70AC7B7F6E1FA2/S0008439500056770a.pdf/the-no-three-in-line-problem.pdf), accessed 2026-11-26, gives a probabilistic argument for a conjecture, not a proof of a cutoff. The primary database cites Hall–Jackson–Sudbery–Wild (1975) for the classical (3/2−ε)n asymptotic lower bound. Neither a single finite record nor a heuristic upper-bound estimate resolves the general asymptotic problem.
- [Zerothesis challenge brief](https://zerothesis.com/challenges/no-three-in-line?tab=brief), accessed 2026-11-26, explicitly dates its finite comparisons to an August 31 database cut. Its 78/79/80 baselines based on 76 are outdated after the October 78 witness; treat its near-miss figures as historical, not current records. The same caution applies to listings that stop at n≤70.

## Assignment metadata

Literature Researcher subagent, inherited parent model and reasoning settings. The runtime identifies the assistant as GPT-6/Codex but does not expose an exact model identifier or reasoning-effort setting to this agent; neither is inferred. Research was read-only externally; local data and notes were written in this workspace. Access dates above are the local date 2026-11-26.

Reproduce the extension diagnostic from the workspace root with `python3 research/check_seed_extensions.py`. All four n=79 offsets and all nine n=80 offsets print `addable=0 cells=[]`; it tests the complete translated seed and all remaining cells using exact integer cross products. This check is independent of a general solver and does not cover replacements.
