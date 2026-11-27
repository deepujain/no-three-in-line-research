"""Independent synthetic determinant oracle, with no production imports.

No published source or actual-grid fixture is read. This module defines expected
sets rather than reproducing rectangle masks, threshold partitions or clipping.
"""
from itertools import combinations, product
import hashlib
import json
from pathlib import Path


def collinear(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) == (c[0]-a[0])*(b[1]-a[1])


def triples(points):
    return {ijk for ijk in combinations(range(len(points)), 3)
            if collinear(*(points[i] for i in ijk))}


def full_axis_sources(n):
    """Enumerate binary row choices, independently of permutation decompositions."""
    choices = tuple(combinations(range(n), 2))
    for rows in product(choices, repeat=n):
        if any(sum(c in row for row in rows) != 2 for c in range(n)):
            continue
        points = tuple((c, r) for r, columns in enumerate(rows) for c in columns)
        if not triples(points):
            yield points


def inserted_target(points, n, gap):
    """Build the target using explicit ordered coordinate alphabets."""
    c, r = gap
    columns = tuple(k for k in range(n+1) if k != c)
    rows = tuple(k for k in range(n+1) if k != r)
    return tuple((columns[x], rows[y]) for x, y in points) + ((c, r),)


def excluded(n, gap):
    return gap[0] in (0, n) and gap[1] in (0, n)


def expected_gaps(points, n):
    """Return literal tuple-keyed expected sets; no encoded bit arithmetic."""
    result = {}
    for gap in product(range(n+1), repeat=2):
        target = inserted_target(points, n, gap)
        conflicts = triples(target)
        result[gap] = {
            'excluded': excluded(n, gap),
            'valid': not conflicts,
            'old': {ijk for ijk in conflicts if ijk[-1] < len(points)},
            'new': {ijk[:2] for ijk in conflicts if ijk[-1] == len(points)},
            'target': target,
        }
    return result


def rectangle_cells(rect):
    c0, c1, r0, r1 = rect
    return {(c, r) for c in range(c0, c1+1) for r in range(r0, r1+1)}


def line_cells(p, q, rect):
    """Brute force determinant oracle; no gcd, division or signed clipping."""
    assert p != q
    return {z for z in rectangle_cells(rect) if collinear(p, q, z)}


def line_cases():
    """All slopes/signs, zero components, outside endpoints and narrow bounds."""
    endpoints = tuple(product(range(-1, 3), repeat=2))
    intervals = tuple(combinations(range(-1, 4), 2)) + tuple((v, v) for v in range(-1, 4))
    for p, q in combinations(endpoints, 2):
        for c0, c1 in intervals:
            for r0, r1 in intervals:
                rect = (c0, c1, r0, r1)
                expected = line_cells(p, q, rect)
                yield p, q, rect, expected
                yield q, p, rect, expected


def check_certificate(points, n, gap, kind, indices):
    """Check actual membership and mapped determinant of a worker certificate."""
    assert not excluded(n, gap)
    assert kind in ('old', 'new')
    assert len(indices) == (3 if kind == 'old' else 2)
    assert len(set(indices)) == len(indices)
    assert all(type(i) is int and 0 <= i < len(points) for i in indices)
    target = inserted_target(points, n, gap)
    witnesses = tuple(target[i] for i in indices)
    if kind == 'new':
        witnesses += (target[-1],)
    assert len(set(witnesses)) == 3 and collinear(*witnesses)


def self_audit():
    counts = {'sources': 0, 'targets': 0, 'included_targets': 0, 'excluded_targets': 0,
              'valid_included': 0, 'old_obstructed': 0, 'new_obstructed': 0,
              'certificate_checks': 0, 'line_cases': 0}
    by_n = {}
    for n in (2, 3, 4):
        sources = list(full_axis_sources(n)); by_n[n] = len(sources)
        assert len(sources) == len(set(sources))
        for points in sources:
            counts['sources'] += 1
            assert len(points) == 2*n and len(set(points)) == 2*n
            for gap, expected in expected_gaps(points, n).items():
                counts['targets'] += 1
                target = expected['target']; c, r = gap
                assert len(target) == 2*n+1 and len(set(target)) == 2*n+1
                for axis, inserted in ((0, c), (1, r)):
                    assert [sum(p[axis] == v for p in target) for v in range(n+1)] == [1 if v == inserted else 2 for v in range(n+1)]
                if expected['excluded']:
                    counts['excluded_targets'] += 1
                    continue
                counts['included_targets'] += 1
                counts['valid_included'] += expected['valid']
                counts['old_obstructed'] += bool(expected['old'])
                counts['new_obstructed'] += bool(expected['new'])
                for kind in ('old', 'new'):
                    for indices in expected[kind]:
                        check_certificate(points, n, gap, kind, indices)
                        counts['certificate_checks'] += 1
                assert expected['valid'] == (not expected['old'] and not expected['new'])
    for p, q, rect, expected in line_cases():
        counts['line_cases'] += 1
        assert expected == line_cells(q, p, rect)
        assert expected <= rectangle_cells(rect)
    return {'passed': True, 'source_counts_by_n': by_n, 'counts': counts,
            'scope': 'Synthetic oracle preparation/self-consistency only; no production worker comparison, actual source or actual-grid computation.'}


if __name__ == '__main__':
    result = self_audit()
    result['oracle_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    root = Path(__file__).resolve().parents[1]
    (root / 'data/nonuniform-insertion-independent-oracle-preparation.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, indent=2, sort_keys=True))
