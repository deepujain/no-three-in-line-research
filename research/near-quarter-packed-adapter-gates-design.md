# Packed near-quarter adapter and host gate proposal

Status: design only. The Lead requested this proposal while the isolated tiny
core/codec finishes review. No new source, geometry allocation, search, wrapper
or dispatcher change is made here. Model setting: `gpt-6.1-sol`, reasoning `high`.
The existing full-CNF branch remains stopped and its failed stages are preserved.

## Concrete production lift

Keep `near_quarter_tiny_secants.py` and `near_quarter_tiny_batches.py` unchanged.
Add one narrow `research/near_quarter_packed_state.py`, with `PackedOrbitState`
for odd n3..79 and a tiny specialized read-only orbit view over packed cells.
It implements the same geometry/type/axis invariant as the reviewed tiny state,
with explicit progress-aware interruption rollback. It is not a new solver,
learned-clause mechanism, partial-orbit family or general adapter framework.

After separate source review, make only these integration changes:

- In `near_quarter_rowbatch_core.py`, factor bounded core initialization so the
  existing hard-tiny constructor still accepts only n3/5/7, while one explicit
  `PackedRowBatchCore` constructor selects the new state. Preserve row policy,
  batch order and logical event/cursor transitions. Bind a common deadline
  callback to state before operations; no caller-supplied module/class paths.
- Replace the per-row retained Python contributor lists in `_scan` with one
  admissibility byte array, per-row one/two-weight counts and one chosen-row
  candidate/weight buffer. Domains are still rebuilt, not cached by depth.
- In `near_quarter_rowbatch_checkpoint.py`, permit only the two literal core
  classes and a closed adapter1/adapter2 restore dispatch. Adapter2 selects the
  new source in the existing state-adapter identity slot and writes identity
  adapter byte2 by closed class selection. Capture separate import-time source
  bundles for the two literal state modules; no schema/source-slot expansion.
  Adapter2 uses leaf_mode1 only, preserving v1's existing rule that tiny-census
  mode belongs to adapter1. Keep v1's exact wire
  fields, 40-frame cap, external authority and strict replay unchanged.
- Add `tests/test_near_quarter_packed_state.py` and production-adapter cases in
  the isolated checkpoint tests. Do not edit historical DFS, CNF, shared CLI,
  process helper, unrelated reflection checkpoint, or accepted old frontiers.

These integration source changes change their SHA-256 identities. Prior tiny
checkpoints remain preserved under their old source binding; there is no
silent migration, source-hash substitution or merging of frontier histories.
Adapter2 cannot restore an adapter1 checkpoint and vice versa. The initial
n79 family still consists of exactly39 four-orbits plus one diagonal pair.

## Bounded model and concrete arrays

Validate strict integer odd n in3..79 before any n-dependent allocation. Check
`array('H').itemsize==2`; reject unsupported widths rather than changing wire
or overflow assumptions. At n79, m39 gives1521 four-orbits,39 diagonal pairs,
1560 orbit IDs,6162 stored point incidences,6241 grid cells and158 selected
points. All counts below are validated with Python integer arithmetic before
constructing arrays; no count comes from an unchecked checkpoint field.

| State structure | Representation and maximum |
| --- | --- |
| flat orbit cells | array H,6162 cells, each y*n+x in0..6240 |
| orbit offsets | array H,1561 entries ending at6162 |
| secant blockers | array H,6241 counters |
| occupancy | bytearray6241 |
| row and column loads | two bytearrays of79 |
| selected point cells | preallocated array H,158 slots plus scalar length |
| selected orbit IDs | preallocated array H,40 slots plus scalar length |
| type counts | scalar four<=39 and diagonal<=1 |
| in-progress point transaction | bounded scalar progress fields described below |
| admissibility scratch | bytearray1521, reset per complete scan |
| row scratch | two arrays H of79 one/two-weight counts |
| chosen domain | array H IDs and byte weights, at most1521 entries each |

Orbit cells+offsets are15,446 packed bytes; live geometry arrays/point+orbit
stacks are19,277; permutations are3,278; the scratch arrays listed above are
6,400. Their subtotal is44,401 bytes. This is arithmetic for these arrays only,
not a new complete live-memory budget: Python objects/headers, frame objects,
source reads, temporary map construction, transaction scalars, digest/codec
buffers, verifiers, interpreter/native/OS state and guard memory are excluded.
The v1 wire's96-byte frames are not Python frame-size measurements. The prior
68,700-byte proposal remains historical arithmetic for a different reserved
layout and must not be silently relabeled an observed RSS result.

The specialized orbit view supplies len/index/ordered iteration returning at
most four coordinate pairs per access, using `divmod(cell,n)`; it retains no
second complete tuple map or point->variable dictionary. The minimal model
mapping exposes n, four_count, diagonal_count and this view, which suffices for
the unchanged `expand`/`check_candidate` verifier path. No weighted-line/CNF
routine is called on that minimal mapping. Point insertion order is precisely
the sorted tuple order of the frozen `orbit_map` source.

Construction uses the same finite coordinate/rotation/canonical-tuple procedure
as `orbit_map`, with checks on every coordinate iteration; its temporary set
has at most1521 canonical four-orbits. Sort that bounded set in exact tuple
order, append the same39 diagonal pairs, pack, then release temporary tuples.
Check before/after the bounded sort; the hard process guard covers that Python
sort interval as well. Never use hash iteration order as orbit order. Independent
tests compare the entire ordered map with the frozen function, not merely its
size. At construction compute the existing v1 binary map digest; future host
preflight also compares the frozen model's historical JSON map digest against
source-bound accepted records. Neither hash proves geometry by itself.

## Secant arithmetic and overflow

For each unoccupied prospective point p, blocked[p]>0 exactly means an existing
selected pair is collinear with p. Each inserted point adds every maximal grid
line through p and an earlier point q, including endpoints. Primitive steps
use integer gcd, with signed dx/dy; coordinate differences are in-78..78.
Line walks remain within0..78 and visit at most79 cells. There is no resident
line catalogue or cumulative update log.

At all valid/transient prefixes, <=158 distinct selected points imply each
cell counter<=C(158,2)=12,403<65,536. Type caps, orbit disjointness and point
occupancy checks are prerequisites of that bound, not optional optimizations.
Every increment checks against65535 before mutation and every inverse checks
positive before decrement. An impossible overflow/underflow is a fatal
consistency error, never a geometrical rejection/prune. Grid indices<=6240,
offsets<=6162, IDs<=1560, domain counts<=1521 and row scratch counts<=1521 all
fit H. Row/column loads never exceed2. Cursor pairs remain two H local indices;
their number1,155,960 is not stored in H.

## Exact interruption-safe point and orbit transactions

A point transaction retains entry point-count, prospective cell p, current
previous-point index t, current line's start/step/length, and next cell index j.
These are bounded scalar fields, not a list of previous updates.

1. Check stop/deadline and p's occupancy, axis capacities and blocker before
   mutation. Prepare the selected-point/metadata destination slots in advance.
2. For each earlier point in stack order, compute its line and walk cells.
   Before each increment check deadline/cancel and counter width. After each
   increment advance j. After each complete line advance t and reset j.
3. Only after all such lines finish, commit p to its preallocated point slot,
   occupancy and axis loads, with no intervening cancellable operation.
4. On stop/error before point commit, decrement exactly the j completed cells
   of the current line, then all lines for earlier complete previous points
   0..t-1. Recompute their line walks; do not retain an unbounded cell journal.
   The point was never appended, so occupancy/axis state is still its entry
   state. A counter fault during this inverse poisons the state/stage.

An orbit transaction records entry selected-point count. If any of its up to
four points rejects/stops, first undo that point's incomplete progress, then
remove fully committed new points in reverse order back to entry. Do not add
its selected-orbit ID/type count until all its points commit. A pair transaction
retains the reviewed core's whole-orbit rollback around those guarantees.
An orbit rejected for geometry returns False with exact entry snapshot; a stop
raises only after rollback. Unexpected consistency failure marks the core
unusable and prohibits saving/adoption from it; the immutable parent survives.

Pop and rollback must finish the complete bounded inverse even after a deadline
or cancellation arrives. A nonthrowing poll latches stop while decrementing;
no cancellation exception may split the inverse. `pop` returns normally, the
core commits its corresponding frame transition, then the common check can
raise the latched stop. A successful push interrupted before its RAM frontier
commit instead rolls back and leaves PENDING. These distinct push-versus-pop
rules prevent geometry and frame phase from disagreeing after a stop.
Preallocate successor/child-frame metadata before mutation. Check immediately
before logical counter/phase commits after domain scans; cleanup work is
charged as physical work even if no logical node/candidate commits.

The full geometry snapshot includes blocker/occupancy/axis arrays, zeroed
unused point+orbit stack slots, active lengths/type counts, and poison/pending
transaction flags. Static packed map bytes are bound separately by identity.
Every coherent checkpoint boundary requires no pending point/orbit transaction
and no poison flag. `save_candidate` compares replayed full snapshot and
frontier/counters before any write, as in the revised tiny codec.

## Deadline-aware reconstruction and observable work

Use one monotonic deadline and signal-cancellation flag from before load or
construction. Bind the same budget to model construction, probes, pair cursor,
point/secant loops, source hashing, private restore and publication. Checks
occur at every geometry cell update and coordinate construction iteration;
cleanup polls but finishes inverses. Hash/sort/fsync and Python scheduling have
bounded inputs but are not hard real-time operations. The unchanged external
process guard supplies the hard acceptance ceiling; sampled RSS has its stated
measurement limitations.

Checkpoint wire decoding remains bounded before allocations. Replay builds
its entire state privately, validates each ancestor domain/child/cursor and
all source/map/permutation identities, then adopts only after a final check.
Timeout in source checks, model creation, ancestor scans or incoming batch
application returns no adopted child core and no new frontier. An already
accepted parent is never invalidated or consumed merely by attempted replay.
A frontier that repeatedly cannot restore within a fixed gate is reported as
restore-limited; never retry unchanged automatically or raise the budget.

Maintain existing exact logical nodes/leaves/prunes/committed batch counters.
Add bounded per-invocation physical counters for point attempts, pair-line
walks, cell increments, inverse cell updates, rejected/aborted orbit attempts,
and restore work; do not serialize them as historical tree nodes. Successful
and aborted probes and cleanup count toward wall/RSS and these work counters.
A slow single domain scan is not hidden as a high node rate. Stage output must
distinguish import/map, restore, new traversal, verification, checkpoint and
cleanup elapsed phases, without claiming their sum is inside a guard if it is
not actually measured there.

## Tiny oracle and fault gates before a broad-grid run

First implement only the new state and tiny tests, using n3/n5/n7. Reuse the
frozen independent determinant oracle: all4/64/4096 tiny orbit subsets,
4/17/100 valid partial subsets and8/102/1200 extension attempts. Compare full
snapshots after every accepted/rejected push and pop, plus exact ordered map
and leaves. Require every admitted source family/type/axis condition, including
rejecting bool/even/>79 before allocation and checking H width.

For each selected representative point transaction, inject a stop at every
increment boundary, including before the first update, between lines, after
the last counter update and before point/orbit metadata commit. Verify snapshot
restoration. Exercise stops after first/second successful batch orbits, a second
rejection, and injected pre-mutation exceptions. Pop/rollback stop polls must
finish a coherent inverse, latch stop and let the core commit before raising.
Overflow/underflow fault tests must poison and reject save rather than advertise
a pruned or resumed frontier. No partial-orbit witness callback is added.

Then integrate only on tiny grids. Run every reachable first-event-mode phase
roundtrip, one-node stages, both declared order directions, repeated LEAF/FOUND acks,
parent/chain/source/counter corruption and immutable-save faults with adapter2.
Require the same mathematical leaves and logical tree counters as adapter1
in the same first-event mode and the independent brute-force census (the real
tiny complete-set counts are1/0/0, so first-event mode loses no tiny census leaf).
Adapter2 must still reject mode2 and DONE/TINY_LEAF; no wire rule is relaxed to
reuse a test mode. The abstract12-leaf quota fixture remains
an explicitly abstract cursor/control test, not an adapter geometry oracle.

## Proposed actual-host preflight and cost sequence

All host scheduling, deadlines and receipt acceptance remain with Lead. These
are proposed parameters for reviewed gates, not commands or permission to run.
Use the existing unchanged `owned_process_guard.py`
SHA c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48.
Every gate stays at or below30 seconds and256MiB, counts the owned tree plus
monitor as implemented, includes cleanup, and fails closed on ps/source/signal/
identity errors. The source-bound worker retains original SID/PGID. No fallback
backend, larger cap or automatic repeat follows failure. The prior subagent ps
restriction is not evidence about actual-host gate success; Lead owns host use.

1. **Tiny host contracts.** After independent state/core/codec source approval,
   guarded n3/n5/n7 witness/exhaustion, one-node save/resume, external-hash
   rejection and SIGTERM/cancel during replay/push/publication. Proposed child
   logical deadline5s under a10s/256MiB helper. Require positive monitor samples,
   clean owned-tree cleanup, coherent accepted parent/output hashes and no
   invalid-stage promotion. These test the final source/entrypoint bundle.
2. **Known fixture, no search.** Replay the accepted n71 fixture's one diagonal
   and35 four-orbits in declared fixed order, dual-verify142 points, undo to the
   exact empty snapshot. Use a20s child deadline under30s/256MiB; one fixed order
   initially, no branch tree. Bind `data/published-n71-rct4.json`
   SHA00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9
   and checker `check_near_quarter_fixture.py`
   SHAe4b1438b9c461a5bb447170c0198ecfd2b9fa174d1b281435bcc6e694b933cd6.
   Measure actual RSS/time including construction and dual checks. Failure is a
   failed fixed-fixture gate, never a new result about existence/search.
3. **Modest traversal pilot.** Fresh n9, explicit default permutations and all
   four diagonal slices, max25 new nodes,5s child/10s256MiB helper. Save/replay
   once only if a coherent frontier is produced and the stage passes its gate.
   Report exact committed nodes, domain/batch/cell work, frontier bytes and
   source identities. This is a cost measurement, not an n79 forecast.
4. **n79 construction preflight.** Only after those gates and Lead scheduling,
   build/pack/hash n79 and push/pop one declared diagonal pair, with no DFS or
   MRV scan,20s child/30s256MiB helper. Compare ordered model identity to frozen
   oracle and accepted records under that same measured interval. Report import,
   construction, transient-map peak (only if separately measured), sampled total
   RSS and clean empty restoration. No memory-fit conclusion before this run.
5. **n79 first limited cost stage.** After reviewed preflight evidence and an
   explicit scheduled allocation, max1 new node with a20s child/30s256MiB helper,
   exact declared slices/permutations, source manifest and immutable genesis.
   Include its initial domain and checkpoint replay costs. A stopped domain or
   restore may yield zero new progress; that is reported without cap changes.
   Guarded success authorizes only the recorded stage, not an autonomous queue.

The future wrapper must publish witness data durably before any accepted FOUND
stage, and publish its stage report only after durable candidate installation.
A root-owned acceptance operation validates receipt/report/source/parent/output
hashes and clean resource gate before advancing the chain. A killed/torn stage
can leave an orphan candidate but cannot consume its accepted parent. No such
wrapper or acceptance-pointer operation is implemented by the current core.

The reviewed half-turn single-deletion lemma already closes the proposed
three-of-final-four157 escape from an invalid complete158 candidate. It supplies
no more general157 impossibility and no novelty claim; keep it as a scoped
pruned hypothesis rather than expanding this adapter's search family.
