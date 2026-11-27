# Independent mirror-pair shortcut review

Reviewer: Mathematical Reviewer, `gpt-6-astra`, high reasoning, 2026-11-27.
The separate fast DFS core is approved at the hashes below. Guard integration,
source binding and durable witness publication require their own review before
guarded large-grid use. No n79 search, construction or performance benchmark
was performed by this reviewer.

| Artifact | SHA-256 |
| --- | --- |
| `research/diagonal_secant_dfs_fast.py` | `38ec5044a8db85f046be24feb97c51adb6a95825afccac375d078195a57022a3` |
| `tests/test_diagonal_secant_dfs_fast.py` | `ba4942ab4d5517c6adf6ae3a6e7651348b74106609855fadf098cccc41d0149d` |
| Unchanged original core | `6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7` |

For a valid old state and a candidate mirror pair a=(i,j), b=(j,i), i<j,
the two points occupy distinct rows and distinct columns. Their capacity
conditions are therefore independent. Occupancy excludes repeated cells,
and the two existing secant-counter entries reject exactly all triples
containing two old points and either new point. The only other possible
new triple contains one old point and both a,b. Their common line is exactly
x+y=i+j, so membership of i+j in the old coordinate-sum set rejects exactly
that case. No other kind of new triple is possible. Thus this predicate is
equivalent to sequential transactional insertion, under the original exact
secant invariant and the documented distinct mirror-pair precondition.

The actual search constructs only such mirror pairs. It rebuilds the sum set
once at each visited state, and candidate tests do not mutate that state.
Only actual DFS branches call the unchanged transactional push/pop. I compared
the complete source diff: line traversal, SecantState, row/column targets,
MRV tie breaking, candidate order, declared slice enumeration, branch rollback,
node/deadline checks and dual-verifier leaf handling are unchanged. The other
change is the certificate method label. Since the viable lists are identical,
uncapped node and ordered witness traversals remain identical. A fixed wall
budget can of course end at a different point when execution costs change.

Both author tests independently passed in 0.231 seconds. They compare the
predicate against real original push/pop at all enumerated valid partial
states for n3/4/5, including rollback, and compare complete ordered witness
visits, slice results and node counts against the original core. Unique tiny
witness sets also agree with the independent exhaustive reference.

I additionally enumerated every subset of the n3 grid for each deficit,
retaining only those accepted by direct row/column counts and integer
determinants for every triple. Across 335 such arbitrary valid partial states,
all 1,005 candidate mirror-pair predictions agreed with direct determinant
and capacity checking of the combined point set. These states need not
already possess mirror symmetry, so this independently exercises the local
predicate beyond the actual DFS's invariant states.

The sum-set construction costs O(number of old points) per node. Python set
membership is expected constant time, not a worst-case bound. No measured
n79 speedup or RSS claim follows from these correctness tests. The standalone
core CLI still has the original cooperative-limit and non-atomic file-writing
limitations; this core approval does not promote it to a guarded execution
or artifact wrapper. Exhaustion remains scoped to declared reflection slices.
