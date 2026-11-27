"""Standalone owned-worker root scan; no DFS, checkpoint or continuation.

Source supports n2..79; each actual-host allocation requires separate approval.
One declared root, one complete residual scan, and control order if passing.
"""
import time
MODULE_STARTED=time.monotonic()
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import diagonal_residual_checkpoint as residual
from research import diagonal_rowbatch_checkpoint as control
from research.diagonal_secant_dfs_fast import SecantState,pair_orbits
from research.diagonal_secant_checkpoint import atomic,encode,sha
from research.owned_process_guard import guarded_process

SCHEMA='diagonal-residual-root-preflight-v1'
POLICY='residual-row-degree-component-parity-bipartite-sum-v1'
ORDER='minimum-viable-row-then-lexicographic-unordered-batch-v1'
MAX_JSON=16384
SOURCES=dict(residual.SOURCES,control=ROOT/'research/diagonal_rowbatch_checkpoint.py',
             helper=ROOT/'research/owned_process_guard.py',preflight=Path(__file__).resolve(),
             entrypoint=Path(__file__).resolve())


def require(ok,message):
    if not ok:raise ValueError(message)


def check(deadline,cancelled=lambda:False):
    if cancelled():raise InterruptedError('cancelled')
    if time.monotonic()>=deadline:raise TimeoutError('deadline')


def sources(deadline=float('inf'),cancelled=lambda:False):
    result={}
    for name,path in SOURCES.items():
        check(deadline,cancelled)
        with path.open('rb') as stream:data=stream.read(1_000_001)
        require(len(data)<=1_000_000,'source too large')
        result[name]=sha(data)
    check(deadline,cancelled)
    return result


def read_bytes(path,limit=MAX_JSON):
    with Path(path).open('rb') as stream:data=stream.read(limit+1)
    require(len(data)<=limit,'artifact too large')
    return data


def decode(data):
    require(len(data)<=MAX_JSON,'JSON too large')
    # Bound parser nesting without interpreting strings as structure.
    depth=0;quoted=False;escaped=False
    for byte in data:
        if quoted:
            if escaped:escaped=False
            elif byte==92:escaped=True
            elif byte==34:quoted=False
        elif byte==34:quoted=True
        elif byte in (91,123):
            depth+=1;require(depth<=5,'JSON too deep')
        elif byte in (93,125):depth-=1
    def pairs(items):
        obj={}
        for key,value in items:
            require(key not in obj,'duplicate JSON key');obj[key]=value
        return obj
    def constant(value):raise ValueError('nonfinite JSON')
    return json.loads(data,object_pairs_hook=pairs,parse_constant=constant)


def grid(n,d,t):
    require(type(n) is int and 2<=n<=79,'n outside2..79')
    require(all(type(i) is int and 0<=i<n for i in (d,t)),'invalid root slice')


def snapshot(state):
    return (tuple(state.points),tuple(sorted(state.occupied)),tuple(state.rows),
            tuple(state.columns),tuple(state.blocked),tuple(state.frames),tuple(state.target))


def scan_root(n,d,t,deadline,cancelled=lambda:False):
    """No DFS or run call: create singleton root and scan exactly once."""
    grid(n,d,t);check(deadline,cancelled)
    state=SecantState(n,d);require(state.push(((t,t),)),'root insertion failed')
    check(deadline,cancelled);orbits=pair_orbits(n);before=snapshot(state)
    work=residual.new_work();scan_started=time.monotonic()
    needs,available,degrees,failures=residual.residual_scan(state,set(),orbits,deadline,work)
    check(deadline,cancelled)
    scan_seconds=time.monotonic()-scan_started
    require(snapshot(state)==before,'scan mutated root')
    row=None;viable=[];batches=[];compared=False;comparison_started=time.monotonic()
    if not failures:
        row=min((r for r in range(n) if needs[r]),key=lambda r:(degrees[r],r))
        for index,present in enumerate(available):
            check(deadline,cancelled);residual.bump(work,'candidate_orbit_tests')
            if present and row in orbits[index][0]:viable.append(index)
        for batch in itertools.combinations(viable,needs[row]):
            check(deadline,cancelled);batches.append(batch)
        byrow=[[] for _ in range(n)]
        for index,orbit in enumerate(orbits):
            check(deadline,cancelled)
            for r in orbit[0]:byrow[r].append(index)
        expected=control.candidates(state,set(),orbits,byrow,deadline)
        check(deadline,cancelled)
        require(expected==batches,'control candidate order mismatch');compared=True
    require(snapshot(state)==before,'control comparison mutated root')
    check(deadline,cancelled)
    return {'n':n,'deficit':d,'diagonal':t,'prefix_points':[[t,t]],'nodes':0,
            'search_performed':False,'orbit_order_sha256':sha(encode(orbits)),
            'root_state_sha256':sha(encode(before)),'prune_policy':POLICY,'branch_order':ORDER,
            'needs':list(needs),'degrees':degrees,'available_count':sum(available),
            'available_sha256':sha(bytes(available)),'violations':list(failures),
            'chosen_row':row,'viable_ids':viable,'batch_count':len(batches),
            'ordered_batches_sha256':sha(encode(batches)),'control_compared':compared,
            'state_unchanged':True,'physical_work':work,'scan_seconds':scan_seconds,
            'comparison_seconds':time.monotonic()-comparison_started}


def validate_job(job):
    require(type(job) is dict and set(job)=={'schema','n','deficit','diagonal','deadline',
            'invocation_started','seconds','source_hashes'},'invalid job keys')
    require(job['schema']==SCHEMA,'job schema mismatch');grid(job['n'],job['deficit'],job['diagonal'])
    for field in ('deadline','invocation_started','seconds'):
        require(type(job[field]) in (int,float) and math.isfinite(job[field]),'invalid timing')
    require(2<job['seconds']<=30 and 0<job['deadline']-job['invocation_started']<=job['seconds']-1,
            'invalid worker deadline')
    require(type(job['source_hashes']) is dict and set(job['source_hashes'])==set(SOURCES),
            'job source keys mismatch')
    require(all(type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
                for v in job['source_hashes'].values()),'invalid source digest')


def worker(path,expected_sha):
    path=Path(path);raw=read_bytes(path);require(sha(raw)==expected_sha,'job digest mismatch')
    job=decode(raw);validate_job(job);cancelled=[False]
    def term(signum,frame):cancelled[0]=True
    old={sig:signal.signal(sig,term) for sig in (signal.SIGTERM,signal.SIGINT)}
    try:
        deadline=job['deadline'];stop=lambda:cancelled[0]
        require(sources(deadline,stop)==job['source_hashes'],'source changed before scan')
        result=scan_root(job['n'],job['deficit'],job['diagonal'],deadline,stop)
        require(sources(deadline,stop)==job['source_hashes'],'source changed after scan')
        report={'schema':SCHEMA,'job_sha256':expected_sha,'source_hashes':job['source_hashes'],
                'result':result}
        payload=encode(report);require(len(payload)<=MAX_JSON,'worker report too large')
        check(deadline,stop);atomic(path.parent/'worker.json',payload);check(deadline,stop)
        return report
    finally:
        for sig,handler in old.items():signal.signal(sig,handler)


def validate_result(report,job,job_sha):
    require(type(report) is dict and set(report)=={'schema','job_sha256','source_hashes','result'},
            'invalid report keys')
    require(report['schema']==SCHEMA and report['job_sha256']==job_sha and
            report['source_hashes']==job['source_hashes'],'report binding mismatch')
    r=report['result'];n=job['n'];edges=n*(n-1)//2
    keys={'n','deficit','diagonal','prefix_points','nodes','search_performed','orbit_order_sha256',
          'root_state_sha256','prune_policy','branch_order','needs','degrees','available_count',
          'available_sha256','violations','chosen_row','viable_ids','batch_count',
          'ordered_batches_sha256','control_compared','state_unchanged','physical_work',
          'scan_seconds','comparison_seconds'}
    require(type(r) is dict and set(r)==keys,'invalid result keys')
    require(all(type(r[k]) is int and r[k]==job[k] for k in ('n','deficit','diagonal')),
            'root declaration mismatch')
    require(r['prefix_points']==[[job['diagonal'],job['diagonal']]] and
            all(type(v) is int for v in r['prefix_points'][0]) and type(r['nodes']) is int and
            r['nodes']==0 and r['search_performed'] is False and r['state_unchanged'] is True,
            'root-only invariant mismatch')
    require(r['prune_policy']==POLICY and r['branch_order']==ORDER,'policy mismatch')
    for key in ('orbit_order_sha256','root_state_sha256','available_sha256','ordered_batches_sha256'):
        require(type(r[key]) is str and len(r[key])==64 and all(c in '0123456789abcdef' for c in r[key]),
                'invalid result digest')
    expected_needs=[2-(i==job['deficit'])-(i==job['diagonal']) for i in range(n)]
    require(r['needs']==expected_needs and all(type(v) is int for v in r['needs']),'root needs mismatch')
    require(type(r['degrees']) is list and len(r['degrees'])==n and
            all(type(v) is int and 0<=v<n for v in r['degrees']),'invalid degrees')
    require(type(r['available_count']) is int and 0<=r['available_count']<=edges and
            sum(r['degrees'])==2*r['available_count'],'invalid edge count')
    require(type(r['violations']) is list and r['violations']==[v for v in residual.RULES if v in r['violations']],
            'invalid violations')
    work=r['physical_work']
    require(type(work) is dict and set(work)==set(residual.new_work()) and
            all(type(v) is int and 0<=v<=residual.MAX_U64 for v in work.values()),'invalid work counters')
    require(work['scan_attempts']==work['completed_scans']==1 and work['edge_tests']==edges,
            'not exactly one complete residual scan')
    require(all(work[v]==int(v in r['violations']) for v in residual.RULES),'rule counters mismatch')
    require(type(r['batch_count']) is int and 0<=r['batch_count']<=3003,'invalid batch count')
    if r['violations']:
        require(r['chosen_row'] is None and r['viable_ids']==[] and r['batch_count']==0 and
                r['control_compared'] is False and work['candidate_orbit_tests']==0,'rejected scan compared')
    else:
        row=min((i for i in range(n) if expected_needs[i]),key=lambda i:(r['degrees'][i],i))
        require(type(r['chosen_row']) is int and r['chosen_row']==row and r['control_compared'] is True,
                'passing scan not control-compared')
        ids=r['viable_ids']
        require(type(ids) is list and len(ids)==r['degrees'][row] and
                all(type(v) is int and 0<=v<edges for v in ids) and ids==sorted(set(ids)),
                'invalid chosen domain')
        require(r['batch_count']==math.comb(len(ids),expected_needs[row]) and
                work['candidate_orbit_tests']==edges,'domain size mismatch')
    for key in ('scan_seconds','comparison_seconds'):
        require(type(r[key]) in (int,float) and math.isfinite(r[key]) and r[key]>=0,'invalid duration')
    return r


def run(n,d,t,seconds,rss_mib,out,*,started=None):
    started=time.monotonic() if started is None else started
    grid(n,d,t)
    require(type(seconds) in (int,float) and math.isfinite(seconds) and 2<seconds<=30,'seconds outside(2,30]')
    require(type(rss_mib) in (int,float) and math.isfinite(rss_mib) and 0<rss_mib<=256,'RSS outside(0,256]')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    cancelled=[False]
    def term(signum,frame):cancelled[0]=True
    old={sig:signal.signal(sig,term) for sig in (signal.SIGTERM,signal.SIGINT)}
    report={'schema':SCHEMA,'status':'incomplete','accepted':False,'accepted_scan':None,
            'n':n,'deficit':d,'diagonal':t,'nodes':0,'search_performed':False,
            'complete':False,'seconds_limit':seconds,'rss_limit_mib':rss_mib,
            'acceptance_requires':'Successful supervisor exit plus accepted report and unchanged pinned sources.',
            'timing_scope':'elapsed_seconds ends before final report write; returned invocation_seconds includes report durability and signal restoration, excluding summary emission.',
            'scope':'One declared root operation only; no DFS, continuation or exhaustion claim.'}
    source_hashes=None
    try:
        deadline=started+seconds;stop=lambda:cancelled[0]
        source_hashes=sources(deadline,stop);report['source_hashes']=source_hashes
        job={'schema':SCHEMA,'n':n,'deficit':d,'diagonal':t,'deadline':deadline-1,
             'invocation_started':started,'seconds':seconds,'source_hashes':source_hashes}
        payload=encode(job);validate_job(job);job_sha=sha(payload);report['job_sha256']=job_sha
        atomic(out/'job.json',payload);check(deadline,stop)
        remaining=deadline-time.monotonic()
        gate=guarded_process([sys.executable,str(Path(__file__).resolve()),'--_worker',
                              str(out/'job.json'),job_sha],remaining,rss_mib,out/'worker.log',cancelled=stop)
        report['guard']=gate
        require(gate.get('gate_status')=='exited' and gate.get('returncode')==0 and
                gate.get('cleanup_status')=='clean' and not gate.get('monitor_error') and
                not gate.get('cleanup_error'),'helper gate rejected')
        require(type(gate.get('rss_samples')) is int and gate['rss_samples']>0 and
                type(gate.get('cleanup_samples')) is int and gate['cleanup_samples']>0,
                'missing resource/cleanup samples')
        require(0<gate['peak_sampled_rss_kib']<=rss_mib*1024 and
                0<gate['seconds_limit']<=remaining and gate['rss_limit_mib']==rss_mib and
                gate['elapsed_seconds']<gate['seconds_limit'],'resource limits failed')
        check(deadline,stop)
        raw=read_bytes(out/'worker.json');observed=decode(raw)
        report['worker_report_sha256']=sha(raw);report['worker_result']=observed
        accepted=validate_result(observed,job,job_sha)
        require(sources(deadline,stop)==source_hashes,'source changed after worker')
        log=read_bytes(out/'worker.log',65536);report['worker_log_tail']=log[-4096:].decode(errors='replace')
        check(deadline,stop)
        report.update(status='root_scan_accepted',accepted=True,accepted_scan=accepted)
    except Exception as exc:
        report.update(status='rejected',accepted=False,accepted_scan=None,error=f'{type(exc).__name__}: {exc}'[:512])
    finally:
        def reject_late():
            if not report['accepted']:return
            try:
                check(started+seconds,lambda:cancelled[0])
                require(sources(started+seconds,lambda:cancelled[0])==source_hashes,'late source change')
            except Exception as exc:
                report.update(status='rejected',accepted=False,accepted_scan=None,
                              error=f'{type(exc).__name__}: {exc}'[:512])
        try:
            reject_late();report['elapsed_seconds']=time.monotonic()-started
            atomic(out/'report.json',encode(report));was_accepted=report['accepted'];reject_late()
            if was_accepted and not report['accepted']:
                report['elapsed_seconds']=time.monotonic()-started;atomic(out/'report.json',encode(report))
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)
    return dict(report,invocation_seconds=time.monotonic()-started)


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if len(args)==3 and args[0]=='--_worker':worker(args[1],args[2]);return 0
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True);parser.add_argument('--deficit',type=int,required=True)
    parser.add_argument('--diagonal',type=int,required=True);parser.add_argument('--seconds',type=float,default=10)
    parser.add_argument('--rss-mib',type=float,default=256);parser.add_argument('--output-dir',type=Path,required=True)
    a=parser.parse_args(args)
    result=run(a.n,a.deficit,a.diagonal,a.seconds,a.rss_mib,a.output_dir,
               started=MODULE_STARTED if argv is None else time.monotonic())
    print(json.dumps(result,sort_keys=True));return 0 if result['accepted'] else 2


if __name__=='__main__':sys.exit(main())
