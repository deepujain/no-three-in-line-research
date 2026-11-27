"""Separate row-floor CNF with configurable direct small-capacity thresholds.

Only encoding choices change. The original compact and row-quota compilers
are untouched. No solver, large model enumeration, build, or guard runs here.
"""
from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
from pathlib import Path

try:
    from .near_quarter_compact import line_groups
    from .near_quarter_row_quota import row_floor_clauses, row_quota_counts
except ImportError:
    from near_quarter_compact import line_groups
    from near_quarter_row_quota import row_floor_clauses, row_quota_counts

VARIANT = 'near-quarter-row-floor-direct-thresholds-v1'


@dataclass(frozen=True)
class CapacityThresholds:
    """Independent direct cutoffs, capped at seven for this experiment."""
    atmost_two: int = 7
    conditional_atmost_one: int = 7

    def __post_init__(self):
        for value in (self.atmost_two, self.conditional_atmost_one):
            if type(value) is not int or not 0 <= value <= 7:
                raise ValueError('direct thresholds must be integers in 0..7')


def _thresholds(value):
    if not isinstance(value, CapacityThresholds):
        raise ValueError('thresholds must be CapacityThresholds')
    return value


def shared_capacity_clauses(weights, guards, pool, thresholds=CapacityThresholds()):
    """Exact C<=2 and each d=>C<=1, with independent direct cutoffs.

    Direct AM2 excludes every selected triple. Direct guarded AM1 excludes
    each pair whenever its guard is true. Both use zero auxiliary variables.
    Longer supports retain the frozen sequential/gate construction.
    """
    from pysat.card import CardEnc, EncType
    thresholds = _thresholds(thresholds)
    weights = tuple(weights)
    guards = tuple(sorted(set(guards)))
    if (len({v for v,_ in weights}) != len(weights) or
            any(type(v) is not int or v <= 0 or type(w) is not int or w <= 0 for v,w in weights) or
            any(type(d) is not int or d <= 0 for d in guards) or
            {v for v,_ in weights}.intersection(guards)):
        raise ValueError('invalid common weights or diagonal guards')
    heavy = [v for v,w in weights if w == 2]
    light = [v for v,w in weights if w == 1]
    for v,w in weights:
        if w > 2:
            yield [-v]
    for a,b in combinations(heavy,2):
        yield [-a,-b]
    for h in heavy:
        for v in light:
            yield [-h,-v]
    if len(light) <= max(2,thresholds.atmost_two):
        for triple in combinations(light,3):
            yield [-v for v in triple]
    else:
        yield from CardEnc.atmost(lits=light,bound=2,vpool=pool,encoding=EncType.seqcounter).clauses
    for d in guards:
        for h in heavy:
            yield [-d,-h]
    if not guards or len(light) <= 1:
        return
    if len(light) <= thresholds.conditional_atmost_one:
        for d in guards:
            for a,b in combinations(light,2):
                yield [-d,-a,-b]
    else:
        if len(guards) == 1:
            gate = guards[0]
        else:
            gate = pool.id()
            for d in guards:
                yield [-d,gate]
        for clause in CardEnc.atmost(lits=light,bound=1,vpool=pool,encoding=EncType.seqcounter).clauses:
            yield [-gate]+clause


def threshold_counts(model, thresholds=CapacityThresholds()):
    """Source/configuration identities only; no geometry enumeration."""
    thresholds = _thresholds(thresholds)
    base = row_quota_counts(model)
    baseline_limit = base.pop('direct_light_limit')
    return {**base, 'baseline_row_encoding_variant':base['encoding_variant'],
            'encoding_variant':VARIANT, 'baseline_direct_light_limit':baseline_limit,
            'capacity_thresholds':asdict(thresholds),
            'threshold_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def model_header(model, thresholds=CapacityThresholds()):
    return {'family':threshold_counts(model,thresholds),'off_diagonal_quotient':'full C4',
            'exceptional_diagonal_guards':True,'row_floor_representatives':'0..n//2',
            'row_floor':'weighted occupancy >= 2; replaces global four-orbit equality'}


def streamed_cnf(model, thresholds=CapacityThresholds()):
    """Complete equivalent row-floor formula; never searches or claims RSS."""
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    thresholds = _thresholds(thresholds)
    four = model['four_count']
    total = len(model['orbits'])
    pool = IDPool(start_from=total+1)
    yield from CardEnc.equals(lits=list(range(four+1,total+1)),bound=1,
                              vpool=pool,encoding=EncType.seqcounter).clauses
    yield from row_floor_clauses(model)
    for group in line_groups(model):
        if not group['special_diagonal_orbit']:
            yield from shared_capacity_clauses(group['off_diagonal_weights'],
                                               group['diagonal_guards'],pool,thresholds)
