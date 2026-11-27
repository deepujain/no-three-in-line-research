"""Tiny-only reference census for full-row unordered reflection-orbit branching.

Research prototype, not a bounded production worker. n>5 is forbidden.
"""
import itertools
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.diagonal_secant_dfs_fast import SecantState,pair_orbits,mirror_pair_admissible
from src.verify import verify_certificate,verify_certificate_bruteforce


def census(n, *, deficits=None, diagonals=None, on_witness=None):
    if type(n) is not int or not 2<=n<=5:raise ValueError('tiny-only census requires 2 <= n <= 5')
    def indices(values):
        values=list(range(n)) if values is None else list(values)
        if not values or any(type(i) is not int or not 0<=i<n for i in values) or len(set(values))!=len(values):raise ValueError('invalid slice')
        return sorted(values)
    ds,ts=indices(deficits),indices(diagonals)
    orbits=pair_orbits(n);byrow=[[] for _ in range(n)]
    for i,orb in enumerate(orbits):
        for y in sorted({p[1] for p in orb}):byrow[y].append(i)
    nodes=0;visits=0;per_slice=[]
    for d in ds:
        for t in ts:
            state=SecantState(n,d);assert state.push(((t,t),))
            selected=set();before_nodes=nodes;before_visits=visits
            def visit():
                nonlocal nodes,visits
                nodes+=1
                if all(state.rows[i]==state.target[i] for i in range(n)):
                    points=sorted(state.points)
                    if len(points)!=2*n-1 or state.columns!=state.target or {(y,x) for x,y in points}!=set(points):raise RuntimeError('invariant failure')
                    cert={'n':n,'points':[list(p) for p in points], 'metadata':{'deficit':d,'diagonal':t}}
                    checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                    if not all(x['valid'] and x['point_count']==2*n-1 for x in checks):raise RuntimeError('invalid witness')
                    visits+=1
                    if on_witness:on_witness(cert)
                    return
                sums={x+y for x,y in state.points};rows=[]
                for row in range(n):
                    need=state.target[row]-state.rows[row]
                    if need==0:continue
                    if need not in (1,2):raise RuntimeError('row capacity invariant failed')
                    viable=[idx for idx in byrow[row] if idx not in selected and mirror_pair_admissible(state,orbits[idx],sums)]
                    rows.append((len(viable),row,need,viable))
                _,row,need,viable=min(rows,key=lambda r:(r[0],r[1]))
                for batch in itertools.combinations(viable,need):
                    pushed=[]
                    try:
                        for idx in batch:
                            if not state.push(orbits[idx]):break
                            selected.add(idx);pushed.append(idx)
                        else:visit()
                    finally:
                        for idx in reversed(pushed):selected.remove(idx);state.pop()
            visit()
            per_slice.append({'deficit':d,'diagonal':t,'nodes':nodes-before_nodes,'witness_visits':visits-before_visits})
    return {'n':n,'nodes':nodes,'witness_visits':visits,'slice_results':per_slice}
