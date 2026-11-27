"""Independent n2..4 cursor expectations, not a production/resume worker.

Pure direct-determinant choices via the frozen independent oracle. No actual
artifact loading, production imports, durable I/O or automatic allocation.
"""
from copy import deepcopy
import hashlib
import json
from research import two_row_descent_independent_oracle as exact

POLICY = 'independent-tiny-current-included-first-strict-raw-v1'


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


def hashed(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def point_id(n, points):
    return hashed({'n':n,'points':sorted(map(list,points))})


def install_orders(state):
    ranks = exact.priorities(state['points'],state['n'])
    state['rows'] = list(ranks['rows'])
    state['pairs'] = [list(pair) for pair in ranks['pairs']]
    state['order_identity'] = hashed({'state':state['identity'],'policy':POLICY,
                                     'rows':state['rows'],'pairs':state['pairs']})


def fresh(points, n, *, row_used=0, pair_used=0, generation=0, row_cap=512, pair_cap=32):
    points = exact.geometry.row_state(points,n)
    assert all(type(v) is int and v >= 0 for v in (row_used,pair_used,generation,row_cap,pair_cap))
    assert row_used <= row_cap <= 512 and pair_used <= pair_cap <= 96
    state = {'n':n,'points':[list(p) for p in points],'U':exact.raw(points),
             'identity':point_id(n,points),'policy':POLICY,'generation':generation,
             'row_started':row_used,'row_completed':row_used,'pair_started':pair_used,'pair_completed':pair_used,
             'row_cap':row_cap,'pair_cap':pair_cap,'phase':'row','row_cursor':0,'pair_cursor':0,
             'row_sweep_complete':False,'pair_scan_complete':False,'pending':None,'status':'ready','records':[]}
    state['base'] = {'row_started':row_used,'row_completed':row_used,'pair_started':pair_used,
                     'pair_completed':pair_used,'generation':generation}
    install_orders(state)
    advance(state)
    return state


def advance(state):
    if state['U'] == 0:
        state.update(status='zero',row_sweep_complete=False,pair_scan_complete=False)
    elif state['phase'] == 'row' and state['row_cursor'] == len(state['rows']):
        state.update(phase='pair',row_sweep_complete=True)
    if state['U'] and state['phase'] == 'pair' and state['pair_cursor'] == len(state['pairs']):
        state.update(status='no_strict_descent',row_sweep_complete=True,pair_scan_complete=True)


def begin(authority):
    state = deepcopy(authority)
    assert state['pending'] is None
    if state['status'] != 'ready':
        return state
    advance(state)
    if state['status'] != 'ready':
        return state
    kind = state['phase']; cursor = state[kind+'_cursor']
    if state[kind+'_started'] >= state[kind+'_cap']:
        state['status'] = kind+'_cap'
        return state
    choice = state['rows'][cursor] if kind == 'row' else state['pairs'][cursor]
    state[kind+'_started'] += 1
    state['pending'] = {'sequence':len(state['records'])+1,'kind':kind,'choice':deepcopy(choice),'cursor':cursor,
                        'state_identity':state['identity'],'order_identity':state['order_identity']}
    state['records'].append(dict(deepcopy(state['pending']),completion='pending'))
    state['status'] = 'pending'
    return state


def evaluate(pending, *, row_control_stub=False):
    selected = pending['pending']; assert selected and pending['status'] == 'pending'
    points,n = pending['points'],pending['n']
    kind,choice = selected['kind'],selected['choice']
    if kind == 'row' and row_control_stub:
        result = {'minimum':(pending['U'],tuple(x for x,y in points if y == choice)),
                  'points':tuple(map(tuple,points)),'strict':False}
    else:
        result = exact.row_optimum(points,n,choice) if kind == 'row' else exact.pair_optimum(points,n,*choice)
    return json.loads(canonical(dict(result,control_stub=(kind == 'row' and row_control_stub))))


def finish(pending, result):
    state = deepcopy(pending); selected = deepcopy(state['pending'])
    assert selected and state['status'] == 'pending'
    kind,choice = selected['kind'],selected['choice']
    points = exact.geometry.row_state(result['points'],state['n'])
    score = exact.raw(points)
    assert score == result['minimum'][0] <= state['U']
    strict = score < state['U']
    assert strict == result['strict']
    rows = (choice,) if kind == 'row' else choice
    assert all(p[1] in rows for p in set(map(tuple,state['points'])) ^ set(points))
    state[kind+'_completed'] += 1
    state['records'][-1].update(completion='completed',minimum=deepcopy(result['minimum']),strict=strict,
                                control_stub=result['control_stub'])
    event = {'kind':kind,'choice':deepcopy(choice),'minimum':deepcopy(result['minimum']),'strict':strict,
             'before_identity':state['identity'],'before_score':state['U'],
             'after_identity':point_id(state['n'],points) if strict else state['identity'],
             'before_points':deepcopy(state['points']),'after_points':[list(p) for p in points] if strict else deepcopy(state['points']),
             'control_stub':result['control_stub'],
             'row_started':state['row_started'],'row_completed':state['row_completed'],
             'pair_started':state['pair_started'],'pair_completed':state['pair_completed']}
    state.update(pending=None,status='ready')
    if strict:
        state.update(points=[list(p) for p in points],U=score,identity=point_id(state['n'],points),
                     generation=state['generation']+1,phase='row',row_cursor=0,pair_cursor=0,
                     row_sweep_complete=False,pair_scan_complete=False)
        install_orders(state)
    else:
        assert score == state['U']
        state[kind+'_cursor'] += 1
    advance(state)
    return state,event


def abandon_pending(authority):
    """Explicit test transition only: unresolved work loses a charged start."""
    state = deepcopy(authority); assert state['pending'] and state['status'] == 'pending'
    state['records'][-1]['completion'] = 'abandoned'
    state.update(pending=None,status='ready')
    return state


def run(authority, *, row_control_stub=False, stop_after=None):
    state = deepcopy(authority); events = []; boundaries = [deepcopy(state)]
    while state['status'] == 'ready':
        pending = begin(state)
        if pending['status'] != 'pending':
            state = pending
            break
        state,event = finish(pending,evaluate(pending,row_control_stub=row_control_stub))
        events.append(event); boundaries.append(deepcopy(state))
        if stop_after is not None and len(events) >= stop_after:
            break
    return {'state':state,'events':events,'boundaries':boundaries}


def export(authority):
    return canonical({'authority':authority,'sha256':hashed(authority)})


def restore(raw, *, expected_identity=None, expected_order_identity=None, expected_generation=None):
    document = json.loads(raw); state = document['authority']
    assert document['sha256'] == hashed(state), 'whole-authority digest'
    points = exact.geometry.row_state(state['points'],state['n'])
    assert state['identity'] == point_id(state['n'],points) and state['U'] == exact.raw(points)
    assert state['policy'] == POLICY
    ranks = exact.priorities(points,state['n'])
    assert state['rows'] == list(ranks['rows']) and state['pairs'] == [list(p) for p in ranks['pairs']]
    assert state['order_identity'] == hashed({'state':state['identity'],'policy':POLICY,
                                            'rows':state['rows'],'pairs':state['pairs']})
    if expected_identity is not None: assert state['identity'] == expected_identity
    if expected_order_identity is not None: assert state['order_identity'] == expected_order_identity
    if expected_generation is not None: assert state['generation'] == expected_generation
    assert 0 <= state['row_cursor'] <= len(state['rows']) and 0 <= state['pair_cursor'] <= len(state['pairs'])
    for kind,cap in (('row',512),('pair',96)):
        assert 0 <= state[kind+'_completed'] <= state[kind+'_started'] <= state[kind+'_cap'] <= cap
        attempts=[r for r in state['records'] if r['kind']==kind]
        assert state[kind+'_started']==state['base'][kind+'_started']+len(attempts)
        assert state[kind+'_completed']==state['base'][kind+'_completed']+sum(r['completion']=='completed' for r in attempts)
    assert state['generation']==state['base']['generation']+sum(r.get('strict',False) for r in state['records'] if r['completion']=='completed')
    if state['pending']:
        selected=state['pending'];kind=selected['kind'];cursor=selected['cursor']
        assert state['status'] == 'pending' and selected['state_identity'] == state['identity']
        assert selected['order_identity'] == state['order_identity'] and state[kind+'_cursor'] == cursor
        assert selected['choice'] == (state['rows'][cursor] if kind == 'row' else state['pairs'][cursor])
    return state
