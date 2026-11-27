"""Pure synthetic review oracle. No production imports or selected-source reads.

Reuses the frozen independent design helper without editing it. Expected sets
are literal coordinate tuples, not production masks or compact records.
"""
from collections import Counter
from itertools import combinations, product
import hashlib
import json
from math import gcd
from pathlib import Path
from research import unimodular_extension_independent_design_tiny as design
from research import nonuniform_insertion_independent_tiny_oracle as geometry


def canonical(u):
    return u[0]>0 or (u[0]==0 and u[1]>0)


def source_points(points,n):
    assert type(n) is int and 4<=n<=6, 'review oracle accepts only tiny synthetic orders'
    points=tuple(sorted(map(tuple,points)))
    assert len(points)==2*n and len(set(points))==len(points)
    assert all(len(p)==2 and all(type(v) is int and 0<=v<n for v in p) for p in points)
    assert all(Counter(p[axis] for p in points)==Counter({v:2 for v in range(n)}) for axis in (0,1))
    assert not geometry.triples(points)
    return points


def expected_inventory(points,n):
    """All accepted/rejected bounded directions and the complete exterior family."""
    points=source_points(points,n)
    horizontal=[(abs(points[i][0]-points[j][0]),(i,j)) for i,j in combinations(range(len(points)),2)
                if points[i][1]==points[j][1]]
    vertical=[(abs(points[i][1]-points[j][1]),(i,j)) for i,j in combinations(range(len(points)),2)
              if points[i][0]==points[j][0]]
    h=max(v for v,ij in horizontal);v=max(w for w,ij in vertical)
    bound_a,bound_b=n//h,n//v
    admitted={};rejected={};outside_cutoff={}
    # Independently inspect the full universal tiny coefficient box. Do not
    # generate the expected admitted set using the production H/V cutoff.
    for u in product(range(-n,n+1),repeat=2):
        if not canonical(u) or gcd(*u)!=1:continue
        values=design.project(points,u);lo,hi=min(values),max(values)
        info={'width':hi-lo,'minimum':lo,'maximum':hi,'counts':dict(Counter(values)),
              'extreme_pairs':{(i,j) for i,a in enumerate(values) for j,b in enumerate(values) if b-a==hi-lo}}
        if abs(u[0])>bound_a or abs(u[1])>bound_b:
            assert hi-lo>n
            outside_cutoff[u]=info
        elif hi-lo>n:rejected[u]=info
        else:admitted[u]=info
    assert len(admitted)<=4
    signed=set(admitted)|{(-a,-b) for a,b in admitted}|{(0,0)}
    assert len({(a%3,b%3) for a,b in signed})==len(signed)
    frames={};all_eligible={};exterior={}
    for u,w in combinations(sorted(admitted),2):
        det=design.determinant(u,w)
        if abs(det)!=1:continue
        ordinary={u,w}=={(1,0),(0,1)}
        placements={};raw_choices=[];occupied_choices=[]
        for t,mapped in design.placements(points,n,u,w):
            cx,cy=Counter(p[0] for p in mapped),Counter(p[1] for p in mapped)
            deficient=({i for i in range(n+1) if cx[i]<2},{i for i in range(n+1) if cy[i]<2})
            placements[t]={'mapped':mapped,'deficient':deficient}
            for z in product(*deficient):
                q=design.inverse(u,w,t,z)
                entry={'q':q,'translation':t,'added':z,'occupied':z in mapped,
                       'protected':-1<=q[0]<=n and -1<=q[1]<=n}
                if entry['occupied']:occupied_choices.append(entry)
                else:raw_choices.append(entry)
        assert len(raw_choices)+len(occupied_choices)<=4
        frames[(u,w)]={'determinant':det,'ordinary':ordinary,'placements':placements,
                       'choices':raw_choices,'occupied_choices':occupied_choices}
        if ordinary:continue
        for entry in raw_choices:
            q=entry['q'];all_eligible.setdefault(q,[]).append(((u,w),entry))
            if not entry['protected']:exterior.setdefault(q,[]).append(((u,w),entry))
    obstructions={q:{(i,j) for i,j in combinations(range(len(points)),2)
                     if geometry.collinear(points[i],points[j],q)} for q in exterior}
    return {'points':points,'n':n,'H':h,'V':v,'coefficient_bounds':(bound_a,bound_b),
            'horizontal_max_witnesses':{ij for w,ij in horizontal if w==h},
            'vertical_max_witnesses':{ij for w,ij in vertical if w==v},
            'admitted':admitted,'rejected':rejected,'outside_cutoff':outside_cutoff,
            'frames':frames,'all_eligible_preimages':all_eligible,'exterior_preimages':exterior,
            'obstructions':obstructions,'valid_preimages':{q for q,witnesses in obstructions.items() if not witnesses}}


def check_width_obstruction(points,u,indices,n):
    assert len(indices)==2 and len(set(indices))==2
    assert all(type(i) is int and 0<=i<len(points) for i in indices)
    values=[u[0]*points[i][0]+u[1]*points[i][1] for i in indices]
    assert abs(values[1]-values[0])>n


def check_point_obstruction(points,q,indices):
    assert q not in points and len(indices)==2 and len(set(indices))==2
    assert all(type(i) is int and 0<=i<len(points) for i in indices)
    assert geometry.collinear(points[indices[0]],points[indices[1]],q)


def main():
    counts=dict(sources=0,admitted_directions=0,rejected_directions=0,outside_cutoff_directions=0,
                frames=0,nonordinary_frames=0,nonordinary_choices=0,exterior_preimages=0,
                width_certificates=0,point_certificates=0,valid_exterior_preimages=0,occupied_choices=0)
    for points in geometry.full_axis_sources(4):
        result=expected_inventory(points,4);counts['sources']+=1;points=result['points']
        for key,target in (('admitted','admitted_directions'),('rejected','rejected_directions'),('outside_cutoff','outside_cutoff_directions')):
            counts[target]+=len(result[key])
        for u,info in result['rejected'].items():
            for ij in info['extreme_pairs']:
                check_width_obstruction(points,u,ij,4);counts['width_certificates']+=1
        counts['frames']+=len(result['frames'])
        for frame in result['frames'].values():
            counts['occupied_choices']+=len(frame['occupied_choices'])
            if not frame['ordinary']:
                counts['nonordinary_frames']+=1;counts['nonordinary_choices']+=len(frame['choices'])
        counts['exterior_preimages']+=len(result['exterior_preimages'])
        counts['valid_exterior_preimages']+=len(result['valid_preimages'])
        for q,pairs in result['obstructions'].items():
            for ij in pairs:check_point_obstruction(points,q,ij);counts['point_certificates']+=1
    root=Path(__file__).resolve().parents[1]
    paths=(Path(__file__),Path(design.__file__),Path(geometry.__file__))
    result={'passed':True,'counts':counts,'pins':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'scope':'Independent synthetic oracle preparation only; no production worker comparison or selected-source read/inventory.'}
    (root/'data/exterior-affine-independent-oracle-preparation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
