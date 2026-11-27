"""Bounded 2n-1 deficient-axis Metropolis walk; invalid states are not witnesses."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.trade_search import point_conflicts, rectangle_proposal
from src.verify import verify_certificate, verify_certificate_bruteforce

SOURCE = ROOT / 'data/trades-n79-seed270079-state.json'
SOURCE_SHA = '9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26'
SOURCE_NORMALIZED = 'f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d'
SEED = 279157
MAX_PROPOSALS = 100000


def axes(points, n, full=False):
    if type(n) is not int or n < 2 or not isinstance(points, set):
        raise ValueError('invalid board or point set')
    if any(not isinstance(p, tuple) or len(p) != 2 or any(type(z) is not int or not 0 <= z < n for z in p) for p in points):
        raise ValueError('invalid cell')
    if len(points) != 2 * n - (0 if full else 1):
        raise ValueError('invalid cardinality')
    rows = Counter(x for x, y in points)
    cols = Counter(y for x, y in points)
    def deficient(counts):
        values = [counts[i] for i in range(n)]
        if full:
            if any(v != 2 for v in values):
                raise ValueError('invalid full axis')
            return None
        if values.count(1) != 1 or values.count(2) != n - 1:
            raise ValueError('invalid deficient axis')
        return values.index(1)
    return deficient(rows), deficient(cols)


def relocation(points, n, point, axis):
    r, c = axes(points, n)
    if point not in points or axis not in ('row', 'column'):
        raise ValueError('invalid relocation input')
    x, y = point
    new = (r, y) if axis == 'row' else (x, c)
    if new == point or new in points:
        return None
    remaining = points - {point}
    delta = -point_conflicts(point, remaining) + point_conflicts(new, remaining)
    result = remaining | {new}
    axes(result, n)
    return delta, result


def rectangle(points, n, first, second):
    axes(points, n)
    if first not in points or second not in points or first == second:
        raise ValueError('invalid rectangle input')
    proposal = rectangle_proposal(points, first, second)
    if proposal is not None:
        axes(proposal[1], n)
    return proposal


def canonical_conflicts(report):
    return sorted(tuple(sorted(tuple(p) for p in conflict['points'])) for conflict in report['conflicts'])


def dual_audit(points, n, score, deadline, clock=time.monotonic, full=False):
    axes(points, n, full=full)
    cert = {'n': n, 'points': [list(p) for p in sorted(points)]}
    if clock() >= deadline:
        raise TimeoutError('before first validator')
    first = verify_certificate(cert)
    if clock() >= deadline:
        raise TimeoutError('before second validator')
    second = verify_certificate_bruteforce(cert)
    if (any(v['errors'] or v['point_count'] != len(points) or v['conflict_count'] != score or v['valid'] != (score == 0) for v in (first, second))
            or first['normalized_sha256'] != second['normalized_sha256']
            or canonical_conflicts(first) != canonical_conflicts(second)):
        raise RuntimeError('dual validator disagreement')
    return first, second


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def initialize(points, n, score):
    axes(points, n, full=True)
    incident = {p: point_conflicts(p, points - {p}) for p in points}
    removed = min(points, key=lambda p: (-incident[p], p))
    return points - {removed}, removed, score - incident[removed]


def audit_save(points, n, score, path, metadata, deadline, clock=time.monotonic):
    reports = dual_audit(points, n, score, deadline, clock)
    # Once validated, save even if the deadline passed in the second validator.
    atomic(path, {'n': n, 'points': [list(p) for p in sorted(points)],
                  'metadata': {**metadata, 'valid': score == 0, 'exact_conflict_count': score,
                               'normalized_sha256': reports[0]['normalized_sha256']},
                  'validators': list(reports)})
    return reports[0]['normalized_sha256']


def walk(n, source, source_score, out, *, seed=SEED, seconds=25, max_proposals=MAX_PROPOSALS,
         clock=time.monotonic, source_bytes_sha256=None, expected_source_normalized=None, pins=None, started=None):
    if type(seed) is not int or type(max_proposals) is not int or not 0 <= max_proposals <= MAX_PROPOSALS or isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('invalid run bounds')
    start = clock() if started is None else started
    deadline = start + seconds
    rng = random.Random(seed)
    report = {'n': n, 'seed': seed, 'max_proposals': max_proposals, 'seconds': seconds,
              'temperature': 2, 'source_bytes_sha256': source_bytes_sha256,
              'attempted': 0, 'legal': 0, 'accepted': 0,
              'moves': {k: {'attempted': 0, 'legal': 0, 'accepted': 0} for k in ('row', 'column', 'rectangle')},
              'best_score': None, 'best_normalized_sha256': None, 'status': 'timeout',
              'scope': 'exploratory walk, no retained-source constraint or nonexistence claim'}
    try:
        source_reports = dual_audit(source, n, source_score, deadline, clock, full=True)
        report['source_normalized_sha256'] = source_reports[0]['normalized_sha256']
        if expected_source_normalized is not None and report['source_normalized_sha256'] != expected_source_normalized:
            raise ValueError('source normalized hash mismatch')
        points, removed, score = initialize(source, n, source_score)
        report['removed'] = list(removed)
        metadata = {'seed': seed, 'source_bytes_sha256': source_bytes_sha256,
                    'source_normalized_sha256': report['source_normalized_sha256'],
                    'removed': list(removed), 'temperature': 2, 'max_proposals': max_proposals,
                    'seconds': seconds, 'pins': pins}
        report['best_normalized_sha256'] = audit_save(points, n, score, out, metadata, deadline, clock)
        report['best_score'] = score
        if score == 0:
            report['status'] = 'witness'
        else:
            for _ in range(max_proposals):
                if clock() >= deadline:
                    break
                draw = rng.randrange(4)
                kind = ('row', 'column', 'rectangle', 'rectangle')[draw]
                ordered = sorted(points)
                if kind == 'rectangle':
                    a, b = rng.sample(ordered, 2)
                    proposal = rectangle(points, n, a, b)
                else:
                    proposal = relocation(points, n, rng.choice(ordered), kind)
                report['attempted'] += 1
                report['moves'][kind]['attempted'] += 1
                if proposal is None:
                    continue
                report['legal'] += 1
                report['moves'][kind]['legal'] += 1
                delta, candidate = proposal
                if delta <= 0 or rng.random() < math.exp(-delta / 2):
                    points, score = candidate, score + delta
                    report['accepted'] += 1
                    report['moves'][kind]['accepted'] += 1
                    if score < report['best_score']:
                        digest = audit_save(points, n, score, out, metadata, deadline, clock)
                        report['best_score'], report['best_normalized_sha256'] = score, digest
                        if score == 0:
                            report['status'] = 'witness'
                            break
            else:
                report['status'] = 'proposal_cap'
    except TimeoutError as error:
        report['timeout_phase'] = str(error)
    except Exception as error:
        report['status'] = 'error'
        report['error'] = f'{type(error).__name__}: {error}'
    report['elapsed_seconds'] = clock() - start
    return report


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--best', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.best.resolve() == args.report.resolve() or args.best.exists() or args.report.exists():
        parser.error('best and report must be distinct new paths')
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('source byte hash mismatch')
    doc = json.loads(raw)
    if doc['n'] != 79 or doc['normalized_sha256'] != SOURCE_NORMALIZED:
        raise ValueError('source identity mismatch')
    points = [tuple(p) for p in doc['points']]
    if len(points) != len(set(points)):
        raise ValueError('duplicate source point')
    pin_paths = ('research/score11_deficiency_walk.py', 'src/trade_search.py', 'src/verify.py')
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in pin_paths}
    report = walk(79, set(points), 11, args.best, source_bytes_sha256=SOURCE_SHA,
                  expected_source_normalized=SOURCE_NORMALIZED, pins=pins, started=started)
    atomic(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['status'] == 'error' else 0


if __name__ == '__main__':
    sys.exit(main())
