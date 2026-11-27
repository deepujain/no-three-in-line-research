"""Pure tiny-only expectations for the new deterministic raw-descent worker.

No production imports, actual point fixtures, or orders outside2..4 are accepted.
Full pair optima use direct determinant enumeration, not the cubic algorithm.
"""
from itertools import combinations
from research import row_block_independent_oracle as geometry
from research import two_row_descent_independent_design_tiny as design


def raw(points):
    return len(geometry.triples(points))


def priorities(points, n):
    points = geometry.row_state(points, n)
    triples = geometry.triples(points)
    row_sets = [set(p[1] for p in t) for t in triples]
    incidence = tuple(sum(r in rows for rows in row_sets) for r in range(n))
    joint = {(r, s): sum(r in rows and s in rows for rows in row_sets)
             for r, s in combinations(range(n), 2)}
    removed = {(r, s): sum(r in rows or s in rows for rows in row_sets)
               for r, s in combinations(range(n), 2)}
    rows = tuple(sorted((r for r in range(n) if incidence[r]), key=lambda r: (-incidence[r], r)))
    pairs = tuple(sorted((pair for pair, count in removed.items() if count),
                         key=lambda pair: (-removed[pair], *pair)))
    return {'I': incidence, 'J': joint, 'M': removed, 'rows': rows, 'pairs': pairs}


def row_optimum(points, n, row):
    points = geometry.row_state(points, n)
    retained = tuple(p for p in points if p[1] != row)
    count = len(points)-len(retained)
    result = min((raw(retained+tuple((x, row) for x in cols)), cols)
                 for cols in combinations(range(n), count))
    changed = tuple(sorted(retained+tuple((x, row) for x in result[1])))
    return {'minimum': result, 'points': changed, 'strict': result[0] < raw(points)}


def merged_outer(n, total):
    assert type(n) is int and 2 <= n <= 4 and total in (3, 4)
    for x in range(n):
        if total == 3:
            yield (x,)
        for y in range(x+1, n):
            yield (x, y)


def pair_assignments(points, n, r, s):
    points = geometry.row_state(points, n)
    assert 0 <= r < s < n
    retained = tuple(p for p in points if p[1] not in (r, s))
    total = len(points)-len(retained)
    # Independently construct/sort the union; do not rely on merged_outer.
    sizes = (2,) if total == 4 else (1, 2)
    outer = sorted(cols for count in sizes for cols in combinations(range(n), count))
    for a in outer:
        for b in combinations(range(n), total-len(a)):
            changed = tuple(sorted(retained+tuple((x, r) for x in a)+tuple((y, s) for y in b)))
            yield (raw(changed), a, b), changed


def pair_optimum(points, n, r, s):
    minimum, changed = min(pair_assignments(points, n, r, s), key=lambda result: result[0])
    return {'minimum': minimum, 'points': changed, 'strict': minimum[0] < raw(points)}


def cubic_design_result(points, n, r, s):
    """Check the mathematical reduction against the fully independent optimum."""
    retained, base, first, second, cross = design.tables(points, n, r, s)
    total = len(points)-len(retained)
    best = None; first_zero = None; outer_count = 0
    for a in merged_outer(n, total):
        outer_count += 1
        costs = [(second[y]+sum(cross[x][y] for x in a), y) for y in range(n)]
        selected = sorted(costs)[:total-len(a)]
        b = tuple(sorted(y for score, y in selected))
        candidate = (base+sum(first[x] for x in a)+sum(score for score, y in selected), a, b)
        if best is None or candidate < best:
            best = candidate
        if candidate[0] == 0 and first_zero is None:
            first_zero = candidate
    return {'minimum': best, 'first_zero': first_zero, 'outer_count': outer_count,
            'partner_visits': outer_count*n}


def reference_descent(points, n, row_cap=512, pair_cap=32):
    """Complete tiny fixed policy, including current eligibility and shared caps."""
    current = geometry.row_state(points, n)
    row_started = pair_started = accepted = 0
    events = []
    while raw(current):
        ranks = priorities(current, n)
        improved = False
        for row in ranks['rows']:
            if row_started == row_cap:
                return {'points': current, 'U': raw(current), 'row_started': row_started,
                        'pair_started': pair_started, 'accepted': accepted, 'status': 'row_cap', 'events': events}
            row_started += 1
            result = row_optimum(current, n, row)
            events.append(('row', row, result['minimum'], result['strict']))
            if result['strict']:
                assert raw(result['points']) < raw(current)
                current = result['points']; accepted += 1; improved = True
                break
        if improved:
            continue
        for r, s in ranks['pairs']:
            if pair_started == pair_cap:
                return {'points': current, 'U': raw(current), 'row_started': row_started,
                        'pair_started': pair_started, 'accepted': accepted, 'status': 'pair_cap', 'events': events}
            pair_started += 1
            result = pair_optimum(current, n, r, s)
            events.append(('pair', (r, s), result['minimum'], result['strict']))
            if result['strict']:
                assert raw(result['points']) < raw(current)
                current = result['points']; accepted += 1; improved = True
                break
        if not improved:
            return {'points': current, 'U': raw(current), 'row_started': row_started,
                    'pair_started': pair_started, 'accepted': accepted,
                    'status': 'no_strict_descent', 'events': events}
    return {'points': current, 'U': 0, 'row_started': row_started, 'pair_started': pair_started,
            'accepted': accepted, 'status': 'zero', 'events': events}
