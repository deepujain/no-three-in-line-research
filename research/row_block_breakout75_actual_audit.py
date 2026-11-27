"""Read-only pilot audit of saved states and receipt; does not replay trajectory.

Run only after the pilot exists under a separately owned guard. No production
checkpoint import, resume, search or mutation is implemented here.
"""
import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1]
WORKER_SHA='ee8a78e0f199f2a2f52e2bc37530c12a05c6b54a978f31371b05d9558cd51e0f'


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        while block:=f.read(65536): h.update(block)
    return h.hexdigest()


def normalized(points):
    return hashlib.sha256(json.dumps({'n':75,'points':[list(p) for p in sorted(points)]},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def parse_points(values):
    if type(values) is not list or len(values)!=149: raise ValueError('point count')
    points=[]
    for p in values:
        if type(p) is not list or len(p)!=2 or any(type(v) is not int or not 0<=v<75 for v in p): raise ValueError('point domain')
        points.append(tuple(p))
    if len(set(points))!=149 or sorted(Counter(y for x,y in points).values()) != [1]+[2]*74: raise ValueError('row pattern')
    return points


def direct_score(points,weights=None):
    weights=weights or {}; raw=weighted=0
    for p,q,r in combinations(points,3):
        dx,dy=q[0]-p[0],q[1]-p[1]
        if dx*(r[1]-p[1]) != dy*(r[0]-p[0]): continue
        raw+=1; a,b=dy,-dx; g=math.gcd(abs(a),abs(b)); a//=g; b//=g
        if a<0 or (a==0 and b<0): a,b=-a,-b
        weighted+=weights.get((a,b,a*p[0]+b*p[1]),1)
    return raw,weighted


def norm(mapping):
    if type(mapping) is not dict: raise ValueError('pin mapping')
    result={str((ROOT/Path(k)).resolve()):v for k,v in mapping.items()}
    if len(result)!=len(mapping): raise ValueError('duplicate normalized pins')
    return result


def audit(report_path,receipt_path,manifest_path,expected_manifest_sha):
    report_path,receipt_path,manifest_path=map(Path,(report_path,receipt_path,manifest_path)); paths=(report_path,receipt_path,manifest_path)
    snapshots=[p.read_bytes() for p in paths]; hashes=[hashlib.sha256(b).hexdigest() for b in snapshots]
    if hashes[2]!=expected_manifest_sha: raise ValueError('manifest hash')
    if len(snapshots[0])>1024*1024: raise ValueError('report cap')
    report,job,manifest=map(json.loads,snapshots); pins=norm(manifest); m=str(manifest_path.resolve())
    if m in pins: raise ValueError('self pin')
    pins[m]=hashes[2]
    if pins!=norm(report['pins']) or pins!=norm(job['sources_before']): raise ValueError('pin set binding')
    worker=ROOT/'research/row_block_breakout75.py'; runtime=str(Path(sys.executable).resolve())
    if pins.get(str(worker))!=WORKER_SHA or str(ROOT/'src/verify.py') not in pins or runtime not in pins or str(Path(random.__file__).resolve()) not in pins: raise ValueError('mandatory pins')
    for path,expected in pins.items():
        if sha(path)!=expected: raise ValueError('pin drift')
    out=report_path.resolve().parent
    argv=[str(ROOT/'.venv/bin/python'),'research/row_block_breakout75.py','--seconds','25','--output-dir',str(out.relative_to(ROOT)), '--source-pins',str(manifest_path.resolve().relative_to(ROOT))]
    if job.get('argv')!=argv or job.get('status')!='completed' or job.get('sources_unchanged') is not True: raise ValueError('job binding')
    g=job['gate']; ints=('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')
    if any(type(g.get(k)) is not int for k in ints) or g.get('gate_status')!='exited' or g['returncode']!=0 or g.get('cleanup_status')!='clean' or g.get('cleanup_error') is not None or g.get('monitor_error') is not None or g.get('trigger_gate_status') is not None or g['seconds_limit']!=30 or g['rss_limit_mib']!=256 or not 0<g['peak_sampled_rss_kib']<=256*1024 or g['rss_samples']<1 or g['cleanup_samples']<1: raise ValueError('guard')
    elapsed=(report.get('elapsed_seconds'),g.get('elapsed_seconds'),job.get('elapsed_seconds'))
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in elapsed) or not 0<=elapsed[0]<25 or not 0<elapsed[1]<30 or not elapsed[0]<=elapsed[1]<=elapsed[2]<=30: raise ValueError('elapsed')
    if report.get('method')!='from_scratch_row_block_breakout75' or report.get('accepted') is not True or report.get('identity_valid') is not True or report.get('closure') is not False or report.get('checkpoint_saved') is not True or report.get('n')!=75 or report.get('k')!=149 or report.get('seed')!=275149: raise ValueError('report status')
    cp_path=out/'completed-boundary.json'; cp_raw=cp_path.read_bytes()
    if len(cp_raw)>2*1024*1024 or report.get('checkpoint_bytes')!=len(cp_raw) or report.get('checkpoint_sha256')!=hashlib.sha256(cp_raw).hexdigest(): raise ValueError('checkpoint binding/cap')
    cp=json.loads(cp_raw)
    if type(cp) is not dict or set(cp)!={'metadata','current','best','weights','rng'}: raise ValueError('checkpoint keys')
    meta=cp['metadata']
    if len(json.dumps(meta,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii'))>16384: raise ValueError('metadata cap')
    current=parse_points(cp['current']); best=parse_points(cp['best'])
    if meta.get('schema')!='row-block-completed-boundary-v1' or meta.get('current_normalized_sha256')!=normalized(current) or meta.get('best_normalized_sha256')!=normalized(best): raise ValueError('checkpoint identities')
    ids=meta['identities']
    if ids.get('manifest_sha256')!=hashes[2] or ids.get('manifest_path')!=m or ids.get('worker_sha256')!=WORKER_SHA or ids.get('runtime_path')!=runtime or ids.get('runtime_sha256')!=pins[runtime] or ids.get('python_version')!=sys.version or ids.get('RNG_version')!=3 or ids.get('soft_seconds')!=25 or ids.get('search_seconds')!=23 or ids.get('owned_seconds')!=30 or ids.get('rss_limit_mib')!=256: raise ValueError('runtime identity')
    if ids.get('random_module_path') != str(Path(random.__file__).resolve()) or ids.get('random_module_sha256') != pins.get(str(Path(random.__file__).resolve())): raise ValueError('random source identity')
    policy=meta['policy']; expected_policy={'n':75,'k':149,'seed':275149,'max_steps':200000,'migration_period':16,'migration_samples':32,'penalty_period':32,'max_weight_keys':65536,'max_weight':65535}
    if report.get('policy')!={k:v for k,v in expected_policy.items() if k in ('migration_period','migration_samples','penalty_period','max_weight_keys','max_weight')} or report.get('max_steps')!=200000 or report.get('soft_seconds')!=25 or report.get('search_seconds')!=23 or report.get('status') not in ('search_deadline','step_cap','weight_key_cap','weight_value_cap'): raise ValueError('report policy/status')
    if policy!=expected_policy: raise ValueError('policy identity')
    weights={}; records=cp['weights']
    if type(records) is not list or len(records)>65536: raise ValueError('weight count')
    last=None
    for row in records:
        if type(row) is not list or len(row)!=4 or any(type(x) is not int for x in row): raise ValueError('weight record')
        a,b,c,w=row; key=(a,b,c)
        if not (0<=a<=74 and -74<=b<=74 and abs(c)<=10952 and math.gcd(a,abs(b))==1 and (a>0 or b>0) and 1<w<=65535) or (last is not None and key<=last): raise ValueError('weight schema/order')
        weights[key]=w; last=key
    rng=cp['rng']
    if type(rng) is not list or len(rng)!=3 or type(rng[0]) is not int or rng[0]!=3 or type(rng[1]) is not list or len(rng[1])!=625 or rng[2] is not None or any(type(v) is not int or not 0<=v<=0xffffffff for v in rng[1][:-1]) or type(rng[1][-1]) is not int or not 0<=rng[1][-1]<=624: raise ValueError('RNG state')
    random.Random().setstate((3,tuple(rng[1]),None))
    logical=meta['logical']; keys=('transitions','row_transitions','migration_transitions','penalty_events','best_improvements','best_improvements_after_penalty','raw_down','raw_neutral','raw_up')
    if type(logical) is not dict or set(logical)!=set(keys) or any(type(v) is not int or not 0<=v<2**64 for v in logical.values()) or logical['transitions']>200000 or logical['row_transitions']+logical['migration_transitions']!=logical['transitions'] or logical['raw_down']+logical['raw_neutral']+logical['raw_up']!=logical['transitions'] or logical['migration_transitions']!=logical['transitions']//16 or logical['penalty_events']>logical['transitions']//32 or report.get('logical')!=logical: raise ValueError('logical counters')
    if type(meta['stagnation']) is not int or not 0<=meta['stagnation']<32 or meta['deficient_row']!=next(y for y in range(75) if sum(p[1]==y for p in current)==1): raise ValueError('boundary deficiency')
    if meta.get('validation')!=report.get('validation') or meta.get('stagnation')!=report.get('stagnation') or any(type(meta.get(k)) is not int or not 0<=meta[k]<2**64 for k in ('current_unweighted','current_weighted','best_unweighted','best_weighted_at_capture','best_weight_epoch')) or meta['best_weight_epoch']>logical['penalty_events'] or any(w>logical['penalty_events']+1 for w in weights.values()) or meta['best_weighted_at_capture']>65535*meta['best_unweighted']: raise ValueError('boundary counters/weights')
    current_raw,current_weight=direct_score(current,weights); best_raw,_=direct_score(best)
    if (current_raw,current_weight,best_raw)!=(meta['current_unweighted'],meta['current_weighted'],meta['best_unweighted']) or best_raw>current_raw or (report.get('current_unweighted'),report.get('current_weighted'),report.get('best_unweighted'))!=(current_raw,current_weight,best_raw): raise ValueError('independent score mismatch')
    if current_raw==0 or best_raw==0 or report.get('witness_saved') is not False: raise ValueError('zero result requires separate witness audit')
    if report.get('weight_keys') != len(weights) or report.get('weight_key_maximum') != len(weights): raise ValueError('weight count binding')
    classification=meta['validation']
    if current_raw>0 and classification!='invalid_research_state': raise ValueError('invalid classification')
    if current_raw==0 and classification not in ('unverified_zero_candidate','dual_verified_witness'): raise ValueError('zero classification')
    if classification=='dual_verified_witness' and report.get('witness_saved') is not True: raise ValueError('witness binding')
    initial=out/'initial.json'; initial_score=None
    aux_hashes={}
    if initial.exists():
        aux_hashes[initial]=sha(initial); x=json.loads(initial.read_text()); initial_points=parse_points(x['points']); initial_score,_=direct_score(initial_points)
        generator=random.Random(275149); deficient=generator.randrange(75); expected_initial=[]
        for y in range(75): expected_initial.extend((x,y) for x in generator.sample(range(75),1 if y==deficient else 2))
        if sorted(initial_points)!=sorted(expected_initial) or best_raw>initial_score: raise ValueError('initial seed/best monotonicity')
        if x.get('n')!=75 or x.get('unweighted')!=initial_score or x.get('weighted')!=initial_score or x.get('valid') is not False or report.get('initial_unweighted')!=initial_score: raise ValueError('initial diagnostic')
    else: raise ValueError('missing positive initial state')
    if initial_score<=0: raise ValueError('nonpositive initial state')
    diagnostic=out/'best.json'
    if diagnostic.exists() != (report.get('best_diagnostic_saved') is True): raise ValueError('best file flag')
    if diagnostic.exists():
        aux_hashes[diagnostic]=sha(diagnostic); d=json.loads(diagnostic.read_text()); cert=d['certificate']; vals=d['validators']; pts=parse_points(cert['points']); score,_=direct_score(pts)
        if d.get('valid') is not False or d.get('classification')!='dual_checked_invalid_research_state' or not 0<score<=1000 or score!=best_raw or normalized(pts)!=normalized(best) or type(vals) is not list or len(vals)!=2 or cert.get('n')!=75 or cert.get('claimed_conflict_count')!=score or cert.get('axis_counts')!={'rows':[sum(y==r for x,y in pts) for r in range(75)],'columns':[sum(x==c for x,y in pts) for c in range(75)]}: raise ValueError('best diagnostic')
        for v,alg in zip(vals,('integer_normalized_slopes','integer_cross_products')):
            if v.get('algorithm')!=alg or v.get('valid') is not False or v.get('conflict_count')!=score or v.get('normalized_sha256')!=normalized(best) or v.get('n')!=75 or v.get('point_count')!=149 or v.get('errors')!=[]: raise ValueError('best validators')
        conflicts=[]
        for i,j,k in combinations(range(len(pts)),3):
            a,b,c=pts[i],pts[j],pts[k]
            if (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0]): conflicts.append({'indices':[i,j,k],'points':[list(a),list(b),list(c)]})
        encoded=json.dumps(conflicts,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
        if d.get('conflicts_sha256')!=hashlib.sha256(encoded).hexdigest(): raise ValueError('best conflict digest')
    for path,expected in aux_hashes.items():
        if sha(path)!=expected: raise ValueError('diagnostic drift')
    checkpoints=report.get('checkpoints'); penalties=report.get('penalty_checkpoints')
    if type(checkpoints) is not list or len(checkpoints)>64 or type(penalties) is not list or len(penalties)>32: raise ValueError('telemetry limits')
    if len(checkpoints)+len(penalties)>64: raise ValueError('combined telemetry cap')
    for item in checkpoints+penalties:
        if type(item) is not dict or type(item.get('step')) is not int or not 0<item['step']<=logical['transitions'] or type(item.get('unweighted')) is not int or not 0<item['unweighted']<=math.comb(149,3) or type(item.get('penalty_events')) is not int or not 0<=item['penalty_events']<=logical['penalty_events'] or type(item.get('state_sha256')) is not str or len(item['state_sha256'])!=64 or any(c not in '0123456789abcdef' for c in item['state_sha256']): raise ValueError('telemetry schema')
    if [x['step'] for x in checkpoints] != [1<<i for i in range(logical['transitions'].bit_length())] or any(type(x.get('best')) is not int or not 0<x['best']<=x['unweighted'] for x in checkpoints): raise ValueError('power checkpoint coverage')
    if [x['penalty_events'] for x in penalties] != list(range(1,min(32,logical['penalty_events'])+1)) or any(a['step']>=b['step'] for a,b in zip(penalties,penalties[1:])): raise ValueError('penalty telemetry coverage')
    if hashlib.sha256(cp_path.read_bytes()).hexdigest()!=hashlib.sha256(cp_raw).hexdigest(): raise ValueError('checkpoint drift')
    if [sha(p) for p in paths]!=hashes: raise ValueError('snapshot drift')
    return {'accepted':True,'scope':'saved boundary and receipt only; trajectory not replayed', 'initial_unweighted':initial_score,'current_unweighted':current_raw,'best_unweighted':best_raw,'weighted_current':current_weight,'logical':logical,'telemetry_penalty_hashes_distinct':len({x['state_sha256'] for x in penalties}),'telemetry_note':'reported history only; trajectory not replayed','checkpoint_sha256':hashlib.sha256(cp_raw).hexdigest(),'report_sha256':hashes[0],'receipt_sha256':hashes[1],'manifest_sha256':hashes[2],'pins_checked':len(pins)}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--report',type=Path,required=True); p.add_argument('--receipt',type=Path,required=True); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--manifest-sha256',required=True); a=p.parse_args()
    print(json.dumps(audit(a.report,a.receipt,a.manifest,a.manifest_sha256),sort_keys=True))

if __name__=='__main__': main()
