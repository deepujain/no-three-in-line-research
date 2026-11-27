"""One selected n74 insertion family. Actual use requires a separate Lead allocation.

Pure helpers accept synthetic sources. Source indices always refer to sorted points.
The CLI accepts only the pinned selected n74 record, never an alternative source.
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
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce

FIXTURE = 'data/published-n74.json'
FIXTURE_SHA = '276340cef4486bd33666a664e2eba968cbef7deda4398c26590f1307ccf280d4'
NORMALIZED = '3c9c8bf350cb3441dfcef0cdef24a3ba2d53cd0895a3885da18680e2407f27a5'
SOURCE_N = 74
RAW_SHA = '1c276251f9c819d2941eedb1fa02bd860c093b970af395d8baea86ad4cd5c9f0'


def determinant(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def mapped_point(p, c, r):
    return (p[0]+(p[0] >= c), p[1]+(p[1] >= r))


def threshold_intervals(coords, n):
    """Inclusive gap intervals; equality is retained on the shifted side."""
    values = sorted(set(coords))
    if not values or any(type(v) is not int or not 0 <= v < n for v in values):
        raise ValueError('threshold coordinates')
    starts = [0]+[v+1 for v in values]
    ends = values+[n]
    return list(zip(starts, ends))


def _column_masks(n, check, counters):
    g = n+1
    result = [[0]*g for _ in range(g)]
    counters['phase'] = 'precomputation'
    for c0 in range(g):
        value = 0
        for c1 in range(c0, g):
            check(); value |= 1 << (g*c1)
            result[c0][c1] = value
            counters['precomputed_intervals'] += 1
    counters['precomputation_complete'] = True
    return result


def rectangle_mask(c0, c1, r0, r1, n, *, columns=None):
    if not (0 <= c0 <= c1 <= n and 0 <= r0 <= r1 <= n):
        raise ValueError('rectangle bounds')
    repeat = (sum(1 << ((n+1)*c) for c in range(c0, c1+1))
              if columns is None else columns[c0][c1])
    return repeat*(((1 << (r1-r0+1))-1) << r0)


def clipped_line_points(p, q, bounds):
    """All lattice points of an infinite line in inclusive c0,c1,r0,r1 bounds."""
    c0, c1, r0, r1 = bounds
    if c0 > c1 or r0 > r1:
        raise ValueError('line rectangle bounds')
    a, b = q[0]-p[0], q[1]-p[1]
    divisor = math.gcd(abs(a), abs(b))
    if not divisor:
        raise ValueError('equal line endpoints')
    steps = (a//divisor, b//divisor)
    low = high = None
    for origin, step, lo, hi in zip(p, steps, (c0, r0), (c1, r1)):
        if not step:
            if not lo <= origin <= hi:
                return
            continue
        lower, upper = ((lo-origin, hi-origin) if step > 0 else (hi-origin, lo-origin))
        lower = -((-lower)//step)
        upper //= step
        low = lower if low is None else max(low, lower)
        high = upper if high is None else min(high, upper)
    for t in range(low, high+1):
        yield (p[0]+t*steps[0], p[1]+t*steps[1])


def _source_points(points, n, check, counters):
    if type(n) is not int or not 2 <= n <= 74:
        raise ValueError('source order')
    points = tuple(sorted(map(tuple, points)))
    if len(points) != 2*n or len(set(points)) != len(points):
        raise ValueError('source dimensions/duplicates')
    if any(len(p) != 2 or any(type(v) is not int or not 0 <= v < n for v in p) for p in points):
        raise ValueError('source coordinate domain')
    if any(Counter(p[axis] for p in points) != Counter({v: 2 for v in range(n)}) for axis in (0, 1)):
        raise ValueError('source axis loads')
    counters['phase'] = 'kernel_source_validation'
    for triple in combinations(points, 3):
        check(); counters['source_validation_triples'] += 1
        if determinant(*triple) == 0:
            raise ValueError('invalid geometric source before uniform shortcut')
    counters['kernel_source_valid'] = True
    return points


def _included_bits(n, exclude_corners):
    g = n+1; bits = (1 << (g*g))-1
    if exclude_corners:
        for c, r in ((0, 0), (0, n), (n, 0), (n, n)):
            bits &= ~(1 << (g*c+r))
    return bits


def verify_obstructions(points, n, included, uncovered, records, check=lambda: None, counters=None):
    """Check every removed bit against reconstructed source members, not coverage math."""
    if len(records) != 4*(n+1)**2 or uncovered & ~included:
        raise ValueError('certificate dimensions/bit domain')
    counters = {} if counters is None else counters
    counters['phase'] = 'certificate_verification'
    counters['certificate_checks'] = 0
    g = n+1; decoded = {}
    for index in range(g*g):
        check(); kind, i, j, k = struct.unpack_from('<BBBB', records, 4*index)
        bit = 1 << index
        required = bool(included & bit and not uncovered & bit)
        if bool(kind) != required or (not kind and (i or j or k)):
            raise ValueError('missing, extraneous or malformed obstruction')
        if not kind:
            continue
        if kind not in (1, 2) or (kind == 2 and k):
            raise ValueError('obstruction kind/unused index')
        indices = (i, j, k) if kind == 1 else (i, j)
        if len(set(indices)) != len(indices) or any(v >= len(points) for v in indices):
            raise ValueError('obstruction source indices')
        c, r = divmod(index, g)
        triple = [mapped_point(points[v], c, r) for v in indices]
        if kind == 2:
            triple.append((c, r))
        if len(set(triple)) != 3 or determinant(*triple):
            raise ValueError('obstruction is not a distinct collinear target triple')
        decoded[(c, r)] = {'kind': 'old' if kind == 1 else 'new', 'indices': indices}
        counters['certificate_checks'] += 1
    return decoded


def cover_family(points, n, exclude_corners=True, deadline=None, *, check=None, counters=None, exhaustive=False):
    """Return an obstruction cover; unexcluded gaps are positive only if geometry_complete.

    All point indices use lexicographically sorted source order. Class masks may be
    partial unless their corresponding *_complete flag is true. exhaustive=True
    disables early full-cover stopping for independent synthetic class comparisons.
    """
    outer_check = check or (lambda: None)
    def tick():
        outer_check()
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError('kernel deadline')
    count = {} if counters is None else counters
    count.update(source_validation_triples=0, precomputed_intervals=0, precomputation_complete=False,
                 triples_started=0, triples_completed=0, rectangle_tests=0, zero_rectangles=0,
                 pairs_started=0, pairs_completed=0, pair_rectangles=0, line_points=0,
                 assigned_gaps=0, certificate_checks=0)
    points = _source_points(points, n, tick, count)
    columns = _column_masks(n, tick, count)
    included = _included_bits(n, exclude_corners); uncovered = included
    records = bytearray(4*(n+1)**2)
    old_blocked = new_blocked = 0
    old_complete = new_complete = False
    g = n+1

    def assign(hit, kind, indices):
        nonlocal uncovered
        packed = (kind, *indices) if kind == 1 else (kind, *indices, 0)
        while hit:
            tick(); bit = hit & -hit; index = bit.bit_length()-1
            struct.pack_into('<BBBB', records, 4*index, *packed)
            uncovered &= ~bit; hit ^= bit
            count['assigned_gaps'] += 1

    count['phase'] = 'old_triples'
    for i, j, k in combinations(range(len(points)), 3):
        tick(); count['triples_started'] += 1
        triple = (points[i], points[j], points[k]); xs, ys = zip(*triple)
        cs = threshold_intervals(xs, n); rs = threshold_intervals(ys, n)
        for ci, (c0, c1) in enumerate(cs):
            xx = tuple(x+(x >= c0) for x in xs)
            for ri, (r0, r1) in enumerate(rs):
                if ci in (0, len(cs)-1) and ri in (0, len(rs)-1):
                    continue  # Certified valid source; this region is a uniform translation.
                tick(); count['rectangle_tests'] += 1
                yy = tuple(y+(y >= r0) for y in ys)
                if (xx[1]-xx[0])*(yy[2]-yy[0]) != (yy[1]-yy[0])*(xx[2]-xx[0]):
                    continue
                count['zero_rectangles'] += 1
                bits = rectangle_mask(c0, c1, r0, r1, n, columns=columns) & included
                old_blocked |= bits
                assign(bits & uncovered, 1, (i, j, k))
                if not uncovered and not exhaustive:
                    break
            if not uncovered and not exhaustive:
                break
        if not uncovered and not exhaustive:
            break
        count['triples_completed'] += 1
    else:
        old_complete = True

    if uncovered or exhaustive:
        count['phase'] = 'new_pairs'
        for i, j in combinations(range(len(points)), 2):
            tick(); count['pairs_started'] += 1
            p, q = points[i], points[j]
            if p[0] != q[0] and p[1] != q[1]:
                for c0, c1 in threshold_intervals((p[0], q[0]), n):
                    for r0, r1 in threshold_intervals((p[1], q[1]), n):
                        tick(); count['pair_rectangles'] += 1
                        pp, qq = mapped_point(p, c0, r0), mapped_point(q, c0, r0)
                        for c, r in clipped_line_points(pp, qq, (c0, c1, r0, r1)):
                            tick(); count['line_points'] += 1
                            bit = 1 << (g*c+r)
                            if not included & bit:
                                continue
                            new_blocked |= bit
                            assign(bit & uncovered, 2, (i, j))
                            if not uncovered and not exhaustive:
                                break
                        if not uncovered and not exhaustive:
                            break
                    if not uncovered and not exhaustive:
                        break
            if not uncovered and not exhaustive:
                break
            count['pairs_completed'] += 1
        else:
            new_complete = True

    tick()
    if count['rectangle_tests'] > 12*math.comb(len(points), 3):
        raise ValueError('old rectangle resource bound')
    if count['pair_rectangles'] > 9*math.comb(len(points), 2) or count['line_points'] > 3*g*math.comb(len(points), 2):
        raise ValueError('pair resource bound')
    decoded = verify_obstructions(points, n, included, uncovered, records, tick, count)
    if len(decoded) != count['assigned_gaps'] or len(decoded) > included.bit_count():
        raise ValueError('certificate assignment bound')
    count['phase'] = 'geometry_finished'
    return {'included': included, 'uncovered': uncovered, 'certificates': decoded,
            'old_blocked': old_blocked, 'new_blocked': new_blocked,
            'old_complete': old_complete, 'new_complete': new_complete,
            'geometry_complete': old_complete and new_complete,
            'certificate_complete': uncovered == 0, 'counters': count}


def digest(path, check=lambda: None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); chunk = stream.read(1024*1024)
            if not chunk:
                return h.hexdigest()
            h.update(chunk)


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
    start = clock() if started is None else started
    deadline = start+seconds
    def check():
        if clock() >= deadline:
            raise TimeoutError('shared soft deadline')
    report = {'method': 'selected_n74_nonuniform_insertion', 'status': 'incomplete',
              'complete': False, 'closure': False, 'witness_saved': False, 'counters': {},
              'score_census_complete': False, 'source_record': 1, 'source_sha256': FIXTURE_SHA,
              'normalized_source_sha256': NORMALIZED,
              'family': {'source_n': SOURCE_N, 'gaps': [0, SOURCE_N], 'exclude_both_boundary': True,
                         'included_count': (SOURCE_N+1)**2-4, 'bit_index': '(source_n+1)*c+r'},
              'scope': 'Only selected record1 and 5621 nonuniform insertion gaps; no boundary-corner cases, repairs, alternate source, orientation loop or fallback.'}
    pins = {}; pins_ready = False
    def verify_pins():
        for name, sha in pins.items():
            if digest(name, check) != sha:
                raise ValueError('source pin changed: '+name)
    try:
        check(); raw_manifest = Path(manifest).read_bytes()
        if len(raw_manifest) > 2*1024*1024:
            raise ValueError('oversized pin manifest')
        sources = json.loads(raw_manifest)
        if not isinstance(sources, dict) or not 1 <= len(sources) <= 512:
            raise ValueError('pin manifest shape')
        for name, sha in sources.items():
            if not isinstance(name, str) or not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('pin entry')
            pins[str((ROOT/name).resolve())] = sha
        required = {str(Path(__file__).resolve()), str((ROOT/FIXTURE).resolve()), str((ROOT/'src/verify.py').resolve())}
        if not required <= pins.keys() or pins[str((ROOT/FIXTURE).resolve())] != FIXTURE_SHA:
            raise ValueError('missing reviewed source pins')
        pins[str(Path(manifest).resolve())] = hashlib.sha256(raw_manifest).hexdigest()
        verify_pins(); pins_ready = True; check()
        source = json.loads((ROOT/FIXTURE).read_text())
        if source['n'] != SOURCE_N or source.get('source_record') != 1 or source.get('raw_sha256') != RAW_SHA:
            raise ValueError('selected source identity')
        checks = []
        for validator in (verify_certificate, verify_certificate_bruteforce):
            check(); checks.append(validator(source)); check()
        if not all(v['valid'] and v['point_count'] == 2*SOURCE_N and v['normalized_sha256'] == NORMALIZED for v in checks):
            raise ValueError('source dual validation')
        report['source_validation'] = checks
        points = tuple(sorted(map(tuple, source['points'])))
        result = cover_family(points, SOURCE_N, check=check, counters=report['counters'])
        report.update({key: result[key] for key in ('old_complete', 'new_complete', 'geometry_complete', 'certificate_complete')})
        report['unexcluded_gaps'] = [list(divmod(i, SOURCE_N+1)) for i in range((SOURCE_N+1)**2) if result['uncovered'] & (1 << i)]
        report['obstructions'] = [{'gap': gap, **entry} for gap, entry in sorted(result['certificates'].items())]
        check()
        if result['certificate_complete']:
            report.update(status='selected_family_obstructed', closure=True)
        elif result['geometry_complete']:
            gap = report['unexcluded_gaps'][0]
            check(); candidate = {'n': SOURCE_N+1, 'points': [mapped_point(p, *gap) for p in points]+[tuple(gap)],
                                  'source_record': 1, 'source_sha256': FIXTURE_SHA, 'gap': gap,
                                  'normalized_source_sha256': NORMALIZED, 'novelty_claimed': False}
            report['counters']['phase'] = 'candidate_validator1'
            a = verify_certificate(candidate); check()
            report['counters']['phase'] = 'candidate_validator2'
            b = verify_certificate_bruteforce(candidate)
            if not (a['valid'] and b['valid'] and a['point_count'] == b['point_count'] == 2*SOURCE_N+1
                    and a['normalized_sha256'] == b['normalized_sha256']):
                raise ValueError('candidate dual validation disagreement')
            # No deadline or pin check may interpose between successful validator2 and save.
            atomic(out/'valid149.json', {'certificate': candidate, 'validators': [a, b]})
            report.update(witness_saved=True, candidate_validators=[a, b], status='verified149')
            check()
        else:
            raise ValueError('partial geometry cannot produce a positive result')
        report['complete'] = True
    except TimeoutError as error:
        report.update(status='timeout', error=str(error), complete=False, closure=False)
    except Exception as error:
        report.update(status='error', error=f'{type(error).__name__}: {error}', complete=False, closure=False)
    try:
        if not pins_ready:
            raise ValueError('initial pin validation incomplete')
        verify_pins(); check(); report['identity_valid'] = True
    except Exception as error:
        report.update(status='timeout' if isinstance(error, TimeoutError) else 'error',
                      error=str(error), identity_valid=False, complete=False, closure=False)
    report.update(pins=pins, elapsed_seconds=clock()-start)
    atomic(out/'report.json', report)
    try:
        check()
    except TimeoutError as error:
        report.update(status='timeout', error=str(error), complete=False, closure=False,
                      elapsed_seconds=clock()-start)
        atomic(out/'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--source-pins', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=25)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.output_dir, args.source_pins, args.seconds, started=ENTRY_STARTED)
    print(json.dumps({k: report.get(k) for k in ('status', 'complete', 'closure', 'witness_saved', 'elapsed_seconds', 'counters')}, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
