# Mathematical baseline and research directions

Prepared 2026-11-26 by the Mathematician agent, model `gpt-6-astra`, reasoning `high`.
These are derivations and proposed experiments, not novelty claims. A proof written
here is not independently reviewed merely because its author also ran tests.
The literature record and witness provenance belong to the separate literature
audit. In particular, do not infer that order 75 remains open.

## Problem and exact elementary restrictions

Let G_n = {0,...,n−1}². A witness is a set S contained in G_n such that every
three distinct points have nonzero integer determinant

    D(A,B,C) = (Bx−Ax)(Cy−Ay) − (By−Ay)(Cx−Ax).

Every row has at most two points, so |S| ≤ 2n; likewise for columns. Equality
requires exactly two points in **every** row and column. For n=1 the sharper
bound |S| ≤ n² gives one point. A valid partial witness is a lower bound only.

At equality, represent each selected (x,y) as an edge between column x and row y.
The resulting simple bipartite graph has degree two at every vertex. Its
components are even cycles, so alternate coloring decomposes it into two
disjoint perfect matchings. Thus every extremal witness is the union of two
permutations with no coincident entry. This is an exact representation, not an
assumption that discards solutions. It does not enforce non-axis collinearity.

### Symmetry restrictions

The quarter turn R(x,y)=(n−1−y,x) has orbits of size four, except that for odd n
the center has orbit size one. There are no size-two orbits: R² fixes only the
center. Consequently any quarter-turn invariant set has size 0 or 1 modulo 4.
For odd n, 2n is 2 modulo 4, so no size-2n witness can have this symmetry.
For n=79 this excludes 158 points under quarter-turn invariance outright.
Full D4 invariance includes quarter turns and is excluded as well. Quarter-turn
invariance itself does **not** imply reflection invariance.
Patterns described as near-quarter-turn or `rct4` in external catalogs need
their own definition; this argument applies only to exact invariance under R.

Half-turn invariance is different: noncentral orbits have size two, so it is not
excluded at odd n. In an even-size half-turn invariant set at odd n the center
must be absent, because including its singleton orbit would make cardinality
odd. Reflection symmetry also requires its own orbit count; do not transfer
the quarter-turn obstruction to all symmetry classes.

Using a dihedral symmetry to choose one representative of equivalent solutions
is generally legitimate. Requiring the solution itself to be fixed by that
symmetry restricts the solution family. Exhausting the latter is not a proof
about arbitrary solutions.

## Classical algebraic baselines

All points below are least nonnegative integer representatives of field
coordinates. Their integer geometry must be distinguished from field geometry.

### Quadratic graph: p points in a p-square

For prime p and a≠0 in F_p, set

    P = {(x, ax²+bx+c mod p): x=0,...,p−1}.

Distinct points have distinct x. For any three distinct x values, the
determinant is, up to sign, a(x₂−x₁)(x₃−x₁)(x₃−x₂) modulo p, hence nonzero.
If the corresponding real points were collinear, their integer determinant
would be zero and therefore zero modulo p, a contradiction. Thus P is valid.
This is the classical finite-field parabola construction; it is not new.

The same points embed unchanged into an n-square for n≥p. This gives p points,
not 2p. No point count doubles merely by changing coordinate conventions.

### Anisotropic conic: p+1 points in a p-square

For odd prime p choose a quadratic nonresidue d. The affine conic

    C = {(x,y) in F_p²: x²−d y²=1}

has exactly p+1 points. One is (−1,0). All others are obtained uniquely, for
t in F_p, by intersecting y=t(x+1) with the conic:

    x=(1+d t²)/(1−d t²),  y=2t/(1−d t²).

The denominator is nonzero: 1=d t² would make d a square. The resulting point
cannot be (−1,0), since x+1=2/(1−d t²)≠0; conversely its parameter is uniquely
t=y/(x+1). This proves the count without relying on numerical enumeration.

Every affine line has at most two conic points. Parameterize a line as
(u,v)+s(r,q) with (r,q)≠(0,0). Substitution gives a quadratic in s with leading
coefficient r²−d q²≠0, again by the nonsquare property. Therefore it has at most
two roots. Three distinct integer representatives collinear over the reals
would reduce to three distinct collinear field points, a contradiction. Their
residues remain distinct because all coordinates lie in {0,...,p−1}.

For p=79 this baseline gives 80 points. It certifies a useful test fixture and
lower bound, not progress to the extremal 158-point target. The current module
uses the smallest positive nonsquare d unless one is explicitly supplied.

### Vertical lift: 2p points in a 2p-square

For the quadratic graph above take both (x,y) and (x,y+p). This gives 2p points
in a rectangle of width p and height 2p. A vertical line has exactly two.
Any nonvertical collinear triple would have three distinct x coordinates, so
reduction modulo p would contradict the quadratic graph proof. Therefore the
lift is valid, including p=2. Its containing square has order 2p, not p; its
point count is only n when n=2p.

## Counterexamples to tempting shortcuts

1. **Replacing the prime by an arbitrary integer.** For modulus 9, the graph
   y=x² mod 9 contains (0,0),(3,0),(6,0). The field proof uses invertibility of
   nonzero differences; a residue ring with zero divisors does not supply it.
   Prime powers require genuine field coordinates and an additional valid
   integer embedding argument, not simply arithmetic modulo p^k.
2. **Union of shifted parabolas.** For every odd prime p, the union of
   y=x² mod p and y=x²+1 mod p contains (1,1),(p−1,1),(0,1). For p=3 these
   are exactly (0,1),(1,1),(2,1). Even a union of individually valid sets can
   fail immediately on a horizontal line. Other shifts are not all ruled out
   by this particular example; every proposed family needs its own check.
3. **Wrapping a valid Euclidean witness preserves validity.** In the 5-square,
   (0,4),(1,0),(2,1) have determinant 5 and are valid. Translating y by one
   modulo 5 produces (0,0),(1,1),(2,2), which are collinear. Ordinary integer
   translations and invertible real affine maps preserve collinearity when
   points remain in bounds; modular wrapping need not.
4. **Finite-field and Euclidean constraints are interchangeable.** The same
   determinant-5 triple is collinear modulo 5 but not over the reals. Field
   noncollinearity is sufficient for an injective representative embedding,
   but not necessary. A field constraint can exclude useful Euclidean sets.
   For composite moduli, determinant zero and membership in a chosen notion
   of torus line need not coincide; define toroidal lines explicitly before
   using that word in a solver or theorem.
5. **Doubling or reflecting a witness preserves validity.** Cross triples
   between two individually valid subsets remain unchecked. The shifted
   parabola example is already a counterexample to a broad union rule.
6. **Solver failure proves nonexistence.** A timeout, stalled search, positive
   best conflict score, or exhausted restricted neighborhood says only that
   the stated run did not find a witness. Global infeasibility requires a
   complete correct model and an appropriately checked proof or exhaustive
   computation. Floating point optimality reports alone are insufficient.

## Exact one-hole extension lemma

Suppose S has 2n points in an n-square and is embedded unchanged in the
top-left block of an (n+1)-square. Every old row and column is saturated. Any
new point must therefore have both new coordinates, leaving only (n,n).
Thus preserving S and adding two points is impossible.

If exactly one old point (a,b) is removed, and no other old-cell changes are
allowed, a full extension is forced to add

    (a,n), (n,b), (n,n).

Proof: old column a and row b each have one vacancy; every other old row and
column remains full. Besides the removed cell, which would undo the deletion,
the only eligible cells are precisely those three. All three are needed to
increase 2n−1 to 2n+2. Conversely these three fill every row and column to two;
they do not automatically satisfy the remaining line constraints.

`one_point_extensions` enumerates this family. It checks integer domains,
distinctness, and row/column saturation; the independent geometry verifier
must check the source and every candidate. For n=78 there are 156 candidates
per corner embedding, or 624 with all four corners. Those are all candidates
in this explicitly restricted family, not all possible order-79 witnesses.
Other source orientations may be equivalent under whole-square symmetries;
duplicate audits are harmless if their scope is recorded correctly.

## Ten starting approaches

These are distinct mechanisms or restricted families, rather than ten random
seeds. Some search the same exact feasible set using different state spaces;
none is asserted to be a novel research method. The shepherd should record
the actual experiment, parameters, budgets, and result separately. A cheap
rejection below rejects an idea or bounded configuration, not the full problem.

| ID | Mechanism and hypothesis | Cheap first experiment / rejection | What a failure actually means |
|---|---|---|---|
| M1 | **Repair a known optimal witness at its boundary.** A small deleted set can expose enough rows and columns to fit the two new boundary lines. Begin with the forced one-hole family, then allow k deletions and solve only the residual cells. | Verify the source independently; audit all one-hole cases; for each larger deleted set use row/column capacity and bipartite matching before geometry. Reject a patch with insufficient residual matching capacity. | An exhaustive one-hole rejection rules out only that source embedding and repair family. k-hole failure does not exclude unrelated solutions. |
| M2 | **Search the exact two-permutation representation by alternating-cycle trades.** Keep all row/column equations satisfied while changing cycles of the bipartite incidence graph to eliminate non-axis conflicts. | At small n, confirm the move implementation preserves degrees and reaches known witnesses. Measure how often 4-cycle versus longer alternating-cycle moves improve a fixed conflict score. Reject a move set that is trapped by its own invariants. | Failure of one move set or energy landscape does not establish infeasibility; moves can require temporary conflict increases. |
| M3 | **Global binary ILP/SAT/CP model with line cuts.** For each grid cell use a Boolean variable, exactly two per row/column, and at most two on each maximal integer grid line. An exact solver may exploit long-line propagation better than local search. | Build and exhaustively cross-check the full model at n≤5 against a simple enumerator. Compare precomputed maximal-line inequalities with lazy separation. Check the unrestricted model before adding symmetry constraints. | Only a completed exact solve with a trusted/checkable certificate can support infeasibility. Timeouts and bounded lazy-cut runs cannot. |
| M4 | **Variable-cardinality conflict-hypergraph construction.** Grow a valid set by greedy/beam search and repair with bounded ejection chains, allowing point count to fall temporarily. This can cross barriers that a fixed two-permutation state cannot. | Benchmark small n, inspect whether the attainable point count and repair cost improve over algebraic and random baselines, and hash states to detect cycling. Compare candidate neighborhoods under equal operation budgets. | A plateau at 2n−k is a lower-bound witness and a search diagnostic, never an upper bound. |
| M5 | **Orbit search under a viable symmetry subgroup.** Half-turn or selected reflection symmetry may compress the search while still allowing 158 at n79. Treat asymmetric search as a separate control. | First solve orbit-size/cardinality and row/column feasibility exactly. For n79 reject quarter turns and full D4 without search; exclude the center in the half-turn, even-cardinality model. Check whether any orbit itself contains a triple. | Exhaustion applies only to the chosen invariant family. Restricting to half turns can still discard all actual solutions. |
| M6 | **Algebraic templates followed by controlled deformations.** Parameterized quadratic/conic pieces can offer structured low-conflict initial states; Euclidean corrections may escape unnecessarily strong finite-field constraints. | Reproduce the proven baselines, enumerate a small declared parameter family, count actual integer triples, and compare with equal-size random controls. Reject the naïve shifted quadratic union using its explicit horizontal triple. | No theorem follows from the best member of a sampled family. Modular arc validity alone supplies about n points here, not 2n. |
| M7 | **Geometric composition with cross-line compatibility.** Combine valid pieces in strips or blocks and select compatible boundary states. The potential gain is reuse of small exact solutions. | Before full assembly, enumerate all cross triples (two points in one piece, one in another) and check row/column capacity. Determine whether a proposed fixed gap or placement really eliminates them; otherwise reject that composition rule. | Local validity of every piece proves nothing about the union. A failed arrangement is not a no-composition theorem. |
| M8 | **Continuation by nonuniform grid embedding.** Insert rows/columns or stretch selected gaps in smaller known witnesses, then repair the changed geometry. Moving internal gaps explores starts unavailable by simple corner extension. | Enumerate one inserted row/column on small witnesses, explicitly recompute every determinant, then score changed conflicts and residual row/column vacancies. Reject any claim that piecewise stretching automatically preserves validity. | An unchanged affine embedding preserves geometry but has too few points; a nonlinear coordinate embedding needs a new full check. Failure concerns the tested embedding family. |
| M9 | **Strip/frontier dynamic programming.** Process columns in order, recording occupied lines that can forbid later cells and row capacities. Exact state compression might exploit equivalence of future constraints. | Implement only tiny widths first and compare counts with brute force. Prove that states merged by compression have identical legal continuations; measure state growth before attempting large n. | Dropping old line information without a proof makes the method heuristic. State explosion rejects the implementation budget, not the mathematical instance. |
| M10 | **Obstruction and upper-bound certificates.** Derive parity/orbit restrictions or a weighted collection of line inequalities; search for short rational dual certificates that forbid a declared family. This may remove wasted search regions even if it cannot settle n79. | Recover |S|≤2n from row inequalities, recover the quarter-turn contradiction, and rationally check any stronger linear certificate. Compare with known valid small witnesses to catch overconstraints. | A dual bound of 2n merely repeats the elementary ceiling. Bounds for a restricted symmetry class or relaxed auxiliary formulation must retain their exact scope. |

M1 is the cheapest decisive first audit given an already verified order-78
witness. M2 and M3 directly target the full 158-point condition. M4 supplies
partial witnesses and escape paths; M5 has a strict parity precheck. M6–M9
should earn larger budgets through small-instance evidence. M10 can disprove
overconstrained ideas quickly but offers no present general obstruction at 79.

## Reproducibility and acceptance

`src/constructions.py` uses only Python's standard library. Its baseline JSON
certificates use `n` and `points`; provenance files using a different schema
need an explicit conversion before verification. `tests/test_constructions.py`
checks the constructions with both supplied exact geometry implementations,
the conic equation/count, edge cases, the explicit false-construction examples,
and the exhaustive n=2 one-hole classification by independent boundary choices.

A newly found candidate is a success only after checking integer coordinates,
range, uniqueness, exact count, and every collinear triple with independent
exact methods. Save the full coordinate certificate, normalized hash, model
and search parameters, and provenance. A valid 158-point order-79 candidate
would settle existence at that order; whether it is a new record requires the
separate current literature review. Neither a promising score nor an unverified
image is a witness.
