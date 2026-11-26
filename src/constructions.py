"""Classical exact baselines and a rigorously restricted extension family.

Coordinates are (x, y), zero based. No novelty is claimed for these baselines.
Generate a certificate with: python src/constructions.py conic --prime 79
Geometry validation belongs to verify.py, not this generator.
"""

import argparse
from collections import Counter
import json
import math


def is_prime(value):
    if type(value) is not int or value < 2:
        return False
    return all(value % divisor for divisor in range(2, math.isqrt(value) + 1))


def _require_prime(p, odd=False):
    if not is_prime(p) or (odd and p == 2):
        raise ValueError("p must be an odd prime" if odd else "p must be prime")


def _integer(value, name):
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, excluding bool")


def parabola(p, a=1, b=0, c=0):
    """p points (x, a*x*x+b*x+c mod p), with nonzero a mod p.

    Three distinct x values give a nonzero Vandermonde determinant mod p,
    so their integer determinant cannot be zero.
    """
    _require_prime(p)
    for value, name in ((a, "a"), (b, "b"), (c, "c")):
        _integer(value, name)
    if a % p == 0:
        raise ValueError("a must be nonzero modulo p")
    return [(x, (a * x * x + b * x + c) % p) for x in range(p)]


def norm_conic(p, d=None):
    """p+1 points of x*x-d*y*y=1 mod an odd prime p.

    d is a quadratic nonresidue. The rational parametrization lists all
    points and has no zero denominator because d is a nonresidue.
    """
    _require_prime(p, odd=True)
    if d is None:
        d = next(v for v in range(2, p) if pow(v, (p - 1) // 2, p) == p - 1)
    _integer(d, "d")
    d %= p
    if pow(d, (p - 1) // 2, p) != p - 1:
        raise ValueError("d must be a quadratic nonresidue modulo p")
    points = [((p - 1), 0)]
    for t in range(p):
        denominator_inverse = pow((1 - d * t * t) % p, -1, p)
        points.append(((1 + d * t * t) * denominator_inverse % p,
                       2 * t * denominator_inverse % p))
    return sorted(points)


def lifted_parabola(p, a=1, b=0, c=0):
    """2p points in a p by 2p rectangle, hence in a 2p-square.

    Each x has two points separated vertically by p. A nonvertical triple
    would require three distinct x coordinates, ruled out modulo p.
    This is NOT a 2p-point construction in a p-square.
    """
    return sorted((x, y + offset) for x, y in parabola(p, a, b, c)
                  for offset in (0, p))


def make_certificate(family, p, n=None):
    generators = {"parabola": parabola, "conic": norm_conic,
                  "lifted-parabola": lifted_parabola}
    if family not in generators:
        raise ValueError(f"unknown family: {family}")
    points = generators[family](p)
    minimum_n = 2 * p if family == "lifted-parabola" else p
    if n is None:
        n = minimum_n
    _integer(n, "n")
    if n < minimum_n:
        raise ValueError(f"{family} requires n >= {minimum_n}")
    return {"n": n, "points": [list(point) for point in points],
            "construction": family, "prime": p,
            "point_count": len(points),
            "coordinate_convention": "[x,y], integers from 0 through n-1",
            "novelty_claim": False}


def one_point_extensions(n, points):
    """Yield (deleted_point, candidate) for every one-hole corner extension.

    Input must be an n-square witness of size 2n. This function checks the
    domain and row/column saturation; callers must separately verify its
    geometry. Each candidate keeps all other input points and adds exactly
    (a,n), (n,b), (n,n) after deleting (a,b). Candidate validity is NOT assumed.
    """
    _integer(n, "n")
    if n < 2:
        raise ValueError("n must be at least 2")
    normalized = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("each point must be a coordinate pair")
        x, y = point
        _integer(x, "x")
        _integer(y, "y")
        if not (0 <= x < n and 0 <= y < n):
            raise ValueError("input point outside n-square")
        normalized.append((x, y))
    if len(normalized) != 2 * n or len(set(normalized)) != 2 * n:
        raise ValueError("input must contain 2n distinct points")
    if any(count != 2 for counts in
           (Counter(x for x, _ in normalized), Counter(y for _, y in normalized))
           for count in counts.values()):
        raise ValueError("input must have exactly two points per row and column")
    for a, b in sorted(normalized):
        candidate = sorted((set(normalized) - {(a, b)}) | {(a, n), (n, b), (n, n)})
        yield (a, b), candidate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=("parabola", "conic", "lifted-parabola"))
    parser.add_argument("--prime", type=int, required=True)
    parser.add_argument("--n", type=int)
    args = parser.parse_args(argv)
    try:
        certificate = make_certificate(args.family, args.prime, args.n)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(certificate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
