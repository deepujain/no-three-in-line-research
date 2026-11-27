"""Isolated bounded near-quarter geometry, not integrated with a search worker.

Grid arithmetic supports odd n3..79; tests instantiate n3/n5/n7 only. Each
budget stop reverses incomplete point/orbit additions. Inverses latch stops,
finish, and leave propagation to the owner after its frontier commit.
"""
from array import array
from dataclasses import dataclass
import hashlib
from math import gcd
import struct


class PackedStop(Exception):
    """Cooperative deadline/cancellation; state is coherent before propagation."""


class PackedStateError(RuntimeError):
    """Fatal consistency error: poisoned state cannot be adopted or continued."""


MAX_U64 = (1 << 64)-1
POINT_PRECHECK, LINE_BUILD, CELL_UPDATE, POINT_COMMIT, ORBIT_COMMIT = range(1, 6)
PUSH, POP = 1, 2


def packed_bounds(n):
    if type(n) is not int or not 3 <= n <= 79 or n % 2 != 1:
        raise ValueError('packed state permits odd grids3..79')
    m = n//2
    return {'m': m, 'four': m*m, 'diagonal': m, 'orbits': m*m+m,
            'incidences': 4*m*m+2*m, 'cells': n*n, 'points': 2*n, 'selected': m+1,
            'pair_count': n*(2*n-1)}


def line_span(a, b, n, check=lambda: None):
    """Maximal primitive grid line as start cell, signed cell step, cell count."""
    ax, ay = a % n, a//n
    bx, by = b % n, b//n
    dx, dy = bx-ax, by-ay
    divisor = gcd(dx, dy)
    if divisor == 0:
        raise PackedStateError('pair line requires distinct cells')
    dx, dy = dx//divisor, dy//divisor
    while 0 <= ax-dx < n and 0 <= ay-dy < n:
        check()
        ax, ay = ax-dx, ay-dy
    start, length = ay*n+ax, 0
    while 0 <= ax < n and 0 <= ay < n:
        check()
        length += 1
        ax, ay = ax+dx, ay+dy
    return start, dy*n+dx, length


class PackedOrbitView:
    """Read-only coordinate view; each access materializes at most four pairs."""
    __slots__ = ('_n', '_cells', '_offsets')

    def __init__(self, n, cells, offsets):
        self._n, self._cells, self._offsets = n, cells, offsets

    def __len__(self):
        return len(self._offsets)-1

    def __getitem__(self, index):
        if type(index) is not int:
            raise TypeError('orbit index must be an integer')
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError('orbit index outside map')
        return tuple((self._cells[i] % self._n, self._cells[i]//self._n)
                     for i in range(self._offsets[index], self._offsets[index+1]))

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


@dataclass
class PointProgress:
    cell: int
    stage: int = POINT_PRECHECK
    previous_index: int = 0
    line_start: int = 0
    line_step: int = 0
    line_length: int = 0
    next_cell: int = 0

    def record(self):
        return (self.cell, self.stage, self.previous_index, self.line_start,
                self.line_step, self.line_length, self.next_cell)


class PackedOrbitState:
    def __init__(self, n, *, check=lambda: None):
        bounds = packed_bounds(n)  # Must precede all n-dependent allocation.
        if array('H').itemsize != 2:
            raise ValueError('packed geometry requires two-byte unsigned H')
        check()
        self.n, self.bounds = n, bounds
        self._check = check
        self._poisoned = False
        self._operation = 0
        self._orbit_entry = 0
        self._orbit_phase = 0
        self._progress = None
        self._latched_stop = None
        self._inverse_error = None
        self._inverse_failed = False
        self.work = dict.fromkeys(('point_attempts', 'pair_lines', 'cell_increments',
            'inverse_cells', 'points_undone', 'orbit_attempts', 'rejected_orbits', 'aborted_orbits'), 0)
        self._orbit_cells, self._orbit_offsets = self._build_model(check)
        self.model = {'n': n, 'four_count': bounds['four'], 'diagonal_count': bounds['diagonal'],
                      'orbits': PackedOrbitView(n, self._orbit_cells, self._orbit_offsets)}
        self.blocked = array('H', [0])*bounds['cells']
        self.occupied = bytearray(bounds['cells'])
        self.rows, self.columns = bytearray(n), bytearray(n)
        self._point_cells = array('H', [0])*bounds['points']
        self._selected_ids = array('H', [0])*bounds['selected']
        self._point_count = self._selected_count = 0
        self.four_selected = self.diagonal_selected = 0
        self.map_digest = self._map_digest(check)
        check()

    def _build_model(self, check):
        n, four = self.n, set()
        for x in range(n):
            for y in range(n):
                check()
                if x == y or x+y == n-1:
                    continue
                orbit = tuple(sorted(((x, y), (y, n-1-x), (n-1-x, n-1-y), (n-1-y, x))))
                if orbit not in four and len(four) == self.bounds['four']:
                    raise PackedStateError('orbit bound exceeded')
                four.add(orbit)
        def sort_key(orbit):
            check()
            return orbit
        check()
        ordered = sorted(four, key=sort_key)
        check()
        if len(ordered) != self.bounds['four']:
            raise PackedStateError('orbit census differs from grid bound')
        del four
        cells = array('H', [0])*self.bounds['incidences']
        offsets = array('H', [0])*(self.bounds['orbits']+1)
        position = 0
        for i in range(self.bounds['orbits']):
            check()
            orbit = ordered[i] if i < len(ordered) else (
                (i-len(ordered), i-len(ordered)), (n-1-(i-len(ordered)), n-1-(i-len(ordered))))
            for x, y in orbit:
                check()
                cells[position] = y*n+x
                position += 1
            offsets[i+1] = position
        if position != len(cells):
            raise PackedStateError('packed incidence count mismatch')
        return cells, offsets

    def _map_digest(self, check):
        hasher = hashlib.sha256(b'NQRB-MAP-v1\0')
        hasher.update(struct.pack('>HH', self.n, self.bounds['orbits']))
        for orbit in self.model['orbits']:
            check()
            hasher.update(bytes((len(orbit),)))
            for x, y in orbit:
                check()
                hasher.update(struct.pack('>HH', x, y))
        return hasher.digest()

    @property
    def points(self):
        return tuple((self._point_cells[i] % self.n, self._point_cells[i]//self.n)
                     for i in range(self._point_count))

    @property
    def selected(self):
        return tuple(self._selected_ids[i] for i in range(self._selected_count))

    @property
    def poisoned(self):
        return self._poisoned

    @property
    def stop_latched(self):
        return self._latched_stop is not None

    def _usable(self, *, allow_latched=False):
        if self._poisoned:
            raise PackedStateError('packed state is poisoned')
        if self._operation or self._progress is not None:
            raise PackedStateError('operation already active')
        if self._latched_stop is not None and not allow_latched:
            raise self._latched_stop

    def bind_check(self, check):
        self._usable()
        if not callable(check):
            raise ValueError('budget check must be callable')
        self._check = check

    def raise_latched(self):
        stop = self._latched_stop
        self._latched_stop = None
        if stop is not None:
            raise stop

    def assert_checkpointable(self):
        self._usable()
        if self._orbit_phase or self._orbit_entry or self._inverse_error is not None:
            raise PackedStateError('pending transaction metadata')
        return True

    def snapshot(self):
        """Geometry identity; physical work/deadline functions are not tree state."""
        return (self.blocked.tobytes(), bytes(self.occupied), bytes(self.rows), bytes(self.columns),
                self._point_cells.tobytes(), self._selected_ids.tobytes(),
                self._point_count, self._selected_count, self.four_selected, self.diagonal_selected,
                self._poisoned, self._operation, self._orbit_entry, self._orbit_phase,
                None if self._progress is None else self._progress.record(),
                self._latched_stop is not None, self._inverse_error is not None, self._inverse_failed)

    def _work_inc(self, name):
        value = self.work[name]
        if type(value) is not int or not 0 <= value < MAX_U64:
            self._poisoned = True
            raise PackedStateError('physical counter overflow/type fault')
        self.work[name] = value+1

    def _increment(self, cell):
        if self.blocked[cell] == 65535:
            self._poisoned = True
            raise PackedStateError('secant counter overflow')
        self._work_inc('cell_increments')
        self.blocked[cell] += 1

    def _decrement(self, cell):
        if self.blocked[cell] == 0:
            self._poisoned = True
            raise PackedStateError('secant counter underflow')
        self._work_inc('inverse_cells')
        self.blocked[cell] -= 1

    def _poll_inverse(self):
        try:
            self._check()
        except PackedStop as stop:
            if self._latched_stop is None:
                self._latched_stop = stop
        except BaseException as error:
            self._poisoned = True
            if self._inverse_error is None:
                self._inverse_error = error

    def _raise_inverse_error(self):
        if self._inverse_error is not None:
            raise PackedStateError('unexpected inverse polling failure') from self._inverse_error

    def _undo_progress(self):
        progress = self._progress
        if progress is None:
            return
        while progress.next_cell:
            self._poll_inverse()
            cell = progress.line_start+(progress.next_cell-1)*progress.line_step
            self._decrement(cell)
            progress.next_cell -= 1
        for i in range(progress.previous_index-1, -1, -1):
            start, step, length = line_span(progress.cell, self._point_cells[i], self.n, self._poll_inverse)
            for j in range(length):
                self._poll_inverse()
                self._decrement(start+j*step)
            progress.previous_index = i
        self._progress = None

    def _remove_last_point(self):
        count = self._point_count
        if count == 0:
            self._poisoned = True
            raise PackedStateError('point stack underflow')
        point = self._point_cells[count-1]
        for i in range(count-1):
            start, step, length = line_span(point, self._point_cells[i], self.n, self._poll_inverse)
            for j in range(length):
                self._poll_inverse()
                self._decrement(start+j*step)
        x, y = point % self.n, point//self.n
        if not self.occupied[point] or not self.rows[y] or not self.columns[x]:
            self._poisoned = True
            raise PackedStateError('point metadata underflow')
        self.occupied[point] = 0
        self.rows[y] -= 1
        self.columns[x] -= 1
        self._point_cells[count-1] = 0
        self._point_count = count-1
        self._work_inc('points_undone')

    def _unwind(self, entry):
        if self._inverse_failed:
            raise PackedStateError('inverse already failed; no retry')
        try:
            self._undo_progress()
            while self._point_count > entry:
                self._remove_last_point()
            self._raise_inverse_error()
        except BaseException:
            self._poisoned = self._inverse_failed = True
            raise

    def _insert_point(self, cell):
        self._work_inc('point_attempts')
        self._check()
        x, y = cell % self.n, cell//self.n
        if self.occupied[cell] or self.rows[y] >= 2 or self.columns[x] >= 2 or self.blocked[cell]:
            return False
        if self._point_count >= self.bounds['points']:
            self._poisoned = True
            raise PackedStateError('point stack capacity exceeded')
        progress = PointProgress(cell)
        self._progress = progress
        self._check()
        for i in range(self._point_count):
            progress.stage = LINE_BUILD
            self._check()
            start, step, length = line_span(cell, self._point_cells[i], self.n, self._check)
            progress.line_start, progress.line_step, progress.line_length = start, step, length
            progress.next_cell = 0
            self._work_inc('pair_lines')
            for j in range(length):
                progress.stage = CELL_UPDATE
                self._check()
                self._increment(start+j*step)
                progress.next_cell = j+1
            progress.previous_index = i+1
            progress.next_cell = 0
        progress.stage = POINT_COMMIT
        self._check()  # Includes after-last-cell and before-metadata stop boundary.
        self._point_cells[self._point_count] = cell
        self._point_count += 1
        self.occupied[cell] = 1
        self.rows[y] += 1
        self.columns[x] += 1
        self._progress = None
        return True

    def push(self, variable):
        self._usable()
        if type(variable) is not int or not 1 <= variable <= self.bounds['orbits']:
            raise ValueError('invalid packed orbit ID')
        self._check()
        four = variable <= self.bounds['four']
        if (variable in self.selected or (four and self.four_selected >= self.bounds['m']) or
                (not four and self.diagonal_selected >= 1)):
            return False
        if self._selected_count >= self.bounds['selected']:
            self._poisoned = True
            raise PackedStateError('selected-orbit capacity exceeded')
        self._work_inc('orbit_attempts')
        entry = self._point_count
        self._operation, self._orbit_entry, self._orbit_phase = PUSH, entry, POINT_PRECHECK
        try:
            for index in range(self._orbit_offsets[variable-1], self._orbit_offsets[variable]):
                if not self._insert_point(self._orbit_cells[index]):
                    self._unwind(entry)
                    self._work_inc('rejected_orbits')
                    self.raise_latched()
                    return False
            self._orbit_phase = ORBIT_COMMIT
            self._check()
            self._selected_ids[self._selected_count] = variable
            self._selected_count += 1
            if four:
                self.four_selected += 1
            else:
                self.diagonal_selected += 1
            return True
        except PackedStop:
            self._work_inc('aborted_orbits')
            self._unwind(entry)
            self._latched_stop = None  # The stop is propagated by this push.
            raise
        except BaseException:
            self._poisoned = True
            if not self._inverse_failed:
                self._unwind(entry)
            raise
        finally:
            self._operation = self._orbit_entry = self._orbit_phase = 0

    def pop(self, *, rollback=False):
        if type(rollback) is not bool:
            raise ValueError('rollback selector must be bool')
        self._usable(allow_latched=rollback)
        if not self._selected_count:
            raise ValueError('empty packed orbit stack')
        if not rollback:
            self._check()  # A stop before mutation leaves the child frontier intact.
        variable = self._selected_ids[self._selected_count-1]
        self._operation = POP
        self._orbit_entry = self._point_count-(self._orbit_offsets[variable]-self._orbit_offsets[variable-1])
        try:
            while self._point_count > self._orbit_entry:
                self._remove_last_point()
            self._selected_ids[self._selected_count-1] = 0
            self._selected_count -= 1
            if variable <= self.bounds['four']:
                self.four_selected -= 1
            else:
                self.diagonal_selected -= 1
            self._raise_inverse_error()
        except BaseException:
            self._poisoned = self._inverse_failed = True
            raise
        finally:
            self._operation = self._orbit_entry = self._orbit_phase = 0
        # A latched PackedStop is deliberately not raised until frontier commit.
        return variable

    def rollback_last_orbit(self):
        """Finish owner rollback even with an already expired/latched budget."""
        return self.pop(rollback=True)

    def full_family_leaf(self):
        return (not self._poisoned and not self._operation and self._progress is None and
                self.four_selected == self.bounds['m'] and self.diagonal_selected == 1 and
                self._point_count == self.bounds['points'] and
                all(v == 2 for v in self.rows) and all(v == 2 for v in self.columns))
