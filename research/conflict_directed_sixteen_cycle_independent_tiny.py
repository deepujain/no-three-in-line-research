"""Independent pure tiny oracle. Never invokes run/main or fixed n79 inputs."""
from collections import Counter
from itertools import combinations, permutations, product
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import conflict_directed_sixteen_cycle_rebuild157 as m

def determinant(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def valid(P):return all(determinant(*t) for t in combinations(P,3))
def matching(P):return len({x for x,y in P})==len(P)==len({y for x,y in P})
def onecycle(p):
    if sorted(p)!=list(range(len(p))):return False
    # A permutation is a single cycle iff there is no nonempty proper invariant subset.
    return not any({p[i] for i in part}==set(part) for k in range(1,len(p)) for part in combinations(range(len(p)),k))
def states(n):
    for cells in combinations(product(range(n),repeat=2),2*n-1):
        if all(sorted(Counter(p[a] for p in cells).values())==[1]+[2]*(n-1) for a in (0,1)):yield frozenset(cells)
counts={'axis_states_n3':0,'patch_families':0,'full_solutions':0,'prefixes_checked':0,'kernel_families':0,'hitting_matchings_checked':0,'cycle_label_checks':0,'shared_cap_started':0,'shared_cap_kernel_attempts':0}

def audit_family(n,A,S,F):
    R=tuple(sorted(A-set(F)))
    if not valid(R):return
    k=len(F);c=m.new_counters();unsafe,domains=m.root_domains(n,R,S,F,c,lambda:None)
    direct=[]
    for row,_ in F:
        direct.append(sum(1<<j for j,(_,col) in enumerate(F) if (row,col) not in S and valid(R+((row,col),))))
    assert domains==direct
    board=set(product(range(n),repeat=2))
    blocked={p for p in board if any(determinant(a,b,p)==0 for a,b in combinations(R,2))}
    assert unsafe==sum(1<<(n*x+y) for x,y in blocked)
    expected=set()
    for perm in permutations(range(k)):
        M=frozenset((F[i][0],F[perm[i]][1]) for i in range(k))
        if onecycle(perm) and not M&S and valid(tuple(set(R)|M)):expected.add(M)
    K=None;seen=set()
    def check():
        if K is None:return
        prefix=tuple(K.path)
        if prefix in seen:return
        seen.add(prefix)
        assert valid(R+prefix) and matching(prefix) and not set(prefix)&S
        assert len(set(R)|set(prefix))==len(R)+len(prefix)
    K=m.Constructor(n,R,S,F,domains,unsafe,c,check,1000);found=[]
    def callback(M):
        if len(M)==k:found.append(frozenset(M))
        return False
    assert K.run(callback) is False and K.root_restored
    assert not K.path and K.sigma==[-1]*k
    assert set(found)==expected and len(found)==len(expected)
    assert c['insertions_started']==c['insertions_completed']==c['rollbacks']
    # Generic source-distance equations and exact axis restoration on each full exchange.
    for M in found:
        P=(A-set(F))|M
        assert all(Counter(p[a] for p in P)==Counter(p[a] for p in A) for a in (0,1))
        assert len(S-P)==len(S-A)+len(set(F)&S)-len(M&S)
        assert len(P-S)==len(A-S)-len(set(F)-S)+len(M-S)
    counts['patch_families']+=1;counts['full_solutions']+=len(found);counts['prefixes_checked']+=len(seen)

all3=list(states(3));counts['axis_states_n3']=len(all3);assert len(all3)==45
for A in all3:
    outside=set(product(range(3),repeat=2))-A
    for extra in sorted(outside):
        S=A|{extra}
        for k in (2,3):
            for F in combinations(sorted(A),k):
                if matching(F):audit_family(3,A,S,F)
# Empty/single-point retained contexts and permuted, noncontiguous freed axes.
for n,k in ((4,3),(5,4)):
    rows=list(range(k-1))+[n-1]
    for cols in permutations(rows):
        F=tuple(zip(rows,cols))
        for extra in (set(),{(n-2,n-2)}):
            if extra&set(F):continue
            A=set(F)|extra;S=A|{(n-1,0)}
            audit_family(n,A,S,F)
# Exhaust every triple-family on four selected five-cell sets. These are abstract
# hitting-set fixtures, not an assertion that each triple is geometrically collinear.
for A in all3[::12]:
    trip=list(combinations(sorted(A),3))
    matchings=[frozenset(C) for k in range(4) for C in combinations(sorted(A),k) if matching(C)]
    for bits in range(1<<len(trip)):
        conflicts=[t for i,t in enumerate(trip) if bits>>i&1]
        found=m.cover_kernels(A,conflicts,m.new_counters(),lambda:None)
        assert found==sorted(set(found),key=lambda C:(len(C),C))
        assert all(matching(C) and all(set(C)&set(t) for t in conflicts) for C in found)
        for H in matchings:
            if all(H&set(t) for t in conflicts):
                assert any(set(C)<=H for C in found)
                counts['hitting_matchings_checked']+=1
        counts['kernel_families']+=1
# Every proper/full cycle length on exactly16 abstract labels, several cyclic
# relabelings, no grid coordinates or geometry.
for shift in range(16):
    order=[(i+shift)%16 for i in range(16)]
    for length in range(1,17):
        sigma=[-1]*16
        for i in range(length-1):sigma[order[i]]=order[i+1]
        assert m.proper_cycle(order[length-1],order[0],sigma)==(length<16)
        sigma[order[length-1]]=order[0]
        if length==16:assert m.single_cycle(sigma)
        counts['cycle_label_checks']+=1
# Exactly1000 shared starts across independent tiny n3 kernels; no cap reset.
c=m.new_counters();F=((0,0),(1,1),(2,2));u,d=m.root_domains(3,(),set(F),F,c,lambda:None)
while True:
    K=m.Constructor(3,(),set(F),F,d,u,c,lambda:None,1000)
    counts['shared_cap_kernel_attempts']+=1
    try:assert K.run(lambda M:False) is False
    except m.InsertionCap:
        assert K.root_restored and not K.path and K.sigma==[-1]*3
        break
    assert K.root_restored
    assert counts['shared_cap_kernel_attempts']<1001
assert c['insertions_started']==c['insertions_completed']==c['rollbacks']==1000
counts['shared_cap_started']=c['insertions_started']
files=['research/conflict_directed_sixteen_cycle_rebuild157.py','tests/test_conflict_directed_sixteen_cycle_rebuild157.py','research/source_disjoint_matching_rebuild157.py']
result={'accepted':True,'scope':'Independent tiny inputs n3..5 and abstract16labels only; no actual n79 load/geometry/selection/search','counts':counts,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},'independent_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
p=ROOT/'data/conflict-directed-sixteen-cycle-independent-tiny-audit.json';p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True));print('audit_sha256',hashlib.sha256(p.read_bytes()).hexdigest())
