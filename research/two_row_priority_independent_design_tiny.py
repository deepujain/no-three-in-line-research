"""Tiny-only line-incidence priority proof check against direct triples."""
from itertools import combinations
import hashlib
import json
from math import comb
from pathlib import Path
from research import row_block_independent_oracle as o


def run():
    counts = {'states': 0, 'row_incidences': 0, 'row_pair_unions': 0, 'zero_union_pairs': 0}
    for n in (2, 3, 4):
        for points in o.states(n):
            counts['states'] += 1
            conflicts = o.triples(points)
            incidence = [0]*n
            joint = {(r, s): 0 for r, s in combinations(range(n), 2)}
            for members in o.expected_index(points, n).values():
                t = len(members)
                if t < 3:
                    continue
                rows = sorted(p[1] for p in members)
                assert len(set(rows)) == t
                for row in rows:
                    incidence[row] += comb(t-1, 2)
                for r, s in combinations(rows, 2):
                    joint[r, s] += t-2
            for r in range(n):
                assert incidence[r] == sum(any(p[1] == r for p in tri) for tri in conflicts)
                counts['row_incidences'] += 1
            assert sum(incidence) == 3*len(conflicts)
            for r, s in combinations(range(n), 2):
                removed = incidence[r]+incidence[s]-joint[r, s]
                exact = sum(any(p[1] in (r, s) for p in tri) for tri in conflicts)
                assert removed == exact
                retained = tuple(p for p in points if p[1] not in (r, s))
                assert o.score(retained)[0] == len(conflicts)-removed
                counts['row_pair_unions'] += 1
                counts['zero_union_pairs'] += removed == 0
    return {'scope': 'all rowvalid n2..4 states; no actual n75 geometry or production implementation',
            'counts': counts, 'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'oracle_sha256': hashlib.sha256(Path(o.__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = run()
    output = Path('data/two-row-priority-independent-design-tiny.json')
    output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True)); print(hashlib.sha256(output.read_bytes()).hexdigest())
