"""Check the 51 row-feasible centered n71-to-n79 zero-deletion extensions.

Preparation is not an authorization to execute the n79 check. Each candidate
is independently checked by both exact geometry validators. This is specific
to the pinned fixture and does not search arbitrary n79 configurations.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce
from research.diagonal_secant_checkpoint import atomic, encode

FIXTURE_SHA256 = '00a206f24c3044c252a57160c59af6ef39e2312f0132329b123143c2ad0c01d9'


def boundary_orbits(n):
    """Return canonical (radius endpoints, points) for the four outer radii."""
    if type(n) is not int or n < 9 or n % 2 != 1:
        raise ValueError('odd target n>=9 required')
    c = n//2
    orbits = []
    for u, v in itertools.combinations(range(c-3, c+1), 2):
        for sign in (1, -1):
            x, y = c+u, c+sign*v
            points = tuple(sorted(((x,y), (y,n-1-x), (n-1-x,n-1-y), (n-1-y,x))))
            orbits.append(((u,v), points))
    if len(orbits) != 12 or len({points for _, points in orbits}) != 12:
        raise RuntimeError('boundary orbit invariant failed')
    return tuple(orbits)


def selections(n):
    orbits = boundary_orbits(n); radii = range(n//2-3, n//2+1)
    result = []
    for ids in itertools.combinations(range(12), 4):
        degree = {r: 0 for r in radii}
        for i in ids:
            u, v = orbits[i][0]; degree[u] += 1; degree[v] += 1
        if all(v == 2 for v in degree.values()):
            result.append(ids)
    if len(result) != 51:
        raise RuntimeError('boundary selection count invariant failed')
    return tuple(result)


def validate_fixture(fixture):
    n = fixture.get('n') if isinstance(fixture, dict) else None
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('odd source grid required')
    checks = [verify_certificate(fixture), verify_certificate_bruteforce(fixture)]
    if not all(c['valid'] and c['point_count'] == 2*n for c in checks) or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
        raise ValueError('fixture failed dual verification or cardinality')
    points = {tuple(p) for p in fixture['points']}
    if any(x+y == n-1 for x,y in points):
        raise ValueError('fixture contains anti-diagonal point')
    diagonal = {(x,y) for x,y in points if x == y}
    off = points-diagonal
    if len(diagonal) != 2 or {(n-1-x,n-1-y) for x,y in diagonal} != diagonal:
        raise ValueError('fixture diagonal pair mismatch')
    if {(y,n-1-x) for x,y in off} != off:
        raise ValueError('fixture off-diagonal quarter-turn mismatch')
    return checks[0]['normalized_sha256']


def check_extensions(fixture, seconds, out, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds, (int,float)) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('invalid time budget')
    started = clock(); deadline = started+seconds
    fixture_hash = validate_fixture(fixture)
    source_n = fixture['n']; n = source_n+8
    base = [(x+4,y+4) for x,y in fixture['points']]
    orbits = boundary_orbits(n); choices = selections(n)
    report = {'status':'incomplete', 'complete':False, 'source_n':source_n, 'n':n,
              'fixture_normalized_sha256':fixture_hash, 'translation':[4,4],
              'boundary_orbits':len(orbits), 'row_feasible_selections':len(choices),
              'completed_candidates':0, 'valid_candidates':0, 'candidate_checks':[],
              'scope':'Only zero-deletion near-quarter-turn extensions of this centered pinned fixture.'}
    for ids in choices:
        if clock() >= deadline:
            break
        points = base+[p for i in ids for p in orbits[i][1]]
        cert = {'n':n, 'points':[list(p) for p in sorted(points)]}
        checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
        if checks[0]['valid'] != checks[1]['valid'] or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
            raise RuntimeError('verifiers disagree')
        if checks[0]['valid']:
            if checks[0]['point_count'] != 2*n:
                raise RuntimeError('candidate cardinality mismatch')
            cert['metadata'] = {'method':'centered_n71_boundary_extension', 'source_normalized_sha256':fixture_hash,
                                'boundary_orbit_ids':list(ids), 'normalized_sha256':checks[0]['normalized_sha256'],
                                'novelty_claim':False}
            atomic(Path(out)/('witness-'+checks[0]['normalized_sha256']+'.json'), encode(cert))
            report['valid_candidates'] += 1
        report['candidate_checks'].append({'orbit_ids':list(ids), 'valid':checks[0]['valid'],
                                           'normalized_sha256':checks[0]['normalized_sha256']})
        report['completed_candidates'] += 1
    report['complete'] = report['completed_candidates'] == len(choices)
    report['status'] = 'complete' if report['complete'] else 'timeout'
    report['elapsed_seconds'] = clock()-started
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture', type=Path, required=True); p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args(); raw = args.fixture.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        p.error('fixture byte hash mismatch')
    fixture = json.loads(raw)
    if fixture.get('n') != 71:
        p.error('fixture must be n71')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = check_extensions(fixture, args.seconds, args.output_dir)
    report['fixture_sha256'] = FIXTURE_SHA256
    atomic(args.output_dir/'report.json', encode(report))
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    main()
