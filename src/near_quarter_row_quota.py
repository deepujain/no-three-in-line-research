"""Equivalent near-quarter CNF using row floors instead of a global four count.

Keep exactly one diagonal pair and every approved compact line capacity.
All rows have capacity two; half-turn representative row floors force every
row to equal two. Total size 2*n then implies exactly (n-1)/2 four-orbits.
No solver, guard, large enumeration or original source is changed here.
"""
import hashlib
from pathlib import Path

try:
    from .near_quarter_compact import compact_counts,line_groups,shared_capacity_clauses
except ImportError:
    from near_quarter_compact import compact_counts,line_groups,shared_capacity_clauses

VARIANT = 'near-quarter-row-floor-shared-capacity-v1'


def at_least_two(weights):
    """Zero-auxiliary CNF for a positive weighted sum >=2."""
    weights = tuple(weights)
    if (len({v for v,w in weights}) != len(weights) or
            any(type(v) is not int or v <= 0 or type(w) is not int or w <= 0 for v,w in weights)):
        raise ValueError('weights require distinct positive variable IDs and coefficients')
    heavy = [v for v,w in weights if w >= 2]
    light = [v for v,w in weights if w == 1]
    if len(light) < 2:
        yield heavy
    else:
        for omitted in light:
            yield heavy+[v for v in light if v != omitted]


def row_floor_clauses(model):
    """One floor per half-turn row representative, including the center."""
    n = model['n']
    mapping = model['point_to_var']
    for row in range(n//2+1):
        weights = {}
        for x in range(n):
            variable = mapping.get((x,row))
            if variable is not None:
                weights[variable] = weights.get(variable,0)+1
        yield from at_least_two(sorted(weights.items()))


def row_quota_counts(model):
    """Only algebraic family/source metadata; no geometry enumeration."""
    base = compact_counts(model)
    return {**base,'base_encoding_variant':base['encoding_variant'],
            'encoding_variant':VARIANT,
            'row_quota_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'global_four_count':'implied by row floors, line capacities and exactly one diagonal pair'}


def streamed_cnf(model):
    """Yield the equivalent family without the large four-orbit equality."""
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    four = model['four_count']
    total = len(model['orbits'])
    pool = IDPool(start_from=total+1)
    yield from CardEnc.equals(lits=list(range(four+1,total+1)),bound=1,
                              vpool=pool,encoding=EncType.seqcounter).clauses
    yield from row_floor_clauses(model)
    for group in line_groups(model):
        if group['special_diagonal_orbit']:
            # Exactly one diagonal pair is still explicit, so the approved
            # special main/anti-diagonal omission has the same justification.
            continue
        yield from shared_capacity_clauses(group['off_diagonal_weights'],
                                           group['diagonal_guards'],pool)
