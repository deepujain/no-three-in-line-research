# Independent deadline roundoff correction review

Approved narrow source correction. Reviewed source `research/diagonal_residual_root_preflight.py` SHA-256 `04ff2dadecae1fc72cc21c1a19a7efe90fd46762e07554335b344ad01632abcc` and test `tests/test_diagonal_residual_root_preflight.py` SHA-256 `c4abe464106addc03fbb94f8b2824a9c4996a8d54436424a4f81a4d100da1fd3`.

The validator now compares `started < worker_deadline <= (started + seconds) - 1`, using the same floating-point evaluation order as job generation. The old subtraction could round the reconstructed duration above the limit for an exactly generated deadline. The change adds no epsilon, reserve reduction or cap relaxation; finite timing checks and the existing seconds range remain intact.

The new synthetic regression starts at 6.036 with ten seconds, reproduces the old subtraction result above nine, accepts the exact generated deadline and rejects an extra 0.001 seconds. This review independently reran that test, passing in 0.010 seconds. Root reports all nine focused tests passing in 1.328 seconds. No scanner or host allocation was rerun. Historical actual-host evidence remains bound to the prior source hashes preserved at commit 26fec70; this correction does not retroactively rewrite that evidence.
