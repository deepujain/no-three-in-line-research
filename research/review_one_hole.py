#!/usr/bin/env python3
"""Independently audit all one-deletion, 3-insertion extensions of n=78 seed."""
from collections import Counter
from itertools import combinations
import json
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
seed = [tuple(p) for p in json.loads((root / 'data/published-n78.json').read_text())['points']]

def collinear(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) == (b[1] - a[1]) * (c[0] - a[0])

assert len(seed) == len(set(seed)) == 156
assert all(0 <= x < 78 and 0 <= y < 78 for x, y in seed)
assert all(sum(x == i for x, _ in seed) == sum(y == i for _, y in seed) == 2 for i in range(78))
assert not any(collinear(*t) for t in combinations(seed, 3))
results = []
for dx in (0, 1):
    for dy in (0, 1):
        old = [(x + dx, y + dy) for x, y in seed]
        new_x = 78 if dx == 0 else 0
        new_y = 78 if dy == 0 else 0
        reasons = Counter()
        valid = []
        for hole in old:
            rest = [p for p in old if p != hole]
            additions = [(hole[0], new_y), (new_x, hole[1]), (new_x, new_y)]
            assert len(set(rest + additions)) == 158
            # Old triples are already clean. Classify a failure by the first
            # new point that lies on a line through two retained old points,
            # otherwise by a pair of new points collinear with an old point.
            if any(collinear(a, b, c) for a, b in combinations(rest, 2) for c in additions):
                reasons['one_new_two_old'] += 1
            elif any(collinear(a, b, c) for a, b in combinations(additions, 2) for c in rest):
                reasons['two_new_one_old'] += 1
            elif collinear(*additions):
                reasons['three_new'] += 1
            else:
                reasons['valid'] += 1
                valid.append({'removed': hole, 'added': additions, 'points': rest + additions})
        results.append({'offset': [dx, dy], 'new_column': new_x, 'new_row': new_y,
                        'candidates': len(old), 'first_failure_counts': dict(reasons),
                        'valid_count': len(valid), 'valid_witnesses': valid})
result = {'seed': 'data/published-n78.json',
          'seed_file_sha256': hashlib.sha256((root / 'data/published-n78.json').read_bytes()).hexdigest(),
          'seed_point_count': len(seed),
          'seed_triples_checked': 620620, 'seed_collinear_triples': 0,
          'grid_size': 79, 'candidate_description': 'Each corner translation of the full seed; delete one original point; add the forced new-row/new-column corner triple.',
          'total_candidates': sum(r['candidates'] for r in results),
          'total_valid': sum(r['valid_count'] for r in results), 'results': results}
(root / 'data/one-hole-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:result[k] for k in ('total_candidates','total_valid','results')}, indent=2))
