"""Prepared artifact-chain auditor; CLI runs synthetic self-tests only.

Actual use requires Root's separate artifact handoff and computation allocation.
No production worker imports, automatic file discovery, search or replay.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path


def identity(n, points):
    payload = {'n':n,'points':[list(p) for p in sorted(points)]}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()


def authenticated_json(path, expected_sha, check):
    """Explicit path/hash only. Future caller owns allocation and path selection."""
    check()
    path = Path(path)
    if path.stat().st_size > 1024*1024:
        raise ValueError('artifact size cap')
    raw = path.read_bytes()
    if len(raw) > 1024*1024 or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('artifact byte identity')
    check()
    return json.loads(raw)


def state_audit(value, n, check):
    check()
    if type(n) is not int or not 2 <= n <= 75 or type(value) not in (tuple,list) or len(value) != 2*n-1:
        raise ValueError('grid/cardinality')
    points = []
    for p in value:
        if type(p) not in (tuple,list) or len(p) != 2 or any(type(x) is not int or not 0 <= x < n for x in p):
            raise ValueError('coordinate domain')
        points.append(tuple(p))
    points = tuple(sorted(points))
    rows = Counter(y for x,y in points)
    if len(set(points)) != len(points) or sorted(rows.get(y,0) for y in range(n)) != [1]+[2]*(n-1):
        raise ValueError('distinctness/row pattern')
    score = 0
    for i,(p,q,r) in enumerate(combinations(points,3)):
        if i % 1024 == 0:
            check()
        score += (q[0]-p[0])*(r[1]-p[1]) == (q[1]-p[1])*(r[0]-p[0])
    check()
    return {'points':points,'U':score,'normalized_sha256':identity(n,points),
            'rows':[rows[y] for y in range(n)],'columns':[sum(x==c for x,y in points) for c in range(n)]}


def counters(record, previous):
    keys = ('row_started','pair_started','row_completed','pair_completed')
    current = {}
    for key in keys:
        value = record.get(key)
        if type(value) is not int or value < previous[key]:
            raise ValueError('nonmonotone or malformed counter')
        current[key] = value
    for kind,cap in (('row',512),('pair',32)):
        if not 0 <= current[kind+'_completed'] <= current[kind+'_started'] <= cap:
            raise ValueError('started/completed cap')
        if current[kind+'_started']-current[kind+'_completed'] > 1:
            raise ValueError('multiple unfinished optimizations')
    return current


def audit_chain(initial, improvements, boundary, *, n, expected_initial_identity,
                expected_initial_score, max_states, check):
    """Recount a complete saved chain. Does not establish optimizer/exhaustion claims.

    The caller supplies already authenticated JSON snapshots and exact expected
    handoff identity. Resource interruption propagates; no partial PASS is emitted.
    """
    if type(max_states) is not int or not 1 <= max_states <= 98:
        raise ValueError('explicit bounded audit scope required')
    if type(improvements) is not list or len(improvements)+1 > max_states or len(improvements) > 97:
        raise ValueError('chain exceeds allocated scope')
    if type(expected_initial_score) is not int or expected_initial_score < 0:
        raise ValueError('expected initial score')
    if (type(initial.get('n')) is not int or type(boundary.get('n')) is not int
            or initial.get('n') != n or boundary.get('n') != n or boundary.get('schema') != 'two-row-raw-descent-boundary-v1'):
        raise ValueError('initial/boundary schema')
    before = state_audit(initial.get('points'),n,check)
    if (type(initial.get('score')) is not int or before['normalized_sha256'] != expected_initial_identity
            or initial.get('normalized_sha256') != expected_initial_identity
            or initial.get('score') != before['U'] or before['U'] != expected_initial_score):
        raise ValueError('initial handoff identity/score')
    evidence = [{k:v for k,v in before.items() if k != 'points'}]
    counts = dict.fromkeys(('row_started','pair_started','row_completed','pair_completed'),0)
    for record in improvements:
        check()
        after = state_audit(record.get('points'),n,check)
        if (any(type(record.get(key)) is not int for key in ('n','before_score','score'))
                or record.get('n') != n or record.get('before_normalized_sha256') != before['normalized_sha256']
                or record.get('normalized_sha256') != after['normalized_sha256']
                or record.get('before_score') != before['U'] or record.get('score') != after['U']
                or not after['U'] < before['U']):
            raise ValueError('chain identity/strict score decrease')
        rows = record.get('rows'); kind = record.get('kind')
        if type(rows) not in (tuple,list) or any(type(y) is not int or not 0 <= y < n for y in rows):
            raise ValueError('selected row schema')
        if (kind == 'row' and len(rows) != 1) or (kind == 'pair' and (len(rows) != 2 or rows[0] >= rows[1])) or kind not in ('row','pair'):
            raise ValueError('selected row/pair')
        if any(p[1] not in rows for p in set(before['points']) ^ set(after['points'])):
            raise ValueError('change outside selected rows')
        if kind == 'row' and before['rows'][rows[0]] != after['rows'][rows[0]]:
            raise ValueError('row load changed')
        if sum(before['rows'][y] for y in rows) != sum(after['rows'][y] for y in rows):
            raise ValueError('selected total load changed')
        previous_completed = counts[kind+'_completed']
        counts = counters(record,counts)
        if counts[kind+'_completed'] <= previous_completed:
            raise ValueError('accepted move without completed optimization')
        for key in ('row_sweep_complete','pair_scan_complete','enumeration_complete'):
            if type(record.get(key)) is not bool:
                raise ValueError('completion field schema')
        evidence.append({k:v for k,v in after.items() if k != 'points'})
        before = after
    if len(improvements) > expected_initial_score:
        raise ValueError('strict decrease count bound')
    # Last artifact identity can be checked without a duplicate cubic recount.
    final_points = boundary.get('points')
    if (type(final_points) not in (tuple,list) or len(final_points) != 2*n-1
            or any(type(p) not in (tuple,list) or len(p) != 2 or any(type(x) is not int for x in p) for p in final_points)
            or tuple(sorted(tuple(p) for p in final_points)) != before['points']):
        raise ValueError('boundary differs from last saved accepted state')
    if boundary.get('normalized_sha256') != before['normalized_sha256']:
        raise ValueError('boundary identity')
    state = boundary.get('state')
    if (type(state) is not dict or type(state.get('U')) is not int or type(state.get('accepted')) is not int
            or state.get('U') != before['U'] or state.get('accepted') != len(improvements)):
        raise ValueError('boundary score/complete accepted-chain count')
    final_counts = counters(state,counts)
    if any(type(state.get(key)) is not bool for key in ('row_sweep_complete','pair_scan_complete')):
        raise ValueError('boundary completion schema')
    if state.get('status') == 'row_cap' and (state['row_sweep_complete'] or state['pair_scan_complete']):
        raise ValueError('partial row scan labeled complete')
    if state.get('status') == 'pair_cap' and (not state['row_sweep_complete'] or state['pair_scan_complete']):
        raise ValueError('pair cap completion inconsistency')
    if before['U'] == 0 and (state['row_sweep_complete'] or state['pair_scan_complete']):
        raise ValueError('stale zero-state completion claim')
    check()
    return {'artifact_chain_passed':True,'n':n,'states_recounted':len(evidence),
            'scores':[item['U'] for item in evidence],'states':evidence,'final_counters':final_counts,
            'zero_geometry_verified':before['U'] == 0,
            'execution_claims_unproven':['exact neighborhood minima','first-improvement ordering','I/J/M zero skips',
                                        'complete final-state neighborhood coverage','receipt/resource acceptance'],
            'scope':'Independent artifact identities, determinant scores, row invariants, strict decreases and changed-row membership only.'}


def self_test():
    from copy import deepcopy
    from research import two_row_descent_independent_oracle as oracle
    from src.verify import normalized_sha256
    points = ((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
    target = oracle.pair_optimum(points,4,0,1)['points']
    old_hash,new_hash = identity(4,points),identity(4,target)
    assert old_hash == normalized_sha256(4,points) and new_hash == normalized_sha256(4,target)
    initial = {'n':4,'points':points,'normalized_sha256':old_hash,'score':1}
    record = {'n':4,'points':target,'before_normalized_sha256':old_hash,'normalized_sha256':new_hash,
              'before_score':1,'score':0,'kind':'pair','rows':[0,1],'row_started':3,'row_completed':3,
              'pair_started':1,'pair_completed':1,'row_sweep_complete':True,'pair_scan_complete':False,'enumeration_complete':False}
    boundary = {'schema':'two-row-raw-descent-boundary-v1','n':4,'points':target,'normalized_sha256':new_hash,
                'state':{'U':0,'accepted':1,'row_started':3,'row_completed':3,'pair_started':1,'pair_completed':1,
                         'row_sweep_complete':False,'pair_scan_complete':False,'status':'zero'}}
    args = dict(n=4,expected_initial_identity=old_hash,expected_initial_score=1,max_states=2,check=lambda:None)
    result = audit_chain(initial,[record],boundary,**args)
    assert result['scores'] == [1,0]
    corruptions = [lambda i,r,b:r.update(score=1),lambda i,r,b:r.update(before_normalized_sha256='0'*64),
                   lambda i,r,b:r.update(rows=[2,3]),lambda i,r,b:r.update(pair_started=33),
                   lambda i,r,b:b['state'].update(accepted=2),lambda i,r,b:b['state'].update(row_sweep_complete=True),
                   lambda i,r,b:i.update(points=[points[0]]*7),lambda i,r,b:b.update(points=points),
                   lambda i,r,b:r.update(score=False),lambda i,r,b:b['state'].update(U=False),
                   lambda i,r,b:b.update(points=[(bool(x),y) for x,y in target])]
    for mutate in corruptions:
        i,r,b = deepcopy((initial,record,boundary)); mutate(i,r,b)
        try:
            audit_chain(i,[r],b,**args)
        except ValueError:
            pass
        else:
            raise AssertionError('corruption accepted')
    # Two genuine pair improvements, but deliberately reuse the completed count.
    dense = ((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))
    middle = oracle.pair_optimum(dense,4,0,1)['points']
    pair,second = next(((r,s),oracle.pair_optimum(middle,4,r,s)['points'])
                       for r,s in combinations(range(4),2)
                       if oracle.pair_optimum(middle,4,r,s)['minimum'][0] == 0)
    first_record,second_record = deepcopy(record),deepcopy(record)
    first_record.update(points=middle,before_normalized_sha256=identity(4,dense),normalized_sha256=identity(4,middle),
                        before_score=5,score=1,enumeration_complete=True)
    second_record.update(points=second,before_normalized_sha256=identity(4,middle),normalized_sha256=identity(4,second),rows=pair)
    dense_initial = dict(initial,points=dense,score=5,normalized_sha256=identity(4,dense))
    dense_boundary = deepcopy(boundary)
    dense_boundary.update(points=second,normalized_sha256=identity(4,second))
    dense_boundary['state'].update(accepted=2,pair_started=2,pair_completed=2)
    dense_args = dict(args,expected_initial_identity=identity(4,dense),expected_initial_score=5,max_states=3)
    try:
        audit_chain(dense_initial,[first_record,second_record],dense_boundary,**dense_args)
    except ValueError as error:
        assert str(error) == 'accepted move without completed optimization'
    else:
        raise AssertionError('reused completed optimization accepted')
    second_record.update(pair_started=2,pair_completed=2)
    assert audit_chain(dense_initial,[first_record,second_record],dense_boundary,**dense_args)['scores'] == [5,1,0]
    return {'passed':True,'scope':'SOURCE/TINY synthetic only; actual audit unexecuted.',
            'valid_chain':result,'negative_cases':len(corruptions)+1,'two_pair_scores':[5,1,0],
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = self_test()
    path = Path('data/two-row-descent-independent-chain-audit-preparation-v3.json')
    assert not path.exists(), 'preserve evidence'
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'source_sha256':result['source_sha256'],
                      'evidence_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},sort_keys=True))
