"""Exact certificate validation, using only Python's standard library.

API: verify_certificate({"n": int, "points": [[x, y], ...], ...}) returns
a JSON-serializable report. Coordinates are integers in [0, n); bool and float
values are rejected. Metadata is ignored. Indices in conflicts refer to the
input order. normalized_sha256 hashes compact, sorted-key JSON containing only
{"n": n, "points": lexicographically_sorted_points}; UTF-8, no final newline.

verify_certificate_bruteforce has the same interface but checks all triples
by a cross product, independently of the normalized-slope implementation.
CLI: python src/verify.py certificate.json [--brute-force]. Exit codes: 0 valid,
1 invalid certificate, 2 unreadable or malformed JSON. A JSON report is always
written to stdout, including on input errors. Use '-' to read stdin.
"""

import argparse
import hashlib
import itertools
import json
import math
import sys


def _parse_certificate(certificate):
    errors = []
    if not isinstance(certificate, dict):
        return None, [], ["certificate must be an object"], 0
    n = certificate.get("n")
    if type(n) is not int or n < 1:
        errors.append("n must be a positive integer (bool and float are forbidden)")
    points = certificate.get("points")
    if not isinstance(points, list):
        return n, [], errors + ["points must be an array"], 0
    parsed = []
    seen = {}
    for i, point in enumerate(points):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            errors.append(f"points[{i}] must be a two-element coordinate array")
            continue
        x, y = point
        if type(x) is not int or type(y) is not int:
            errors.append(f"points[{i}] coordinates must be integers (bool and float are forbidden)")
            continue
        pair = (x, y)
        if pair in seen:
            errors.append(f"points[{i}] duplicates points[{seen[pair]}]")
        else:
            seen[pair] = i
        if type(n) is int and n >= 1 and not (0 <= x < n and 0 <= y < n):
            errors.append(f"points[{i}] is outside the grid")
        parsed.append(pair)
    return n, parsed, errors, len(points)


def normalized_sha256(n, points):
    """Hash already validated n and points; input order does not affect it."""
    payload = {"n": n, "points": [list(p) for p in sorted(points)]}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalized_direction(dx, dy):
    """Unoriented primitive integer direction; distinct points required."""
    divisor = math.gcd(dx, dy)
    if divisor == 0:
        raise ValueError("direction requires distinct points")
    dx, dy = dx // divisor, dy // divisor
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    return dx, dy


def collinear_triples(points):
    """Return every collinear index triple exactly once, in sorted order.

    At each anchor only later indices are grouped, so the smallest index of
    each triple supplies its unique anchor. All rational slopes are covered.
    """
    triples = []
    for i, (x, y) in enumerate(points):
        directions = {}
        for j in range(i + 1, len(points)):
            other_x, other_y = points[j]
            direction = normalized_direction(other_x - x, other_y - y)
            directions.setdefault(direction, []).append(j)
        for group in directions.values():
            triples.extend((i, j, k) for j, k in itertools.combinations(group, 2))
    return sorted(triples)


def collinear_triples_bruteforce(points):
    """Independent geometry audit: determinant of every three points."""
    triples = []
    for i, j, k in itertools.combinations(range(len(points)), 3):
        ax, ay = points[i]
        bx, by = points[j]
        cx, cy = points[k]
        if (bx - ax) * (cy - ay) == (by - ay) * (cx - ax):
            triples.append((i, j, k))
    return triples


def _verify(certificate, triple_finder, algorithm):
    n, points, errors, count = _parse_certificate(certificate)
    triples = [] if errors else triple_finder(points)
    return {
        "valid": not errors and not triples,
        "n": n if type(n) is int else None,
        "point_count": count,
        "errors": errors,
        "conflict_count": len(triples),
        "conflicts": [
            {"indices": list(t), "points": [list(points[i]) for i in t]}
            for t in triples
        ],
        "normalized_sha256": None if errors else normalized_sha256(n, points),
        "algorithm": algorithm,
    }


def verify_certificate(certificate):
    return _verify(certificate, collinear_triples, "integer_normalized_slopes")


def verify_certificate_bruteforce(certificate):
    return _verify(certificate, collinear_triples_bruteforce, "integer_cross_products")


def _reject_constant(value):
    raise ValueError(f"nonstandard JSON number: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", help="JSON file, or '-' for stdin")
    parser.add_argument("--brute-force", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.certificate == "-":
            certificate = json.load(sys.stdin, parse_constant=_reject_constant)
        else:
            with open(args.certificate, encoding="utf-8") as stream:
                certificate = json.load(stream, parse_constant=_reject_constant)
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"valid": False, "point_count": 0, "conflicts": [],
                          "conflict_count": 0, "normalized_sha256": None,
                          "errors": [str(exc)]}, sort_keys=True))
        return 2
    verifier = verify_certificate_bruteforce if args.brute_force else verify_certificate
    report = verifier(certificate)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
