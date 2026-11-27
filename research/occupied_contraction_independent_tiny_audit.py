"""Synthetic n2..4 only; independent determinant and rectangle-count oracle.

No production imports, actual witness reads, solver, or large-grid mode.
"""
from itertools import combinations
import hashlib
import json
from pathlib import Path


def determinant(t):
    a, b, c = t
    return ((b[0] - a[0]) * (c[1] - a[1])
            - (b[1] - a[1]) * (c[0] - a[0]))


def score(points):
    return sum(determinant(t) == 0 for t in combinations(sorted(points), 3))


def contract(points, column, row):
    return sorted((x - int(x > column), y - int(y > row))
                  for x, y in points if x != column and y != row)


def intervals(values, n):
    result = []
    lower = 0
    for value in sorted(set(values)):
        if lower < value:
            result.append((lower, value - 1))
        lower = value + 1
    if lower < n:
        result.append((lower, n - 1))
    return result


def rectangle_scores(points, n):
    diff = [[0] * (n + 1) for _ in range(n + 1)]
    examined = 0
    zero_rectangles = 0
    for triple in combinations(points, 3):
        for c0, c1 in intervals([p[0] for p in triple], n):
            for r0, r1 in intervals([p[1] for p in triple], n):
                examined += 1
                image = [(x - int(x > c0), y - int(y > r0))
                         for x, y in triple]
                if determinant(image) != 0:
                    continue
                zero_rectangles += 1
                diff[c0][r0] += 1
                diff[c1 + 1][r0] -= 1
                diff[c0][r1 + 1] -= 1
                diff[c1 + 1][r1 + 1] += 1
    for c in range(n):
        for r in range(n):
            diff[c][r] += ((diff[c - 1][r] if c else 0)
                           + (diff[c][r - 1] if r else 0)
                           - (diff[c - 1][r - 1] if c and r else 0))
    return [column[:n] for column in diff[:n]], examined, zero_rectangles


def main():
    records = []
    for n in (2, 3, 4):
        counts = dict(n=n, axis_full_sources=0, valid_sources=0,
                      contraction_scores_checked=0, occupied_axis_checks=0,
                      threshold_rectangles_examined=0,
                      zero_rectangles=0)
        board = [(x, y) for x in range(n) for y in range(n)]
        for points in combinations(board, 2 * n):
            if any(sum(p[a] == v for p in points) != 2
                   for a in (0, 1) for v in range(n)):
                continue
            counts['axis_full_sources'] += 1
            counts['valid_sources'] += score(points) == 0
            actual, examined, zeros = rectangle_scores(points, n)
            counts['threshold_rectangles_examined'] += examined
            counts['zero_rectangles'] += zeros
            for column in range(n):
                for row in range(n):
                    image = contract(points, column, row)
                    assert actual[column][row] == score(image)
                    counts['contraction_scores_checked'] += 1
                    if (column, row) in points:
                        assert len(image) == 2 * n - 3
                        for axis in (0, 1):
                            loads = [sum(p[axis] == v for p in image)
                                     for v in range(n - 1)]
                            assert sorted(loads) == [1] + [2] * (n - 2)
                        counts['occupied_axis_checks'] += 1
        records.append(counts)
    source = [(0, 0), (0, 1), (1, 2), (1, 3),
              (2, 0), (2, 1), (3, 2), (3, 3)]
    bad = contract(source, 1, 2)
    assert score(source) == 0 and score(bad) == 1
    result = {
        'status': 'PASS_SYNTHETIC_ONLY',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'records': records,
        'validity_preservation_counterexample': {
            'n': 4, 'source': source, 'occupied_cut': [1, 2],
            'contracted': bad, 'source_score': 0, 'contracted_score': 1,
            'new_triple': [[0, 0], [1, 1], [2, 2]],
        },
        'scope': 'No actual source points, n75/n77/n79 work, or solver execution.',
    }
    target = Path(__file__).resolve().parent.parent / 'data' / 'occupied-contraction-independent-tiny-audit.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
