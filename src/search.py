"""Bounded seeded single-core min-conflicts search; standard library only.

CLI: python src/search.py --n 8 --seconds 2 --seed 42 --output data/run.json
Use --initial existing.json to preserve a valid incumbent and try randomized
deletion/greedy-repair cycles; --n may be larger than the initial grid. Each
repair removes between one and --delete-count points (default two), then scans
vacant cells in seeded random order. The initial pass tries additions directly.
The output file is a certificate {n, points, metadata}; stdout is its JSON
verification report. Both exact verifiers must accept before a file is written.

API: search(n, seconds, seed, initial=None, delete_count=2) returns a verified
certificate. Search uses local
random.Random(seed), no workers or threads. Wall-clock stopping means identical
seeds and time budgets need not give identical results. Metadata records seed,
iterations, elapsed_seconds, and both the requested budget and stopping reason.
The budget bounds the search loop; setup, final pruning, audit, and file I/O
add overhead. A deterministic greedy deletion supplies a valid certificate
even when the target size min(n*n, 2*n) has not been attained.
For random starts, iterations counts point moves; for initial-certificate
repair, it counts candidate-cell evaluations. Restarts counts random state
resets or repair passes, respectively. Every output reports its method.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import sys
import time

try:
    from .verify import (collinear_triples, normalized_direction,
                         verify_certificate, verify_certificate_bruteforce)
except ImportError:
    from verify import (collinear_triples, normalized_direction,
                        verify_certificate, verify_certificate_bruteforce)


def _prune(points):
    result = list(points)
    while True:
        conflicts = collinear_triples(result)
        if not conflicts:
            return result
        degree = Counter(i for triple in conflicts for i in triple)
        victim = max(degree, key=lambda i: (degree[i], i))
        result.pop(victim)


def _candidate_cost(points, index, candidate):
    """Number of triples containing candidate, all other points fixed."""
    directions = Counter()
    x, y = candidate
    for j, (px, py) in enumerate(points):
        if j != index:
            directions[normalized_direction(px - x, py - y)] += 1
    return sum(count * (count - 1) // 2 for count in directions.values())


def _search_from_initial(n, seconds, seed, initial, delete_count):
    started = time.monotonic()
    deadline = started + seconds
    original_report = verify_certificate(initial)
    original_audit = verify_certificate_bruteforce(initial)
    if not original_report["valid"] or not original_audit["valid"]:
        raise ValueError("initial certificate must pass both exact verifiers")
    embedded = {"n": n, "points": initial["points"]}
    if not verify_certificate(embedded)["valid"]:
        raise ValueError("initial points must fit the requested n grid")
    rng = random.Random(seed)
    incumbent = [tuple(point) for point in initial["points"]]
    target = min(n * n, 2 * n)
    evaluations = restarts = 0
    first = True
    while len(incumbent) < target and time.monotonic() < deadline:
        trial = list(incumbent)
        if not first and trial:
            remove = rng.randint(1, min(delete_count, len(trial)))
            removed = set(rng.sample(range(len(trial)), remove))
            trial = [point for i, point in enumerate(trial) if i not in removed]
        first = False
        occupied = set(trial)
        candidates = [(x, y) for x in range(n) for y in range(n) if (x, y) not in occupied]
        rng.shuffle(candidates)
        for point in candidates:
            if time.monotonic() >= deadline:
                break
            evaluations += 1
            if _candidate_cost(trial, -1, point) == 0:
                trial.append(point)
                if len(trial) > len(incumbent):
                    incumbent = list(trial)
                if len(incumbent) == target:
                    break
        restarts += 1
    certificate = {
        "n": n,
        "points": [list(point) for point in sorted(incumbent)],
        "metadata": {
            "method": "seeded_single_core_incumbent_deletion_greedy_repair",
            "seed": seed,
            "seconds_budget": seconds,
            "elapsed_seconds": time.monotonic() - started,
            "iterations": evaluations,
            "restarts": restarts,
            "delete_count": delete_count,
            "target_point_count": target,
            "initial_point_count": len(initial["points"]),
            "initial_normalized_sha256": original_report["normalized_sha256"],
            "initial_embedded_normalized_sha256": verify_certificate(embedded)["normalized_sha256"],
            "stopping_reason": "target_reached" if len(incumbent) == target else "time_budget",
            "reproducibility": "seeded stochastic choices; wall-clock stopping can change iteration count and result",
            "novelty_claim": False,
        },
    }
    fast = verify_certificate(certificate)
    audit = verify_certificate_bruteforce(certificate)
    if not fast["valid"] or not audit["valid"]:
        raise RuntimeError("search result failed independent validation")
    certificate["metadata"]["normalized_sha256"] = fast["normalized_sha256"]
    certificate["metadata"]["independent_validation"] = [fast["algorithm"], audit["algorithm"]]
    certificate["metadata"]["elapsed_seconds"] = time.monotonic() - started
    return certificate


def search(n, seconds, seed, initial=None, delete_count=2):
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(delete_count) is not int or delete_count < 1:
        raise ValueError("delete_count must be a positive integer")
    if initial is not None:
        return _search_from_initial(n, seconds, seed, initial, delete_count)
    started = time.monotonic()
    deadline = started + seconds
    rng = random.Random(seed)
    target = min(n * n, 2 * n)
    points = [(x, y) for x in range(n) for y in rng.sample(range(n), min(2, n))]
    best_raw = list(points)
    best_conflicts = len(collinear_triples(points))
    iterations = restarts = stagnant = 0
    solved = best_conflicts == 0
    while not solved and time.monotonic() < deadline:
        conflicts = collinear_triples(points)
        if not conflicts:
            best_raw, solved = list(points), True
            break
        if len(conflicts) < best_conflicts:
            best_raw, best_conflicts = list(points), len(conflicts)
            stagnant = 0
        else:
            stagnant += 1
        if stagnant >= max(30, 8 * n):
            points = [(x, y) for x in range(n) for y in rng.sample(range(n), min(2, n))]
            restarts += 1
            stagnant = 0
            continue
        degree = Counter(i for triple in conflicts for i in triple)
        worst = max(degree.values())
        index = rng.choice([i for i, count in degree.items() if count == worst])
        x, current_y = points[index]
        occupied_y = {py for j, (px, py) in enumerate(points) if px == x and j != index}
        candidates = [(x, y) for y in range(n) if y not in occupied_y]
        # Random walks escape plateaus; ties are resolved by the local RNG.
        if rng.random() < 0.12:
            chosen = rng.choice(candidates)
        else:
            scored = [(_candidate_cost(points, index, point), point) for point in candidates]
            minimum = min(cost for cost, _ in scored)
            chosen = rng.choice([point for cost, point in scored if cost == minimum])
        points[index] = chosen
        iterations += 1
        # Capture the final move even if the deadline expires immediately after it.
        current_conflicts = len(collinear_triples(points))
        if current_conflicts < best_conflicts:
            best_raw, best_conflicts = list(points), current_conflicts
        solved = best_conflicts == 0
    result = sorted(_prune(best_raw))
    certificate = {
        "n": n,
        "points": [list(point) for point in result],
        "metadata": {
            "method": "seeded_single_core_min_conflicts_with_greedy_pruning",
            "seed": seed,
            "seconds_budget": seconds,
            "elapsed_seconds": time.monotonic() - started,
            "iterations": iterations,
            "restarts": restarts,
            "target_point_count": target,
            "stopping_reason": "target_reached" if solved else "time_budget",
            "reproducibility": "seeded stochastic choices; wall-clock stopping can change iteration count and result",
            "novelty_claim": False,
        },
    }
    fast = verify_certificate(certificate)
    audit = verify_certificate_bruteforce(certificate)
    if not fast["valid"] or not audit["valid"]:
        raise RuntimeError("search result failed independent validation")
    certificate["metadata"]["normalized_sha256"] = fast["normalized_sha256"]
    certificate["metadata"]["independent_validation"] = [fast["algorithm"], audit["algorithm"]]
    certificate["metadata"]["elapsed_seconds"] = time.monotonic() - started
    return certificate


def _finite_seconds(value):
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("seconds must be a number") from exc
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("seconds must be finite and nonnegative")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", required=True, type=int)
    parser.add_argument("--seconds", required=True, type=_finite_seconds)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--initial", type=Path, help="valid incumbent certificate; preserved unless improved")
    parser.add_argument("--delete-count", type=int, default=2)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.n < 1:
        parser.error("n must be positive")
    initial = None
    try:
        if args.initial:
            initial = json.loads(args.initial.read_text(encoding="utf-8"))
        certificate = search(args.n, args.seconds, args.seed, initial, args.delete_count)
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verify_certificate(certificate), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
