"""Fixed exhaustive n2..4 determinant oracle for deficiency move primitives.

This is an independent tiny review harness, never a prospective n79 search.
"""
from collections import Counter
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import time
from src.trade_search import point_conflicts, rectangle_proposal


def triples(points):
    result=[]
    for a,b,c in combinations(sorted(points),3):
        if (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]):
            result.append((a,b,c))
    return result


def deficiency(points,n):
    assert len(points)==2*n-1
    axes=[Counter(p[i] for p in points) for i in (0,1)]
    assert all(sorted(q[i] for i in range(n))==[1]+[2]*(n-1) for q in axes)
    return tuple(next(i for i in range(n) if q[i]==1) for q in axes)


def check_all():
    started=time.monotonic();results=[]
    for n in (2,3,4):
        counts=Counter()
        for chosen in combinations(product(range(n),repeat=2),2*n-1):
            P=set(chosen)
            axes=[Counter(p[i] for p in P) for i in (0,1)]
            if any(max(q.values())>2 for q in axes):continue
            d=deficiency(P,n);counts['deficient_states']+=1
            before=len(triples(P));immutable=frozenset(P)
            if any(sum(p in t for t in triples(P))>=3 for p in P):counts['states_with_high_incidence_points']+=1
            # Primitive per-point score is checked independently on every state.
            for p in P:
                assert point_conflicts(p,P-{p})==sum(p in t for t in triples(P))
                counts['point_incidence_checks']+=1
            for axis in (0,1):
                for old in sorted(P):
                    counts['relocation_attempts']+=1
                    new=tuple(d[axis] if i==axis else old[i] for i in (0,1))
                    legal=old[axis]!=d[axis] and new not in P
                    if not legal:
                        assert frozenset(P)==immutable
                        counts['illegal_relocations']+=1;continue
                    remaining=P-{old};Q=remaining|{new}
                    after=deficiency(Q,n)
                    assert after[axis]==old[axis] and after[1-axis]==d[1-axis]
                    delta=-point_conflicts(old,remaining)+point_conflicts(new,remaining)
                    assert delta==len(triples(Q))-before
                    # Its old cell is the new deficiency's legal inverse destination.
                    assert new in Q and old not in Q and new[axis]!=after[axis]
                    assert (Q-{new})|{old}==P
                    inv=-point_conflicts(new,Q-{new})+point_conflicts(old,Q-{new})
                    assert inv==-delta
                    counts['legal_relocations']+=1
            for first,second in combinations(sorted(P),2):
                counts['rectangle_attempts']+=1
                crossed={(first[0],second[1]),(second[0],first[1])}
                legal=(first[0]!=second[0] and first[1]!=second[1] and not crossed&P)
                proposal=rectangle_proposal(P,first,second)
                assert frozenset(P)==immutable
                assert (proposal is not None)==legal
                if not legal:
                    counts['illegal_rectangles']+=1;continue
                delta,Q=proposal
                assert Q==(P-{first,second})|crossed and deficiency(Q,n)==d
                assert delta==len(triples(Q))-before
                inverse=rectangle_proposal(Q,*sorted(crossed))
                assert inverse==(-delta,P)
                counts['legal_rectangles']+=1
        assert counts['relocation_attempts']==counts['legal_relocations']+counts['illegal_relocations']
        assert counts['rectangle_attempts']==counts['legal_rectangles']+counts['illegal_rectangles']
        results.append({'n':n,**counts})
    line={(i,i) for i in range(4)}
    assert len(triples(line))==4
    for p in line:assert point_conflicts(p,line-{p})==3
    # Deliberately occupied deficient intersection: no artificial-cell assumption.
    example={(0,1),(1,0),(1,2),(2,0),(2,2)}
    assert deficiency(example,3)==(0,1) and (0,1) in example
    return {'scope':'Exhaustive tiny n2..4 states with2n-1points/axis capacities; direct integer determinants. No n79 evaluation.','stages':results,'line_of_four_triples':4,'occupied_deficiency_intersection_checked':True,'production_primitives':'point_conflicts and rectangle_proposal only; no production full scoring/validator used','trade_search_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'src/trade_search.py').read_bytes()).hexdigest(),'elapsed_seconds':time.monotonic()-started}


if __name__=='__main__':
    result=check_all();result['oracle_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out=Path(__file__).resolve().parents[1]/'data/deficiency-move-independent-tiny-evidence.json'
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True));print('evidence_sha256',hashlib.sha256(out.read_bytes()).hexdigest())
