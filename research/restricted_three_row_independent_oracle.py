"""Independent bounded synthetic three-row oracle; no production imports or file discovery."""
from collections import Counter
from itertools import combinations, product
import hashlib
import json


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def identity(n,points):return hashlib.sha256(canonical({'n':n,'points':sorted(points)})).hexdigest()
def collinear(p,q,r):return (q[0]-p[0])*(r[1]-p[1])==(q[1]-p[1])*(r[0]-p[0])
def triples(points):return tuple(t for t in combinations(sorted(points),3) if collinear(*t))
def raw(points):return sum(collinear(*t) for t in combinations(points,3))


def validate(points,n):
    if type(n) is not int or not 2<=n<=6:raise ValueError('synthetic grid bound')
    points=tuple(sorted(tuple(p) for p in points))
    if (len(points)!=2*n-1 or len(set(points))!=len(points)
            or any(len(p)!=2 or any(type(x) is not int or not 0<=x<n for x in p) for p in points)):
        raise ValueError('point invariants')
    counts=Counter(y for x,y in points)
    if sorted(counts.get(y,0) for y in range(n))!=[1]+[2]*(n-1):raise ValueError('row invariant')
    return points


def all_states(n):
    if type(n) is not int or not 2<=n<=4:raise ValueError('finite census bound')
    for singleton in range(n):
        choices=[list(combinations(range(n),1 if y==singleton else 2)) for y in range(n)]
        for rows in product(*choices):yield tuple(sorted((x,y) for y,cols in enumerate(rows) for x in cols))


def profile(points,n):
    points=validate(points,n);violations=triples(points);I=[0]*n
    J=dict.fromkeys(combinations(range(n),2),0);K=dict.fromkeys(combinations(range(n),3),0)
    for triple in violations:
        ys=tuple(sorted(p[1] for p in triple));assert len(set(ys))==3
        for y in ys:I[y]+=1
        for pair in combinations(ys,2):J[pair]+=1
        K[ys]+=1
    M={rows:sum(bool(set(rows)&{p[1] for p in triple}) for triple in violations) for rows in K}
    for r,s,t in K:assert M[r,s,t]==I[r]+I[s]+I[t]-J[r,s]-J[r,t]-J[s,t]+K[r,s,t]
    blocks=sorted((rows for rows,v in K.items() if v),key=lambda rows:(-M[rows],*rows))
    assert sum(K.values())==len(violations)
    return {'U':len(violations),'I':tuple(I),'J':J,'K':K,'M':M,'blocks':tuple(blocks),
            'records':tuple((*rows,M[rows],K[rows]) for rows in blocks),'state_hash':identity(n,points)}


def tables(points,n,rows):
    points=validate(points,n);rows=tuple(rows)
    if len(rows)!=3 or tuple(sorted(set(rows)))!=rows or not all(0<=r<n for r in rows):raise ValueError('three rows')
    retained=tuple(p for p in points if p[1] not in rows)
    unary=tuple(tuple(sum(collinear(p,q,(x,y)) for p,q in combinations(retained,2)) for x in range(n)) for y in rows)
    current=tuple(tuple(x for x,y in points if y==r) for r in rows)
    domains=[]
    for k,old in enumerate(current):
        missing=sorted((x for x in range(n) if x not in old),key=lambda x:(unary[k][x],x))
        domains.append(tuple(sorted((*old,*missing[:min(4,n)-len(old)]))))
    C={}
    for i,j in combinations(range(3),2):
        C[i,j]={(a,b):sum(collinear((a,rows[i]),(b,rows[j]),q) for q in retained)
                for a in domains[i] for b in domains[j]}
    T={(a,b,c):int(collinear((a,rows[0]),(b,rows[1]),(c,rows[2]))) for a,b,c in product(*domains)}
    return {'retained':retained,'base':raw(retained),'unary':unary,'current':current,'domains':tuple(domains),
            'C':C,'T':T,'rows':rows,'n':n}


def assignments(domains,total):
    choices=[sorted((*combinations(domain,1),*combinations(domain,2))) for domain in domains]
    for value in product(*choices):
        if sum(map(len,value))==total:yield value


def objective(table,X,Y,Z):
    selected=(X,Y,Z);score=table['base']
    for i,cols in enumerate(selected):score+=sum(table['unary'][i][x] for x in cols)
    for i,j in combinations(range(3),2):score+=sum(table['C'][i,j][x,y] for x in selected[i] for y in selected[j])
    score+=sum(table['T'][x,y,z] for x,y,z in product(X,Y,Z))
    return score


def replaced(table,selected):return tuple(sorted((*table['retained'],*((x,y) for y,cols in zip(table['rows'],selected) for x in cols))))


def optimum(points,n,rows,check=lambda:None):
    table=tables(points,n,rows);best=None;count=0;first_zero=None;trace=[]
    for choice in assignments(table['domains'],sum(map(len,table['current']))):
        check();value=raw(replaced(table,choice));item=(value,*choice)
        assert objective(table,*choice)==value
        if best is None or item<best:best=item
        if value==0 and first_zero is None:first_zero=(count,item)
        count+=1;trace.append(item)
    assert objective(table,*table['current'])==raw(points)
    assert best is not None and best[0]<=raw(points)
    if first_zero is not None:assert first_zero[1]==best
    return {'minimum':best,'count':count,'first_zero_index':None if first_zero is None else first_zero[0],
            'trace_sha256':hashlib.sha256(canonical(trace)).hexdigest(),'table':table}
