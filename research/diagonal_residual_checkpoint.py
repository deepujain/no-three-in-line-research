"""Checkpointable residual-bound row batches; separate fresh-genesis format.

A checkpoint is one DFS stack, never a materialized search tree. Resume requires
an externally trusted exact checkpoint hash and exclusive checkpoint ownership.
Callbacks must be idempotent: work since the previous publication can replay.
"""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.diagonal_secant_checkpoint import atomic,encode,sha
from research.diagonal_secant_dfs_fast import SecantState,pair_orbits,mirror_pair_admissible
from src.verify import verify_certificate,verify_certificate_bruteforce

SOURCES={'residual_checkpoint':Path(__file__).resolve(),
         'residual_tiny_reference':ROOT/'research/diagonal_residual_graph_tiny.py',
         'tiny_reference':ROOT/'research/diagonal_rowbatch_tiny.py',
         'checkpoint_utilities':ROOT/'research/diagonal_secant_checkpoint.py',
         'fast_core':ROOT/'research/diagonal_secant_dfs_fast.py',
         'original_core':ROOT/'research/diagonal_secant_dfs.py',
         'verifier':ROOT/'src/verify.py'}
MAX_N=79
MAX_CHECKPOINT_BYTES=1_000_000


def source_hashes():return {name:sha(path.read_bytes()) for name,path in SOURCES.items()}


def indices(values,n):
    if values is None:values=list(range(n))
    else:
        values=list(itertools.islice(values,n+1))
        if len(values)>n:raise ValueError('too many slice indices')
    if not values or any(type(i) is not int or not 0<=i<n for i in values) or len(set(values))!=len(values):raise ValueError('invalid slice indices')
    return sorted(values)


RULES = ('row_shortage', 'component_parity', 'bipartite_imbalance',
         'global_color_shortage', 'component_color_shortage')
MAX_U64 = (1 << 64)-1


def new_work():
    return dict.fromkeys(('scan_attempts', 'completed_scans', 'edge_tests',
                         'graph_steps', 'candidate_orbit_tests', *RULES), 0)


def bump(work, name):
    if work is not None:
        value = work[name]
        if type(value) is not int or not 0 <= value < MAX_U64:
            raise OverflowError('physical work counter overflow/type fault')
        work[name] = value+1


def check_deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError


def residual_scan(state, selected, orbits, deadline=None, work=None):
    """Complete canonical scan, then necessary bounds; scratch only.

    A timeout raises without returning any verdict. The caller supplies the
    coherent frozen reflection state; canonical orbit coverage is checked.
    """
    n = state.n
    if type(n) is not int or not 2 <= n <= MAX_N or type(state) is not SecantState:
        raise ValueError('bounded frozen reflection state required')
    if len(orbits) != n*(n-1)//2:
        raise ValueError('incomplete orbit declaration')
    check_deadline(deadline)
    needs = tuple(state.target[r]-state.rows[r] for r in range(n))
    if any(type(b) is not int or b not in (0, 1, 2) for b in needs) or sum(needs) % 2:
        raise RuntimeError('residual demand invariant failed')
    bump(work, 'scan_attempts')
    available = bytearray(len(orbits))
    degrees, neighbors = [0]*n, [0]*n
    if not any(needs):
        check_deadline(deadline)
        bump(work, 'completed_scans')
        return needs, available, degrees, ()
    sums, colors, index = {x+y for x, y in state.points}, 0, 0
    for x in range(n):
        for y in range(x+1, n):
            check_deadline(deadline)
            orbit = orbits[index]
            if orbit != ((x, y), (y, x)):
                raise ValueError('noncanonical/incomplete orbit declaration')
            bump(work, 'edge_tests')
            if index not in selected and mirror_pair_admissible(state, orbit, sums):
                if not needs[x] or not needs[y]:
                    raise RuntimeError('admissible edge has saturated endpoint')
                available[index] = 1
                degrees[x] += 1; degrees[y] += 1
                neighbors[x] |= 1 << y; neighbors[y] |= 1 << x
                colors |= 1 << (x+y)
            index += 1
    check_deadline(deadline)
    failures = set()
    if any(degrees[r] < needs[r] for r in range(n)):
        failures.add('row_shortage')
    if colors.bit_count() < sum(needs)//2:
        failures.add('global_color_shortage')
    component_of, sides = [-1]*n, [-1]*n
    demands, component_colors = [], []
    for root in range(n):
        check_deadline(deadline)
        if not needs[root] or component_of[root] != -1:
            continue
        component = len(demands)
        queue, totals, bipartite = [root], [0, 0], True
        component_of[root], sides[root] = component, 0
        while queue:
            check_deadline(deadline)
            bump(work, 'graph_steps')
            vertex = queue.pop()
            totals[sides[vertex]] += needs[vertex]
            remaining = neighbors[vertex]
            while remaining:
                check_deadline(deadline)
                bump(work, 'graph_steps')
                bit = remaining & -remaining
                remaining ^= bit
                adjacent = bit.bit_length()-1
                if component_of[adjacent] == -1:
                    component_of[adjacent] = component
                    sides[adjacent] = 1-sides[vertex]
                    queue.append(adjacent)
                elif sides[adjacent] == sides[vertex]:
                    bipartite = False
        demand = sum(totals)
        demands.append(demand); component_colors.append(0)
        if demand % 2:
            failures.add('component_parity')
        if bipartite and totals[0] != totals[1]:
            failures.add('bipartite_imbalance')
    for index, present in enumerate(available):
        check_deadline(deadline)
        if present:
            bump(work, 'graph_steps')
            x, y = orbits[index][0]
            component_colors[component_of[x]] |= 1 << (x+y)
    for demand, palette in zip(demands, component_colors):
        check_deadline(deadline)
        if demand % 2 == 0 and palette.bit_count() < demand//2:
            failures.add('component_color_shortage')
    check_deadline(deadline)
    bump(work, 'completed_scans')
    for rule in RULES:
        if rule in failures:
            bump(work, rule)
    return needs, available, degrees, tuple(rule for rule in RULES if rule in failures)


def candidates(state, selected, orbits, byrow, deadline=None, work=None):
    needs, available, degrees, failures = residual_scan(state, selected, orbits, deadline, work)
    if not any(needs):
        check_deadline(deadline)
        return None
    if failures:
        check_deadline(deadline)
        return []
    row = min((r for r in range(state.n) if needs[r]), key=lambda r: (degrees[r], r))
    viable = []
    for index, present in enumerate(available):
        check_deadline(deadline)
        bump(work, 'candidate_orbit_tests')
        if present and row in orbits[index][0]:
            viable.append(index)
    batches = []
    for batch in itertools.combinations(viable, needs[row]):
        check_deadline(deadline)
        batches.append(batch)
    check_deadline(deadline)
    return batches


def run(n,seconds,max_nodes,checkpoint,*,expected_sha256=None,deficits=None,diagonals=None,on_witness=None):
    if type(n) is not int or not 2<=n<=MAX_N:raise ValueError('n must be integer in [2,79]')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0:raise ValueError('invalid seconds')
    if type(max_nodes) is not int or max_nodes<1:raise ValueError('invalid node limit')
    started=time.monotonic();deadline=started+seconds
    physical={'restore':new_work(),'traversal':new_work()}
    restore_seconds=0.0
    ds,ts=indices(deficits,n),indices(diagonals,n)
    orbits=pair_orbits(n);byrow=[[] for _ in range(n)]
    for i,orbit in enumerate(orbits):
        for row in sorted({p[1] for p in orbit}):byrow[row].append(i)
    identity={'format':'diagonal-residual-rowbatch-frontier-v1','n':n,'deficits':ds,'diagonals':ts,
              'source_hashes':source_hashes(),'orbit_order_sha256':sha(encode(orbits)),
              'branch_order':'minimum-viable-row-then-lexicographic-unordered-batch-v1',
              'prune_policy':'residual-row-degree-component-parity-bipartite-sum-v1'}
    slices=[(d,t) for d in ds for t in ts];checkpoint=Path(checkpoint)
    if checkpoint.exists():
        with checkpoint.open('rb') as stream:raw=stream.read(MAX_CHECKPOINT_BYTES+1)
        if len(raw)>MAX_CHECKPOINT_BYTES:raise ValueError('checkpoint exceeds size limit')
        if expected_sha256 is None or sha(raw)!=expected_sha256:raise ValueError('checkpoint hash missing or mismatched')
        data=json.loads(raw)
        if not isinstance(data,dict):raise ValueError('checkpoint must be an object')
        if data.get('identity')!=identity:raise ValueError('checkpoint identity mismatch')
    else:
        if expected_sha256 is not None:raise ValueError('checkpoint missing')
        data={'identity':identity,'slice_index':0,'frames':[{'batch':None,'next':None}],
              'nodes':0,'witness_visits':0,'slice_counts':[[0,0] for _ in slices]}
    index=data.get('slice_index');frames=data.get('frames');counts=data.get('slice_counts')
    if (type(index) is not int or not 0<=index<=len(slices) or not isinstance(frames,list) or len(frames)>n or
        not isinstance(counts,list) or len(counts)!=len(slices) or
        any(not isinstance(c,list) or len(c)!=2 or any(type(v) is not int or v<0 for v in c) or c[1]>c[0] for c in counts) or
        type(data.get('nodes')) is not int or type(data.get('witness_visits')) is not int or
        sum(c[0] for c in counts)!=data['nodes'] or sum(c[1] for c in counts)!=data['witness_visits'] or
        any(c!=[0,0] for c in counts[index+1:])):raise ValueError('invalid checkpoint counters')
    if (index==len(slices)) != (not frames):raise ValueError('invalid checkpoint frontier')
    state=None;selected=set();options=[]
    def push_batch(batch):
        pushed=[]
        for idx in batch:
            if not state.push(orbits[idx]):
                for previous in reversed(pushed):selected.remove(previous);state.pop()
                return False
            selected.add(idx);pushed.append(idx)
        return True
    def pop_batch(batch):
        for idx in reversed(batch):selected.remove(idx);state.pop()
    def restore():
        nonlocal state,selected,options
        if index==len(slices):return
        d,t=slices[index];state=SecantState(n,d)
        if not state.push(((t,t),)):raise ValueError('invalid root')
        selected=set();options=[]
        for pos,frame in enumerate(frames):
            if time.monotonic()>=deadline:raise TimeoutError
            if not isinstance(frame,dict) or set(frame)!={'batch','next'}:raise ValueError('invalid frame')
            batch,cursor=frame['batch'],frame['next']
            if pos==0:
                if batch is not None:raise ValueError('invalid root frame')
            else:
                if (not isinstance(batch,list) or len(batch) not in (1,2) or
                    any(type(i) is not int for i in batch) or batch!=sorted(set(batch)) or
                    options[-1] is None or tuple(batch) not in options[-1]):raise ValueError('invalid batch path')
                parent=frames[pos-1]
                if parent['next'] is None or parent['next']<1 or options[-1][parent['next']-1]!=tuple(batch):raise ValueError('invalid branch cursor')
                if not push_batch(batch):raise ValueError('inadmissible batch path')
                if time.monotonic()>=deadline:raise TimeoutError
            if cursor is None:
                if pos!=len(frames)-1:raise ValueError('pending node must end stack')
                options.append(None)
            else:
                opts=candidates(state,selected,orbits,byrow,deadline,physical['restore'])
                if opts is None or type(cursor) is not int or not 0<=cursor<=len(opts):raise ValueError('invalid cursor')
                options.append(opts)
    restore_started=time.monotonic()
    try:restore()
    except TimeoutError:
        restore_elapsed=time.monotonic()-restore_started
        publication_started=time.monotonic()
        if source_hashes()!=identity['source_hashes']:raise ValueError('sources changed during reconstruction')
        if expected_sha256 is not None:
            with checkpoint.open('rb') as stream:current=stream.read(MAX_CHECKPOINT_BYTES+1)
            if len(current)>MAX_CHECKPOINT_BYTES or sha(current)!=expected_sha256:raise ValueError('checkpoint changed during reconstruction')
            checkpoint_hash=expected_sha256
        else:
            if checkpoint.exists():raise ValueError('checkpoint appeared during reconstruction')
            data['previous_checkpoint_sha256']=None;payload=encode(data);atomic(checkpoint,payload);checkpoint_hash=sha(payload)
        return {'physical_work':physical,'restore_seconds':restore_elapsed,
                'publication_seconds':time.monotonic()-publication_started,
                'traversal_seconds':0.0,'status':'timeout','checkpoint_sha256':checkpoint_hash,'nodes_this_run':0,
                'nodes_total':data['nodes'],'witness_visits_total':data['witness_visits'],
                'slice_index':index,'slice_counts':counts,'scope':'Only declared diagonal-reflection slices; no unrestricted infeasibility conclusion.'}
    restore_seconds += time.monotonic()-restore_started
    initial_restore_seconds=restore_seconds
    traversal_started=time.monotonic()
    def pop_frame():
        frame=frames.pop();options.pop()
        if frame['batch'] is not None:pop_batch(frame['batch'])
    nodes_this_run=0;status=None
    while index<len(slices):
        if not frames:
            index+=1;data['slice_index']=index
            if index==len(slices):break
            frames.append({'batch':None,'next':None})
            restore_started=time.monotonic()
            try:restore()
            except TimeoutError:status='timeout';break
            finally:restore_seconds += time.monotonic()-restore_started
        frame=frames[-1]
        if frame['next'] is not None and frame['next']==len(options[-1]):pop_frame();continue
        if frame['next'] is None:
            if time.monotonic()>=deadline:status='timeout';break
            if nodes_this_run>=max_nodes:status='node_limit';break
            try:opts=candidates(state,selected,orbits,byrow,deadline,physical['traversal'])
            except TimeoutError:status='timeout';break
            if opts is None:
                d,t=slices[index];points=sorted(state.points)
                if len(points)!=2*n-1 or state.columns!=state.target or {(y,x) for x,y in points}!=set(points):raise RuntimeError('full state invariant failed')
                cert={'n':n,'points':[list(p) for p in points],'metadata':{'method':'diagonal_residual_checkpoint','deficit':d,'diagonal':t,'novelty_claim':False}}
                checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                if not all(c['valid'] and c['point_count']==2*n-1 for c in checks):raise RuntimeError('witness verification failed')
                cert['metadata']['normalized_sha256']=checks[0]['normalized_sha256']
                if on_witness:on_witness(cert)
                data['witness_visits']+=1;counts[index][1]+=1
            data['nodes']+=1;counts[index][0]+=1;nodes_this_run+=1
            if opts is None:pop_frame()
            else:frame['next']=0;options[-1]=opts
            continue
        if time.monotonic()>=deadline:status='timeout';break
        batch=options[-1][frame['next']];frame['next']+=1
        if push_batch(batch):frames.append({'batch':list(batch),'next':None});options.append(None)
    traversal_seconds=max(0.0,time.monotonic()-traversal_started-(restore_seconds-initial_restore_seconds))
    publication_started=time.monotonic()
    if source_hashes()!=identity['source_hashes']:raise ValueError('sources changed during traversal')
    if expected_sha256 is not None:
        if not checkpoint.exists():raise ValueError('checkpoint changed during traversal')
        with checkpoint.open('rb') as stream:current=stream.read(MAX_CHECKPOINT_BYTES+1)
        if len(current)>MAX_CHECKPOINT_BYTES or sha(current)!=expected_sha256:raise ValueError('checkpoint changed during traversal')
    elif checkpoint.exists():raise ValueError('checkpoint appeared during traversal')
    if status is None and time.monotonic()>=deadline:status='timeout'
    data['previous_checkpoint_sha256']=expected_sha256
    payload=encode(data)
    if len(payload)>MAX_CHECKPOINT_BYTES:raise ValueError('checkpoint exceeds size limit')
    atomic(checkpoint,payload)
    return {'physical_work':physical,'restore_seconds':restore_seconds,
            'traversal_seconds':traversal_seconds,'publication_seconds':time.monotonic()-publication_started,
            'status':status or 'all_declared_slices_exhausted','checkpoint_sha256':sha(payload),
            'nodes_this_run':nodes_this_run,'nodes_total':data['nodes'],'witness_visits_total':data['witness_visits'],
            'slice_index':index,'slice_counts':counts,'scope':'Only declared diagonal-reflection slices; no unrestricted infeasibility conclusion.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n',type=int,required=True);p.add_argument('--seconds',type=float,required=True)
    p.add_argument('--max-nodes',type=int,required=True);p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--expected-sha256');p.add_argument('--deficit',type=int,action='append');p.add_argument('--diagonal',type=int,action='append')
    p.add_argument('--witness-directory',type=Path,required=True)
    a=p.parse_args(argv);a.witness_directory.mkdir(parents=True,exist_ok=True)
    def save(cert):atomic(a.witness_directory/(cert['metadata']['normalized_sha256']+'.json'),encode(cert))
    print(json.dumps(run(a.n,a.seconds,a.max_nodes,a.checkpoint,expected_sha256=a.expected_sha256,deficits=a.deficit,diagonals=a.diagonal,on_witness=save),sort_keys=True))
    return 0


if __name__=='__main__':sys.exit(main())
