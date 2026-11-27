# Research Lead decision log

## 2026-11-26 — Pilot launch

- User authorized the autonomous 24-hour pilot discussed in the chat.
- Dispatched three separate agents: Literature Researcher, Research Software Engineer, Mathematician. The lead coordinates and integrates; no independent Mathematical Reviewer has yet been dispatched.
- Literature reported that the primary database was updated 2026-10-28 and includes the n=78 full construction; older benchmark pages can be stale. Do not select a target from an old benchmark list.
- Tentative first target: n=79. A published n=78 construction embeds with 156 points; 158 is the row-count ceiling. Whether 157 would be new is still under investigation.
- First deliverable is a trustworthy baseline and search/verification pipeline, not a discovery claim.

## 2026-11-26 — First shepherd review

- Selected n=79 as the first finite exploratory target: verified baseline 156, elementary ceiling 158. Global near-miss record completeness is not established; even a 157-point witness needs a fresh novelty check.
- Both exact checkers accepted the source and embedded baseline. Software tests and small-instance experiments passed. Four five-second deletion/repair runs retained 156.
- Literature Researcher changed role to Mathematical Reviewer and independently checked the Mathematician's scoped lemmas. The same agent was reused; this is not a claim of five simultaneous agents.
- The reviewer exhausted 624 one-hole boundary extensions, none valid. Prune that family for this seed. Retain other repairs.
- Quarter-turn symmetry cannot produce 158 at this odd order; prune that precise symmetry/target combination, retaining half-turn and asymmetric approaches.
- All 24,340 empty cells across four translations were audited. The minimum number of necessary old deletions for even one new point is two. Stop spending time on zero/one-deletion repair; two/three-deletion budgets remain possible.
- Dispatched a blocker-guided exact repair audit for up to three deletions. Enumerate deletions that hit blocking pairs, rather than spending the next budget on unguided random deletions. This is a new branch prompted by evidence, not a renamed random seed.
- Hourly continuation was created and its stored configuration independently checked: active, every hour, this research chat. It is conditional on host/scheduler/account availability. Deadline remains unchanged.
- Local Python environment has no SciPy, OR-Tools, Z3, or PySAT, but does have a C++ compiler. An exact-constraint branch must first choose a dependency or implement a small correctness benchmark; do not claim a solver ran.

## 2026-11-26 — Evidence-driven branch and second review

- The blocker-guided repair branch completed, rather than timing out. It generated all 1,456 relevant deletion sets per translated seed: 8 of size two and 1,448 of size three. Across four translations: 5,824 sets. No repair increases cardinality to 157 or 158.
- Its completeness argument includes readdition of removed old points. Every improvement needs at least one genuinely new point; the deletion set must hit all disjoint blockers for that point. Enumerating endpoint choices and optional extra deletions covers all relevant sets of size at most three. Exact geometry checks cover the additions and retained seed.
- The Mathematician changed role to independent Mathematical Reviewer of the engineer's implementation. The reviewer approved the scoped completeness argument and cross-checked tiny cases against direct enumeration. The engineer added deadline checks requested in review; timeouts remain explicitly incomplete.
- **Prune the full at-most-three-deletion improvement neighborhood for these seeds.** Do not keep repeating the default random deletion budget three in later rounds. This negative result is not claimed novel or global.
- Next allocation: prototype row/column alternating-cycle trades, investigate larger guided neighborhoods under the time cap, and benchmark an exact line-constraint formulation on tiny grids before expanding. Keep a separate exploration allocation for the other starting approaches.
- At launch, 32 Python tests and browser checks at five viewport sizes passed. GitHub CI and the initial Pages deployment passed. Public page returned HTTP 200. The visualization remains a saved evidence snapshot with no discovery claim.

## 2026-11-26 — Human correction: keep useful work moving

- The human objected to waiting idle between hourly sessions. That was a scheduling error by the Research Lead: hourly was intended as review cadence, not an idle gate. Immediately reassigned all three workers to new mechanisms: nonuniform grid insertion, degree-preserving trades, and exact line constraints/SAT.
- Added a distinct five-minute worker dispatcher alongside the hourly synthesis heartbeat. A bounded numerical experiment pool runs between model turns, with conservative six-hour aggregate worker-time accounting, at most three numerical children, memory checks, local checkpoints and receipts. It is a program, not an additional AI researcher.
- Supervisor tests exposed the desktop sandbox's restriction on `ps`; host-permitted process tests passed. The guard fails closed rather than silently dropping memory checks. Independent review requested deadline/accounting/launch-recovery fixes; these were implemented and tested before expanding the queue.
- Nonuniform insertion scan classified all 6,241 cuts using 1,561 checked rotational representatives. Only four corner embeddings are valid without repairs. The reviewed four-deletion audit excludes improvements for all 6,237 nonuniform embeddings.
- The numerical pool then completed the four-deletion corner audit: 130,290 relevant deletion sets at each of four corners, no improvement. Combining the two families excludes all 6,241 embeddings of this one published seed followed by at most four transformed-seed deletions. No global or novelty claim follows. Later corner audits should use the checked source symmetry and compute a single representative.
- Five-deletion follow-up closed 6,229 nonuniform embeddings, retaining two partial orbit classes. Both initially examined 20,000 of 596,904 exact-five deletion sets, with explicit offsets and source-order hashes. The new stream worker preserves gapless histories and refuses stale/mismatched resume chains.
- Trade experiments preserve a separate valid 156-point incumbent. The best 158-point degree-two search state has 11 forbidden triples and is invalid. Pair/triple and broader uncolored rectangle moves did not improve it in the recorded bounded runs.
- A complete uncolored-neighborhood audit found all 12,089 legal two-edge switches increase the score; an independent C++ arithmetic check matched the histogram. Exhausting the score-at-most-12 component found six states and no escape. This is a scoped finite barrier, not impossibility of a valid 158-point arrangement. A higher-threshold search is in progress.
- The exact line formulation at order 79 has 6,241 variables and 1,644,284 maximal-line constraints. Instead of materializing all 41,820,272 triple clauses, the active SAT branch adds verified geometric cuts lazily. Optional free solver versions are pinned in an isolated environment; no paid compute or API keys were used.
- Glucose3 and MiniSat22 each reached 1.5 million valid learned cuts without a witness or UNSAT. Cut-limit termination is incomplete. Persistent, validated geometry checkpoints allow the numerical queue to continue these experiments without discarding the learned cuts.
- Best valid point count remains 156. Keep the graph's invalid-state conflict score distinct from a valid point count. No newly discovered lower bound, global impossibility proof, or new-record claim is made.

## 2026-11-26 — Persistent frontier handoff and 157-point SAT branch

- A longer SAT continuation learned a further 5,252,564 geometric cuts after loading 1,500,000. It was gracefully interrupted to hand over the reviewed supervisor and diversify the numerical lanes; the checkpoint was flushed and retained. Its nonzero process exit is an interruption, not a mathematical failure or UNSAT. The process receipt accounts for its consumed time.
- The numerical queue resumed both large five-deletion embedding classes with exclusive durable tips and immutable offset records. Checkpoints preserve exact source ordering, history links, and completed prefixes. Final claims require a gapless chain, trusted local scan evidence, and inspection of witness records.
- The higher rectangle barrier search exhausted the score-at-most-13 component: 36 distinct states, no lower score than 11, no pending frontier. This strengthens the local barrier for that starting state and move family; it still says nothing about global order-79 existence. Its resumed computation relies on the disclosed trusted checkpoint semantics.
- Noticed the SAT branch was targeting only 158, while 157 would also improve our witnessed baseline. Assigned an efficient separate target-157 model: one row deficit and one column deficit, each exactly-one, with every real row/column count plus its indicator equal to two.
- Mathematician independently proved the encoding equivalent and supplied a valid small example where the deficit row/column intersection is already occupied, rejecting an overrestrictive ghost-cell shortcut. The Research Software Engineer implemented target-aware counts and validation. Seven solver tests, including exhaustive small real-variable assignments for both target cardinalities, passed and were independently rerun. Literature Researcher also inspected the implementation and tests.
- Released all three numerical lanes after that review: the two embedding streams plus a target-157 SAT continuation, reusing only validated geometry cuts. No fourth numerical benchmark should run concurrently. Formal review remains hourly, with five-minute worker dispatch and continuous bounded numerical work between reviews.

- Publication checks: 81 tests passed including all optional SAT tests, and browser checks passed at five viewport sizes. Added relocated-checkout reference resolution without rewriting immutable result bytes; every linked record remains hash checked. Published tips are snapshots of active streams, not live telemetry.
