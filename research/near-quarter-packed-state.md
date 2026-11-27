# Isolated packed near-quarter geometry state

The new `near_quarter_packed_state.py` implements only the isolated geometry
stage of the approved packed-adapter design. It does not integrate with the
core/codec, run a search, publish witnesses, or add a guard/CLI route. Frozen
tiny references and reflection sources/frontiers are unchanged. Model setting:
`gpt-6.1-sol`, reasoning `high`.

`PackedOrbitState` checks odd n3..79 and two-byte unsigned array width before
model allocation. The ordered packed orbit map exactly follows the frozen
quarter-turn and diagonal-pair model, with a small read-only coordinate view
and no retained point-to-variable dictionary or second full tuple map. Blocker
counters, occupancy, axis loads and fixed point/orbit stacks retain the reviewed
secant invariant. Every unused stack slot is zeroed on undo. Logical n79 bounds
are checked arithmetic; no geometry larger than n7 was instantiated in this
stage. No measured memory claim follows from the packed array sizes.

A point's progress record distinguishes completed pair lines from the completed
prefix of its current line. A cooperative `PackedStop` unwinds that exact
prefix and then all fully inserted points of its orbit. Checks include the
interval after the final cell update and before point/orbit metadata commit.
Rejected or interrupted pushes restore the complete entry snapshot. Unexpected
forward errors restore geometry when possible and poison the state; counter
inconsistency or inverse failure poisons it and forbids continuation/adoption.
A failed inverse is not retried against partially changed counters.

During an inverse, stop polling latches `PackedStop` while completing the full
pop. Its owner must commit the matching frontier transition, then call
`raise_latched()`. `rollback_last_orbit()` explicitly allows bounded owner
cleanup across already accepted orbits when the deadline is already expired
or a stop is already latched. It does not clear the stop. This distinction is
needed for whole-pair rollback: ordinary `pop()` may stop before mutation,
whereas owner cleanup must finish despite an already expired budget. No shared
core changes have been made to consume this contract yet.

Nine isolated tests passed in2.085 seconds. They compare all4/64/4096 n3/n5/n7
orbit subsets and8/102/1200 extensions with the frozen state and independent
determinants, rebuild exact counters/axis/occupancy state, undo fully, and
obtain1/0/0 dual-verified full leaves. The entire ordered model and v1 binary
map digest agree with the frozen oracle. All1512 unordered tiny grid-point
pairs match determinant lines in both directions.

Fault evidence covers170 construction stop boundaries,509 checked point/orbit
boundaries from six successful representatives across both orbit sizes and all
three tiny grids,118 valid-partial pop cancellation cases, and1164 composed
owner pair transactions including1164 second-push stops and990 second-push
rejections. Sticky cancellation remains active throughout undo. Tests also
inject increment overflow, inverse underflow, unexpected inverse polling,
forward failure before an update, physical-counter overflow, and an incomplete-
point inverse failure that is attempted exactly once. Poisoned or latched
states fail `assert_checkpointable()`.

`data/near-quarter-packed-state-tiny-evidence.json` records the concrete counts,
source identities, timing and limitations. Physical work counters exclude
logical DFS nodes and count actual attempted updates and inverses, including
aborted work. The orbit-attempt counter begins after duplicate/type prechecks;
its rejection count describes geometric rejection, with cancellation recorded
separately. These are local tests, without actual-host RSS/process guards or
hard wall-time claims. Independent source approval is required before the
planned narrow core/codec integration; broad-grid host gates remain separate
Lead-scheduled work.
