"""One selected n76-to-n75 contraction census; actual use needs Lead allocation."""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from array import array
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

FIXTURE = 'data/published-n76.json'
FIXTURE_SHA = 'b5353bc39d2e65c81dca5a5bb5668b93f2c3d14ec80b627d0383cee26d298c17'
NORMALIZED = '97591fb28df5c742e090960c8feaf2fad9753b2a187a7b293139a0d574140ff5'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.'+path.name)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, sort_keys=True); f.write('\n')
            f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def intervals(coordinates, n):
    bounds = [-1, *sorted(set(coordinates)), n]
    return [(a+1, b-1) for a, b in zip(bounds, bounds[1:]) if b-a > 1]


def contract(points, c, r):
    return [(x-(x > c), y-(y > r)) for x, y in points if x != c and y != r]


def census(points, n, check=lambda: None, counters=None):
    """Count every surviving forbidden triple; retain one obstruction per occupied cut."""
    points = tuple(sorted(map(tuple, points)))
    if not 2 <= n <= 76 or len(points) != 2*n or len(set(points)) != len(points):
        raise ValueError('source dimensions/duplicates')
    if any(type(v) is not int or not 0 <= v < n for p in points for v in p):
        raise ValueError('source coordinate domain')
    if any(Counter(p[axis] for p in points) != Counter({v: 2 for v in range(n)}) for axis in (0, 1)):
        raise ValueError('source axis loads')
    count = counters if counters is not None else {}
    count.update(triples=0, rectangles=0, zero_rectangles=0, prefix_rows=0, obstruction_cut_tests=0)
    stride = n+1; diff = array('q', [0])*(stride*stride)
    if diff.itemsize != 8: raise ValueError('requires signed64 compact array')
    pending = set(points); witnesses = {}
    for triple in combinations(points, 3):
        check(); count['triples'] += 1
        xs, ys = zip(*triple)
        for c0, c1 in intervals(xs, n):
            xx = [x-(x > c0) for x in xs]
            for r0, r1 in intervals(ys, n):
                count['rectangles'] += 1
                yy = [y-(y > r0) for y in ys]
                if (xx[1]-xx[0])*(yy[2]-yy[0]) != (yy[1]-yy[0])*(xx[2]-xx[0]):
                    continue
                count['zero_rectangles'] += 1
                diff[c0*stride+r0] += 1; diff[(c1+1)*stride+r0] -= 1
                diff[c0*stride+r1+1] -= 1; diff[(c1+1)*stride+r1+1] += 1
                count['obstruction_cut_tests'] += len(pending)
                hit = [p for p in pending if c0 <= p[0] <= c1 and r0 <= p[1] <= r1]
                for p in hit:
                    witnesses[p] = triple; pending.remove(p)
    expected = math.comb(2*n, 3)
    if count['triples'] != expected or count['rectangles'] > 16*expected:
        raise ValueError('census counter bound')
    for c in range(n):
        check()
        for r in range(n):
            i = c*stride+r
            diff[i] += (diff[i-stride] if c else 0)+(diff[i-1] if r else 0)-(diff[i-stride-1] if c and r else 0)
            if not 0 <= diff[i] <= expected: raise ValueError('prefix score bound')
        count['prefix_rows'] += 1
    if any((diff[c*stride+r] > 0) != ((c, r) in witnesses) for c, r in points):
        raise ValueError('obstruction coverage mismatch')
    return diff, witnesses


def run(out, manifest, seconds=25, *, started=None, clock=time.monotonic):
    if isinstance(seconds, bool) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('duration')
    start = clock() if started is None else started; deadline = start+seconds
    def check():
        if clock() >= deadline: raise TimeoutError('shared soft deadline')
    pins = {}; report = {'method': 'selected_n76_to_n75_occupied_contraction', 'status': 'incomplete',
                        'complete': False, 'closure': False, 'witness_saved': False, 'counters': {},
                        'scope': 'Only152 occupied cuts of authenticated n76 configuration1; no repairs, alternative source or n77 fallback.'}
    def verify_pins():
        for name, sha in pins.items():
            if digest(name) != sha: raise ValueError('source pin changed: '+name)
    try:
        check(); sources = json.loads(Path(manifest).read_text())
        pins.update({str(ROOT/p): sha for p, sha in sources.items()})
        required = {str(Path(__file__).resolve()), str(ROOT/FIXTURE), str(ROOT/'src/verify.py')}
        if not required <= pins.keys() or pins[str(ROOT/FIXTURE)] != FIXTURE_SHA:
            raise ValueError('missing reviewed source pins')
        pins[str(Path(manifest).resolve())] = digest(manifest); verify_pins(); check()
        source = json.loads((ROOT/FIXTURE).read_text())
        if source['n'] != 76 or source.get('source_record') != 1: raise ValueError('selected source identity')
        checks = [verify_certificate(source), verify_certificate_bruteforce(source)]
        if not all(v['valid'] and v['point_count'] == 152 and v['normalized_sha256'] == NORMALIZED for v in checks):
            raise ValueError('source validation')
        report['source_validation'] = checks; check()
        points = tuple(sorted(map(tuple, source['points'])))
        scores, witnesses = census(points, 76, check, report['counters'])
        report['occupied_scores'] = [{'cut': p, 'triples': scores[p[0]*77+p[1]]} for p in points]
        report['obstructions'] = [{'cut': p, 'source_triple': t} for p, t in sorted(witnesses.items())]
        zero = [p for p in points if scores[p[0]*77+p[1]] == 0]
        report['zero_cuts'] = zero
        if zero:
            check(); candidate = {'n': 75, 'points': contract(points, *zero[0]), 'source_record': 1,
                                  'source_sha256': FIXTURE_SHA, 'cut': zero[0], 'novelty_claimed': False}
            a = verify_certificate(candidate); check(); b = verify_certificate_bruteforce(candidate)
            if not (a['valid'] and b['valid'] and a['point_count'] == b['point_count'] == 149):
                raise ValueError('candidate dual validation disagreement')
            atomic(out/'valid149.json', {'certificate': candidate, 'validators': [a, b]})
            report.update(witness_saved=True, candidate_validators=[a, b], status='verified149')
        else:
            report.update(status='selected_family_obstructed', closure=True)
        check(); report['complete'] = True
    except TimeoutError as e: report.update(status='timeout', error=str(e), complete=False, closure=False)
    except Exception as e: report.update(status='error', error=f'{type(e).__name__}: {e}', complete=False, closure=False)
    try: verify_pins()
    except Exception as e: report.update(status='error', error=str(e), identity_valid=False, complete=False, closure=False)
    else:
        report['identity_valid'] = True
        try: check()
        except TimeoutError as e: report.update(status='timeout', error=str(e), complete=False, closure=False)
    report.update(pins=pins, elapsed_seconds=clock()-start); atomic(out/'report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--source-pins', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=25); a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=False)
    r = run(a.output_dir, a.source_pins, a.seconds, started=ENTRY_STARTED)
    print(json.dumps(r, sort_keys=True)); return 0 if r['complete'] else 2


if __name__ == '__main__': sys.exit(main())
