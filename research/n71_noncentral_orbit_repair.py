"""Finite repair after the lexicographically first noncentral n71 four-orbit.

Only the pinned source fixture/deletion is exposed by CLI. Root supplies the
existing owned30s/256MiB guard; this checker has a <=25s soft deadline and no
resume mode. Frozen central-case helpers supply geometry filtering/publication.
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
from research.n71_central_orbit_repair import edge_points, first_added_conflict, atomic, encode
from src.verify import verify_certificate, verify_certificate_bruteforce

DELETED_N71 = ((0,19), (19,70), (51,0), (70,51))


def edge_specs(inner_radii, outer_radii):
    inner, outer = tuple(inner_radii), tuple(outer_radii)
    if (len(inner) != 2 or len(set(inner)) != 2 or len(outer) != 4 or
            len(set(outer)) != 4 or any(type(r) is not int or r <= 0 for r in inner+outer) or
            max(inner) >= min(outer)):
        raise ValueError('two positive inner radii and four distinct outer radii required')
    return tuple((u,v,sign) for u,v in itertools.combinations(sorted(inner+outer),2)
                 for sign in (1,-1))


def degree_choices(edges, demands, check=lambda: None):
    choices = []
    for index, ids in enumerate(itertools.combinations(range(len(edges)),5)):
        if index % 256 == 0:
            check()
        degree = dict.fromkeys(demands,0)
        for i in ids:
            u,v,_ = edges[i]
            degree[u] += 1
            degree[v] += 1
        if degree == demands:
            choices.append(ids)
    check()
    if len(edges) != 30 or len(choices) != 1094:
        raise RuntimeError('noncentral degree enumeration differs')
    return tuple(choices)


def valid_seconds(seconds):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('soft budget must be positive and <=25s')


def _evaluate(n, retained, removed, seconds, out, *, fixture_hash=None,
              clock=time.monotonic, started=None):
    """Prepared-subset boundary for tiny n13 tests; retained geometry must be valid."""
    valid_seconds(seconds)
    started = clock() if started is None else started
    deadline = started+seconds
    def check():
        if clock() >= deadline:
            raise TimeoutError('soft deadline')
    report = {'status':'incomplete','complete':False,'n':n,'translation':[4,4],
        'source_n':n-8,'fixture_normalized_sha256':fixture_hash,
        'scope':'Only the pinned centered n71 fixture with its lexicographically first noncentral four-orbit deleted and five four-orbits added, allowing exact readdition.',
        'degree_feasible_total':1094,'readdition_choices':51,
        'completed_candidates':0,'valid_candidates':0,
        'candidate_orbit_checks':[],'candidate_checks':[]}
    try:
        check()
        center = n//2
        inner = tuple(sorted({abs(v-center) for p in removed for v in p}))
        outer = tuple(range(center-3,center+1))
        edges = edge_specs(inner,outer)
        demands = {**{r:1 for r in inner},**{r:2 for r in outer}}
        choices = degree_choices(edges,demands,check)
        orbits = tuple(edge_points(n,e) for e in edges)
        removed_id = orbits.index(tuple(sorted(removed)))
        if sum(removed_id in ids for ids in choices) != 51:
            raise RuntimeError('readdition count differs')
        report.update(deleted_translated_orbit=[list(p) for p in sorted(removed)],
            deleted_source_orbit=[list((x-4,y-4)) for x,y in sorted(removed)],
            deleted_edge_id=removed_id,labeled_edge_count=30,
            radius_demands=[[r,demands[r]] for r in sorted(demands)])
        bad = set()
        for i,points in enumerate(orbits):
            check()
            overlap = bool(set(points).intersection(retained))
            conflict = None if overlap else first_added_conflict(retained,points,check)
            if overlap or conflict is not None:
                bad.add(i)
            report['candidate_orbit_checks'].append({'edge_id':i,'edge':list(edges[i]),
                'points':[list(p) for p in points],'retained_overlap':overlap,
                'blocking_triple':conflict,'admissible':not overlap and conflict is None})
        for ids in choices:
            check()
            blocked = next((i for i in ids if i in bad),None)
            record = {'edge_ids':list(ids),'readds_deleted':removed_id in ids}
            if blocked is not None:
                record.update(result='filtered_orbit',blocking_edge_id=blocked)
            else:
                points = list(retained)+[p for i in ids for p in orbits[i]]
                if (len(points) != 2*n or len(set(points)) != 2*n or
                        any(sum(y==r for x,y in points)!=2 or sum(x==r for x,y in points)!=2
                            for r in range(n))):
                    raise RuntimeError('final exact row/column/cardinality differs')
                cert = {'n':n,'points':[list(p) for p in sorted(points)]}
                checks = [verify_certificate(cert),verify_certificate_bruteforce(cert)]
                if (checks[0]['valid'] != checks[1]['valid'] or
                        checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']):
                    raise RuntimeError('dual final verifiers disagree')
                record.update(result='dual_checked',valid=checks[0]['valid'],
                    normalized_sha256=checks[0]['normalized_sha256'],
                    blocking_triple=None if checks[0]['valid'] else checks[0]['conflicts'][0]['points'])
                if checks[0]['valid']:
                    cert['metadata'] = {'method':'centered_n71_first_noncentral_four_orbit_repair',
                        'source_normalized_sha256':fixture_hash,'edge_ids':list(ids),
                        'deleted_source_orbit':report['deleted_source_orbit'],'novelty_claim':False}
                    atomic(Path(out)/('witness-'+checks[0]['normalized_sha256']+'.json'),encode(cert))
                    report['valid_candidates'] += 1
            report['candidate_checks'].append(record)
            report['completed_candidates'] += 1
            if report['valid_candidates']:
                report['status'] = 'witness'
                break
        else:
            report.update(status='complete',complete=True)
    except TimeoutError:
        report['status'] = 'timeout'
    report['elapsed_seconds'] = clock()-started
    return report


def check_case(fixture, seconds, out, *, clock=time.monotonic):
    valid_seconds(seconds)
    started = clock()
    if fixture.get('n') != 71:
        raise ValueError('only pinned n71 source case')
    fixture_hash = validate_fixture(fixture)
    source = {tuple(p) for p in fixture['points']}
    groups = {tuple(sorted(((x,y),(y,70-x),(70-x,70-y),(70-y,x))))
              for x,y in source if x != y and x != 35 and y != 35}
    if not groups or min(groups) != DELETED_N71 or not set(DELETED_N71).issubset(source):
        raise ValueError('pinned lexicographically first noncentral orbit differs')
    retained = tuple(sorted((x+4,y+4) for x,y in source-set(DELETED_N71)))
    removed = tuple(sorted((x+4,y+4) for x,y in DELETED_N71))
    return _evaluate(79,retained,removed,seconds,out,fixture_hash=fixture_hash,
                     clock=clock,started=started)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(argv)
    raw = args.fixture.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        parser.error('pinned fixture bytes differ')
    fixture = json.loads(raw)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    report = check_case(fixture,args.seconds,args.output_dir)
    report['fixture_sha256'] = FIXTURE_SHA256
    atomic(args.output_dir/'report.json',encode(report))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['status'] in ('complete','witness') else 2


if __name__ == '__main__':
    raise SystemExit(main())
