"""Pure small-cut necessary condition for a complete radius multigraph.

No geometry, core integration or checkpoint handling is performed here.
The caller must supply every individually admissible orbit edge.
"""
import itertools


def small_cut_obstruction(demands, edges, check=lambda: None):
    """Return the first violating 2/3-vertex subset, or None after a full scan.

    Edge instances are distinct orbit variables, including parallel edges.
    A raised budget/interruption exception propagates and supplies no verdict.
    """
    n=len(demands)
    if not 1<=n<=40 or any(type(d) is not int or not 0<=d<=2 for d in demands):
        raise ValueError('invalid bounded quotient demands')
    matrix=[[0]*n for _ in range(n)]; degree=[0]*n
    for i,edge in enumerate(edges):
        check()
        if i>=1521 or not isinstance(edge,(tuple,list)) or len(edge)!=2:
            raise ValueError('invalid bounded radius edges')
        u,v=edge
        if type(u) is not int or type(v) is not int or not 0<=u<n or not 0<=v<n or u==v:
            raise ValueError('invalid radius endpoints')
        if demands[u] and demands[v]:
            matrix[u][v]+=1;matrix[v][u]+=1
            degree[u]+=1;degree[v]+=1
    check()
    active=[i for i,d in enumerate(demands) if d]
    total=sum(demands)
    for size in (2,3):
        for subset in itertools.combinations(active,size):
            check()
            inside=sum(matrix[u][v] for u,v in itertools.combinations(subset,2))
            demand=sum(demands[u] for u in subset)
            cross=sum(degree[u] for u in subset)-2*inside
            if demand>2*inside+min(total-demand,cross):
                check()
                return subset
    check()
    return None
