"""Pure fixed-pool Boolean projection and bounded streaming DIMACS IO."""
from collections import Counter
from dataclasses import dataclass
import hashlib
from itertools import combinations
import os
from pathlib import Path
import tempfile

CNF_BYTES = 1602603
MAX_VARIABLES = 2645
MAX_CLAUSES = 89957
MAX_LITERALS = 237112
MODEL_BYTES = 32768


@dataclass(frozen=True)
class Layout:
    arc_count: int
    pool_count: int
    old_count: int
    k: int

    def __post_init__(self):
        if any(type(v) is not int or v < 0 for v in
               (self.arc_count, self.pool_count, self.old_count, self.k)):
            raise ValueError('invalid layout')
        if not 1 <= self.k <= 8 or self.arc_count > 246 or self.pool_count > 64 or self.old_count > 157:
            raise ValueError('layout exceeds gate bounds')

    def x(self, i):
        if not 0 <= i < self.arc_count: raise ValueError('arc index')
        return i+1

    def q(self, i):
        if not 0 <= i < self.pool_count: raise ValueError('pool index')
        return self.arc_count+i+1

    def d(self, i):
        if not 0 <= i < self.old_count: raise ValueError('old index')
        return self.arc_count+self.pool_count+i+1

    def z(self, i, j):
        if j == 0: return True
        if i == 0 or j > i: return False
        if not 1 <= i <= self.arc_count or not 1 <= j <= self.k+1:
            raise ValueError('threshold index')
        width = self.k+1
        before = sum(min(t, width) for t in range(1, i))
        return self.arc_count+self.pool_count+self.old_count+before+j

    @property
    def variables(self):
        return self.arc_count+self.pool_count+self.old_count+sum(
            min(i, self.k+1) for i in range(1, self.arc_count+1))


def neg(term):
    return not term if type(term) is bool else -term


def simplify(terms):
    result = []; seen = set()
    for v in terms:
        if type(v) is bool:
            if v: return None
            continue
        if type(v) is not int or not v: raise ValueError('invalid literal')
        if -v in seen: return None
        if v not in seen: seen.add(v); result.append(v)
    return tuple(result)


def bits(mask):
    if type(mask) is not int or mask < 0: raise ValueError('invalid mask')
    while mask:
        low = mask & -mask; yield low.bit_length()-1; mask ^= low


def iter_clauses(A, pool, arcs, tables, old_conflict_masks, layout,
                 check=lambda: None, counters=None):
    if (len(A), len(pool), len(arcs)) != (layout.old_count, layout.pool_count, layout.arc_count):
        raise ValueError('layout/input mismatch')
    counts = counters if counters is not None else Counter()

    def emit(group, terms):
        counts[group+'_started'] = counts.get(group+'_started', 0)+1; check()
        clause = simplify(terms)
        counts[group+'_completed'] = counts.get(group+'_completed', 0)+1
        if clause is not None:
            if any(abs(v) > layout.variables for v in clause): raise ValueError('literal domain')
            return group, clause
        return None

    def raw():
        for i in range(1, len(arcs)+1):
            for j in range(1, min(i, layout.k+1)+1):
                a, b, z, x = layout.z(i-1, j), layout.z(i-1, j-1), layout.z(i, j), layout.x(i-1)
                for clause in ((neg(a), z), (-x, neg(b), z), (-z, a, x), (-z, a, b)):
                    yield 'threshold', clause
        yield 'threshold', (layout.z(len(arcs), layout.k),)
        yield 'threshold', (neg(layout.z(len(arcs), layout.k+1)),)
        for i, j in combinations(range(len(arcs)), 2):
            check()
            if arcs[i].rows & arcs[j].rows or arcs[i].cols & arcs[j].cols:
                yield 'incompatibility', (-layout.x(i), -layout.x(j))
        for p in range(len(pool)):
            support = []
            for i, arc in enumerate(arcs):
                check()
                if arc.pool == p:
                    support.append(layout.x(i)); yield 'q', (-layout.x(i), layout.q(p))
            yield 'q', (-layout.q(p), *support)
        for v in range(len(A)):
            support = []
            for i, arc in enumerate(arcs):
                check()
                if v in (arc.a, arc.b):
                    support.append(layout.x(i)); yield 'd', (-layout.x(i), layout.d(v))
            yield 'd', (-layout.d(v), *support)
        for mask in old_conflict_masks:
            yield 'old', tuple(layout.d(v) for v in bits(mask))
        for i, cell in enumerate(pool):
            for mask in cell.pairs:
                yield 'one_new', (-layout.q(i), *(layout.d(v) for v in bits(mask)))
        for i, j in combinations(range(len(pool)), 2):
            check(); old, new = tables[i, j]
            for v in bits(old): yield 'two_new', (-layout.q(i), -layout.q(j), layout.d(v))
            for k in bits(new):
                if k > j: yield 'all_new', (-layout.q(i), -layout.q(j), -layout.q(k))

    for group, terms in raw():
        item = emit(group, terms)
        if item is not None: yield item


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(65536): h.update(block)
    return h.hexdigest()


def write_cnf(path, A, pool, arcs, tables, old_conflict_masks, layout,
              check=lambda: None, counters=None):
    path = Path(path); fd, temp = tempfile.mkstemp(prefix='.cnf-body-', dir=path.parent)
    clauses = literals = size = 0; groups = Counter(); created = False
    try:
        with os.fdopen(fd, 'wb') as body:
            for group, clause in iter_clauses(A, pool, arcs, tables, old_conflict_masks, layout, check, counters):
                check(); encoded = (''.join(str(v)+' ' for v in clause)+'0\n').encode('ascii')
                clauses += 1; literals += len(clause); size += len(encoded); groups[group] += 1
                if clauses > MAX_CLAUSES or literals > MAX_LITERALS or size+17 > CNF_BYTES:
                    raise ValueError('CNF construction cap')
                body.write(encoded)
            body.flush(); os.fsync(body.fileno())
        header = f'p cnf {layout.variables} {clauses}\n'.encode('ascii')
        with path.open('xb') as final:
            created = True; final.write(header)
            with open(temp, 'rb') as body:
                while block := body.read(65536): check(); final.write(block)
            final.flush(); os.fsync(final.fileno())
        check()
        return {'variables': layout.variables, 'clauses': clauses, 'literals': literals,
                'bytes': size+len(header), 'sha256': digest(path), 'groups': dict(groups)}
    except BaseException:
        if created: path.unlink(missing_ok=True)
        raise
    finally:
        Path(temp).unlink(missing_ok=True)


def parse_model(raw, variables):
    if type(raw) is not str or len(raw.encode('ascii')) > MODEL_BYTES:
        raise ValueError('model format/size')
    tokens = raw.split()
    if len(tokens) != variables: raise ValueError('incomplete model')
    values = {}
    for token in tokens:
        if not token or token.lstrip('-').isdigit() is False or token.startswith('+'):
            raise ValueError('model token')
        v = int(token)
        if not 0 < abs(v) <= variables or abs(v) in values: raise ValueError('model domain/duplicate')
        values[abs(v)] = v > 0
    return values


def verify_model(values, A, pool, arcs, tables, conflicts, layout, check=lambda: None):
    if set(values) != set(range(1, layout.variables+1)) or any(type(v) is not bool for v in values.values()):
        raise ValueError('incomplete model map')
    for _, clause in iter_clauses(A, pool, arcs, tables, conflicts, layout, check):
        if not any(values[abs(v)] == (v > 0) for v in clause): raise ValueError('false model clause')
    return tuple(i for i in range(len(arcs)) if values[layout.x(i)])
