# Independent compact preflight integration review

Mathematical Reviewer: `gpt-6-astra`, reasoning `high`; reviewed 2026-11-27.
The frozen integration is approved for a separately scheduled build-only
preflight. The Lead completed the real-host tiny gate and then the scheduled
n79 build; both saved reports were independently inspected below. This
reviewer did not execute an n79 model or authorize solver search.

## Reviewed identities

* Separate preflight `research/near_quarter_compact_preflight.py`:
  `a4d94e8efe9a9fa33ffc4194b829c85d47a975b0dda6073e1139af19758b280a`
* Opt-in dispatcher `src/lazy_sat.py`:
  `6b2a3409ade12ce10b79247b703b1add1f4c8350642033aace375db75096bf18`
* Tests `tests/test_near_quarter_compact_preflight.py`:
  `37b80a3c7b688413663d9f83c87f00ad87d5d256228217e062180711866cc7fe`

The original guard remains
`1405aa420d2828cf268076104266560436707f559733dce3e5f4d4f9fe78be27`;
the original model remains
`b53adcf159cd7d32416e02ae970a339afcb40442107c966ef6393680d479838a`;
the reviewed compact encoder remains
`f2b5840a160d51fc8e5d663cad42f5416286f4b2535cda7ab3cd7c4598b281f1`;
the line generator remains
`d789d1b4924676886a950757fcf98994f221a0ad1ee7ca12874667ecfa034897`.

## Source findings

The separate module imports the exact frozen `guarded_process` function rather
than implementing a different monitor. Input validation caps wall time at
30 seconds and sampled RSS at 256 MiB, with smaller positive finite values
permitted. It retains the fresh child process session, parent-plus-child
native RSS accounting, fail-closed missing/malformed monitoring, and cleanup
semantics documented in the original preflight review. This is a sampled kill
gate with possible overshoot, not a kernel-enforced allocation or peak-memory
cap. The transient `ps` process is excluded; the guard covers this preflight,
not the entire independently managed research pool.

The child counts the full C4 line groups, recording actual orbit sizes as the
number of represented full lines. It then streams the frozen compact clauses
into `glucose3` using only `add_clause`, followed by `delete`. It contains no
call to `solve` or `solve_limited`, and every report has an explicit null solver
result and false search flag. Preliminary group counting and subsequent CNF
construction both occur under the same guard timer. Global cardinalities and
line semantics remain those of the already approved compact encoder.

The job binds hashes for the original model, line generator, compact encoder,
shared guard, and the separate preflight itself. The child checks them before
encoder import and after the clause stream, and the parent rechecks after the
guard returns. A complete model hash is published only after the full stream.
Host gate failure, source change, or host error clears completion/build flags
and the complete model hash even when the child published completion first.
Partial counters and the explicitly separate prefix hash remain available as
lower bounds; they are not evidence of a completed build.

The new dispatcher only activates with `--near-quarter-compact-preflight` and
delegates the remaining argument list and exit status. Build is its sole mode.
Invalid options terminate through its parser rather than falling through to
normal SAT search. The original preflight branch and ordinary search branch
retain their existing bodies.

## Independent checks

The reviewer reran the compact preflight, original preflight, and original
dispatch suites together: 23 tests ran in 0.554 seconds, with 20 passing and
three real-host tests skipped because sandbox `ps` is unavailable. Within the
new suite, nine tests passed and its one real-host subprocess test was skipped.
These tests cover the exact guard identity, capped limits, source changes
before and after streaming, startup zeros, host failure overriding child
completion, complete tiny hashes/counts, no-solve patches, argument forwarding,
and invalid-input rejection without search. `git diff --check` passed.

A separate reviewer construction-only solver spy checked n=3,5,7. It captured
every emitted clause and matched the frozen compact streams exactly: 2,32,180
clauses and 3,10,31 line groups respectively. Its search methods raised if
called; neither was called, and deletion occurred. These were tiny worker
correctness checks, not host memory measurements.

The real-host command reruns the new suite, whose final test launches
the n=3 opt-in CLI with the actual monitor and verifies positive sampled RSS,
all source hashes, two added clauses, three groups representing eight lines,
and the explicit no-search result. The Lead reported 136 host tests passing
without skips. The reviewer independently read the saved n=3 CLI report:
`built`, two clauses, three groups/eight represented lines, source identities
matching this review, complete hash
`204ced29cd45616df3009b879750d2abf90890594d4e72c8c34ac0d9a44ed222`,
0.152871 seconds, two real RSS samples with a peak of 51,600 KiB, exit zero,
no monitor error, and no search. This completes the real-host tiny gate.

## Published n71 fixed assignment

The previously independently verified published fixture was checked against
the actual compact local clause encoder without building a full n71 CNF.
The result is saved in `data/near-quarter-compact-n71-fixed-review.json`.
Its fixture SHA is
`00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9`.

The reviewer reconstructed the fixed 35 four-orbit selections and one diagonal
pair, confirming their expansion equals all 142 fixture points. Lines were
generated from pairs of the 140 selected off-diagonal points using normalized
integer equations, then grouped under quarter rotations. For each group,
grid cells and full off-diagonal weights were derived directly from the line
equations; all members' signatures and diagonal guards were checked.

All 2,450 relevant local groups passed both arithmetic capacities and projected
SAT with every support/guard decision variable fixed to that published
assignment. Only one local CNF was retained at a time; the largest had 595
clauses and 202 auxiliaries. The check took 0.21 seconds. These SAT calls tested
auxiliary satisfiability only and did not search for configurations.

This is sufficient for the fixed assignment: every possible non-main violation
requires at least two selected off-diagonal points, so its line appears in
the pair-generated set. Exactly one selected diagonal pair handles the main
and anti-diagonal capacities. Lines with fewer than two selected off-diagonal
points automatically meet every remaining capacity. No full model construction,
n79 execution, or unrestricted nonexistence claim follows from this check.

## Scheduled n79 build report audit

The Lead then scheduled `r16-near-quarter-compact-preflight-n79` through the
existing supervisor. The reviewer independently read both its supervisor
record and `data/near-quarter-compact-preflight-n79.json`, and compared all five
reported source hashes plus the supervisor's entrypoint hash to current files.
Every hash matches the frozen identities above. This was report inspection
and arithmetic verification, not another n79 build or line enumeration.

The report is internally consistent: the guard exited successfully, return
code zero, no monitor error, both source checks accepted, all count/CNF/build
completion flags true, and 2,300,453 emitted clauses equal 2,300,453 completed
native insertions. The maximum variable ID is 591,304, of which 1,560 are orbit
decision variables and 589,744 are auxiliaries. The complete model and prefix
hashes agree:

`909f510443e97c8b909e783115df53f6360f87b18dbce471794ffdf09bb4c2f6`

There are 411,545 C4 line groups, including one special diagonal group, and
411,544 compiled non-special groups. Their orbit sizes represent 1,644,284
full geometric lines. An independent arithmetic count confirms these totals:
for each positive primitive direction `(a,b)` with `a,b<=39`, the number of
maximal lines containing at least three grid points in that direction is
`(79-2a)(79-2b)-max(79-3a,0)*max(79-3b,0)`. Sum twice for the two slope signs
and add 158 horizontal/vertical lines. This gives 1,644,284. Exactly 1,896 of
these lines pass through the center and have a two-member C4 orbit; all others
have four members. Therefore `(1644284-1896)/4+1896/2=411545` groups. This also
agrees with half of the earlier complete half-turn count, 823,090. The 40,605
diagonal-guard incidence sum is an incidence count, not a count of variables.

Construction finished in 14.522241 seconds under the unchanged 30-second gate.
Across 331 samples, peak guard-plus-child RSS was 257,776 KiB, or 251.734375 MiB.
The distance to the 256 MiB sampling threshold was only 4.265625 MiB. Thus this
specific build passed the sampled gate; it does not establish sufficient
memory for a solver search, an unsampled peak bound, or a future repeated run.
The report explicitly retains `search_performed=false` and `solver_result=null`.

The complete formula digest is accepted from the audited hash-producing
construction and its successful terminal checks; it was not independently
recomputed by rebuilding the large formula. Any search requires its own
reviewed wrapper and separately scheduled resource gate. This review neither
authorizes automatic search nor claims SAT, UNSAT, novelty, or global
nonexistence.
