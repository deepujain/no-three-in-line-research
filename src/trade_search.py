"""Single-core annealing of exact degree-two grid states, standard library only.

Full states are two disjoint permutations: every row and column has two points.
A legal swap in either permutation is an alternating rectangle trade. Occasional
alternating-cycle recoloring preserves the point set and exposes other trades.
Scores count every collinear triple exactly with integer directions; axis triples
are absent by construction. Invalid full states are explicitly search states,
never certificates. Every saved incumbent passes both independent verifiers.
"""

import argparse
from collections import Counter, deque, OrderedDict
import itertools
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


def point_conflicts(point, others):
    """Exact number of triples through point with both other points in others."""
    x, y = point
    counts = Counter(normalized_direction(px - x, py - y) for px, py in others)
    return sum(count * (count - 1) // 2 for count in counts.values())


def degree_two(points, n):
    return (len(points) == 2 * n and len(set(points)) == 2 * n
            and Counter(x for x, _ in points) == Counter({i: 2 for i in range(n)})
            and Counter(y for _, y in points) == Counter({i: 2 for i in range(n)}))


def decompose(points, n):
    """Color each even bipartite cycle into two permutation matchings."""
    points = set(points)
    if not degree_two(points, n):
        raise ValueError("points must have row and column degree exactly two")
    adjacency = {i: [] for i in range(2 * n)}
    for row, column in sorted(points):
        adjacency[row].append(n + column)
        adjacency[n + column].append(row)
    permutations = [[None] * n for _ in range(2)]
    used = set()
    for start in range(n):
        if permutations[0][start] is not None:
            continue
        current, color = start, 0
        while True:
            options = [neighbor for neighbor in adjacency[current]
                       if tuple(sorted((current, neighbor))) not in used]
            if not options:
                break
            neighbor = min(options)
            used.add(tuple(sorted((current, neighbor))))
            row, column = (current, neighbor - n) if current < n else (neighbor, current - n)
            permutations[color][row] = column
            current, color = neighbor, 1 - color
        if current != start:
            raise RuntimeError("degree-two component did not close")
    if any(sorted(permutation) != list(range(n)) for permutation in permutations):
        raise RuntimeError("cycle decomposition did not produce permutations")
    return permutations


def state_points(permutations):
    return {(row, column) for permutation in permutations for row, column in enumerate(permutation)}


def random_permutations(n, rng):
    first = list(range(n))
    rng.shuffle(first)
    shift = rng.randrange(1, n)
    return [first, first[shift:] + first[:shift]]


def complete_seed(seed, n, rng):
    """Complete a full (n-1)-grid seed by removing two edges and adding four.

    This produces a degree-two state, generally invalid geometrically. Missing
    row/column get two incident edges; every existing degree stays two.
    """
    points = {tuple(point) for point in seed["points"]}
    rows, columns = Counter(x for x, _ in points), Counter(y for _, y in points)
    missing_rows = [i for i in range(n) if rows[i] == 0]
    missing_columns = [i for i in range(n) if columns[i] == 0]
    if len(missing_rows) != 1 or len(missing_columns) != 1 or any(
            rows[i] not in (0, 2) or columns[i] not in (0, 2) for i in range(n)):
        raise ValueError("seed must leave exactly one empty row and column, with all others degree two")
    candidates = sorted(points)
    first = rng.choice(candidates)
    second = rng.choice([point for point in candidates if point[0] != first[0] and point[1] != first[1]])
    row, column = missing_rows[0], missing_columns[0]
    points.difference_update((first, second))
    points.update(((first[0], column), (second[0], column), (row, first[1]), (row, second[1])))
    return decompose(points, n)


def swap_proposal(permutations, points, color, first, second):
    """Return (exact score delta, new point set), or None for an illegal swap."""
    chosen, other = permutations[color], permutations[1 - color]
    a, b = chosen[first], chosen[second]
    if first == second or b == other[first] or a == other[second]:
        return None
    old_first, old_second = (first, a), (second, b)
    new_first, new_second = (first, b), (second, a)
    after_first_removal = points - {old_first}
    remaining = after_first_removal - {old_second}
    delta = -point_conflicts(old_first, after_first_removal) - point_conflicts(old_second, remaining)
    delta += point_conflicts(new_first, remaining)
    delta += point_conflicts(new_second, remaining | {new_first})
    return delta, remaining | {new_first, new_second}


def accept_swap(permutations, color, first, second):
    permutation = permutations[color]
    permutation[first], permutation[second] = permutation[second], permutation[first]


def rotation_proposal(permutations, points, color, rows):
    """Rotate two/three matching edges; exact delta or None for collisions."""
    rows = tuple(rows)
    if len(rows) not in (2, 3) or len(set(rows)) != len(rows):
        raise ValueError("a rotation needs two or three distinct rows")
    chosen, other = permutations[color], permutations[1 - color]
    columns = [chosen[row] for row in rows]
    replacements = [(row, columns[(i + 1) % len(rows)]) for i, row in enumerate(rows)]
    if any(column == other[row] for row, column in replacements):
        return None
    working = set(points)
    delta = 0
    for row, column in zip(rows, columns):
        point = row, column
        working.remove(point)
        delta -= point_conflicts(point, working)
    for point in replacements:
        delta += point_conflicts(point, working)
        working.add(point)
    return delta, working


def accept_rotation(permutations, color, rows):
    columns = [permutations[color][row] for row in rows]
    for i, row in enumerate(rows):
        permutations[color][row] = columns[(i + 1) % len(rows)]


def rectangle_proposal(points, first, second):
    """Uncolored two-edge switch; reversed edge order is the same cross pairing.

    In a bipartite rectangle, of the two row-to-column pairings one is the
    original edge pair and the other is the unique nontrivial replacement.
    No matching-color restriction is imposed.
    """
    row_a, column_a = first
    row_b, column_b = second
    if row_a == row_b or column_a == column_b:
        return None
    replacements = (row_a, column_b), (row_b, column_a)
    if any(point in points for point in replacements):
        return None
    after_first = points - {first}
    remaining = after_first - {second}
    delta = -point_conflicts(first, after_first) - point_conflicts(second, remaining)
    delta += point_conflicts(replacements[0], remaining)
    delta += point_conflicts(replacements[1], remaining | {replacements[0]})
    return delta, remaining | set(replacements)


def audit_rectangles(state, seconds=60):
    """Exhaust every unordered old-edge pair, returning exact finite scope."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    started = time.monotonic()
    n = state["n"]
    points, score, digest = checked_full_state(state, n)
    deadline = started + seconds
    result = {"audit": "all_uncolored_two_edge_rectangle_switches", "n": n,
              "source_normalized_sha256": digest, "source_score": score,
              "point_pair_count": len(points) * (len(points) - 1) // 2,
              "point_pairs_examined": 0, "same_axis_edge_pairs": 0,
              "occupied_replacement_rejections": 0, "legal_switch_count": 0,
              "improving_switch_count": 0, "delta_histogram": {},
              "status": "incomplete", "minimum_neighbor_score": None,
              "best_neighbor_state": None,
              "scope": "Both row-to-column pairings are considered: the old edges are the identity pairing and the crossed edges are the unique nontrivial switch; reversed old-edge order is deduplicated. This audit covers one fixed state's two-edge switches only."}
    histogram = Counter()
    for first, second in itertools.combinations(sorted(points), 2):
        if time.monotonic() >= deadline:
            result["status"] = "timeout_incomplete"
            break
        result["point_pairs_examined"] += 1
        if first[0] == second[0] or first[1] == second[1]:
            result["same_axis_edge_pairs"] += 1
            continue
        proposal = rectangle_proposal(points, first, second)
        if proposal is None:
            result["occupied_replacement_rejections"] += 1
            continue
        delta, changed = proposal
        histogram[delta] += 1
        result["legal_switch_count"] += 1
        result["improving_switch_count"] += delta < 0
        if result["minimum_neighbor_score"] is None or score + delta < result["minimum_neighbor_score"]:
            result["minimum_neighbor_score"] = score + delta
            result["best_neighbor_state"] = {"n": n, "points": [list(p) for p in sorted(changed)],
                                              "state_kind": "invalid_full_search_state" if score + delta else "valid_full_search_state",
                                              "valid": score + delta == 0, "collinear_triple_count": score + delta}
            result["best_switch_old_edges"] = [list(first), list(second)]
    else:
        result["status"] = "complete"
    result["delta_histogram"] = dict(sorted(histogram.items()))
    if result["best_neighbor_state"] is not None:
        _, best_score, best_hash = checked_full_state(result["best_neighbor_state"], n)
        if best_score != result["minimum_neighbor_score"]:
            raise RuntimeError("rectangle audit score mismatch")
        result["best_neighbor_state"]["normalized_sha256"] = best_hash
        result["best_neighbor_state"]["independent_audit"] = ["integer_normalized_slopes", "integer_cross_products"]
    result["elapsed_seconds"] = time.monotonic() - started
    return result


def checked_full_state(certificate, n):
    """Validate schema/degrees and independently recompute a possibly nonzero score."""
    if not isinstance(certificate, dict):
        raise ValueError("resume state must be an object")
    fast, slow = verify_certificate(certificate), verify_certificate_bruteforce(certificate)
    if certificate.get("n") != n or fast["errors"] or slow["errors"]:
        raise ValueError("resume state schema/grid failed independent validation")
    points = {tuple(point) for point in certificate["points"]}
    if not degree_two(points, n) or fast["conflict_count"] != slow["conflict_count"]:
        raise ValueError("resume state must have degree two and agreeing exact scores")
    return points, fast["conflict_count"], fast["normalized_sha256"]


def recolor_cycle(permutations, start):
    """Swap matching colors on one alternating cycle; points are unchanged."""
    first, second = permutations
    inverse_second = {column: row for row, column in enumerate(second)}
    cycle, row = [], start
    while row not in cycle:
        cycle.append(row)
        row = inverse_second[first[row]]
    for row in cycle:
        first[row], second[row] = second[row], first[row]
    return len(cycle)


def _independent_certificate(certificate):
    reports = [verify_certificate(certificate), verify_certificate_bruteforce(certificate)]
    if not all(report["valid"] for report in reports):
        raise ValueError("certificate failed independent validation")
    return reports


def _prune(points):
    points = sorted(points)
    while True:
        triples = collinear_triples(points)
        if not triples:
            return points
        counts = Counter(i for triple in triples for i in triple)
        points.pop(max(counts, key=lambda i: (counts[i], i)))


def search(n, seconds, seed, max_iterations=None, initial=None, temperature=2.5,
           cooling_period=5000, recolor_period=200, restart_period=20000,
           resume_state=None, move_kind="pair", focus_probability=0.0,
           tabu_size=0, focus_refresh_period=200, history_size=10000):
    """Return {incumbent, search_state, run}; deterministic operation cap optional.

    seconds=None means stop only at max_iterations. Wall-clock stopping is not
    deterministic. All temperatures/caps are recorded; elapsed includes audits.
    """
    if type(n) is not int or n < 2:
        raise ValueError("n must be an integer at least two")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if seconds is not None and (isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0):
        raise ValueError("seconds must be finite and nonnegative, or None")
    if max_iterations is not None and (type(max_iterations) is not int or max_iterations < 0):
        raise ValueError("max_iterations must be a nonnegative integer")
    if seconds is None and max_iterations is None:
        raise ValueError("a time or operation bound is required")
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    if any(type(value) is not int or value < 1 for value in (cooling_period, recolor_period, restart_period)):
        raise ValueError("periods must be positive integers")
    if move_kind not in ("pair", "mixed", "triple", "rectangle") or (n < 3 and move_kind in ("mixed", "triple")):
        raise ValueError("move_kind must be pair, mixed, triple or rectangle (n=2 cannot use triple)")
    if not math.isfinite(focus_probability) or not 0 <= focus_probability <= 1:
        raise ValueError("focus_probability must lie in [0,1]")
    if type(tabu_size) is not int or tabu_size < 0 or type(focus_refresh_period) is not int or focus_refresh_period < 1:
        raise ValueError("tabu_size must be nonnegative and focus_refresh_period positive")
    if type(history_size) is not int or history_size < 1:
        raise ValueError("history_size must be a positive integer")
    started = time.monotonic()
    deadline = math.inf if seconds is None else started + seconds
    rng = random.Random(seed)
    incumbent = {"n": n, "points": []}
    if initial is not None:
        _independent_certificate(initial)
        incumbent = {"n": n, "points": [list(point) for point in initial["points"]],
                     "metadata": {"source": "provided independently validated seed", "novelty_claim": False}}
        _independent_certificate(incumbent)
    resume_hash = None
    if resume_state is not None:
        points, score, resume_hash = checked_full_state(resume_state, n)
        permutations = decompose(points, n)
    else:
        permutations = complete_seed(initial, n, rng) if initial is not None else random_permutations(n, rng)
        points = state_points(permutations)
        score = len(collinear_triples(sorted(points)))
    initial_score = score
    best_points, best_score = set(points), score
    iterations = accepted = uphill = rejected_illegal = cycles = revisits = restarts = 0
    seen = OrderedDict([(tuple(sorted(points)), None)])
    history_evictions = 0
    recent = deque([tuple(sorted(points))] if tabu_size else [])
    recent_set = set(recent)
    tabu_rejections = pair_proposals = triple_proposals = rectangle_proposals = 0
    focused_rows, focused_points = [], []
    best_at = 0
    while score and time.monotonic() < deadline and (max_iterations is None or iterations < max_iterations):
        iterations += 1
        if iterations % recolor_period == 0:
            recolor_cycle(permutations, rng.randrange(n))
            cycles += 1
        if iterations - best_at >= restart_period:
            permutations = decompose(best_points, n) if resume_state is not None else complete_seed(initial, n, rng) if initial is not None else random_permutations(n, rng)
            points = state_points(permutations)
            score = len(collinear_triples(sorted(points)))
            restarts += 1
            best_at = iterations
            if score < best_score:
                best_points, best_score = set(points), score
            if score == 0:
                break
            recent.clear()
            recent_set.clear()
        if focus_probability and (not focused_rows or iterations % focus_refresh_period == 1):
            ordered = sorted(points)
            triples = collinear_triples(ordered)
            focused_rows = [ordered[index][0] for triple in triples for index in triple]
            focused_points = [ordered[index] for triple in triples for index in triple]
        color = rng.randrange(2)
        if move_kind == "rectangle":
            rectangle_proposals += 1
            alive_conflicts = [point for point in focused_points if point in points]
            first_point = rng.choice(alive_conflicts) if alive_conflicts and rng.random() < focus_probability else (rng.randrange(n), None)
            if first_point[1] is None:
                first_point = first_point[0], permutations[color][first_point[0]]
            second_row = rng.choice([row for row in range(n) if row != first_point[0]])
            second_point = second_row, permutations[rng.randrange(2)][second_row]
            proposal = rectangle_proposal(points, first_point, second_point)
        else:
            first = rng.choice(focused_rows) if focused_rows and rng.random() < focus_probability else rng.randrange(n)
            triple_move = move_kind == "triple" or (move_kind == "mixed" and rng.random() < 0.5)
            rows = [first] + rng.sample([row for row in range(n) if row != first], 2 if triple_move else 1)
            if triple_move:
                triple_proposals += 1
                proposal = rotation_proposal(permutations, points, color, rows)
            else:
                pair_proposals += 1
                proposal = swap_proposal(permutations, points, color, *rows)
        if proposal is None:
            rejected_illegal += 1
            continue
        delta, proposed_points = proposal
        phase = (iterations % cooling_period) / cooling_period
        current_temperature = max(0.03, temperature * (1 - phase) ** 2)
        if delta <= 0 or rng.random() < math.exp(-delta / current_temperature):
            key = tuple(sorted(proposed_points))
            if tabu_size and key in recent_set and score + delta >= best_score:
                tabu_rejections += 1
                continue
            if move_kind == "rectangle":
                permutations = decompose(proposed_points, n)
            else:
                accept_rotation(permutations, color, rows)
            points, score = proposed_points, score + delta
            accepted += 1
            uphill += delta > 0
            if key in seen:
                revisits += 1
                seen.move_to_end(key)
            else:
                seen[key] = None
                if len(seen) > history_size:
                    seen.popitem(last=False)
                    history_evictions += 1
            if tabu_size:
                recent.append(key)
                recent_set.add(key)
                if len(recent) > tabu_size:
                    recent_set.remove(recent.popleft())
            if score < best_score:
                best_points, best_score, best_at = set(points), score, iterations
    candidate = {"n": n, "points": [list(point) for point in _prune(best_points)]}
    _independent_certificate(candidate)
    if len(candidate["points"]) > len(incumbent["points"]):
        incumbent = candidate
    checks = _independent_certificate(incumbent)
    incumbent.setdefault("metadata", {}).update({"normalized_sha256": checks[0]["normalized_sha256"],
                                                 "independent_validation": [check["algorithm"] for check in checks],
                                                 "novelty_claim": False})
    state = {"n": n, "points": [list(point) for point in sorted(best_points)],
             "state_kind": "valid_full_search_state" if best_score == 0 else "invalid_full_search_state",
             "valid": best_score == 0, "collinear_triple_count": best_score}
    fast, slow = verify_certificate(state), verify_certificate_bruteforce(state)
    if fast["conflict_count"] != best_score or slow["conflict_count"] != best_score or not degree_two(best_points, n):
        raise RuntimeError("incremental score or degree invariant failed final independent audit")
    state["normalized_sha256"] = fast["normalized_sha256"]
    state["independent_audit"] = [fast["algorithm"], slow["algorithm"]]
    run = {"method": "two_disjoint_permutations_alternating_rectangle_trades_and_cycle_recoloring",
           "seed": seed, "n": n, "seconds_budget": seconds, "max_iterations": max_iterations,
           "temperature": temperature, "cooling_period": cooling_period, "recolor_period": recolor_period,
           "restart_period": restart_period, "iterations": iterations, "accepted_moves": accepted,
           "move_kind": move_kind, "focus_probability": focus_probability,
           "focus_refresh_period": focus_refresh_period, "tabu_size": tabu_size,
           "tabu_rejections": tabu_rejections, "pair_proposals": pair_proposals,
           "triple_proposals": triple_proposals, "initial_full_state_score": initial_score,
           "rectangle_proposals": rectangle_proposals,
           "resume_state_normalized_sha256": resume_hash,
           "accepted_uphill_moves": uphill, "illegal_proposals": rejected_illegal,
           "alternating_cycle_recolorings": cycles, "state_hash_revisits": revisits,
           "tracked_state_hashes": len(seen), "state_history_capacity": history_size,
           "state_history_evictions": history_evictions,
           "state_hash_revisit_scope": "exact revisits within a bounded least-recently-used state cache, not lifetime distinct states",
           "restarts": restarts, "best_score": best_score,
           "incumbent_point_count": len(incumbent["points"]), "elapsed_seconds": time.monotonic() - started,
           "stopping_reason": "valid_full_state" if score == 0 else "operation_cap" if max_iterations is not None and iterations >= max_iterations else "time_budget",
           "reproducibility": "seeded operation-capped runs are reproducible; wall-clock stopping changes iteration counts and may change results",
           "novelty_claim": False}
    return {"incumbent": incumbent, "search_state": state, "run": run}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--initial", type=Path)
    parser.add_argument("--temperature", type=float, default=2.5)
    parser.add_argument("--resume-state", type=Path)
    parser.add_argument("--move-kind", choices=("pair", "mixed", "triple", "rectangle"), default="pair")
    parser.add_argument("--focus-probability", type=float, default=0.0)
    parser.add_argument("--tabu-size", type=int, default=0)
    parser.add_argument("--cooling-period", type=int, default=5000)
    parser.add_argument("--restart-period", type=int, default=20000)
    parser.add_argument("--history-size", type=int, default=10000)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        initial = json.loads(args.initial.read_text()) if args.initial else None
        resume = json.loads(args.resume_state.read_text()) if args.resume_state else None
        result = search(args.n, args.seconds, args.seed, args.max_iterations, initial, args.temperature,
                        cooling_period=args.cooling_period, restart_period=args.restart_period,
                        resume_state=resume, move_kind=args.move_kind,
                        focus_probability=args.focus_probability, tabu_size=args.tabu_size,
                        history_size=args.history_size)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix, key in (("incumbent", "incumbent"), ("state", "search_state"), ("run", "run")):
        path = args.output_prefix.with_name(args.output_prefix.name + f"-{suffix}.json")
        path.write_text(json.dumps(result[key], sort_keys=True, indent=2) + "\n")
    print(json.dumps(result["run"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
