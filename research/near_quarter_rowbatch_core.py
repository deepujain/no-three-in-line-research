"""Iterative near-quarter row batches with a hard-tiny geometry adapter.

The separately versioned wire contract supports up to n79. This adapter never
instantiates geometry outside n3/n5/n7. No CLI, process guard or numerical pilot.
"""
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import struct

from research.near_quarter_rowbatch_cursor import Cursor, Domain, NONE, SINGLE, PAIR, END
from research.near_quarter_tiny_secants import TinyOrbitState
from src.near_quarter_model import check_candidate

ZERO = bytes(32)
BETWEEN, ACTIVE, EXHAUSTED, FOUND = range(1, 5)
ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE = range(1, 8)
DRAINED, ORBIT_SHORTFALL, ROW_SHORTFALL, TARGET_NONLEAF, TINY_LEAF = range(1, 6)
COUNTERS = ('nodes', 'leaves', 'attempts', 'rejected', 'orbit_prunes', 'row_prunes', 'target_closures')
ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = tuple(ROOT/p for p in (
    'research/near_quarter_rowbatch_core.py', 'research/near_quarter_tiny_secants.py',
    'research/near_quarter_rowbatch_cursor.py', 'research/near_quarter_rowbatch_checkpoint.py',
    'src/near_quarter_model.py', 'src/verify.py', 'src/line_model.py'))


def _source_digests(check=lambda: None):
    hashes = []
    for path in SOURCE_PATHS:
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
    return tuple(hashes)


EXECUTING_SOURCE_HASHES = _source_digests()


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
        self.n, self.m, self.leaf_mode = n, n//2, leaf_mode
        self.state = TinyOrbitState(n)
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
        self.source_hashes = EXECUTING_SOURCE_HASHES
        self.check_sources(check)
        self.map_digest = self._map_digest()
        self.perm_digest = digest('NQRB-PERMS-v1', self.permutation_bytes())

    def check_sources(self, check=lambda: None):
        if _source_digests(check) != self.source_hashes:
            raise ValueError('executing source identity changed')

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
        """Scratch only; check between complete tiny push/pop operations."""
        viable, weights = [], {row: [] for row in self.rows if self.state.rows[row] < 2}
        r = self.m-self.state.four_selected
        try:
            for variable in self.orbits:
                check()
                if variable in self.state.selected:
                    continue
                self.work['restore_probes' if self.restore_mode else 'domain_probes'] += 1
                if not self.state.push(variable):
                    continue
                try:
                    viable.append(variable)
                    orbit = self.state.model['orbits'][variable-1]
                    for row in weights:
                        weight = sum(y == row for x, y in orbit)
                        if weight:
                            weights[row].append((variable, weight))
                finally:
                    self.state.pop()
            if len(viable) < r:
                return ORBIT_SHORTFALL, None, None
            for row in self.rows:
                if row not in weights:
                    continue
                contribution = sorted((w for v, w in weights[row]), reverse=True)[:r]
                if sum(contribution) < 2-self.state.rows[row]:
                    return ROW_SHORTFALL, row, None
            if not weights:
                raise RuntimeError('full rows without exact leaf')
            row = min(weights, key=lambda a: (len(weights[a]), -(2-self.state.rows[a]), self.rows.index(a)))
            entries = weights[row]
            domain = Domain(tuple(v for v, w in entries), tuple(w for v, w in entries),
                            2-self.state.rows[row], r)
            return 0, row, domain
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
        pushed = 0
        try:
            for variable in batch:
                check()
                if not self.state.push(variable):
                    for _ in range(pushed):
                        self.state.pop()
                    return False
                pushed += 1
            check()
            return True
        except BaseException:
            for _ in range(pushed):
                self.state.pop()
            raise

    def step(self, *, check=lambda: None, node_room=True):
        """One coherent frontier transition; false means quota or terminal/event."""
        check()
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
                next_frame = frame.cleared(LEAF, leaf_digest=self.leaf_digest())
                self._inc('leaves')
            elif self.state.four_selected >= self.m:
                next_frame = frame.cleared(DONE, close_reason=TARGET_NONLEAF)
                self._inc('target_closures')
            else:
                reason, row, domain = self._scan(check)
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
                    for _ in frame.pending:
                        self.state.pop()
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
                self.state.pop()
                self.frames, self.slice_index = [], next_index
                self.outer = BETWEEN if next_index < len(self.diagonals) else EXHAUSTED
            else:
                new_frames = self.frames[:-2]+[replace(self.frames[-2], phase=READY)]
                for _ in frame.incoming:
                    self.state.pop()
                self.frames = new_frames
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
            raise ValueError('tiny invocation node cap1..10000')
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
