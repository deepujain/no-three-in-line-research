"""Complete maximal lattice-line capacity model, with bounded streamed export.

Variable id for (x,y) is y*n+x+1; a line constraint is sum(vars)<=2.
Rows and columns are included. At target 2n, these imply exactly two per row
and column; target must additionally be imposed by the solver.
"""
import argparse
import json
import math


def _check_n(n):
    if type(n) is not int or n < 1:
        raise ValueError('n must be a positive integer')


def directions(n):
    """Canonical primitive directions capable of three grid points."""
    _check_n(n)
    m = (n - 1) // 2
    if m:
        yield (0, 1)
    for dx in range(1, m + 1):
        for dy in range(-m, m + 1):
            if math.gcd(dx, abs(dy)) == 1:
                yield (dx, dy)


def maximal_lines(n):
    """Yield each maximal line of at least three points once, as point tuples."""
    for dx, dy in directions(n):
        xlo, xhi = max(0, -2*dx), min(n-1, n-1-2*dx)
        ylo, yhi = max(0, -2*dy), min(n-1, n-1-2*dy)
        for x in range(xlo, xhi + 1):
            for y in range(ylo, yhi + 1):
                if 0 <= x-dx < n and 0 <= y-dy < n:
                    continue
                line = []
                xx, yy = x, y
                while 0 <= xx < n and 0 <= yy < n:
                    line.append((xx, yy))
                    xx += dx
                    yy += dy
                yield tuple(line)


def model_counts(n):
    """Count constraints and incidences analytically without materializing lines."""
    _check_n(n)
    count = incidence = direction_count = 0
    for dx, dy in directions(n):
        direction_count += 1
        u, v = abs(dx), abs(dy)
        # Difference of starts whose kth point fits and starts whose previous
        # point also fits: number of maximal lines of length at least k.
        def at_least(k):
            return ((max(0, n-(k-1)*u)*max(0, n-(k-1)*v)) -
                    (max(0, n-k*u)*max(0, n-k*v)))
        c = at_least(3)
        count += c
        incidence += 2*c
        k = 3
        while (n-(k-1)*u > 0) and (n-(k-1)*v > 0):
            incidence += at_least(k)
            k += 1
    return {'n': n, 'variables': n*n, 'maximal_lines_length_at_least_3': count,
            'line_variable_incidences': incidence, 'primitive_directions': direction_count,
            'target_2n': 2*n if n >= 2 else None,
            'note': 'Line cardinality constraints only; objective/target and optional exact row/column equalities are separate.'}


def line_variable_ids(n):
    for line in maximal_lines(n):
        yield [y*n+x+1 for x,y in line]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('n', type=int)
    parser.add_argument('--export-jsonl', metavar='PATH', help='stream line capacity constraints as JSON lines')
    parser.add_argument('--max-lines', type=int, default=100000,
                        help='refuse export above this many lines; default 100000')
    args = parser.parse_args()
    counts = model_counts(args.n)
    if args.max_lines < 0:
        parser.error('--max-lines must be nonnegative')
    if args.export_jsonl:
        if counts['maximal_lines_length_at_least_3'] > args.max_lines:
            parser.error('refusing export: counted lines exceed --max-lines; inspect counts first and choose a deliberate cap')
        with open(args.export_jsonl, 'w', encoding='utf-8') as out:
            for line in line_variable_ids(args.n):
                out.write(json.dumps({'vars': line, 'upper': 2}, separators=(',', ':')) + '\n')
    print(json.dumps(counts, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
