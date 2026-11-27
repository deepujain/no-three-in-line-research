"""Exact shared-off-diagonal CNF variant of the near-quarter-turn family.

Only the four-orbit contribution is shared under quarter turns. Exceptional
main-diagonal contributions remain separate conditional capacities. No solver
is launched. The original compiler and its guarded preflight are unchanged.
"""
import hashlib
from itertools import combinations
from pathlib import Path

try:
    from .near_quarter_model import family_counts, maximal_lines
except ImportError:
    from near_quarter_model import family_counts, maximal_lines

VARIANT = 'c4-shared-offdiagonal-direct-small-v1'
DIRECT_LIGHT_LIMIT = 5


def line_groups(model):
    """Stream one representative per complete C4 orbit of maximal lines.

No global signature table is retained. Rotations of a representative are
checked for equal off-diagonal multiplicities and valid diagonal exceptions.
"""
    n = model['n']
    mapping = model['point_to_var']
    four = model['four_count']
    for line in maximal_lines(n):
        canonical = tuple(sorted(line))
        rotations = [canonical]
        for _ in range(3):
            rotations.append(tuple(sorted((y,n-1-x) for x,y in rotations[-1])))
        if canonical != min(rotations):
            continue
        special = (all(x == y for x,y in canonical) or
                   all(x+y == n-1 for x,y in canonical))
        common = None
        guards = set()
        for rotated in rotations:
            weights = {}
            diagonal = []
            for point in rotated:
                var = mapping.get(point)
                if var is None:
                    continue
                if var <= four:
                    weights[var] = weights.get(var,0)+1
                else:
                    diagonal.append(var)
            signature = tuple(sorted(weights.items()))
            if common is not None and common != signature:
                raise ValueError('off-diagonal C4 multiplicities differ')
            common = signature
            if not special and len(diagonal) > 1:
                raise ValueError('non-main line has multiple diagonal cells')
            guards.update(diagonal)
        if special:
            if common:
                raise ValueError('diagonals have off-diagonal contribution')
        elif len(guards) > 2:
            raise ValueError('C4 line orbit has more than two diagonal guards')
        yield {'line':canonical, 'orbit_size':len(set(rotations)),
               'off_diagonal_weights':common, 'diagonal_guards':tuple(sorted(guards)),
               'special_diagonal_orbit':special}


def shared_capacity_clauses(weights, guards, pool):
    """Encode C<=2 and each d=>C<=1, sharing the common capacity.

Auxiliaries are existential; a gated sequential counter need not constrain
its flags when every exceptional-diagonal indicator is false.
"""
    from pysat.card import CardEnc, EncType
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
    if len(light) <= DIRECT_LIGHT_LIMIT:
        for triple in combinations(light,3):
            yield [-v for v in triple]
    else:
        yield from CardEnc.atmost(lits=light,bound=2,vpool=pool,encoding=EncType.seqcounter).clauses
    for d in guards:
        for h in heavy:
            yield [-d,-h]
    if not guards or len(light) <= 1:
        return
    if len(light) <= DIRECT_LIGHT_LIMIT:
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


def compact_counts(model):
    """Source/orbit identities only; no lines or CNF are enumerated."""
    return {**family_counts(model), 'encoding_variant':VARIANT,
            'compact_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'direct_light_limit':DIRECT_LIGHT_LIMIT}


def streamed_cnf(model):
    """Yield a complete equivalent family CNF, with no search or RSS claim."""
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    n = model['n']
    four = model['four_count']
    total = len(model['orbits'])
    pool = IDPool(start_from=total+1)
    for ids,bound in ((list(range(1,four+1)),(n-1)//2),
                      (list(range(four+1,total+1)),1)):
        yield from CardEnc.equals(lits=ids,bound=bound,vpool=pool,encoding=EncType.seqcounter).clauses
    for group in line_groups(model):
        if group['special_diagonal_orbit']:
            # Main: 2*sum(diagonal pairs)=2 by the global equality above.
            # Anti-diagonal: empty. Neither has any four-orbit contribution.
            continue
        yield from shared_capacity_clauses(group['off_diagonal_weights'],
                                           group['diagonal_guards'],pool)
