# Singleton migration by one-cell relocation: bounded mathematical design

Status: DESIGN ONLY. No implementation, valid-state geometry, fixture search, actual-state access, optimizer, experiment allocation or continuation of the curtailed family was performed or authorized by this document. This is a conditional next-neighborhood analysis if an exhaustive same-load one-row diagnostic reports no gain. The saved n5 diagnostic is not evaluated or used as a migration fixture here.

## Legal move and exact support

Let P be distinct cells in an n by n integer grid, n at least 2, with N=2n−1 points. Exactly one row r has one point a; every other row has two. Write U(P) for the number of unordered collinear triples.

Choose a current point p=(x,s) with s different from r and an empty cell q=(z,r) in the singleton row. Replace p by q:

    P' = (P without p) union {q}.

The source row s now has one point, row r has two and every other row is unchanged. The number of points stays 2n−1, all coordinates stay in-grid, distinctness is preserved and all row loads remain at most two. The singleton has moved from r to s. The move changes two cells in two rows. Its scoring dependencies involve the entire fixed complement, even though its modification support is only those two rows.

This family contains exactly 2(n−1)^2 legal candidates before pruning: 2(n−1) removable points times n−1 empty singleton-row cells. It is distinct from any neighborhood that requires each row's load to stay unchanged. It keeps the old singleton point and one of the two source-row points in place; it is a subset of full reoptimization of the two rows with their loads swapped.

## Exact objective

For a removable point p and empty singleton-row cell q, define:

    d(p) = number of old conflicting triples containing p;
    c(q) = number of unordered pairs {u,v} in P collinear with q;
    h(p,q) = number of points t in P without p collinear with p and q.

Then the exact new score is

    U(P') = U(P) − d(p) + c(q) − h(p,q).

Proof: deleting p removes exactly its d(p) old conflicts. Every new conflict then contains q and two retained old points. Of the c(q) old pairs, exactly h(p,q) contain the deleted p, one for each other endpoint t. Removing those pairs leaves precisely the new conflicts. There is only one inserted point, so no additional multiple-insertion interaction term exists. In particular, c(q)−h(p,q) is a nonnegative integer.

The strict gain condition is

    d(p) + h(p,q) > c(q).

Dropping h is incorrect: it counts candidate triples that still include the removed cell. Strict gain requires d(p)>0, because otherwise no old conflict disappears and the number of new conflicts is nonnegative. Therefore removing only conflict-bearing points is a complete pruning rule for strict moves in this family.

For connection to the preceding singleton one-row test, pairs involving the old singleton a cannot be collinear with q: a and q determine row r, which contains no other old point. Thus c(q) is also the full-complement unary of q with row r removed, and d(a) is the current singleton unary. A failed singleton same-load test implies c(q)>=d(a) for every empty q. Migration instead compares c(q) with d(p)+h(p,q), which is a different threshold. The same-load certificate alone supplies no migration certificate. This observation does not assert that any particular state has a migration gain, or provide a geometrically realized separating example.

## Current-conflict witness and block limits

A strict migration removes an old conflict containing p. Since each old row has at most two points, that conflict occupies three distinct rows, including source row s. It gives a current K-positive triple containing s. Its row triple need not contain singleton row r. Consequently, restricting to K-positive triples that already contain both changed rows is unjustified and could exclude a strict migration.

If a later implementation insists on a block containing both the old-conflict witness and the new destination, their row union has at most four rows; it has three when the witness already includes r. This is a support bound, not a four-row necessity claim, a barrier proof, or permission to implement a four-row optimizer. The two-cell move needs no block optimizer. Existing current/best-inclusive domains for same-load one-row replacements need not contain the insertion q, and an assignment rule fixing the singleton's row would forbid the migration even if all columns were available. The previous same-load embedding theorem therefore does not authorize this move automatically.

## Minimal bounded exact policy

A possible later reviewed policy is one complete read-only relocation sweep on one independently bound state. It makes no mutation, restart or follow-up move during that sweep:

1. Validate the fixed input identity, strict coordinates, distinctness and row-load pattern before geometry. Fix canonical point order and ascending empty destination columns.
2. Count the baseline and d(p) in one pass over unordered old triples. Each collinear triple increments U and d at its three endpoints. If U is zero, return that terminal status without a destination sweep.
3. For each empty q in ascending column order, initialize scalar c and one endpoint-count array h to zero. For every unordered pair {u,v} in P, test collinearity with q once. On success increment c and the h entries at both u and v. Each endpoint entry is then exactly h(p,q).
4. For each removable p with d(p)>0, compute the exact score from the formula. Retain only the best strict candidate, with a declared tie key `(score, source_row, removed_column, inserted_column)`. This key is deterministic; it is not claimed to be lexical order of the complete final point set.
5. Report either that single proposed move or complete absence of a strict move in this precise relocation family. Stop. Any application, follow-up same-load pass, repeated migration or broader neighborhood requires separate authorization.

The endpoint construction follows because every successful pair containing p has exactly one other endpoint t. Useful accounting identities are sum_p d(p)=3U and, for each q, sum_p h(p,q)=2c(q). The old singleton's h entry is zero. These are consistency checks, not independent geometric oracles.

This policy requires at most

    C(2n−1,3) + (n−1) C(2n−1,2)

determinant tests, and at most 2(n−1)^2 scalar candidate score calculations. Each determinant must be charged before arithmetic. A later specification must freeze n, the input digest and the resulting operation ceiling before execution, with any independent oracle work budgeted separately. No time or RSS claim follows from this count.

Working storage beyond the original state is one d array, one reusable h array, scalar counters and one best candidate. No full list of candidate states is needed. A stopped or truncated sweep cannot certify no gain. The zero-baseline terminal case and omission of d=0 removals are justified exact early pruning; adaptive destination sampling is not part of this exhaustive policy.

## Interpretation and later review requirements

A strict result would be a valid row-load migration and an exact reduction in raw conflicts, not a no-three-in-line construction unless the resulting full score were independently zero. A completed negative result would exclude only these one-cell relocations. It would not exclude replacing more cells in the two rows, choosing different columns for both retained points, changing multiple rows, or other mechanisms.

Before any implementation or tiny gate, a separate SOURCE/TINY specification would need a predetermined permitted input, exact source/fixture identities, independent raw-score oracle comparisons, complete count/shape/tie checks, rejection-before-geometry tests, synthetic quota boundaries, immutable success/failure evidence and an owned resource gate. This design does not select another fixture or allocate a run. It provides no claim about the actual64 state, no reason to resume the old prefix, and no guarantee that a migration gain exists after a same-load local minimum.
