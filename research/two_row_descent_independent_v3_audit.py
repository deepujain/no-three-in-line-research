"""V3 source-delta and synthetic regression; preserve v2 audit/evidence."""
import hashlib
import json
from pathlib import Path
from research import two_row_descent_independent_worker_audit as prior
from research import two_row_descent75_v2_frozen as previous

V2 = 'e122a497bf2da967c4b35cc043f4a13febbd781a8e7baca9d81cda7f2dfcda41'
V3 = '0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'


def focused(module, points, *, suppress_rows=False, fail=False):
    events = []
    original = module.row_optimum
    def current(points,index,n,row,check,work):
        return {'score':prior.oracle.raw(points),'columns':tuple(x for x,y in points if y == row),
                'points':points,'zero':False,'enumeration_complete':True}
    def commit(event):
        events.append(event)
        if fail:
            raise OSError('synthetic artifact persistence failure')
    try:
        if suppress_rows:
            module.row_optimum = current
        state = module.descend(points,4,commit=commit)
    finally:
        module.row_optimum = original
    assert events and events[0]['kind'] == 'pair' and events[0]['row_sweep_complete']
    assert prior.oracle.raw(events[0]['points']) == events[0]['score'] < events[0]['before_score']
    if fail:
        assert state['status'] == 'error' and state['accepted'] == 1
        assert state['points'] == events[0]['points'] and state['U'] == events[0]['score']
    else:
        assert state['status'] == 'zero'
    return {k:v for k,v in state.items() if k != 'index'}, events


def run():
    assert prior.sha(previous.__file__) == V2 and prior.sha(prior.worker.__file__) == V3
    before = Path(previous.__file__).read_text()
    expected = before.replace("state.update(points=current,index=None,U=0,accepted=state['accepted']+1,status='zero')",
        "state.update(points=current,index=None,U=0,accepted=state['accepted']+1,status='zero',\n                                     row_sweep_complete=False,pair_scan_complete=False)")
    expected = expected.replace("state.update(points=current,index=index,U=score,accepted=state['accepted']+1)",
        "state.update(points=current,index=index,U=score,accepted=state['accepted']+1,\n                                 row_sweep_complete=False,pair_scan_complete=False)")
    assert expected == Path(prior.worker.__file__).read_text(), 'delta exceeds two flag resets'
    prior.WORKER_SHA = V3
    exhaustive = prior.run()
    stuck = ((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
    positive = ((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))
    cases = []
    for name,points,suppress_rows,fail in (
        ('genuine_pair_zero',stuck,False,False),
        ('genuine_pair_zero_callback_failure',stuck,False,True),
        ('positive_pair_callback_failure_with_row_control_stub',positive,True,True)):
        old,old_events = focused(previous,points,suppress_rows=suppress_rows,fail=fail)
        new,new_events = focused(prior.worker,points,suppress_rows=suppress_rows,fail=fail)
        assert old_events == new_events
        assert old['row_sweep_complete'] and not new['row_sweep_complete'] and not new['pair_scan_complete']
        assert {k:v for k,v in old.items() if k != 'row_sweep_complete'} == {k:v for k,v in new.items() if k != 'row_sweep_complete'}
        cases.append({'name':name,'v2':old,'v3':new,'events':new_events,
                      'row_control_stub':suppress_rows,'pair_geometry_and_rebuild':'genuine n4'})
    assert cases[-1]['v3']['U'] == 1
    assert prior.sha(previous.__file__) == V2 and prior.sha(prior.worker.__file__) == V3
    return {'passed':True,'v2_sha256':V2,'v3_sha256':V3,'audit_sha256':prior.sha(__file__),
            'scope':'SOURCE/TINY only; no actual input reads. Positive pair case suppresses row optimization with a disclosed control stub; pair geometry and rebuild remain real.',
            'exhaustive':exhaustive,'focused_cases':cases}


if __name__ == '__main__':
    result = run()
    path = Path('data/two-row-descent-independent-worker-audit-v3.json')
    assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'audit_sha256':result['audit_sha256'],
                      'evidence_sha256':prior.sha(path),'counts':result['exhaustive']['counts']},sort_keys=True))
