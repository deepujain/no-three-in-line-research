"""Finite full-C4 n78-to-n80 repairs:230 raw degree factors,77 loop proofs.

New even-grid/doubled-radius arithmetic; frozen odd-grid sources stay unchanged.
Root supplies owned30s/256MiB; one <=25s soft deadline covers all39 cases.
No resume, new guard or host allocation is implemented.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.n71_central_orbit_repair import first_added_conflict, atomic, encode
from research.n71_noncentral_orbit_repair import valid_seconds
from src.verify import verify_certificate, verify_certificate_bruteforce

FIXTURE_SHA256 = '4c13bf3e807885f9e61d00593bb27d060b773e40d887f63d955d962d9890a912'
CASE_MANIFEST = ROOT/'data/n78-to-n80-one-orbit-cases.proposal.json'
CASE_MANIFEST_SHA256 = '687e33121e0365efe2b6e94ac6dc501c1ab0f3cae55bf20654b7a37ed23a8e4a'
OLD_LOOP = ((36,36),(36,41),(41,36),(41,41))
PROOF_TRIPLE = ((0,0),(37,37),(42,42))
SCOPE = 'Only centered full-C4 n78-to-n80 extensions of this fixed fixture with one original full four-orbit deleted and two added, including exact readdition. No n79 conclusion.'


def orbit_points(n,spec):
    """Integer coordinates from positive odd doubled radii, allowing loops."""
    u,v,sign = spec
    if (type(n) is not int or n<4 or n%2 or type(u) is not int or type(v) is not int or
            not 1<=u<=v<=n-1 or u%2!=1 or v%2!=1 or
            type(sign) is not int or sign not in (1,-1) or (u==v and sign!=1)):
        raise ValueError('even-grid doubled-radius orbit required')
    x,y = (n-1+u)//2,(n-1+sign*v)//2
    points = tuple(sorted(((x,y),(y,n-1-x),(n-1-x,n-1-y),(n-1-y,x))))
    if len(set(points))!=4:
        raise RuntimeError('fullC4 orbit cardinality differs')
    return points


def edge_specs(inner,outer):
    inner = tuple(inner)
    if (len(inner) not in (1,2) or len(set(inner))!=len(inner) or
            type(outer) is not int or outer%2!=1 or
            any(type(r) is not int or r<1 or r%2!=1 or r>=outer for r in inner)):
        raise ValueError('one/two positive odd inner radii below odd outer radius')
    vertices = tuple(sorted((*inner,outer)))
    return tuple((u,v,sign) for u,v in itertools.combinations_with_replacement(vertices,2)
                 for sign in ((1,) if u==v else (1,-1)))


def degree_choices(edges,demands,check=lambda:None):
    choices = []
    for ids in itertools.combinations(range(len(edges)),2):
        check()
        degree = dict.fromkeys(demands,0)
        for i in ids:
            u,v,_ = edges[i]
            degree[u] += 1
            degree[v] += 1
        if degree==demands:choices.append(ids)
    expected_edges,expected_choices = (4,2) if len(demands)==2 else (9,6)
    if len(edges)!=expected_edges or len(choices)!=expected_choices:
        raise RuntimeError('loop-inclusive degree enumeration differs')
    return tuple(choices)


def validate_fixture(fixture):
    if not isinstance(fixture,dict) or fixture.get('n')!=78:
        raise ValueError('pinned n78 fixture required')
    checks = [verify_certificate(fixture),verify_certificate_bruteforce(fixture)]
    if (not all(r['valid'] and r['point_count']==156 for r in checks) or
            checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']):
        raise ValueError('fixture dual geometry/cardinality differs')
    source = {tuple(p) for p in fixture['points']}
    if ({(y,77-x) for x,y in source}!=source or
            any(sum(y==r for x,y in source)!=2 or sum(x==r for x,y in source)!=2 for r in range(78))):
        raise ValueError('fixture fullC4/row/column structure differs')
    return checks[0]['normalized_sha256']


def validate_cases(fixture,raw):
    if hashlib.sha256(raw).hexdigest()!=CASE_MANIFEST_SHA256:
        raise ValueError('fixed39-case manifest bytes differ')
    manifest = json.loads(raw)
    source = {tuple(p) for p in fixture['points']}
    groups = sorted({tuple(sorted(((x,y),(y,77-x),(77-x,77-y),(77-y,x)))) for x,y in source})
    expected = []
    for i,orbit in enumerate(groups):
        radii = sorted({abs(2*v-77) for p in orbit for v in p})
        loop = len(radii)==1
        expected.append({'source_orbit_index':i,'points':[list(p) for p in orbit],
            'inner_radii_twice':radii,'deleted_is_diagonal_loop':loop,
            'all_free_radius_labeled_orbits':4 if loop else 9,'raw_two_orbit_subsets':6 if loop else 36,
            'degree_choices_including_outer_loop':2 if loop else 6,
            'outer_loop_rejections_by_proof':1 if loop else 2,
            'degree_choices_after_outer_loop_prune':1 if loop else 4,'exact_readdition_choices':1})
    if (len(groups)!=39 or groups[38]!=OLD_LOOP or
            sum(c['deleted_is_diagonal_loop'] for c in expected)!=1 or
            manifest!={'schema':1,'source_n':78,'target_n':80,'translation':[1,1],
                'fixture_sha256':FIXTURE_SHA256,
                'radius_encoding':'twice absolute radius about center; positive odd integers',
                'outer_radius_twice':79,'cases':expected}):
        raise ValueError('exact39-case fullC4 orbit coverage differs')
    return manifest['cases']


def evaluate_deletion(n,retained,removed,proof_triple,*,check,on_witness,
                      verifiers=(verify_certificate,verify_certificate_bruteforce)):
    """Prepared valid retained-subset boundary; proof membership is checked."""
    inner = tuple(sorted({abs(2*v-(n-1)) for p in removed for v in p}))
    loop = len(inner)==1
    result = {'status':'incomplete','complete':False,'degree_feasible_total':2 if loop else 6,
        'expected_outer_loop_rejections':1 if loop else 2,'readdition_choices':1,
        'completed_candidates':0,'valid_candidates':0,'proof_rejected_candidates':0,
        'candidate_orbit_checks':[],'candidate_checks':[]}
    try:
        check()
        outer = n-1
        edges = edge_specs(inner,outer)
        demands = {r:2 if loop else 1 for r in inner};demands[outer]=2
        choices = degree_choices(edges,demands,check)
        orbits = tuple(orbit_points(n,e) for e in edges)
        outer_id = edges.index((outer,outer,1))
        removed_id = orbits.index(tuple(sorted(removed)))
        if (sum(outer_id in ids for ids in choices)!=(1 if loop else 2) or
                sum(removed_id in ids for ids in choices)!=1):
            raise RuntimeError('outer-loop/readdition partition differs')
        required = sorted({i for ids in choices if outer_id not in ids for i in ids})
        result.update(labeled_orbits=[{'edge_id':i,'edge':list(e),'points':[list(p) for p in orbits[i]]}
                                    for i,e in enumerate(edges)],deleted_edge_id=removed_id,
                      outer_loop_edge_id=outer_id,geometry_filter_edge_ids=required,
                      radius_demands=[[r,demands[r]] for r in sorted(demands)])
        bad = set()
        for i in required:
            check()
            overlap = bool(set(orbits[i]).intersection(retained))
            conflict = None if overlap else first_added_conflict(retained,orbits[i],check)
            if overlap or conflict is not None:bad.add(i)
            result['candidate_orbit_checks'].append({'edge_id':i,'retained_overlap':overlap,
                'blocking_triple':conflict,'admissible':not overlap and conflict is None})
        for ids in choices:
            check()
            record = {'edge_ids':list(ids),'readds_deleted':removed_id in ids}
            if outer_id in ids:
                points = set(retained)|{p for i in ids for p in orbits[i]}
                triple = tuple(tuple(p) for p in proof_triple)
                if len(triple)!=3 or len(set(triple))!=3 or not set(triple)<=points:
                    raise RuntimeError('outer-loop proof points absent')
                (ax,ay),(bx,by),(cx,cy) = triple
                if (bx-ax)*(cy-ay)!=(by-ay)*(cx-ax):
                    raise RuntimeError('outer-loop proof determinant nonzero')
                record.update(result='outer_loop_proof',blocking_triple=[list(p) for p in triple])
                result['proof_rejected_candidates'] += 1
            else:
                blocked = next((i for i in ids if i in bad),None)
                if blocked is not None:
                    record.update(result='filtered_orbit',blocking_edge_id=blocked)
                else:
                    points = list(retained)+[p for i in ids for p in orbits[i]]
                    if (len(points)!=2*n or len(set(points))!=2*n or
                            any(sum(y==r for x,y in points)!=2 or sum(x==r for x,y in points)!=2 for r in range(n))):
                        raise RuntimeError('exact final cardinality/row/column differs')
                    cert = {'n':n,'points':[list(p) for p in sorted(points)]}
                    checks = [verify(cert) for verify in verifiers]
                    if (len(checks)!=2 or checks[0]['valid']!=checks[1]['valid'] or
                            checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']):
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
                result['status']='witness'
                break
        else:result.update(status='complete',complete=True)
    except TimeoutError:result['status']='timeout'
    return result


def evaluate_batch(n,source,cases,proof_triple,*,check,on_witness,evaluator=evaluate_deletion):
    report = {'status':'incomplete','complete':False,'declared_cases':len(cases),
        'declared_degree_choices':sum(c['degree_choices_including_outer_loop'] for c in cases),'case_results':[]}
    try:
        for case in cases:
            check()
            old = {tuple(p) for p in case['points']}
            retained = tuple(sorted((x+1,y+1) for x,y in source-old))
            removed = tuple(sorted((x+1,y+1) for x,y in old))
            def save(cert,ids,digest):on_witness(case,cert,ids,digest)
            result = evaluator(n,retained,removed,proof_triple,check=check,on_witness=save)
            if result['complete'] and (result['completed_candidates']!=case['degree_choices_including_outer_loop'] or
                    result['proof_rejected_candidates']!=case['outer_loop_rejections_by_proof']):
                raise RuntimeError('complete case raw/proof coverage differs from pinned manifest')
            result.update(source_orbit_index=case['source_orbit_index'],deleted_source_orbit=case['points'])
            report['case_results'].append(result)
            if result['status'] in ('timeout','witness'):
                report['status']=result['status'];break
            if not result['complete']:raise RuntimeError('unknown incomplete case outcome')
        else:report.update(status='complete',complete=True)
    except TimeoutError:report['status']='timeout'
    complete = [r['source_orbit_index'] for r in report['case_results'] if r['complete']]
    attempted = {r['source_orbit_index'] for r in report['case_results']}
    report.update(completed_case_indices=complete,completed_cases=len(complete),
        partial_case_indices=[r['source_orbit_index'] for r in report['case_results'] if not r['complete']],
        unstarted_case_indices=[c['source_orbit_index'] for c in cases if c['source_orbit_index'] not in attempted],
        completed_candidates=sum(r['completed_candidates'] for r in report['case_results']),
        proof_rejected_candidates=sum(r['proof_rejected_candidates'] for r in report['case_results']),
        valid_candidates=sum(r['valid_candidates'] for r in report['case_results']))
    return report


def check_batch(fixture,seconds,out,*,clock=time.monotonic):
    valid_seconds(seconds)
    started=clock();deadline=started+seconds
    fixture_hash=validate_fixture(fixture)
    cases=validate_cases(fixture,CASE_MANIFEST.read_bytes())
    source={tuple(p) for p in fixture['points']}
    def check():
        if clock()>=deadline:raise TimeoutError('shared batch soft deadline')
    def save(case,cert,ids,digest):
        cert['metadata']={'method':'centered_n78_to_n80_all39_fullC4_orbit_repairs',
            'source_normalized_sha256':fixture_hash,'source_orbit_index':case['source_orbit_index'],
            'deleted_source_orbit':case['points'],'edge_ids':list(ids),'novelty_claim':False}
        atomic(Path(out)/('witness-'+digest+'.json'),encode(cert))
    report=evaluate_batch(80,source,cases,PROOF_TRIPLE,check=check,on_witness=save)
    report.update(scope=SCOPE,fixture_normalized_sha256=fixture_hash,case_manifest_sha256=CASE_MANIFEST_SHA256,
        source_n=78,n=80,translation=[1,1],elapsed_seconds=clock()-started,soft_seconds=seconds)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv);raw=args.fixture.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:parser.error('pinned fixture bytes differ')
    fixture=json.loads(raw)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    report=check_batch(fixture,args.seconds,args.output_dir)
    report['fixture_sha256']=FIXTURE_SHA256
    atomic(args.output_dir/'report.json',encode(report))
    print(json.dumps(report,sort_keys=True))
    return 0 if report['status'] in ('complete','witness') else 2


if __name__=='__main__':raise SystemExit(main())
