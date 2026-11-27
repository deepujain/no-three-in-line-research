"""Independent full-complement verification; import performs no geometry.

Only a separately authorized fixed-input driver may invoke geometric APIs.
The shared core supplies accounting and normalized identity, never geometry.
"""
from itertools import combinations
from math import gcd

from research.full_complement_row75_core import normalized_sha256


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def validate_points(points, n):
    """Independent strict shape check; fixed byte identity belongs to driver."""
    require(type(n) is int and n in (5, 75), 'reviewed grid size')
    require(type(points) is tuple and len(points) == 2*n-1, 'canonical point tuple/count')
    rows = [[] for _ in range(n)]
    previous = None
    for point in points:
        require(type(point) is tuple and len(point) == 2, 'strict cell tuple')
        x, y = point
        require(type(x) is int and type(y) is int, 'strict cell integers')
        require(0 <= x < n and 0 <= y < n, 'cell bounds')
        require(previous is None or previous < point, 'strict sorted distinct cells')
        rows[y].append(x)
        previous = point
    require(sum(len(row) == 1 for row in rows) == 1
            and sum(len(row) == 2 for row in rows) == n-1, 'one singleton and otherwise full rows')
    return tuple(tuple(row) for row in rows)


def direct_raw(points, n, budget, component='independent_baseline'):
    """Direct adjacent-edge determinants, independent of both line encodings."""
    validate_points(points, n)
    budget.checkpoint()
    score = 0
    for first, second, third in combinations(points, 3):
        budget.charge('raw_triples', component)
        dx1, dy1 = second[0]-first[0], second[1]-first[1]
        dx2, dy2 = third[0]-second[0], third[1]-second[1]
        if dx1*dy2 == dy1*dx2:
            score += 1
    return score


def _direction_line(left, right, budget, component):
    """Primitive signed direction and intercept: dy*x - dx*y = intercept."""
    budget.charge('pair_lines', component)
    dx, dy = right[0]-left[0], right[1]-left[1]
    divisor = gcd(abs(dx), abs(dy))
    require(divisor > 0, 'distinct line endpoints')
    dx, dy = dx//divisor, dy//divisor
    if dx < 0 or dx == 0 and dy < 0:
        dx, dy = -dx, -dy
    intercept = dy*left[0]-dx*left[1]
    return dx, dy, intercept


def _endpoint_table(points, budget, component):
    """Mask indices are local to exactly this point tuple."""
    lines = {}
    bits = tuple(1 << index for index in range(len(points)))
    try:
        for first, second in combinations(range(len(points)), 2):
            key = _direction_line(points[first], points[second], budget, component)
            lines[key] = lines.get(key, 0) | bits[first] | bits[second]
        return lines
    except BaseException:
        lines.clear()
        raise


def _endpoint_count(mask, point_count, budget, component):
    budget.charge('recoveries', component)
    multiplicity = mask.bit_count()
    require(2 <= multiplicity <= point_count and mask.bit_length() <= point_count,
            'local endpoint mask multiplicity')
    return multiplicity


def _target_column(key, row, n, budget, component):
    budget.charge('intersections', component)
    dx, dy, intercept = key
    if dy == 0:
        return None  # A horizontal line contributes nothing to a retained-row unary.
    numerator = intercept + dx*row
    column, remainder = divmod(numerator, dy)
    if remainder == 0 and 0 <= column < n:
        return column
    return None


def endpoint_raw(points, n, budget, component='independent_candidate_lines'):
    """Full raw score from distinct endpoint masks, without triangular inversion."""
    validate_points(points, n)
    budget.checkpoint()
    lines = _endpoint_table(points, budget, component)
    try:
        budget.check_graph(points, lines)
        total = 0
        for mask in lines.values():
            multiplicity = _endpoint_count(mask, len(points), budget, component)
            total += multiplicity*(multiplicity-1)*(multiplicity-2)//6
        return total
    finally:
        lines.clear()
        del lines


def _check_profile_schema(costs, records, n, rows, baseline):
    require(type(baseline) is int and baseline >= 0, 'strict nonnegative baseline')
    require(type(costs) is list and len(costs) == n, 'primary cost matrix shape')
    maximum = (2*n-2)*(2*n-3)//2
    for costs_row in costs:
        require(type(costs_row) is list and len(costs_row) == n
                and all(type(value) is int and 0 <= value <= maximum for value in costs_row),
                'strict bounded primary unary cells')
    require(type(records) is list and len(records) == n, 'complete row records')
    for row, record in enumerate(records):
        require(type(record) is dict and set(record) == {'row', 'current', 'best', 'best_score'},
                'strict row record schema')
        require(type(record['row']) is int and record['row'] == row
                and type(record['current']) is tuple
                and all(type(column) is int for column in record['current'])
                and record['current'] == rows[row],
                'current row binding')
        chosen = record['best']
        require(type(chosen) is tuple and len(chosen) == len(rows[row])
                and all(type(column) is int and 0 <= column < n for column in chosen)
                and tuple(sorted(set(chosen))) == chosen, 'strict sorted same-load best columns')
        require(type(record['best_score']) is int and 0 <= record['best_score'] <= baseline,
                'strict bounded best score')


def verify_profiles(points, n, costs, records, baseline, budget):
    """Independently verify every unary and lexical minimum; retain no line maps."""
    rows = validate_points(points, n)
    _check_profile_schema(costs, records, n, rows, baseline)
    budget.checkpoint()
    comparisons = 0
    for row in range(n):
        retained = tuple(point for point in points if point[1] != row)
        lines = _endpoint_table(retained, budget, 'independent_retained')
        row_costs = [0]*n
        retained_score = 0
        try:
            budget.check_graph(points, costs, records, retained, lines, row_costs)
            for key, mask in lines.items():
                multiplicity = _endpoint_count(mask, len(retained), budget, 'independent_retained')
                retained_score += multiplicity*(multiplicity-1)*(multiplicity-2)//6
                column = _target_column(key, row, n, budget, 'independent_retained')
                if column is not None:
                    row_costs[column] += multiplicity*(multiplicity-1)//2
        finally:
            lines.clear()
            del lines
        require(row_costs == costs[row], 'independent all-cell unary disagreement')
        require(retained_score + sum(row_costs[column] for column in rows[row]) == baseline,
                'independent retained baseline disagreement')
        chosen = records[row]['best']
        for selected in chosen:
            for unselected in range(n):
                if unselected in chosen:
                    continue
                budget.charge('comparisons', 'independent_retained')
                comparisons += 1
                require((row_costs[selected], selected) < (row_costs[unselected], unselected),
                        'independent lexical minimum disagreement')
        require(retained_score + sum(row_costs[column] for column in chosen) == records[row]['best_score'],
                'independent best full score disagreement')
    require(sum(costs[row][column] for row in range(n) for column in rows[row]) == 3*baseline,
            'occupied unary triple-count identity')
    return {'verified_rows': n, 'verified_cells': n*n, 'lexical_comparisons': comparisons,
            'all_unaries_and_lexical_minima_verified': True}


def verify_candidate(base, candidate, n, row, columns, predicted, budget, *, validator_start=None):
    """Validate only the selected strict replacement; never adopt or iterate it."""
    before = validate_points(base, n)
    after = validate_points(candidate, n)
    require(type(row) is int and 0 <= row < n, 'strict candidate row')
    require(type(columns) is tuple and len(columns) == len(before[row])
            and all(type(column) is int and 0 <= column < n for column in columns)
            and tuple(sorted(set(columns))) == columns, 'strict same-load candidate columns')
    require(type(predicted) is int and predicted >= 0, 'strict predicted raw score')
    require(validator_start is None or callable(validator_start), 'validator start guard')
    require(all(len(before[index]) == len(after[index]) for index in range(n)), 'preserved individual loads')
    require(after[row] == columns
            and tuple(point for point in base if point[1] != row)
            == tuple(point for point in candidate if point[1] != row), 'exact one-row replacement')
    if validator_start is not None:
        validator_start()
    direct = direct_raw(candidate, n, budget, 'independent_candidate_direct')
    if validator_start is not None:
        validator_start()
    endpoint = endpoint_raw(candidate, n, budget, 'independent_candidate_lines')
    require(direct == endpoint == predicted, 'independent candidate raw-score disagreement')
    # No final deadline check here: after both validators return, driver owns zero-save priority.
    return {'score': direct, 'direct_score': direct, 'endpoint_score': endpoint,
            'normalized_sha256': normalized_sha256(candidate, n),
            'same_load_single_row_replacement_verified': True}
