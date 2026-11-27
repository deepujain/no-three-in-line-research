"""Independent synthetic geometry/edge audit; no selected-source access."""
from copy import deepcopy
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
from unittest.mock import patch
from research import exterior_unimodular75 as worker
from research import exterior_affine_independent_oracle as oracle
from research import exterior_affine_independent_edge_fixtures as edge
from research.nonuniform_insertion_independent_tiny_oracle import full_axis_sources, triples


def rejects(call):
    try:call()
    except (ValueError,TypeError):return
    raise AssertionError('invalid input accepted')


def choice_key(item):
    return (tuple(map(tuple,item['frame'])),tuple(item['translation']),tuple(item['added']),tuple(item['preimage']))


def main():
    counts=dict(sources=0,admitted=0,rejected=0,cutoff_exclusions=0,frames=0,raw_choices=0,
                exterior_preimages=0,pair_certificates=0,inventory_mutations=0,invalid_axis_sources=0,
                malformed_sources=0,deadline_stops=0,protected_cases=0,generic_occupied_choices=0,
                duplicate_stream_records=0)
    sources=[tuple(sorted(p)) for p in full_axis_sources(4)]
    for points in sources:
        expected=oracle.expected_inventory(points,4)
        result=worker.analyze_family(tuple(reversed(points)),4)
        inv=result['inventory'];counts['sources']+=1
        assert inv['points']==points and inv['inventory_complete'] is True
        assert (inv['H'],inv['V'])==(expected['H'],expected['V'])
        assert inv['H_witness'] in expected['horizontal_max_witnesses'] and inv['V_witness'] in expected['vertical_max_witnesses']
        assert (inv['a_bound'],inv['b_bound'])==expected['coefficient_bounds']
        admitted={tuple(r['vector']):r for r in inv['admitted']}
        rejected={tuple(r['vector']):r for r in inv['rejected']}
        assert len(admitted)==len(inv['admitted']) and len(rejected)==len(inv['rejected'])
        assert set(admitted)==set(expected['admitted']) and set(rejected)==set(expected['rejected'])
        counts['admitted']+=len(admitted);counts['rejected']+=len(rejected);counts['cutoff_exclusions']+=len(expected['outside_cutoff'])
        for u,r in admitted.items():
            e=expected['admitted'][u]
            assert (r['min'],r['max'],r['width'])==(e['minimum'],e['maximum'],e['width'])
            assert dict(r['levels'])==e['counts']
            assert (r['min_index'],r['max_index']) in e['extreme_pairs']
        for u,r in rejected.items():oracle.check_width_obstruction(points,u,r['indices'],4)
        frames={f:info for f,info in expected['frames'].items() if not info['ordinary']}
        assert set(result['frames'])==set(frames) and len(result['frames'])==len(frames)
        counts['frames']+=len(frames)
        expected_choices=set()
        for frame,info in frames.items():
            actual=worker.frame_candidates(points,4,frame)
            for e in info['choices']+info['occupied_choices']:
                expected_choices.add((frame,e['translation'],e['added'],e['q']))
            assert {choice_key(r) for r in actual}=={(frame,e['translation'],e['added'],e['q']) for e in info['choices']+info['occupied_choices']}
            assert len(actual)<=4
        assert {choice_key(r) for r in result['candidate_choices']}==expected_choices
        assert len(result['candidate_choices'])==len(expected_choices)
        counts['raw_choices']+=len(expected_choices)
        eligible={tuple(r['preimage']):r for r in result['eligible_candidates']}
        assert set(eligible)==set(expected['exterior_preimages']) and len(eligible)==len(result['eligible_candidates'])
        counts['exterior_preimages']+=len(eligible)
        for q,r in eligible.items():
            assert choice_key(r) in expected_choices and r['reason']=='eligible'
        for r in result['exclusions']:
            q=tuple(r['preimage'])
            if r['reason']=='protected':assert -1<=q[0]<=4 and -1<=q[1]<=4
            elif r['reason']=='duplicate':assert q in eligible and choice_key(r)!=choice_key(eligible[q])
            elif r['reason']=='occupied':assert q in points
            else:raise AssertionError('unknown exclusion')
        blocked={tuple(r['preimage']):r for r in result['pair_obstructions']}
        assert set(blocked)=={q for q,pairs in expected['obstructions'].items() if pairs}
        for q,r in blocked.items():
            oracle.check_point_obstruction(points,q,r['indices']);counts['pair_certificates']+=1
        assert {tuple(r['preimage']) for r in result['survivors']}==expected['valid_preimages']
        assert all(result[k] is True for k in ('inventory_complete','candidates_complete','pairs_complete','family_complete'))
        assert result['certificate_complete']==(not expected['valid_preimages'])
    points=sources[0];base=worker.direction_inventory(points,4)
    mutations=[]
    def changed(fn):
        v=deepcopy(base);fn(v);mutations.append(v)
    changed(lambda v:v['admitted'].pop())
    changed(lambda v:v['rejected'].pop())
    changed(lambda v:v['admitted'].append(deepcopy(v['admitted'][0])))
    changed(lambda v:v['rejected'].append(deepcopy(v['rejected'][0])))
    for key in ('H','V','a_bound','b_bound'):
        changed(lambda v,key=key:v.__setitem__(key,v[key]+1))
    for key in ('H_witness','V_witness'):
        changed(lambda v,key=key:v.__setitem__(key,(0,0)))
    for key,value in (('width',5),('min',-999),('max',999),('min_index',999),('max_index',-1),('levels',[]),('vector',(2,0))):
        changed(lambda v,key=key,value=value:v['admitted'][0].__setitem__(key,value))
    for key,value in (('indices',(0,0)),('indices',(0,999)),('vector',(99,1))):
        changed(lambda v,key=key,value=value:v['rejected'][0].__setitem__(key,value))
    for bad in mutations:rejects(lambda:worker.verify_inventory(points,4,bad));counts['inventory_mutations']+=1
    rows=tuple(combinations(range(4),2))
    for choices in product(rows,repeat=4):
        if any(sum(x in row for row in choices)!=2 for x in range(4)):continue
        p=tuple((x,y) for y,row in enumerate(choices) for x in row)
        if not triples(p):continue
        c={};rejects(lambda:worker.direction_inventory(p,4,counters=c))
        assert c['coefficient_vectors']==0 and not c.get('source_valid');counts['invalid_axis_sources']+=1
    for p,n in ((points,3),(points,2),(points,True),(points,75),(points[:-1],4),((points[0],)*8,4),
                (((False,0),)+points[1:],4),(((0.0,0),)+points[1:],4),(((-1,0),)+points[1:],4),
                (((0,4),)+points[1:],4),(((0,),)+points[1:],4),(edge.OCCUPIED_POINTS,4)):
        rejects(lambda:worker.direction_inventory(p,n));counts['malformed_sources']+=1
    for q,expected in edge.protected_cases():
        assert worker.protected(q,4)==expected;counts['protected_cases']+=1
    raw=worker.frame_candidates(edge.OCCUPIED_POINTS,4,edge.OCCUPIED_FRAME)
    assert {r['added'] for r in raw}==edge.OCCUPIED_RAW
    assert {r['added'] for r in raw if r['reason']=='occupied'}==edge.OCCUPIED_EXCLUDED
    counts['generic_occupied_choices']=len(raw)
    for frame in (((1,0),(0,2)),((1,0),(2,0))):rejects(lambda:worker.frame_candidates(points,4,frame))
    records=edge.duplicate_collector_cases();frames=list(dict.fromkeys(r['frame'] for r in records))
    def stub_candidates(p,n,frame,**kwargs):
        return [dict(deepcopy(r),reason='unfiltered') for r in records if r['frame']==frame]
    with patch.object(worker,'canonical_frames',return_value=frames),patch.object(worker,'frame_candidates',side_effect=stub_candidates):
        result=worker.analyze_family(points,4)
    assert {r['preimage'] for r in result['eligible_candidates']}=={(6,4),(4,6)}
    assert result['counters']['duplicate_choices']==1 and result['counters']['protected_choices']==2
    expected_tests=0
    for q in ((4,6),(6,4)):
        for i,j in combinations(range(len(points)),2):
            expected_tests+=1
            if oracle.geometry.collinear(points[i],points[j],q):break
    assert result['counters']['pair_tests']==expected_tests
    counts['duplicate_stream_records']=len(records)
    for phase in ('source_geometry','direction_projection','inventory_certificate','frame_candidates','candidate_pairs','pair_certificate'):
        c={}
        def stop():
            if c.get('phase')==phase:raise TimeoutError('independent phase stop')
        try:worker.analyze_family(points,4,check=stop,counters=c)
        except TimeoutError:counts['deadline_stops']+=1
        else:raise AssertionError('deadline swallowed')
    for key in ('projections','pair_tests'):
        c={}
        def partial_stop():
            if c.get(key,0)>0:raise TimeoutError('partial inventory/pair stop')
        try:worker.analyze_family(points,4,check=partial_stop,counters=c)
        except TimeoutError:counts['deadline_stops']+=1
        else:raise AssertionError('partial work returned complete')
    root=Path(__file__).resolve().parents[1]
    paths=(Path(__file__),Path(worker.__file__),Path(oracle.__file__),Path(edge.__file__))
    report={'passed':True,'counts':counts,'pins':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'scope':'Independent synthetic n4 full geometry/certificates plus explicitly generic occupied/duplicate-stream fixtures. No selected-source read/inventory, actual geometry or solver.'}
    (root/'data/exterior-affine-independent-worker-audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=='__main__':main()
