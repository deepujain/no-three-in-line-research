"""Independent tiny-only determinant/combinatorial oracle; never load n79 data."""
from collections import Counter
from itertools import combinations, permutations, product
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import blocker_guided_eight_arc_scaffold157 as m


def det(a, b, c):
    return a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1])


def triples(points):
    return tuple(t for t in combinations(sorted(points), 3) if det(*t) == 0)


def match(points):
    return len(points) == len({p[0] for p in points}) == len({p[1] for p in points})


def cycles(p):
    assert sorted(p) == list(range(len(p)))
    seen = set(); lengths = []
    for i in range(len(p)):
        if i in seen:
            continue
        count = 0
        while i not in seen:
            seen.add(i); count += 1; i = p[i]
        lengths.append(count)
    return sorted(lengths)


def oracle_pool(n, A, S, budget, limit, counts):
    cells = []
    for q in product(range(n), repeat=2):
        if q in S:
            continue
        pairs = tuple((i, j) for i, j in combinations(range(len(A)), 2)
                      if det(A[i], A[j], q) == 0)
        # Independent set cover by exhaustive deletion subsets: no directions.
        lower = next(size for size in range(len(A)+1)
                     if any(all(i in F or j in F for i, j in pairs)
                            for F in combinations(range(len(A)), size)))
        buckets = m.partition(A, q, m.new_counters(), lambda: None)
        represented = {(i, j) for i, j in combinations(range(len(A)), 2)
                       if any(mask >> i & 1 and mask >> j & 1 for mask in buckets)}
        assert represented == set(pairs)
        assert sum(mask.bit_count()-1 for mask in buckets) == lower
        counts['outside_points_and_exact_minimum_covers'] += 1
        counts['four_point_buckets'] += sum(mask.bit_count() == 4 for mask in buckets)
        if lower <= budget:
            cells.append((lower, q, pairs))
    return sorted(cells)[:limit]


def check_fixture(n, A, k, limit, counts, examples):
    A = tuple(sorted(A)); outside = sorted(set(product(range(n), repeat=2))-set(A))
    S = set(A) | {outside[-1]}
    c = m.new_counters()
    expected_pool = oracle_pool(n, A, S, 2*k, limit, counts)
    pool = m.make_pool(n, A, S, 2*k, c, lambda: None, limit=limit)
    assert [(p.lower, p.point) for p in pool] == [(x, q) for x, q, _ in expected_pool]
    arcs = m.make_arcs(A, pool, c, lambda: None)
    expected_arcs = sorted((p.lower, p.point, a, b) for p in pool
                          for a in A for b in A if a[0] == p.point[0] and b[1] == p.point[1])
    assert [(pool[a.pool].lower, pool[a.pool].point, A[a.a], A[a.b]) for a in arcs] == expected_arcs
    tables = m.make_tables(A, pool, c, lambda: None)
    for (i, j), (old, new) in tables.items():
        assert old == sum(1 << h for h, p in enumerate(A) if not det(pool[i].point, pool[j].point, p))
        assert new == sum(1 << h for h, p in enumerate(pool) if h not in (i, j) and not det(pool[i].point, pool[j].point, p.point))
        counts['pair_tables'] += 1
    expected = set()
    for ids in combinations(range(len(arcs)), k):
        F = tuple(A[h] for ai in ids for h in (arcs[ai].a, arcs[ai].b))
        Q = tuple(pool[arcs[ai].pool].point for ai in ids)
        counts['arc_families_enumerated'] += 1
        if len(set(F)) != 2*k or not match(F) or len(set(Q)) != k or not match(Q):
            continue
        P = (set(A)-set(F)) | set(Q)
        bad_triples = triples(P)
        for t in bad_triples:
            counts['oracle_conflicts_with_%d_new_points' % sum(p in set(Q) for p in t)] += 1
        if bad_triples:
            continue
        expected.add(ids)
    found = []
    old = m.conflict_masks(A, triples(A))
    kernel = m.Constructor(A, pool, arcs, tables, old, c, lambda: None, k)
    assert kernel.run(lambda ids: found.append(ids) or False) is False
    assert {tuple(sorted(ids)) for ids in found} == expected
    assert kernel.root_restored and not kernel.path and c['arc_admissions'] == c['arc_rollbacks']
    counts['complete_fixture_families'] += 1
    counts['unique_scaffolds'] += len(expected)
    counts['scaffold_orderings'] += len(found)
    counts['nonincreasing_scaffold_orderings'] += sum(tuple(sorted(ids)) != ids for ids in found)
    for ids in expected:
        selected, Q, supports, F, R, P, forced = m.scaffold(A, S, pool, arcs, ids, old, tables, lambda: None)
        assert len(P) == len(A)-k and len(S-set(P)) == 2*k+1 and len(set(P)-S) == k
        domains = m.residual_domains(n, P, S, supports, c, lambda: None, {})
        expected_domains = []
        for _, b in supports:
            mask = 0
            for j, (a, _) in enumerate(supports):
                t = (b[0], a[1])
                assert t in S or t not in set(P)
                if t not in S and all(det(x, y, t) for x, y in combinations(P, 2)):
                    mask |= 1 << j
                counts['residual_cells'] += 1
            expected_domains.append(mask)
        assert domains == tuple(expected_domains)
        cover = m.frozen.maximum_matching(domains, k, c, lambda: None)
        expected_matching = max((len(cols) for size in range(k+1)
             for rows in combinations(range(k), size) for cols in permutations(range(k), size)
             if all(domains[i] >> j & 1 for i, j in zip(rows, cols))), default=0)
        assert cover['matching_size'] == expected_matching
        allowed_cycles = []
        for tau in permutations(range(k)):
            sigma = tuple(v for i in range(k) for v in (2*i+1, 2*tau[i]))
            assert cycles(sigma) == [2*x for x in cycles(tau)]
            counts['expanded_cycle_permutations'] += 1
            if cycles(tau) == [k] and all(domains[i] >> tau[i] & 1 for i in range(k)):
                allowed_cycles.append(tau)
                plan = {(supports[i][1][0], supports[tau[i]][0][1]) for i in range(k)}
                assert len(plan) == k and match(tuple(plan)) and not plan & (S | set(P))
                assert all(Counter(p[h] for p in set(P) | plan) == Counter(p[h] for p in A) for h in (0, 1))
                conflicts = triples(set(P) | plan)
                if conflicts and 'individually_safe_jointly_invalid_plan' not in examples:
                    examples['individually_safe_jointly_invalid_plan'] = {
                        'n': n, 'A': A, 'S': sorted(S), 'P': P, 'supports': supports,
                        'domains': domains, 'tau': tau, 'plan': sorted(plan), 'conflicts': conflicts}
        actual = m.root_cycle(domains, c, lambda: None)
        assert (actual is None) == (not allowed_cycles)
        if actual is not None:
            assert actual in allowed_cycles
            counts['root_ready_scaffolds'] += 1


def main():
    counts = Counter(); examples = {}
    # All size-four old subsets on 3x3 with degree at most two.
    for A in combinations(tuple(product(range(3), repeat=2)), 4):
        if any(max(Counter(p[h] for p in A).values()) > 2 for h in (0, 1)):
            continue
        for k in (1, 2):
            check_fixture(3, A, k, 5, counts, examples)
    # Depth-three fixtures use <=12 arcs on permutations or <=4 pool points,
    # keeping complete enumeration below the production4096-attempt cap.
    rng = random.Random(20261127)
    for extra in ((), ((0, 3),), ((0, 3), (1, 2)), ((0, 3), (1, 2), (2, 0))):
        check_fixture(4, {(i, i) for i in range(4)} | set(extra), 2, 12, counts, examples)
    check_fixture(5, {(i, i) for i in range(4)} | {(4, 0), (0, 4)}, 1, 64, counts, examples)
    for _ in range(100):
        cols = rng.sample(list(range(6)), 6)
        A = {(i, cols[i]) for i in range(6)}
        if any(sum(det(x, y, p) == 0 for p in A) > 4 for x, y in combinations(A, 2)):
            continue
        check_fixture(6, A, 3, 12, counts, examples)
    for _ in range(100):
        A = set()
        for p in rng.sample(list(product(range(6), repeat=2)), 36):
            if all(sum(q[h] == p[h] for q in A) < 2 for h in (0, 1)):
                A.add(p)
            if len(A) == 8:
                break
        if any(sum(det(x, y, p) == 0 for p in A) > 4 for x, y in combinations(A, 2)):
            continue
        check_fixture(6, A, 3, 4, counts, examples)
    # Explicit four-collinear bucket, with candidate on both sides of line.
    A = ((0, 0), (1, 1), (2, 2), (3, 3), (0, 3))
    oracle_pool(5, A, set(A), 6, 64, counts)
    # Every directed graph through k=3, including loops and short-cycle covers.
    for k in (1, 2, 3):
        perms = list(permutations(range(k)))
        for bits in range(1 << (k*k)):
            domains = tuple((bits >> (k*i)) & ((1 << k)-1) for i in range(k))
            expected = [p for p in perms if cycles(p) == [k] and all(domains[i] >> p[i] & 1 for i in range(k))]
            result = m.root_cycle(domains, m.new_counters(), lambda: None)
            assert (result is None) == (not expected)
            assert result is None or result in expected
            counts['all_small_directed_graphs'] += 1
    assert counts['four_point_buckets'] and counts['nonincreasing_scaffold_orderings']
    assert all(counts['oracle_conflicts_with_%d_new_points' % i] for i in range(4)), dict(counts)
    result = {'status': 'PASS', 'scope': 'Frozen source and deterministic tiny boards only; no n79 loading/scoring/search or completion DFS.',
              'counts': dict(counts), 'examples': examples,
              'pins': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(m.__file__), ROOT/'tests/test_blocker_guided_eight_arc_scaffold157.py', Path(__file__))}}
    out = ROOT/'data/blocker-guided-eight-arc-scaffold-independent-tiny-audit.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'status': result['status'], 'counts': result['counts'], 'examples': list(examples)}, sort_keys=True))


if __name__ == '__main__':
    main()
