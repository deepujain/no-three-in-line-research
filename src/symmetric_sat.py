"""Exact symmetry-restricted wrapper around the lazy SAT engine.

Diagonal reflection seeks 2n-1 points; half-turn seeks 2n. Every imposed orbit
constraint is necessary only within its named invariant family. Solver UNSAT
therefore applies only to that family. Symmetry clauses are initial scoped CNF,
never reusable geometry cuts. Optional python-sat is required.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import resource
import sys
import time

from verify import normalized_direction, verify_certificate, verify_certificate_bruteforce


def _cell(n, x, y):
    return y*n+x+1


def symmetry_encoding(n, symmetry):
    """Return (target, initial real-cell clauses, scope) for one exact family."""
    if type(n) is not int or n < 2:
        raise ValueError('n must be integer >= 2')
    if symmetry not in ('diagonal','half-turn'):
        raise ValueError('symmetry must be diagonal or half-turn')
    target = 2*n-1 if symmetry == 'diagonal' else 2*n
    transform = (lambda x,y: (y,x)) if symmetry == 'diagonal' else (lambda x,y: (n-1-x,n-1-y))
    clauses, orbits, fixed = [], [], []
    equality_clauses = 0
    for y in range(n):
        for x in range(n):
            a = _cell(n,x,y)
            tx,ty = transform(x,y)
            b = _cell(n,tx,ty)
            if a == b:
                fixed.append(a)
            elif a < b:
                clauses.extend(([-a,b],[a,-b]))
                equality_clauses += 2
                orbits.append((a,x,y))
    orbit_groups = defaultdict(list)
    fixed_constraints = orbit_exclusions = diagonal_orbit_exclusions = 0
    if symmetry == 'diagonal':
        # Odd total forces an odd number of fixed points. All fixed points
        # lie on one line, allowing at most two: consequently exactly one.
        clauses.append(fixed)
        fixed_constraints += 1
        for i,a in enumerate(fixed):
            for b in fixed[i+1:]:
                clauses.append([-a,-b])
                fixed_constraints += 1
        for representative,x,y in orbits:
            orbit_groups[x+y].append(representative)
            if (x+y) % 2 == 0:
                diagonal = _cell(n,(x+y)//2,(x+y)//2)
                clauses.append([-representative,-diagonal])
                diagonal_orbit_exclusions += 1
    else:
        # Even total and two-point nonfixed orbits force the odd-grid center
        # absent. Each selected orbit then occupies its full center line pair.
        for center in fixed:
            clauses.append([-center])
            fixed_constraints += 1
        for representative,x,y in orbits:
            direction = normalized_direction(2*x-(n-1),2*y-(n-1))
            orbit_groups[direction].append(representative)
    for group in orbit_groups.values():
        for i,a in enumerate(group):
            for b in group[i+1:]:
                clauses.append([-a,-b])
                orbit_exclusions += 1
    scope = {
        'family':'main_diagonal_reflection' if symmetry == 'diagonal' else 'half_turn_rotation',
        'symmetry':symmetry,'target':target,'restricted':True,
        'transform':'(x,y)->(y,x)' if symmetry == 'diagonal' else '(x,y)->(n-1-x,n-1-y)',
        'invariant_orbit_count':len(orbits),'fixed_cell_count':len(fixed),
        'equality_clauses':equality_clauses,'fixed_point_clauses':fixed_constraints,
        'same_line_orbit_exclusion_clauses':orbit_exclusions,
        'diagonal_point_orbit_exclusion_clauses':diagonal_orbit_exclusions,
        'checkpoint_policy':'only actual real-cell collinear triples are reusable; these scoped symmetry clauses never enter the geometry checkpoint',
        'unsat_scope':'this invariant family only; no claim about unrestricted configurations',
    }
    return target,clauses,scope


def _peak_rss_bytes():
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(usage if sys.platform == 'darwin' else usage*1024)


def search(n, seconds, symmetry, backend='glucose3', *, target=None, checkpoint=None,
           max_cuts=None, progress=None, progress_interval=5.0,
           all_line_constraints=False, _engine=None):
    started = time.monotonic()
    expected,clauses,scope = symmetry_encoding(n,symmetry)
    compiled_seconds = time.monotonic()-started
    if target is not None and (type(target) is not int or target != expected):
        raise ValueError('diagonal requires target 2*n-1; half-turn requires target 2*n')
    if _engine is None:
        from lazy_sat import search as _engine
    report = _engine(n,seconds,backend,target=expected,extra_clauses=clauses,scope=scope,
                         checkpoint=checkpoint,max_cuts=max_cuts,progress=progress,
                         progress_interval=progress_interval,all_line_constraints=all_line_constraints)
    if report['witness'] is not None:
        certificate = report['witness']
        points = set(map(tuple,certificate['points']))
        reflected = {(y,x) for x,y in points} if symmetry == 'diagonal' else {(n-1-x,n-1-y) for x,y in points}
        checks = [verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
        if reflected != points or len(points) != expected or not all(check['valid'] for check in checks):
            raise RuntimeError('symmetric witness failed independent geometry/count/invariance audit')
        report['witness']['symmetry'] = symmetry
        report['witness']['independent_validation'] = [check['algorithm'] for check in checks]
    report['memory_telemetry'] = {
        'peak_process_rss_bytes':_peak_rss_bytes(),
        'limit_enforcement':'external process supervisor; this worker does not impose a resident-memory hard limit',
        'formula_growth_control':'max_cuts bounds new geometry clauses; checkpoint reads are streamed',
    }
    report['novelty_claim'] = False
    report['symmetry_compile_seconds'] = compiled_seconds
    report['wrapper_elapsed_seconds'] = time.monotonic()-started
    report['duration_scope'] = 'SAT engine deadline includes axis encoding, cut loading and solves; symmetry compilation and final independent audits add measured wrapper overhead'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,required=True)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--symmetry',choices=('diagonal','half-turn'),required=True)
    parser.add_argument('--target',type=int)
    parser.add_argument('--backend',choices=('glucose3','minisat22'),default='glucose3')
    parser.add_argument('--checkpoint',type=Path,help='exclusive validated geometry-only JSONL checkpoint')
    parser.add_argument('--progress',type=Path)
    parser.add_argument('--max-cuts',type=int)
    parser.add_argument('--progress-interval',type=float,default=5.0)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args(argv)
    paths = [path.resolve() for path in (args.output,args.checkpoint,args.progress) if path is not None]
    if len(paths) != len(set(paths)):
        parser.error('output, checkpoint and progress paths must differ')
    try:
        report = search(args.n,args.seconds,args.symmetry,args.backend,target=args.target,
                        checkpoint=args.checkpoint,max_cuts=args.max_cuts,progress=args.progress,
                        progress_interval=args.progress_interval)
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(report,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    print(payload)


if __name__ == '__main__':
    main()
