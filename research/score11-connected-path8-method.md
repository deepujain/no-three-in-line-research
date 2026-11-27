# Score11 connected eight-edge path completion

Implementation model: gpt-6.1-sol, high. Source/tiny preparation only; no actual
source geometry evaluation or owned-host run was performed for this delivery.
Seven tiny tests passed in 0.065 seconds. Independent mathematical approval is
recorded in the pinned arithmetic audit. Independent source review is pending.

The checker reconstructs the source's bipartite cycles of lengths 4, 12 and 142
and matches all six length-eight intervals containing the approved three-edge
cover against the exact pinned manifest. Each interval deletes eight original
points, retains 150 points, and frees a 20-cell rectangle. Every eight-cell and
seven-cell binary factor under both residual axis capacities is generated once
per template. Seven-cell factors are enumerated directly, including factors
that cannot be extended to an eight-cell factor.

There are 204 full and 1812 partial factors per template, 12096 raw records.
Effective original deletion is the patch minus original cells reinserted by the
factor. The accepted through-five fixed-source negative is pinned through the
prefix audit, suffix/combined audit and final accepted review. After this
prune, 3864 records remain. Requiring effective deletion to hit all eleven
original triples leaves 80 full and 1226 partial records, 1306 total. Counts
refer to candidate/template records: final sets shared across templates are
not deduplicated, and no distinct-final-set count is claimed.

Both complete validators establish the exact pinned source identity and its
eleven conflicts. Every patch hits all original triples, so each retained set
is valid. Individual-cell filtering excludes triples with two retained points.
Sequential exact conflict checks against retained plus previously added points
also cover two-new/one-retained and three-new triples. Every surviving 157/158
set receives both full validators and immediate atomic witness persistence.

The one shared soft deadline is at most 25 seconds and begins before source and
evidence validation. Source validation and a full witness validator call may
finish after the last soft-clock check; the existing Root-owned 30s/256MiB guard
is the outer gate. No new guard, checkpoint, scheduler or resume protocol is
introduced. Root owns any future allocation and run.

Each of the six templates is unstarted, partial or complete. Quota and geometry
started/completed counters are separate; interruption during geometry does not
count the factor as complete. A template is complete only after its complete
generator exhausts and its counts match the approved arithmetic. A witness
stops the run with incomplete coverage; timeout makes no closure claim. Only a
clean complete negative can close these six paths of this exact source. It
does not close all eight-deletion repairs, all connected trades or n79 globally.

Tiny tests compare quota generation to independent exhaustive small binary
matrices, reproduce the approved source incidence and factor histograms
without source geometry, compare geometry on a 4x4 fixture to brute-force
triples, reject changed evidence, test timeout accounting before validation
and during a mocked geometry call, and require both witness validators before
atomic saving. Full source evaluation remains a separately owned action.
