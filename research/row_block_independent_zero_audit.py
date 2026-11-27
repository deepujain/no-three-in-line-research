"""Independent tiny transition-zero orchestration plus disclosed author reruns."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import random
import tempfile
from unittest.mock import patch
from research import row_block_independent_oracle as oracle
from research import row_block_breakout75 as w
from research import row_block_breakout75_tiny as author


def run_case(mode, points):
    with tempfile.TemporaryDirectory(prefix='independent-row-zero-') as name:
        root = Path(name); out = root/'output'; out.mkdir(); manifest = root/'pins.json'
        paths = [Path(w.__file__).resolve(), w.ROOT/'src/verify.py',
                 Path(w.sys.executable).resolve(), Path(w.random.__file__).resolve()]
        manifest.write_text(json.dumps({str(p): w.digest(p) for p in paths}))
        rng = random.Random(275149); old = w.make_boundary(points, 4, rng)
        expected = oracle.reference_step(oracle.boundary(points, 4))
        assert old.unweighted > 0 and expected.U == 0
        state = {'clock': 0, 'events': []}
        advance, first, second, save = w.propose_transition, w.verify_certificate, w.verify_certificate_bruteforce, w.atomic_bytes
        def initialize(n, current_rng, **kwargs):
            assert n == 4
            current_rng.setstate(old.rng_state)
            return old
        def transition(boundary, current_rng, **kwargs):
            new = advance(boundary, current_rng, **kwargs)
            assert new.unweighted == 0 and new.points == expected.points
            state['events'].append('completed_zero')
            if mode == 'after_search_deadline': state['clock'] = 23.5
            if mode == 'after_main_deadline': state['clock'] = 26
            return new
        def one(candidate):
            state['events'].append('validator1')
            result = first(candidate)
            assert candidate['axis_counts']['rows'] == [sum(y == row for x, y in expected.points) for row in range(4)]
            assert candidate['axis_counts']['columns'] == [sum(x == col for x, y in expected.points) for col in range(4)]
            if mode == 'first_finishes_late': state['clock'] = 26
            return result
        def two(candidate):
            state['events'].append('validator2'); result = second(candidate)
            if mode == 'second_finishes_late': state['clock'] = 26
            return result
        def write(path, raw):
            state['events'].append(path.name); save(path, raw)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(w, N=4, MAX_STEPS=1))
            for key, value in [('initial_boundary', initialize), ('propose_transition', transition),
                               ('verify_certificate', one), ('verify_certificate_bruteforce', two), ('atomic_bytes', write)]:
                stack.enter_context(patch.object(w, key, value))
            report = w.run(out, manifest, clock=lambda: state['clock'], started=0)
        assert report['checkpoint_saved']
        payload = json.loads((out/'completed-boundary.json').read_bytes())
        assert tuple(map(tuple, payload['current'])) == expected.points
        assert payload['metadata']['current_unweighted'] == 0
        if mode in ('after_main_deadline', 'first_finishes_late'):
            assert not report['witness_saved'] and 'validator2' not in state['events']
            assert payload['metadata']['validation'] == 'unverified_zero_candidate'
        else:
            assert report['witness_saved']
            assert state['events'].index('valid149.json') == state['events'].index('validator2') + 1
            assert payload['metadata']['validation'] == 'dual_verified_witness'
        assert report['accepted'] is (mode in ('ordinary', 'after_search_deadline'))
        return {'mode': mode, 'events': state['events'], 'status': report['status'],
                'accepted': report['accepted'], 'witness_saved': report['witness_saved'],
                'checkpoint_validation': payload['metadata']['validation']}


if __name__ == '__main__':
    expected_hash = 'ee8a78e0f199f2a2f52e2bc37530c12a05c6b54a978f31371b05d9558cd51e0f'
    assert w.digest(w.__file__) == expected_hash
    points = next(p for p in oracle.states(4) if oracle.score(p)[0]
                  and oracle.reference_step(oracle.boundary(p, 4)).U == 0)
    modes = ('ordinary', 'after_search_deadline', 'after_main_deadline', 'first_finishes_late', 'second_finishes_late')
    result = {'scope': 'synthetic n4 actual transition and real dual validators; no actual n75 geometry/search',
              'source_points': points, 'independent_transition_zero_cases': [run_case(m, points) for m in modes],
              'disclosed_author_lifecycle_reruns': [author.lifecycle(m) for m in ('normal', 'zero', 'late_first', 'late_second',
                  'late_raw_zero', 'disagreement', 'checkpoint_failure', 'serialization_failure', 'pin_drift', 'witness_then_pin_drift')],
              'worker_sha256': expected_hash, 'helper_sha256': w.digest(__file__), 'author_helper_sha256': w.digest(author.__file__)}
    assert w.digest(w.__file__) == expected_hash
    output = Path('data/row-block-independent-zero-audit.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True)); print(w.digest(output))
