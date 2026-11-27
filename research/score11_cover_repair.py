"""Minimal conflict-cover repair of one pinned score-11 state; no unapproved host run."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.trade_search import degree_two, point_conflicts
from src.verify import verify_certificate, verify_certificate_bruteforce
from research.diagonal_secant_checkpoint import atomic, encode

SOURCE_BYTES = '9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26'
SOURCE_NORMALIZED = 'f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d'


def load_source(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_BYTES:
        raise ValueError('source byte hash mismatch')
    cert = json.loads(raw)
    checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
    if cert.get('n') != 79 or any(c['errors'] or c['point_count'] != 158 or c['conflict_count'] != 11 or c['normalized_sha256'] != SOURCE_NORMALIZED for c in checks):
        raise ValueError('source dual verification failed')
    conflicts = [{tuple(p) for p in item['points']} for item in checks[0]['conflicts']]
    other = {frozenset(map(tuple, item['points'])) for item in checks[1]['conflicts']}
    if len(conflicts) != 11 or {frozenset(t) for t in conflicts} != other:
        raise ValueError('source conflict sets disagree')
    points = {tuple(p) for p in cert['points']}
    if not degree_two(points, 79):
        raise ValueError('source degree mismatch')
    return points, conflicts


def minimal_covers(conflicts, limit, deadline, clock):
    """Complete minimal covers of size <=limit unless deadline interrupts."""
    conflicts = tuple(frozenset(t) for t in conflicts)
    if any(not t for t in conflicts) or type(limit) is not int or limit < 0:
        raise ValueError('invalid conflict graph or bound')
    found = set()
    def visit(chosen):
        if clock() >= deadline:
            raise TimeoutError
        missing = next((t for t in conflicts if not chosen.intersection(t)), None)
        if missing is None:
            if all(any(t.intersection(chosen) == {p} for t in conflicts) for p in chosen):
                found.add(frozenset(chosen))
            return
        if len(chosen) == limit:
            return
        for p in sorted(missing):
            visit(chosen | {p})
    visit(set())
    return sorted(found, key=lambda x:(len(x), tuple(sorted(x))))


def candidates(points, removed):
    """All initially safe cells in rows and columns freed by removed points."""
    retained = points - removed
    row_count = Counter(x for x,y in retained); col_count = Counter(y for x,y in retained)
    return [p for p in itertools.product(sorted({x for x,y in removed}), sorted({y for x,y in removed}))
            if p not in retained and row_count[p[0]] < 2 and col_count[p[1]] < 2 and point_conflicts(p, retained) == 0]


def search_cover(n, points, removed, deadline, clock, emit):
    retained = points-removed; cells = candidates(points, removed)
    counts = {'candidate_cells':len(cells), 'nodes':0, 'witnesses':0}
    def visit(current, start, row_count, col_count):
        if clock() >= deadline:
            raise TimeoutError
        counts['nodes'] += 1
        if len(current) >= 2*n-1:
            emit(current)
            counts['witnesses'] += 1
        if len(current) == 2*n:
            return
        for i in range(start, len(cells)):
            p = cells[i]; x,y = p
            if row_count[x] >= 2 or col_count[y] >= 2 or point_conflicts(p, current):
                continue
            row_count[x] += 1; col_count[y] += 1
            visit(current | {p}, i+1, row_count, col_count)
            row_count[x] -= 1; col_count[y] -= 1
    visit(retained, 0, Counter(x for x,y in retained), Counter(y for x,y in retained))
    return counts


def run(source, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds, (float,int)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('soft limit must be in (0,25]')
    started = clock(); deadline = started + seconds
    points, conflicts = load_source(source)
    report = {'source_bytes_sha256':SOURCE_BYTES, 'source_normalized_sha256':SOURCE_NORMALIZED,
              'source_conflicts':11, 'cover_limit':4, 'complete':False, 'status':'incomplete',
              'scope':'Inclusion-minimal conflict covers of size at most four only; nonminimal extra deletions excluded.',
              'cover_count':None, 'covers':[], 'completed_covers':0, 'witness_events':0}
    def emit(pts):
        cert = {'n':79, 'points':[list(p) for p in sorted(pts)]}
        checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
        if any(not c['valid'] or c['point_count'] < 157 for c in checks) or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
            raise RuntimeError('witness dual verification failed')
        digest = checks[0]['normalized_sha256']
        cert['metadata'] = {'method':'score11_minimal_cover_repair', 'source_normalized_sha256':SOURCE_NORMALIZED,
                            'normalized_sha256':digest, 'novelty_claim':False}
        path = out/('witness-'+digest+'.json')
        # A duplicate can be reached via another cover; preserve the first verified file.
        if path.exists():
            if json.loads(path.read_text()) != cert:
                raise RuntimeError('conflicting witness file')
        else:
            atomic(path, encode(cert))
        report['witness_events'] += 1
    try:
        covers = minimal_covers(conflicts, 4, deadline, clock)
        report['cover_count'] = len(covers)
        report['covers'] = [[list(p) for p in sorted(c)] for c in covers]
        if not covers:
            report['status'] = 'no_minimal_cover_at_most_four'; report['complete'] = True
        else:
            for cover in covers:
                detail = search_cover(79, points, set(cover), deadline, clock, emit)
                report.setdefault('cover_results', []).append(detail)
                report['completed_covers'] += 1
            report['status'] = 'complete'; report['complete'] = True
    except TimeoutError:
        report['status'] = 'timeout'
    report['elapsed_seconds'] = clock()-started
    atomic(out/'report.json', encode(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True); p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--seconds', type=float, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.source, args.output_dir, args.seconds)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
