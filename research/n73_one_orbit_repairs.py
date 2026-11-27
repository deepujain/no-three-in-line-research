"""Bounded all36 one-four-orbit repairs of the pinned centered n73 fixture.

One shared <=25s soft deadline; Root owns the existing30s/256MiB host guard.
No resume, protocol or numerical launch is implemented here. Published n71 and
packed sources are unchanged. Tiny tests use prepared n9/n11 subsets only.
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
sys.path.insert(0,str(ROOT))
from research.n73_boundary_extension import RAW_HASH, FIXTURE_HASH as FIXTURE_SHA256, NORMALIZED_HASH, load_pinned
from research.n71_boundary_extension import validate_fixture
from research.n71_central_orbit_repair import edge_points, first_added_conflict, atomic, encode
from research.n71_noncentral_orbit_repair import valid_seconds
from src.verify import verify_certificate, verify_certificate_bruteforce

CASE_MANIFEST = ROOT/'data/n73-one-orbit-repair-cases.proposal.json'
CASE_MANIFEST_SHA256 = 'ca6147bee2ae9bcde4118f2ccdfb855af87c44cd5dd49e2aa3ec60580fbeabae'
SCOPE = 'Only all36 original four-orbit deletions of this pinned centered n73 near-quarter fixture, with four four-orbits added and exact readdition allowed.'


def edge_specs(inner_radii, outer_radii):
    inner,outer = tuple(inner_radii),tuple(outer_radii)
    if (len(inner)!=2 or len(set(inner))!=2 or len(outer)!=3 or len(set(outer))!=3 or
            any(type(r) is not int or r<0 for r in inner) or
            any(type(r) is not int or r<=0 for r in outer) or max(inner)>=min(outer)):
        raise ValueError('two distinct inner and three positive outer radii required')
    return tuple((u,v,sign) for u,v in itertools.combinations(sorted(inner+outer),2)
                 for sign in ((1,) if u==0 else (1,-1)))


def degree_choices(edges, demands, check=lambda:None):
    choices = []
    for index,ids in enumerate(itertools.combinations(range(len(edges)),4)):
        if index%256==0:check()
        degree = dict.fromkeys(demands,0)
        for i in ids:
            u,v,_ = edges[i]
            degree[u] += 1
            degree[v] += 1
        if degree==demands:choices.append(ids)
    check()
    expected_edges,expected_choices = (16,62) if 0 in demands else (20,124)
    if len(edges)!=expected_edges or len(choices)!=expected_choices:
        raise RuntimeError('n73 four-edge degree enumeration differs')
    return tuple(choices)


def validate_cases(fixture, raw):
    if hashlib.sha256(raw).hexdigest()!=CASE_MANIFEST_SHA256:
        raise ValueError('fixed36-case manifest bytes differ')
    manifest = json.loads(raw)
    source = {tuple(p) for p in fixture['points']}
    groups = sorted({tuple(sorted(((x,y),(y,72-x),(72-x,72-y),(72-y,x))))
                     for x,y in source if x!=y})
    expected = []
    for i,orbit in enumerate(groups):
        inner = sorted({abs(v-36) for p in orbit for v in p})
        edges,count = (16,62) if 0 in inner else (20,124)
        expected.append({'source_orbit_index':i,'points':[list(p) for p in orbit],
            'inner_radii':inner,'labeled_edges':edges,'raw_four_edge_subsets':math.comb(edges,4),
            'degree_choices':count,'exact_readdition_choices':8})
    if (len(expected)!=36 or sum(0 in c['inner_radii'] for c in expected)!=1 or
            manifest!={'schema':1,'source_n':73,'target_n':79,'translation':[3,3],
                'fixture_sha256':FIXTURE_SHA256,'outer_radii':[37,38,39],'cases':expected}):
        raise ValueError('exact n73 all36 orbit coverage differs')
    return manifest['cases']


def evaluate_deletion(n, retained, removed, *, check, on_witness,
                      verifiers=(verify_certificate,verify_certificate_bruteforce)):
    """Finite prepared-subset calculation; retained must be independently valid.

    No source fixture, clock, output path or mutable published globals are
    replaced. Deadline and immediate witness persistence are caller callbacks.
    """
    center = n//2
    inner = tuple(sorted({abs(v-center) for p in removed for v in p}))
    expected = 62 if 0 in inner else 124
    result = {'status':'incomplete','complete':False,'degree_feasible_total':expected,
        'readdition_choices':8,'completed_candidates':0,'valid_candidates':0,
        'deleted_translated_orbit':[list(p) for p in sorted(removed)],
        'candidate_orbit_checks':[],'candidate_checks':[]}
    try:
        check()
        center = n//2
        inner = tuple(sorted({abs(v-center) for p in removed for v in p}))
        outer = tuple(range(center-2,center+1))
        edges = edge_specs(inner,outer)
        demands = {**{r:1 for r in inner},**{r:2 for r in outer}}
        choices = degree_choices(edges,demands,check)
        orbits = tuple(edge_points(n,e) for e in edges)
        removed_id = orbits.index(tuple(sorted(removed)))
        if sum(removed_id in ids for ids in choices) != 8:
            raise RuntimeError('exact readdition count differs')
        result.update(deleted_edge_id=removed_id,labeled_edge_count=len(edges),
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
        'declared_degree_choices':sum(c['degree_choices'] for c in cases),'case_results':[]}
    try:
        for case in cases:
            check()
            removed_source = {tuple(p) for p in case['points']}
            retained = tuple(sorted((x+3,y+3) for x,y in source-removed_source))
            removed = tuple(sorted((x+3,y+3) for x,y in removed_source))
            def save(cert,ids,digest):
                on_witness(case,cert,ids,digest)
            result = evaluator(n,retained,removed,check=check,on_witness=save)
            if result['complete'] and result['completed_candidates']!=case['degree_choices']:
                raise RuntimeError('complete case coverage differs from pinned manifest')
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
    if fixture.get('n')!=73:
        raise ValueError('fixed n73 fixture required')
    fixture_hash = validate_fixture(fixture)
    if fixture_hash!=NORMALIZED_HASH:
        raise ValueError('pinned n73 normalized fixture differs')
    cases = validate_cases(fixture,CASE_MANIFEST.read_bytes())
    source = {tuple(p) for p in fixture['points']}
    def check():
        if clock()>=deadline:raise TimeoutError('shared batch soft deadline')
    def save(case,cert,ids,digest):
        cert['metadata'] = {'method':'centered_n73_all36_four_orbit_repairs',
            'source_normalized_sha256':fixture_hash,'source_orbit_index':case['source_orbit_index'],
            'deleted_source_orbit':case['points'],'edge_ids':list(ids),'novelty_claim':False}
        atomic(Path(out)/('witness-'+digest+'.json'),encode(cert))
    report = evaluate_batch(79,source,cases,check=check,on_witness=save)
    report.update(scope=SCOPE,fixture_normalized_sha256=fixture_hash,
        case_manifest_sha256=CASE_MANIFEST_SHA256,source_n=73,n=79,
        translation=[3,3],elapsed_seconds=clock()-started,soft_seconds=seconds)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,required=True)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(argv)
    fixture = load_pinned(args.raw,args.fixture)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    report = check_batch(fixture,args.seconds,args.output_dir)
    report.update(raw_sha256=RAW_HASH,fixture_sha256=FIXTURE_SHA256)
    atomic(args.output_dir/'report.json',encode(report))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['status'] in ('complete','witness') else 2


if __name__ == '__main__':
    raise SystemExit(main())
