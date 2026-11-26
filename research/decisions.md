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
