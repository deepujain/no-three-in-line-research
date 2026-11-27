# Mirror-pair admissibility shortcut

This is an independent experimental variant of the reviewed diagonal DFS. The original DFS, resource guard and CLI adapter remain unchanged. Only the MRV candidate test changes: at each node construct the set of coordinate sums of selected points, then evaluate each candidate pair with occupancy, axis capacity, existing secant counts, and membership in that set. Actual DFS branches still use the original exact transactional `push` and `pop`; row selection, candidate ordering, slice enumeration and witness validation are unchanged. Set membership has expected constant time in Python, not a worst-case constant-time guarantee; building the set takes time proportional to the selected points once per node.

For `a=(i,j)` and `b=(j,i)` with `i<j`, the two new points occupy different rows and different columns, so their capacity checks are independent. Occupancy checks exclude duplicate cells. Nonzero `blocked[a]` or `blocked[b]` means an old-old-new triple exists. The only remaining possible new collinear triple contains both `a`, `b` and one old point: their common line is exactly `x+y=i+j`, so the coordinate-sum membership test rejects exactly that case. Two new points cannot alone form a triple. Thus, provided the secant invariant holds and the sum set represents the current state, the predicate accepts exactly when sequential transactional insertion accepts. Rebuilding the sum set at each node avoids staleness after mutations.

`python3 -m unittest tests.test_diagonal_secant_dfs_fast -v` passed. For each deficit at n=3,4,5, the test traverses every reachable valid partial state formed by the diagonal singletons and reflection pairs, and compares the shortcut against a real original-state push/pop for every pair, including rejected cases and full rollback. Complete DFS searches over every deficit/singleton slice at n=3,4,5 have identical ordered witness visits, slice status/counts and node counts to the original; unique witnesses also match independent exhaustive enumeration. Both implementations validate each witness with the existing slope and determinant checkers. These are correctness tests, not performance measurements. No n=79 run, benchmark, guard integration or large computation was performed. Independent review is required before any guarded use.

Frozen SHA-256:

- Original DFS: `6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7`
- Variant: `38ec5044a8db85f046be24feb97c51adb6a95825afccac375d078195a57022a3`
- Variant tests: `ba4942ab4d5517c6adf6ae3a6e7651348b74106609855fadf098cccc41d0149d`
