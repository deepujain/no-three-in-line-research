"""Controlled cooling variant of the frozen paired-color walk; no unapproved n79 run."""
import argparse
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.paired_color_walk import initialize, exact_score, proposal
from src.verify import verify_certificate, verify_certificate_bruteforce


def temperature(elapsed, seconds):
    if not math.isfinite(elapsed) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('finite elapsed and positive duration required')
    fraction = max(0.0, min(1.0, elapsed / seconds))
    return 4.0 + (0.02 - 4.0) * fraction


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
    while score and (now := clock()) < deadline and (max_iterations is None or iterations < max_iterations):
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
        t = temperature(now-start, seconds)
        if delta <= 0 or rng.random() < math.exp(-delta/t):
            pi, points, score = new_pi, new_points, score+delta
            accepted += 1
            if score < best_score:
                best_pi, best_points, best_score = pi[:], set(points), score
                last_improvement = iterations
    final_temperature = temperature(clock()-start, seconds)
    cert = {'n':n, 'points':[list(p) for p in sorted(best_points)]}
    checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
    if any(c['errors'] or c['conflict_count'] != best_score for c in checks):
        raise RuntimeError('independent final score validation failed')
    return {'method':'paired-color-half-turn-swap-linear-cooling',
            'scope':'restricted heuristic, not a complete half-turn search',
            'n':n, 'seed':seed, 'seconds':seconds, 'initializer':initializer, 'initial_score':initial_score,
            'initial_temperature':4.0, 'final_temperature':final_temperature,
            'iterations':iterations, 'accepted':accepted, 'illegal':illegal, 'restarts':restarts,
            'final_current_score':score, 'best_score':best_score, 'state_kind':'valid_full_search_state' if best_score == 0 else 'invalid_full_search_state',
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
