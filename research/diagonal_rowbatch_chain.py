"""Sequential, bounded, fail-closed row-batch checkpoint-guard chain.

A chain ledger is single-use. Interrupted or rejected invocations require a
separate ownership audit and explicit new allocation; this runner never resumes
an existing ledger. Only cooperating callers honor the chain lock.
"""
import time
MODULE_STARTED=time.monotonic()
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import diagonal_rowbatch_checkpoint_guard as guard
from research.diagonal_secant_checkpoint import encode,sha
from research.diagonal_secant_dfs_fast import pair_orbits
from src.verify import verify_certificate,verify_certificate_bruteforce

CEILING=900.0
LAUNCH_WINDOW=840.0
RESERVATION=32.0
MAX_INVOCATIONS=26


def source_hashes():
    return {'chain':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), **guard.hashes()}


def _frontier(path, expected, n, deficits, diagonals, sources):
    raw=guard.read_frontier(path)
    if sha(raw)!=expected:raise ValueError('checkpoint hash mismatch')
    data=json.loads(raw)
    if not isinstance(data,dict):raise ValueError('checkpoint must be an object')
    identity=data.get('identity',{})
    wanted={'format':'diagonal-rowbatch-frontier-v1','n':n,'deficits':deficits,'diagonals':diagonals,
            'source_hashes':{'rowbatch_checkpoint':sources['checkpoint_core'],
                             'tiny_reference':sources['tiny_reference'],
                             'checkpoint_utilities':sources['checkpoint_utilities'],
                             'fast_core':sources['fast_core'],
                             'original_core':sources['original_core'],
                             'verifier':sources['verifier']},
            'orbit_order_sha256':sha(encode(pair_orbits(n))),
            'branch_order':'minimum-viable-row-then-lexicographic-unordered-batch-v1'}
    if identity!=wanted:raise ValueError('checkpoint identity mismatch')
    counts=data.get('slice_counts');index=data.get('slice_index');frames=data.get('frames')
    if (not isinstance(counts,list) or len(counts)!=len(deficits)*len(diagonals) or
        any(not isinstance(c,list) or len(c)!=2 or any(type(v) is not int or v<0 for v in c) for c in counts) or
        any(c[1]>c[0] for c in counts) or
        type(data.get('nodes')) is not int or type(data.get('witness_visits')) is not int or
        data['nodes']!=sum(c[0] for c in counts) or data['witness_visits']!=sum(c[1] for c in counts) or
        type(index) is not int or not 0<=index<=len(counts) or not isinstance(frames,list) or len(frames)>n or
        (index==len(counts)) != (not frames) or any(c != [0,0] for c in counts[index+1:])):
        raise ValueError('invalid checkpoint counters or frontier')
    return data


def run(n,checkpoint,expected_sha256,ledger_dir,*,max_nodes,deficits=None,diagonals=None,
        seconds=30.0,rss_mib=256.0,aggregate_seconds=900.0,max_invocations=26,started=None):
    started=time.monotonic() if started is None else started
    if type(n) is not int or not 2<=n<=79:raise ValueError('invalid n')
    if type(max_nodes) is not int or max_nodes<1:raise ValueError('invalid node cap')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 1<seconds<=30:raise ValueError('invalid per-invocation time')
    if isinstance(rss_mib,bool) or not isinstance(rss_mib,(int,float)) or not math.isfinite(rss_mib) or not 0<rss_mib<=256:raise ValueError('invalid RSS cap')
    if isinstance(aggregate_seconds,bool) or not isinstance(aggregate_seconds,(int,float)) or not math.isfinite(aggregate_seconds) or not 0<aggregate_seconds<=CEILING:raise ValueError('invalid aggregate ceiling')
    if type(max_invocations) is not int or not 1<=max_invocations<=MAX_INVOCATIONS:raise ValueError('invalid invocation cap')
    if not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or any(c not in '0123456789abcdef' for c in expected_sha256):raise ValueError('trusted expected SHA required')
    def indices(values):
        values=list(range(n)) if values is None else list(values)
        if not values or any(type(i) is not int or not 0<=i<n for i in values) or len(set(values))!=len(values):raise ValueError('invalid slice indices')
        return sorted(values)
    ds,ts=indices(deficits),indices(diagonals)
    checkpoint=Path(checkpoint).resolve();directory=Path(ledger_dir).resolve();ledger_path=directory/'ledger.json'
    chain_lock=checkpoint.with_name(checkpoint.name+'.chain.lock')
    chain_marker=checkpoint.with_name(checkpoint.name+'.chain-owner.json')
    interrupted=False
    def term(signum,frame):
        nonlocal interrupted
        interrupted=True
    old=signal.signal(signal.SIGTERM,term)
    try:
        with open(chain_lock,'a+b') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('chain already owned')
            if chain_marker.exists():
                marker=json.loads(chain_marker.read_text())
                if marker.get('status')!='closed':raise ValueError('prior chain requires independent ownership audit')
            sources=source_hashes();current=_frontier(checkpoint,expected_sha256,n,ds,ts,sources)
            def sources_stable():
                try:return source_hashes()==sources
                except OSError:return False
            directory.mkdir(parents=True,exist_ok=False)
            ledger={'status':'running','complete':False,'n':n,'deficits':ds,'diagonals':ts,
                    'checkpoint':str(checkpoint),'initial_expected_sha256':expected_sha256,
                    'current_accepted_sha256':expected_sha256,'source_hashes':sources,
                    'max_nodes':max_nodes,'seconds_limit':seconds,'rss_limit_mib':rss_mib,
                    'aggregate_seconds':aggregate_seconds,'launch_window_seconds':min(LAUNCH_WINDOW,max(0,aggregate_seconds-60)),
                    'reservation_seconds_per_invocation':RESERVATION,'reserved_seconds':0,
                    'max_invocations':max_invocations,'invocations':[],
                    'scope':'Declared diagonal-reflection slices only; no unrestricted infeasibility conclusion.'}
            def publish():
                ledger['elapsed_seconds']=time.monotonic()-started
                guard.atomic(ledger_path,encode(ledger))
            publish()
            guard.atomic(chain_marker,encode({'status':'running','ledger':str(ledger_path),'initial_expected_sha256':expected_sha256}))
            for number in range(1,max_invocations+1):
                elapsed=time.monotonic()-started
                if interrupted:ledger['status']='cancelled';break
                if current['slice_index']==len(ds)*len(ts):ledger['status']='all_declared_slices_exhausted';ledger['complete']=True;break
                if elapsed+RESERVATION>ledger['launch_window_seconds'] or ledger['reserved_seconds']+RESERVATION>aggregate_seconds:
                    ledger['status']='reservation_limit';break
                if not sources_stable():ledger['status']='source_changed';break
                report_path=directory/f'invocation-{number:02d}.json'
                item={'number':number,'status':'running','expected_sha256':expected_sha256,'report':str(report_path),'reserved_seconds':RESERVATION}
                ledger['invocations'].append(item);ledger['reserved_seconds']+=RESERVATION;publish()
                if interrupted or time.monotonic()-started+RESERVATION>ledger['launch_window_seconds']:
                    item['status']='not_launched';ledger['status']='cancelled' if interrupted else 'reservation_limit';break
                report=None
                try:
                    report=guard.run(n,seconds,rss_mib,max_nodes,checkpoint,report_path,expected_sha256=expected_sha256,deficits=ds,diagonals=ts)
                    if not sources_stable():raise ValueError('source changed')
                    if interrupted:raise ValueError('chain cancelled')
                    if time.monotonic()-started>=aggregate_seconds:raise ValueError('aggregate deadline exceeded')
                    if json.loads(report_path.read_text())!=report:raise ValueError('report mismatch')
                    g=report.get('guard',{});w=report.get('worker_result',{})
                    if (g.get('gate_status')!='exited' or g.get('cleanup_status')!='clean' or type(g.get('returncode')) is not int or g.get('returncode')!=0 or
                        g.get('source_stable') is not True or g.get('monitor_error') is not None or
                        type(g.get('rss_samples')) is not int or g['rss_samples']<1 or
                        type(g.get('peak_sampled_rss_kib')) not in (int,float) or not math.isfinite(g['peak_sampled_rss_kib']) or not 0<g['peak_sampled_rss_kib']<=rss_mib*1024 or
                        type(g.get('elapsed_seconds')) not in (int,float) or not math.isfinite(g['elapsed_seconds']) or not 0<=g['elapsed_seconds']<seconds or
                        type(report.get('elapsed_seconds')) not in (int,float) or not math.isfinite(report['elapsed_seconds']) or not 0<=report['elapsed_seconds']<seconds or
                        report.get('source_hashes')!={k:v for k,v in sources.items() if k!='chain'} or
                        report.get('n')!=n or report.get('max_nodes')!=max_nodes or
                        report.get('seconds_limit')!=seconds or report.get('rss_limit_mib')!=rss_mib or
                        report.get('previous_checkpoint_sha256')!=expected_sha256 or
                        report.get('status') not in ('node_limit','timeout','all_declared_slices_exhausted') or
                        w.get('status')!=report.get('status') or
                        type(report.get('complete')) is not bool or report.get('complete')!=(report.get('status')=='all_declared_slices_exhausted')):raise ValueError('guard report not accepted')
                    accepted=report.get('accepted_checkpoint_sha256')
                    if not accepted or report.get('published_checkpoint_sha256')!=accepted or w.get('checkpoint_sha256')!=accepted:raise ValueError('no accepted frontier')
                    next_state=_frontier(checkpoint,accepted,n,ds,ts,sources)
                    if next_state.get('previous_checkpoint_sha256')!=expected_sha256:raise ValueError('predecessor mismatch')
                    delta=next_state['nodes']-current['nodes'];wdelta=next_state['witness_visits']-current['witness_visits']
                    if (type(w.get('nodes_this_run')) is not int or delta!=w.get('nodes_this_run') or not 0<=delta<=max_nodes or not 0<=wdelta<=delta or
                        w.get('nodes_total')!=next_state['nodes'] or w.get('witness_visits_total')!=next_state['witness_visits'] or
                        w.get('slice_counts')!=next_state['slice_counts'] or w.get('slice_index')!=next_state['slice_index'] or
                        next_state['slice_index']<current['slice_index'] or
                        any(new[0]<oldc[0] or new[1]<oldc[1] or new[1]-oldc[1]>new[0]-oldc[0] for oldc,new in zip(current['slice_counts'],next_state['slice_counts']))):raise ValueError('invalid counter transition')
                    exhausted=next_state['slice_index']==len(ds)*len(ts)
                    if exhausted!=(report['status']=='all_declared_slices_exhausted'):raise ValueError('invalid exhaustion claim')
                    witness_paths=list(Path(report['witness_dir']).glob('*.json'))
                    if wdelta and not witness_paths:raise ValueError('missing persisted witness')
                    witness_hashes=[]
                    for p in witness_paths:
                        cert=json.loads(p.read_text());checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                        if (cert.get('n')!=n or not all(c['valid'] and c['point_count']==2*n-1 for c in checks) or
                            {(y,x) for x,y in cert['points']}!={tuple(q) for q in cert['points']} or
                            checks[0]['normalized_sha256']!=checks[1]['normalized_sha256'] or p.stem!=checks[0]['normalized_sha256'] or
                            cert.get('metadata',{}).get('guard_source_hashes')!=report['source_hashes']):raise ValueError('invalid witness')
                        witness_hashes.append(p.stem)
                    if time.monotonic()-started>=aggregate_seconds or interrupted or not sources_stable():raise ValueError('final acceptance check failed')
                    item.update(status='accepted',accepted_sha256=accepted,nodes_delta=delta,witness_visits_delta=wdelta,witness_hashes=sorted(witness_hashes),report_sha256=sha(report_path.read_bytes()))
                    expected_sha256=accepted;current=next_state;ledger['current_accepted_sha256']=accepted;publish()
                    if time.monotonic()-started>=aggregate_seconds or interrupted or not sources_stable():
                        item.update(status='rejected',published_unaccepted_sha256=accepted,error='post-ledger acceptance check failed')
                        item.pop('accepted_sha256',None)
                        ledger['current_accepted_sha256']=item['expected_sha256']
                        ledger['status']='rejected';ledger['complete']=False;break
                    if wdelta or witness_paths:ledger['status']='witness';break
                    if exhausted:ledger['status']='all_declared_slices_exhausted';ledger['complete']=True;break
                    if report['status']=='timeout':ledger['status']='timeout';break
                except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
                    if 'accepted_sha256' in item:
                        item['published_unaccepted_sha256']=item.pop('accepted_sha256')
                    elif isinstance(report,dict) and report.get('published_checkpoint_sha256'):
                        item['published_unaccepted_sha256']=report['published_checkpoint_sha256']
                    item.update(status='rejected',error=f'{type(exc).__name__}: {exc}')
                    ledger['current_accepted_sha256']=item['expected_sha256']
                    ledger['status']='rejected';ledger['complete']=False;break
            else:ledger['status']='invocation_limit'
            if not sources_stable():ledger['status']='source_changed';ledger['complete']=False
            if interrupted:ledger['status']='cancelled';ledger['complete']=False
            if time.monotonic()-started>=aggregate_seconds:ledger['status']='aggregate_deadline';ledger['complete']=False
            publish()
            marker_status='rejected' if ledger['status'] in ('rejected','cancelled','aggregate_deadline','source_changed') else 'closed'
            guard.atomic(chain_marker,encode({'status':marker_status,'ledger':str(ledger_path),
                                             'current_accepted_sha256':ledger['current_accepted_sha256']}))
            # Receipt and marker writes can themselves cross a gate. Recheck
            # after both; a corrective write still has an unavoidable tail.
            if marker_status=='closed' and (interrupted or time.monotonic()-started>=aggregate_seconds or not sources_stable()):
                if ledger['invocations'] and ledger['invocations'][-1]['status']=='accepted':
                    last=ledger['invocations'][-1]
                    last['published_unaccepted_sha256']=last.pop('accepted_sha256')
                    last.update(status='rejected',error='post-terminal-publication acceptance check failed')
                    ledger['current_accepted_sha256']=last['expected_sha256']
                ledger['status']='rejected';ledger['complete']=False
                publish()
                guard.atomic(chain_marker,encode({'status':'rejected','ledger':str(ledger_path),
                                                 'current_accepted_sha256':ledger['current_accepted_sha256']}))
            return ledger
    finally:signal.signal(signal.SIGTERM,old)


def main(argv=None,started=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--expected-sha256',required=True);p.add_argument('--ledger-dir',type=Path,required=True)
    p.add_argument('--max-nodes',type=int,required=True);p.add_argument('--invocation-seconds',type=float,default=30)
    p.add_argument('--rss-mib',type=float,default=256);p.add_argument('--seconds',type=float,default=900,help='aggregate chain ceiling')
    p.add_argument('--max-invocations',type=int,default=26);p.add_argument('--deficit',type=int,action='append');p.add_argument('--diagonal',type=int,action='append')
    a=p.parse_args(argv)
    effective_started=(MODULE_STARTED if argv is None else time.monotonic()) if started is None else started
    try:r=run(a.n,a.checkpoint,a.expected_sha256,a.ledger_dir,max_nodes=a.max_nodes,deficits=a.deficit,diagonals=a.diagonal,seconds=a.invocation_seconds,rss_mib=a.rss_mib,aggregate_seconds=a.seconds,max_invocations=a.max_invocations,started=effective_started)
    except (OSError,ValueError) as exc:p.error(str(exc))
    print(json.dumps(r,sort_keys=True));return 0 if r['status'] in ('invocation_limit','reservation_limit','witness','timeout','all_declared_slices_exhausted') else 2


if __name__=='__main__':sys.exit(main())
