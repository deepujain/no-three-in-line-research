"""Synthetic n2..4 production census audit; never load the selected n76 source."""
import hashlib
from itertools import permutations
import json
from math import comb
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from research import occupied_contraction75 as implementation
from research.occupied_contraction_independent_tiny_audit import contract, score


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / 'research/occupied_contraction75.py'
    start_pin = digest(source)
    rows = []
    for n in (2, 3, 4):
        # Every full bipartite degree-two graph splits into two disjoint
        # matchings; construct the tiny universe differently from author tests.
        sources = set()
        perm = list(permutations(range(n)))
        for first in perm:
            for second in perm:
                if any(a == b for a, b in zip(first, second)):
                    continue
                sources.add(tuple(sorted([(x, first[x]) for x in range(n)]
                                         + [(x, second[x]) for x in range(n)])))
        counts = dict(n=n, sources=len(sources), cuts=0, occupied=0,
                      verified_obstructions=0, zero_occupied=0,
                      valid_sources=0, obstruction_cut_tests=0)
        for points in sorted(sources):
            counters = {}
            result, witnesses = implementation.census(points, n, counters=counters)
            assert counters['triples'] == comb(2 * n, 3)
            assert counters['rectangles'] <= 16 * counters['triples']
            assert counters['obstruction_cut_tests'] <= 2 * n * counters['zero_rectangles']
            assert counters['prefix_rows'] == n
            counts['obstruction_cut_tests'] += counters['obstruction_cut_tests']
            counts['valid_sources'] += score(points) == 0
            for c in range(n):
                for r in range(n):
                    image = contract(points, c, r)
                    expected = score(image)
                    assert result[c * (n + 1) + r] == expected
                    counts['cuts'] += 1
                    if (c, r) not in points:
                        assert (c, r) not in witnesses
                        continue
                    counts['occupied'] += 1
                    assert len(image) == len(set(image)) == 2 * n - 3
                    for axis in (0, 1):
                        assert sorted(sum(p[axis] == v for p in image)
                                      for v in range(n - 1)) == [1] + [2] * (n - 2)
                    assert ((c, r) in witnesses) == (expected > 0)
                    if not expected:
                        counts['zero_occupied'] += 1
                    else:
                        triple = witnesses[c, r]
                        assert len(set(triple)) == 3 and set(triple) <= set(points)
                        assert all(p[0] != c and p[1] != r for p in triple)
                        target = contract(triple, c, r)
                        assert len(set(target)) == 3 and score(target) == 1
                        counts['verified_obstructions'] += 1
        rows.append(counts)
    assert [r['sources'] for r in rows] == [1, 6, 90]
    counters = {}
    calls = 0

    def stop():
        nonlocal calls
        calls += 1
        if calls == 3:
            raise TimeoutError('synthetic census interruption')

    try:
        implementation.census([(0, 0), (0, 1), (1, 0), (1, 1)], 2, stop, counters)
    except TimeoutError:
        assert counters['triples'] == 2
    else:
        raise AssertionError('partial census returned')
    assert digest(source) == start_pin
    result = {
        'status': 'PASS_SYNTHETIC_ONLY', 'source_sha256': start_pin,
        'audit_source_sha256': digest(Path(__file__)), 'records': rows,
        'interruption': {'checker_calls': calls, 'partial_counters': counters, 'returned_census': False},
        'scope': 'Synthetic n2..4 only; no actual n76 fixture, contraction, validation, or allocation.',
    }
    (ROOT / 'data/occupied-contraction75-independent-tiny-audit.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
