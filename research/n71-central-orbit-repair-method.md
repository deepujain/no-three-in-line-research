# One fixed central four-orbit deletion checker

Implementation model `gpt-6.1-sol`, reasoning `high`. This standalone finite
checker implements only the independently approved central case in
`n71-one-four-orbit-repair-proposal.md`. No packed source was changed, and no
n79 geometry or repair search was executed during implementation.

The CLI requires exact fixture bytes SHA-256
`00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9`
and n71. Both existing exact verifiers validate the original fixture. The unique
central off-diagonal orbit must equal `(10,35),(35,10),(35,60),(60,35)`.
Translation by `(4,4)` and deletion leave the exceptional diagonal pair intact.
Exactly five new four-orbits fill the remaining row/column demands. Their
radius endpoints are0,25,36,37,38,39, with demand1 at0 and25 and2 at each outer
radius. There is one orientation at0 and two elsewhere:25 distinct labeled
edges. Exhausting all53,130 five-edge subsets yields547 degree-feasible choices,
including all51 readditions of the exact deleted orbit. Nothing omits those51.

For each candidate four-orbit, the checker defensively rejects overlap with
retained cells. It tests every triple involving any new point against retained
points and the same orbit by integer determinants; retained-only triples are
valid because the retained set is a subset of the dual-verified fixture. A
rejected orbit retains an explicit collinear triple. Any full selection
containing it is impossible, independently of its other selected orbits, so
filtering that selection is exact. The report links every filtered selection
to its rejected edge. This filter need not find conflicts between different
new orbits: every surviving full selection receives both unchanged complete
geometry verifiers after exact cardinality, row and column assertions. A
verified witness is atomically written before early return. That return is
truthfully incomplete as an exhaustive census.

The soft budget is positive and at most25s. Deadline checks cover arithmetic
enumeration, orbit filtering and candidate boundaries. Existing full validators
and atomic writes are not interrupted internally. Root must apply the existing
owned process guard at30s/256MiB in a nonoverlapping allocation. A timeout report
retains completed filter/candidate evidence and claims no exhaustive result.
A hard kill can leave no report. The imported atomic writer fsyncs its file and
renames it but does not fsync the directory; no crash-durability claim is made.
There is no scheduler, guard implementation, resume mode or checkpoint protocol.

Twelve tests pass in0.295s: seven new tests plus the five previous finite51
checks. Only n3-to-n11 analogous geometry is constructed in these tests. Actual
tiny row loads independently select exactly547 of all53,130 subsets and show
51 readditions. Small filter cases agree with the independent slope verifier;
controlled survivors exercise both complete verifiers547 times. Further tests
cover all547 tiny records, strict budgets, invalid fixtures, timeout before work,
timeout partway through filtering, and witness persistence before early return.
Source hashes are in `data/n71-central-orbit-repair-source-pins.json`; the full
test output and scope are in `data/n71-central-orbit-repair-tiny-evidence.json`.

A complete clean negative result would exclude only these547 central-deletion
selections of this particular centered fixed near-quarter fixture. It would not
cover the other34 source four-orbit deletions, more deletions, other fixtures,
unrestricted extensions, or n79 generally. Even if the exact filters reject
every candidate, actual scope closure still requires the complete report,
clean host gate and independent evidence audit.
