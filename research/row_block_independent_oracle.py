"""Independent tiny-only row-block oracle; no production imports or fixture IO.

All state entry points restrict n to 2..4. Direct determinants enumerate triples;
the line index instead groups projections along every bounded primitive normal.
The reference transition is intentionally slow and is not a production search.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from math import gcd
import random


def tiny_points(points):
    points = tuple(sorted(tuple(p) for p in points))
    assert len(points) <= 16 and len(set(points)) == len(points)
    assert all(len(p) == 2 and all(type(v) is int and 0 <= v <= 3 for v in p)
               for p in points)
    return points


def row_state(points, n):
    assert type(n) is int and 2 <= n <= 4, 'synthetic n2..4 only'
    points = tiny_points(points)
    assert len(points) == 2*n - 1 and all(max(p) < n for p in points)
    counts = Counter(y for x, y in points)
    assert sorted(counts.values()) == [1] + [2]*(n-1)
    return points


def states(n):
    assert type(n) is int and 2 <= n <= 4
    pairs = tuple(combinations(range(n), 2))
    for deficient in range(n):
        for singleton in range(n):
            for rows in product(pairs, repeat=n-1):
                it = iter(rows)
                points = tuple(sorted((x, y) for y in range(n)
                                      for x in ((singleton,) if y == deficient else next(it))))
                yield row_state(points, n)


def determinant(p, q, r):
    return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])


def line_key(p, q):
    """Fraction slope normal, separate from a pair-cross-product constructor."""
    tiny_points((p, q))
    if p[0] == q[0]:
        return (1, 0, p[0])
    slope = Fraction(q[1]-p[1], q[0]-p[0])
    a, b = slope.numerator, -slope.denominator
    c = a*p[0] + b*p[1]
    if a < 0 or (a == 0 and b < 0):
        a, b, c = -a, -b, -c
    return a, b, c


def triples(points):
    return tuple(t for t in combinations(tiny_points(points), 3)
                 if determinant(*t) == 0)


def score(points, weights=None):
    weights = {} if weights is None else weights
    assert all(type(w) is int and 1 <= w <= 65535 for w in weights.values())
    conflicts = triples(points)
    return len(conflicts), sum(weights.get(line_key(t[0], t[1]), 1) for t in conflicts)


def expected_index(points, n):
    points = row_state(points, n)
    result = {}
    # Every line through two n-grid cells has a primitive normal bounded by n-1.
    for a, b in product(range(1-n, n), repeat=2):
        if not (a > 0 or (a == 0 and b > 0)) or gcd(abs(a), abs(b)) != 1:
            continue
        groups = defaultdict(list)
        for x, y in points:
            groups[a*x+b*y].append((x, y))
        for c, members in groups.items():
            if len(members) >= 2:
                result[(a, b, c)] = tuple(members)
    return result


def row_unary(points, n, row, weights=None):
    points = row_state(points, n)
    assert type(row) is int and 0 <= row < n
    retained = tuple(p for p in points if p[1] != row)
    base = score(retained, weights)[1]
    return tuple(score(retained + ((x, row),), weights)[1] - base for x in range(n))


def row_alternatives(points, n, row, weights=None):
    points = row_state(points, n)
    old = tuple(p for p in points if p[1] == row)
    retained = tuple(p for p in points if p[1] != row)
    old_w = score(points, weights)[1]
    base = score(retained, weights)[1]
    costs = row_unary(points, n, row, weights)
    alternatives = []
    for xs in combinations(range(n), len(old)):
        added = tuple((x, row) for x in xs)
        if added == old:
            continue
        changed = tuple(sorted(retained + added))
        u, w = score(changed, weights)
        unary = sum(costs[x] for x in xs)
        assert w == base + unary, 'same-row mixed-triple additivity failed'
        alternatives.append({'added': added, 'points': changed, 'U': u, 'W': w,
                             'delta': w-old_w, 'unary_sum': unary})
    return alternatives


def best_row_alternatives(points, n, row, weights=None):
    alternatives = row_alternatives(points, n, row, weights)
    if not alternatives:
        return None, ()
    minimum = min(a['unary_sum'] for a in alternatives)
    return minimum, tuple(a['added'] for a in alternatives if a['unary_sum'] == minimum)


def deficient_row(points, n):
    points = row_state(points, n)
    counts = Counter(y for x, y in points)
    return next(y for y in range(n) if counts[y] == 1)


def migration(points, n, donor, destination, weights=None):
    points = row_state(points, n)
    deficient = deficient_row(points, n)
    assert donor in points and donor[1] != deficient
    assert destination not in points and destination[1] == deficient
    assert 0 <= destination[0] < n
    remaining = tuple(p for p in points if p != donor)
    changed = row_state(remaining + (destination,), n)
    old_w = score(points, weights)[1]
    remove_w = score(remaining, weights)[1] - old_w
    u, w = score(changed, weights)
    insert_w = w - score(remaining, weights)[1]
    return {'points': changed, 'U': u, 'W': w, 'delta': w-old_w,
            'removal_delta': remove_w, 'insertion_delta': insert_w,
            'deficient_row': donor[1]}


def migrations(points, n, weights=None):
    points = row_state(points, n)
    deficient = deficient_row(points, n)
    for donor in points:
        if donor[1] == deficient:
            continue
        for x in range(n):
            destination = (x, deficient)
            if destination not in points:
                yield donor, destination, migration(points, n, donor, destination, weights)


class OracleCap(Exception):
    pass


def penalized_weights(points, weights, max_keys=65536, max_weight=65535):
    violated = sorted({line_key(t[0], t[1]) for t in triples(points)})
    result = dict(weights)
    if len(set(weights) | set(violated)) > max_keys:
        raise OracleCap('weight_key_cap')
    if any(weights.get(key, 1) + 1 > max_weight for key in violated):
        raise OracleCap('weight_value_cap')
    for key in violated:
        result[key] = weights.get(key, 1) + 1
    assert score(points, result)[1] - score(points, weights)[1] == score(points)[0]
    return result


def weighted_fixture(points, n):
    return {key: 2 + (abs(key[0])*7 + abs(key[1])*5 + abs(key[2])*3) % 11
            for key in expected_index(points, n)}


@dataclass(frozen=True)
class Boundary:
    n: int
    points: tuple
    weights: tuple
    U: int
    W: int
    best_points: tuple
    best_U: int
    step: int
    stagnation: int
    penalties: int
    rng_state: tuple


def boundary(points, n, weights=None, seed=275149, rng_state=None,
             best_points=None, step=0, stagnation=0, penalties=0):
    points = row_state(points, n)
    weights = dict(weights or {})
    rng = random.Random(seed)
    if rng_state is not None:
        rng.setstate(rng_state)
    u, w = score(points, weights)
    best_points = points if best_points is None else row_state(best_points, n)
    best_u = score(best_points)[0]
    assert best_u <= u
    return Boundary(n, points, tuple(sorted(weights.items())), u, w,
                    best_points, best_u, step, stagnation, penalties, rng.getstate())


def reference_step(old, max_keys=65536, max_weight=65535):
    """One exact tiny policy step. Immutable input survives every cap failure."""
    if old.U == 0:
        return old
    points, weights, n = old.points, dict(old.weights), old.n
    rng = random.Random()
    rng.setstate(old.rng_state)
    step = old.step + 1
    if step % 16:
        rows = sorted({p[1] for t in triples(points) for p in t})
        row = rng.choice(rows)
        _, best = best_row_alternatives(points, n, row, weights)
        added = rng.choice(best)
        changed = tuple(sorted(tuple(p for p in points if p[1] != row) + added))
    else:
        deficient = deficient_row(points, n)
        donors = [p for p in points if p[1] != deficient]
        destinations = [(x, deficient) for x in range(n) if (x, deficient) not in points]
        sampled = {}
        for _ in range(32):
            donor, destination = rng.choice(donors), rng.choice(destinations)
            move = migration(points, n, donor, destination, weights)
            sampled[move['points']] = move['W']
        minimum = min(sampled.values())
        changed = rng.choice(sorted(p for p, w in sampled.items() if w == minimum))
    u, w = score(changed, weights)
    improved = u < old.best_U
    best_points, best_u = (changed, u) if improved else (old.best_points, old.best_U)
    stagnation = 0 if improved else old.stagnation + 1
    penalties = old.penalties
    if u == 0:
        stagnation = 0
    elif stagnation == 32:
        weights = penalized_weights(changed, weights, max_keys, max_weight)
        w = score(changed, weights)[1]
        stagnation, penalties = 0, penalties + 1
    return Boundary(n, changed, tuple(sorted(weights.items())), u, w,
                    best_points, best_u, step, stagnation, penalties, rng.getstate())


def two_row_counterexample():
    retained, first, second = ((0, 0),), (1, 1), (2, 2)
    assert score(retained)[0] == score(retained + (first,))[0] == score(retained + (second,))[0] == 0
    assert score(retained + (first, second))[0] == 1
    return {'retained': retained, 'first': first, 'second': second,
            'individual_increments': [0, 0], 'joint_increment': 1}
