"""Tiny-only reversible near-quarter orbit state, not a production search.

This prototype deliberately permits n3/n5/n7 only. It has no production DFS, solver,
checkpoint, CLI route, broad-grid run option, or n79 allocation path.
"""
from array import array
from math import gcd

from src.near_quarter_model import orbit_map


def grid_line(a,b,n):
    dx,dy = b[0]-a[0],b[1]-a[1]
    divisor = gcd(dx,dy)
    if divisor == 0:
        raise ValueError('line requires distinct points')
    dx,dy = dx//divisor,dy//divisor
    x,y = a
    while 0 <= x-dx < n and 0 <= y-dy < n:
        x,y = x-dx,y-dy
    while 0 <= x < n and 0 <= y < n:
        yield y*n+x
        x,y = x+dx,y+dy


class TinyOrbitState:
    """Secant counts plus exact row/column/family caps and rollback.

    blocked[cell] counts selected unordered pairs whose entire line contains
    cell, including pair endpoints. Only a fresh unoccupied point is queried.
    No global conflict, learned-clause, visited-state or line cache is retained.
    """
    def __init__(self,n):
        if type(n) is not int or n not in (3,5,7):
            raise ValueError('tiny prototype permits only n3/n5/n7')
        self.n = n
        self.model = orbit_map(n)
        self.blocked = array('H',[0])*(n*n)
        self.occupied = bytearray(n*n)
        self.rows = bytearray(n)
        self.columns = bytearray(n)
        self.points = []
        self.selected = []
        self.four_selected = self.diagonal_selected = 0

    def snapshot(self):
        return (self.blocked.tobytes(),bytes(self.occupied),bytes(self.rows),bytes(self.columns),
                tuple(self.points),tuple(self.selected),self.four_selected,self.diagonal_selected)

    def _remove_last_point(self):
        point = self.points.pop()
        x,y = point
        for other in self.points:
            for cell in grid_line(point,other,self.n):
                if self.blocked[cell] == 0:
                    raise RuntimeError('secant count underflow')
                self.blocked[cell] -= 1
        self.occupied[y*self.n+x] = 0
        self.rows[y] -= 1
        self.columns[x] -= 1

    def push(self,variable):
        if type(variable) is not int or not 1 <= variable <= len(self.model['orbits']):
            raise ValueError('invalid orbit variable')
        if variable in self.selected:
            return False
        four = variable <= self.model['four_count']
        if (four and self.four_selected >= self.n//2) or (not four and self.diagonal_selected >= 1):
            return False
        before = len(self.points)
        for point in self.model['orbits'][variable-1]:
            x,y = point
            cell = y*self.n+x
            if self.occupied[cell] or self.rows[y] >= 2 or self.columns[x] >= 2 or self.blocked[cell]:
                while len(self.points) > before:
                    self._remove_last_point()
                return False
            for other in self.points:
                for index in grid_line(point,other,self.n):
                    if self.blocked[index] == 65535:
                        raise RuntimeError('secant count overflow')
                    self.blocked[index] += 1
            self.points.append(point)
            self.occupied[cell] = 1
            self.rows[y] += 1
            self.columns[x] += 1
        self.selected.append(variable)
        if four:
            self.four_selected += 1
        else:
            self.diagonal_selected += 1
        return True

    def pop(self):
        if not self.selected:
            raise ValueError('empty orbit stack')
        variable = self.selected.pop()
        for _ in self.model['orbits'][variable-1]:
            self._remove_last_point()
        if variable <= self.model['four_count']:
            self.four_selected -= 1
        else:
            self.diagonal_selected -= 1

    def full_family_leaf(self):
        return (self.four_selected == self.n//2 and self.diagonal_selected == 1 and
                len(self.points) == 2*self.n and all(v == 2 for v in self.rows) and
                all(v == 2 for v in self.columns))


def tiny_mrv_traversal(n,*,diagonal_order=None,orbit_order=None,row_order=None,max_nodes=10000):
    """Tiny-only validation of diagonal-first/MRV branching and sound row bounds.

    This exhausts tiny fixture trees only; it provides no production worker or
    resumable checkpoint. Duplicated sets from different insertion orders are
    allowed. Permutation identity is explicit rather than an implicit default.
    """
    import hashlib
    import json
    from pathlib import Path
    from src.near_quarter_model import check_candidate
    state = TinyOrbitState(n)  # Hard n3/n5/n7 boundary also applies here.
    if type(max_nodes) is not int or not 1 <= max_nodes <= 10000:
        raise ValueError('tiny node ceiling must be in 1..10000')
    def permutation(values,expected):
        values = list(expected if values is None else values)
        if any(type(v) is not int for v in values) or sorted(values) != list(expected):
            raise ValueError('order must be an exact permutation of the declared domain')
        return values
    four = state.model['four_count']
    diagonals = permutation(diagonal_order,range(four+1,len(state.model['orbits'])+1))
    orbits = permutation(orbit_order,range(1,four+1))
    rows = permutation(row_order,range(n))
    row_rank = {row:i for i,row in enumerate(rows)}
    identity = {'version':'tiny-near-quarter-mrv-v1','n':n,'diagonal_order':diagonals,
                'orbit_order':orbits,'row_order':rows,
                'prune_policy':'top-r optimistic row reachability; no monotonic ID restriction',
                'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result = {'nodes':0,'full_leaf_visits':0,'unique_sets':[], 'status':'tiny_slices_exhausted',
              'row_shortfall_prunes':0,'orbit_shortfall_prunes':0,'identity':identity,
              'order_identity_sha256':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()}
    found = set()
    stopped = False
    def visit():
        nonlocal stopped
        if result['nodes'] >= max_nodes:
            stopped = True
            return
        result['nodes'] += 1
        if state.full_family_leaf():
            if not check_candidate(state.model,state.selected)['valid_full_witness']:
                raise RuntimeError('tiny full leaf failed dual validation')
            result['full_leaf_visits'] += 1
            found.add(tuple(sorted(state.selected)))
            return
        remaining = n//2-state.four_selected
        if remaining <= 0:
            return
        domains = {row:[] for row in rows if state.rows[row] < 2}
        contributions = {row:[] for row in domains}
        viable_count = 0
        before = state.snapshot()
        for variable in orbits:
            if state.push(variable):
                viable_count += 1
                orbit = state.model['orbits'][variable-1]
                for row in domains:
                    weight = sum(y == row for x,y in orbit)
                    if weight:
                        domains[row].append(variable)
                        contributions[row].append(weight)
                state.pop()
            if state.snapshot() != before:
                raise RuntimeError('MRV probe did not restore geometry and occupancy')
        if viable_count < remaining:
            result['orbit_shortfall_prunes'] += 1
            return
        for row,weights in contributions.items():
            if sum(sorted(weights,reverse=True)[:remaining]) < 2-state.rows[row]:
                result['row_shortfall_prunes'] += 1
                return
        row = min(domains,key=lambda r:(len(domains[r]),-(2-state.rows[r]),row_rank[r]))
        for variable in domains[row]:
            if stopped:
                return
            if not state.push(variable):
                raise RuntimeError('MRV admissibility changed without mutation')
            try:
                visit()
            finally:
                state.pop()
    for diagonal in diagonals:
        if not state.push(diagonal):
            raise RuntimeError('empty-state diagonal pair rejected')
        try:
            visit()
        finally:
            state.pop()
        if stopped:
            result['status'] = 'tiny_node_limit'
            break
    result['unique_sets'] = [list(ids) for ids in sorted(found)]
    return result
