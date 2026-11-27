"""Bounded resumable fast diagonal DFS with an externally pinned checkpoint hash.

Checkpoints represent the DFS stack, not an exponentially materialized tree.
Each invocation atomically publishes one frontier; aborted invocations replay
from the last published checkpoint, so witness callbacks must be idempotent.
Exclusive checkpoint ownership is required.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.diagonal_secant_dfs_fast import SecantState, pair_orbits, mirror_pair_admissible
from src.verify import verify_certificate, verify_certificate_bruteforce

SOURCES = {'checkpoint':Path(__file__).resolve(), 'fast_core':ROOT/'research/diagonal_secant_dfs_fast.py',
           'original_core':ROOT/'research/diagonal_secant_dfs.py', 'verifier':ROOT/'src/verify.py'}


def sha(data): return hashlib.sha256(data).hexdigest()
def source_hashes(): return {k:sha(p.read_bytes()) for k,p in SOURCES.items()}
def encode(value): return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def atomic(path, payload):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.'+path.name+'.')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(payload); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _indices(values, n):
    values = list(range(n)) if values is None else list(values)
    if not values or len(values) != len(set(values)) or any(type(i) is not int or not 0<=i<n for i in values):
        raise ValueError('invalid slice indices')
    return sorted(values)


def _candidates(state, selected, orbits, byrow, deadline=None):
    sums = {x+y for x,y in state.points}; options = []
    for row in range(state.n):
        if deadline is not None and time.monotonic()>=deadline: raise TimeoutError
        if state.rows[row] >= state.target[row]: continue
        viable = []
        for idx in byrow[row]:
            if deadline is not None and time.monotonic()>=deadline: raise TimeoutError
            if idx not in selected and mirror_pair_admissible(state,orbits[idx],sums): viable.append(idx)
        options.append((len(viable),row,viable))
    return None if not options else min(options,key=lambda x:(x[0],x[1]))[2]


def run(n, seconds, max_nodes, checkpoint, *, expected_sha256=None, deficits=None, diagonals=None, on_witness=None):
    if type(n) is not int or n<2: raise ValueError('n must be integer >=2')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0: raise ValueError('invalid seconds')
    if type(max_nodes) is not int or max_nodes<1: raise ValueError('invalid node limit')
    started=time.monotonic(); deadline=started+seconds
    ds=_indices(deficits,n); ts=_indices(diagonals,n)
    orbits=pair_orbits(n); byrow=[[] for _ in range(n)]
    for i,orbit in enumerate(orbits):
        for row in sorted({p[1] for p in orbit}): byrow[row].append(i)
    identity={'format':'diagonal-fast-dfs-frontier-v1','n':n,'deficits':ds,'diagonals':ts,
              'source_hashes':source_hashes(), 'orbit_order_sha256':sha(encode(orbits)),
              'branch_order':'mrv-row-ascending-tie-orbit-order-v1'}
    slices=[(d,t) for d in ds for t in ts]
    checkpoint=Path(checkpoint)
    if checkpoint.exists():
        raw=checkpoint.read_bytes()
        if expected_sha256 is None or sha(raw)!=expected_sha256: raise ValueError('checkpoint hash missing or mismatched')
        data=json.loads(raw)
        if data.get('identity')!=identity: raise ValueError('checkpoint identity mismatch')
    else:
        if expected_sha256 is not None: raise ValueError('checkpoint missing')
        data={'identity':identity,'slice_index':0,'frames':[{'orbit':None,'next':None}],
              'nodes':0,'witness_visits':0,'slice_counts':[[0,0] for _ in slices]}
    index=data.get('slice_index'); frames=data.get('frames'); counts=data.get('slice_counts')
    if (type(index) is not int or not 0<=index<=len(slices) or not isinstance(frames,list) or
        not isinstance(counts,list) or len(counts)!=len(slices) or
        any(not isinstance(c,list) or len(c)!=2 or any(type(v) is not int or v<0 for v in c) for c in counts) or
        type(data.get('nodes')) is not int or type(data.get('witness_visits')) is not int or
        sum(c[0] for c in counts)!=data['nodes'] or sum(c[1] for c in counts)!=data['witness_visits'] or
        any(c != [0,0] for c in counts[index+1:])): raise ValueError('invalid checkpoint counters')
    if (index==len(slices)) != (not frames): raise ValueError('invalid checkpoint frontier')
    state=None;selected=set(); candidates=[]
    def restore():
        nonlocal state, selected, candidates
        if index==len(slices): return
        d,t=slices[index];state=SecantState(n,d)
        if not state.push(((t,t),)): raise ValueError('invalid root')
        selected=set();candidates=[]
        for pos,frame in enumerate(frames):
            if not isinstance(frame,dict) or set(frame)!={'orbit','next'}: raise ValueError('invalid frame')
            orbit, cursor=frame['orbit'], frame['next']
            if pos==0:
                if orbit is not None: raise ValueError('invalid root frame')
            else:
                if candidates[-1] is None or type(orbit) is not int or orbit in selected or orbit not in candidates[-1]: raise ValueError('invalid path')
                parent=frames[pos-1]
                if parent['next'] is None or parent['next']<1 or candidates[-1][parent['next']-1]!=orbit: raise ValueError('invalid branch cursor')
                if not state.push(orbits[orbit]): raise ValueError('invalid insertion')
                selected.add(orbit)
            if cursor is None:
                if pos!=len(frames)-1: raise ValueError('pending node must be leaf of stack')
                candidates.append(None)
            else:
                viable=_candidates(state,selected,orbits,byrow)
                if viable is None or type(cursor) is not int or not 0<=cursor<=len(viable): raise ValueError('invalid cursor')
                candidates.append(viable)
    restore()
    def pop_frame():
        frame=frames.pop();candidates.pop()
        if frame['orbit'] is not None:
            selected.remove(frame['orbit']);state.pop()
    nodes_this_run=0;status=None
    while index<len(slices):
        if not frames:
            index+=1;data['slice_index']=index
            if index==len(slices): break
            frames.append({'orbit':None,'next':None});restore()
        frame=frames[-1]
        if frame['next'] is not None and frame['next']==len(candidates[-1]):
            pop_frame();continue
        if frame['next'] is None:
            if time.monotonic()>=deadline: status='timeout';break
            if nodes_this_run>=max_nodes: status='node_limit';break
            try: viable=_candidates(state,selected,orbits,byrow,deadline)
            except TimeoutError: status='timeout';break
            if viable is None:
                d,t=slices[index];points=sorted(state.points)
                if state.columns!=state.target or len(points)!=2*n-1 or {(y,x) for x,y in points}!=set(points):
                    raise RuntimeError('full state invariant failed')
                cert={'n':n,'points':[list(p) for p in points], 'metadata':{'method':'diagonal_secant_checkpoint','deficit':d,'diagonal':t,'novelty_claim':False}}
                checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                if not all(c['valid'] and c['point_count']==2*n-1 for c in checks):raise RuntimeError('witness verification failed')
                cert['metadata']['normalized_sha256']=checks[0]['normalized_sha256']
                if on_witness:on_witness(cert)
                data['witness_visits']+=1;counts[index][1]+=1
            data['nodes']+=1;counts[index][0]+=1;nodes_this_run+=1
            if viable is None: pop_frame()
            else: frame['next']=0;candidates[-1]=viable
            continue
        idx=candidates[-1][frame['next']];frame['next']+=1
        if not state.push(orbits[idx]): raise RuntimeError('candidate invariant failed')
        selected.add(idx);frames.append({'orbit':idx,'next':None});candidates.append(None)
    if source_hashes()!=identity['source_hashes']: raise ValueError('sources changed during traversal')
    if expected_sha256 is not None:
        if not checkpoint.exists() or sha(checkpoint.read_bytes())!=expected_sha256: raise ValueError('checkpoint changed during traversal')
    elif checkpoint.exists(): raise ValueError('checkpoint appeared during traversal')
    if status is None and time.monotonic()>=deadline: status='timeout'
    data['previous_checkpoint_sha256']=expected_sha256
    payload=encode(data);atomic(checkpoint,payload)
    return {'status':status or 'all_declared_slices_exhausted','checkpoint_sha256':sha(payload),
            'nodes_this_run':nodes_this_run,'nodes_total':data['nodes'],'witness_visits_total':data['witness_visits'],
            'slice_index':index,'slice_counts':counts,'scope':'Only declared diagonal-reflection slices; no unrestricted infeasibility conclusion.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,required=True);p.add_argument('--seconds',type=float,required=True)
    p.add_argument('--max-nodes',type=int,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--expected-sha256');p.add_argument('--deficit',type=int,action='append');p.add_argument('--diagonal',type=int,action='append')
    p.add_argument('--witness-directory',type=Path,required=True)
    a=p.parse_args(argv);a.witness_directory.mkdir(parents=True,exist_ok=True)
    def save(cert):
        path=a.witness_directory/(cert['metadata']['normalized_sha256']+'.json')
        atomic(path,encode(cert))
    result=run(a.n,a.seconds,a.max_nodes,a.checkpoint,expected_sha256=a.expected_sha256,deficits=a.deficit,diagonals=a.diagonal,on_witness=save)
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':sys.exit(main())
