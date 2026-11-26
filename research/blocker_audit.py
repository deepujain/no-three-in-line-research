"""Exhaustive, exact individual-insertion audit for four seed translations.

Run from any directory with Python 3; no dependencies. The default seed is the
published n78 witness and the target grid is n79. Output is data/blocker-audit.json.
For every empty cell c, directions from c partition old points. Because the seed
has no collinear triple, any group contains at most two old points. Groups of
two are precisely the disjoint blocking pairs, so their count is the minimum
number of old deletions allowing c alone to be inserted. This is a statement
about this finite seed, not a global extremal bound or a new theorem.
"""

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import normalized_direction, verify_certificate, verify_certificate_bruteforce


def blocking_pairs(points, candidate):
    cx, cy = candidate
    groups = {}
    for i, (x, y) in enumerate(points):
        direction = normalized_direction(x - cx, y - cy)
        groups.setdefault(direction, []).append(i)
    if any(len(group) > 2 for group in groups.values()):
        raise ValueError("input seed contains a collinear triple")
    pairs = sorted(tuple(group) for group in groups.values() if len(group) == 2)
    flattened = [index for pair in pairs for index in pair]
    if len(flattened) != len(set(flattened)):
        raise RuntimeError("blocking pairs are not disjoint")
    return pairs


def blocking_pairs_cross_products(points, candidate):
    """Independent pair-by-pair determinant implementation."""
    cx, cy = candidate
    result = []
    for i, j in itertools.combinations(range(len(points)), 2):
        ax, ay = points[i]
        bx, by = points[j]
        if (ax - cx) * (by - cy) == (ay - cy) * (bx - cx):
            result.append((i, j))
    return result


def audit_translation(seed, dx, dy, delete_budget):
    n = seed["n"] + 1
    points = [(x + dx, y + dy) for x, y in seed["points"]]
    certificate = {"n": n, "points": [list(point) for point in points]}
    fast = verify_certificate(certificate)
    slow = verify_certificate_bruteforce(certificate)
    if not fast["valid"] or not slow["valid"]:
        raise ValueError("translated seed failed exact independent audits")
    occupied = set(points)
    empties = [(x, y) for x in range(n) for y in range(n) if (x, y) not in occupied]
    histogram = Counter()
    minimum = None
    witness = None
    for candidate in empties:
        pairs = blocking_pairs(points, candidate)
        count = len(pairs)
        histogram[count] += 1
        if minimum is None or count < minimum:
            minimum, witness = count, (candidate, pairs)
    candidate, pairs = witness
    sample_indices = sorted({0, len(empties) // 4, len(empties) // 2,
                             3 * len(empties) // 4, len(empties) - 1})
    samples = [empties[index] for index in sample_indices]
    if candidate not in samples:
        samples.append(candidate)
    independent = []
    for point in samples:
        grouped = blocking_pairs(points, point)
        determinants = blocking_pairs_cross_products(points, point)
        if grouped != determinants:
            raise RuntimeError("independent blocker audit disagrees")
        independent.append({"point": list(point), "blocking_pair_count": len(grouped),
                            "exact_pair_sets_match": True})
    deleted = [pair[0] for pair in pairs]
    deleted_set = set(deleted)
    repaired = {"n": n, "points": [list(point) for i, point in enumerate(points)
                                      if i not in deleted_set] + [list(candidate)]}
    witness_fast = verify_certificate(repaired)
    witness_slow = verify_certificate_bruteforce(repaired)
    if not witness_fast["valid"] or not witness_slow["valid"]:
        raise RuntimeError("minimum-deletion witness failed independent verification")
    return {
        "translation": [dx, dy],
        "n": n,
        "seed_point_count": len(points),
        "normalized_seed_sha256": fast["normalized_sha256"],
        "empty_cell_count": len(empties),
        "histogram_minimum_old_deletions": {str(k): histogram[k] for k in sorted(histogram)},
        "minimum_old_deletions_for_any_new_point": minimum,
        "deletion_budgets_proved_insufficient_for_any_genuinely_new_point": list(range(minimum)),
        "minimum_cell_count": histogram[minimum],
        "maximum_old_deletions_for_an_individual_new_point": max(histogram),
        "all_blocking_pairs_disjoint": True,
        "all_direction_groups_have_size_at_most_two": True,
        "witness": {
            "point": list(candidate),
            "blocking_pair_count": len(pairs),
            "blocking_pairs": [{"indices": list(pair),
                                "points": [list(points[i]) for i in pair]} for pair in pairs],
            "example_deletion_indices": deleted,
            "resulting_point_count_after_deletions_and_one_addition": len(repaired["points"]),
            "resulting_certificate_normalized_sha256": witness_fast["normalized_sha256"],
            "resulting_certificate_passes_both_exact_verifiers": True,
        },
        "independent_cross_product_samples": independent,
        "delete_budget_compared": delete_budget,
        "budget_cannot_insert_any_genuinely_new_point": minimum > delete_budget,
    }


def audit(seed, delete_budget=3):
    started = time.monotonic()
    fast = verify_certificate(seed)
    slow = verify_certificate_bruteforce(seed)
    if not fast["valid"] or not slow["valid"]:
        raise ValueError("seed failed both-verifier prerequisite")
    translations = [audit_translation(seed, dx, dy, delete_budget)
                    for dx, dy in itertools.product((0, 1), repeat=2)]
    minimum = min(record["minimum_old_deletions_for_any_new_point"] for record in translations)
    return {
        "audit": "exact_individual_new_point_blocking_pairs",
        "seed_n": seed["n"],
        "target_n": seed["n"] + 1,
        "seed_point_count": len(seed["points"]),
        "seed_normalized_sha256": fast["normalized_sha256"],
        "seed_passes_both_exact_verifiers": True,
        "translations": translations,
        "minimum_old_deletions_across_all_four_translations": minimum,
        "deletion_budgets_proved_insufficient_in_all_four_translations": list(range(minimum)),
        "delete_budget_compared": delete_budget,
        "budget_cannot_insert_any_genuinely_new_point_in_any_translation": minimum > delete_budget,
        "interpretation": (
            "For each empty cell, all old collinear-pair blockers are disjoint because the validated seed has no collinear triple. "
            "At least one deletion per blocker is necessary, and selecting one old point from each disjoint blocker is sufficient for inserting that cell alone. "
            "If this minimum exceeds the deletion budget, deleting at most that many seed points cannot admit any genuinely new point. "
            "This prunes only those seed-relative repair budgets; it is neither a global bound nor an impossibility result for larger deletions, other seeds, or other constructions."
        ),
        "elapsed_seconds": time.monotonic() - started,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=ROOT / "data/published-n78.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/blocker-audit.json")
    parser.add_argument("--delete-budget", type=int, default=3)
    args = parser.parse_args(argv)
    if args.delete_budget < 0:
        parser.error("--delete-budget must be nonnegative")
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    report = audit(seed, args.delete_budget)
    report["seed_file"] = str(args.seed.resolve().relative_to(ROOT)) if args.seed.resolve().is_relative_to(ROOT) else str(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "minimum": report["minimum_old_deletions_across_all_four_translations"],
                      "delete_budget": args.delete_budget, "elapsed_seconds": report["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
