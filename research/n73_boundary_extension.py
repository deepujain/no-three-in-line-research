"""Prepared bounded n73-to-n79 check; do not run without separate authorization."""
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
from research.n71_boundary_extension import validate_fixture
from research.diagonal_secant_checkpoint import atomic, encode

RAW_HASH = '6053ddbe7a6a5c445a04b406a7554144e2990a7384db11d932ac961a7ebd205e'
FIXTURE_HASH = '0c99133e2025005e99a702a8538752aa58ee763f4a01d6531f8015c423db29ae'
NORMALIZED_HASH = '2e7f40e3be9a53dda71ee01ee076b30f8ad632707d14cc51616afbeb752b798b'
ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&@?!()[]<>{}=*+|-/~^_:;,.'


def load_pinned(raw_path, fixture_path):
    raw = raw_path.read_bytes(); data = fixture_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RAW_HASH or hashlib.sha256(data).hexdigest() != FIXTURE_HASH:
        raise ValueError('source or fixture byte hash mismatch')
    fixture = json.loads(data)
    if len(raw) != 148 or raw[-1:] != b'\n' or raw.count(b'\n') != 1:
        raise ValueError('invalid source encoding')
    code = raw[:-1].decode('ascii')
    if len(code) != 147 or code[0] != 'c' or fixture.get('n') != 73:
        raise ValueError('invalid source dimensions or class')
    if fixture.get('alphabet') != ALPHABET or fixture.get('encoded_source') != code:
        raise ValueError('fixture encoding mismatch')
    points = [[ALPHABET.index(code[1+2*y+j]), y] for y in range(73) for j in range(2)]
    if points != fixture.get('points') or any(x >= 73 for x, y in points):
        raise ValueError('decoded fixture mismatch')
    return fixture


def boundary_orbits(n):
    if type(n) is not int or n < 7 or n % 2 != 1:
        raise ValueError('odd target n >= 7 required')
    c = n // 2
    result = []
    for u, v in itertools.combinations(range(c-2, c+1), 2):
        for sign in (1, -1):
            x, y = c+u, c+sign*v
            points = tuple(sorted(((x,y), (y,n-1-x), (n-1-x,n-1-y), (n-1-y,x))))
            result.append(((u,v), points))
    if len(result) != 6 or len({p for _, p in result}) != 6 or any(len(set(p)) != 4 for _, p in result):
        raise RuntimeError('orbit invariant failed')
    return tuple(result)


def selections(n):
    orbits = boundary_orbits(n); radii = range(n//2-2, n//2+1)
    choices = []
    for ids in itertools.combinations(range(6), 3):
        degree = {r: 0 for r in radii}
        for i in ids:
            u, v = orbits[i][0]; degree[u] += 1; degree[v] += 1
        if all(v == 2 for v in degree.values()):
            choices.append(ids)
    if len(choices) != 8:
        raise RuntimeError('selection invariant failed')
    return tuple(choices)


def check_extensions(fixture, seconds, out, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds, (int,float)) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('invalid time budget')
    started = clock(); deadline = started + seconds
    fixture_hash = validate_fixture(fixture)
    if fixture_hash != NORMALIZED_HASH or fixture.get('n') != 73:
        raise ValueError('fixture normalized hash mismatch')
    n = 79; base = [(x+3,y+3) for x,y in fixture['points']]
    orbits = boundary_orbits(n); choices = selections(n)
    report = {'status':'incomplete', 'complete':False, 'source_n':73, 'n':n,
              'fixture_normalized_sha256':fixture_hash, 'translation':[3,3],
              'boundary_orbits':len(orbits), 'row_feasible_selections':len(choices),
              'completed_candidates':0, 'valid_candidates':0, 'candidate_checks':[],
              'scope':'Only zero-deletion near-quarter-turn extensions of this centered pinned fixture.'}
    for ids in choices:
        if clock() >= deadline:
            break
        points = base + [p for i in ids for p in orbits[i][1]]
        cert = {'n':n, 'points':[list(p) for p in sorted(points)]}
        checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
        if checks[0]['valid'] != checks[1]['valid'] or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
            raise RuntimeError('verifiers disagree')
        if checks[0]['valid']:
            if checks[0]['point_count'] != 2*n:
                raise RuntimeError('candidate cardinality mismatch')
            cert['metadata'] = {'method':'centered_n73_boundary_extension', 'source_normalized_sha256':fixture_hash,
                                'boundary_orbit_ids':list(ids), 'normalized_sha256':checks[0]['normalized_sha256'], 'novelty_claim':False}
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
    p.add_argument('--raw', type=Path, required=True); p.add_argument('--fixture', type=Path, required=True)
    p.add_argument('--seconds', type=float, required=True); p.add_argument('--output-dir', type=Path, required=True)
    args = p.parse_args(); fixture = load_pinned(args.raw, args.fixture)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = check_extensions(fixture, args.seconds, args.output_dir)
    report['raw_sha256'] = RAW_HASH; report['fixture_sha256'] = FIXTURE_HASH
    atomic(args.output_dir/'report.json', encode(report))
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
