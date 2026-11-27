"""Owned-process guard for the checkpointed diagonal row-batch DFS.

Checkpoint ownership is exclusive. Only a clean guarded worker may publish its
private frontier as the accepted checkpoint. Witnesses are independent, atomic,
and may be saved even when the invocation's frontier is rejected.
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
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.owned_process_guard import guarded_process
from research.diagonal_secant_checkpoint import atomic, encode, sha
from research.diagonal_rowbatch_checkpoint import MAX_CHECKPOINT_BYTES
from src.verify import verify_certificate, verify_certificate_bruteforce

SOURCES={'checkpoint_core':ROOT/'research/diagonal_rowbatch_checkpoint.py',
         'checkpoint_utilities':ROOT/'research/diagonal_secant_checkpoint.py',
         'tiny_reference':ROOT/'research/diagonal_rowbatch_tiny.py',
         'fast_core':ROOT/'research/diagonal_secant_dfs_fast.py',
         'original_core':ROOT/'research/diagonal_secant_dfs.py',
         'verifier':ROOT/'src/verify.py', 'helper':ROOT/'research/owned_process_guard.py',
         'guard':Path(__file__).resolve(), 'entrypoint':ROOT/'src/lazy_sat.py'}


def hashes(): return {k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in SOURCES.items()}


def read_frontier(path):
    with Path(path).open('rb') as stream:payload=stream.read(MAX_CHECKPOINT_BYTES+1)
    if len(payload)>MAX_CHECKPOINT_BYTES:raise ValueError('checkpoint exceeds size limit')
    return payload


def worker(job):
    if hashes()!=job['source_hashes']: raise ValueError('source changed before search')
    from research.diagonal_rowbatch_checkpoint import run
    def witness(cert):
        if hashes()!=job['source_hashes']: raise ValueError('source changed before witness')
        checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
        if not all(c['valid'] and c['point_count']==2*job['n']-1 for c in checks):raise ValueError('invalid witness')
        if checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']:raise ValueError('witness hash mismatch')
        cert['metadata']['guard_source_hashes']=job['source_hashes']
        atomic(Path(job['witness_dir'])/(checks[0]['normalized_sha256']+'.json'),encode(cert))
    result=run(job['n'],job['cooperative_seconds'],job['max_nodes'],job['staged_checkpoint'],
               expected_sha256=job['expected_sha256'],deficits=job['deficits'],diagonals=job['diagonals'],on_witness=witness)
    if hashes()!=job['source_hashes']: raise ValueError('source changed after search')
    atomic(job['worker_result'],encode(result))


def run(n,seconds,rss_mib,max_nodes,checkpoint,output,*,expected_sha256=None,deficits=None,diagonals=None,started=None):
    started=time.monotonic() if started is None else started
    if type(n) is not int or not 2<=n<=79:raise ValueError('n must be in [2,79]')
    if isinstance(seconds,bool) or not isinstance(seconds,(float,int)) or not math.isfinite(seconds) or not 1 < seconds <= 30:raise ValueError('seconds must be in (1,30]')
    if isinstance(rss_mib,bool) or not isinstance(rss_mib,(float,int)) or not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:raise ValueError('rss-mib must be in (0,256]')
    if type(max_nodes) is not int or max_nodes<1:raise ValueError('max-nodes must be positive')
    for indices in (deficits,diagonals):
        if indices is not None and (not indices or len(set(indices))!=len(indices) or any(type(i) is not int or not 0<=i<n for i in indices)):raise ValueError('invalid slice indices')
    checkpoint=Path(checkpoint).resolve();output=Path(output).resolve()
    lockpath=checkpoint.with_name(checkpoint.name+'.lock')
    protected={path.resolve() for path in SOURCES.values()}
    if checkpoint==output or output==lockpath or checkpoint in protected or output in protected:raise ValueError('conflicting output paths')
    checkpoint.parent.mkdir(parents=True,exist_ok=True);output.parent.mkdir(parents=True,exist_ok=True)
    interrupted=False
    def term(signum,frame):
        nonlocal interrupted
        interrupted=True
    import signal
    old=signal.signal(signal.SIGTERM,term)
    try:
        with open(lockpath,'a+b') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('checkpoint is already owned')
            if checkpoint.exists():
                original=read_frontier(checkpoint)
                if expected_sha256 is None or sha(original)!=expected_sha256:raise ValueError('checkpoint hash missing or mismatched')
            else:
                if expected_sha256 is not None:raise ValueError('checkpoint missing')
                original=None
            sources=hashes()
            witness_dir=Path(tempfile.mkdtemp(prefix=output.name+'.witnesses-',dir=output.parent))
            report={'status':'incomplete','complete':False,'accepted_checkpoint_sha256':None,
                    'published_checkpoint_sha256':None,
                    'previous_checkpoint_sha256':expected_sha256,'source_hashes':sources,'witness_dir':str(witness_dir),
                    'n':n,'seconds_limit':seconds,'rss_limit_mib':rss_mib,'max_nodes':max_nodes,
                    'scope':'Declared diagonal-reflection slices only; no unrestricted infeasibility conclusion.'}
            atomic(output,encode(report))
            with tempfile.TemporaryDirectory(prefix='rowbatch-checkpoint-worker-') as tmp:
                tmp=Path(tmp);staged=tmp/'frontier.json';worker_result=tmp/'result.json';log=tmp/'worker.log'
                if original is not None:atomic(staged,original)
                remaining=seconds-(time.monotonic()-started)
                # Reserve at least one second, or one quarter of the remaining
                # time, for worker checkpoint publication and guard cleanup.
                reserve=max(1.0,remaining*.25)
                cooperative=remaining-reserve
                if interrupted:gate={'gate_status':'cancelled','cleanup_status':'not_launched','returncode':None}
                elif cooperative<=0:gate={'gate_status':'wall_limit','cleanup_status':'not_launched','returncode':None}
                else:
                    job={'n':n,'cooperative_seconds':cooperative,'max_nodes':max_nodes,'deficits':deficits,
                         'diagonals':diagonals,'staged_checkpoint':str(staged),'expected_sha256':expected_sha256,
                         'worker_result':str(worker_result),'source_hashes':sources,'witness_dir':str(witness_dir)}
                    atomic(tmp/'job.json',encode(job))
                    remaining=seconds-(time.monotonic()-started)
                    if remaining<=0:gate={'gate_status':'wall_limit','cleanup_status':'not_launched','returncode':None}
                    else:gate=guarded_process([sys.executable,str(Path(__file__).resolve()),'--_worker',str(tmp/'job.json')],remaining,rss_mib,log,cancelled=lambda:interrupted)
                reason=None if gate.get('gate_status')=='exited' and gate.get('cleanup_status')=='clean' and gate.get('returncode')==0 else gate.get('gate_status','guard_error')
                if gate.get('gate_status')=='exited' and gate.get('cleanup_status')!='clean':reason='cleanup_error'
                elif gate.get('gate_status')=='exited' and gate.get('returncode')!=0:reason='worker_error'
                stable=hashes()==sources
                if reason is None and not stable:reason='source_changed'
                if reason is None and interrupted:reason='cancelled'
                if reason is None and time.monotonic()-started>=seconds:reason='wall_limit'
                report['guard']=dict(gate,source_stable=stable)
                if worker_result.exists():report['worker_result']=json.loads(worker_result.read_text())
                result=report.get('worker_result')
                if (reason is None and expected_sha256 is not None and isinstance(result,dict) and
                    result.get('status')=='timeout' and result.get('nodes_this_run')==0 and
                    result.get('checkpoint_sha256')==expected_sha256 and staged.exists() and sha(read_frontier(staged))==expected_sha256):
                    reason='reconstruction_timeout'
                if reason is None:
                    payload=read_frontier(staged)
                    if not isinstance(result,dict) or sha(payload)!=result.get('checkpoint_sha256'):raise ValueError('worker checkpoint/result mismatch')
                    if result.get('status') not in ('timeout','node_limit','all_declared_slices_exhausted'):raise ValueError('invalid worker status')
                    data=json.loads(payload);identity=data.get('identity',{})
                    from research.diagonal_rowbatch_checkpoint import source_hashes as core_hashes
                    from research.diagonal_secant_dfs_fast import pair_orbits
                    ds=list(range(n)) if deficits is None else sorted(deficits)
                    ts=list(range(n)) if diagonals is None else sorted(diagonals)
                    if (identity!={'format':'diagonal-rowbatch-frontier-v1','n':n,'deficits':ds,'diagonals':ts,
                                   'source_hashes':core_hashes(),'orbit_order_sha256':sha(encode(pair_orbits(n))),
                                   'branch_order':'minimum-viable-row-then-lexicographic-unordered-batch-v1'} or
                        data.get('previous_checkpoint_sha256')!=expected_sha256 or
                        data.get('nodes')!=result.get('nodes_total') or
                        data.get('witness_visits')!=result.get('witness_visits_total') or
                        data.get('slice_index')!=result.get('slice_index') or
                        data.get('slice_counts')!=result.get('slice_counts') or
                        (result['status']=='all_declared_slices_exhausted' and
                         (data['slice_index']!=len(ds)*len(ts) or data.get('frames')!=[]))):
                        raise ValueError('worker identity or frontier mismatch')
                    if original is None:
                        if checkpoint.exists():raise ValueError('checkpoint appeared during run')
                    elif not checkpoint.exists() or sha(read_frontier(checkpoint))!=expected_sha256:raise ValueError('checkpoint changed during run')
                    atomic(checkpoint,payload)
                    report['published_checkpoint_sha256']=sha(payload)
                    report['accepted_checkpoint_sha256']=report['published_checkpoint_sha256']
                    report['status']=result['status'];report['complete']=result['status']=='all_declared_slices_exhausted'
                    if hashes()!=sources:
                        report['status']='source_changed';report['complete']=False;report['accepted_checkpoint_sha256']=None
                        report['guard']['source_stable']=False
                    elif interrupted:
                        report['status']='cancelled';report['complete']=False;report['accepted_checkpoint_sha256']=None
                    elif time.monotonic()-started>=seconds:
                        report['status']='wall_limit';report['complete']=False;report['accepted_checkpoint_sha256']=None
                else:report['status']=reason
                report['elapsed_seconds']=time.monotonic()-started
                report['worker_log_tail']=log.read_bytes()[-4096:].decode(errors='replace') if log.exists() else ''
            def reject_late():
                if report['accepted_checkpoint_sha256'] is None:return
                try: stable=hashes()==sources
                except OSError: stable=False
                reason=('source_changed' if not stable else 'cancelled' if interrupted else
                        'wall_limit' if time.monotonic()-started>=seconds else None)
                if reason:
                    report.update(status=reason,complete=False,accepted_checkpoint_sha256=None)
                    report['guard']['source_stable']=stable
            reject_late()
            report['elapsed_seconds']=time.monotonic()-started
            atomic(output,encode(report))
            reject_late()
            if report['accepted_checkpoint_sha256'] is None and report['published_checkpoint_sha256'] is not None:
                report['elapsed_seconds']=time.monotonic()-started
                atomic(output,encode(report))
            return report
    finally:signal.signal(signal.SIGTERM,old)


def main(argv=None,started=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if len(args)==2 and args[0]=='--_worker':worker(json.loads(Path(args[1]).read_text()));return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,required=True);p.add_argument('--seconds',type=float,default=30)
    p.add_argument('--rss-mib',type=float,default=256);p.add_argument('--max-nodes',type=int,required=True)
    p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--expected-sha256');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--deficit',type=int,action='append');p.add_argument('--diagonal',type=int,action='append')
    a=p.parse_args(args)
    start=(MODULE_STARTED if argv is None else time.monotonic()) if started is None else started
    try:r=run(a.n,a.seconds,a.rss_mib,a.max_nodes,a.checkpoint,a.output,expected_sha256=a.expected_sha256,deficits=a.deficit,diagonals=a.diagonal,started=start)
    except (ValueError,OSError) as exc:p.error(str(exc))
    print(json.dumps(r,sort_keys=True));return 0 if r['status'] in ('timeout','node_limit','all_declared_slices_exhausted') and r['accepted_checkpoint_sha256'] else 2


if __name__=='__main__':sys.exit(main())
