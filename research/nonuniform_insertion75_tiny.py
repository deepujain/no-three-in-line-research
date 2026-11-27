"""Author synthetic geometry/lifecycle falsifiers; never reads a published fixture."""
from contextlib import ExitStack
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import struct
import tempfile
from unittest.mock import patch

from research import nonuniform_insertion75 as worker


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def direct_zero(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])


def sources(n):
    for points in combinations(product(range(n), repeat=2), 2*n):
        if any(sum(p[a] == v for p in points) != 2 for a in (0, 1) for v in range(n)):
            continue
        if not any(direct_zero(*triple) for triple in combinations(points, 3)):
            yield points


def geometry_tests():
    counts = {'sources': 0, 'included_gaps': 0, 'rectangles': 0, 'lines': 0, 'certificates': 0,
              'early_complete': 0, 'invalid_sources': 0, 'deadline_phases': 0}
    saved = {}
    for n in (2, 3, 4):
        all_sources = list(sources(n)); saved[n] = all_sources
        for points in all_sources:
            result = worker.cover_family(points, n, exhaustive=True)
            fast = worker.cover_family(tuple(reversed(points)), n)
            assert result['geometry_complete'] and result['old_complete'] and result['new_complete']
            assert fast['uncovered'] == result['uncovered']
            if fast['certificate_complete'] and not fast['geometry_complete']:
                counts['early_complete'] += 1
            counts['sources'] += 1
            for c, r in product(range(n+1), repeat=2):
                bit = 1 << ((n+1)*c+r)
                if c in (0, n) and r in (0, n):
                    assert not result['included'] & bit and (c, r) not in result['certificates']
                    continue
                counts['included_gaps'] += 1
                alphabet_c = [v for v in range(n+1) if v != c]
                alphabet_r = [v for v in range(n+1) if v != r]
                target = [(alphabet_c[x], alphabet_r[y]) for x, y in points]+[(c, r)]
                old = any(direct_zero(*(target[i] for i in t)) for t in combinations(range(2*n), 3))
                new = any(direct_zero(target[i], target[j], target[-1]) for i, j in combinations(range(2*n), 2))
                assert bool(result['old_blocked'] & bit) == old
                assert bool(result['new_blocked'] & bit) == new
                assert bool(result['uncovered'] & bit) == (not old and not new)
                if (c, r) in fast['certificates']:
                    cert = fast['certificates'][(c, r)]
                    triple = [target[i] for i in cert['indices']]
                    if cert['kind'] == 'new':
                        triple.append(target[-1])
                    assert len(set(triple)) == 3 and direct_zero(*triple)
                    counts['certificates'] += 1
        for c0 in range(n+1):
            for c1 in range(c0, n+1):
                for r0 in range(n+1):
                    for r1 in range(r0, n+1):
                        bits = worker.rectangle_mask(c0, c1, r0, r1, n)
                        actual = {divmod(i, n+1) for i in range((n+1)**2) if bits & (1 << i)}
                        expected = {(c, r) for c in range(c0, c1+1) for r in range(r0, r1+1)}
                        assert actual == expected; counts['rectangles'] += 1
        for coords in product(range(n), repeat=3):
            intervals = worker.threshold_intervals(coords, n)
            assert [v for lo, hi in intervals for v in range(lo, hi+1)] == list(range(n+1))
            for lo, hi in intervals:
                assert all(tuple(x >= c for x in coords) == tuple(x >= lo for x in coords) for c in range(lo, hi+1))
    for p, q in combinations(product(range(-1, 2), repeat=2), 2):
        for c0, c1 in ((-1, -1), (-1, 2), (0, 1), (2, 2)):
            for r0, r1 in ((-1, 0), (0, 2), (1, 1)):
                bounds = c0, c1, r0, r1
                expected = {(c, r) for c in range(c0, c1+1) for r in range(r0, r1+1) if direct_zero(p, q, (c, r))}
                assert set(worker.clipped_line_points(p, q, bounds)) == expected
                assert set(worker.clipped_line_points(q, p, bounds)) == expected
                counts['lines'] += 2
    try:
        list(worker.clipped_line_points((0, 0), (0, 0), (0, 1, 0, 1)))
        raise AssertionError('equal endpoints accepted')
    except ValueError:
        pass
    invalid = tuple((x, y) for x in range(3) for y in range(3) if x != y)
    # This six-cycle contains a diagonal triple; axis fullness alone is insufficient.
    invalid = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 2))
    assert any(direct_zero(*t) for t in combinations(invalid, 3))
    try:
        worker.cover_family(invalid, 3)
        raise AssertionError('invalid source accepted')
    except ValueError:
        counts['invalid_sources'] += 1
    records = bytearray(36)
    struct.pack_into('<BBBB', records, 0, 2, 0, 1, 0)
    try:
        worker.verify_obstructions(saved[2][0], 2, worker._included_bits(2, True), worker._included_bits(2, True), records)
        raise AssertionError('excluded record accepted')
    except ValueError:
        pass
    for phase in ('kernel_source_validation', 'precomputation', 'old_triples', 'new_pairs', 'certificate_verification'):
        counters = {}
        def stop():
            if counters.get('phase') == phase:
                raise TimeoutError(phase)
        try:
            worker.cover_family(saved[2][0], 2, check=stop, counters=counters)
            raise AssertionError('phase deadline missed: '+phase)
        except TimeoutError:
            counts['deadline_phases'] += 1
    return counts, saved


def lifecycle_case(points, n, mode):
    """Patch constants only inside this synthetic process; production CLI is fixed."""
    with tempfile.TemporaryDirectory(prefix='insertion-tiny-') as directory:
        root = Path(directory); (root/'data').mkdir(); (root/'src').mkdir()
        (root/'src/verify.py').write_text('synthetic pin sentinel\n')
        sentinel = root/'sentinel'; sentinel.write_text('unchanged\n')
        fixture = {'n': n, 'points': list(points), 'source_record': 2 if mode == 'wrong_record' else 1,
                   'raw_sha256': 'synthetic-raw'}
        fixture_path = root/'data/synthetic.json'; fixture_path.write_text(json.dumps(fixture))
        normalized = worker.verify_certificate(fixture)['normalized_sha256']
        manifest = root/'pins.json'
        pins = {str(Path(worker.__file__).resolve()): sha(worker.__file__),
                'src/verify.py': sha(root/'src/verify.py'), 'data/synthetic.json': sha(fixture_path),
                'sentinel': sha(sentinel)}
        manifest.write_text(json.dumps(pins)); out = root/'output'; out.mkdir()
        state = {'now': 0, 'counters': {}, 'report_writes': 0}
        real_cover, real_second, real_atomic, real_digest = worker.cover_family, worker.verify_certificate_bruteforce, worker.atomic, worker.digest
        target_phase = mode.removeprefix('deadline_') if mode.startswith('deadline_') else None
        def clock():
            if state['counters'].get('phase') == target_phase and target_phase is not None:
                return 26
            return state['now']
        def cover(*args, **kwargs):
            state['counters'] = kwargs['counters']
            result = real_cover(*args, **kwargs)
            if mode == 'partial_positive':
                result['geometry_complete'] = False
            if mode == 'pin_drift':
                sentinel.write_text('changed\n')
            if mode == 'deadline_final_pins':
                state['final_pins'] = True
            return result
        def second(certificate):
            result = real_second(certificate)
            if certificate['n'] == n+1:
                if mode == 'late_validator2':
                    state['now'] = 26
                if mode == 'candidate_disagreement':
                    result['valid'] = False
            return result
        def atomic(path, value):
            if path.name == 'valid149.json' and mode == 'save_failure':
                raise OSError('synthetic save failure')
            real_atomic(path, value)
            if path.name == 'report.json':
                state['report_writes'] += 1
                if mode == 'deadline_report_save':
                    state['now'] = 26
        def digest(path, check=lambda: None):
            if state.get('final_pins'):
                state['now'] = 26
            return real_digest(path, check)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(worker, ROOT=root, SOURCE_N=n, FIXTURE='data/synthetic.json',
                                               FIXTURE_SHA=sha(fixture_path), NORMALIZED=normalized, RAW_SHA='synthetic-raw'))
            for name, value in (('cover_family', cover), ('verify_certificate_bruteforce', second), ('atomic', atomic), ('digest', digest)):
                stack.enter_context(patch.object(worker, name, value))
            report = worker.run(out, manifest, clock=clock, started=0)
        persisted = json.loads((out/'report.json').read_text())
        assert json.loads(json.dumps(report)) == persisted
        if mode == 'positive':
            assert report['complete'] and report['witness_saved'] and not report['closure'], report
        elif mode == 'negative':
            assert report['complete'] and report['closure'] and report['certificate_complete']
        else:
            assert not report['complete'] and not report['closure'], (mode, report)
        if mode == 'late_validator2':
            assert report['witness_saved'] and (out/'valid149.json').exists()
            saved = json.loads((out/'valid149.json').read_text())
            assert real_second(saved['certificate'])['valid']
        if mode in ('candidate_disagreement', 'partial_positive', 'save_failure'):
            assert not report['witness_saved'] and not (out/'valid149.json').exists()
        if mode == 'pin_drift':
            assert not report['identity_valid']
        if mode == 'deadline_report_save':
            assert state['report_writes'] == 2
        return {'mode': mode, 'status': report['status'], 'complete': report['complete'],
                'closure': report['closure'], 'witness_saved': report['witness_saved']}


def main():
    geometry, saved = geometry_tests()
    results = [lifecycle_case(saved[2][0], 2, mode) for mode in
               ('positive', 'partial_positive', 'wrong_record', 'late_validator2', 'candidate_disagreement',
                'save_failure', 'pin_drift', 'deadline_precomputation', 'deadline_old_triples',
                'deadline_new_pairs', 'deadline_certificate_verification', 'deadline_final_pins', 'deadline_report_save')]
    results.append(lifecycle_case(saved[3][0], 3, 'negative'))
    report = {'passed': True, 'worker_sha256': sha(worker.__file__), 'tiny_sha256': sha(__file__),
              'geometry': geometry, 'lifecycle': results,
              'scope': 'Author synthetic n2..4 only; no published source load or actual n74 insertion/census.'}
    target = Path(__file__).resolve().parents[1]/'data/nonuniform-insertion75-author-tiny.json'
    target.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
