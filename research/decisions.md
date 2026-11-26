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
