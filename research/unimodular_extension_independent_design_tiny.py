"""Synthetic n4 falsifiers of an affine design; no actual source or production worker."""
from collections import Counter
from itertools import combinations, product
import hashlib
import json
from math import gcd
from pathlib import Path
from research.nonuniform_insertion_independent_tiny_oracle import full_axis_sources, triples, collinear


def project(points,u):
    return [u[0]*x+u[1]*y for x,y in points]


def width(points,u):
    values=project(points,u)
    return max(values)-min(values)


def determinant(u,v):
    return u[0]*v[1]-u[1]*v[0]


def inverse(u,v,t,z):
    d=determinant(u,v); assert abs(d)==1
    x,y=z[0]-t[0],z[1]-t[1]
    return ((v[1]*x-u[1]*y)//d,(-v[0]*x+u[0]*y)//d)


def placements(points,n,u,v):
    xx,yy=project(points,u),project(points,v)
    for tx in range(-min(xx),n-max(xx)+1):
        for ty in range(-min(yy),n-max(yy)+1):
            mapped=tuple((x+tx,y+ty) for x,y in zip(xx,yy))
            yield (tx,ty),mapped


def candidates(points,n,u,v):
    result=[]
    for t,mapped in placements(points,n,u,v):
        cx,cy=Counter(p[0] for p in mapped),Counter(p[1] for p in mapped)
        for z in product((j for j in range(n+1) if cx[j]<2),(j for j in range(n+1) if cy[j]<2)):
            if z not in mapped:
                q=inverse(u,v,t,z)
                assert q not in points
                assert (u[0]*q[0]+u[1]*q[1]+t[0],v[0]*q[0]+v[1]*q[1]+t[1])==z
                result.append((q,t,z,mapped))
    return result


def main():
    n=4; counts=dict(sources=0,matrix_coefficient_cases=0,short_signed_directions=0,
                     canonical_nonaxis_frames=0,canonical_candidates=0,pair_geometry_checks=0)
    examples=[]
    allvectors=list(product(range(-n,n+1),repeat=2))
    for source_index,points in enumerate(full_axis_sources(n)):
        counts['sources']+=1
        h=max(abs(a[0]-b[0]) for a,b in combinations(points,2) if a[1]==b[1])
        vv=max(abs(a[1]-b[1]) for a,b in combinations(points,2) if a[0]==b[0])
        bounded={u for u in product(range(-n//h-1,n//h+1),range(-n//vv-1,n//vv+1))
                 if u!=(0,0) and gcd(*u)==1 and abs(u[0])<=n//h and abs(u[1])<=n//vv and width(points,u)<=n}
        brute_short={u for u in allvectors if u!=(0,0) and width(points,u)<=n}
        assert bounded==brute_short
        assert all(n-1<=width(points,u)<=n for u in bounded)
        assert len(bounded)<=8
        assert len({(a%3,b%3) for a,b in bounded|{(0,0)}})==len(bounded)+1
        counts['short_signed_directions']+=len(bounded)
        canonical=sorted(u for u in bounded if u[0]>0 or (u[0]==0 and u[1]>0))
        frames=[(u,v) for u,v in combinations(canonical,2) if abs(determinant(u,v))==1]
        assert len(frames)<=6
        canon_q=set();canon_valid=set()
        for u,v in frames:
            if {u,v}=={(1,0),(0,1)}:continue
            counts['canonical_nonaxis_frames']+=1
            choices=candidates(points,n,u,v);assert len(choices)<=4
            counts['canonical_candidates']+=len(choices)
            for q,t,z,mapped in choices:
                canon_q.add(q)
                old_pair_valid=not any(collinear(a,b,q) for a,b in combinations(points,2))
                assert old_pair_valid==(not triples(mapped+(z,)))
                counts['pair_geometry_checks']+=1
                if old_pair_valid:canon_valid.add(q)
            if len(examples)<2:
                examples.append({'source_index':source_index,'source':points,'matrix':[u,v],
                                 'determinant':determinant(u,v),'candidates':[
                                     {'preimage':q,'translation':t,'added_point':z,
                                      'outside_protected_box':not(-1<=q[0]<=n and -1<=q[1]<=n)}
                                     for q,t,z,mapped in choices]})
        brute_q=set();brute_valid=set()
        for u,v in product(allvectors,repeat=2):
            counts['matrix_coefficient_cases']+=1
            if abs(determinant(u,v))!=1 or width(points,u)>n or width(points,v)>n:continue
            if u[0]*u[1]==0 and v[0]*v[1]==0:continue
            for t,mapped in placements(points,n,u,v):
                cx,cy=Counter(p[0] for p in mapped),Counter(p[1] for p in mapped)
                for z in product(range(n+1),repeat=2):
                    if z in mapped:continue
                    q=inverse(u,v,t,z)
                    if cx[z[0]]<2 and cy[z[1]]<2:brute_q.add(q)
                    if not triples(mapped+(z,)):brute_valid.add(q)
        assert brute_q==canon_q and brute_valid==canon_valid
    root=Path(__file__).resolve().parents[1]
    result={'passed':True,'counts':counts,'examples':examples,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'Design falsifiers on all11 synthetic full-axis valid n4 sources only. No selected n74 source read or measurement, no production implementation.'}
    (root/'data/unimodular-extension-independent-design-tiny.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
