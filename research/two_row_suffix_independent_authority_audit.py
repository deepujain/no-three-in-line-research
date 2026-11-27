"""Independent suffix authority/ledger auditor; CLI is synthetic preparation only.

No optimizer, production imports at module load, actual discovery or recovery.
Future actual use requires Root's separate authenticated handoff and allocation.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path

POLICY='exact-raw-IJ-M-merged-lex-v3'
COUNTERS=('row_started','row_completed','pair_started','pair_completed','accepted')


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def hashed(value):return hashlib.sha256(canonical(value)).hexdigest()


def integer_fields(value, names):
    if type(value) is not dict or any(type(value.get(k)) is not int or value[k]<0 for k in names):
        raise ValueError('exact nonnegative integer fields')


def counter_fields(value):
    if type(value) is not dict or set(value)!=set(COUNTERS):raise ValueError('counter keys')
    integer_fields(value,COUNTERS)


def points_checked(values,n):
    if type(n) is not int or not 2<=n<=75 or type(values) not in (list,tuple) or len(values)!=2*n-1:
        raise ValueError('point/grid cardinality')
    points=[]
    for p in values:
        if type(p) not in (list,tuple) or len(p)!=2 or any(type(x) is not int or not 0<=x<n for x in p):
            raise ValueError('point domain')
        points.append(tuple(p))
    points=tuple(sorted(points));rows=Counter(y for x,y in points)
    if len(set(points))!=len(points) or sorted(rows.get(y,0) for y in range(n))!=[1]+[2]*(n-1):
        raise ValueError('duplicate/row invariant')
    return points


def state_identity(n,points):return hashed({'n':n,'points':[list(p) for p in points]})


def recount(values,n,check):
    points=points_checked(values,n);score=0;incidence=[0]*n;joint=dict.fromkeys(combinations(range(n),2),0)
    for i,(p,q,r) in enumerate(combinations(points,3)):
        if i%1024==0:check()
        if (q[0]-p[0])*(r[1]-p[1])!=(q[1]-p[1])*(r[0]-p[0]):continue
        score+=1;rows=sorted((p[1],q[1],r[1]))
        if len(set(rows))!=3:raise ValueError('row-capacity triple contradiction')
        for y in rows:incidence[y]+=1
        for pair in combinations(rows,2):joint[pair]+=1
    removed={p:incidence[p[0]]+incidence[p[1]]-v for p,v in joint.items()}
    rows=sorted((r for r in range(n) if incidence[r]),key=lambda r:(-incidence[r],r))
    pairs=[list(p) for p in sorted((p for p,v in removed.items() if v),key=lambda p:(-removed[p],*p))]
    identity=state_identity(n,points)
    orders={'rows':rows,'pairs':pairs}
    orders['sha256']=hashed({'state_hash':identity,'policy':POLICY,**orders})
    check()
    return {'points':points,'U':score,'state_hash':identity,'orders':orders,
            'row_counts':[sum(y==r for x,y in points) for r in range(n)]}


def reference_blob(ref,blobs,check):
    if (type(ref) is not dict or type(ref.get('path')) is not str or len(ref['path'])>256
            or type(ref.get('sha256')) is not str or len(ref['sha256'])!=64):
        raise ValueError('artifact reference schema')
    check();raw=blobs[ref['path']]
    if not isinstance(raw,bytes) or len(raw)>16384 or hashlib.sha256(raw).hexdigest()!=ref['sha256']:
        raise ValueError('artifact reference bytes')
    if 'bytes' in ref and (type(ref['bytes']) is not int or ref['bytes']!=len(raw)):
        raise ValueError('artifact byte count')
    return json.loads(raw)


def candidate_points(current,record,n):
    minimum=record.get('minimum');kind=record['kind'];rows=record['rows']
    if type(minimum) is not list or len(minimum)!=(2 if kind=='row' else 3) or type(minimum[0]) is not int:
        raise ValueError('recorded minimum schema')
    columns=minimum[1:]
    for cols in columns:
        if type(cols) is not list or len(cols) not in (1,2) or any(type(x) is not int or not 0<=x<n for x in cols) or cols!=sorted(set(cols)):
            raise ValueError('recorded selected columns')
    if sum(map(len,columns))!=sum(current['row_counts'][r] for r in rows):
        raise ValueError('selected load changed')
    points=tuple(p for p in current['points'] if p[1] not in rows)+tuple((x,row) for row,cols in zip(rows,columns) for x in cols)
    return points_checked(points,n)


def audit_authority(raw,initial,blobs,*,n,expected_initial_hash,expected_initial_score,expected_base,
                    historical_pair_prefix,historical_row_complete,max_states,check,side_outputs=()):
    """Audit a supplied snapshot and explicit references, not a directory or search.

    Direct triples verify accepted states and rankings. Recorded nonimproving
    minima remain source-supported; their optimizers/candidate scores are not
    independently replayed. Side outputs never become authoritative implicitly.
    """
    if type(raw) is not bytes or type(max_states) is not int or not 1<=max_states<=67 or len(raw)>1024*1024:
        raise ValueError('explicit bounded scope')
    document=json.loads(raw)
    if type(document) is not dict or set(document)!={'payload','payload_sha256'} or document['payload_sha256']!=hashed(document['payload']):
        raise ValueError('authority payload identity')
    a=document['payload']
    required={'schema','policy','n','points','U','state_hash','generation','base','counters','caps','origin','phase',
              'row_cursor','pair_cursor','row_sweep_complete','pair_scan_complete','orders','pending','attempts','artifacts','witness','status'}
    if type(a) is not dict or set(a)!=required:raise ValueError('authority keys')
    integer_fields(a,('n','U','generation','row_cursor','pair_cursor'))
    counter_fields(a['base']);counter_fields(a['counters'])
    if a['pending'] is not None and (type(a['pending']) is not int or a['pending']<1):raise ValueError('pending type')
    integer_fields(a['caps'],('row','pair'))
    integer_fields(initial,('n','score'))
    if type(expected_initial_score) is not int or expected_initial_score<0:raise ValueError('expected score type')
    if a.get('schema')!='two-row-suffix-authority-v1' or a.get('policy')!=POLICY or type(a.get('n')) is not int or a['n']!=n:
        raise ValueError('authority schema/policy')
    if (type(expected_base) is not dict or set(expected_base)!=set(COUNTERS)
            or any(type(v) is not int or v<0 for v in expected_base.values()) or a.get('base')!=expected_base):
        raise ValueError('expected base binding')
    if a.get('caps')!={'row':512,'pair':96}:
        raise ValueError('fixed suffix ceilings')
    origin=a.get('origin')
    if (type(origin) is not dict or set(origin)!={'state_hash','pair_prefix','row_complete','basis'}
            or type(origin.get('pair_prefix')) is not int or origin.get('state_hash')!=expected_initial_hash
            or origin.get('pair_prefix')!=historical_pair_prefix or origin.get('row_complete') is not historical_row_complete
            or origin.get('basis')!=('source_bound_prior_execution_not_independent_minimum_certificate' if historical_row_complete else 'synthetic_fresh')):
        raise ValueError('historical source-supported coverage binding')
    if (type(historical_pair_prefix) is not int or not 0<=historical_pair_prefix<=expected_base['pair_completed']
            or type(historical_row_complete) is not bool or (historical_pair_prefix and not historical_row_complete)):
        raise ValueError('historical prefix schema')
    cache={};accepted_states=[]
    def state(values):
        points=points_checked(values,n);identity=state_identity(n,points)
        if identity not in cache:
            if len(cache)>=max_states:raise ValueError('state recount allocation exhausted')
            cache[identity]=recount(points,n,check)
        elif cache[identity]['points']!=points:raise ValueError('state identity collision')
        return cache[identity]
    current=state(initial['points'])
    if (initial.get('n')!=n or initial.get('state_hash')!=expected_initial_hash or initial.get('score')!=expected_initial_score
            or current['state_hash']!=expected_initial_hash or current['U']!=expected_initial_score):
        raise ValueError('initial independent identity/score')
    accepted_states.append(current)
    rc=len(current['orders']['rows']) if historical_row_complete else 0;pc=historical_pair_prefix
    row_done=historical_row_complete;pair_done=False
    if pc>len(current['orders']['pairs']):raise ValueError('historical prefix exceeds direct ranking')
    for kind in ('row','pair'):
        if not expected_base[kind+'_completed']<=expected_base[kind+'_started']<=a['caps'][kind]:raise ValueError('base counter order')
    counts=dict(expected_base);attempts=a.get('attempts');refs=a.get('artifacts')
    if type(attempts) is not list or len(attempts)>268 or type(refs) is not list or len(refs)>65:
        raise ValueError('ledger/reference count')
    accepted=0;pending=None;observations=[];source_supported_nonimprovements=0;abandoned=0
    for seq,r in enumerate(attempts,1):
        check()
        if type(r) is not dict or len(canonical(r))>1024 or r.get('seq')!=seq or r.get('kind') not in ('row','pair'):
            raise ValueError('attempt schema/sequence')
        integer_fields(r,('seq','cursor','before_score'))
        if type(r.get('rows')) is not list or any(type(y) is not int for y in r['rows']):raise ValueError('attempt rows type')
        expected_record={'seq','kind','rows','state_hash','order_hash','cursor','outcome','before_score'}
        if r.get('outcome') in ('complete','accepted'):expected_record|={'minimum','enumeration_complete'}
        if set(r)!=expected_record:raise ValueError('attempt exact keys')
        kind=r['kind'];outcome=r.get('outcome');phase='pair' if row_done else 'row'
        cursor=pc if kind=='pair' else rc;order=current['orders']['pairs' if kind=='pair' else 'rows']
        if current['U']==0 or pair_done or kind!=phase or cursor>=len(order):raise ValueError('attempt outside active next neighborhood')
        expected_rows=order[cursor] if kind=='pair' else [order[cursor]]
        if (r.get('state_hash')!=current['state_hash'] or r.get('order_hash')!=current['orders']['sha256']
                or r.get('cursor')!=cursor or r.get('rows')!=expected_rows or r.get('before_score')!=current['U']):
            raise ValueError('state-keyed next neighborhood/score binding')
        counts[kind+'_started']+=1
        if counts[kind+'_started']>a['caps'][kind] or counts[kind+'_started']-expected_base[kind+'_started']>(204 if kind=='row' else 64):
            raise ValueError('cumulative/epoch start cap')
        if outcome=='pending':
            if seq!=len(attempts):raise ValueError('pending must be final')
            pending=seq
        elif outcome=='abandoned':abandoned+=1
        elif outcome in ('complete','accepted'):
            proposed=candidate_points(current,r,n);score=r['minimum'][0]
            if type(r.get('enumeration_complete')) is not bool or (score>0 and not r['enumeration_complete']):
                raise ValueError('positive partial result cannot complete')
            counts[kind+'_completed']+=1
            if outcome=='complete':
                if score!=current['U']:raise ValueError('nonimprovement current-included score')
                source_supported_nonimprovements+=1
                if kind=='row':rc+=1;row_done=rc==len(current['orders']['rows'])
                else:pc+=1;pair_done=pc==len(current['orders']['pairs'])
            else:
                if not 0<=score<current['U'] or accepted>=len(refs):raise ValueError('accepted strict score/reference')
                move=reference_blob(refs[accepted],blobs,check)
                integer_fields(move,('n','score','before_score','generation','attempt','old_pair_cursor'))
                counter_fields(move.get('counters'))
                if type(move.get('rows')) is not list or any(type(y) is not int for y in move['rows']):raise ValueError('move row types')
                if canonical(move.get('minimum'))!=canonical(r['minimum']):raise ValueError('move minimum exact types')
                after=state(move.get('points'))
                counts['accepted']+=1
                if (move.get('schema')!='two-row-suffix-move-v1' or move.get('n')!=n
                        or move.get('before_hash')!=current['state_hash'] or move.get('before_score')!=current['U']
                        or move.get('state_hash')!=after['state_hash'] or move.get('score')!=after['U'] or after['U']!=score
                        or move.get('generation')!=counts['accepted'] or move.get('attempt')!=seq
                        or move.get('kind')!=kind or move.get('rows')!=expected_rows or move.get('minimum')!=r['minimum']
                        or move.get('counters')!=counts or move.get('old_row_sweep_complete') is not row_done
                        or move.get('old_pair_cursor')!=pc or move.get('enumeration_complete') is not r['enumeration_complete']
                        or after['points']!=proposed):
                    raise ValueError('accepted move artifact/independent geometry binding')
                current=after;accepted+=1;accepted_states.append(current)
                rc=pc=0;row_done=pair_done=False
        else:raise ValueError('attempt outcome')
        observations.append({'seq':seq,'kind':kind,'outcome':outcome,'state_hash':r['state_hash'],'cursor':cursor})
    if accepted!=len(refs) or accepted>expected_initial_score:
        raise ValueError('accepted-chain completeness/bound')
    if a.get('counters')!=counts or a.get('generation')!=counts['accepted'] or a.get('pending')!=pending:
        raise ValueError('authority counter/generation/pending binding')
    final=points_checked(a.get('points'),n)
    if final!=current['points'] or a.get('state_hash')!=current['state_hash'] or a.get('U')!=current['U']:
        raise ValueError('durable authority differs from last accepted state')
    expected_phase='done' if current['U']==0 or pair_done else ('pair' if row_done else 'row')
    if (a.get('phase')!=expected_phase or a.get('row_cursor')!=rc or a.get('pair_cursor')!=pc
            or a.get('row_sweep_complete') is not row_done or a.get('pair_scan_complete') is not pair_done):
        raise ValueError('durable cursor/coverage/phase binding')
    if a.get('orders') is None:
        if pending is not None or rc or pc or row_done or pair_done:raise ValueError('cleared orders retain coverage')
    elif canonical(a['orders'])!=canonical(current['orders']):raise ValueError('current direct ranking/order identity')
    side_results=[]
    witness=a.get('witness')
    all_side=list(side_outputs)
    if len(all_side)>3:raise ValueError('side-output audit scope')
    if witness is not None:all_side.append({'kind':'authoritative_witness','ref':witness})
    for item in all_side:
        value=reference_blob(item['ref'],blobs,check);kind=item['kind']
        if kind in ('authoritative_witness','saved_witness'):
            certificate=value.get('certificate')
            if type(certificate) is not dict or type(certificate.get('n')) is not int or certificate.get('n')!=n:raise ValueError('witness certificate schema')
            side=state(certificate.get('points'))
            if side['U']!=0 or type(certificate.get('claimed_conflict_count')) is not int or certificate.get('claimed_conflict_count')!=0:raise ValueError('witness not independent zero')
            if kind=='authoritative_witness' and (current['U']!=0 or side['points']!=current['points']):
                raise ValueError('authoritative witness/state mismatch')
        elif kind in ('raw_candidate','orphan_move'):
            integer_fields(value,('n','score'))
            if value.get('n')!=n:raise ValueError('side candidate grid')
            side=state(value.get('points'))
            if value.get('score')!=side['U']:raise ValueError('side candidate independent score')
        else:raise ValueError('side-output kind')
        side_results.append({'kind':kind,'path':item['ref']['path'],'state_hash':side['state_hash'],'U':side['U'],
                             'authoritative':kind=='authoritative_witness'})
    if accepted and current['U']==0 and witness is None:raise ValueError('accepted zero lacks witness reference')
    if a['status'] not in ('active','zero','no_strict_descent','row_cap','pair_cap','search_deadline','error','zero_unverified','split'):
        raise ValueError('durable status schema')
    if a['status']=='zero' and current['U']!=0 or a['status']=='no_strict_descent' and not pair_done:
        raise ValueError('durable status/state')
    if a['status'] in ('row_cap','pair_cap'):
        kind=a['status'].split('_')[0];allowance=204 if kind=='row' else 64
        if counts[kind+'_started']<a['caps'][kind] and counts[kind+'_started']-expected_base[kind+'_started']<allowance:
            raise ValueError('cap status without exhausted allowance')
    check()
    return {'authority_chain_passed':True,'n':n,'unique_states_recounted':len(cache),
            'accepted_scores':[s['U'] for s in accepted_states],'accepted_state_hashes':[s['state_hash'] for s in accepted_states],
            'new_accepted_moves':accepted,'counters':counts,'new_attempts':len(attempts),'abandoned_starts':abandoned,
            'pending_attempt':pending,'durable_status':a['status'],'receipt_acceptance_checked':False,'durable_U':current['U'],'durable_state_hash':current['state_hash'],
            'direct_rankings_checked':len(cache),'observations':observations,'side_outputs':side_results,
            'historical_coverage_basis':origin['basis'],'historical_pair_prefix':historical_pair_prefix,
            'recorded_nonimprovements_not_independent_minima':source_supported_nonimprovements,
            'cursor_accounting':{'row_cursor':rc,'pair_cursor':pc,'row_sweep_complete':row_done,'pair_scan_complete':pair_done},
            'limits':'Direct state scores/rankings, accepted-move legality and ledger accounting only. No optimizer/minimum replay or independent prefix exclusion. Side outputs never adopted. Receipt/resource/lifecycle acceptance is separate.'}
