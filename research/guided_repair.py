"""Exact blocker-guided deletion/insertion neighborhood, standard library only.

For a valid seed S, exhaust every possible repair improving |S| by one or two
after deleting at most k original seed points. A new point's disjoint blocker
pairs must all be hit by the deletion set D. Enumerating one endpoint of every
pair and optional additional seed deletions therefore covers every relevant D.
For each D, exhaust addition subsets, including removed seed points that can be
readded. Integer pair/remaining-seed and addition-triple checks are exact.

Default CLI audits all four n78-to-n79 translations with k=3 and a 60s compute
limit. A timeout is explicitly incomplete. Any found certificate is immediately
saved inside the output JSON and independently checked by both verifiers.
"""

import argparse
from collections import Counter
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import normalized_direction, verify_certificate, verify_certificate_bruteforce


class AuditTimeout(Exception):
    pass


def _check_deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise AuditTimeout


def blockers(seed_points, candidate):
    groups = {}
    cx, cy = candidate
    for i, (x, y) in enumerate(seed_points):
        direction = normalized_direction(x - cx, y - cy)
        groups.setdefault(direction, []).append(i)
    if any(len(group) > 2 for group in groups.values()):
        raise ValueError("seed is not a no-three-in-line set")
    return tuple(sorted(tuple(group) for group in groups.values() if len(group) == 2))


def deletion_sets(seed_count, eligible, max_deletions, deadline=None):
    """All D through budget that can admit at least one genuinely new cell."""
    found = set()
    for _, pairs in eligible:
        _check_deadline(deadline)
        for endpoints in itertools.product(*pairs):
            base = frozenset(endpoints)
            optional = [i for i in range(seed_count) if i not in base]
            for extra_count in range(max_deletions - len(base) + 1):
                for extras in itertools.combinations(optional, extra_count):
                    _check_deadline(deadline)
                    found.add(tuple(sorted(base.union(extras))))
    return sorted(found, key=lambda item: (len(item), item))


def _collinear(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) == (b[1] - a[1]) * (c[0] - a[0])


def audit_translation(seed, dx=0, dy=0, max_deletions=3, deadline=None,
                      on_certificate=None, collect_deletion_results=False):
    """Return exhaustive scope/results for one embedding, or explicit timeout.

    Target grid is seed['n']+1. on_certificate receives each first-found target
    certificate and its deletion indices. collect_deletion_results supports
    independent tiny-instance differential tests, and is off for large audits.
    """
    if type(max_deletions) is not int or max_deletions < 0:
        raise ValueError("max_deletions must be a nonnegative integer")
    points = [tuple((x + dx, y + dy)) for x, y in seed["points"]]
    n = seed["n"] + 1
    certificate = {"n": n, "points": [list(p) for p in points]}
    fast, slow = verify_certificate(certificate), verify_certificate_bruteforce(certificate)
    if not fast["valid"] or not slow["valid"]:
        raise ValueError("translated seed failed independent validation")
    count = len(points)
    report = {
        "translation": [dx, dy], "n": n, "seed_point_count": count,
        "normalized_seed_sha256": fast["normalized_sha256"],
        "max_original_seed_deletions": max_deletions,
        "status": "incomplete", "phase": "preparing_candidates",
        "eligible_new_cell_count": 0, "deletion_set_count": 0,
        "deletion_sets_completed": 0, "deletion_set_size_histogram": {},
        "addition_subsets_tested_by_target_size": {str(count + 1): 0, str(count + 2): 0},
        "compatible_addition_subsets_by_target_size": {str(count + 1): 0, str(count + 2): 0},
        "pair_compatibility_rejections": 0, "triple_compatibility_rejections": 0,
        "available_genuinely_new_cell_count_histogram": {},
        "found_certificates": [],
    }
    per_deletion = []
    try:
        occupied = set(points)
        eligible = []
        for x in range(n):
            for y in range(n):
                _check_deadline(deadline)
                if (x, y) in occupied:
                    continue
                pairs = blockers(points, (x, y))
                if len(pairs) <= max_deletions:
                    eligible.append(((x, y), pairs))
        report["eligible_new_cell_count"] = len(eligible)
        report["eligible_new_cells"] = [
            {"point": list(point), "blocking_pairs": [list(pair) for pair in pairs]}
            for point, pairs in eligible]
        report["phase"] = "enumerating_deletion_sets"
        deletions = deletion_sets(count, eligible, max_deletions, deadline)
        report["deletion_set_count"] = len(deletions)
        report["deletion_set_size_histogram"] = dict(sorted(Counter(map(len, deletions)).items()))
        report["phase"] = "checking_addition_subsets"
        all_mask = (1 << count) - 1

        @lru_cache(maxsize=None)
        def seed_points_on_pair(a, b):
            return sum(1 << i for i, point in enumerate(points)
                       if point != a and point != b and _collinear(a, b, point))

        found_sizes = set()
        available_new_histogram = Counter()
        for deleted in deletions:
            _check_deadline(deadline)
            removed = set(deleted)
            removed_mask = sum(1 << i for i in deleted)
            remaining_mask = all_mask ^ removed_mask
            pool = [point for point, pairs in eligible
                    if all(i in removed or j in removed for i, j in pairs)]
            available_new_histogram[len(pool)] += 1
            pool.extend(points[i] for i in deleted)
            pool = sorted(pool)
            compatibility = {}
            for a, b in itertools.combinations(pool, 2):
                _check_deadline(deadline)
                compatibility[(a, b)] = not (seed_points_on_pair(a, b) & remaining_mask)
            _check_deadline(deadline)
            per_result = {"deletion_indices": list(deleted), "available_addition_point_count": len(pool),
                          "valid_addition_subsets_by_target_size": {str(count + 1): 0, str(count + 2): 0}}
            for gain in (1, 2):
                size = len(deleted) + gain
                target = str(count + gain)
                for additions in itertools.combinations(pool, size):
                    report["addition_subsets_tested_by_target_size"][target] += 1
                    if report["addition_subsets_tested_by_target_size"][target] % 256 == 0:
                        _check_deadline(deadline)
                    if any(not compatibility[(a, b)] for a, b in itertools.combinations(additions, 2)):
                        report["pair_compatibility_rejections"] += 1
                        continue
                    if any(_collinear(a, b, c) for a, b, c in itertools.combinations(additions, 3)):
                        report["triple_compatibility_rejections"] += 1
                        continue
                    report["compatible_addition_subsets_by_target_size"][target] += 1
                    per_result["valid_addition_subsets_by_target_size"][target] += 1
                    if target not in found_sizes:
                        repaired = {"n": n, "points": [list(point) for i, point in enumerate(points)
                                                         if i not in removed] + [list(point) for point in additions],
                                    "metadata": {"method": "exact_blocker_guided_repair", "translation": [dx, dy],
                                                 "deleted_seed_indices": list(deleted), "novelty_claim": False,
                                                 "initial_normalized_sha256": fast["normalized_sha256"]}}
                        checks = [verify_certificate(repaired), verify_certificate_bruteforce(repaired)]
                        if not all(check["valid"] for check in checks):
                            raise RuntimeError("geometry screening disagreed with independent validation")
                        repaired["metadata"]["normalized_sha256"] = checks[0]["normalized_sha256"]
                        repaired["metadata"]["independent_validation"] = [check["algorithm"] for check in checks]
                        report["found_certificates"].append(repaired)
                        found_sizes.add(target)
                        if on_certificate:
                            on_certificate(repaired, list(deleted))
            report["deletion_sets_completed"] += 1
            if collect_deletion_results:
                per_deletion.append(per_result)
        report["available_genuinely_new_cell_count_histogram"] = dict(sorted(available_new_histogram.items()))
        report["status"], report["phase"] = "complete", "complete"
        report["pair_seed_masks_computed"] = seed_points_on_pair.cache_info().currsize
    except AuditTimeout:
        report["status"] = "timeout_incomplete"
    if collect_deletion_results:
        report["per_deletion_results"] = per_deletion
    return report


def audit(seed, max_deletions=3, seconds=60, on_certificate=None):
    if isinstance(seconds, bool) or not isinstance(seconds, (float, int)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    checks = [verify_certificate(seed), verify_certificate_bruteforce(seed)]
    if not all(check["valid"] for check in checks):
        raise ValueError("original seed failed independent validation")
    started = time.monotonic()
    deadline = started + seconds
    report = {"audit": "exact_blocker_guided_original_seed_deletion_neighborhood",
              "seed_n": seed["n"], "target_n": seed["n"] + 1,
              "seed_point_count": len(seed["points"]),
              "seed_normalized_sha256": checks[0]["normalized_sha256"],
              "max_original_seed_deletions": max_deletions, "seconds_budget": seconds,
              "status": "incomplete", "translations": [],
              "scope": "All repairs gaining one or two points after at most the specified number of original-seed deletions, including readdition of removed seed points. No conclusion about larger deletion budgets, other seeds, or global existence."}
    for dx, dy in itertools.product((0, 1), repeat=2):
        current = audit_translation(seed, dx, dy, max_deletions, deadline, on_certificate)
        report["translations"].append(current)
        if current["status"] != "complete":
            break
    report["status"] = "complete" if len(report["translations"]) == 4 and all(r["status"] == "complete" for r in report["translations"]) else "timeout_incomplete"
    report["elapsed_seconds"] = time.monotonic() - started
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, default=ROOT / "data/published-n78.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/guided-repair-audit.json")
    parser.add_argument("--max-deletions", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=60)
    args = parser.parse_args(argv)
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    discovered = []

    def save_immediately(certificate, deleted):
        discovered.append(certificate)
        args.output.write_text(json.dumps({"status": "in_progress_certificate_found", "found_certificates": discovered},
                                         indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"event": "independently_validated_certificate_found", "point_count": len(certificate["points"]),
                          "deleted_seed_indices": deleted, "normalized_sha256": certificate["metadata"]["normalized_sha256"]}), flush=True)

    try:
        report = audit(seed, args.max_deletions, args.seconds, save_immediately)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "status": report["status"], "elapsed_seconds": report["elapsed_seconds"],
                      "translations_completed": sum(r["status"] == "complete" for r in report["translations"])}, sort_keys=True))
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
