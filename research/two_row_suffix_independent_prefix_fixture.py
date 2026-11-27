"""Disclosed Stage1 stub reaches real pair-prefix continuation on synthetic n4."""
import hashlib
import json
from pathlib import Path
from research import two_row_suffix_independent_oracle as cursor

POINTS=((0,0),(0,1),(1,2),(2,1),(2,3),(3,2),(3,3))


def run():
    # Imported counters are synthetic controller fields, not actual history.
    initial=cursor.fresh(POINTS,4,row_used=308,pair_used=32,generation=28,pair_cap=96)
    whole=cursor.run(initial,row_control_stub=True)
    pairs=[e for e in whole['events'] if e['kind']=='pair']
    assert len(pairs)==2 and pairs[0]['choice']==[0,1] and pairs[0]['minimum'][0]==1 and not pairs[0]['strict']
    assert pairs[1]['choice']==[0,2] and pairs[1]['minimum'][0]==0 and pairs[1]['strict']
    cut=next(i+1 for i,e in enumerate(whole['events']) if e['kind']=='pair')
    boundary=whole['boundaries'][cut]
    assert boundary['row_sweep_complete'] and not boundary['pair_scan_complete']
    assert boundary['pair_cursor']==1 and boundary['pair_started']==boundary['pair_completed']==33
    loaded=cursor.restore(cursor.export(boundary),expected_identity=boundary['identity'],
                          expected_order_identity=boundary['order_identity'],expected_generation=28)
    resumed=cursor.run(loaded,row_control_stub=True)
    assert whole['events'][:cut]+resumed['events']==whole['events'] and resumed['state']==whole['state']
    assert resumed['events'][0]['choice']==[0,2] and resumed['state']['pair_started']==34
    assert resumed['state']['generation']==29 and not resumed['state']['row_sweep_complete']
    assert not resumed['state']['pair_scan_complete'] and resumed['state']['pair_cursor']==0
    # The real policy would already accept a row-zero; retain that discrepancy.
    real=cursor.exact.reference_descent(POINTS,4)
    assert real['pair_started']==0 and real['U']==0
    return {'passed':True,'scope':'Synthetic n4 controller fixture only; no actual input or production imports.',
            'disclosure':'Stage1 current-return stub suppresses a real row improvement. Both pair minima are direct determinant optima. Imported308/32/28 counters are synthetic, not actual historical coverage.',
            'points':POINTS,'uninterrupted_events':whole['events'],'cut_after_decisions':cut,
            'boundary':{k:v for k,v in boundary.items() if k!='records'},'resumed_events':resumed['events'],
            'real_full_policy_reference':real,
            'oracle_sha256':hashlib.sha256(Path(cursor.__file__).read_bytes()).hexdigest(),
            'fixture_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-prefix-fixture.json')
    assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','scope','disclosure','oracle_sha256','fixture_sha256')},sort_keys=True))
    print(hashlib.sha256(path.read_bytes()).hexdigest())
