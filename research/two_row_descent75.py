"""Fixed audited-best97 handoff, deterministic exact raw row/two-row descent.

No resume, alternate input, RNG or weight policy. Actual CLI execution needs a
separately allocated 25-soft/30-owned/256-MiB gate. Pure helpers support tiny QA.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce, normalized_sha256

N = 75
ROW_CAP = 512
PAIR_CAP = 32
REPORT_CAP = 1024*1024
HANDOFF_PATH = 'data/two-row-descent75-input-identities.json'
HANDOFF_SHA = 'e1941ac155bfb723d22835ced79c731644bb3ec426b5df3046c091585300431a'
BEST_NORMALIZED = '4312bb212dd558efd0f6eb573baa40f3ad19de2b1537e11e7be734fb14b4f168'


class SearchStop(Exception):
    pass


def choose2(t): return t*(t-1)//2

def choose3(t): return t*(t-1)*(t-2)//6


def phase(work, name, check):
    work['phase'] = name
    check()


def inc(work, name, amount=1):
    work[name] = work.get(name, 0)+amount


def validate_points(values, n):
    if type(n) is not int or not 2 <= n <= N:
        raise ValueError('grid order')
    points = []
    for p in values:
        if not isinstance(p, (tuple, list)) or len(p) != 2 or any(type(v) is not int or not 0 <= v < n for v in p):
            raise ValueError('coordinate domain')
        points.append(tuple(p))
    points = tuple(sorted(points))
    if len(points) != 2*n-1 or len(set(points)) != len(points):
        raise ValueError('cardinality/duplicates')
    rows = Counter(y for x,y in points)
    if sorted(rows.get(r,0) for r in range(n)) != [1]+[2]*(n-1):
        raise ValueError('row capacity/deficiency')
    return points


def line_key(p, q):
    a,b = q[1]-p[1], p[0]-q[0]
    g = math.gcd(abs(a),abs(b))
    if not g: raise ValueError('distinct pair required')
    a //= g; b //= g
    if a < 0 or (a == 0 and b < 0): a,b = -a,-b
    return a,b,a*p[0]+b*p[1]


def build_index(points, n, check=lambda:None, work=None):
    work = {} if work is None else work
    phase(work,'index_build',check); inc(work,'indexes_started')
    points = validate_points(points,n); index = {}
    for i,j in combinations(range(len(points)),2):
        check(); inc(work,'index_pairs')
        key = line_key(points[i],points[j])
        index[key] = index.get(key,0) | (1 << i) | (1 << j)
    score = 0
    for mask in index.values():
        check(); score += choose3(mask.bit_count())
    inc(work,'indexes_completed')
    return points,index,score


def priorities(points, index, n, check=lambda:None, work=None):
    work = {} if work is None else work
    phase(work,'priorities',check); incidence = [0]*n
    joint = dict.fromkeys(combinations(range(n),2),0)
    for mask in index.values():
        check(); t = mask.bit_count()
        if t < 3: continue
        rows = [p[1] for i,p in enumerate(points) if mask & (1 << i)]
        if len(rows) != len(set(rows)): raise ValueError('horizontal violation under row capacity')
        for r in rows:
            check(); incidence[r] += choose2(t-1)
        for r,s in combinations(sorted(rows),2):
            check(); inc(work,'priority_pair_visits'); joint[r,s] += t-2
    removed = {}
    for r,s in joint:
        check(); removed[r,s] = incidence[r]+incidence[s]-joint[r,s]
    rows = tuple(sorted((r for r in range(n) if incidence[r]),key=lambda r:(-incidence[r],r)))
    pairs = tuple(sorted((p for p,v in removed.items() if v),key=lambda p:(-removed[p],*p)))
    return {'I':tuple(incidence),'J':joint,'M':removed,'rows':rows,'pairs':pairs}


def retained_tables(points, index, n, rows, check, work):
    maskout = sum(1 << i for i,p in enumerate(points) if p[1] in rows)
    costs = [[0]*n for r in rows]; base = 0
    phase(work,'retained_lines',check)
    for (a,b,c),mask in index.items():
        check(); inc(work,'retained_line_visits'); t = (mask & ~maskout).bit_count()
        base += choose3(t)
        if t < 2 or a == 0: continue
        for row,unary in zip(rows,costs):
            num = c-b*row
            if num % a == 0 and 0 <= num//a < n: unary[num//a] += choose2(t)
    retained = tuple(p for p in points if p[1] not in rows)
    return retained,base,costs


def row_optimum(points, index, n, row, check=lambda:None, work=None):
    work = {} if work is None else work
    if type(row) is not int or not 0 <= row < n: raise ValueError('row')
    retained,base,costs = retained_tables(points,index,n,(row,),check,work)
    load = len(points)-len(retained)
    best = None; complete = True
    phase(work,'row_choices',check)
    for cols in combinations(range(n),load):
        check(); inc(work,'row_choices')
        item = base+sum(costs[0][x] for x in cols),cols
        if best is None or item < best: best = item
        if item[0] == 0:
            complete = False; break
    changed = tuple(sorted(retained+tuple((x,row) for x in best[1])))
    return {'score':best[0],'columns':best[1],'points':changed,'zero':best[0]==0,'enumeration_complete':complete}


def pair_tables(points, index, n, r, s, check=lambda:None, work=None):
    work = {} if work is None else work
    if type(r) is not int or type(s) is not int or not 0 <= r < s < n: raise ValueError('row pair')
    retained,base,costs = retained_tables(points,index,n,(r,s),check,work)
    cross = bytearray(n*n)
    phase(work,'cross_table',check)
    for x in range(n):
        for qx,qy in retained:
            check(); inc(work,'cross_attempts'); den = qy-r
            num = x*den+(qx-x)*(s-r)
            if num % den == 0:
                y = num//den
                if 0 <= y < n:
                    cell = x*n+y; cross[cell] += 1
                    if cross[cell] > len(retained): raise ValueError('cross bound')
    return {'retained':retained,'retained_score':base,'u':tuple(costs[0]),'v':tuple(costs[1]),'cross':cross}


def outer_sets(n, total):
    if total not in (3,4): raise ValueError('pair total')
    for x in range(n):
        if total == 3: yield (x,)
        for y in range(x+1,n): yield x,y


def best_partner(costs, b, check=lambda:None, work=None):
    work = {} if work is None else work
    if b not in (1,2): raise ValueError('partner load')
    first = second = None
    for y,cost in enumerate(costs):
        check(); inc(work,'partner_visits'); item = cost,y
        if first is None or item < first: first,second = item,first
        elif second is None or item < second: second = item
    selected = (first,) if b == 1 else (first,second)
    return sum(p[0] for p in selected),tuple(sorted(p[1] for p in selected))


def pair_optimum(points, index, n, r, s, check=lambda:None, work=None):
    work = {} if work is None else work
    t = pair_tables(points,index,n,r,s,check,work)
    total = len(points)-len(t['retained']); best = None; complete = True
    phase(work,'pair_choices',check)
    for X in outer_sets(n,total):
        check(); inc(work,'outer_choices')
        adjusted = (t['v'][y]+sum(t['cross'][x*n+y] for x in X) for y in range(n))
        cost,Y = best_partner(adjusted,total-len(X),check,work)
        item = t['retained_score']+sum(t['u'][x] for x in X)+cost,X,Y
        if best is None or item < best: best = item
        if item[0] == 0:
            complete = False; break
    changed = tuple(sorted(t['retained']+tuple((x,r) for x in best[1])+tuple((y,s) for y in best[2])))
    return {'score':best[0],'X':best[1],'Y':best[2],'points':changed,'zero':best[0]==0,'enumeration_complete':complete}


def descend(points, n, row_cap=ROW_CAP, pair_cap=PAIR_CAP, check=lambda:None,
            commit=lambda event:None, observe=lambda event:None, work=None):
    """Last complete positive boundary survives interruption; exact zero skips rebuild."""
    if any(type(v) is not int or v < 0 for v in (row_cap,pair_cap)) or row_cap > ROW_CAP or pair_cap > PAIR_CAP:
        raise ValueError('started caps')
    work = {} if work is None else work
    state = {'points':validate_points(points,n),'index':None,'U':None,'row_started':0,'pair_started':0,
             'row_completed':0,'pair_completed':0,'accepted':0,'status':'incomplete',
             'row_sweep_complete':False,'pair_scan_complete':False}
    try:
        current,index,score = build_index(points,n,check,work)
        state.update(points=current,index=index,U=score)
        while score:
            state.update(row_sweep_complete=False,pair_scan_complete=False)
            ranks = priorities(current,index,n,check,work); improved = False
            for kind,choices,cap in (('row',ranks['rows'],row_cap),('pair',ranks['pairs'],pair_cap)):
                if kind == 'pair': state['row_sweep_complete'] = True
                for choice in choices:
                    if state[kind+'_started'] >= cap:
                        state['status'] = kind+'_cap'; return state
                    state[kind+'_started'] += 1
                    result = (row_optimum(current,index,n,choice,check,work) if kind == 'row'
                              else pair_optimum(current,index,n,*choice,check,work))
                    state[kind+'_completed'] += 1
                    item = (result['score'],result['columns']) if kind == 'row' else (result['score'],result['X'],result['Y'])
                    strict = result['score'] < score
                    if not result['zero']: observe((kind,choice,item,strict))
                    if not strict: continue
                    event = {'kind':kind,'rows':(choice,) if kind == 'row' else choice,'before_score':score,
                             'score':result['score'],'before_points':current,'points':result['points'],
                             'row_started':state['row_started'],'pair_started':state['pair_started'],
                             'row_completed':state['row_completed'],'pair_completed':state['pair_completed'],
                             'row_sweep_complete':state['row_sweep_complete'],'pair_scan_complete':False,
                             'enumeration_complete':result['enumeration_complete']}
                    if result['zero']:
                        # Exact nonnegative objective, lex-first zero: no optional check/index before callback.
                        current = validate_points(result['points'],n); score = 0; index = None
                        state.update(points=current,index=None,U=0,accepted=state['accepted']+1,status='zero',
                                     row_sweep_complete=False,pair_scan_complete=False)
                        commit(event)
                        observe((kind,choice,item,strict))
                        return state
                    changed,pending,actual = build_index(result['points'],n,check,work)
                    if actual != result['score'] or not actual < score: raise ValueError('rebuilt strict raw score')
                    phase(work,'precommit',check)
                    current,index,score = changed,pending,actual
                    state.update(points=current,index=index,U=score,accepted=state['accepted']+1,
                                 row_sweep_complete=False,pair_scan_complete=False)
                    commit(event); improved = True; break
                if improved: break
            if not improved:
                state.update(status='no_strict_descent',row_sweep_complete=True,pair_scan_complete=True)
                return state
        state['status'] = 'zero'; return state
    except SearchStop as error:
        state['status'] = str(error)
        return state
    except Exception as error:
        state.update(status='error',error=f'{type(error).__name__}: {str(error)[:1000]}')
        return state


def compact(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


def digest(path, check=lambda:None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); block = stream.read(65536)
            if not block: return h.hexdigest()
            h.update(block)


def norm_pins(mapping):
    if type(mapping) is not dict or not 1 <= len(mapping) <= 512: raise ValueError('pin mapping')
    pins = {}
    for name,sha in mapping.items():
        if type(name) is not str or type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('pin schema')
        path = str((ROOT/name).resolve())
        if path in pins: raise ValueError('duplicate normalized pin')
        pins[path] = sha
    return pins


def atomic_bytes(path, raw):
    fd,name = tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name,path)
    finally: Path(name).unlink(missing_ok=True)


def save_json(path, value, cap=REPORT_CAP):
    raw = compact(value)
    if len(raw) > cap: raise ValueError('JSON output cap')
    atomic_bytes(path,raw)
    return hashlib.sha256(raw).hexdigest(),len(raw)


def dual_validate(points, n, score, check):
    candidate = {'n':n,'points':list(points),'claimed_conflict_count':score,'novelty_claimed':False,
                 'axis_counts':{'rows':[sum(y==r for x,y in points) for r in range(n)],
                                'columns':[sum(x==c for x,y in points) for c in range(n)]}}
    check(); first = verify_certificate(candidate)
    check(); second = verify_certificate_bruteforce(candidate)
    if not (first['point_count'] == second['point_count'] == len(points)
            and first['n'] == second['n'] == n
            and first['normalized_sha256'] == second['normalized_sha256'] == normalized_sha256(n,points)
            and first['conflict_count'] == second['conflict_count'] == score
            and first['conflicts'] == second['conflicts']
            and first['valid'] is second['valid'] is (score == 0)
            and not first['errors'] and not second['errors']): raise ValueError('dual validator disagreement')
    # Deliberately no time check after validator two: caller saves immediately.
    summaries = [{k:v for k,v in val.items() if k != 'conflicts'} for val in (first,second)]
    return {'certificate':candidate,'validators':summaries,
            'conflicts_sha256':hashlib.sha256(compact(first['conflicts'])).hexdigest()}


def clean_guard(gate, seconds):
    ints = ('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')
    if type(gate) is not dict or any(type(gate.get(k)) is not int for k in ints): raise ValueError('guard schema')
    elapsed = gate.get('elapsed_seconds')
    if (gate.get('gate_status') != 'exited' or gate['returncode'] != 0 or gate.get('cleanup_status') != 'clean'
            or gate.get('cleanup_error') is not None or gate.get('monitor_error') is not None
            or gate.get('trigger_gate_status') is not None or gate['seconds_limit'] != seconds
            or gate['rss_limit_mib'] != 256 or not 0 < gate['peak_sampled_rss_kib'] <= 256*1024
            or gate['rss_samples'] < 1 or gate['cleanup_samples'] < 1
            or type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0 < elapsed < seconds):
        raise ValueError('unclean guard')


def authenticate_chain(documents, handoff, pins, check=lambda:None):
    """Metadata/schema checks before best coordinates may enter geometry.

    Documents are already byte-authenticated snapshots; this helper is exposed
    for synthetic schema QA. It neither imports old policy nor runs old search.
    """
    required = {'schema','artifacts','best_normalized_sha256','n','point_count','unweighted_score','scope'}
    if (type(handoff) is not dict or set(handoff) != required
            or handoff['schema'] != 'two-row-fixed-handoff-identities-v1' or handoff['n'] != N
            or handoff['point_count'] != 149 or handoff['unweighted_score'] != 97
            or handoff['best_normalized_sha256'] != BEST_NORMALIZED): raise ValueError('handoff metadata')
    def doc(name):
        check(); value = documents[name]
        if type(value) is not dict: raise ValueError('document schema')
        return value
    report_name = 'data/row-block-breakout75-v1/report.json'
    receipt_name = 'data/experiments/shepherd-row-block-breakout75-v1.json'
    manifest_name = 'data/row-block-breakout75-source-pins.json'
    checkpoint_name = 'data/row-block-breakout75-v1/completed-boundary.json'
    report = doc(report_name); receipt = doc(receipt_name); old_sources = doc(manifest_name)
    checkpoint = doc(checkpoint_name); best = doc('data/row-block-breakout75-v1/best.json')
    audit = doc('data/row-block-breakout75-independent-actual-audit.json')
    guard = doc('data/row-block-breakout75-independent-actual-audit-owned-guard.json')
    oldpins = norm_pins(old_sources); oldmanifest = str((ROOT/manifest_name).resolve())
    if oldmanifest in oldpins: raise ValueError('parent manifest self pin')
    oldpins[oldmanifest] = handoff['artifacts'][manifest_name]
    if oldpins != norm_pins(report.get('pins')) or oldpins != norm_pins(receipt.get('sources_before')):
        raise ValueError('parent pin set association')
    if any(pins.get(k) != v for k,v in oldpins.items()): raise ValueError('missing inherited pins')
    for name,sha in handoff['artifacts'].items():
        check()
        if pins.get(str((ROOT/name).resolve())) != sha: raise ValueError('missing handoff artifact pin')
    if (report.get('method') != 'from_scratch_row_block_breakout75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('closure') is not False
            or report.get('checkpoint_saved') is not True or report.get('witness_saved') is not False
            or report.get('n') != N or report.get('k') != 149 or report.get('best_unweighted') != 97
            or report.get('checkpoint_sha256') != handoff['artifacts'][checkpoint_name]):
        raise ValueError('parent report association')
    if (receipt.get('status') != 'completed' or receipt.get('sources_unchanged') is not True
            or receipt.get('source_manifest_sha256') != handoff['artifacts'][manifest_name]):
        raise ValueError('parent receipt association')
    expected_argv = [str(ROOT/'.venv/bin/python'),'research/row_block_breakout75.py','--seconds','25',
                     '--output-dir','data/row-block-breakout75-v1','--source-pins',manifest_name]
    if receipt.get('argv') != expected_argv: raise ValueError('parent argv')
    clean_guard(receipt.get('gate'),30)
    elapsed = report.get('elapsed_seconds')
    if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0 <= elapsed < 25:
        raise ValueError('parent soft deadline')
    if type(checkpoint) is not dict or set(checkpoint) != {'metadata','current','best','weights','rng'}:
        raise ValueError('parent checkpoint schema')
    meta = checkpoint['metadata']; identities = meta.get('identities',{})
    if (meta.get('schema') != 'row-block-completed-boundary-v1' or meta.get('best_unweighted') != 97
            or meta.get('best_normalized_sha256') != BEST_NORMALIZED
            or meta.get('validation') != 'invalid_research_state'
            or identities.get('manifest_path') != oldmanifest
            or identities.get('manifest_sha256') != handoff['artifacts'][manifest_name]
            or identities.get('runtime_path') != str(Path(sys.executable).resolve())
            or identities.get('runtime_sha256') != pins.get(str(Path(sys.executable).resolve()))
            or identities.get('python_version') != sys.version
            or identities.get('worker_sha256') != oldpins.get(str(ROOT/'research/row_block_breakout75.py'))
            or identities.get('soft_seconds') != 25 or identities.get('search_seconds') != 23
            or identities.get('owned_seconds') != 30 or identities.get('rss_limit_mib') != 256):
        raise ValueError('parent checkpoint identities')
    if (audit.get('accepted') is not True or audit.get('best_unweighted') != 97
            or audit.get('checkpoint_sha256') != handoff['artifacts'][checkpoint_name]
            or audit.get('report_sha256') != handoff['artifacts'][report_name]
            or audit.get('receipt_sha256') != handoff['artifacts'][receipt_name]
            or audit.get('manifest_sha256') != handoff['artifacts'][manifest_name]
            or audit.get('pins_checked') != len(oldpins)):
        raise ValueError('independent audit association')
    clean_guard(guard,10)
    expected_audit_argv = [str(ROOT/'.venv/bin/python'),'research/row_block_breakout75_actual_audit.py',
                           '--report',report_name,'--receipt',receipt_name,'--manifest',manifest_name,
                           '--manifest-sha256',handoff['artifacts'][manifest_name]]
    if (guard.get('argv') != expected_audit_argv
            or guard.get('audit_helper_sha256') != '006110e8799b5f0a508ee1ee870fd7fd8181690f2c6d9c970d2b354e9c76605a'
            or guard.get('audit_helper_sha256') != pins.get(str(ROOT/'research/row_block_breakout75_actual_audit.py'))):
        raise ValueError('audit helper identity')
    cert = best.get('certificate'); validators = best.get('validators')
    if (best.get('classification') != 'dual_checked_invalid_research_state' or best.get('valid') is not False
            or type(cert) is not dict or cert.get('n') != N or cert.get('claimed_conflict_count') != 97
            or type(validators) is not list or len(validators) != 2): raise ValueError('best diagnostic schema')
    for val,algorithm in zip(validators,('integer_normalized_slopes','integer_cross_products')):
        if (val.get('algorithm') != algorithm or val.get('valid') is not False or val.get('n') != N
                or val.get('point_count') != 149 or val.get('conflict_count') != 97 or val.get('errors') != []
                or val.get('normalized_sha256') != BEST_NORMALIZED): raise ValueError('best validator association')
    # Geometry is permitted only after every byte/schema/chain check above.
    points = validate_points(cert.get('points'),N)
    if validate_points(checkpoint['best'],N) != points or normalized_sha256(N,points) != BEST_NORMALIZED:
        raise ValueError('best coordinate identity')
    axes = {'rows':[sum(y==r for x,y in points) for r in range(N)],
            'columns':[sum(x==c for x,y in points) for c in range(N)]}
    if cert.get('axis_counts') != axes: raise ValueError('best axis metadata')
    return points


def load_handoff(pins, check):
    """Only production path to active coordinates; every artifact hashes first."""
    handoff_path = ROOT/HANDOFF_PATH
    if pins.get(str(handoff_path)) != HANDOFF_SHA or digest(handoff_path,check) != HANDOFF_SHA:
        raise ValueError('fixed handoff identity')
    raw = handoff_path.read_bytes()
    if len(raw) > 16384: raise ValueError('handoff cap')
    handoff = json.loads(raw); artifacts = handoff.get('artifacts')
    if type(artifacts) is not dict or len(artifacts) != 8: raise ValueError('artifact set')
    snapshots = {}
    for name,sha in artifacts.items():
        check(); path = ROOT/name
        if pins.get(str(path.resolve())) != sha or digest(path,check) != sha:
            raise ValueError('handoff byte identity: '+name)
        # Snapshot hash precedes parsing, and caps precede allocation of full JSON.
        if path.stat().st_size > 2*1024*1024: raise ValueError('handoff artifact cap')
        value = path.read_bytes()
        if hashlib.sha256(value).hexdigest() != sha: raise ValueError('handoff snapshot drift')
        snapshots[name] = value
    documents = {name:json.loads(raw) for name,raw in snapshots.items() if name.endswith('.json')}
    cpname = 'data/row-block-breakout75-v1/completed-boundary.json'
    report = documents['data/row-block-breakout75-v1/report.json']
    if report.get('checkpoint_bytes') != len(snapshots[cpname]): raise ValueError('checkpoint byte association')
    points = authenticate_chain(documents,handoff,pins,check)
    validation = dual_validate(points,N,97,check)
    best = documents['data/row-block-breakout75-v1/best.json']
    if (validation['validators'] != best['validators'] or validation['conflicts_sha256'] != best.get('conflicts_sha256')):
        raise ValueError('fresh best recount')
    return points,{'handoff_sha256':HANDOFF_SHA,'normalized_sha256':BEST_NORMALIZED,'score':97,
                   'scope':'Coordinates only; archived weights/RNG/counters are provenance.'}


def run(out, manifest, seconds=25, *, started=None, clock=time.monotonic):
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 2 < seconds <= 25: raise ValueError('duration')
    start = clock() if started is None else started; soft = start+seconds; search = soft-2
    def final_check():
        if clock() >= soft: raise TimeoutError('main soft deadline')
    def search_check():
        if clock() >= search: raise SearchStop('search_deadline')
    report = {'method':'exact_raw_two_row_descent75','status':'incomplete','accepted':False,'identity_valid':False,
              'closure':False,'witness_saved':False,'boundary_saved':False,'improvements':[],'work':{},
              'n':N,'k':149,'row_cap':ROW_CAP,'pair_cap':PAIR_CAP,'soft_seconds':seconds,'search_seconds':seconds-2,
              'scope':'One fixed best97 handoff; strict raw descent only. No global exclusion, resume or automatic continuation.'}
    pins = {}; ready = False; state = None; handoff_info = None; zero_handled = False
    def verify_pins():
        for path,sha in pins.items():
            if digest(path,final_check) != sha: raise ValueError('pin drift: '+path)
    def process_zero(points):
        nonlocal zero_handled
        zero_handled = True
        report['validation'] = 'unverified_zero_candidate'
        try:
            validated = dual_validate(points,N,0,final_check)
            # Nothing optional, including a clock or pin check, intervenes here.
            sha,size = save_json(out/'valid149.json',validated)
            report.update(witness_saved=True,witness_sha256=sha,witness_bytes=size,
                          witness_normalized_sha256=normalized_sha256(N,points),validation='dual_verified_witness')
        except Exception as error:
            report.update(validation='unverified_zero_candidate',validation_error=f'{type(error).__name__}: {str(error)[:1000]}')
        if not report['witness_saved']:
            try:
                save_json(out/'raw-zero.json',{'n':N,'points':points,'score':0,'classification':'unverified_zero_candidate',
                                             'normalized_sha256':normalized_sha256(N,points)})
                report['raw_zero_saved'] = True
            except Exception as error: report['raw_zero_error'] = f'{type(error).__name__}: {str(error)[:1000]}'
    def commit(event):
        if event['score'] == 0: process_zero(event['points'])
        serial = len(report['improvements'])+1
        if serial > 97: raise ValueError('strict improvement ceiling')
        before_hash = normalized_sha256(N,event['before_points']); after_hash = normalized_sha256(N,event['points'])
        record = {k:v for k,v in event.items() if k not in ('before_points','points')}
        record.update(n=N,points=event['points'],before_normalized_sha256=before_hash,normalized_sha256=after_hash)
        path = out/f'improvement-{serial:03d}.json'
        sha,size = save_json(path,record,16384)
        report['improvements'].append({'path':str(path.resolve().relative_to(ROOT)),'sha256':sha,'bytes':size,
                                       'score':event['score'],'before_score':event['before_score'],
                                       'before_normalized_sha256':before_hash,'normalized_sha256':after_hash,
                                       'kind':event['kind'],'rows':event['rows']})
    try:
        final_check(); path = Path(manifest).resolve()
        if path.stat().st_size > 2*1024*1024: raise ValueError('manifest cap')
        raw = path.read_bytes(); pins = norm_pins(json.loads(raw))
        runtime = str(Path(sys.executable).resolve())
        required = {str(Path(__file__).resolve()),str(ROOT/'src/verify.py'),runtime,str(ROOT/HANDOFF_PATH),
                    str(ROOT/'research/row_block_breakout75_actual_audit.py')}
        if not required <= pins.keys(): raise ValueError('mandatory new source/runtime/handoff pins')
        if str(path) in pins: raise ValueError('manifest self entry')
        pins[str(path)] = hashlib.sha256(raw).hexdigest()
        verify_pins(); ready = True
        points,handoff_info = load_handoff(pins,final_check)
        state = {'points':points,'U':97,'accepted':0,'row_started':0,'pair_started':0,
                 'row_completed':0,'pair_completed':0,'row_sweep_complete':False,'pair_scan_complete':False,
                 'status':'search_deadline'}
        save_json(out/'initial.json',{'n':N,'points':points,'score':97,'normalized_sha256':BEST_NORMALIZED,
                                    'classification':'dual_checked_invalid_research_state','handoff':handoff_info})
        result = descend(points,N,check=search_check,commit=commit,work=report['work'])
        if result['U'] is None: result.update(points=points,U=97)
        state = result; report['status'] = result['status']
        if result.get('error'): report['search_error'] = result['error']
    except Exception as error:
        report.update(status='error',error=f'{type(error).__name__}: {str(error)[:1000]}')
    if state is not None:
        if state['U'] == 0 and not zero_handled: process_zero(state['points'])
        if state['U'] > 0:
            report['validation'] = 'invalid_research_state'
            if clock() < soft-0.5:
                try:
                    validated = dual_validate(state['points'],N,state['U'],final_check)
                    validated.update(valid=False,classification='dual_checked_invalid_research_state')
                    save_json(out/'best.json',validated); report['best_diagnostic_saved'] = True
                except Exception as error: report['best_diagnostic_error'] = f'{type(error).__name__}: {str(error)[:1000]}'
        try:
            summary = {k:v for k,v in state.items() if k not in ('points','index','error')}
            boundary = {'schema':'two-row-raw-descent-boundary-v1','n':N,'points':state['points'],
                        'normalized_sha256':normalized_sha256(N,state['points']),'state':summary,'handoff':handoff_info,
                        'validation':report['validation'],'policy':{'row_cap':ROW_CAP,'pair_cap':PAIR_CAP},
                        'improvements':report['improvements']}
            sha,size = save_json(out/'completed-boundary.json',boundary)
            report.update(boundary_saved=True,boundary_sha256=sha,boundary_bytes=size,state=summary,
                          current_unweighted=state['U'],best_unweighted=state['U'])
        except Exception as error: report.update(status='boundary_failure',boundary_error=f'{type(error).__name__}: {str(error)[:1000]}')
    try:
        if not ready or state is None: raise ValueError('initial handoff incomplete')
        verify_pins(); final_check(); report['identity_valid'] = True
        report['accepted'] = (report['boundary_saved'] and report['status'] not in ('error','boundary_failure')
                              and 'search_error' not in report and (state['U'] > 0 or report['witness_saved']))
    except Exception as error:
        report.update(accepted=False,identity_valid=False,final_error=f'{type(error).__name__}: {str(error)[:1000]}')
    report.update(pins=pins,handoff=handoff_info,elapsed_seconds=clock()-start)
    try:
        save_json(out/'report.json',report); final_check()
    except Exception as error:
        report.update(accepted=False,final_error=f'{type(error).__name__}: {str(error)[:1000]}',elapsed_seconds=clock()-start)
        save_json(out/'report.json',report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--source-pins',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    report = run(args.output_dir,args.source_pins,args.seconds,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('status','accepted','witness_saved','boundary_saved','current_unweighted','state','elapsed_seconds')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__ == '__main__': sys.exit(main())
