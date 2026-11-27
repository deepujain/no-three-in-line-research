"""Author synthetic n4 geometry and isolated lifecycle faults; no published source."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import exterior_unimodular75 as worker


POSITIVE9 = [(0,0),(2,0),(1,1),(4,1),(1,3),(4,3),(0,4),(2,4),(3,2)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def zero(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])


def sources():
    for points in combinations(product(range(4), repeat=2), 8):
        if any(sum(p[a] == v for p in points) != 2 for a in (0,1) for v in range(4)):
            continue
        if not any(zero(*triple) for triple in combinations(points, 3)):
            yield points


def geometry():
    counts = dict(sources=0, admitted=0, rejected=0, frames=0, raw_choices=0, exterior=0,
                  mutated_certificates=0, phase_timeouts=0, invalid_sources=0)
    all_sources = list(sources())
    for points in all_sources:
        result = worker.analyze_family(tuple(reversed(points)), 4)
        inventory = result['inventory']; assert inventory['points'] == points
        assert result['family_complete'] and result['certificate_complete'] and not result['survivors']
        expected = {}
        for a, b in product(range(-4,5), repeat=2):
            if not (a > 0 or (a == 0 and b > 0)) or gcd(abs(a), abs(b)) != 1:
                continue
            values = [a*x+b*y for x,y in points]
            if max(values)-min(values) <= 4:
                expected[(a,b)] = max(values)-min(values)
        assert {tuple(r['vector']): r['width'] for r in inventory['admitted']} == expected
        assert worker.verify_inventory(points, 4, inventory)
        counts['sources'] += 1; counts['admitted'] += len(expected)
        counts['rejected'] += len(inventory['rejected']); counts['frames'] += len(result['frames'])
        counts['raw_choices'] += len(result['candidate_choices']); counts['exterior'] += len(result['eligible_candidates'])
        for item in result['candidate_choices']:
            u,v = item['frame']; tx,ty = item['translation']; q = item['preimage']; z = item['added']
            mapped = [(u[0]*x+u[1]*y+tx, v[0]*x+v[1]*y+ty) for x,y in points]
            assert (u[0]*q[0]+u[1]*q[1]+tx,v[0]*q[0]+v[1]*q[1]+ty) == z
            assert z not in mapped
            old_pair = any(zero(a,b,q) for a,b in combinations(points,2))
            assert old_pair == any(zero(*triple) for triple in combinations(mapped+[z],3))
        for item in result['pair_obstructions']:
            i,j = item['indices']; assert zero(points[i],points[j],item['preimage'])
    p = all_sources[0]; base = worker.direction_inventory(p,4)
    mutations = []
    bad=deepcopy(base); bad['rejected'].pop(); mutations.append(bad)
    bad=deepcopy(base); bad['rejected'][0]['indices']=(0,0); mutations.append(bad)
    bad=deepcopy(base); bad['rejected'].append(deepcopy(bad['rejected'][0])); mutations.append(bad)
    bad=deepcopy(base); bad['admitted'][0]['width']=0; mutations.append(bad)
    bad=deepcopy(base); bad['admitted'][0]['levels']=[]; mutations.append(bad)
    bad=deepcopy(base); bad['H']+=1; mutations.append(bad)
    for bad in mutations:
        try:
            worker.verify_inventory(p,4,bad); raise AssertionError('bad inventory accepted')
        except ValueError:
            counts['mutated_certificates'] += 1
    invalid=((0,0),(0,1),(1,0),(1,1),(2,2),(2,3),(3,2),(3,3))
    assert any(zero(*t) for t in combinations(invalid,3))
    try:
        worker.direction_inventory(invalid,4); raise AssertionError('invalid source theorem used')
    except ValueError:
        counts['invalid_sources'] += 1
    for phase in ('source_geometry','direction_projection','inventory_certificate','frame_candidates','candidate_pairs','pair_certificate'):
        counters={}
        def stop():
            if counters.get('phase') == phase: raise TimeoutError(phase)
        try:
            worker.analyze_family(p,4,check=stop,counters=counters); raise AssertionError('deadline missed')
        except TimeoutError:
            counts['phase_timeouts'] += 1
    generic=[(0,0),(1,2),(1,4),(2,1),(2,3),(3,2),(3,4),(4,3)]
    raw=worker.frame_candidates(generic,4,((1,0),(0,1)))
    assert len(raw)==4 and sum(item['reason']=='occupied' for item in raw)==1
    assert all(worker.protected(q,4) for q in ((-1,-1),(4,4),(-1,4),(4,-1)))
    assert all(not worker.protected(q,4) for q in ((-2,0),(5,4),(0,-2),(4,5)))
    for validator in (worker.verify_certificate,worker.verify_certificate_bruteforce):
        assert validator({'n':5,'points':POSITIVE9})['valid']
    return counts, all_sources


def lifecycle(points, mode):
    with tempfile.TemporaryDirectory(prefix='exterior-affine-tiny-') as directory:
        root=Path(directory); (root/'data').mkdir(); (root/'src').mkdir()
        (root/'src/verify.py').write_text('synthetic pin sentinel\n')
        sentinel=root/'sentinel'; sentinel.write_text('unchanged')
        cert={'n':4,'points':list(points),'source_record':2 if mode=='wrong_record' else 1,'raw_sha256':'synthetic-raw'}
        fixture=root/'data/tiny.json'; fixture.write_text(json.dumps(cert))
        normalized=worker.verify_certificate(cert)['normalized_sha256']
        manifest=root/'pins.json'; manifest.write_text(json.dumps({str(Path(worker.__file__).resolve()):sha(worker.__file__),
             'data/tiny.json':sha(fixture),'src/verify.py':sha(root/'src/verify.py'),'sentinel':sha(sentinel)}))
        out=root/'output'; out.mkdir(); state={'now':0,'counters':{},'writes':0}
        analyze, build, second, atomic, digest = worker.analyze_family,worker.build_candidate,worker.verify_certificate_bruteforce,worker.atomic,worker.digest
        positive=mode in ('positive_stub','late_validator2','candidate_disagreement','save_failure')
        target=mode.removeprefix('deadline_') if mode.startswith('deadline_') else None
        def clock():
            return 26 if target is not None and state['counters'].get('phase')==target else state['now']
        def analysis(*args,**kwargs):
            state['counters']=kwargs['counters']; result=analyze(*args,**kwargs)
            if mode=='partial_inventory':result['inventory_complete']=False
            if mode=='partial_candidates':result['candidates_complete']=False
            if mode=='partial_pairs':result['pairs_complete']=False
            if mode=='pin_drift':sentinel.write_text('changed')
            if mode=='deadline_final_pins':state['final_pins']=True
            if positive:
                # Isolated pipeline stub: this is NOT an exterior affine witness.
                result['survivors']=[{'synthetic_pipeline_stub':True}];result['certificate_complete']=False
            return result
        def candidate(*args):
            if positive:return {'n':5,'points':POSITIVE9,'synthetic_pipeline_stub':True}
            return build(*args)
        def validator2(certificate):
            value=second(certificate)
            if certificate['n']==5:
                if mode=='late_validator2':state['now']=26
                if mode=='candidate_disagreement':value['valid']=False
            return value
        def save(path,value):
            if path.name=='valid149.json' and mode=='save_failure':raise OSError('synthetic save failure')
            atomic(path,value)
            if path.name=='report.json':
                state['writes']+=1
                if mode=='deadline_report_save':state['now']=26
        def hashed(path,check=lambda:None):
            if state.get('final_pins'):state['now']=26
            return digest(path,check)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(worker,ROOT=root,SOURCE_N=4,FIXTURE='data/tiny.json',
                    FIXTURE_SHA=sha(fixture),NORMALIZED=normalized,RAW_SHA='synthetic-raw'))
            for key,value in (('analyze_family',analysis),('build_candidate',candidate),('verify_certificate_bruteforce',validator2),('atomic',save),('digest',hashed)):
                stack.enter_context(patch.object(worker,key,value))
            report=worker.run(out,manifest,clock=clock,started=0)
        assert json.loads(json.dumps(report))==json.loads((out/'report.json').read_text())
        if mode=='negative':assert report['complete'] and report['closure'] and not report['witness_saved']
        elif mode=='positive_stub':assert report['complete'] and report['witness_saved'] and not report['closure']
        else:assert not report['complete'] and not report['closure'],(mode,report)
        if mode=='late_validator2':
            assert report['witness_saved'] and second(json.loads((out/'valid149.json').read_text())['certificate'])['valid']
        if mode in ('candidate_disagreement','save_failure'):assert not report['witness_saved'] and not (out/'valid149.json').exists()
        if mode=='pin_drift':assert not report['identity_valid']
        if mode=='deadline_report_save':assert state['writes']==2
        return {'mode':mode,'status':report['status'],'complete':report['complete'],'closure':report['closure'],'witness_saved':report['witness_saved']}


def main():
    geometry_counts,all_sources=geometry()
    modes=('negative','positive_stub','late_validator2','candidate_disagreement','save_failure','wrong_record',
           'partial_inventory','partial_candidates','partial_pairs','pin_drift','deadline_direction_projection',
           'deadline_inventory_certificate','deadline_frame_candidates','deadline_candidate_pairs',
           'deadline_pair_certificate','deadline_final_pins','deadline_report_save')
    result={'passed':True,'worker_sha256':sha(worker.__file__),'tiny_sha256':sha(__file__),
            'geometry':geometry_counts,'lifecycle':[lifecycle(all_sources[0],mode) for mode in modes],
            'scope':'All11 valid full-axis n4 sources; positive lifecycle uses explicitly stubbed analysis/construction and genuine valid9-on5, not an affine witness. No published source load or actual inventory/frame run.'}
    (Path(__file__).resolve().parents[1]/'data/exterior-unimodular75-author-tiny.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
