"""Fixed audited65 restricted three-row descent; SOURCE/TINY only until allocated.

Sixteen TOTAL starts, current-inclusive four-column domains, induced K>0 blocks.
No row/pair controller, restart, widening, resume CLI or automatic continuation.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
KERNEL_SHA = '0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
SUFFIX_SHA = 'fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'
# Authenticate imported helper bytes before executing either module. These are
# source reads only: no original point artifact or geometry is loaded here.
for _name, _sha in (('two_row_descent75.py', KERNEL_SHA), ('two_row_suffix75.py', SUFFIX_SHA)):
    if hashlib.sha256((ROOT/'research'/_name).read_bytes()).hexdigest() != _sha:
        raise ValueError('frozen helper source drift: '+_name)
from research import two_row_descent75 as kernel
from research import two_row_suffix75 as shared

POLICY = 'restricted-three-row-Kpositive-M-rst-four-current-unary-globallex-v1'
MAX_STARTS = 16
MAX_PUBLICATIONS = 34
MAX_INDEX_ATTEMPTS = 17
CAP = 1024*1024
HANDOFF_PATH = shared.HANDOFF_PATH
HANDOFF_SHA = shared.HANDOFF_SHA
FIXED_STATE = shared.FIXED_STATE
compact = kernel.compact
digest = kernel.digest
SearchStop = kernel.SearchStop
clone = shared.clone
hashed = shared.hashed
atomic_file = shared.atomic_file
json_file = shared.json_file
# Reviewed boundaries: fixed metadata authentication plus fresh dual recount;
# exact-zero validators/immediate durable save. Never invoke shared.drive/run.
load_handoff = shared.load_handoff
preserve_zero = shared.preserve_zero


def collinear(p, q, r):
    return (q[0]-p[0])*(r[1]-p[1]) == (r[0]-p[0])*(q[1]-p[1])


def priorities(points, index, n, check=lambda:None, work=None):
    work = {} if work is None else work
    kernel.phase(work, 'selection', check)
    I = [0]*n; J = Counter(); K = Counter()
    for mask in index.values():
        check(); kernel.inc(work, 'selection_line_visits')
        t = mask.bit_count()
        if t < 3: continue
        rows = []; remaining = mask
        while remaining:
            bit = remaining & -remaining; remaining ^= bit
            rows.append(points[bit.bit_length()-1][1])
        rows.sort()
        if len(set(rows)) != t: raise ValueError('violating horizontal line')
        for r in rows:
            check(); I[r] += kernel.choose2(t-1)
        for pair in combinations(rows, 2):
            check(); kernel.inc(work, 'selection_pair_updates'); J[pair] += t-2
        for triple in combinations(rows, 3):
            check(); kernel.inc(work, 'selection_triple_updates'); K[triple] += 1
    if sum(K.values()) > 65: raise ValueError('score exceeds fixed65 selection bound')
    M = {(r,s,t):I[r]+I[s]+I[t]-J[r,s]-J[r,t]-J[s,t]+k for (r,s,t),k in K.items()}
    rows = sorted(K, key=lambda p:(-M[p], *p))
    return {'I':tuple(I), 'J':J, 'K':K, 'M':M, 'blocks':rows}


def make_orders(points, index, n, state_hash, check=lambda:None, work=None):
    p = priorities(points, index, n, check, work)
    records = [[*rows, p['M'][rows], p['K'][rows]] for rows in p['blocks']]
    return {'blocks':records, 'sha256':hashed({'state_hash':state_hash, 'policy':POLICY, 'blocks':records})}


def domain(current, unary, n, check=lambda:None):
    """At most three missing minima are retained; never cache n outcomes."""
    selected = set(current); missing = []; count = min(4,n)-len(selected)
    for x in range(n):
        check()
        if x in selected: continue
        item = unary[x], x
        if len(missing) < count:
            missing.append(item); missing.sort()
        elif count and item < missing[-1]:
            missing[-1] = item; missing.sort()
    return tuple(sorted(selected | {x for cost,x in missing}))


def block_tables(points, index, n, rows, check=lambda:None, work=None):
    work = {} if work is None else work
    if (len(rows) != 3 or any(type(r) is not int for r in rows)
            or not 0 <= rows[0] < rows[1] < rows[2] < n): raise ValueError('row triple')
    rows = tuple(rows); maskout = sum(1 << i for i,p in enumerate(points) if p[1] in rows)
    unary = [[0]*n for r in rows]; base = 0; current_score = 0
    kernel.phase(work, 'retained_lines', check)
    for (a,b,c),mask in index.items():
        check(); kernel.inc(work, 'retained_line_visits'); k = (mask & ~maskout).bit_count()
        current_score += kernel.choose3(mask.bit_count())
        base += kernel.choose3(k)
        if k < 2 or a == 0: continue
        for row,u in zip(rows, unary):
            check(); kernel.inc(work, 'unary_intersections'); num = c-b*row
            if num % a == 0 and 0 <= num//a < n: u[num//a] += kernel.choose2(k)
    retained = tuple(p for p in points if p[1] not in rows)
    current = tuple(tuple(x for x,y in points if y == row) for row in rows)
    domains = tuple(domain(cols,u,n,check) for cols,u in zip(current,unary))
    d0,d1,d2 = map(len,domains)
    C = {}
    kernel.phase(work, 'cross_tables', check)
    for i,j in ((0,1),(0,2),(1,2)):
        table = bytearray(len(domains[i])*len(domains[j]))
        for a,x in enumerate(domains[i]):
            for b,y in enumerate(domains[j]):
                value = 0
                for q in retained:
                    check(); kernel.inc(work, 'cross_determinants')
                    value += collinear((x,rows[i]),(y,rows[j]),q)
                table[a*len(domains[j])+b] = value
        C[i,j] = table
    T = bytearray(d0*d1*d2)
    kernel.phase(work, 'ternary_table', check)
    for a,x in enumerate(domains[0]):
        for b,y in enumerate(domains[1]):
            for c,z in enumerate(domains[2]):
                check(); kernel.inc(work, 'ternary_determinants')
                T[(a*d1+b)*d2+c] = collinear((x,rows[0]),(y,rows[1]),(z,rows[2]))
    return {'retained':retained, 'base':base, 'current_score':current_score, 'unary':unary, 'domains':domains,
            'current':current, 'C':C, 'T':T, 'rows':rows}


def row_sets(cols, size=None):
    # Singleton (x,) precedes every (x,y), then the next singleton.
    for i,x in enumerate(cols):
        if size in (None,1): yield (x,)
        if size in (None,2):
            for y in cols[i+1:]: yield (x,y)


def assignments(domains, total):
    if total not in (5,6): raise ValueError('block load')
    for X in row_sets(domains[0], 2 if total == 6 else None):
        for Y in row_sets(domains[1], 2 if total == 6 else None):
            load = total-len(X)-len(Y)
            if load in (1,2):
                for Z in row_sets(domains[2], load): yield X,Y,Z


def objective(tables, X, Y, Z):
    domains = tables['domains']; unary = tables['unary']; C = tables['C']; T = tables['T']
    cols = X,Y,Z
    indices = tuple(tuple(domains[i].index(x) for x in cols[i]) for i in range(3))
    d1,d2 = len(domains[1]),len(domains[2])
    value = tables['base'] + sum(unary[i][x] for i in range(3) for x in cols[i])
    for i,j in ((0,1),(0,2),(1,2)):
        value += sum(C[i,j][a*len(domains[j])+b] for a in indices[i] for b in indices[j])
    return value + sum(T[(a*d1+b)*d2+c] for a in indices[0] for b in indices[1] for c in indices[2])


def block_optimum(points, index, n, rows, check=lambda:None, work=None):
    work = {} if work is None else work
    t = block_tables(points,index,n,rows,check,work)
    old = t['current_score']
    if objective(t,*t['current']) != old: raise ValueError('current objective identity')
    total = len(points)-len(t['retained']); best = None; exhausted = True
    kernel.phase(work, 'assignments', check)
    for X,Y,Z in assignments(t['domains'],total):
        check(); kernel.inc(work, 'assignments'); item = objective(t,X,Y,Z),X,Y,Z
        if best is None or item < best: best = item
        if item[0] == 0:
            exhausted = False; break
    if best is None or best[0] > old: raise ValueError('current assignment excluded')
    changed = tuple(sorted(t['retained']+tuple((x,row) for row,cols in zip(rows,best[1:]) for x in cols)))
    return {'score':best[0], 'X':best[1], 'Y':best[2], 'Z':best[3], 'points':changed,
            'zero':best[0] == 0, 'optimum_established':True, 'enumeration_exhausted':exhausted,
            'domains':t['domains']}


def new_authority(points, n, *, prepared=None, check=lambda:None, work=None):
    prepared = kernel.build_index(points,n,check,work) if prepared is None else prepared
    points,index,score = prepared; points = kernel.validate_points(points,n)
    if type(score) is not int or not 0 <= score <= 65: raise ValueError('initial score')
    state_hash = kernel.normalized_sha256(n,points)
    orders = None if not score else make_orders(points,index,n,state_hash,check,work)
    a = {'schema':'restricted-three-row-authority-v1','policy':POLICY,'n':n,'points':points,'U':score,
         'state_hash':state_hash,'origin_hash':state_hash,'generation':0,'counters':{'started':0,'completed':0,'accepted':0},
         'start_cap':MAX_STARTS,'orders':orders,'cursor':0,'pending':None,'attempts':[],'artifacts':[],
         'witness':None,'status':'active' if score else 'zero'}
    return clone(validate_authority(a))


def valid_ref(ref):
    if (type(ref) is not dict or set(ref) != {'path','sha256','bytes'} or len(compact(ref)) > 512
            or type(ref['path']) is not str or not 0 < len(ref['path']) <= 256
            or Path(ref['path']).name != ref['path'] or ref['path'] in ('.','..')
            or type(ref['sha256']) is not str or len(ref['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in ref['sha256'])
            or type(ref['bytes']) is not int or not 0 < ref['bytes'] <= 16384): raise ValueError('artifact reference')


def validate_authority(a):
    fields = {'schema','policy','n','points','U','state_hash','origin_hash','generation','counters','start_cap',
              'orders','cursor','pending','attempts','artifacts','witness','status'}
    if (type(a) is not dict or set(a) != fields or a['schema'] != 'restricted-three-row-authority-v1'
            or a['policy'] != POLICY or type(a['start_cap']) is not int or a['start_cap'] != MAX_STARTS): raise ValueError('authority schema')
    points = kernel.validate_points(a['points'],a['n'])
    if (kernel.normalized_sha256(a['n'],points) != a['state_hash'] or type(a['U']) is not int
            or not 0 <= a['U'] <= 65 or type(a['origin_hash']) is not str or len(a['origin_hash']) != 64): raise ValueError('state identity')
    counters = a['counters']
    if (set(counters) != {'started','completed','accepted'} or any(type(v) is not int for v in counters.values())
            or not 0 <= counters['accepted'] <= counters['completed'] <= counters['started'] <= MAX_STARTS
            or type(a['generation']) is not int or a['generation'] != counters['accepted']): raise ValueError('global counts')
    attempts = a['attempts']; refs = a['artifacts']
    if (type(attempts) is not list or len(attempts) != counters['started']
            or type(refs) is not list or len(refs) != counters['accepted']): raise ValueError('ledger count')
    pending = []; completed = accepted = 0; chain = a['origin_hash']; score = None
    for seq,r in enumerate(attempts,1):
        required = {'seq','rows','state_hash','order_hash','cursor','outcome','before_score'}
        if type(r) is not dict or not required <= r.keys() or len(compact(r)) > 2048 or r['seq'] != seq: raise ValueError('attempt schema')
        if (type(r['rows']) is not list or len(r['rows']) != 3 or any(type(x) is not int for x in r['rows'])
                or not 0 <= r['rows'][0] < r['rows'][1] < r['rows'][2] < a['n']
                or r['state_hash'] != chain or type(r['before_score']) is not int or not 0 < r['before_score'] <= 65
                or (score is not None and score != r['before_score']) or type(r['cursor']) is not int or r['cursor'] < 0): raise ValueError('attempt state')
        if r['outcome'] == 'pending':
            if set(r) != required: raise ValueError('pending result fields')
            pending.append(seq)
        elif r['outcome'] in ('complete','accepted'):
            if set(r) != required | {'minimum','optimum_established','enumeration_exhausted','domains','after_hash'}: raise ValueError('complete result fields')
            item = r['minimum']
            if (type(item) is not list or len(item) != 4 or type(item[0]) is not int or not 0 <= item[0] <= r['before_score']
                    or r['optimum_established'] is not True or type(r['enumeration_exhausted']) is not bool
                    or (item[0] > 0 and not r['enumeration_exhausted'])): raise ValueError('result optimum')
            ds = r['domains']
            if (type(ds) is not list or len(ds) != 3 or any(type(d) is not list or len(d) != min(4,a['n'])
                    or d != sorted(set(d)) or any(type(x) is not int or not 0 <= x < a['n'] for x in d) for d in ds)
                    or any(type(cols) is not list or len(cols) not in (1,2) or cols != sorted(set(cols))
                        or any(x not in d for x in cols) for d,cols in zip(ds,item[1:]))
                    or sum(map(len,item[1:])) not in (5,6)): raise ValueError('result domains/loads')
            completed += 1
            if r['outcome'] == 'accepted':
                if item[0] >= r['before_score'] or r['after_hash'] == chain: raise ValueError('non-strict accepted')
                accepted += 1; chain = r['after_hash']
            elif item[0] != r['before_score'] or r['after_hash'] != chain: raise ValueError('nonimprovement')
            score = item[0]
        else: raise ValueError('attempt outcome')
    if (completed != counters['completed'] or accepted != counters['accepted'] or chain != a['state_hash']
            or (score is not None and score != a['U']) or pending != ([] if a['pending'] is None else [a['pending']])
            or (pending and pending != [len(attempts)])): raise ValueError('ledger binding')
    for ref in refs+([] if a['witness'] is None else [a['witness']]): valid_ref(ref)
    if a['witness'] is not None and a['U'] != 0: raise ValueError('positive witness authority')
    if type(a['cursor']) is not int or a['cursor'] < 0: raise ValueError('cursor')
    orders = a['orders']
    current_records = [r for r in attempts if r['state_hash'] == a['state_hash']]
    if orders is None:
        if a['cursor'] or a['pending'] is not None or current_records: raise ValueError('unmaterialized coverage')
    else:
        if (type(orders) is not dict or set(orders) != {'blocks','sha256'} or type(orders['blocks']) is not list
                or len(orders['blocks']) > 65 or len(compact(orders)) > 8192): raise ValueError('candidate cap')
        blocks = orders['blocks']
        if any(type(b) is not list or len(b) != 5 or any(type(x) is not int for x in b)
                or not 0 <= b[0] < b[1] < b[2] < a['n'] or not 1 <= b[4] <= b[3] <= a['U'] for b in blocks): raise ValueError('candidate shape')
        if (len({tuple(b[:3]) for b in blocks}) != len(blocks) or sum(b[4] for b in blocks) != a['U']
                or blocks != sorted(blocks,key=lambda b:(-b[3],*b[:3]))
                or orders['sha256'] != hashed({'state_hash':a['state_hash'],'policy':POLICY,'blocks':blocks})): raise ValueError('candidate identity/order')
        cursor = 0
        for r in current_records:
            if (cursor >= len(blocks) or r['cursor'] != cursor or r['rows'] != blocks[cursor][:3]
                    or r['order_hash'] != orders['sha256'] or r['outcome'] == 'accepted'): raise ValueError('current coverage ledger')
            if r['outcome'] == 'complete': cursor += 1
        if cursor != a['cursor'] or cursor > len(blocks): raise ValueError('coverage prefix')
    if type(a['status']) is not str or len(a['status']) > 128: raise ValueError('status')
    header = {k:v for k,v in a.items() if k not in ('points','orders','attempts','artifacts')}
    if len(compact(header)) > 65536 or len(compact(a['points'])) > 4096: raise ValueError('header/point cap')
    return a


def authority_bytes(a):
    validate_authority(a)
    raw = compact({'payload':a, 'payload_sha256':hashed(a)})
    if len(raw) > CAP: raise ValueError('authority byte cap')
    return raw


def inspect_recovery(raw, artifact_reader=None, check=lambda:None, geometry=True):
    """Synthetic inspection only. No CLI recovery or orphan discovery."""
    if len(raw) > CAP: raise ValueError('authority byte cap')
    value = json.loads(raw)
    if set(value) != {'payload','payload_sha256'} or value['payload_sha256'] != hashed(value['payload']): raise ValueError('payload hash')
    a = validate_authority(value['payload'])
    if geometry:
        points,index,score = kernel.build_index(a['points'],a['n'],check)
        if score != a['U']: raise ValueError('authority raw score')
        if a['orders'] is not None and a['orders'] != make_orders(points,index,a['n'],a['state_hash'],check): raise ValueError('authority candidate reconstruction')
    if artifact_reader is not None:
        for ref in a['artifacts']+([] if a['witness'] is None else [a['witness']]):
            check(); blob = artifact_reader(ref['path'])
            if len(blob) != ref['bytes'] or len(blob) > 16384 or hashlib.sha256(blob).hexdigest() != ref['sha256']: raise ValueError('referenced artifact identity')
    return clone(a)


def plan_start(a):
    validate_authority(a)
    if a['status'] != 'active' or a['pending'] is not None or a['orders'] is None: raise ValueError('start state')
    if a['counters']['started'] >= MAX_STARTS: raise SearchStop('block_cap')
    if a['cursor'] >= len(a['orders']['blocks']): raise SearchStop('restricted_candidate_list_exhausted')
    p = clone(a); seq = len(p['attempts'])+1
    p['attempts'].append({'seq':seq,'rows':p['orders']['blocks'][p['cursor']][:3], 'state_hash':p['state_hash'],
                          'order_hash':p['orders']['sha256'],'cursor':p['cursor'],'before_score':p['U'],'outcome':'pending'})
    p['pending'] = seq; p['counters']['started'] += 1
    return validate_authority(p)


def result_item(result): return [result['score'],result['X'],result['Y'],result['Z']]


def finish_record(a, result, accepted):
    if a['pending'] is None or result.get('optimum_established') is not True: raise ValueError('unfinished result')
    if result['zero'] is not (result['score'] == 0) or (result['score'] > 0 and not result['enumeration_exhausted']): raise ValueError('partial positive result')
    p = clone(a); r = p['attempts'][-1]
    r.update(outcome='accepted' if accepted else 'complete', minimum=clone(result_item(result)),
             optimum_established=True, enumeration_exhausted=result['enumeration_exhausted'], domains=clone(result['domains']),
             after_hash=kernel.normalized_sha256(a['n'],result['points']))
    p['pending'] = None; p['counters']['completed'] += 1
    return p


def plan_nonimprovement(a, result):
    if result['score'] != a['U'] or result['zero'] or kernel.validate_points(result['points'],a['n']) != kernel.validate_points(a['points'],a['n']):
        # A tied lexical minimizer can change coordinates. It is not adopted;
        # only the score and exact completed neighborhood certify this prefix.
        if result['score'] != a['U'] or result['zero']: raise ValueError('nonimprovement score')
    p = finish_record(a,result,False); p['attempts'][-1]['after_hash'] = a['state_hash']; p['cursor'] += 1
    return validate_authority(p)


def prepare_accept(a, result, rebuilt=None):
    if not 0 <= result['score'] < a['U']: raise ValueError('strict result')
    points = kernel.validate_points(result['points'],a['n']); rows = a['attempts'][-1]['rows']
    before = kernel.validate_points(a['points'],a['n'])
    if tuple(p for p in points if p[1] not in rows) != tuple(p for p in before if p[1] not in rows): raise ValueError('unselected row change')
    if tuple(tuple(x for x,y in points if y == row) for row in rows) != tuple(tuple(result[k]) for k in ('X','Y','Z')): raise ValueError('result assignment points')
    if result['score'] and (rebuilt is None or rebuilt[0] != points or rebuilt[2] != result['score']): raise ValueError('positive rebuild')
    p = finish_record(a,result,True); p['counters']['accepted'] += 1; p['generation'] += 1
    state_hash = kernel.normalized_sha256(a['n'],points)
    move = {'schema':'restricted-three-row-move-v1','n':a['n'],'points':points,'score':result['score'], 'before_score':a['U'],
            'before_hash':a['state_hash'],'state_hash':state_hash,'generation':p['generation'],'attempt':a['pending'],
            'rows':rows,'minimum':clone(result_item(result)),'domains':clone(result['domains']), 'counters':p['counters'],
            'old_order_hash':a['orders']['sha256'],'old_cursor':a['cursor'], 'optimum_established':True,
            'enumeration_exhausted':result['enumeration_exhausted']}
    if len(compact(move)) > 16384: raise ValueError('move byte cap')
    p.update(points=clone(points),U=result['score'],state_hash=state_hash,orders=None,cursor=0,status='active' if result['score'] else 'zero')
    return move,p


def build(points, n, check, work):
    if work.get('indexes_started',0) >= MAX_INDEX_ATTEMPTS: raise ValueError('index-build attempt cap')
    return kernel.build_index(points,n,check,work)


def drive(authority, *, check=lambda:None, publish=lambda a,tag:None, save_move=None, save_zero=None,
          observe=lambda e:None, stop_after=None, prepared=None, work=None):
    """Separate three-row controller. Synthetic split API never retries pending."""
    a = clone(validate_authority(authority)); work = {} if work is None else work
    decisions = 0; status = a['status']; error = None; attempted_charge = None
    start_publication_pending = zero_publication_pending = False
    def persist(p, tag):
        if tag not in ('start','accept_zero'): check()
        authority_bytes(p); publish(p,tag)
    try:
        if a['pending'] is not None: raise ValueError('pending authority cannot resume')
        if stop_after == 0: return {'authority':a,'status':'split','decisions':0,'error':None,'attempted_charge':None}
        if a['status'] != 'active': return {'authority':a,'status':a['status'],'decisions':0,'error':None,'attempted_charge':None}
        state = build(a['points'],a['n'],check,work) if prepared is None else prepared
        if state[2] != a['U'] or kernel.normalized_sha256(a['n'],state[0]) != a['state_hash']: raise ValueError('prepared geometry identity')
        while a['status'] == 'active':
            check()
            if a['counters']['started'] >= MAX_STARTS: status = 'block_cap'; break
            if a['orders'] is None: a['orders'] = make_orders(*state[:2],a['n'],a['state_hash'],check,work)
            if a['cursor'] == len(a['orders']['blocks']): status = 'restricted_candidate_list_exhausted'; break
            p = plan_start(a); attempted_charge = clone(p['counters']); start_publication_pending = True
            # No new deadline check between charging and mandatory publication.
            persist(p,'start'); a = p; start_publication_pending = False
            rows = a['attempts'][-1]['rows']; result = block_optimum(*state[:2],a['n'],rows,check,work)
            if result['zero']:
                points = kernel.validate_points(result['points'],a['n'])
                if save_zero is None: raise ValueError('zero callback required')
                ref = save_zero(points)
                if ref is None: status = 'zero_unverified'; break
                zero_publication_pending = True
                move,p = prepare_accept(a,result); p['witness'] = ref
                if save_move is None: raise ValueError('move callback required')
                p['artifacts'].append(save_move(move)); persist(p,'accept_zero'); a = p
                zero_publication_pending = False; decisions += 1
                observe({'rows':rows,'minimum':clone(result_item(result)),'strict':True,'before_hash':move['before_hash']})
                status = 'zero'; break
            strict = result['score'] < a['U']; event = {'rows':rows,'minimum':clone(result_item(result)),'strict':strict,'before_hash':a['state_hash']}
            if strict:
                rebuilt = build(result['points'],a['n'],check,work)
                move,p = prepare_accept(a,result,rebuilt)
                if save_move is None: raise ValueError('move callback required')
                p['artifacts'].append(save_move(move)); persist(p,'accept'); a = p; state = rebuilt
                # Rankings remain absent until the next allowed start is needed.
            else:
                p = plan_nonimprovement(a,result); persist(p,'complete'); a = p
            decisions += 1; observe(event)
            if stop_after is not None and decisions >= stop_after: status = 'split'; break
    except SearchStop as exc:
        if start_publication_pending:
            status = 'error'; error = 'start publication interrupted with unresolved charge: '+str(exc)
        elif zero_publication_pending:
            status = 'error'; error = 'saved witness lacks durable zero authority: '+str(exc)
        else: status = str(exc)
    except Exception as exc: status = 'error'; error = f'{type(exc).__name__}: {str(exc)[:1000]}'
    return {'authority':a,'status':status,'decisions':decisions,'error':error,'attempted_charge':attempted_charge}


class FileStore:
    def __init__(self, out):
        self.out = Path(out); self.publications = 0; self.last_durable = None; self.uncertain = False
    def publish(self, a, tag):
        if self.uncertain: raise ValueError('uncertain authority publication')
        if self.publications >= MAX_PUBLICATIONS: raise ValueError('authority publication cap')
        self.publications += 1
        try: atomic_file(self.out/'authority.json',authority_bytes(a))
        except Exception:
            self.uncertain = True; raise
        self.last_durable = clone(a)
    def save_move(self, move):
        return json_file(self.out/f"move-{move['generation']:03d}-attempt-{move['attempt']:03d}.json",move,cap=16384,immutable=True)


def run(out, manifest, seconds=25, *, started=None, clock=time.monotonic):
    """Future owned allocation only. Not invoked by SOURCE/TINY evidence."""
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 2 < seconds <= 25: raise ValueError('duration')
    start = clock() if started is None else started; soft = start+seconds; search = soft-2
    def final_check():
        if clock() >= soft: raise TimeoutError('main soft deadline')
    def search_check():
        if clock() >= search: raise SearchStop('search_deadline')
    out = Path(out); store = FileStore(out); pins = {}; ready = False; result = None; input_info = None
    report = {'method':'fixed65_restricted_three_row75','accepted':False,'identity_valid':False,'closure':False,
              'n':75,'k':149,'status':'incomplete','soft_seconds':seconds,'search_seconds':seconds-2,'block_cap':MAX_STARTS,
              'witness_saved':False,'work':{},'scope':'One induced K>0 four-column three-row allocation; no automatic continuation or exclusion claim.'}
    def verify_pins():
        for name,sha in pins.items():
            if digest(name,final_check) != sha: raise ValueError('pin drift: '+name)
    def save_zero(points): return preserve_zero(points,75,out,final_check,report)
    try:
        final_check(); path = Path(manifest).resolve()
        if path.stat().st_size > 2*CAP: raise ValueError('manifest byte cap')
        raw = path.read_bytes(); pins = kernel.norm_pins(json.loads(raw)); runtime = str(Path(sys.executable).resolve())
        required = {str(Path(__file__).resolve()),str(Path(kernel.__file__).resolve()),str(Path(shared.__file__).resolve()),
                    str(ROOT/'src/verify.py'),runtime,str(ROOT/HANDOFF_PATH)}
        if (not required <= pins.keys() or pins[str(Path(kernel.__file__).resolve())] != KERNEL_SHA
                or pins[str(Path(shared.__file__).resolve())] != SUFFIX_SHA): raise ValueError('mandatory helper/runtime pins')
        if str(path) in pins: raise ValueError('manifest self entry')
        pins[str(path)] = hashlib.sha256(raw).hexdigest(); verify_pins(); ready = True
        points,input_info = load_handoff(pins,final_check)
        prepared = build(points,75,search_check,report['work'])
        if prepared[2] != 65: raise ValueError('initial index must recount65')
        a = new_authority(points,75,prepared=prepared,check=search_check,work=report['work'])
        final_check(); store.publish(a,'initialize')
        json_file(out/'initial.json',{'n':75,'points':points,'score':65,'state_hash':FIXED_STATE,
                  'counters':a['counters'],'order_sha256':a['orders']['sha256'],'handoff':input_info},cap=16384,immutable=True)
        result = drive(a,check=search_check,publish=store.publish,save_move=store.save_move,save_zero=save_zero,prepared=prepared,work=report['work'])
        report['status'] = result['status']
        if result['error']: report['search_error'] = result['error']
        if result.get('attempted_charge'): report['last_attempted_charge'] = result['attempted_charge']
        if not store.uncertain:
            final = clone(result['authority']); final['status'] = result['status']; store.publish(final,'final_stop')
    except Exception as exc: report.update(status='error',error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(authority_publications=store.publications,authority_uncertain=store.uncertain)
    if store.last_durable is not None:
        a = store.last_durable
        report['state'] = {k:a[k] for k in ('n','U','state_hash','generation','counters','cursor','pending','status')}
        report.update(artifacts=a['artifacts'],attempts=a['attempts'],order_sha256=None if a['orders'] is None else a['orders']['sha256'])
        try:
            report['authority_sha256'] = digest(out/'authority.json',final_check)
            report['authority_bytes'] = (out/'authority.json').stat().st_size
        except Exception as exc: report['authority_identity_error'] = f'{type(exc).__name__}: {str(exc)[:1000]}'
    try:
        if not ready or store.last_durable is None or store.uncertain: raise ValueError('no unambiguous durable authority')
        verify_pins(); final_check(); report['identity_valid'] = True
        allowed = ('block_cap','restricted_candidate_list_exhausted','search_deadline','zero')
        errors = any(key == 'error' or key.endswith('_error') for key in report)
        report['accepted'] = (report['status'] in allowed and not errors
                and report['work'].get('indexes_started',0) <= MAX_INDEX_ATTEMPTS
                and (store.last_durable['U'] > 0 or report['witness_saved'])
                and (result is None or result.get('attempted_charge') is None or all(
                    store.last_durable['counters'][k] >= result['attempted_charge'][k] for k in ('started','completed','accepted')))
                and (not report['witness_saved'] or (store.last_durable['U'] == 0 and store.last_durable['witness'] == report.get('witness'))))
    except Exception as exc: report.update(accepted=False,identity_valid=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(pins=pins,handoff=input_info,elapsed_seconds=clock()-start)
    try: json_file(out/'report.json',report); final_check()
    except Exception as exc:
        report.update(accepted=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}',elapsed_seconds=clock()-start)
        json_file(out/'report.json',report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True); parser.add_argument('--source-pins',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25); args = parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    report = run(args.output_dir,args.source_pins,args.seconds,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('status','accepted','witness_saved','state','authority_publications','elapsed_seconds')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__ == '__main__': sys.exit(main())
