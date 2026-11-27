"""Pure determinant oracle for tiny Boolean scaffold projections; no solver."""
from itertools import combinations, product


def determinant(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def valid(points):
    return all(determinant(*t) != 0 for t in combinations(sorted(points), 3))


def support_catalog(A, pool):
    """All row/column support choices, without production helper imports."""
    A, pool = tuple(sorted(A)), tuple(sorted(pool))
    arcs=[]
    for q in pool:
        for a,b in product(A,repeat=2):
            if a[0]==q[0] and b[1]==q[1] and a!=b and a[0]!=b[0] and a[1]!=b[1]:
                arcs.append((q,a,b))
    return tuple(sorted(arcs))


def derive(selected):
    return {e[0] for e in selected}, {p for _,a,b in selected for p in (a,b)}


def matching(points):
    return len({p[0] for p in points})==len(points)==len({p[1] for p in points})


def compatible(selected):
    endpoints=[p for _,a,b in selected for p in (a,b)]
    return len(endpoints)==len(set(endpoints)) and matching(endpoints)


def four_classes(A, Q, D):
    """Evaluate projected clauses directly, independently of pooled bit tables."""
    old = all(D.intersection(t) for t in combinations(sorted(A),3) if determinant(*t)==0)
    one = all(D.intersection((a,b)) for q in Q for a,b in combinations(sorted(A),2) if determinant(a,b,q)==0)
    two = all(a in D for q,r in combinations(sorted(Q),2) for a in A if determinant(q,r,a)==0)
    three = all(determinant(*t)!=0 for t in combinations(sorted(Q),3))
    return old,one,two,three


def enumerate_projection(A, S, pool, k):
    """Return all support selections and independently evaluate projection."""
    assert A < S and len(S-A)==1 and not set(pool)&S
    arcs=support_catalog(A,pool); records=[]
    for selection in combinations(arcs,k):
        if not compatible(selection):
            continue
        Q,D=derive(selection); P=(A-D)|Q
        clauses=four_classes(A,Q,D)
        assert len(D)==2*k and len(Q)==k
        assert len(P)==len(A)-k and len(S-P)==2*k+1 and len(P-S)==k
        assert all(clauses)==valid(P)
        records.append((selection,frozenset(Q),frozenset(D),clauses,frozenset(P)))
    return arcs,records
