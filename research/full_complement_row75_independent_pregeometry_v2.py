"""Source-only invalid-schema and seeded quota checks. No valid geometry."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'research/full_complement_row75_core.py': 'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b',
    'research/full_complement_row75_independent.py': 'c8fcea3629d5a4d3ccac5f92d925a3e88306fa3e747b40f109142d310dbe07e3',
}


def identities():
    found = {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in PINS}
    assert found == PINS
    return found


def main():
    before = identities()
    for path in PINS:
        source = (ROOT/path).read_text()
        ast.parse(source, filename=path)
        compile(source, path, 'exec')
    from research import full_complement_row75_core as core
    from research import full_complement_row75_independent as verifier
    # The already-approved n5 literal, used only for schema checks and no geometry.
    points = ((0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,1),(1,2),(1,3))
    fixture_sha = core.normalized_sha256(points, 5)
    assert fixture_sha == '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37'
    rows = tuple(tuple(x for x,y in points if y == row) for row in range(5))
    synthetic_costs = [[0]*5 for _ in range(5)]
    synthetic_records = [{'row': row, 'current': rows[row], 'best': rows[row], 'best_score': 14}
                         for row in range(5)]
    traps = []

    def forbidden(*args, **kwargs):
        traps.append(True)
        raise AssertionError('geometry forbidden during source-only schema tests')

    rejected = []
    with patch.object(verifier, '_endpoint_table', forbidden), \
            patch.object(verifier, 'direct_raw', forbidden), patch.object(verifier, 'endpoint_raw', forbidden):
        profile_mutations = []
        bad = deepcopy(synthetic_costs); bad[0][0] = True
        profile_mutations.append(('boolean_cost', bad, synthetic_records, 14))
        bad = deepcopy(synthetic_costs); bad[0][0] = -1
        profile_mutations.append(('negative_cost', bad, synthetic_records, 14))
        profile_mutations.append(('missing_cost_row', synthetic_costs[:-1], synthetic_records, 14))
        bad = deepcopy(synthetic_records); bad[0]['row'] = False
        profile_mutations.append(('boolean_row', synthetic_costs, bad, 14))
        bad = deepcopy(synthetic_records); bad[0]['current'] = (False, 1)
        profile_mutations.append(('boolean_current_column', synthetic_costs, bad, 14))
        bad = deepcopy(synthetic_records); bad[0]['best'] = (0, 0)
        profile_mutations.append(('duplicate_best_column', synthetic_costs, bad, 14))
        bad = deepcopy(synthetic_records); bad[0]['best_score'] = True
        profile_mutations.append(('boolean_best_score', synthetic_costs, bad, 14))
        profile_mutations.append(('boolean_baseline', synthetic_costs, synthetic_records, True))
        for name, costs, records, baseline in profile_mutations:
            budget = core.Budget()
            try:
                verifier.verify_profiles(points, 5, costs, records, baseline, budget)
            except verifier.VerificationError:
                assert not any(budget.counts.values())
                rejected.append(name)
            else:
                raise AssertionError('invalid profile accepted: '+name)
        candidate_mutations = [
            ('boolean_candidate_row', True, (0,1), 14),
            ('out_of_grid_candidate_row', 5, (0,1), 14),
            ('boolean_candidate_column', 0, (False,1), 14),
            ('duplicate_candidate_column', 0, (0,0), 14),
            ('mismatched_candidate_columns', 0, (0,2), 14),
            ('boolean_candidate_score', 0, (0,1), True),
        ]
        for name, row, columns, predicted in candidate_mutations:
            budget = core.Budget()
            try:
                verifier.verify_candidate(points, points, 5, row, columns, predicted, budget)
            except verifier.VerificationError:
                assert not any(budget.counts.values())
                rejected.append(name)
            else:
                raise AssertionError('invalid candidate accepted: '+name)
    assert not traps and len(rejected) == 14

    quota_stops = []
    for kind in ('pair_lines', 'intersections', 'recoveries', 'raw_triples'):
        budget = core.Budget()
        budget.counts[kind] = core.LIMITS[kind]
        prior = budget.snapshot()
        try:
            if kind == 'pair_lines':
                verifier._direction_line(object(), object(), budget, 'synthetic')
            elif kind == 'intersections':
                verifier._target_column(object(), object(), object(), budget, 'synthetic')
            elif kind == 'recoveries':
                verifier._endpoint_count(object(), object(), budget, 'synthetic')
            else:
                # Deliberate schema bypass with unusable sentinels, never a valid state.
                with patch.object(verifier, 'validate_points', lambda *args: ()):
                    verifier.direct_raw((object(), object(), object()), 5, budget, 'synthetic')
        except core.QuotaExceeded:
            assert budget.snapshot() == prior
            quota_stops.append(kind)
        else:
            raise AssertionError('operation touched exhausted synthetic quota: '+kind)
    # Fake scorers and a fake clock exercise ordering, never valid geometry.
    start_guard_checks = []
    for name, initial, direct_end, endpoint_end, success in (
            ('started_on_time_finishes_after_soft', 0, 24, 26, True),
            ('first_validator_starts_too_late', 25, 25, 26, False),
            ('second_validator_starts_too_late', 0, 25, 26, False),
            ('owned_deadline_still_enforced', 0, 24, 30, False)):
        clock = [initial]
        events = []
        def owned_check():
            if clock[0] >= 30:
                raise TimeoutError('synthetic owned deadline')
        def start_check():
            events.append('start_guard')
            if clock[0] >= 25:
                raise TimeoutError('synthetic start deadline')
        budget = core.Budget(owned_check)
        def fake_direct(*args):
            events.append('direct_stub')
            clock[0] = direct_end
            budget.charge('raw_triples', 'synthetic')
            return 0
        def fake_endpoint(*args):
            events.append('endpoint_stub')
            clock[0] = endpoint_end
            budget.charge('recoveries', 'synthetic')
            return 0
        passed = False
        with patch.object(verifier, 'direct_raw', fake_direct), patch.object(verifier, 'endpoint_raw', fake_endpoint):
            try:
                value = verifier.verify_candidate(points, points, 5, 0, (0,1), 0, budget,
                                                  validator_start=start_check)
                assert value['score'] == 0
                passed = True
            except TimeoutError:
                pass
        assert passed is success
        if name == 'first_validator_starts_too_late':
            assert events == ['start_guard']
        elif name == 'second_validator_starts_too_late':
            assert events == ['start_guard', 'direct_stub', 'start_guard']
        else:
            assert events == ['start_guard', 'direct_stub', 'start_guard', 'endpoint_stub']
        start_guard_checks.append({'case': name, 'expected_success': success, 'events': events,
                                   'synthetic_counter_totals': dict(budget.counts),
                                   'real_geometric_operations': 0})
    after = identities()
    evidence = {
        'passed': True,
        'scope': 'SOURCE-only syntax, invalid-schema rejection and exhausted-counter sentinels. No valid geometry.',
        'source_before': before, 'source_after': after,
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'approved_n5_literal_sha256': fixture_sha,
        'syntax_compile_passes': 2, 'invalid_schema_rejections': rejected,
        'geometry_trap_calls': len(traps), 'quota_refused_before_sentinel_access': quota_stops,
        'synthetic_validator_start_guards': start_guard_checks,
        'real_geometric_operations': 0,
    }
    raw = (json.dumps(evidence, sort_keys=True, indent=2)+'\n').encode('ascii')
    assert len(raw) <= 65536
    path = ROOT/'data/full-complement-row75-independent-pregeometry-v2.json'
    with path.open('xb') as output:
        output.write(raw)
    print(json.dumps({'passed': True, 'output': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                      'real_geometric_operations': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
