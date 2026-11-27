"""Fresh local-retention SAT; CLI scope is score11 n79,target157,D6 only."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver
from lazy_sat import axis_encoding, _cell
from research.score11_cover_repair import load_source, SOURCE_BYTES, SOURCE_NORMALIZED
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import normalized_direction, normalized_sha256, verify_certificate, verify_certificate_bruteforce


def check_time(deadline, clock):
    if clock() >= deadline:
        raise TimeoutError


def retention_encoding(source_ids, max_deleted, pool):
    source_ids = list(source_ids)
    if (len(source_ids) != len(set(source_ids)) or any(type(v) is not int or v <= 0 for v in source_ids)
            or type(max_deleted) is not int or not 0 <= max_deleted <= len(source_ids)):
        raise ValueError('invalid source literals or deletion bound')
    return CardEnc.atmost(lits=[-v for v in source_ids], bound=max_deleted,
                          vpool=pool, encoding=EncType.seqcounter).clauses


def build_formula(n, target, source_points, conflicts, max_deleted):
    source_points = set(source_points)
    if (len(source_points) != 2 * n or any(type(x) is not int or type(y) is not int or not (0 <= x < n and 0 <= y < n) for x, y in source_points)
            or Counter(x for x, y in source_points) != Counter({i: 2 for i in range(n)})
            or Counter(y for x, y in source_points) != Counter({i: 2 for i in range(n)})):
        raise ValueError('source must have exactly two points per axis')
    clauses, pool, deficits = axis_encoding(n, target)
    axis_count = len(clauses)
    axis_top = pool.top
    clauses.extend(retention_encoding([_cell(n, *p) for p in sorted(source_points)], max_deleted, pool))
    retention_count = len(clauses) - axis_count
    seen = set()
    for conflict in conflicts:
        triple = frozenset(conflict)
        if len(triple) != 3 or not triple <= source_points or triple in seen:
            raise ValueError('invalid source conflict')
        a, b, c = sorted(triple)
        if (b[0] - a[0]) * (c[1] - a[1]) != (b[1] - a[1]) * (c[0] - a[0]):
            raise ValueError('source conflict is not collinear')
        seen.add(triple)
        clauses.append([-_cell(n, *p) for p in sorted(triple)])
    stats = {'initial_variable_count': pool.top, 'axis_variable_top': axis_top,
             'initial_axis_clauses': axis_count, 'initial_retention_clauses': retention_count,
             'initial_source_geometry_clauses': len(seen), 'initial_total_clauses': len(clauses),
             'initial_literal_entries': sum(map(len, clauses)),
             'row_deficit_indicator_count': len(deficits['row']),
             'column_deficit_indicator_count': len(deficits['column'])}
    if pool.top > 60000 or len(clauses) > 110000 or stats['initial_literal_entries'] > 400000:
        raise ValueError('formula exceeds reviewed construction ceilings')
    return clauses, stats


def model_points(model, n, target, source_points, max_deleted):
    assignment = {}
    for literal in model:
        if type(literal) is not int or literal == 0:
            raise RuntimeError('malformed native model')
        if abs(literal) <= n * n:
            if abs(literal) in assignment:
                raise RuntimeError('duplicate real-cell assignment')
            assignment[abs(literal)] = literal > 0
    if len(assignment) != n * n:
        raise RuntimeError('partial real-cell model')
    points = {((v - 1) % n, (v - 1) // n) for v, selected in assignment.items() if selected}
    if (len(points) != target or any(v > 2 for v in Counter(x for x, y in points).values())
            or any(v > 2 for v in Counter(y for x, y in points).values())
            or len(source_points - points) > max_deleted):
        raise RuntimeError('native model violates target, axes or hard retention')
    return points


def conflict_stream(points, deadline=math.inf, clock=time.monotonic):
    """Every triple once by its smallest point index, with bounded anchor state."""
    ordered = sorted(points)
    for i, (x, y) in enumerate(ordered):
        check_time(deadline, clock)
        groups = {}
        for q in ordered[i + 1:]:
            check_time(deadline, clock)
            groups.setdefault(normalized_direction(q[0] - x, q[1] - y), []).append(q)
        for group in groups.values():
            for b, c in itertools.combinations(group, 2):
                check_time(deadline, clock)
                yield ordered[i], b, c


def separate(points, emit, state, deadline, clock, remaining, batch_limit):
    limit = min(remaining, batch_limit)
    if limit <= 0:
        return
    for triple in conflict_stream(points, deadline, clock):
        emit(triple)
        state['conflict_lower_bound'] += 1
        if state['conflict_lower_bound'] >= limit:
            return
    state['scan_complete'] = True


def audit_and_save(points, n, target, source_points, max_deleted, score, path, metadata, deadline, clock):
    cert = {'n': n, 'points': [list(p) for p in sorted(points)]}
    # Recheck retention directly even when invoked after a native model check.
    if len(points) != target or len(source_points - points) > max_deleted:
        raise RuntimeError('saved candidate violates hard scope')
    check_time(deadline, clock)
    first = verify_certificate(cert)
    check_time(deadline, clock)
    second = verify_certificate_bruteforce(cert)
    if score != 0:
        check_time(deadline, clock)
    if (any(c['errors'] or c['point_count'] != target or c['conflict_count'] != score or c['valid'] != (score == 0) for c in (first, second))
            or first['normalized_sha256'] != second['normalized_sha256']):
        raise RuntimeError('saved candidate dual audit disagreement')
    cert['metadata'] = {**metadata, 'valid': score == 0, 'exact_conflict_count': score,
                        'normalized_sha256': first['normalized_sha256']}
    atomic(path, encode(cert))
    return first['normalized_sha256']


def search_local(n, target, source_points, conflicts, max_deleted, out, seconds, *,
                 max_new_cuts=20000, batch_limit=256, clock=time.monotonic,
                 started=None, source_bytes_sha256=None):
    """Generic tiny-test kernel; only the fixed reviewed scope is exposed by CLI."""
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 25
            or type(max_new_cuts) is not int or not 0 <= max_new_cuts <= 20000
            or type(batch_limit) is not int or not 1 <= batch_limit <= 256):
        raise ValueError('invalid reviewed time/cut limits')
    source_points = set(source_points)
    start = clock() if started is None else started
    deadline = start + seconds
    source_digest = normalized_sha256(n, source_points)
    reference_score = len(conflicts)
    report = {'method': 'score11_hard_retention_sat', 'n': n, 'target': target,
              'max_effective_source_deletions': max_deleted,
              'minimum_retained_source': len(source_points) - max_deleted,
              'source_normalized_sha256': source_digest, 'source_bytes_sha256': source_bytes_sha256,
              'backend': 'glucose3', 'status': 'timeout', 'complete': False,
              'candidate_models': 0, 'complete_candidate_scans': 0, 'partial_candidate_scans': 0,
              'initial_source_conflicts': reference_score, 'new_cuts': 0, 'max_new_cuts': max_new_cuts,
              'cut_cap_excludes_initial_source_clauses': True, 'per_model_cut_limit': batch_limit,
              'old_cuts_loaded': 0, 'source_reference_score': reference_score,
              'source_reference_point_count': len(source_points),
              'best_invalid_score': None, 'best_invalid_saved': False,
              'scope': 'Exact target and axis capacities plus hard effective source deletion cap; no symmetry or patch restriction.',
              'unsat_note': 'Solver-reported scoped UNSAT is conditional; no independent UNSAT proof is checked.'}
    solver = timer = None
    fired = threading.Event()
    cuts = []
    best_score = reference_score
    try:
        check_time(deadline, clock)
        clauses, stats = build_formula(n, target, source_points, conflicts, max_deleted)
        report.update(stats)
        check_time(deadline, clock)
        solver = Solver(name='glucose3', bootstrap_with=clauses)
        del clauses
        check_time(deadline, clock)

        def interrupt():
            fired.set()
            solver.interrupt()

        timer = threading.Timer(max(0, deadline - clock()), interrupt)
        timer.daemon = True
        timer.start()
        while not fired.is_set():
            check_time(deadline, clock)
            if len(cuts) >= max_new_cuts:
                report['status'] = 'cut_limit'
                break
            answer = solver.solve_limited(expect_interrupt=True)
            if fired.is_set() or clock() >= deadline:
                raise TimeoutError
            if answer is None:
                report['status'] = 'solver_unknown'
                break
            if answer is False:
                report['status'] = 'unsat_solver_reported_scoped'
                report['complete'] = True
                break
            try:
                points = model_points(solver.get_model(), n, target, source_points, max_deleted)
            except RuntimeError as error:
                report['status'] = 'invalid_native_model'
                report['native_model_error'] = str(error)
                break
            # A real model must satisfy every freshly added old-source clause.
            if any(set(t) <= points for t in conflicts):
                raise RuntimeError('native model violates initial geometry clauses')
            report['candidate_models'] += 1
            metadata = {'method': report['method'], 'source_normalized_sha256': source_digest,
                        'source_bytes_sha256': source_bytes_sha256, 'target': target,
                        'max_effective_source_deletions': max_deleted,
                        'effective_source_deletions': len(source_points - points),
                        'retained_source_points': len(source_points & points),
                        'new_points': len(points - source_points), 'model_number': report['candidate_models'],
                        'novelty_claim': False}
            state = {'scan_complete': False, 'conflict_lower_bound': 0}

            def emit(triple):
                a, b, c = triple
                if len(set(triple)) != 3 or (b[0] - a[0]) * (c[1] - a[1]) != (b[1] - a[1]) * (c[0] - a[0]):
                    raise RuntimeError('invalid lazy geometry clause')
                ids = sorted(_cell(n, *p) for p in triple)
                solver.add_clause([-v for v in ids])
                cuts.append(ids)
                report['new_cuts'] = len(cuts)

            try:
                separate(points, emit, state, deadline, clock, max_new_cuts - len(cuts), batch_limit)
            finally:
                if state['scan_complete']:
                    report['complete_candidate_scans'] += 1
                else:
                    report['partial_candidate_scans'] += 1
                last_metadata = {**metadata, **state, 'normalized_sha256': normalized_sha256(n, points),
                                 'exact_conflict_count': state['conflict_lower_bound'] if state['scan_complete'] else None,
                                 'valid': False if state['conflict_lower_bound'] else None}
                atomic(out / 'last-candidate.json', encode({'n': n, 'points': [list(p) for p in sorted(points)], 'metadata': last_metadata}))
                report['last_candidate'] = last_metadata
            check_time(deadline, clock)
            if not state['scan_complete']:
                continue
            score = state['conflict_lower_bound']
            if score == 0:
                digest = normalized_sha256(n, points)
                audit_and_save(points, n, target, source_points, max_deleted, 0,
                               out / ('witness-' + digest + '.json'), metadata, deadline, clock)
                report['status'] = 'valid_witness'
                report['witness_normalized_sha256'] = digest
                break
            if score < best_score:
                digest = audit_and_save(points, n, target, source_points, max_deleted, score,
                                        out / 'best-invalid.json', metadata, deadline, clock)
                report['best_invalid_score'] = score
                best_score = score
                report['best_invalid_saved'] = True
                report['best_invalid_normalized_sha256'] = digest
    except TimeoutError:
        report['status'] = 'timeout'
    finally:
        if timer is not None:
            timer.cancel()
            timer.join()
        if solver is not None:
            solver.delete()
    report['timer_interrupt_fired'] = fired.is_set()
    report['elapsed_seconds'] = clock() - start
    payload = encode({'n': n, 'variable_mapping': 'y*n+x+1', 'resumption_supported': False,
                      'initial_source_clause_count': reference_score, 'new_cuts': cuts})
    atomic(out / 'new-geometry-cuts.json', payload)
    report['new_geometry_artifact_sha256'] = hashlib.sha256(payload).hexdigest()
    atomic(out / 'report.json', encode(report))
    return report


def run(source, out, seconds):
    started = time.monotonic()
    points, conflicts = load_source(source)
    if normalized_sha256(79, points) != SOURCE_NORMALIZED:
        raise RuntimeError('fixed source normalized identity changed')
    return search_local(79, 157, points, conflicts, 6, out, seconds,
                        started=started, source_bytes_sha256=SOURCE_BYTES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = run(args.source, args.output_dir, args.seconds)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] in ('valid_witness', 'unsat_solver_reported_scoped', 'cut_limit') else 2


if __name__ == '__main__':
    sys.exit(main())
