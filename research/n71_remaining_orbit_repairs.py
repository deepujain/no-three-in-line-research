"""One bounded finite batch for the remaining33 pinned n71 orbit deletions.

No resume/protocol/guard is implemented. Root supplies owned30s/256MiB;
all cases share one <=25s soft deadline. Published finite/packed sources stay
unchanged. The parameterized deletion helper is also tested on tiny subsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.n71_boundary_extension import FIXTURE_SHA256, validate_fixture
from research.n71_central_orbit_repair import DELETED_N71 as CENTRAL, edge_points, first_added_conflict, atomic, encode
from research.n71_noncentral_orbit_repair import DELETED_N71 as FIRST, edge_specs, degree_choices, valid_seconds
from src.verify import verify_certificate, verify_certificate_bruteforce

CASE_MANIFEST = ROOT/'data/n71-remaining33-orbit-cases.json'
CASE_MANIFEST_SHA256 = 'b2f8f9d3c49c4d91e72eb2f79473c51744434c39c4323e37c1da813badde4f54'
SCOPE = 'Only the remaining33 pinned four-orbit deletions of this centered fixed n71 near-quarter fixture, excluding the separately checked central and first noncentral orbits; exact readdition allowed.'


def validate_cases(fixture, raw):
    if hashlib.sha256(raw).hexdigest() != CASE_MANIFEST_SHA256:
        raise ValueError('fixed33-case manifest bytes differ')
    manifest = json.loads(raw)
    source = {tuple(p) for p in fixture['points']}
    groups = sorted({tuple(sorted(((x,y),(y,70-x),(70-x,70-y),(70-y,x))))
                     for x,y in source if x != y})
    expected = [{'source_orbit_index':i,'points':[list(p) for p in orbit]}
                for i,orbit in enumerate(groups) if orbit not in (CENTRAL,FIRST)]
    if (len(groups) != 35 or len(expected) != 33 or
            manifest != {'schema':1,'fixture_sha256':FIXTURE_SHA256,'source_n':71,
                'excluded_orbits':[[list(p) for p in o] for o in (CENTRAL,FIRST)],'cases':expected}):
        raise ValueError('exact remaining33 source-orbit coverage differs')
    return manifest['cases']


def evaluate_deletion(n, retained, removed, *, check, on_witness,
                      verifiers=(verify_certificate,verify_certificate_bruteforce)):
    """Finite prepared-subset calculation; retained must be independently valid.

    No source fixture, clock, output path or mutable published globals are
    replaced. Deadline and immediate witness persistence are caller callbacks.
    """
    result = {'status':'incomplete','complete':False,'degree_feasible_total':1094,
        'readdition_choices':51,'completed_candidates':0,'valid_candidates':0,
        'deleted_translated_orbit':[list(p) for p in sorted(removed)],
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
            raise RuntimeError('exact readdition count differs')
        result.update(deleted_edge_id=removed_id,labeled_edge_count=30,
            radius_demands=[[r,demands[r]] for r in sorted(demands)])
        bad = set()
        for i,points in enumerate(orbits):
            check()
            overlap = bool(set(points).intersection(retained))
            conflict = None if overlap else first_added_conflict(retained,points,check)
            if overlap or conflict is not None:
                bad.add(i)
            result['candidate_orbit_checks'].append({'edge_id':i,'edge':list(edges[i]),
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
                    raise RuntimeError('exact final cardinality/row/column differs')
                cert = {'n':n,'points':[list(p) for p in sorted(points)]}
                checks = [verify(cert) for verify in verifiers]
                if (len(checks) != 2 or checks[0]['valid'] != checks[1]['valid'] or
                        checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']):
                    raise RuntimeError('dual final verifiers disagree')
                record.update(result='dual_checked',valid=checks[0]['valid'],
                    normalized_sha256=checks[0]['normalized_sha256'],
                    blocking_triple=None if checks[0]['valid'] else checks[0]['conflicts'][0]['points'])
                if checks[0]['valid']:
                    on_witness(cert,ids,checks[0]['normalized_sha256'])
                    result['valid_candidates'] += 1
            result['candidate_checks'].append(record)
            result['completed_candidates'] += 1
            if result['valid_candidates']:
                result['status'] = 'witness'
                break
        else:
            result.update(status='complete',complete=True)
    except TimeoutError:
        result['status'] = 'timeout'
    return result


def evaluate_batch(n, source, cases, *, check, on_witness,
                   evaluator=evaluate_deletion):
    """One fixed ordered batch; a partial case is retained and never resumed."""
    report = {'status':'incomplete','complete':False,'declared_cases':len(cases),
        'declared_degree_choices':1094*len(cases),'case_results':[]}
    try:
        for case in cases:
            check()
            removed_source = {tuple(p) for p in case['points']}
            retained = tuple(sorted((x+4,y+4) for x,y in source-removed_source))
            removed = tuple(sorted((x+4,y+4) for x,y in removed_source))
            def save(cert,ids,digest):
                on_witness(case,cert,ids,digest)
            result = evaluator(n,retained,removed,check=check,on_witness=save)
            result.update(source_orbit_index=case['source_orbit_index'],deleted_source_orbit=case['points'])
            report['case_results'].append(result)
            if result['status'] in ('timeout','witness'):
                report['status'] = result['status']
                break
            if not result['complete']:
                raise RuntimeError('unknown incomplete case outcome')
        else:
            report.update(status='complete',complete=True)
    except TimeoutError:
        report['status'] = 'timeout'
    completed = [r['source_orbit_index'] for r in report['case_results'] if r['complete']]
    attempted = {r['source_orbit_index'] for r in report['case_results']}
    report.update(completed_case_indices=completed,completed_cases=len(completed),
        partial_case_indices=[r['source_orbit_index'] for r in report['case_results'] if not r['complete']],
        unstarted_case_indices=[c['source_orbit_index'] for c in cases if c['source_orbit_index'] not in attempted],
        completed_candidates=sum(r['completed_candidates'] for r in report['case_results']),
        valid_candidates=sum(r['valid_candidates'] for r in report['case_results']))
    return report


def check_batch(fixture, seconds, out, *, clock=time.monotonic):
    valid_seconds(seconds)
    started = clock()
    deadline = started+seconds
    if fixture.get('n') != 71:
        raise ValueError('fixed n71 fixture required')
    fixture_hash = validate_fixture(fixture)
    cases = validate_cases(fixture,CASE_MANIFEST.read_bytes())
    source = {tuple(p) for p in fixture['points']}
    def check():
        if clock() >= deadline:
            raise TimeoutError('shared batch soft deadline')
    def save(case,cert,ids,digest):
        cert['metadata'] = {'method':'centered_n71_remaining33_four_orbit_repairs',
            'source_normalized_sha256':fixture_hash,'source_orbit_index':case['source_orbit_index'],
            'deleted_source_orbit':case['points'],'edge_ids':list(ids),'novelty_claim':False}
        atomic(Path(out)/('witness-'+digest+'.json'),encode(cert))
    report = evaluate_batch(79,source,cases,check=check,on_witness=save)
    report.update(scope=SCOPE,fixture_normalized_sha256=fixture_hash,
        case_manifest_sha256=CASE_MANIFEST_SHA256,source_n=71,n=79,
        translation=[4,4],elapsed_seconds=clock()-started,soft_seconds=seconds)
    return report


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
    report = check_batch(fixture,args.seconds,args.output_dir)
    report['fixture_sha256'] = FIXTURE_SHA256
    atomic(args.output_dir/'report.json',encode(report))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['status'] in ('complete','witness') else 2


if __name__ == '__main__':
    raise SystemExit(main())
