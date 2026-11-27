# Exact line-capacity baseline

Role: Research Software Engineer (transitioned from independent Mathematical Reviewer). Assigned model `gpt-6.1-terra`, reasoning high per parent. Date 2026-11-26. This is a complete model specification and baseline, not a completed search or an infeasibility proof.

## Model

For each cell (x,y) in G_n use a Boolean z_xy. For every maximal straight lattice line L containing at least three grid cells, impose sum(z_xy for (x,y) in L) ≤ 2. Require sum(z_xy)=158 at n=79. Equivalently, for that target impose exactly two points in every row and column; this already forces the total. Line capacities alone describe valid sets of any size, so a solver must also impose the target or maximize cardinality. At n=1 or 2, lines of length less than three are not included, so any optional row/column equality must be specified explicitly; the upper-bound target is impossible at n=1.

The implementation `src/line_model.py` enumerates primitive directions (dx,dy) with dx>0 or (dx,dy)=(0,1), gcd(|dx|,|dy|)=1, and |dx|,|dy|≤floor((n−1)/2), retaining negative dy. It starts at grid cells whose predecessor is outside and second successor is inside, then walks to the boundary. This yields each maximal line of at least three points once. Every collinear triple has a primitive lattice direction and lies on exactly one such maximal line, so these constraints are equivalent to forbidding all collinear triples. Completeness here concerns mathematical representation, not solver availability or proof that a large instance is tractable.

## Validation and measurements

`python3 -m unittest discover -s tests -p test_line_model.py -v` passed. For n=1,2,3,4, the test checks *every* subset of grid cells against the separately written brute-force integer-determinant checker in `src/verify.py`; it also checks uniqueness, maximality, negative slopes and counted versus enumerated lines through n=8. For n=79 the full stream independently sums to the same line and incidence counts as the analytic direction formula. The stream checks counts, not the uniqueness of all n=79 lines; the primitive-start proof establishes uniqueness generally and the tests exercise it on small grids.

`data/line-model-counts.json` contains analytic counts for n=1 through 79. At n=79:

- 6,241 cell variables and 1,896 primitive directions.
- 1,644,284 maximal-line constraints; 6,253,052 variable appearances.
- Of the constraints, 1,068,748 have exactly three cells. Full length distribution appears in `data/line-model-n79-histogram.json`.
- Expanding each line into one clause for each triple produces 41,820,272 ternary clauses; no such expansion has been generated. A compact sequential cardinality counter or a solver's native linear/cardinality constraints has O(k) size per length-k line, subject to backend translation and overhead. Avoid assuming that a native API actually stores constraints compactly without measuring the backend.
- Illustrative packed 32-bit incidence and line-offset arrays occupy 25,012,208 and 6,577,140 bytes respectively (about 30.1 MiB combined). These are theoretical storage for the incidence structure alone, not a solver's total memory: parsing, variable maps, presolve, clauses, indexes, and runtime may consume much more. Large Python list-of-integers representations would be substantially larger.

The CLI `python3 src/line_model.py 79` prints counts without exporting constraints. `--export-jsonl PATH` streams one cardinality record per line, but first computes the count and refuses if it exceeds `--max-lines` (default 100,000). Set a deliberate cap only after assessing space; JSON text is not included in the packed estimate. No large export or CNF has been generated. Source files are regenerated from deterministic enumeration rather than needing a huge checked-in model.

## Solver next step

System Python exposes none of scipy, numpy, ortools, z3, pysat or highspy. The bundled workspace Python has numpy but not the other five. No candidate solver is currently verified available, installed, or run. A practical next experiment is to use an available open-source CP-SAT or MILP backend supporting Boolean linear constraints (for example OR-Tools CP-SAT, if separately made available), or a SAT backend with a validated linear-size at-most-two encoding. First cross-check the complete model and any encoder on all small instances; measure model build time, peak memory, and tiny-instance outcomes before attempting n=79. Include exact row/column equalities for the full target and validate any returned witness independently with both exact geometric checkers. A timeout is not an infeasibility proof; an unsatisfiable claim needs a correctly encoded complete model and independently checkable proof or exhaustive computation. Solver dependency installation and computational resources remain unverified.
