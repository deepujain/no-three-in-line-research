"""Bounded exact DFS for odd-cardinality diagonal-reflection families.

Each run searches explicitly named row-deficit/diagonal-singleton slices.
No exhaustion result applies outside those reflection-invariant slices.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.verify import verify_certificate,verify_certificate_bruteforce


def grid_line(a,b,n):
    dx,dy=b[0]-a[0],b[1]-a[1]
    g=math.gcd(dx,dy)
    if not g: raise ValueError('line needs distinct points')
    dx//=g;dy//=g;x,y=a
    while 0<=x-dx<n and 0<=y-dy<n:
        x-=dx;y-=dy
    while 0<=x<n and 0<=y<n:
        yield (x,y)
        x+=dx;y+=dy


class SecantState:
    """Mutable exact pair-line counts; push is transactional and pop reverses it."""
    def __init__(self,n,deficit):
        if type(n) is not int or n<2 or type(deficit) is not int or not 0<=deficit<n:
            raise ValueError('invalid grid or deficit')
        self.n=n;self.target=[2-(i==deficit) for i in range(n)]
        self.points=[];self.occupied=set();self.rows=[0]*n;self.columns=[0]*n
        self.blocked=[0]*(n*n);self.frames=[]

    def _index(self,p): return p[1]*self.n+p[0]

    def _remove_last(self):
        p=self.points.pop();self.occupied.remove(p)
        self.rows[p[1]]-=1;self.columns[p[0]]-=1
        for q in self.points:
            for cell in grid_line(p,q,self.n):
                index=self._index(cell);self.blocked[index]-=1
                if self.blocked[index]<0: raise RuntimeError('negative secant counter')

    def push(self,orbit):
        orbit=tuple(orbit)
        if not orbit: raise ValueError('invalid orbit')
        for point in orbit:
            if (not isinstance(point,tuple) or len(point)!=2 or
                any(type(c) is not int or not 0<=c<self.n for c in point)):
                raise ValueError('point out of range')
        if len(set(orbit))!=len(orbit): raise ValueError('invalid orbit')
        before=len(self.points)
        for point in orbit:
            x,y=point
            if (point in self.occupied or self.rows[y]>=self.target[y] or
                self.columns[x]>=self.target[x] or self.blocked[self._index(point)]):
                while len(self.points)>before:self._remove_last()
                return False
            for q in self.points:
                for cell in grid_line(point,q,self.n):self.blocked[self._index(cell)]+=1
            self.points.append(point);self.occupied.add(point);self.rows[y]+=1;self.columns[x]+=1
        self.frames.append(len(orbit))
        return True

    def pop(self):
        if not self.frames:raise ValueError('no orbit frame to remove')
        for _ in range(self.frames.pop()):self._remove_last()


def pair_orbits(n):
    if type(n) is not int or n<2: raise ValueError('n must be >=2')
    return [((x,y),(y,x)) for x in range(n) for y in range(x+1,n)]


def search(n,seconds,max_nodes,*,deficits=None,diagonals=None,on_witness=None):
    """Search all declared (deficit, diagonal) slices; duplicate leaves possible.

    Time and node limits are global per invocation. Each slice records only
    traversal status, not proof certificates. on_witness receives dual-verified
    full certificates immediately. Outputs are restricted to T-invariant sets.
    """
    if type(n) is not int or n<2: raise ValueError('n must be >=2')
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0:raise ValueError('seconds must be finite positive')
    if type(max_nodes) is not int or max_nodes<1:raise ValueError('max_nodes must be positive')
    def index_set(values):
        values=list(range(n)) if values is None else list(values)
        if not values or any(type(v) is not int or not 0<=v<n for v in values) or len(set(values))!=len(values):raise ValueError('invalid slice indices')
        return sorted(values)
    ds=index_set(deficits);ts=index_set(diagonals)
    started=time.monotonic();deadline=started+seconds
    orbitlist=pair_orbits(n);byrow=[[] for _ in range(n)]
    for i,orbit in enumerate(orbitlist):
        for row in sorted({p[1] for p in orbit}):byrow[row].append(i)
    result={'n':n,'target':2*n-1,'family':'main_diagonal_reflection','status':'incomplete',
            'seconds_budget':seconds,'max_nodes':max_nodes,'deficits':ds,'diagonal_indices':ts,
            'nodes':0,'witness_visits':0,'slice_results':[], 'first_witness':None,
            'scope':'Only declared deficit/singleton slices of the diagonal-reflection family; no unrestricted infeasibility conclusion.',
            'novelty_claim':False}
    stop=None
    for d in ds:
        for t in ts:
            if time.monotonic()>=deadline:stop='timeout';break
            if result['nodes']>=max_nodes:stop='node_limit';break
            state=SecantState(n,d);assert state.push(((t,t),))
            selected=set();slice_start=result['nodes'];slice_witnesses=result['witness_visits']
            def visit():
                nonlocal stop
                if time.monotonic()>=deadline:stop='timeout';return
                if result['nodes']>=max_nodes:stop='node_limit';return
                result['nodes']+=1
                if all(state.rows[i]==state.target[i] for i in range(n)):
                    if state.columns!=state.target or len(state.points)!=2*n-1:raise RuntimeError('axis/count invariant failed')
                    points=sorted(state.points);image={(y,x) for x,y in points}
                    if image!=set(points):raise RuntimeError('reflection invariant failed')
                    cert={'n':n,'points':[list(p) for p in points], 'metadata':{'method':'diagonal_secant_dfs','deficit':d,'diagonal':t,'novelty_claim':False}}
                    checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                    if not all(c['valid'] and c['point_count']==2*n-1 for c in checks):raise RuntimeError('independent witness check failed')
                    cert['metadata']['normalized_sha256']=checks[0]['normalized_sha256']
                    result['witness_visits']+=1
                    if result['first_witness'] is None:result['first_witness']=cert
                    if on_witness:on_witness(cert)
                    return
                # For this row every completion must add at least one orbit
                # touching it. Trying all such orbits is complete; duplicates
                # from alternate insertion orders are intentionally allowed.
                eligible_rows=[]
                for row in range(n):
                    if time.monotonic()>=deadline:stop='timeout';return
                    if state.rows[row]>=state.target[row]:continue
                    viable=[]
                    for idx in byrow[row]:
                        if time.monotonic()>=deadline:stop='timeout';return
                        if idx in selected:continue
                        if state.push(orbitlist[idx]):
                            state.pop();viable.append(idx)
                    eligible_rows.append((len(viable),row,viable))
                _,row,viable=min(eligible_rows,key=lambda item:(item[0],item[1]))
                for idx in viable:
                    if stop is not None:return
                    if not state.push(orbitlist[idx]):raise RuntimeError('admissibility changed without state mutation')
                    selected.add(idx)
                    try: visit()
                    finally:
                        selected.remove(idx);state.pop()
            visit()
            result['slice_results'].append({'deficit':d,'diagonal':t,'status':stop or 'exhausted',
                'nodes':result['nodes']-slice_start,'witness_visits':result['witness_visits']-slice_witnesses})
            if stop is not None:break
        if stop is not None:break
    result['status']=stop or 'all_declared_slices_exhausted'
    result['elapsed_seconds']=time.monotonic()-started
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--max-nodes',type=int,required=True)
    parser.add_argument('--deficit',type=int,action='append')
    parser.add_argument('--diagonal',type=int,action='append')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def save_witness(cert):
        witness_path=args.output.with_name(args.output.name+'.'+cert['metadata']['normalized_sha256']+'.witness.json')
        if not witness_path.exists():
            witness_path.write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
    report=search(args.n,args.seconds,args.max_nodes,deficits=args.deficit,diagonals=args.diagonal,on_witness=save_witness)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('n','status','nodes','witness_visits','elapsed_seconds')}))
    return 0

if __name__=='__main__':sys.exit(main())
