"""Exhaustive n2..4 direct pair/minimum and bounded policy preparation."""
from itertools import combinations
import hashlib
import json
from pathlib import Path
import time
from research import two_row_descent_independent_oracle as oracle


def run():
    started = time.monotonic()
    counts = {'states': 0, 'row_optima': 0, 'row_pairs': 0, 'direct_assignments': 0,
              'zero_pair_optima': 0, 'policy_traces': 0, 'merged_streams': 0}
    outcome_counts = {}; trajectory_digest = hashlib.sha256()
    for n in (2, 3, 4):
        for total in (3, 4):
            expected = sorted(cols for k in ((2,) if total == 4 else (1, 2))
                              for cols in combinations(range(n), k))
            assert list(oracle.merged_outer(n, total)) == expected
            counts['merged_streams'] += 1
        for points in oracle.geometry.states(n):
            counts['states'] += 1
            old_u = oracle.raw(points)
            for row in range(n):
                result = oracle.row_optimum(points, n, row)
                assert result['minimum'][0] <= old_u
                counts['row_optima'] += 1
            for r, s in combinations(range(n), 2):
                candidates = list(oracle.pair_assignments(points, n, r, s))
                expected = min(candidates, key=lambda item: item[0])[0]
                reduced = oracle.cubic_design_result(points, n, r, s)
                assert reduced['minimum'] == expected
                assert expected[0] <= old_u
                if expected[0] == 0:
                    assert reduced['first_zero'] == expected
                    counts['zero_pair_optima'] += 1
                else:
                    assert reduced['first_zero'] is None
                counts['row_pairs'] += 1
                counts['direct_assignments'] += len(candidates)
            trace = oracle.reference_descent(points, n)
            assert trace['accepted'] <= old_u
            assert trace['U'] <= old_u
            outcome_counts[trace['status']] = outcome_counts.get(trace['status'], 0)+1
            trajectory_digest.update(json.dumps([n, points, trace], sort_keys=True, separators=(',', ':')).encode())
            counts['policy_traces'] += 1
    stuck = ((0, 0), (0, 1), (0, 2), (2, 1), (2, 3), (3, 2), (3, 3))
    fixtures = []
    for row_cap, pair_cap in ((512, 32), (0, 32), (2, 32), (3, 0), (3, 1)):
        trace = oracle.reference_descent(stuck, 4, row_cap, pair_cap)
        fixtures.append({'points': stuck, 'n': 4, 'row_cap': row_cap, 'pair_cap': pair_cap, 'result': trace})
    assert fixtures[0]['result']['U'] == 0 and fixtures[0]['result']['pair_started'] == 1
    assert fixtures[1]['result']['status'] == fixtures[2]['result']['status'] == 'row_cap'
    assert fixtures[3]['result']['status'] == 'pair_cap' and fixtures[4]['result']['U'] == 0
    return {'scope': 'Independent tiny oracle only; no production imports or actual n75 geometry.',
            'counts': counts, 'policy_outcomes': outcome_counts,
            'all_policy_trajectories_sha256': trajectory_digest.hexdigest(),
            'cap_and_two_row_fixtures': fixtures,
            'oracle_sha256': hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
            'preparation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'elapsed_seconds': time.monotonic()-started,
            'limits': 'The earlier design helper sampled n4 states; this separate preparation exhausts all row-valid n2..4 states and every legal final assignment in each selected pair. No statement about n75 success follows.'}


if __name__ == '__main__':
    result = run()
    output = Path('data/two-row-descent-independent-oracle-preparation.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'cap_and_two_row_fixtures'}, sort_keys=True))
    print(hashlib.sha256(output.read_bytes()).hexdigest())
