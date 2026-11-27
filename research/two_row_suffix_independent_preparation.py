"""Finite87-fixture reference preparation; no production or actual artifact IO."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from research import two_row_suffix_independent_oracle as cursor

LOCAL = ((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
DENSE = ((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))


def key(event):
    return event['before_identity'],event['kind'],cursor.canonical(event['choice'])


def assert_trace(points,n,result):
    reference = cursor.exact.reference_descent(points,n)
    projected = [(e['kind'],e['choice'] if e['kind']=='row' else tuple(e['choice']),
                  tuple(e['minimum'][:1])+tuple(tuple(cols) for cols in e['minimum'][1:]),e['strict'])
                 for e in result['events']]
    assert projected == reference['events']
    state=result['state']
    assert tuple(map(tuple,state['points']))==reference['points'] and state['U']==reference['U']
    assert state['row_started']==reference['row_started'] and state['pair_started']==reference['pair_started']
    assert state['generation']==reference['accepted'] and state['status']==reference['status']
    assert len({key(e) for e in result['events']})==len(result['events'])


def run():
    started=time.monotonic();counts=Counter();fixtures=[];all_events=[]
    examples=[]
    for n in (2,3):
        examples.extend((n,p) for p in sorted(cursor.exact.geometry.states(n)))
    examples.extend(((4,LOCAL),(4,DENSE)))
    assert len(examples)==87
    for n,points in examples:
        initial=cursor.fresh(points,n)
        baseline=cursor.run(initial)
        assert_trace(points,n,baseline)
        counts['fixtures']+=1;counts['decisions']+=len(baseline['events'])
        for event in baseline['events']:
            counts[event['kind']+'_decisions']+=1
            counts['strict_decisions']+=event['strict']
            counts['nonimproving_pair_decisions']+=(event['kind']=='pair' and not event['strict'])
        # Every completed-decision boundary plus the initial boundary. Fresh
        # deserialize/reconstruction uses only current points and stored hashes.
        for cut,boundary in enumerate(baseline['boundaries']):
            loaded=cursor.restore(cursor.export(boundary),expected_identity=boundary['identity'],
                                  expected_order_identity=boundary['order_identity'],expected_generation=boundary['generation'])
            continued=cursor.run(loaded)
            concatenated=baseline['events'][:cut]+continued['events']
            assert concatenated==baseline['events'] and continued['state']==baseline['state']
            assert len({key(e) for e in concatenated})==len(concatenated)
            counts['all_boundary_splits']+=1
            counts['completed_decision_splits']+=cut>0
        for cut,boundary in enumerate(baseline['boundaries'][:-1]):
            pending=cursor.begin(boundary);assert pending['status']=='pending'
            loaded=cursor.restore(cursor.export(pending))
            assert loaded['points']==boundary['points'] and loaded['U']==boundary['U']
            kind=loaded['pending']['kind']
            assert loaded[kind+'_started']==boundary[kind+'_started']+1
            assert loaded[kind+'_completed']==boundary[kind+'_completed']
            assert loaded[kind+'_cursor']==boundary[kind+'_cursor']
            # An explicitly simulated lost start has no coverage. Its retry
            # consumes another charge, but otherwise recovers the same choices.
            lost=cursor.abandon_pending(loaded);continued=cursor.run(lost)
            projected=lambda es:[{k:v for k,v in e.items() if k not in ('row_started','pair_started')} for e in es]
            assert projected(continued['events'])==projected(baseline['events'][cut:])
            assert continued['state']['points']==baseline['state']['points']
            assert continued['state'][kind+'_started']==baseline['state'][kind+'_started']+1
            assert continued['state'][kind+'_completed']==baseline['state'][kind+'_completed']
            counts['pending_split_lost_charge_tests']+=1
            result=cursor.evaluate(pending)
            if result['minimum'][0]==0:
                assert pending['U']>0 and pending['pending'] is not None
                finished,event=cursor.finish(pending,result)
                assert finished['U']==0 and not finished['row_sweep_complete'] and not finished['pair_scan_complete']
                counts['zero_candidate_authority_distinctions']+=1
        fixtures.append({'n':n,'points':points,'events':baseline['events'],
                         'final':{k:v for k,v in baseline['state'].items() if k not in ('records','rows','pairs')}})
        all_events.append([n,points,baseline['events'],baseline['state']['identity']])
    cap_cases=[]
    for row_cap,pair_cap in ((0,32),(2,32),(3,0),(3,1)):
        result=cursor.run(cursor.fresh(LOCAL,4,row_cap=row_cap,pair_cap=pair_cap))
        expected=cursor.exact.reference_descent(LOCAL,4,row_cap,pair_cap)
        assert result['state']['status']==expected['status']
        assert result['state']['U']==expected['U']
        cap_cases.append({'row_cap':row_cap,'pair_cap':pair_cap,'status':result['state']['status'],'U':result['state']['U']})
    # Imported counters are synthetic ledger boundaries, not actual history.
    for kind in ('row','pair'):
        base=cursor.fresh(LOCAL,4,row_used=511 if kind=='row' else 0,pair_used=95 if kind=='pair' else 0,
                          row_cap=512,pair_cap=96)
        if kind=='pair':
            base=cursor.run(base,stop_after=3)['state']
            assert base['phase']=='pair'
        pending=cursor.begin(base);loaded=cursor.restore(cursor.export(pending))
        stopped=cursor.run(cursor.abandon_pending(loaded))['state']
        assert stopped['status']==kind+'_cap' and stopped['U']==base['U']
        assert stopped[kind+'_started']==stopped[kind+'_cap'] and stopped[kind+'_completed']==base[kind+'_completed']
        assert stopped[kind+'_cursor']==base[kind+'_cursor']
        counts['last_start_lost_cap_tests']+=1
    # Every final identity/order change is refused even with a recomputed outer
    # digest when the serialized internal relationships or trusted identity fail.
    boundary=cursor.run(cursor.fresh(LOCAL,4),stop_after=3)['state']
    corruptions=[lambda a:a.update(identity='0'*64),lambda a:a.update(policy='different'),
                 lambda a:a['pairs'].reverse(),lambda a:a.update(order_identity='0'*64),
                 lambda a:a.update(generation=a['generation']+1)]
    for mutate in corruptions:
        damaged=deepcopy(boundary);mutate(damaged)
        try:cursor.restore(cursor.export(damaged),expected_identity=boundary['identity'],
                           expected_order_identity=boundary['order_identity'],expected_generation=boundary['generation'])
        except AssertionError:counts['tamper_rejections']+=1
        else:raise AssertionError('tampered authority accepted')
    # Explicit row-control stub to exercise real positive pair geometry.
    stub=cursor.fresh(DENSE,4)
    while True:
        pending=cursor.begin(stub);result=cursor.evaluate(pending,row_control_stub=True)
        next_state,event=cursor.finish(pending,result)
        if event['kind']=='pair':
            assert event['before_score']==5 and event['minimum'][0]==1 and event['strict']
            assert not event['control_stub'] and next_state['phase']=='row'
            assert next_state['row_cursor']==next_state['pair_cursor']==0
            assert not next_state['row_sweep_complete'] and not next_state['pair_scan_complete']
            assert next_state['order_identity']!=stub['order_identity']
            positive_pair={'label':'Stage1 current-return control stub; real pair minimum/recount',
                           'event':event,'next_identity':next_state['identity']}
            break
        stub=next_state
    counts['positive_pair_disclosed_stub_cases']=1
    return {'scope':'Independent n2..4 cursor preparation only; no production imports or actual artifacts.',
            'passed':True,'counts':dict(counts),'fixtures':fixtures,'cap_cases':cap_cases,
            'positive_pair_control_stub':positive_pair,'trace_sha256':cursor.hashed(all_events),
            'oracle_sha256':hashlib.sha256(Path(cursor.__file__).read_bytes()).hexdigest(),
            'preparation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'elapsed_seconds':time.monotonic()-started,
            'limits':'No genuine positive full-policy terminal in these87 traces. Persistence/failure/orphan/real-validator tests require the frozen production adapter and independent lifecycle review. Historical actual32-prefix cannot be independently certified by these tiny tests.'}


if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-oracle-preparation.json')
    assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('fixtures','positive_pair_control_stub')},sort_keys=True))
    print(hashlib.sha256(path.read_bytes()).hexdigest())
