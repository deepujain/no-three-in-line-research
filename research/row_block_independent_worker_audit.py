"""Frozen production versus independent tiny oracle; never runs actual CLI."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import time
from research import row_block_independent_oracle as oracle
from research import row_block_breakout75 as worker

EXPECTED = 'ee8a78e0f199f2a2f52e2bc37530c12a05c6b54a978f31371b05d9558cd51e0f'


def tree(value):
    return tuple(tree(v) for v in value) if isinstance(value, list) else value


def make_old(record):
    ref = oracle.Boundary(**{k: tree(v) for k, v in record.items()})
    rng = random.Random(); rng.setstate(ref.rng_state)
    boundary = worker.make_boundary(ref.points, ref.n, rng, weights=dict(ref.weights))
    logical = dict(boundary.logical)
    logical.update(transitions=ref.step, row_transitions=ref.step, penalty_events=ref.penalties)
    boundary = replace(boundary, best_points=ref.best_points, best_unweighted=ref.best_U,
                       best_weighted_at_capture=oracle.score(ref.best_points, dict(ref.weights))[1],
                       stagnation=ref.stagnation, logical=logical)
    return ref, boundary, rng


def assert_boundary(actual, expected):
    assert actual.points == expected.points and actual.weights == dict(expected.weights)
    assert (actual.unweighted, actual.weighted) == (expected.U, expected.W)
    assert actual.best_points == expected.best_points and actual.best_unweighted == expected.best_U
    assert actual.logical['transitions'] == expected.step
    assert actual.logical['penalty_events'] == expected.penalties
    assert actual.stagnation == expected.stagnation and actual.rng_state == expected.rng_state
    assert actual.deficient_row == oracle.deficient_row(actual.points, actual.n)


def fingerprint(b):
    return (b.points, tuple(sorted(b.index.items())), b.unweighted, b.weighted,
            tuple(sorted(b.weights.items())), b.best_points, b.best_unweighted,
            b.best_weighted_at_capture, b.best_weight_epoch, b.stagnation,
            tuple(sorted(b.logical.items())), b.rng_state)


def run():
    started = time.monotonic()
    assert hashlib.sha256(Path(worker.__file__).read_bytes()).hexdigest() == EXPECTED
    counts = dict(states=0, pair_keys=0, row_cost_vectors=0, best_row_sets=0,
                  all_row_outcomes=0, migration_deltas=0, weighted_states=0,
                  weighted_row_sets=0, weighted_migration_deltas=0,
                  policy_transactions=0, checkpoints=0, interrupted_transactions=0,
                  cap_rollbacks=0, checkpoint_interruptions=0)
    for n in (2, 3, 4):
        for ordinal, points in enumerate(oracle.states(n)):
            ps, index, u, w, rows = worker.build_index(points, n)
            assert ps == points and (u, w) == oracle.score(points)
            members = {key: tuple(p for i, p in enumerate(ps) if mask & (1 << i))
                       for key, mask in index.items()}
            assert members == oracle.expected_index(points, n)
            assert rows == tuple(sorted({p[1] for t in oracle.triples(points) for p in t}))
            counts['states'] += 1
            for p, q in __import__('itertools').combinations(points, 2):
                assert worker.line_key(p, q) == oracle.line_key(p, q)
                counts['pair_keys'] += 1
            for row in range(n):
                costs = worker.row_costs(points, index, row, {}, n)
                expected_costs = oracle.row_unary(points, n, row)
                assert costs == {'unweighted': expected_costs, 'weighted': expected_costs}
                counts['row_cost_vectors'] += 1
                minimum, ties = worker.best_row_alternatives(points, row, costs, n)
                expected_min, expected_ties = oracle.best_row_alternatives(points, n, row)
                assert minimum == expected_min
                assert tuple(tuple((x, row) for x in choice) for choice in ties) == expected_ties
                counts['best_row_sets'] += 1
                for alt in oracle.row_alternatives(points, n, row):
                    new_cost = sum(costs['unweighted'][x] for x, y in alt['added'])
                    old_cost = sum(costs['unweighted'][x] for x, y in points if y == row)
                    assert u + new_cost - old_cost == alt['U']
                    counts['all_row_outcomes'] += 1
            for donor, destination, move in oracle.migrations(points, n):
                delta = worker.migration_delta(points, donor, destination, {})
                assert delta == {'unweighted': move['delta'], 'weighted': move['delta']}
                counts['migration_deltas'] += 1
            if n < 4 or ordinal % 107 == 0:
                weights = oracle.weighted_fixture(points, n)
                ps, wi, wu, ww, wr = worker.build_index(points, n, weights)
                assert wi == index and (wu, ww) == oracle.score(points, weights) and wr == rows
                counts['weighted_states'] += 1
                for row in range(n):
                    costs = worker.row_costs(points, wi, row, weights, n)
                    assert costs['weighted'] == oracle.row_unary(points, n, row, weights)
                    assert costs['unweighted'] == oracle.row_unary(points, n, row)
                    minimum, ties = worker.best_row_alternatives(points, row, costs, n)
                    expected_min, expected_ties = oracle.best_row_alternatives(points, n, row, weights)
                    assert minimum == expected_min and tuple(tuple((x, row) for x in c) for c in ties) == expected_ties
                    counts['weighted_row_sets'] += 1
                for donor, destination, move in oracle.migrations(points, n, weights):
                    delta = worker.migration_delta(points, donor, destination, weights)
                    assert delta == {'unweighted': move['U']-u, 'weighted': move['delta']}
                    counts['weighted_migration_deltas'] += 1
    fixtures = json.loads(Path('data/row-block-independent-boundary-fixtures.json').read_text())
    all_phases = set()
    for record in fixtures['reference_transactions']:
        ref, old, rng = make_old(record['old'])
        expected = oracle.Boundary(**{k: tree(v) for k, v in record['new'].items()})
        before = fingerprint(old)
        work = {}; calls = [0]; phases = []
        def check():
            calls[0] += 1; phases.append(work.get('phase'))
        new = worker.propose_transition(old, rng, check=check, work=work)
        assert_boundary(new, expected)
        assert fingerprint(old) == before and rng.getstate() == new.rng_state
        counts['policy_transactions'] += 1
        all_phases.update(phases)
        raw = worker.checkpoint_bytes(new, {'test': 'independent tiny synthetic'})
        payload = json.loads(raw)
        assert tree(payload['current']) == new.points and tree(payload['best']) == new.best_points
        assert tree(payload['rng']) == new.rng_state
        assert tuple((tuple(a[:3]), a[3]) for a in payload['weights']) == tuple(sorted(new.weights.items()))
        assert payload['metadata']['current_weighted'] == new.weighted
        assert payload['metadata']['logical'] == new.logical and len(raw) < worker.CHECKPOINT_CAP
        assert payload['metadata']['validation'] == ('unverified_zero_candidate' if new.unweighted == 0 else 'invalid_research_state')
        counts['checkpoints'] += 1
        for at in range(1, calls[0]+1):
            interrupted_rng = random.Random(); interrupted_rng.setstate(old.rng_state)
            position = [0]
            def interrupt():
                position[0] += 1
                if position[0] == at:
                    raise worker.SearchStop('independent_injection')
            try:
                worker.propose_transition(old, interrupted_rng, check=interrupt)
            except worker.SearchStop:
                pass
            else:
                raise AssertionError('expected transition interruption')
            assert fingerprint(old) == before and interrupted_rng.getstate() == old.rng_state
            counts['interrupted_transactions'] += 1
        if expected.penalties > ref.penalties:
            for policy in (worker.Policy(max_weight_keys=0), worker.Policy(max_weight=1)):
                r = random.Random(); r.setstate(old.rng_state)
                try:
                    worker.propose_transition(old, r, policy=policy)
                except worker.WeightCap:
                    pass
                else:
                    raise AssertionError('missing weight cap')
                assert fingerprint(old) == before and r.getstate() == old.rng_state
                counts['cap_rollbacks'] += 1
        checkpoint_calls = [0]
        def count_check(): checkpoint_calls[0] += 1
        worker.checkpoint_bytes(new, {}, check=count_check)
        new_before = fingerprint(new)
        for at in range(1, checkpoint_calls[0]+1):
            pos = [0]
            def stop_checkpoint():
                pos[0] += 1
                if pos[0] == at: raise worker.SearchStop('checkpoint_injection')
            try:
                worker.checkpoint_bytes(new, {}, check=stop_checkpoint)
            except worker.SearchStop:
                pass
            else:
                raise AssertionError('missing checkpoint interruption')
            assert fingerprint(new) == new_before
            counts['checkpoint_interruptions'] += 1
    # Maximum legal line weights, exact penalty score change, and stale-score rejection.
    points = next(p for p in oracle.states(4) if oracle.score(p)[0] > 1)
    weights = {key: 65535 for key in oracle.expected_index(points, 4)}
    _, _, u, w, _ = worker.build_index(points, 4, weights)
    assert w == 65535*u == oracle.score(points, weights)[1]
    r = random.Random(275149); old = worker.make_boundary(points, 4, r)
    stale = replace(old, weighted=old.weighted+1)
    try: worker.propose_transition(stale, r)
    except ValueError as error: assert 'delta' in str(error)
    else: raise AssertionError('stale weighted boundary accepted')
    assert r.getstate() == old.rng_state
    counts['maximum_weight_cases'] = 1; counts['stale_score_rejections'] = 1
    assert hashlib.sha256(Path(worker.__file__).read_bytes()).hexdigest() == EXPECTED
    return {'scope': 'frozen production pure helpers versus independent synthetic oracle only',
            'worker_sha256': EXPECTED, 'oracle_sha256': hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
            'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'counts': counts, 'interrupted_phases': sorted(all_phases),
            'elapsed_seconds': time.monotonic()-started,
            'limits': ['No actual n75 geometry or search.', 'No orchestration/validator lifecycle acceptance here.',
                       'No production checkpoint file-write fault test here; lifecycle review owns it.',
                       'Weighted states sampled as declared; not exhaustive over weights.']}


if __name__ == '__main__':
    result = run()
    output = Path('data/row-block-independent-worker-audit.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))
    print(hashlib.sha256(output.read_bytes()).hexdigest())
