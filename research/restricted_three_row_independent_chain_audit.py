"""Independent supplied-byte three-row chain audit; no production import, file discovery or optimizer."""
from itertools import combinations
import hashlib
import json
from research import two_row_suffix_independent_authority_audit as common

POLICY='restricted-three-row-Kpositive-M-rst-four-current-unary-globallex-v1'
canonical=common.canonical
hashed=common.hashed
points_checked=common.points_checked
reference_blob=common.reference_blob
COUNTERS=('started','completed','accepted')


def integers(value,names):common.integer_fields(value,names)
def counters(value):
    if type(value) is not dict or set(value)!=set(COUNTERS):raise ValueError('counter keys')
    integers(value,COUNTERS)


def geometry(values,n,check):
    points=points_checked(values,n);U=0;I=[0]*n;J={};K={}
    for seq,(p,q,r) in enumerate(combinations(points,3)):
        if seq%1024==0:check()
        if (q[0]-p[0])*(r[1]-p[1])!=(q[1]-p[1])*(r[0]-p[0]):continue
        ys=tuple(sorted((p[1],q[1],r[1])));U+=1
        if len(set(ys))!=3:raise ValueError('horizontal conflict invariant')
        for y in ys:I[y]+=1
        for pair in combinations(ys,2):J[pair]=J.get(pair,0)+1
        K[ys]=K.get(ys,0)+1
    M={ys:sum(I[y] for y in ys)-sum(J.get(p,0) for p in combinations(ys,2))+v for ys,v in K.items()}
    blocks=[[*ys,M[ys],K[ys]] for ys in sorted(K,key=lambda ys:(-M[ys],*ys))]
    state_hash=common.state_identity(n,points)
    orders={'blocks':blocks,'sha256':hashed({'state_hash':state_hash,'policy':POLICY,'blocks':blocks})}
    check();return {'points':points,'U':U,'state_hash':state_hash,'orders':orders}


def result_columns(record,current,n):
    minimum=record.get('minimum');domains=record.get('domains');rows=record['rows']
    if type(minimum) is not list or len(minimum)!=4 or type(minimum[0]) is not int or minimum[0]<0:
        raise ValueError('minimum schema')
    if type(domains) is not list or len(domains)!=3:raise ValueError('domains schema')
    for row,domain,cols in zip(rows,domains,minimum[1:]):
        if (type(domain) is not list or len(domain)!=min(4,n) or domain!=sorted(set(domain))
                or any(type(x) is not int or not 0<=x<n for x in domain)
                or not {x for x,y in current['points'] if y==row}<=set(domain)):
            raise ValueError('current-inclusive domain')
        if (type(cols) is not list or len(cols) not in (1,2) or cols!=sorted(set(cols))
                or any(type(x) is not int or x not in domain for x in cols)):
            raise ValueError('selected columns')
    if sum(map(len,minimum[1:]))!=sum(y in rows for x,y in current['points']):raise ValueError('selected load')
    points=tuple(p for p in current['points'] if p[1] not in rows)+tuple((x,y) for y,cols in zip(rows,minimum[1:]) for x in cols)
    return points_checked(points,n)


def audit_chain(raw,initial,blobs,*,n,initial_hash,initial_score,max_states,check,side_outputs=()):
    if type(raw) is not bytes or len(raw)>1024*1024 or type(max_states) is not int or not 1<=max_states<=17:
        raise ValueError('bounded explicit scope')
    doc=json.loads(raw)
    if type(doc) is not dict or set(doc)!={'payload','payload_sha256'} or doc['payload_sha256']!=hashed(doc['payload']):
        raise ValueError('authority wrapper')
    a=doc['payload'];fields={'schema','policy','n','points','U','state_hash','origin_hash','generation','counters','start_cap',
                          'orders','cursor','pending','attempts','artifacts','witness','status'}
    if type(a) is not dict or set(a)!=fields or a['schema']!='restricted-three-row-authority-v1' or a['policy']!=POLICY:
        raise ValueError('authority schema')
    integers(a,('n','U','generation','start_cap','cursor'));counters(a['counters'])
    integers(initial,('n','score'))
    if (a['n']!=n or a['start_cap']!=16 or type(initial_score) is not int or not 0<=initial_score<=65
            or initial['n']!=n or initial['score']!=initial_score or initial.get('state_hash')!=initial_hash
            or a['origin_hash']!=initial_hash):raise ValueError('initial fixed identity')
    if a['pending'] is not None and (type(a['pending']) is not int or not 1<=a['pending']<=16):raise ValueError('pending type')
    cache={}
    def state(points):
        normalized=points_checked(points,n);identity=common.state_identity(n,normalized)
        if identity not in cache:
            if len(cache)>=max_states:raise ValueError('direct-state allocation exhausted')
            cache[identity]=geometry(normalized,n,check)
        if cache[identity]['points']!=normalized:raise ValueError('identity collision')
        return cache[identity]
    current=state(initial['points'])
    if current['state_hash']!=initial_hash or current['U']!=initial_score:raise ValueError('direct initial identity/score')
    counts=dict.fromkeys(COUNTERS,0);cursor=0;pending=None;last_charge=None;accepted=[];scores=[current['U']];ids=[current['state_hash']]
    records=a['attempts'];refs=a['artifacts'];observations=[];nonimproving=0
    if type(records) is not list or len(records)>16 or type(refs) is not list or len(refs)>16:raise ValueError('ledger bounds')
    for seq,r in enumerate(records,1):
        check();required={'seq','rows','state_hash','order_hash','cursor','outcome','before_score'}
        if type(r) is not dict or len(canonical(r))>2048:raise ValueError('record schema')
        integers(r,('seq','cursor','before_score'))
        if (r['seq']!=seq or r.get('state_hash')!=current['state_hash'] or r.get('before_score')!=current['U']
                or current['U']==0 or cursor>=len(current['orders']['blocks'])):raise ValueError('current attempt identity')
        rows=current['orders']['blocks'][cursor][:3]
        if (canonical(r.get('rows'))!=canonical(rows) or r['cursor']!=cursor or r.get('order_hash')!=current['orders']['sha256']):
            raise ValueError('next candidate binding')
        counts['started']+=1;last_charge=dict(counts);outcome=r.get('outcome')
        if outcome=='pending':
            if set(r)!=required or seq!=len(records):raise ValueError('final pending schema')
            pending=seq
        elif outcome in ('complete','accepted'):
            if set(r)!=required|{'minimum','optimum_established','enumeration_exhausted','domains','after_hash'}:
                raise ValueError('completed schema')
            proposed=result_columns(r,current,n);score=r['minimum'][0]
            if (r['optimum_established'] is not True or type(r['enumeration_exhausted']) is not bool
                    or score>0 and not r['enumeration_exhausted']):raise ValueError('partial positive result')
            counts['completed']+=1
            if outcome=='complete':
                if score!=current['U'] or r['after_hash']!=current['state_hash']:raise ValueError('nonimprovement binding')
                nonimproving+=1;cursor+=1
            else:
                if not 0<=score<current['U'] or len(accepted)>=len(refs):raise ValueError('strict accepted reference')
                move=reference_blob(refs[len(accepted)],blobs,check);after=state(move.get('points'))
                counts['accepted']+=1
                expected={'schema':'restricted-three-row-move-v1','n':n,'points':[list(p) for p in after['points']],
                          'score':score,'before_score':current['U'],'before_hash':current['state_hash'],'state_hash':after['state_hash'],
                          'generation':counts['accepted'],'attempt':seq,'rows':rows,'minimum':r['minimum'],'domains':r['domains'],
                          'counters':dict(counts),'old_order_hash':current['orders']['sha256'],'old_cursor':cursor,
                          'optimum_established':True,'enumeration_exhausted':r['enumeration_exhausted']}
                if (canonical(move)!=canonical(expected) or after['U']!=score or after['points']!=proposed
                        or r['after_hash']!=after['state_hash']):raise ValueError('accepted direct geometry/artifact binding')
                accepted.append(refs[len(accepted)]);current=after;cursor=0;scores.append(after['U']);ids.append(after['state_hash'])
        else:raise ValueError('attempt outcome')
        observations.append({'seq':seq,'state_hash':r['state_hash'],'rows':rows,'cursor':r['cursor'],'outcome':outcome})
    if len(refs)!=len(accepted):raise ValueError('accepted reference completeness')
    if (a['counters']!=counts or a['generation']!=counts['accepted'] or a['pending']!=pending or a['cursor']!=cursor
            or points_checked(a['points'],n)!=current['points'] or a['U']!=current['U'] or a['state_hash']!=current['state_hash']):
        raise ValueError('final authority chain binding')
    if a['orders'] is None:
        if cursor or pending is not None or records and records[-1]['outcome']!='accepted':raise ValueError('absent orders with old coverage')
    elif canonical(a['orders'])!=canonical(current['orders']):raise ValueError('direct final order')
    statuses=('active','zero','block_cap','restricted_candidate_list_exhausted','search_deadline','error','zero_unverified','split')
    if a['status'] not in statuses:raise ValueError('status schema')
    if a['status']=='zero' and current['U']!=0:raise ValueError('zero status')
    if a['status']=='block_cap' and counts['started']!=16:raise ValueError('unexhausted block cap')
    if a['status']=='restricted_candidate_list_exhausted' and (pending is not None or current['U']==0 or cursor!=len(current['orders']['blocks'])):
        raise ValueError('unexhausted candidates')
    if current['U']==0 and counts['accepted'] and a['witness'] is None:raise ValueError('accepted zero witness absent')
    if type(side_outputs) not in (list,tuple) or len(side_outputs)>3:raise ValueError('side scope')
    sides=list(side_outputs)
    if a['witness'] is not None:sides.append({'kind':'authoritative_witness','ref':a['witness']})
    side_results=[]
    for item in sides:
        if type(item) is not dict or set(item)!={'kind','ref'}:raise ValueError('side schema')
        value=reference_blob(item['ref'],blobs,check);kind=item['kind']
        if kind in ('authoritative_witness','saved_witness'):
            cert=value.get('certificate');integers(cert,('n','claimed_conflict_count'))
            if cert['n']!=n or cert['claimed_conflict_count']!=0:raise ValueError('certificate schema')
            side=state(cert.get('points'))
            if side['U']!=0:raise ValueError('saved witness not zero')
            if kind=='authoritative_witness' and side['state_hash']!=current['state_hash']:raise ValueError('authority/witness mismatch')
        elif kind in ('orphan_move','raw_candidate'):
            integers(value,('n','score'));side=state(value.get('points'))
            if value['n']!=n or value['score']!=side['U']:raise ValueError('side candidate score')
        else:raise ValueError('side kind')
        side_results.append({'kind':kind,'state_hash':side['state_hash'],'U':side['U'],'adopted':kind=='authoritative_witness'})
    check()
    return {'authority_chain_passed':True,'receipt_acceptance_checked':False,'unique_states_recounted':len(cache),
            'accepted_scores':scores,'accepted_state_hashes':ids,'new_accepted_moves':len(accepted),'counters':counts,
            'last_start_charge':last_charge,'pending_attempt':pending,'cursor':cursor,'durable_status':a['status'],
            'durable_U':current['U'],'durable_state_hash':current['state_hash'],'observations':observations,'side_outputs':side_results,
            'recorded_nonimprovements_not_independent_minima':nonimproving,
            'limits':'Direct accepted/side scores, candidate rankings and ledger/support only. Domain selection and recorded minima remain source-supported. No optimizer replay, exclusion, filesystem or receipt acceptance.'}
