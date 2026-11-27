"""Selected-source exterior unimodular extension; actual use needs Lead allocation.

Pure geometry helpers use sorted source indices. Production CLI is fixed to n74
record1 and excludes the closed preimage box [-1,74]^2. No automatic fallback.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce

FIXTURE = 'data/published-n74.json'
FIXTURE_SHA = '276340cef4486bd33666a664e2eba968cbef7deda4398c26590f1307ccf280d4'
NORMALIZED = '3c9c8bf350cb3441dfcef0cdef24a3ba2d53cd0895a3885da18680e2407f27a5'
RAW_SHA = '1c276251f9c819d2941eedb1fa02bd860c093b970af395d8baea86ad4cd5c9f0'
SOURCE_N = 74


def cross(a, b):
    return a[0]*b[1]-a[1]*b[0]


def dot(u, p):
    return u[0]*p[0]+u[1]*p[1]


def collinear(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])


def canonical(u):
    return u[0] > 0 or (u[0] == 0 and u[1] > 0)


def protected(q, n):
    return -1 <= q[0] <= n and -1 <= q[1] <= n


def _source(points, n, check, count):
    if type(n) is not int or not 4 <= n <= 74:
        raise ValueError('source order; modulo3 gate requires n>=4')
    points = tuple(sorted(map(tuple, points)))
    if len(points) != 2*n or len(set(points)) != len(points):
        raise ValueError('source size/duplicates')
    if any(len(p) != 2 or any(type(v) is not int or not 0 <= v < n for v in p) for p in points):
        raise ValueError('source coordinate domain')
    if any(Counter(p[a] for p in points) != Counter({v: 2 for v in range(n)}) for a in (0, 1)):
        raise ValueError('source axis loads')
    count['phase'] = 'source_geometry'
    for triple in combinations(points, 3):
        check(); count['source_triples'] += 1
        if collinear(*triple):
            raise ValueError('source invalid before width theorem')
    count['source_valid'] = True
    return points


def _axis_witnesses(points):
    rows = {}; columns = {}
    for i, (x, y) in enumerate(points):
        rows.setdefault(y, []).append(i); columns.setdefault(x, []).append(i)
    horizontal = max((abs(points[i][0]-points[j][0]), (i, j)) for i, j in rows.values())
    vertical = max((abs(points[i][1]-points[j][1]), (i, j)) for i, j in columns.values())
    return horizontal, vertical


def _vectors(a_bound, b_bound):
    for a in range(-a_bound, a_bound+1):
        for b in range(-b_bound, b_bound+1):
            if canonical((a, b)) and math.gcd(abs(a), abs(b)) == 1:
                yield (a, b)


def verify_inventory(points, n, inventory, check=lambda: None, counters=None):
    """Re-enumerate domain; verify extreme-pair rejects and full accepted widths."""
    count = {} if counters is None else counters
    count['phase'] = 'inventory_certificate'
    h, v = _axis_witnesses(points)
    if inventory['H'] != h[0] or inventory['V'] != v[0] or tuple(inventory['H_witness']) != h[1] or tuple(inventory['V_witness']) != v[1]:
        raise ValueError('H/V witness identity')
    ab, bb = n//h[0], n//v[0]
    if inventory['a_bound'] != ab or inventory['b_bound'] != bb:
        raise ValueError('coefficient cutoff')
    expected = set(); seen = set()
    for u in _vectors(ab, bb):
        check(); expected.add(u)
    count['inventory_certificate_checks'] = 0
    count['accepted_verification_projections'] = 0
    for admitted, records in ((True, inventory['admitted']), (False, inventory['rejected'])):
        for record in records:
            check(); u = tuple(record['vector'])
            if len(u) != 2 or any(type(x) is not int for x in u) or u not in expected or u in seen:
                raise ValueError('duplicate/invalid direction record')
            seen.add(u)
            if admitted:
                values = []
                for p in points:
                    check(); values.append(dot(u, p)); count['accepted_verification_projections'] += 1
                lo, hi = min(values), max(values)
                if not n-1 <= hi-lo <= n or record['min'] != lo or record['max'] != hi or record['width'] != hi-lo:
                    raise ValueError('admitted width')
                for key, level in (('min_index', lo), ('max_index', hi)):
                    i = record[key]
                    if type(i) is not int or not 0 <= i < len(points) or values[i] != level:
                        raise ValueError('admitted extreme witness')
                if record['levels'] != [list(pair) for pair in sorted(Counter(values).items())]:
                    raise ValueError('admitted level histogram')
            else:
                indices = record['indices']
                if len(indices) != 2 or len(set(indices)) != 2 or any(type(i) is not int or not 0 <= i < len(points) for i in indices):
                    raise ValueError('rejected width indices')
                if abs(dot(u, points[indices[0]])-dot(u, points[indices[1]])) <= n:
                    raise ValueError('rejected width certificate')
            count['inventory_certificate_checks'] += 1
    if seen != expected:
        raise ValueError('incomplete coefficient inventory')
    directions = {tuple(record['vector']) for record in inventory['admitted']}
    signed = directions | {(-a, -b) for a, b in directions} | {(0, 0)}
    if len(directions) > 4 or len({(a % 3, b % 3) for a, b in signed}) != len(signed):
        raise ValueError('modulo3 width theorem contradiction')
    if not {(1, 0), (0, 1)} <= directions:
        raise ValueError('missing source axis directions')
    check()
    return True


def direction_inventory(points, n, *, check=None, counters=None):
    check = check or (lambda: None); count = {} if counters is None else counters
    count.update(source_triples=0, coefficient_vectors=0, projections=0, inventory_complete=False)
    points = _source(points, n, check, count)
    (h, hw), (v, vw) = _axis_witnesses(points)
    result = {'points': points, 'H': h, 'V': v, 'H_witness': hw, 'V_witness': vw,
              'a_bound': n//h, 'b_bound': n//v, 'admitted': [], 'rejected': [], 'inventory_complete': False}
    count['phase'] = 'direction_projection'
    for u in _vectors(result['a_bound'], result['b_bound']):
        check(); count['coefficient_vectors'] += 1
        lo = hi = dot(u, points[0]); low_index = high_index = 0
        values = [lo]; count['projections'] += 1
        for index in range(1, len(points)):
            check(); value = dot(u, points[index]); count['projections'] += 1
            values.append(value)
            if value < lo:
                lo, low_index = value, index
            if value > hi:
                hi, high_index = value, index
            if hi-lo > n:
                result['rejected'].append({'vector': u, 'indices': (low_index, high_index)})
                break
        else:
            if hi-lo < n-1:
                raise ValueError('valid-source width lower bound contradiction')
            result['admitted'].append({'vector': u, 'min': lo, 'max': hi, 'width': hi-lo,
                                       'min_index': low_index, 'max_index': high_index,
                                       'levels': [list(pair) for pair in sorted(Counter(values).items())]})
    if count['coefficient_vectors'] > ((2*n+1)**2-1)//2 or count['projections'] > n*((2*n+1)**2-1):
        raise ValueError('direction resource ceiling')
    verify_inventory(points, n, result, check, count)
    check(); result['inventory_complete'] = count['inventory_complete'] = True
    return result


def canonical_frames(admitted):
    directions = sorted(tuple(item['vector']) for item in admitted)
    return [(u, v) for u, v in combinations(directions, 2)
            if abs(cross(u, v)) == 1 and {u, v} != {(1, 0), (0, 1)}]


def frame_candidates(points, n, frame, *, check=None):
    """Raw deficient intersections across placements, including occupied exclusions."""
    check = check or (lambda: None); u, v = frame; d = cross(u, v)
    if abs(d) != 1:
        raise ValueError('frame determinant')
    xx, yy = [dot(u, p) for p in points], [dot(v, p) for p in points]
    if not n-1 <= max(xx)-min(xx) <= n or not n-1 <= max(yy)-min(yy) <= n:
        raise ValueError('frame widths')
    choices = []
    for tx in range(-min(xx), n-max(xx)+1):
        for ty in range(-min(yy), n-max(yy)+1):
            check(); mapped = {(x+tx, y+ty) for x, y in zip(xx, yy)}
            cx, cy = Counter(x for x, _ in mapped), Counter(y for _, y in mapped)
            for x in (value for value in range(n+1) if cx[value] < 2):
                for y in (value for value in range(n+1) if cy[value] < 2):
                    check(); a, b = x-tx, y-ty
                    q = ((v[1]*a-u[1]*b)//d, (-v[0]*a+u[0]*b)//d)
                    if (dot(u, q)+tx, dot(v, q)+ty) != (x, y):
                        raise ValueError('inverse forward identity')
                    choices.append({'frame': frame, 'translation': (tx, ty), 'added': (x, y),
                                    'preimage': q, 'reason': 'occupied' if (x, y) in mapped else 'unfiltered'})
    if len(choices) > 4:
        raise ValueError('all-placement deficient choice ceiling')
    return choices


def analyze_family(points, n, *, check=None, counters=None):
    check = check or (lambda: None); count = {} if counters is None else counters
    count.update(frames=0, candidate_choices=0, protected_choices=0, occupied_choices=0,
                 duplicate_choices=0, pair_tests=0, pair_certificate_checks=0,
                 candidates_complete=False, pairs_complete=False)
    inventory = direction_inventory(points, n, check=check, counters=count)
    points = inventory['points']; count['phase'] = 'frame_candidates'
    frames = canonical_frames(inventory['admitted'])
    if len(frames) > 5:
        raise ValueError('nonordinary frame bound')
    count['frames'] = len(frames); candidates = []; exclusions = []; eligible = {}
    for frame in frames:
        check()
        for item in frame_candidates(points, n, frame, check=check):
            check(); count['candidate_choices'] += 1; candidates.append(item)
            q = item['preimage']
            if item['reason'] == 'occupied':
                count['occupied_choices'] += 1; exclusions.append(item); continue
            if protected(q, n):
                item['reason'] = 'protected'; count['protected_choices'] += 1
                exclusions.append(item); continue
            if q in eligible:
                item['reason'] = 'duplicate'; count['duplicate_choices'] += 1
                exclusions.append(item); continue
            item['reason'] = 'eligible'; eligible[q] = item
    if len(candidates) > 20 or len(eligible) > 20:
        raise ValueError('candidate preimage bound')
    check(); count['candidates_complete'] = True
    count['phase'] = 'candidate_pairs'; obstructions = []; survivors = []
    for q, item in sorted(eligible.items()):
        for i, j in combinations(range(len(points)), 2):
            check(); count['pair_tests'] += 1
            if collinear(points[i], points[j], q):
                obstructions.append({'preimage': q, 'indices': (i, j)})
                break
        else:
            survivors.append(item)
    if count['pair_tests'] > 20*math.comb(len(points), 2):
        raise ValueError('new pair resource bound')
    check(); count['pairs_complete'] = True
    count['phase'] = 'pair_certificate'
    seen = set()
    for item in obstructions:
        check(); q = item['preimage']; i, j = item['indices']
        if q in seen or q not in eligible or q in points or protected(q, n) or not (0 <= i < j < len(points)) or not collinear(points[i], points[j], q):
            raise ValueError('invalid exterior pair certificate')
        seen.add(q); count['pair_certificate_checks'] += 1
    if seen | {item['preimage'] for item in survivors} != set(eligible) or seen & {item['preimage'] for item in survivors}:
        raise ValueError('candidate classification coverage')
    check(); count['phase'] = 'family_finished'
    return {'inventory': inventory, 'frames': frames, 'candidate_choices': candidates, 'exclusions': exclusions,
            'eligible_candidates': list(eligible.values()), 'pair_obstructions': obstructions, 'survivors': survivors,
            'inventory_complete': True, 'candidates_complete': True, 'pairs_complete': True,
            'family_complete': True, 'certificate_complete': not survivors, 'counters': count}


def build_candidate(points, n, item):
    u, v = item['frame']; tx, ty = item['translation']; z = item['added']; q = item['preimage']
    if protected(q, n) or abs(cross(u, v)) != 1 or (dot(u, q)+tx, dot(v, q)+ty) != tuple(z):
        raise ValueError('candidate witness identity/protected preimage')
    return {'n': n+1, 'points': [(dot(u, p)+tx, dot(v, p)+ty) for p in points]+[tuple(z)],
            'frame': item['frame'], 'translation': item['translation'], 'preimage': q,
            'source_record': 1, 'source_sha256': FIXTURE_SHA, 'normalized_source_sha256': NORMALIZED,
            'novelty_claimed': False}


def digest(path, check=lambda: None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); block = stream.read(1024*1024)
            if not block:
                return h.hexdigest()
            h.update(block)


def atomic(path, value):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.'+path.name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def run(out, manifest, seconds=25, *, started=None, clock=time.monotonic):
    if isinstance(seconds, bool) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('duration')
    start = clock() if started is None else started; deadline = start+seconds
    def check():
        if clock() >= deadline:
            raise TimeoutError('shared soft deadline')
    report = {'method': 'selected_n74_exterior_unimodular_extension', 'status': 'incomplete',
              'complete': False, 'closure': False, 'witness_saved': False, 'counters': {},
              'source_record': 1, 'source_sha256': FIXTURE_SHA, 'normalized_source_sha256': NORMALIZED,
              'family': {'source_n': SOURCE_N, 'target_n': SOURCE_N+1, 'determinants': [-1, 1],
                         'protected_closed_box': [-1, SOURCE_N], 'ordinary_axis_frames_excluded': True,
                         'signed_row_permutations_quotiented': True},
              'scope': 'Only selected record1 exterior unimodular family; no protected preimages, source change, repairs, retry, coefficient expansion or nonunimodular fallback.'}
    pins = {}; pins_ready = False
    def verify_pins():
        for name, sha in pins.items():
            if digest(name, check) != sha:
                raise ValueError('source pin changed: '+name)
    try:
        check(); raw = Path(manifest).read_bytes()
        if len(raw) > 2*1024*1024:
            raise ValueError('oversized pin manifest')
        sources = json.loads(raw)
        if not isinstance(sources, dict) or not 1 <= len(sources) <= 512:
            raise ValueError('pin manifest shape')
        for name, sha in sources.items():
            if not isinstance(name, str) or not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('pin entry')
            resolved = str((ROOT/name).resolve())
            if resolved in pins:
                raise ValueError('duplicate normalized pin')
            pins[resolved] = sha
        required = {str(Path(__file__).resolve()), str((ROOT/FIXTURE).resolve()), str((ROOT/'src/verify.py').resolve())}
        if not required <= pins.keys() or pins[str((ROOT/FIXTURE).resolve())] != FIXTURE_SHA:
            raise ValueError('missing reviewed source pins')
        if str(Path(manifest).resolve()) in pins:
            raise ValueError('manifest must not list itself')
        pins[str(Path(manifest).resolve())] = hashlib.sha256(raw).hexdigest()
        verify_pins(); pins_ready = True; check()
        source = json.loads((ROOT/FIXTURE).read_text())
        if source['n'] != SOURCE_N or source.get('source_record') != 1 or source.get('raw_sha256') != RAW_SHA:
            raise ValueError('selected source identity')
        validators = []
        for validator in (verify_certificate, verify_certificate_bruteforce):
            check(); validators.append(validator(source)); check()
        if not all(v['valid'] and v['point_count'] == 2*SOURCE_N and v['normalized_sha256'] == NORMALIZED for v in validators):
            raise ValueError('source dual validation')
        report['source_validation'] = validators
        points = tuple(sorted(map(tuple, source['points'])))
        result = analyze_family(points, SOURCE_N, check=check, counters=report['counters'])
        report['analysis'] = {key: value for key, value in result.items() if key != 'counters'}
        check()
        if not all(result.get(key) is True for key in ('inventory_complete', 'candidates_complete', 'pairs_complete', 'family_complete')):
            raise ValueError('partial family cannot conclude')
        if result['survivors']:
            candidate = build_candidate(points, SOURCE_N, result['survivors'][0])
            report['counters']['phase'] = 'candidate_validator1'; check()
            a = verify_certificate(candidate); check()
            report['counters']['phase'] = 'candidate_validator2'
            b = verify_certificate_bruteforce(candidate)
            if not (a['valid'] and b['valid'] and a['point_count'] == b['point_count'] == 2*SOURCE_N+1
                    and a['normalized_sha256'] == b['normalized_sha256']):
                raise ValueError('candidate dual validation disagreement')
            # Mandatory persistence precedes any post-validator2 deadline/pin work.
            atomic(out/'valid149.json', {'certificate': candidate, 'validators': [a, b]})
            report.update(witness_saved=True, candidate_validators=[a, b], status='verified149'); check()
        elif result['certificate_complete']:
            report.update(status='selected_exterior_family_obstructed', closure=True)
        else:
            raise ValueError('missing negative certificate completion')
        check(); report['complete'] = True
    except TimeoutError as error:
        report.update(status='timeout', error=str(error), complete=False, closure=False)
    except Exception as error:
        report.update(status='error', error=f'{type(error).__name__}: {error}', complete=False, closure=False)
    try:
        if not pins_ready:
            raise ValueError('initial pins incomplete')
        verify_pins(); check(); report['identity_valid'] = True
    except Exception as error:
        report.update(status='timeout' if isinstance(error, TimeoutError) else 'error', error=str(error),
                      identity_valid=False, complete=False, closure=False)
    report.update(pins=pins, elapsed_seconds=clock()-start); atomic(out/'report.json', report)
    try:
        check()
    except TimeoutError as error:
        report.update(status='timeout', error=str(error), complete=False, closure=False, elapsed_seconds=clock()-start)
        atomic(out/'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--source-pins', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=25)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.output_dir, args.source_pins, args.seconds, started=ENTRY_STARTED)
    print(json.dumps({key: report.get(key) for key in ('status', 'complete', 'closure', 'witness_saved', 'elapsed_seconds', 'counters')}, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
