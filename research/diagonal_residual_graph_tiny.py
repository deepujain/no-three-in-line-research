"""Isolated n<=5 necessary residual-graph bounds; no production integration.

The abstract assessor requires a COMPLETE admissible edge set. An interrupted
scan raises; it never returns a pruning verdict for a partial graph.
"""
from collections import Counter
from dataclasses import dataclass
from itertools import combinations, islice

from research.diagonal_secant_dfs_fast import (
    SecantState, pair_orbits, mirror_pair_admissible)
from src.verify import verify_certificate, verify_certificate_bruteforce


RULES = ('row_shortage', 'component_parity', 'bipartite_imbalance',
         'global_color_shortage', 'component_color_shortage')


def tiny_n(n):
    if type(n) is not int or not 2 <= n <= 5:
        raise ValueError('isolated tiny reference requires n2..5')
    return n


@dataclass(frozen=True)
class Assessment:
    needs: tuple
    edges: tuple
    violations: tuple

    @property
    def rejected(self):
        return bool(self.violations)


def assess(needs, edges, *, check=lambda: None):
    """Assess complete graph; normalize endpoint duplicates, ignore zero demand.

    At most two input occurrences per possible edge are accepted, sufficient
    for a scan from both endpoints. Calls may be interrupted at every check.
    Odd total demand is invalid for the reflection prefix contract.
    """
    check()
    needs = tuple(islice(iter(needs), 6))
    n = tiny_n(len(needs))
    if any(type(b) is not int or not 0 <= b <= 2 for b in needs) or sum(needs) % 2:
        raise ValueError('invalid residual demand')
    limit = n*(n-1)
    raw = tuple(islice(iter(edges), limit+1))
    if len(raw) > limit:
        raise ValueError('edge input exceeds tiny bound')
    canonical = set()
    for edge in raw:
        check()
        if (type(edge) not in (tuple, list) or len(edge) != 2 or
                any(type(v) is not int or not 0 <= v < n for v in edge) or edge[0] == edge[1]):
            raise ValueError('invalid edge')
        a, b = sorted(edge)
        if needs[a] and needs[b]:
            canonical.add((a, b))
    ordered = tuple(sorted(canonical))
    neighbors = [set() for _ in range(n)]
    colors = set()
    for a, b in ordered:
        check()
        neighbors[a].add(b)
        neighbors[b].add(a)
        colors.add(a+b)
    failures = set()
    if any(len(neighbors[v]) < needs[v] for v in range(n)):
        failures.add('row_shortage')
    if len(colors) < sum(needs)//2:
        failures.add('global_color_shortage')
    unseen = {v for v in range(n) if needs[v]}
    while unseen:
        check()
        root = min(unseen)
        sides, queue, component, bipartite = {root: 0}, [root], set(), True
        while queue:
            check()
            v = queue.pop()
            if v in component:
                continue
            component.add(v)
            unseen.discard(v)
            for w in sorted(neighbors[v]):
                check()
                if w not in sides:
                    sides[w] = 1-sides[v]
                    queue.append(w)
                elif sides[w] == sides[v]:
                    bipartite = False
        demand = sum(needs[v] for v in component)
        if demand % 2:
            failures.add('component_parity')
        if bipartite and sum(needs[v] for v in component if sides[v] == 0) != sum(
                needs[v] for v in component if sides[v] == 1):
            failures.add('bipartite_imbalance')
        component_colors = {a+b for a, b in ordered if a in component}
        if demand % 2 == 0 and len(component_colors) < demand//2:
            failures.add('component_color_shortage')
    check()
    return Assessment(needs, ordered, tuple(rule for rule in RULES if rule in failures))


def scan(state, *, check=lambda: None):
    """Read a coherent frozen SecantState without mutation; complete scan first."""
    tiny_n(state.n)
    if type(state) is not SecantState:
        raise ValueError('frozen reflection state required')
    check()
    needs = tuple(state.target[r]-state.rows[r] for r in range(state.n))
    sums = {x+y for x, y in state.points}
    edges = []
    for orbit in pair_orbits(state.n):
        check()
        if mirror_pair_admissible(state, orbit, sums):
            edges.append(orbit[0])
    check()
    return assess(needs, edges, check=check)


def census(n, *, use_bounds=True, check=lambda: None):
    """Tiny full-row reference, preserving surviving branch and witness order."""
    tiny_n(n)
    if type(use_bounds) is not bool:
        raise ValueError('boolean bound toggle required')
    nodes, witnesses, pruned = 0, [], Counter()
    orbits = pair_orbits(n)
    indices = {orbit[0]: i for i, orbit in enumerate(orbits)}
    for deficit in range(n):
        for diagonal in range(n):
            check()
            state = SecantState(n, deficit)
            assert state.push(((diagonal, diagonal),))
            def visit():
                nonlocal nodes
                check()
                nodes += 1
                result = scan(state, check=check)
                if not any(result.needs):
                    cert = {'n': n, 'points': [list(p) for p in sorted(state.points)]}
                    proofs = (verify_certificate(cert), verify_certificate_bruteforce(cert))
                    if not all(p['valid'] and p['point_count'] == 2*n-1 for p in proofs):
                        raise RuntimeError('leaf failed independent verifiers')
                    witnesses.append((deficit, diagonal, proofs[0]['normalized_sha256']))
                    return
                if use_bounds and result.rejected:
                    pruned.update(result.violations)
                    return
                choices = []
                for row, need in enumerate(result.needs):
                    if need:
                        viable = [indices[edge] for edge in result.edges if row in edge]
                        choices.append((len(viable), row, need, viable))
                _, row, need, viable = min(choices, key=lambda item: (item[0], item[1]))
                for batch in combinations(viable, need):
                    check()
                    pushed = 0
                    try:
                        for index in batch:
                            if not state.push(orbits[index]):
                                break
                            pushed += 1
                        else:
                            visit()
                    finally:
                        for _ in range(pushed):
                            state.pop()
            visit()
    return {'n': n, 'nodes': nodes, 'witnesses': witnesses,
            'rule_hits': {name: pruned[name] for name in RULES}}
