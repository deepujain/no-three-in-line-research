"""Closed tiny/packed near-quarter row-batch cores, without CLI or process guard.

Adapter1 remains n3/n5/n7. Adapter2 is mode1 and bounded to odd n3..79;
only tiny integration tests are allocated here, with no broad-grid run.
"""
from array import array
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import struct

from research.near_quarter_rowbatch_cursor import Cursor, Domain, NONE, SINGLE, PAIR, END
from research.near_quarter_tiny_secants import TinyOrbitState
from research.near_quarter_packed_state import PackedOrbitState, PackedStop, packed_bounds
from src.near_quarter_model import check_candidate
from research.near_quarter_radius_graph import radius_obstruction
from research.near_quarter_readonly_probe import probe_orbit

ZERO = bytes(32)
BETWEEN, ACTIVE, EXHAUSTED, FOUND = range(1, 5)
ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE = range(1, 8)
DRAINED, ORBIT_SHORTFALL, ROW_SHORTFALL, TARGET_NONLEAF, TINY_LEAF, RADIUS_SHORTFALL = range(1, 7)
COUNTERS = ('nodes', 'leaves', 'attempts', 'rejected', 'orbit_prunes', 'row_prunes', 'target_closures')
ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = tuple(ROOT/p for p in (
    'research/near_quarter_rowbatch_core.py', 'research/near_quarter_tiny_secants.py',
    'research/near_quarter_rowbatch_cursor.py', 'research/near_quarter_rowbatch_checkpoint.py',
    'src/near_quarter_model.py', 'src/verify.py', 'src/line_model.py'))

PACKED_SOURCE_PATHS = SOURCE_PATHS[:1]+(ROOT/'research/near_quarter_packed_state.py',)+SOURCE_PATHS[2:]
# Transitive helper binding preserves the closed seven-source wire shape.
# This literal and the import-time check bind the executing reviewed helper;
# every subsequent packed source check rechecks current bounded helper bytes.
RADIUS_SOURCE_PATH = ROOT/'research/near_quarter_radius_graph.py'
RADIUS_SOURCE_SHA = bytes.fromhex('647ae1379eb89711707f9900d68a2aba1861839751bdb22f15e9618d1f5cda66')
READONLY_SOURCE_PATH = ROOT/'research/near_quarter_readonly_probe.py'
READONLY_SOURCE_SHA = bytes.fromhex('2b9f51496f80c78881643724029e48cd9987b1428bdffbce7736806d790f5c7d')


def _source_digests(check=lambda: None, *, adapter=1):
    hashes = []
    paths = SOURCE_PATHS if adapter == 1 else PACKED_SOURCE_PATHS+(RADIUS_SOURCE_PATH, READONLY_SOURCE_PATH,)
    for path in paths:
        check()
        hasher, total = hashlib.sha256(), 0
        with path.open('rb') as stream:
            while True:
                check()
                chunk = stream.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > 1_048_576:
                    raise ValueError('source file exceeds bound')
                hasher.update(chunk)
        hashes.append(hasher.digest())
    if adapter == 2 and hashes.pop() != READONLY_SOURCE_SHA:
        raise ValueError('reviewed read-only helper source differs')
    if adapter == 2 and hashes.pop() != RADIUS_SOURCE_SHA:
        raise ValueError('reviewed radius helper source differs')
    return tuple(hashes)


EXECUTING_SOURCE_HASHES = {1: _source_digests(), 2: _source_digests(adapter=2)}


def u16(value):
    return struct.pack('>H', value)


def digest(prefix, data):
    return hashlib.sha256(prefix.encode('ascii')+b'\0'+data).digest()


def permutation(values, expected, *, subset=False):
    expected = tuple(expected)
    from research.near_quarter_rowbatch_cursor import bounded_tuple
    result = expected if values is None else bounded_tuple(values, len(expected))
    if (any(type(v) is not int for v in result) or len(set(result)) != len(result) or
            (not set(result) <= set(expected)) or (not subset and len(result) != len(expected))):
        raise ValueError('invalid order declaration')
    return result


@dataclass(frozen=True)
class Frame:
    phase: int = ENTER
    incoming: tuple = ()
    origin: Cursor = Cursor(NONE)
    row: int = 0
    deficit: int = 0
    domain_length: int = 0
    domain_digest: bytes = ZERO
    cursor: Cursor = Cursor(NONE)
    pending: tuple = ()
    leaf_digest: bytes = ZERO
    close_reason: int = 0

    def cleared(self, phase, **fields):
        return Frame(phase=phase, incoming=self.incoming, origin=self.origin, **fields)


class TinyRowBatchCore:
    def __init__(self, n, *, diagonal_order=None, orbit_order=None, row_order=None,
                 leaf_mode=2, check=lambda: None):
        if type(n) is not int or n not in (3, 5, 7):
            raise ValueError('geometry adapter permits n3/n5/n7 only')
        if type(leaf_mode) is not int or leaf_mode not in (1, 2):
            raise ValueError('invalid leaf mode')
        check()
        self._initialize(n, TinyOrbitState(n), 1, diagonal_order, orbit_order, row_order, leaf_mode, check)

    def _initialize(self, n, state, adapter, diagonal_order, orbit_order, row_order, leaf_mode, check):
        self.n, self.m, self.leaf_mode, self.adapter = n, n//2, leaf_mode, adapter
        self.state = state
        four = self.state.model['four_count']
        self.diagonals = permutation(diagonal_order, range(four+1, four+self.m+1), subset=True)
        self.orbits = permutation(orbit_order, range(1, four+1))
        self.rows = permutation(row_order, range(n))
        self.outer = BETWEEN if self.diagonals else EXHAUSTED
        self.slice_index = 0
        self.frames = []
        self.counts = dict.fromkeys(COUNTERS, 0)
        self.work = dict.fromkeys(('domain_probes', 'batch_probes', 'cursor_checks',
                                  'restore_probes', 'interrupted_scans'), 0)
        self.restore_mode = False
        self.restore_work = dict.fromkeys(state.work, 0) if adapter == 2 else {}
        self.validation_work = dict(self.restore_work)
        self.source_hashes = EXECUTING_SOURCE_HASHES[adapter]
        self.check_sources(check)
        self.map_digest = state.map_digest if adapter == 2 else self._map_digest()
        self.perm_digest = digest('NQRB-PERMS-v1', self.permutation_bytes())
        check()

    def check_sources(self, check=lambda: None):
        if self.adapter not in (1, 2) or _source_digests(check, adapter=self.adapter) != self.source_hashes:
            raise ValueError('executing source identity changed')

    def _bind_check(self, check):
        if self.adapter == 2:
            self.state.bind_check(check)

    def _undo_orbits(self, count, *, suppress_stop=False, defer_stop=False):
        for _ in range(count):
            if self.adapter == 2:
                self.state.rollback_last_orbit()
            else:
                self.state.pop()
        if self.adapter == 2 and not defer_stop:
            if suppress_stop:
                try:
                    self.state.raise_latched()
                except PackedStop:
                    pass  # Original error is propagated after coherent cleanup.
            else:
                self.state.raise_latched()

    def _map_digest(self):
        data = u16(self.n)+u16(len(self.state.model['orbits']))
        for orbit in self.state.model['orbits']:
            data += bytes((len(orbit),))+b''.join(u16(x)+u16(y) for x, y in orbit)
        return digest('NQRB-MAP-v1', data)

    def permutation_bytes(self):
        return (u16(self.n)+u16(len(self.diagonals))+
                b''.join(u16(v) for v in (*self.diagonals, *self.orbits, *self.rows)))

    def leaf_digest(self):
        selected = sorted(self.state.selected)
        return digest('NQRB-LEAF-v1', bytes((1,))+u16(self.n)+self.map_digest+
                      u16(len(selected))+b''.join(u16(v) for v in selected))

    def _inc(self, name):
        if self.counts[name] == (1 << 64)-1:
            raise OverflowError('logical counter overflow')
        self.counts[name] += 1

    def _scan(self, check):
        """One bounded current mask/histogram/domain; no per-depth domains."""
        self._bind_check(check)
        mask = bytearray(len(self.orbits))
        ones, twos = array('H', [0])*self.n, array('H', [0])*self.n
        r, viable = self.m-self.state.four_selected, 0
        try:
            for variable in self.orbits:
                check()
                if variable in self.state.selected:
                    continue
                self.work['restore_probes' if self.restore_mode else 'domain_probes'] += 1
                # Query counts include read-only geometry. state.work remains
                # actual mutation-engine work, excluding query line/read cost.
                admitted = (probe_orbit(self.state, variable, check) if self.adapter == 2
                            else self.state.push(variable))
                if not admitted:
                    continue
                try:
                    viable += 1
                    mask[variable-1] = 1
                    ys = tuple(y for x, y in self.state.model['orbits'][variable-1])
                    seen = []
                    for row in ys:
                        # Adapter1 temporarily contains the candidate; the
                        # read-only packed path already has parent row loads.
                        if row in seen:
                            continue
                        seen.append(row)
                        weight = ys.count(row)
                        parent_load = self.state.rows[row]-(weight if self.adapter == 1 else 0)
                        if parent_load < 2:
                            (ones if weight == 1 else twos)[row] += 1
                except BaseException:
                    if self.adapter == 1:
                        self._undo_orbits(1, suppress_stop=True)
                    raise
                else:
                    if self.adapter == 1:
                        self._undo_orbits(1)
            check()
            if viable < r:
                return ORBIT_SHORTFALL, None, None
            rows = [row for row in self.rows if self.state.rows[row] < 2]
            for row in rows:
                optimistic = 2*min(twos[row], r)+min(ones[row], max(0, r-twos[row]))
                if optimistic < 2-self.state.rows[row]:
                    return ROW_SHORTFALL, row, None
            if not rows:
                raise RuntimeError('full rows without exact leaf')
            # Only the completed mask is eligible. No extra orbit probes;
            # passing nodes retain the exact row/domain/cursor ordering.
            if self.adapter == 2 and radius_obstruction(
                    self.n, self.state.rows, self.state.model['orbits'], mask, r, check):
                return RADIUS_SHORTFALL, None, None
            row = min(rows, key=lambda a: (ones[a]+twos[a], -(2-self.state.rows[a])))
            ids, weights = [], []
            for variable in self.orbits:
                check()
                if mask[variable-1]:
                    weight = sum(y == row for x, y in self.state.model['orbits'][variable-1])
                    if weight:
                        ids.append(variable)
                        weights.append(weight)
            return 0, row, Domain(ids, weights, 2-self.state.rows[row], r)
        except BaseException:
            self.work['interrupted_scans'] += 1
            raise

    def domain_digest(self, row, domain):
        data = u16(self.n)+u16(row)+bytes((domain.deficit,))+u16(domain.remaining)+u16(len(domain.ids))
        data += b''.join(u16(v)+bytes((w,)) for v, w in zip(domain.ids, domain.weights))
        return digest('NQRB-DOMAIN-v1', data)

    def _domain(self, frame, check):
        reason, row, domain = self._scan(check)
        if (reason or row != frame.row or domain.deficit != frame.deficit or
                len(domain.ids) != frame.domain_length or self.domain_digest(row, domain) != frame.domain_digest):
            raise ValueError('reconstructed domain mismatch')
        domain.validate(frame.cursor)
        return domain

    def _cursor_check(self, check):
        self.work['cursor_checks'] += 1
        check()

    def _push_batch(self, batch, check):
        self._bind_check(check)
        pushed = 0
        try:
            for variable in batch:
                check()
                if not self.state.push(variable):
                    undo, pushed = pushed, 0
                    self._undo_orbits(undo)
                    return False
                pushed += 1
            check()
            return True
        except BaseException:
            self._undo_orbits(pushed, suppress_stop=True)
            raise

    def step(self, *, check=lambda: None, node_room=True):
        """One coherent frontier transition; false means quota or terminal/event."""
        check()
        self._bind_check(check)
        if self.outer in (EXHAUSTED, FOUND):
            return False
        if self.outer == BETWEEN:
            frames = [Frame()]
            if not self.state.push(self.diagonals[self.slice_index]):
                raise RuntimeError('empty diagonal rejected')
            self.frames, self.outer = frames, ACTIVE
            return True
        frame = self.frames[-1]
        if frame.phase == ENTER:
            if not node_room:
                return False
            next_frame = replace(frame, phase=COUNTED)
            self._inc('nodes')
            self.frames[-1] = next_frame
        elif frame.phase == COUNTED:
            if self.state.full_family_leaf():
                if not check_candidate(self.state.model, self.state.selected)['valid_full_witness']:
                    raise RuntimeError('leaf failed independent geometry checks')
                check()
                next_frame = frame.cleared(LEAF, leaf_digest=self.leaf_digest())
                self._inc('leaves')
            elif self.state.four_selected >= self.m:
                next_frame = frame.cleared(DONE, close_reason=TARGET_NONLEAF)
                self._inc('target_closures')
            else:
                reason, row, domain = self._scan(check)
                check()
                if reason:
                    fields = ({'row': row, 'deficit': 2-self.state.rows[row]} if reason == ROW_SHORTFALL else {})
                    next_frame = frame.cleared(DONE, close_reason=reason, **fields)
                    self._inc('row_prunes' if reason == ROW_SHORTFALL else 'orbit_prunes')
                else:
                    next_frame = replace(frame, phase=READY, row=row, deficit=domain.deficit,
                        domain_length=len(domain.ids), domain_digest=self.domain_digest(row, domain),
                        cursor=domain.first(lambda: self._cursor_check(check)))
            self.frames[-1] = next_frame
        elif frame.phase == READY:
            if frame.cursor.kind == END:
                self.frames[-1] = replace(frame, phase=DONE, close_reason=DRAINED)
            else:
                domain = self._domain(frame, check)
                self.frames[-1] = replace(frame, phase=PENDING, pending=domain.batch(frame.cursor))
        elif frame.phase == PENDING:
            domain = self._domain(frame, check)
            if frame.pending != domain.batch(frame.cursor):
                raise ValueError('pending batch mismatch')
            successor = domain.successor(frame.cursor, lambda: self._cursor_check(check))
            parent = replace(frame, phase=WAITING, cursor=successor, pending=())
            new_frames = self.frames[:-1]+[parent, Frame(incoming=frame.pending, origin=frame.cursor)]
            # All potentially failing logical-counter checks precede geometry mutation.
            if self.counts['attempts'] == (1 << 64)-1 or self.counts['rejected'] == (1 << 64)-1:
                raise OverflowError('batch counter overflow')
            self.work['batch_probes'] += 1
            if self._push_batch(frame.pending, check):
                if self.state.rows[frame.row] != 2:
                    self._undo_orbits(len(frame.pending), suppress_stop=True)
                    raise RuntimeError('batch did not fill selected row')
                self.counts['attempts'] += 1
                self.frames = new_frames
            else:
                next_frame = replace(frame, phase=READY, cursor=successor, pending=())
                self.counts['attempts'] += 1
                self.counts['rejected'] += 1
                self.frames[-1] = next_frame
        elif frame.phase == LEAF:
            return False
        elif frame.phase == DONE:
            if len(self.frames) == 1:
                next_index = self.slice_index+1
                self._undo_orbits(1, defer_stop=True)
                self.frames, self.slice_index = [], next_index
                self.outer = BETWEEN if next_index < len(self.diagonals) else EXHAUSTED
            else:
                new_frames = self.frames[:-2]+[replace(self.frames[-2], phase=READY)]
                self._undo_orbits(len(frame.incoming), defer_stop=True)
                self.frames = new_frames
            if self.adapter == 2:
                self.state.raise_latched()  # Whole pop and frame commit are complete.
        else:
            raise RuntimeError('top frame cannot be WAITING')
        return True

    def ack_leaf(self, event_digest):
        if self.outer == FOUND:
            if event_digest != self.frames[-1].leaf_digest:
                raise ValueError('wrong terminal acknowledgment')
            return
        if self.outer != ACTIVE or self.frames[-1].phase != LEAF or event_digest != self.frames[-1].leaf_digest:
            raise ValueError('no matching pending leaf')
        if self.leaf_mode == 1:
            self.outer = FOUND
        else:
            self.frames[-1] = replace(self.frames[-1], phase=DONE, close_reason=TINY_LEAF)

    def run(self, max_new_nodes, *, check=lambda: None, on_leaf=None):
        if type(max_new_nodes) is not int or not 1 <= max_new_nodes <= 10000:
            raise ValueError('invocation node cap1..10000')
        before = self.counts['nodes']
        while self.outer not in (EXHAUSTED, FOUND):
            check()
            if self.frames and self.frames[-1].phase == LEAF:
                if on_leaf is None:
                    return 'leaf_pending'
                on_leaf(tuple(sorted(self.state.selected)), self.frames[-1].leaf_digest)
                self.ack_leaf(self.frames[-1].leaf_digest)
                continue
            if not self.step(check=check, node_room=self.counts['nodes']-before < max_new_nodes):
                return 'node_limit'
        return 'found' if self.outer == FOUND else 'declared_slices_exhausted'


class PackedRowBatchCore(TinyRowBatchCore):
    def __init__(self, n, *, diagonal_order=None, orbit_order=None, row_order=None,
                 leaf_mode=1, check=lambda: None):
        packed_bounds(n)
        if type(leaf_mode) is not int or leaf_mode != 1:
            raise ValueError('packed adapter requires first-event leaf mode1')
        check()
        self._initialize(n, PackedOrbitState(n, check=check), 2,
                         diagonal_order, orbit_order, row_order, leaf_mode, check)
