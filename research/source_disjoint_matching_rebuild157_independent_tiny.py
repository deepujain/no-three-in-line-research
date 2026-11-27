import hashlib,json,sys
from itertools import combinations,permutations,product
from pathlib import Path
ROOT=Path('/Users/dejain/nvidia/oss/work/no-three-in-line-research')
sys.path.insert(0,str(ROOT))
from research import source_disjoint_matching_rebuild157 as m

def collinear(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])==0
def valid(P):return not any(collinear(*t) for t in combinations(P,3))
def matches(n):return [frozenset(enumerate(p)) for p in permutations(range(n))]
counts={'families':0,'full_solutions':0,'distinct_prefixes_checked':0,'interruption_points':0,'cap_cases':0}
for n in range(2,6):
    for rperm in permutations(range(n-1)):
        R=tuple(enumerate(rperm))
        if not valid(R):continue
        for extras in (set(),{(n-1,0)},{(n-1,0),(0,n-1)}):
            F=set(R)|extras;c=m.new_counters();unsafe,domains=m.root_domains(n,R,F,c,lambda:None)
            direct=[sum((1<<y) for y in range(n) if (x,y) not in F and valid(R+((x,y),))) for x in range(n)]
            assert domains==direct
            expected={M for M in matches(n) if not M&F and valid(tuple(set(R)|M))}
            seen=set();found=[];kernel=None
            def check():
                if kernel is None:return
                prefix=tuple(kernel.path)
                if prefix in seen:return
                seen.add(prefix)
                assert valid(R+prefix) and not set(prefix)&F
                assert len({x for x,y in prefix})==len(prefix)==len({y for x,y in prefix})
            kernel=m.Constructor(n,R,F,domains,unsafe,c,check,2000)
            def callback(M):
                if len(M)==n:found.append(frozenset(M))
                return False
            assert kernel.run(callback) is False
            assert set(found)==expected and len(found)==len(expected)
            assert kernel.root_restored and not kernel.path
            counts['families']+=1;counts['full_solutions']+=len(found);counts['distinct_prefixes_checked']+=len(seen)
# Interrupt every check in one nontrivial complete tiny DFS, including nested frames.
n=3;R=((0,0),(1,1));F=set(R)
def make(check,cap=2000):
    c=m.new_counters();u,d=m.root_domains(n,R,F,c,lambda:None)
    return m.Constructor(n,R,F,d,u,c,check,cap),c
calls=[0]
def counting():calls[0]+=1
k,c=make(counting);k.run(lambda M:False)
for stop in range(1,calls[0]+1):
    actual=[0]
    def interrupted():
        actual[0]+=1
        if actual[0]==stop:raise TimeoutError
    k,ctr=make(interrupted)
    try:k.run(lambda M:False)
    except TimeoutError:pass
    else:raise AssertionError('interruption was swallowed')
    assert k.root_restored and k.path==[]
    assert ctr['insertions_started']>=ctr['insertions_completed']==ctr['rollbacks']
    counts['interruption_points']+=1
full_starts=c['insertions_started']
for cap in range(full_starts+1):
    k,ctr=make(lambda:None,cap)
    try:
        assert k.run(lambda M:False) is False
        assert cap==full_starts
    except m.InsertionCap:assert cap<full_starts
    assert k.root_restored and not k.path and ctr['insertions_started']<=cap
    counts['cap_cases']+=1
files=['research/source_disjoint_matching_rebuild157.py','tests/test_source_disjoint_matching_rebuild157.py']
out={'accepted':True,'scope':'Independent tiny grids only, n=2..5; no n79 work','counts':counts,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
path=ROOT/'data/source-disjoint-matching-rebuild157-independent-tiny-audit.json'
path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True));print('audit_sha256',hashlib.sha256(path.read_bytes()).hexdigest())
