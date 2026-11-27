"""Odd-grid near-quarter-turn model with streamed weighted line capacities.

This is the restricted odd-grid family in Prellberg arXiv:2602.07751 section 3.
No solver is launched by this module. A candidate must be expanded and checked
by both independent integer-geometry verifiers. Failure is family-scoped.
"""
import hashlib
import json
from pathlib import Path

try:
    from .line_model import maximal_lines
    from .verify import verify_certificate, verify_certificate_bruteforce
except ImportError:
    from line_model import maximal_lines
    from verify import verify_certificate, verify_certificate_bruteforce

SOURCE = 'https://arxiv.org/html/2602.07751#S3'


def orbit_map(n):
    """Return ordered orbits and point->1-based variable mapping.

    Four-point orbits avoid both diagonals; main diagonal has half-turn pairs.
    The anti-diagonal, including the center, is always empty.
    """
    if type(n) is not int or n < 3 or n % 2 != 1:
        raise ValueError('n must be an odd integer >= 3')
    def rotate(p):
        x,y = p
        return (y,n-1-x)
    four = set()
    for x in range(n):
        for y in range(n):
            if x == y or x+y == n-1:
                continue
            a = (x,y); b = rotate(a); c = rotate(b); d = rotate(c)
            four.add(tuple(sorted((a,b,c,d))))
    half = [((i,i),(n-1-i,n-1-i)) for i in range(n//2)]
    orbits = sorted(four) + half
    mapping = {}
    for var, orbit in enumerate(orbits,1):
        for point in orbit:
            if point in mapping:
                raise RuntimeError('orbits overlap')
            mapping[point] = var
    return {'n':n, 'orbits':orbits, 'point_to_var':mapping,
            'four_count':len(four), 'diagonal_count':len(half)}


def expand(model, selected):
    """Expand selected 1-based orbit IDs into unique sorted [x,y] pairs."""
    selected = list(selected)
    if len(selected) != len(set(selected)) or any(type(v) is not int or v < 1 or v > len(model['orbits']) for v in selected):
        raise ValueError('selected IDs must be distinct valid orbit variables')
    return [list(p) for v in sorted(selected) for p in model['orbits'][v-1]]


def check_candidate(model, selected):
    """Return both checker reports; invalid candidates are never witnesses."""
    cert = {'n':model['n'], 'points':expand(model,selected)}
    a,b = verify_certificate(cert), verify_certificate_bruteforce(cert)
    good = (len(cert['points']) == 2*model['n'] and a['valid'] and b['valid'])
    return {'valid_full_witness':good, 'certificate':cert if good else None,
            'checks':[a,b], 'scope':'odd-grid near-quarter-turn family'}


def weighted_lines(model, quotient_halfturn=True):
    """Yield (line, sorted (variable,multiplicity) tuple) without global caching.

    Half-turn is a symmetry of every expanded model assignment; a quarter-turn
    is not generally one because the diagonal pair is exceptional.
    """
    n=model['n'];mapping=model['point_to_var']
    for line in maximal_lines(n):
        canonical=tuple(sorted(line))
        if quotient_halfturn:
            rotated=tuple(sorted((n-1-x,n-1-y) for x,y in line))
            if canonical > rotated:
                continue
        weights = {}
        for point in line:
            var=mapping.get(point)
            if var is not None:
                weights[var]=weights.get(var,0)+1
        yield canonical,tuple(sorted(weights.items()))


def family_counts(model):
    n=model['n']
    return {'n':n,'four_orbits':model['four_count'],
            'diagonal_pair_orbits':model['diagonal_count'],
            'orbit_variables':len(model['orbits']),
            'required_four_orbits':(n-1)//2,'required_diagonal_pairs':1,
            'target':2*n,'scope':'near-quarter-turn restricted family',
            'paper':SOURCE,
            'orbit_mapping_sha256':hashlib.sha256(json.dumps(model['orbits'],separators=(',',':')).encode()).hexdigest(),
            'model_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'line_generator_sha256':hashlib.sha256(Path(maximal_lines.__code__.co_filename).read_bytes()).hexdigest()}


def capacity_clauses(weights, pool):
    """Yield exact CNF for sum(weights*vars)<=2; auxiliaries from IDPool.

    A coefficient >2 forces its variable false; coefficient 2 cannot coexist
    with any other positive term; unit terms use an at-most-two sequential
    counter. PySAT is an optional research dependency.
    """
    from pysat.card import CardEnc, EncType
    heavy=[v for v,w in weights if w==2]
    light=[v for v,w in weights if w==1]
    for v,w in weights:
        if w>2:
            yield [-v]
    for i,a in enumerate(heavy):
        for b in heavy[i+1:]:
            yield [-a,-b]
        for b in light:
            yield [-a,-b]
    if len(light)>2:
        yield from CardEnc.atmost(lits=light,bound=2,vpool=pool,encoding=EncType.seqcounter).clauses


def streamed_cnf(model, quotient_halfturn=True):
    """Yield one CNF clause at a time; no full geometry or CNF is retained.

    No automatic model-size/RSS gate: caller must count and gate before building
    a solver. This function is not an unrestricted no-three-in-line model.
    """
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    n=model['n'];four=model['four_count'];total=len(model['orbits'])
    pool=IDPool(start_from=total+1)
    for ids,bound in ((list(range(1,four+1)),(n-1)//2),
                      (list(range(four+1,total+1)),1)):
        yield from CardEnc.equals(lits=ids,bound=bound,vpool=pool,encoding=EncType.seqcounter).clauses
    for _,weights in weighted_lines(model,quotient_halfturn):
        yield from capacity_clauses(weights,pool)
