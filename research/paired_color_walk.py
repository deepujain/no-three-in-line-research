"""Restricted half-turn paired-color heuristic; no n79 run without approval."""
import argparse
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.trade_search import point_conflicts
from src.verify import verify_certificate, verify_certificate_bruteforce


def paired_points(pi):
    n = len(pi)
    if n < 3 or n % 2 == 0 or any(type(x) is not int for x in pi) or sorted(pi) != list(range(n)):
        raise ValueError('odd permutation of size at least three required')
    sigma = [n-1-pi[n-1-r] for r in range(n)]
    if any(a == b for a, b in zip(pi, sigma)):
        raise ValueError('paired matchings overlap')
    return {(r, col) for r in range(n) for col in (pi[r], sigma[r])}


def exact_score(points):
    points = set(points)
    return sum(point_conflicts(p, points-{p}) for p in points) // 3


def proposal(pi, points, a, b):
    n = len(pi)
    if type(a) is not int or type(b) is not int or not (0 <= a < n and 0 <= b < n) or a == b:
        raise ValueError('two distinct in-range rows required')
    new_pi = list(pi)
    new_pi[a], new_pi[b] = new_pi[b], new_pi[a]
    try:
        new_points = paired_points(new_pi)
    except ValueError:
        return None
    removed, added = points-new_points, new_points-points
    remaining = set(points); delta = 0
    for p in sorted(removed):
        remaining.remove(p)
        delta -= point_conflicts(p, remaining)
    for p in sorted(added):
        delta += point_conflicts(p, remaining)
        remaining.add(p)
    if remaining != new_points:
        raise RuntimeError('point update invariant')
    return new_pi, new_points, delta


def initialize(n, rng, deadline, clock):
    """Try at most 32 random permutations; use cyclic shift as a bounded fallback."""
    for _ in range(32):
        if clock() >= deadline:
            break
        pi = list(range(n))
        rng.shuffle(pi)
        try:
            points = paired_points(pi)
        except ValueError:
            continue
        return pi, points, 'seeded_random'
    pi = [(r+1) % n for r in range(n)]
    return pi, paired_points(pi), 'cyclic_fallback'


def walk(n, seed, seconds, max_iterations=None, *, clock=time.monotonic):
    if type(n) is not int or not 3 <= n <= 79 or n % 2 != 1:
        raise ValueError('odd n in 3..79 required')
    if type(seed) is not int or isinstance(seconds, bool) or not isinstance(seconds, (float, int)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('invalid seed or soft time limit')
    if max_iterations is not None and (type(max_iterations) is not int or max_iterations < 0):
        raise ValueError('invalid iteration cap')
    rng = random.Random(seed)
    start = clock(); deadline = start + seconds
    pi, points, initializer = initialize(n, rng, deadline, clock)
    score = exact_score(points); initial_score = score
    best_pi, best_points, best_score = pi[:], set(points), score
    iterations = accepted = restarts = illegal = 0
    last_improvement = 0
    while score and clock() < deadline and (max_iterations is None or iterations < max_iterations):
        if iterations-last_improvement >= 5000:
            pi, points, score = best_pi[:], set(best_points), best_score
            last_improvement = iterations; restarts += 1
        a, b = rng.sample(range(n), 2)
        move = proposal(pi, points, a, b)
        iterations += 1
        if move is None:
            illegal += 1
            continue
        new_pi, new_points, delta = move
        if delta <= 0 or rng.random() < math.exp(-delta/4.0):
            pi, points, score = new_pi, new_points, score+delta
            accepted += 1
            if score < best_score:
                best_pi, best_points, best_score = pi[:], set(points), score
                last_improvement = iterations
    cert = {'n':n, 'points':[list(p) for p in sorted(best_points)]}
    checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
    if any(c['errors'] or c['conflict_count'] != best_score for c in checks):
        raise RuntimeError('independent final score validation failed')
    return {'method':'paired-color-half-turn-swap-walk', 'scope':'restricted heuristic, not a complete half-turn search',
            'n':n, 'seed':seed, 'seconds':seconds, 'initializer':initializer, 'initial_score':initial_score,
            'iterations':iterations, 'accepted':accepted,
            'illegal':illegal, 'restarts':restarts, 'best_score':best_score,
            'state_kind':'valid_full_search_state' if best_score == 0 else 'invalid_full_search_state',
            'best_pi':best_pi, 'best_points':cert['points'],
            'elapsed_seconds_including_final_checks':clock()-start,
            'score_checks':['integer_normalized_slopes','integer_cross_products']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n', type=int, required=True); p.add_argument('--seed', type=int, required=True)
    p.add_argument('--seconds', type=float, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-iterations', type=int)
    args = p.parse_args()
    report = walk(args.n, args.seed, args.seconds, args.max_iterations)
    with args.output.open('x') as f:
        json.dump(report, f, sort_keys=True, indent=2); f.write('\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
