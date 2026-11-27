"""Necessary residual radius-graph conditions; no geometry probes or core hook.

Caller supplies the COMPLETE current admissibility mask. Parallel orbit edges
remain distinct in that mask; adjacency bits merge neighbors for connectivity
and coloring only. No sufficient-feasibility or runtime-improvement claim.
"""


def component_obstruction(demands, edges, check=lambda: None):
    """Return component_parity, bipartite_balance, or None; never on interruption."""
    if not 1 <= len(demands) <= 40:
        raise ValueError('bounded quotient demands required')
    demands = tuple(demands)
    if any(type(b) is not int or not 0 <= b <= 2 for b in demands):
        raise ValueError('bounded quotient demands required')
    adjacency = [0]*len(demands)
    for index, (u, v) in enumerate(edges):
        check()
        if index >= 1521:
            raise ValueError('bounded radius edge count required')
        if (type(u) is not int or type(v) is not int or not 0 <= u < len(demands) or
                not 0 <= v < len(demands) or u == v):
            raise ValueError('distinct bounded radius endpoints required')
        if demands[u] and demands[v]:
            adjacency[u] |= 1 << v
            adjacency[v] |= 1 << u
    colors = [-1]*len(demands)
    for start, demand in enumerate(demands):
        check()
        if not demand or colors[start] != -1:
            continue
        colors[start] = 0
        stack, totals, bipartite = [start], [0, 0], True
        while stack:
            check()
            u = stack.pop()
            totals[colors[u]] += demands[u]
            neighbors = adjacency[u]
            while neighbors:
                check()
                bit = neighbors & -neighbors
                neighbors ^= bit
                v = bit.bit_length()-1
                if colors[v] == -1:
                    colors[v] = 1-colors[u]
                    stack.append(v)
                elif colors[v] == colors[u]:
                    bipartite = False
        check()
        if sum(totals) % 2:
            return 'component_parity'
        if bipartite and totals[0] != totals[1]:
            return 'bipartite_balance'
    check()
    return None


def radius_obstruction(n, rows, orbits, complete_mask, remaining, check=lambda: None):
    """Check coherent near-quarter row demands against an already complete mask.

    ``orbits`` is the existing ordered four-orbit view; only marked entries are
    read, at most four coordinates each. No candidate push or line is built.
    """
    if type(n) is not int or not 3 <= n <= 79 or n % 2 != 1:
        raise ValueError('bounded odd grid required')
    m = n//2
    if (len(rows) != n or len(complete_mask) != m*m or len(orbits) < m*m or
            type(remaining) is not int or not 0 <= remaining <= m):
        raise ValueError('exact row/mask/remaining bounds')
    demands = []
    for u in range(m+1):
        check()
        load = rows[m+u]
        if type(load) is not int or not 0 <= load <= 2 or rows[m-u] != load:
            raise ValueError('coherent reflected row loads required')
        if u == 0 and load % 2:
            raise ValueError('central row must have even occupancy')
        demands.append((2-load)//2 if u == 0 else 2-load)
    if sum(demands) != 2*remaining:
        raise ValueError('quotient demand/remaining mismatch')
    def edges():
        for index, marked in enumerate(complete_mask):
            check()
            if type(marked) is not int or marked not in (0, 1):
                raise ValueError('complete binary mask required')
            if marked:
                point = orbits[index][0]
                u, v = abs(point[0]-m), abs(point[1]-m)
                yield u, v
    return component_obstruction(demands, edges(), check)
