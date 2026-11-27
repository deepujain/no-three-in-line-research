"""Exercise the independent tiny oracle only; no production/source data imports."""
from dataclasses import asdict
import hashlib
import json
from math import comb
from pathlib import Path
import random
import time
from research import row_block_independent_oracle as oracle


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def run():
    started = time.monotonic()
    result = {'scope': 'independent synthetic oracle preparation only; no production comparisons',
              'states_by_n': {}, 'line_membership_pairs': 0, 'row_unary_cells': 0,
              'row_alternatives': 0, 'migrations': 0, 'weighted_states_by_n': {},
              'weighted_row_alternatives': 0, 'weighted_migrations': 0,
              'penalty_rank_fixture': None, 'forced_uphill_conflict_row_fixture': None,
              'four_point_line_fixture': None, 'tie_fixture': None}
    first_invalid = None
    valid_by_n = {}
    for n in (2, 3, 4):
        count = weighted_count = 0
        for ordinal, points in enumerate(oracle.states(n)):
            count += 1
            index = oracle.expected_index(points, n)
            u, w = oracle.score(points)
            assert u == w == sum(comb(len(members), 3) for members in index.values())
            if not u:
                valid_by_n.setdefault(n, points)
            else:
                first_invalid = first_invalid or (n, points)
            for key, members in index.items():
                a, b, c = key
                assert tuple(p for p in points if a*p[0] + b*p[1] == c) == members
                for p, q in __import__('itertools').combinations(members, 2):
                    assert oracle.line_key(p, q) == key
                    result['line_membership_pairs'] += 1
                if len(members) >= 4 and result['four_point_line_fixture'] is None:
                    result['four_point_line_fixture'] = {'n': n, 'points': points, 'line': key,
                                                         'members': members, 'triples_on_line': comb(len(members), 3)}
            conflict_rows = {p[1] for triple in oracle.triples(points) for p in triple}
            for row in range(n):
                costs = oracle.row_unary(points, n, row)
                assert len(costs) == n and min(costs) >= 0
                result['row_unary_cells'] += n
                alternatives = oracle.row_alternatives(points, n, row)
                result['row_alternatives'] += len(alternatives)
                if not alternatives:
                    assert n == 2 and u == 0
                    continue
                minimum = min(a['unary_sum'] for a in alternatives)
                best = tuple(a['added'] for a in alternatives if a['unary_sum'] == minimum)
                if len(best) > 1 and result['tie_fixture'] is None:
                    rng = random.Random(275149)
                    before = digest(rng.getstate())
                    draws = [rng.choice(best) for _ in range(8)]
                    result['tie_fixture'] = {'n': n, 'points': points, 'row': row, 'best': best,
                                             'seed': 275149, 'draws': draws,
                                             'rng_before_sha256': before, 'rng_after_sha256': digest(rng.getstate())}
                if row in conflict_rows and min(a['W'] for a in alternatives) > u and result['forced_uphill_conflict_row_fixture'] is None:
                    result['forced_uphill_conflict_row_fixture'] = {'n': n, 'points': points,
                        'row': row, 'old_U': u, 'best_distinct_U': min(a['W'] for a in alternatives)}
                if u and result['penalty_rank_fixture'] is None:
                    penalized = oracle.penalized_weights(points, {})
                    _, new_best = oracle.best_row_alternatives(points, n, row, penalized)
                    if new_best != best:
                        result['penalty_rank_fixture'] = {'n': n, 'points': points, 'row': row,
                            'old_best': best, 'new_best': new_best, 'U': u,
                            'W_before': u, 'W_after': oracle.score(points, penalized)[1],
                            'weights_after': [list(key)+( [value]) for key, value in sorted(penalized.items())]}
            for donor, destination, move in oracle.migrations(points, n):
                assert move['removal_delta'] + move['insertion_delta'] == move['delta']
                assert move['deficient_row'] == oracle.deficient_row(move['points'], n)
                result['migrations'] += 1
            # All n2/n3 states, and every107th n4 state: not the full weighted cross product.
            if n < 4 or ordinal % 107 == 0:
                weighted_count += 1
                weights = oracle.weighted_fixture(points, n)
                before = dict(weights)
                uw, ww = oracle.score(points, weights)
                assert uw == u and ww == sum(weights.get(key, 1)*comb(len(members), 3)
                                            for key, members in index.items())
                for row in range(n):
                    result['weighted_row_alternatives'] += len(oracle.row_alternatives(points, n, row, weights))
                for donor, destination, move in oracle.migrations(points, n, weights):
                    assert move['removal_delta'] + move['insertion_delta'] == move['delta']
                    result['weighted_migrations'] += 1
                updated = oracle.penalized_weights(points, weights)
                assert weights == before and oracle.score(points, updated)[1] == ww+u
        result['states_by_n'][str(n)] = count
        result['weighted_states_by_n'][str(n)] = weighted_count
    assert result['states_by_n'] == {'2': 4, '3': 81, '4': 3456}
    assert result['penalty_rank_fixture'] is not None and result['four_point_line_fixture'] is not None
    result['two_row_counterexample'] = oracle.two_row_counterexample()
    n, points = first_invalid
    cap_cases = 0
    for kwargs in ({'max_keys': 0}, {'max_weight': 1}):
        weights = {}
        try:
            oracle.penalized_weights(points, weights, **kwargs)
        except oracle.OracleCap:
            cap_cases += 1
        else:
            raise AssertionError('missing oracle cap rejection')
        assert weights == {}
    result['pure_cap_rejections'] = cap_cases
    result['reference_transactions'] = []
    for n in (3, 4):
        points = next(p for p in oracle.states(n) if oracle.score(p)[0])
        for step, stagnation in ((0, 0), (15, 0), (0, 31), (15, 31)):
            old = oracle.boundary(points, n, step=step, stagnation=stagnation,
                                  best_points=valid_by_n[n])
            before = asdict(old)
            new = oracle.reference_step(old)
            assert asdict(old) == before and new.step == step+1 and new.best_U == 0
            assert oracle.score(new.points, dict(new.weights)) == (new.U, new.W)
            record = {'n': n, 'step_before': step, 'stagnation_before': stagnation,
                      'old': before, 'new': asdict(new)}
            result['reference_transactions'].append(record)
    result['domain_rejections'] = 0
    for n in (1, 5, 75, 79, True):
        try:
            oracle.row_state(((0, 0),), n)
        except AssertionError:
            result['domain_rejections'] += 1
        else:
            raise AssertionError('oracle escaped tiny-only domain')
    result['elapsed_seconds'] = time.monotonic() - started
    result['oracle_sha256'] = hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest()
    result['preparation_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__ == '__main__':
    output = Path('data/row-block-independent-oracle-preparation.json')
    result = run()
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('reference_transactions', 'tie_fixture', 'penalty_rank_fixture',
                                     'four_point_line_fixture', 'forced_uphill_conflict_row_fixture')}, sort_keys=True))
    print(json.dumps({'forced_uphill_fixture_found': result['forced_uphill_conflict_row_fixture'] is not None,
                      'reference_transactions': len(result['reference_transactions']),
                      'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, sort_keys=True))
