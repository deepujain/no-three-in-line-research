"""Tiny-only mathematical falsifier; not a production construction worker."""
from itertools import combinations
import hashlib
import json
from pathlib import Path
from research import row_block_independent_oracle as o


def tables(points, n, r, s):
    points = o.row_state(points, n)
    assert 0 <= r < s < n
    retained = tuple(p for p in points if p[1] not in (r, s))
    base = o.score(retained)[0]
    first = [o.score(retained+((x, r),))[0]-base for x in range(n)]
    second = [o.score(retained+((x, s),))[0]-base for x in range(n)]
    cross = [[0]*n for _ in range(n)]
    for x in range(n):
        for qx, qy in retained:
            denominator = qy-r
            numerator = x*denominator+(qx-x)*(s-r)
            if numerator % denominator == 0:
                y = numerator//denominator
                if 0 <= y < n:
                    cross[x][y] += 1
    for x in range(n):
        for y in range(n):
            assert cross[x][y] == sum(o.determinant((x, r), (y, s), p) == 0 for p in retained)
    return retained, base, first, second, cross


def optimize(points, n, r, s, ka, kb):
    retained, base, first, second, cross = tables(points, n, r, s)
    expected = []
    for a in combinations(range(n), ka):
        for b in combinations(range(n), kb):
            changed = retained+tuple((x, r) for x in a)+tuple((y, s) for y in b)
            direct = o.score(changed)[0]
            table = base+sum(first[x] for x in a)+sum(second[y] for y in b)+sum(cross[x][y] for x in a for y in b)
            assert table == direct
            expected.append((direct, a, b))
    candidates = []
    for a in combinations(range(n), ka):
        costs = [(second[y]+sum(cross[x][y] for x in a), y) for y in range(n)]
        chosen = sorted(costs)[:kb]
        b = tuple(sorted(y for cost, y in chosen))
        candidates.append((base+sum(first[x] for x in a)+sum(cost for cost, y in chosen), a, b))
    assert min(candidates) == min(expected)
    return min(candidates), len(expected)


def run():
    counts = {'states': 0, 'row_pairs': 0, 'load_orientations': 0, 'direct_assignments': 0}
    for n in (2, 3, 4):
        for ordinal, points in enumerate(o.states(n)):
            if n == 4 and ordinal % 107:
                continue
            counts['states'] += 1
            for r, s in combinations(range(n), 2):
                counts['row_pairs'] += 1
                total = sum(p[1] in (r, s) for p in points)
                for ka, kb in (((2, 2),) if total == 4 else ((1, 2), (2, 1))):
                    result, count = optimize(points, n, r, s, ka, kb)
                    counts['load_orientations'] += 1
                    counts['direct_assignments'] += count
    stuck = ((0, 0), (0, 1), (0, 2), (2, 1), (2, 3), (3, 2), (3, 3))
    assert o.score(stuck)[0] == 1
    one_row_minima = [min([1]+[a['U'] for a in o.row_alternatives(stuck, 4, row)]) for row in range(4)]
    assert one_row_minima == [1, 1, 1, 1]
    answer, _ = optimize(stuck, 4, 0, 1, 1, 2)
    assert answer[0] == 0
    changing = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 3))
    fixed, _ = optimize(changing, 4, 0, 1, 1, 2)
    swapped, _ = optimize(changing, 4, 0, 1, 2, 1)
    assert fixed[0] == 1 and swapped[0] == 0
    return {'scope': 'tiny-only mathematical reduction; no production or n75 geometry', 'counts': counts,
            'one_row_local_minimum': {'points': stuck, 'U': 1, 'row_minima': one_row_minima,
                                      'selected_rows': [0, 1], 'two_row_optimum': answer},
            'deficiency_orientation_falsifier': {'points': changing, 'rows': [0, 1],
                                                'fixed_orientation': fixed, 'swapped_orientation': swapped},
            'coverage': 'All n2/n3 row-valid states and every107th n4 state; all row pairs, both legal load orientations and all final assignments in each selected case.',
            'oracle_sha256': hashlib.sha256(Path(o.__file__).read_bytes()).hexdigest(),
            'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = run()
    output = Path('data/two-row-descent-independent-design-tiny.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True)); print(hashlib.sha256(output.read_bytes()).hexdigest())
