"""One fixed audited65 suffix allocation; no CLI resume or alternate source.

Only SOURCE/TINY execution is allowed until Root reserves the actual gate.
Historical32 pair prefix is source-supported, not independently certified.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import two_row_descent75 as kernel

KERNEL_SHA = '0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
HANDOFF_PATH = 'data/two-row-suffix75-input-identities.json'
HANDOFF_SHA = 'f966e46cdd62fc22f48e0415a8b851b6f5dc021bd19b798ca3c2e6526cca910e'
FIXED_STATE = '25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c'
POLICY = 'exact-raw-IJ-M-merged-lex-v3'
CAP = 1024*1024
MAX_ATTEMPTS = 268
MAX_PUBLICATIONS = 538
COUNTERS = ('row_started','row_completed','pair_started','pair_completed','accepted')
BASE = dict(row_started=308,row_completed=308,pair_started=32,pair_completed=32,accepted=28)
compact = kernel.compact
digest = kernel.digest
SearchStop = kernel.SearchStop


def clone(value): return json.loads(compact(value))

def hashed(value): return hashlib.sha256(compact(value)).hexdigest()


def make_orders(points,index,n,state_hash,check=lambda:None):
    ranks = kernel.priorities(points,index,n,check)
    value = {'rows':list(ranks['rows']),'pairs':[list(p) for p in ranks['pairs']]}
    return dict(value,sha256=hashed({'state_hash':state_hash,'policy':POLICY,**value}))


def checked_kernel(a,check=lambda:None):
    points,index,score = kernel.build_index(a['points'],a['n'],check)
    if score != a['U'] or kernel.normalized_sha256(a['n'],points) != a['state_hash']:
        raise ValueError('authority geometry identity')
    orders = make_orders(points,index,a['n'],a['state_hash'],check)
    if a['orders'] is not None and a['orders'] != orders: raise ValueError('authority order reconstruction')
    return points,index,score,orders


def new_authority(points,n,*,base=None,row_cap=512,pair_cap=96,pair_prefix=0,row_complete=False,
                  prepared=None,check=lambda:None):
    base = dict.fromkeys(COUNTERS,0) if base is None else dict(base)
    if set(base)!=set(COUNTERS) or any(type(v) is not int or v<0 for v in base.values()): raise ValueError('base counters')
    if any(type(v) is not int or v<0 for v in (row_cap,pair_cap,pair_prefix)) or row_cap>512 or pair_cap>96:
        raise ValueError('caps/prefix')
    points,index,score = kernel.build_index(points,n,check) if prepared is None else prepared
    points = kernel.validate_points(points,n); state_hash = kernel.normalized_sha256(n,points)
    orders = make_orders(points,index,n,state_hash,check)
    if pair_prefix>len(orders['pairs']) or (pair_prefix and not row_complete): raise ValueError('imported prefix')
    a = {'schema':'two-row-suffix-authority-v1','policy':POLICY,'n':n,'points':points,'U':score,'state_hash':state_hash,
         'generation':base['accepted'],'base':base,'counters':dict(base),'caps':{'row':row_cap,'pair':pair_cap},
         'origin':{'state_hash':state_hash,'pair_prefix':pair_prefix,'row_complete':bool(row_complete),
                   'basis':'source_bound_prior_execution_not_independent_minimum_certificate' if row_complete else 'synthetic_fresh'},
         'phase':'pair' if row_complete else 'row','row_cursor':len(orders['rows']) if row_complete else 0,
         'pair_cursor':pair_prefix,'row_sweep_complete':bool(row_complete),'pair_scan_complete':False,
         'orders':orders,'pending':None,'attempts':[],'artifacts':[],'witness':None,'status':'active'}
    if score==0: a.update(status='zero',phase='done')
    validate_authority(a)
    return clone(a)


def validate_authority(a):
    required = {'schema','policy','n','points','U','state_hash','generation','base','counters','caps','origin','phase',
                'row_cursor','pair_cursor','row_sweep_complete','pair_scan_complete','orders','pending','attempts','artifacts','witness','status'}
    if type(a) is not dict or set(a)!=required or a['schema']!='two-row-suffix-authority-v1' or a['policy']!=POLICY:
        raise ValueError('authority schema/policy')
    points = kernel.validate_points(a['points'],a['n'])
    if kernel.normalized_sha256(a['n'],points)!=a['state_hash'] or type(a['U']) is not int or not 0<=a['U']<=kernel.choose3(len(points)):
        raise ValueError('authority points/score')
    if a['phase'] not in ('row','pair','done') or type(a['row_sweep_complete']) is not bool or type(a['pair_scan_complete']) is not bool:
        raise ValueError('authority phase/flags')
    if a['phase']=='pair' and not a['row_sweep_complete']: raise ValueError('pair before row sweep')
    if a['pair_scan_complete'] and not a['row_sweep_complete']: raise ValueError('pair completion flag')
    for mapping in (a['base'],a['counters']):
        if set(mapping)!=set(COUNTERS) or any(type(v) is not int or v<0 for v in mapping.values()): raise ValueError('counter schema')
    caps=a['caps'];c=a['counters'];b=a['base']
    if set(caps)!={'row','pair'} or any(type(v) is not int or v<0 for v in caps.values()) or caps['row']>512 or caps['pair']>96:
        raise ValueError('cap schema')
    for kind,limit in (('row',204),('pair',64)):
        if not b[kind+'_completed']<=b[kind+'_started']<=c[kind+'_started']<=caps[kind] or not b[kind+'_completed']<=c[kind+'_completed']<=c[kind+'_started']:
            raise ValueError('cumulative counters')
        if c[kind+'_started']-b[kind+'_started']>limit: raise ValueError('epoch starts')
    if a['generation']!=c['accepted'] or not b['accepted']<=c['accepted']<=b['accepted']+65: raise ValueError('generation')
    origin=a['origin']
    if (set(origin)!={'state_hash','pair_prefix','row_complete','basis'} or type(origin['pair_prefix']) is not int
            or not 0<=origin['pair_prefix']<=b['pair_completed'] or type(origin['row_complete']) is not bool
            or (origin['pair_prefix'] and not origin['row_complete'])):raise ValueError('origin coverage')
    attempts=a['attempts'];refs=a['artifacts']
    if type(attempts) is not list or len(attempts)>MAX_ATTEMPTS or type(refs) is not list or len(refs)>65: raise ValueError('ledger count')
    counts=dict.fromkeys(COUNTERS,0); pending=[];accepted=0
    for seq,r in enumerate(attempts,1):
        if len(compact(r))>1024 or r.get('seq')!=seq or r.get('kind') not in ('row','pair') or r.get('outcome') not in ('pending','complete','accepted','abandoned'):
            raise ValueError('attempt schema')
        kind=r['kind'];counts[kind+'_started']+=1
        if r['outcome'] in ('complete','accepted'):counts[kind+'_completed']+=1
        if r['outcome']=='accepted':accepted+=1
        if r['outcome']=='pending':pending.append(seq)
    counts['accepted']=accepted
    if any(c[k]!=b[k]+counts[k] for k in COUNTERS):raise ValueError('ledger/counter binding')
    if pending != ([] if a['pending'] is None else [a['pending']]) or (pending and pending[0]!=len(attempts)):
        raise ValueError('pending binding')
    if pending and attempts[-1].get('state_hash')!=a['state_hash']:raise ValueError('pending state identity')
    if len(refs)!=accepted: raise ValueError('accepted artifact count')
    for ref in refs+([] if a['witness'] is None else [a['witness']]):
        if len(compact(ref))>512 or type(ref.get('path')) is not str or len(ref['path'])>256 or type(ref.get('sha256')) is not str or len(ref['sha256'])!=64:
            raise ValueError('artifact reference')
    if any(type(a[k]) is not int or a[k]<0 for k in ('row_cursor','pair_cursor')): raise ValueError('cursor')
    orders=a['orders']
    if orders is None:
        if a['row_cursor'] or a['pair_cursor'] or a['row_sweep_complete'] or a['pair_scan_complete'] or a['pending'] is not None:
            raise ValueError('unmaterialized cursor')
    else:
        if set(orders)!={'rows','pairs','sha256'} or len(orders['rows'])>a['n'] or len(orders['pairs'])>kernel.choose2(a['n']):raise ValueError('order shape')
        value={'state_hash':a['state_hash'],'policy':POLICY,'rows':orders['rows'],'pairs':orders['pairs']}
        if orders['sha256']!=hashed(value):raise ValueError('order hash')
        if len(set(orders['rows']))!=len(orders['rows']) or any(type(r) is not int or not 0<=r<a['n'] for r in orders['rows']):raise ValueError('row order')
        if len(set(map(tuple,orders['pairs'])))!=len(orders['pairs']) or any(len(p)!=2 or any(type(v) is not int for v in p) or not 0<=p[0]<p[1]<a['n'] for p in orders['pairs']):raise ValueError('pair order')
        if a['row_cursor']>len(orders['rows']) or a['pair_cursor']>len(orders['pairs']):raise ValueError('cursor range')
        if a['row_sweep_complete'] and a['row_cursor']!=len(orders['rows']):raise ValueError('row sweep cursor')
        if a['pair_scan_complete'] and a['pair_cursor']!=len(orders['pairs']):raise ValueError('pair scan cursor')
        if any(len(compact(p))>64 for p in orders['pairs']) or any(len(compact(r))>16 for r in orders['rows']):raise ValueError('order entry cap')
        historical=origin['state_hash']==a['state_hash']
        rc=len(orders['rows']) if historical and origin['row_complete'] else 0
        pc=origin['pair_prefix'] if historical else 0
        row_done=historical and origin['row_complete'];pair_done=False
        for record in attempts:
            if record['state_hash']!=a['state_hash']:continue
            kind=record['kind'];cursor=rc if kind=='row' else pc
            values=orders['rows'] if kind=='row' else orders['pairs']
            expected_rows=[values[cursor]] if kind=='row' and cursor<len(values) else (values[cursor] if cursor<len(values) else None)
            if (record['order_hash']!=orders['sha256'] or record['cursor']!=cursor or record['rows']!=expected_rows
                    or (kind=='row' and row_done) or (kind=='pair' and not row_done) or record['outcome']=='accepted'):
                raise ValueError('current-state coverage ledger')
            if record['outcome']=='complete':
                if kind=='row':rc+=1;row_done=rc==len(orders['rows'])
                else:pc+=1;pair_done=pc==len(orders['pairs'])
        if (a['row_cursor'],a['pair_cursor'],a['row_sweep_complete'],a['pair_scan_complete'])!=(rc,pc,row_done,pair_done):
            raise ValueError('cursor/ledger mismatch')
        expected_phase='done' if pair_done or a['U']==0 else ('pair' if row_done else 'row')
        if a['phase']!=expected_phase:raise ValueError('phase/coverage mismatch')
    if len(compact(a['points']))>4096:raise ValueError('point cap')
    header={k:v for k,v in a.items() if k not in ('points','attempts','artifacts','orders')}
    if len(compact(header))>65536:raise ValueError('header cap')
    return a


def authority_bytes(a):
    validate_authority(a)
    payload=compact(a);raw=compact({'payload':a,'payload_sha256':hashlib.sha256(payload).hexdigest()})
    if len(raw)>CAP:raise ValueError('authority byte cap')
    return raw


def inspect_recovery(raw,artifact_reader=None,check=lambda:None,geometry=True):
    if len(raw)>CAP:raise ValueError('authority byte cap')
    value=json.loads(raw)
    if set(value)!={'payload','payload_sha256'} or value['payload_sha256']!=hashed(value['payload']):raise ValueError('authority payload hash')
    a=validate_authority(value['payload'])
    if geometry:checked_kernel(a,check)
    if artifact_reader is not None:
        for ref in a['artifacts']+([] if a['witness'] is None else [a['witness']]):
            check();blob=artifact_reader(ref['path'])
            if len(blob)>16384 or hashlib.sha256(blob).hexdigest()!=ref['sha256']:raise ValueError('referenced artifact identity')
    # Pending remains charged/uncovered; no automatic retry or orphan discovery.
    return clone(a)


def plan_start(a):
    validate_authority(a)
    if a['status']!='active' or a['pending'] is not None or a['orders'] is None:raise ValueError('start state')
    kind=a['phase'];cursor=a[kind+'_cursor'];orders=a['orders'][kind+'s' if kind=='row' else 'pairs']
    if kind not in ('row','pair') or cursor>=len(orders):raise ValueError('start order')
    if a['counters'][kind+'_started']>=a['caps'][kind] or a['counters'][kind+'_started']-a['base'][kind+'_started']>=(204 if kind=='row' else 64):
        raise SearchStop(kind+'_cap')
    if len(a['attempts'])>=MAX_ATTEMPTS:raise SearchStop('attempt_cap')
    p=clone(a);seq=len(p['attempts'])+1
    rows=[orders[cursor]] if kind=='row' else orders[cursor]
    record={'seq':seq,'kind':kind,'rows':rows,'state_hash':a['state_hash'],'order_hash':a['orders']['sha256'],
            'cursor':cursor,'outcome':'pending','before_score':a['U']}
    p['attempts'].append(record);p['pending']=seq;p['counters'][kind+'_started']+=1
    validate_authority(p);return p


def result_item(a,result):
    record=a['attempts'][a['pending']-1]
    return ([result['score'],result['columns']] if record['kind']=='row' else [result['score'],result['X'],result['Y']])


def finish_record(a,result,accepted):
    p=clone(a);r=p['attempts'][p['pending']-1];kind=r['kind']
    r.update(outcome='accepted' if accepted else 'complete',minimum=result_item(a,result),
             enumeration_complete=result['enumeration_complete'])
    p['pending']=None;p['counters'][kind+'_completed']+=1
    return p


def plan_nonimprovement(a,result):
    if a['pending'] is None or result['score']!=a['U'] or result['zero']:raise ValueError('nonimprovement result')
    p=finish_record(a,result,False);kind=a['phase'];p[kind+'_cursor']+=1
    if kind=='row' and p['row_cursor']==len(p['orders']['rows']):p.update(phase='pair',row_sweep_complete=True)
    if kind=='pair' and p['pair_cursor']==len(p['orders']['pairs']):p.update(phase='done',pair_scan_complete=True,status='no_strict_descent')
    validate_authority(p);return p


def prepare_accept(a,result,rebuilt=None):
    if a['pending'] is None or not 0<=result['score']<a['U']:raise ValueError('strict result')
    points=kernel.validate_points(result['points'],a['n'])
    rows=a['attempts'][-1]['rows'];before=tuple(map(tuple,a['points']))
    if tuple(p for p in points if p[1] not in rows)!=tuple(p for p in before if p[1] not in rows):raise ValueError('unselected row change')
    if result['score'] and (rebuilt is None or rebuilt[0]!=points or rebuilt[2]!=result['score']):raise ValueError('positive rebuild')
    p=finish_record(a,result,True);p['counters']['accepted']+=1;p['generation']=p['counters']['accepted']
    state_hash=kernel.normalized_sha256(a['n'],points)
    move={'schema':'two-row-suffix-move-v1','n':a['n'],'points':points,'score':result['score'],'before_score':a['U'],
          'before_hash':a['state_hash'],'state_hash':state_hash,'generation':p['generation'],'attempt':a['pending'],
          'kind':a['phase'],'rows':rows,'minimum':result_item(a,result),'counters':p['counters'],
          'old_row_sweep_complete':a['row_sweep_complete'],'old_pair_cursor':a['pair_cursor'],
          'enumeration_complete':result['enumeration_complete']}
    if len(compact(move))>16384:raise ValueError('move byte cap')
    p.update(points=[list(point) for point in points],U=result['score'],state_hash=state_hash,phase='row' if result['score'] else 'done',
             row_cursor=0,pair_cursor=0,row_sweep_complete=False,pair_scan_complete=False,orders=None,
             status='active' if result['score'] else 'zero')
    # Caller appends immutable artifact reference before serializing/adopting p.
    return move,p


def drive(authority,*,check=lambda:None,publish=lambda a,tag:None,save_move=None,save_zero=None,
          observe=lambda e:None,stop_after=None,prepared=None,work=None):
    """No CLI recovery: pure/injected persistence supports SOURCE/TINY splits."""
    a=clone(validate_authority(authority));work={} if work is None else work
    decisions=0;status=a['status'];error=None;attempted_charge=None;start_publication_pending=False;zero_publication_pending=False
    def persist(next_a,tag):
        # The loop checks before charging. Once charged, start publication is
        # mandatory; a late write leaves a durable pending charge before kernel.
        # A saved zero likewise gets its bounded authority write before reporting.
        if tag not in ('start','accept_zero'):check()
        authority_bytes(next_a)
        publish(next_a,tag)
    try:
        if a['pending'] is not None:raise ValueError('pending authority requires explicit recovery decision')
        if stop_after==0:return {'authority':a,'status':'split','decisions':0,'error':None}
        state=checked_kernel(a,check) if prepared is None else (*prepared,make_orders(prepared[0],prepared[1],a['n'],a['state_hash'],check))
        if (state[2]!=a['U'] or kernel.normalized_sha256(a['n'],state[0])!=a['state_hash']
                or (a['orders'] is not None and a['orders']!=state[3])):raise ValueError('prepared geometry/order identity')
        while a['status']=='active':
            check()
            if a['orders'] is None:
                a['orders']=state[3]
            if a['phase']=='row' and not a['orders']['rows']:
                if a['U']:raise ValueError('positive score without conflict row')
                a.update(status='zero',phase='done');break
            p=plan_start(a)
            attempted_charge=clone(p['counters'])
            start_publication_pending=True
            persist(p,'start');a=p;start_publication_pending=False
            r=a['attempts'][-1];kind=r['kind'];rows=r['rows']
            result=(kernel.row_optimum(state[0],state[1],a['n'],rows[0],check,work) if kind=='row'
                    else kernel.pair_optimum(state[0],state[1],a['n'],*rows,check,work))
            if result['zero']:
                # Only structure validation precedes validators/immediate witness save.
                points=kernel.validate_points(result['points'],a['n'])
                if save_zero is None:raise ValueError('zero persistence callback required')
                ref=save_zero(points)
                if ref is None:status='zero_unverified';break
                zero_publication_pending=True
                event={'kind':kind,'rows':rows,'minimum':clone(result_item(a,result)),
                       'strict':True,'before_hash':a['state_hash']}
                move,p=prepare_accept(a,result)
                p['witness']=ref
                # Witness is already durable. A separate move may now be written.
                if save_move is None:raise ValueError('move persistence callback required')
                move_ref=save_move(move);p['artifacts'].append(move_ref)
                persist(p,'accept_zero');a=p;zero_publication_pending=False;decisions+=1;observe(event)
                status='zero';break
            strict=result['score']<a['U'];item=clone(result_item(a,result))
            event={'kind':kind,'rows':rows,'minimum':item,'strict':strict,'before_hash':a['state_hash']}
            if strict:
                rebuilt=kernel.build_index(result['points'],a['n'],check,work)
                move,p=prepare_accept(a,result,rebuilt)
                if save_move is None:raise ValueError('move persistence callback required')
                ref=save_move(move);p['artifacts'].append(ref)
                persist(p,'accept');a=p
                # New ranks may be computed only after positive durable commitment.
                state=(*rebuilt,make_orders(rebuilt[0],rebuilt[1],a['n'],a['state_hash'],check))
            else:
                p=plan_nonimprovement(a,result);persist(p,'complete');a=p
            decisions+=1;observe(event)
            if stop_after is not None and decisions>=stop_after:status='split';break
        else:status=a['status']
        if a['status']!='active':status=a['status']
    except SearchStop as exc:
        if start_publication_pending:
            status='error';error='start publication interrupted with unresolved charge: '+str(exc)
        elif zero_publication_pending:
            status='error';error='saved witness lacks durable zero authority: '+str(exc)
        else:status=str(exc)
    except Exception as exc:status='error';error=f'{type(exc).__name__}: {str(exc)[:1000]}'
    return {'authority':a,'status':status,'decisions':decisions,'error':error,'attempted_charge':attempted_charge}


def atomic_file(path,raw,*,immutable=False):
    """File+directory durability. Existing immutable names are never replaced."""
    path=Path(path)
    if immutable and path.exists():raise FileExistsError('immutable output exists')
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        if immutable:
            # Link creates the destination atomically without clobbering it.
            os.link(name,path);Path(name).unlink()
        else:os.replace(name,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:Path(name).unlink(missing_ok=True)


def json_file(path,value,*,cap=CAP,immutable=False):
    raw=compact(value)
    if len(raw)>cap:raise ValueError('JSON output byte cap')
    atomic_file(path,raw,immutable=immutable)
    return {'path':Path(path).name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


class FileStore:
    def __init__(self,out):
        self.out=Path(out);self.publications=0;self.last_durable=None;self.uncertain=False
    def publish(self,a,tag):
        if self.uncertain:raise ValueError('uncertain authority publication')
        if self.publications>=MAX_PUBLICATIONS:raise ValueError('authority publication cap')
        self.publications+=1
        try:atomic_file(self.out/'authority.json',authority_bytes(a))
        except Exception:
            self.uncertain=True;raise
        self.last_durable=clone(a)
    def save_move(self,move):
        name=f"move-{move['generation']:03d}-attempt-{move['attempt']:03d}.json"
        return json_file(self.out/name,move,cap=16384,immutable=True)


def authenticate_chain(documents,metadata,pins,check=lambda:None):
    """Only metadata/schema associations before coordinates enter geometry."""
    if (metadata.get('schema')!='two-row-fixed-suffix-handoff-identities-v1' or metadata.get('n')!=75
            or metadata.get('point_count')!=149 or metadata.get('unweighted_score')!=65
            or metadata.get('normalized_sha256')!=FIXED_STATE or metadata.get('inherited_counters')!=BASE
            or metadata.get('historical_coverage')!={'basis':'source_bound_prior_execution_not_independent_minimum_certificate',
                'pair_prefix':32,'pair_scan_complete':False,'row_sweep_complete':True,'status':'pair_cap'}):
        raise ValueError('fixed suffix metadata schema')
    ids=metadata['artifacts']
    def doc(name):
        check();value=documents[name]
        if type(value) is not dict:raise ValueError('historical document schema')
        return value
    report_name='data/two-row-descent75-v1/report.json';receipt_name='data/experiments/shepherd-two-row-descent75-v1.json'
    manifest_name='data/two-row-descent75-source-pins.json';boundary_name='data/two-row-descent75-v1/completed-boundary.json'
    initial_name='data/two-row-descent75-v1/initial.json';best_name='data/two-row-descent75-v1/best.json'
    audit_name='data/two-row-descent75-independent-chain-actual-audit.json'
    guard_name='data/two-row-descent75-independent-chain-actual-owned-guard.json'
    adapter='research/two_row_descent75_actual_chain_adapter.py';helper='research/two_row_descent_independent_chain_audit.py'
    report=doc(report_name);job=doc(receipt_name);boundary=doc(boundary_name);initial=doc(initial_name);best=doc(best_name)
    audit=doc(audit_name);guard=doc(guard_name);prior=kernel.norm_pins(doc(manifest_name))
    if str(ROOT/manifest_name) in prior:raise ValueError('prior manifest self pin')
    prior[str(ROOT/manifest_name)]=ids[manifest_name]
    if prior!=kernel.norm_pins(report.get('pins')) or prior!=kernel.norm_pins(job.get('sources_before')):
        raise ValueError('prior pin-set binding')
    if any(pins.get(k)!=v for k,v in prior.items()):raise ValueError('missing inherited prior pins')
    if any(pins.get(str((ROOT/k).resolve()))!=v for k,v in ids.items()):raise ValueError('missing suffix input pins')
    runtime=str(Path(sys.executable).resolve())
    if prior.get(str(ROOT/'research/two_row_descent75.py'))!=KERNEL_SHA or runtime not in prior or str(ROOT/'src/verify.py') not in prior:
        raise ValueError('historical mandatory sources/runtime')
    expected_argv=[str(ROOT/'.venv/bin/python'),'research/two_row_descent75.py','--seconds','25','--output-dir',
                   'data/two-row-descent75-v1','--source-pins',manifest_name]
    if (job.get('argv')!=expected_argv or job.get('status')!='completed' or job.get('sources_unchanged') is not True
            or job.get('source_manifest_sha256')!=ids[manifest_name]):raise ValueError('pilot receipt binding')
    kernel.clean_guard(job.get('gate'),30)
    if (report.get('method')!='exact_raw_two_row_descent75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('closure') is not False
            or report.get('boundary_saved') is not True or report.get('witness_saved') is not False
            or report.get('status')!='pair_cap' or report.get('validation')!='invalid_research_state'
            or report.get('n')!=75 or report.get('k')!=149 or report.get('row_cap')!=512 or report.get('pair_cap')!=32
            or report.get('soft_seconds')!=25 or report.get('search_seconds')!=23
            or report.get('boundary_sha256')!=ids[boundary_name] or report.get('current_unweighted')!=65
            or report.get('best_unweighted')!=65):raise ValueError('pilot report binding')
    elapsed=report.get('elapsed_seconds')
    if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0<=elapsed<25:raise ValueError('prior soft deadline')
    state=report.get('state')
    expected_state=dict(BASE,status='pair_cap',U=65,row_sweep_complete=True,pair_scan_complete=False)
    if state!=expected_state or boundary.get('state')!=state or boundary.get('improvements')!=report.get('improvements'):
        raise ValueError('final state/counter/coverage binding')
    if (boundary.get('schema')!='two-row-raw-descent-boundary-v1' or boundary.get('n')!=75
            or boundary.get('normalized_sha256')!=FIXED_STATE or boundary.get('policy')!={'row_cap':512,'pair_cap':32}
            or boundary.get('validation')!='invalid_research_state' or boundary.get('handoff')!=report.get('handoff')):
        raise ValueError('boundary schema/provenance')
    initial_id=metadata.get('prior_initial_normalized_sha256')
    if initial_id!=kernel.BEST_NORMALIZED or initial.get('normalized_sha256')!=initial_id or initial.get('score')!=97:
        raise ValueError('original best97 provenance')
    if initial.get('handoff')!=report.get('handoff') or report['handoff'].get('handoff_sha256')!=kernel.HANDOFF_SHA:
        raise ValueError('initial handoff binding')
    records=report.get('improvements')
    if type(records) is not list or len(records)!=28:raise ValueError('complete historical move list')
    before_hash=initial_id;before_score=97;previous=dict(row_started=0,row_completed=0,pair_started=0,pair_completed=0)
    audited={initial_name:ids[initial_name]}
    for ordinal,meta in enumerate(records,1):
        name=f'data/two-row-descent75-v1/improvement-{ordinal:03d}.json';item=doc(name)
        if meta.get('path')!=name or meta.get('sha256')!=ids[name] or meta.get('kind')!='row':raise ValueError('historical move identity')
        for key in ('score','before_score','before_normalized_sha256','normalized_sha256','kind','rows'):
            if meta.get(key)!=item.get(key):raise ValueError('historical move metadata binding')
        if (item.get('kind')!='row' or type(item.get('rows')) is not list or len(item['rows'])!=1
                or item.get('before_normalized_sha256')!=before_hash or item.get('before_score')!=before_score
                or type(item.get('score')) is not int or not 0<item['score']<before_score):raise ValueError('historical strict chain')
        for key in previous:
            if type(item.get(key)) is not int or not previous[key]<=item[key]<=BASE[key]:raise ValueError('historical counter chain')
            previous[key]=item[key]
        before_hash=item['normalized_sha256'];before_score=item['score'];audited[name]=ids[name]
    if before_hash!=FIXED_STATE or before_score!=65:raise ValueError('historical chain endpoint')
    expected_pilot={k:ids[k] for k in (report_name,receipt_name,manifest_name,boundary_name)}
    chain=audit.get('chain',{})
    if (audit.get('accepted') is not True or audit.get('pilot_artifact_hashes')!=expected_pilot
            or audit.get('audited_chain_artifact_hashes')!=audited or audit.get('pilot_pins_checked')!=len(prior)
            or audit.get('audit_source_sha256')!=ids[adapter] or audit.get('chain_helper_sha256')!=ids[helper]
            or audit.get('runtime_path')!=runtime or audit.get('runtime_sha256')!=pins.get(runtime)
            or chain.get('artifact_chain_passed') is not True or chain.get('n')!=75 or chain.get('states_recounted')!=29
            or chain.get('scores')!=[97]+[doc(f'data/two-row-descent75-v1/improvement-{i:03d}.json')['score'] for i in range(1,29)]
            or chain.get('final_counters')!={k:BASE[k] for k in previous} or chain.get('zero_geometry_verified') is not False):
        raise ValueError('independent actual chain association')
    audit_argv=[str(ROOT/'.venv/bin/python'),adapter,'--seconds','25','--output',audit_name]
    if (guard.get('status')!='completed' or guard.get('argv')!=audit_argv or guard.get('audit_output_sha256')!=ids[audit_name]):
        raise ValueError('independent audit guard association')
    kernel.clean_guard(guard,30)
    source_pins=kernel.norm_pins(guard.get('source_pins'))
    if any(source_pins.get(str(ROOT/name))!=ids[name] for name in (adapter,helper)):
        raise ValueError('independent audit guard source binding')
    if any(pins.get(k)!=v for k,v in source_pins.items()):raise ValueError('independent audit source drift')
    if (best.get('classification')!='dual_checked_invalid_research_state' or best.get('valid') is not False
            or best.get('certificate',{}).get('claimed_conflict_count')!=65):raise ValueError('best65 diagnostic schema')
    for v,algorithm in zip(best.get('validators',[]),('integer_normalized_slopes','integer_cross_products')):
        if (v.get('algorithm')!=algorithm or v.get('normalized_sha256')!=FIXED_STATE or v.get('conflict_count')!=65
                or v.get('valid') is not False or v.get('errors')!=[] or v.get('point_count')!=149 or v.get('n')!=75):
            raise ValueError('best65 validator binding')
    if len(best.get('validators',[]))!=2:raise ValueError('best65 validators')
    # All fixed byte/schema/receipt/audit associations precede geometry.
    points=kernel.validate_points(boundary.get('points'),75)
    if (kernel.normalized_sha256(75,points)!=FIXED_STATE
            or kernel.validate_points(best['certificate'].get('points'),75)!=points
            or kernel.validate_points(doc('data/two-row-descent75-v1/improvement-028.json').get('points'),75)!=points):
        raise ValueError('fixed65 coordinate identity')
    return points


def load_handoff(pins,check):
    path=ROOT/HANDOFF_PATH
    if pins.get(str(path))!=HANDOFF_SHA or digest(path,check)!=HANDOFF_SHA:raise ValueError('fixed suffix metadata hash')
    if path.stat().st_size>16384:raise ValueError('suffix metadata cap')
    metadata=json.loads(path.read_bytes());ids=metadata.get('artifacts')
    if type(ids) is not dict or len(ids)!=39:raise ValueError('fixed39 input artifacts')
    snapshots={}
    for name,sha in ids.items():
        check();p=ROOT/name
        if pins.get(str(p.resolve()))!=sha or digest(p,check)!=sha:raise ValueError('fixed suffix artifact bytes')
        if p.stat().st_size>CAP:raise ValueError('historical artifact cap')
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('historical snapshot drift')
        snapshots[name]=raw
    docs={name:json.loads(raw) for name,raw in snapshots.items() if name.endswith('.json')}
    report=docs['data/two-row-descent75-v1/report.json']
    if report.get('boundary_bytes')!=len(snapshots['data/two-row-descent75-v1/completed-boundary.json']):raise ValueError('boundary byte count')
    for ordinal,meta in enumerate(report.get('improvements',[]),1):
        if meta.get('bytes')!=len(snapshots[f'data/two-row-descent75-v1/improvement-{ordinal:03d}.json']):raise ValueError('historical move byte count')
    points=authenticate_chain(docs,metadata,pins,check)
    fresh=kernel.dual_validate(points,75,65,check)
    best=docs['data/two-row-descent75-v1/best.json']
    if fresh['validators']!=best['validators'] or fresh['conflicts_sha256']!=best.get('conflicts_sha256'):
        raise ValueError('fresh fixed65 dual recount')
    return points,{'metadata_sha256':HANDOFF_SHA,'normalized_sha256':FIXED_STATE,'score':65,
                   'historical_pair_prefix':32,'coverage_basis':metadata['historical_coverage']['basis']}


def preserve_zero(points,n,out,check,report):
    """Validators and witness persistence precede optional ledger/raw output."""
    out=Path(out)
    ref=None
    try:
        validated=kernel.dual_validate(points,n,0,check)
        # No clock, pin, ledger or raw-file work before immediate save.
        ref=json_file(out/'valid149.json',validated,cap=16384,immutable=True)
        report['witness_saved']=True;report['witness']=ref
        report['witness_state_hash']=validated['validators'][0]['normalized_sha256']
        return ref
    except Exception as exc:
        if ref is not None:
            report.update(witness_saved=True,witness=ref,witness_metadata_error=f'{type(exc).__name__}: {str(exc)[:1000]}')
            return ref
        report['zero_validation_error']=f'{type(exc).__name__}: {str(exc)[:1000]}'
        try:
            report['raw_zero']=json_file(out/'raw-zero.json',{'n':n,'points':points,'score':0,
                'classification':'unverified_zero_candidate','state_hash':kernel.normalized_sha256(n,points)},cap=16384,immutable=True)
        except Exception as raw_error:report['raw_zero_error']=f'{type(raw_error).__name__}: {str(raw_error)[:1000]}'
        return None


def run(out,manifest,seconds=25,*,started=None,clock=time.monotonic):
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 2<seconds<=25:raise ValueError('duration')
    start=clock() if started is None else started;soft=start+seconds;search=soft-2
    def final_check():
        if clock()>=soft:raise TimeoutError('main soft deadline')
    def search_check():
        if clock()>=search:raise SearchStop('search_deadline')
    out=Path(out);store=FileStore(out);pins={};ready=False;result=None;input_info=None
    report={'method':'fixed65_cursor_two_row_suffix75','accepted':False,'identity_valid':False,'closure':False,
            'n':75,'k':149,'status':'incomplete','soft_seconds':seconds,'search_seconds':seconds-2,
            'row_cap':512,'pair_cap':96,'new_row_cap':204,'new_pair_cap':64,'witness_saved':False,
            'scope':'One fixed65 suffix; imported32-prefix is source-supported, not an independent exclusion. No resume/automatic continuation.',
            'work':{}}
    def verify_pins():
        for name,sha in pins.items():
            if digest(name,final_check)!=sha:raise ValueError('pin drift: '+name)
    def save_zero(points):
        return preserve_zero(points,75,out,final_check,report)
    try:
        final_check();path=Path(manifest).resolve()
        if path.stat().st_size>2*CAP:raise ValueError('manifest byte cap')
        raw=path.read_bytes();pins=kernel.norm_pins(json.loads(raw));runtime=str(Path(sys.executable).resolve())
        required={str(Path(__file__).resolve()),str(Path(kernel.__file__).resolve()),str(ROOT/'src/verify.py'),runtime,str(ROOT/HANDOFF_PATH)}
        if not required<=pins.keys() or pins.get(str(Path(kernel.__file__).resolve()))!=KERNEL_SHA:raise ValueError('mandatory suffix/kernel/runtime pins')
        if str(path) in pins:raise ValueError('manifest self entry')
        pins[str(path)]=hashlib.sha256(raw).hexdigest();verify_pins();ready=True
        points,input_info=load_handoff(pins,final_check)
        prepared=kernel.build_index(points,75,search_check,report['work'])
        if prepared[2]!=65:raise ValueError('index must recount65')
        a=new_authority(points,75,base=BASE,pair_prefix=32,row_complete=True,prepared=prepared,check=search_check)
        if len(a['orders']['pairs'])<33:raise ValueError('source-bound prefix lacks next eligible pair')
        final_check();store.publish(a,'initialize')
        json_file(out/'initial.json',{'n':75,'points':points,'score':65,'state_hash':FIXED_STATE,'counters':BASE,
                  'order_sha256':a['orders']['sha256'],'pair_cursor':32,'handoff':input_info},cap=16384,immutable=True)
        result=drive(a,check=search_check,publish=store.publish,save_move=store.save_move,save_zero=save_zero,
                     prepared=prepared,work=report['work'])
        report['status']=result['status']
        if result['error']:report['search_error']=result['error']
        if result.get('attempted_charge'):report['last_attempted_charge']=result['attempted_charge']
        if not store.uncertain:
            # Mandatory final snapshot may be late; acceptance still fails time.
            final=clone(result['authority']);final['status']=result['status']
            store.publish(final,'final_stop')
    except Exception as exc:report.update(status='error',error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(authority_publications=store.publications,authority_uncertain=store.uncertain)
    if store.last_durable is not None:
        a=store.last_durable
        report['state']={k:a[k] for k in ('n','U','state_hash','generation','counters','phase','row_cursor','pair_cursor',
                                        'row_sweep_complete','pair_scan_complete','pending','status')}
        report['artifacts']=a['artifacts'];report['attempts']=a['attempts']
        report['order_sha256']=None if a['orders'] is None else a['orders']['sha256']
        try:
            report['authority_sha256']=digest(out/'authority.json',final_check)
            report['authority_bytes']=(out/'authority.json').stat().st_size
        except Exception as exc:report['authority_identity_error']=f'{type(exc).__name__}: {str(exc)[:1000]}'
    try:
        if not ready or store.last_durable is None or store.uncertain:raise ValueError('no unambiguous durable authority')
        verify_pins();final_check();report['identity_valid']=True
        allowed=('row_cap','pair_cap','search_deadline','no_strict_descent','zero')
        report['accepted']=(report['status'] in allowed and 'search_error' not in report and 'authority_identity_error' not in report
                            and 'witness_metadata_error' not in report
                            and (store.last_durable['U']>0 or report['witness_saved'])
                            and (result is None or result.get('attempted_charge') is None or all(
                                store.last_durable['counters'][key]>=result['attempted_charge'][key]
                                for key in ('row_started','pair_started')))
                            and (not report['witness_saved'] or (store.last_durable['U']==0
                                  and store.last_durable['witness']==report.get('witness'))))
    except Exception as exc:report.update(accepted=False,identity_valid=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(pins=pins,handoff=input_info,elapsed_seconds=clock()-start)
    try:
        json_file(out/'report.json',report);final_check()
    except Exception as exc:
        report.update(accepted=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}',elapsed_seconds=clock()-start)
        json_file(out/'report.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--source-pins',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    report=run(args.output_dir,args.source_pins,args.seconds,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('status','accepted','witness_saved','state','authority_publications','elapsed_seconds')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__=='__main__':sys.exit(main())
