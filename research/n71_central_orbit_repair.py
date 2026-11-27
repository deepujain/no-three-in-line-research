"""Finite central-orbit deletion check for one pinned centered n71 fixture.

All 547 degree-feasible choices include the 51 deleted-orbit readditions.
No resume, alternate deletion, packed search or process guard is implemented.
Root separately owns a 30s/256MiB host guard around the <=25s soft checker.
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
from research.n71_boundary_extension import FIXTURE_SHA256, validate_fixture
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import verify_certificate, verify_certificate_bruteforce

DELETED_N71 = ((10, 35), (35, 10), (35, 60), (60, 35))


def edge_specs(inner_radius, outer_radii):
    """Arithmetic only; retain both orientations between positive radii."""
    if (type(inner_radius) is not int or inner_radius <= 0 or
            len(outer_radii) != 4 or len(set(outer_radii)) != 4 or
            any(type(r) is not int or r <= inner_radius for r in outer_radii)):
        raise ValueError('fixed central-edge radius shape')
    vertices = (0, inner_radius, *sorted(outer_radii))
    return tuple((u, v, sign) for u, v in itertools.combinations(vertices, 2)
                 for sign in ((1,) if u == 0 else (1, -1)))


def degree_choices(edges, demands, check=lambda: None):
    """Exhaustive five-of-25 arithmetic; no orbit geometry is constructed."""
    result = []
    for count, ids in enumerate(itertools.combinations(range(len(edges)), 5)):
        if count % 256 == 0:
            check()
        degree = dict.fromkeys(demands, 0)
        for i in ids:
            u, v, _ = edges[i]
            degree[u] += 1
            degree[v] += 1
        if degree == demands:
            result.append(ids)
    check()
    if len(edges) != 25 or len(result) != 547:
        raise RuntimeError('central degree enumeration differs')
    return tuple(result)


def edge_points(n, spec):
    u, v, sign = spec
    center = n//2
    x, y = center+u, center+sign*v
    points = tuple(sorted(((x, y), (y, n-1-x), (n-1-x, n-1-y), (n-1-y, x))))
    if len(set(points)) != 4 or any(x == y or x+y == n-1 for x, y in points):
        raise RuntimeError('four-orbit geometry differs')
    return points


def first_added_conflict(base, added, check=lambda: None):
    """Exact determinant test of every triple involving an added point.

    The retained base is a subset of the independently dual-verified fixture.
    Return coordinates of a rejection witness; never infer from approximate math.
    """
    points = tuple(base)+tuple(added)
    old_count = len(base)
    count = 0
    for i, j, k in itertools.combinations(range(len(points)), 3):
        if k < old_count:
            continue
        count += 1
        if count % 256 == 0:
            check()
        ax, ay = points[i]
        bx, by = points[j]
        cx, cy = points[k]
        if (bx-ax)*(cy-ay) == (by-ay)*(cx-ax):
            return [list(points[t]) for t in (i, j, k)]
    check()
    return None


def check_case(fixture, seconds, out, *, clock=time.monotonic):
    """n3 is the tiny analogous test boundary; CLI authorizes only pinned n71."""
    if (type(seconds) not in (int, float) or not math.isfinite(seconds) or
            not 0 < seconds <= 25):
        raise ValueError('soft budget must be positive and <=25s')
    started = clock()
    deadline = started+seconds
    def check():
        if clock() >= deadline:
            raise TimeoutError('soft deadline')
    report = {'status': 'incomplete', 'complete': False,
        'scope': 'Only this fixed centered fixture with its unique central four-orbit deleted, five four-orbits added, allowing exact deleted-orbit readdition.',
        'source_n': fixture.get('n'), 'translation': [4, 4],
        'degree_feasible_total': 547, 'readdition_choices': 51,
        'completed_candidates': 0, 'valid_candidates': 0,
        'candidate_orbit_checks': [], 'candidate_checks': []}
    try:
        check()
        fixture_hash = validate_fixture(fixture)
        source_n = fixture['n']
        if source_n not in (3, 71):
            raise ValueError('only fixed n71 or tiny n3 test boundary')
        center = source_n//2
        source_points = {tuple(p) for p in fixture['points']}
        central = tuple(sorted((x, y) for x, y in source_points if
                               x != y and (x == center or y == center)))
        if (len(central) != 4 or
                {(y, source_n-1-x) for x, y in central} != set(central) or
                (source_n == 71 and central != DELETED_N71)):
            raise ValueError('pinned central source orbit differs')
        inner = abs(central[0][0]-center) or abs(central[0][1]-center)
        n = source_n+8
        outer = tuple(range(n//2-3, n//2+1))
        edges = edge_specs(inner, outer)
        demands = {0: 1, inner: 1, **{r: 2 for r in outer}}
        choices = degree_choices(edges, demands, check)
        removed_id = edges.index((0, inner, 1))
        if sum(removed_id in ids for ids in choices) != 51:
            raise RuntimeError('deleted-orbit readdition count differs')
        retained = tuple(sorted((x+4, y+4) for x, y in source_points-set(central)))
        removed = tuple(sorted((x+4, y+4) for x, y in central))
        orbits = tuple(edge_points(n, edge) for edge in edges)
        if orbits[removed_id] != removed:
            raise RuntimeError('removed edge mapping differs')
        report.update(n=n, fixture_normalized_sha256=fixture_hash,
            deleted_source_orbit=[list(p) for p in central],
            deleted_translated_orbit=[list(p) for p in removed],
            deleted_edge_id=removed_id, radius_demands=[[r, demands[r]] for r in sorted(demands)],
            labeled_edge_count=len(edges))
        bad_orbits = set()
        for i, points in enumerate(orbits):
            check()
            overlap = bool(set(points).intersection(retained))
            conflict = None if overlap else first_added_conflict(retained, points, check)
            if overlap or conflict is not None:
                bad_orbits.add(i)
            report['candidate_orbit_checks'].append({'edge_id': i, 'edge': list(edges[i]),
                'points': [list(p) for p in points], 'retained_overlap': overlap,
                'blocking_triple': conflict, 'admissible': not overlap and conflict is None})
        for ids in choices:
            check()
            blocked = next((i for i in ids if i in bad_orbits), None)
            record = {'edge_ids': list(ids), 'readds_deleted': removed_id in ids}
            if blocked is not None:
                record.update(result='filtered_orbit', blocking_edge_id=blocked)
            else:
                points = list(retained)+[p for i in ids for p in orbits[i]]
                cert = {'n': n, 'points': [list(p) for p in sorted(points)]}
                if (len(points) != 2*n or len(set(points)) != 2*n or
                        any(sum(y == r for x, y in points) != 2 or
                            sum(x == r for x, y in points) != 2 for r in range(n))):
                    raise RuntimeError('final exact row/column/cardinality differs')
                checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
                if (checks[0]['valid'] != checks[1]['valid'] or
                        checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']):
                    raise RuntimeError('dual final verifiers disagree')
                record.update(result='dual_checked', valid=checks[0]['valid'],
                    normalized_sha256=checks[0]['normalized_sha256'],
                    blocking_triple=None if checks[0]['valid'] else checks[0]['conflicts'][0]['points'])
                if checks[0]['valid']:
                    cert['metadata'] = {'method': 'centered_n71_central_four_orbit_repair',
                        'source_normalized_sha256': fixture_hash, 'edge_ids': list(ids),
                        'deleted_source_orbit': report['deleted_source_orbit'], 'novelty_claim': False}
                    atomic(Path(out)/('witness-'+checks[0]['normalized_sha256']+'.json'), encode(cert))
                    report['valid_candidates'] += 1
            report['candidate_checks'].append(record)
            report['completed_candidates'] += 1
            if report['valid_candidates']:
                report['status'] = 'witness'
                break
        else:
            report['complete'] = True
            report['status'] = 'complete'
    except TimeoutError:
        report['status'] = 'timeout'
    report['elapsed_seconds'] = clock()-started
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path)
    parser.add_argument('--seconds', required=True, type=float)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    raw = args.fixture.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        parser.error('pinned fixture bytes differ')
    fixture = json.loads(raw)
    if fixture.get('n') != 71:
        parser.error('pinned n71 fixture required')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = check_case(fixture, args.seconds, args.output_dir)
    report['fixture_sha256'] = FIXTURE_SHA256
    atomic(args.output_dir/'report.json', encode(report))
    print(json.dumps(report, sort_keys=True))
    return 0 if report['status'] in ('complete', 'witness') else 2


if __name__ == '__main__':
    raise SystemExit(main())
