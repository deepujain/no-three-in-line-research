"""Exact incremental SAT with lazy integer-collinearity cuts.

Requires optional python-sat. Only valid independently checked witnesses are
published. UNSAT is solver-reported, not an independently checked proof.
"""
import time
_PROCESS_STARTED = time.monotonic()
import argparse
import hashlib
import json
import math
import sys
import threading
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver
from verify import verify_certificate, verify_certificate_bruteforce


def _cell(n, x, y):
    return y * n + x + 1


def axis_encoding(n, target=None):
    """Exact row/column capacities for target 2n or 2n-1.

    The deficient target uses one Boolean per row and per column, exactly one
    true in each family, and sum(real cells)+deficit=2 on every axis. Deficits
    are independent indicators, not one artificial cell. IDs from IDPool keep
    real cells, deficit indicators and cardinality auxiliaries disjoint.
    """
    if type(n) is not int or n < 2:
        raise ValueError('n must be integer >= 2')
    target = 2*n if target is None else target
    if type(target) is not int or target not in (2*n, 2*n-1):
        raise ValueError('target must be 2*n or 2*n-1')
    pool = IDPool(start_from=n*n + 1)
    clauses = []
    deficits = {'row': [], 'column': []}
    if target == 2*n-1:
        deficits = {axis: [pool.id((axis+'_deficit', i)) for i in range(n)]
                    for axis in ('row', 'column')}
        for family in deficits.values():
            clauses.extend(CardEnc.equals(lits=family, bound=1, vpool=pool,
                                          encoding=EncType.seqcounter).clauses)
    for i in range(n):
        for axis, cells in (('row', [_cell(n, x, i) for x in range(n)]),
                            ('column', [_cell(n, i, y) for y in range(n)])):
            if deficits[axis]:
                cells.append(deficits[axis][i])
            clauses.extend(CardEnc.equals(lits=cells, bound=2, vpool=pool,
                                          encoding=EncType.seqcounter).clauses)
    return clauses, pool, deficits


def search(n, seconds, backend='glucose3', *, target=None, all_line_constraints=False, checkpoint=None, max_cuts=None, progress=None, progress_interval=5.0,
           extra_clauses=None, scope=None):
    """Lazy SAT; optional scoped initial clauses never enter geometry checkpoints.

    Additional clauses may reference real cells only, and require explicit scope
    metadata so solver-reported UNSAT cannot be mistaken for unrestricted UNSAT.
    """
    if type(n) is not int or n < 2:
        raise ValueError('n must be integer >= 2')
    target = 2*n if target is None else target
    if type(target) is not int or target not in (2*n, 2*n-1):
        raise ValueError('target must be 2*n or 2*n-1')
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('seconds must be positive')
    if backend not in ('glucose3', 'minisat22'):
        raise ValueError('supported interruptible backends: glucose3, minisat22')
    if max_cuts is not None and (type(max_cuts) is not int or max_cuts < 0):
        raise ValueError('max_cuts must be a nonnegative integer')
    if not math.isfinite(progress_interval) or progress_interval <= 0:
        raise ValueError('progress_interval must be positive')
    if all_line_constraints and n > 6:
        raise ValueError('full triple expansion is restricted to tiny validation instances')
    if checkpoint is not None and progress is not None and Path(checkpoint).resolve() == Path(progress).resolve():
        raise ValueError('checkpoint and progress paths must differ')
    if scope is not None and (not isinstance(scope,dict) or not isinstance(scope.get('family'),str) or not scope['family']):
        raise ValueError('scope must be a dict with a nonempty family name')
    if extra_clauses is not None and scope is None:
        raise ValueError('extra_clauses require explicit scope metadata')
    search_scope = dict(scope) if scope is not None else {'family':'unrestricted'}
    scoped_clauses = []
    if extra_clauses is not None:
        if not isinstance(extra_clauses,(list,tuple)):
            raise ValueError('extra_clauses must be an array of clauses')
        for clause in extra_clauses:
            if not isinstance(clause,(list,tuple)) or any(type(v) is not int or not 1 <= abs(v) <= n*n for v in clause):
                raise ValueError('extra clauses may contain only nonzero real-cell integer literals')
            scoped_clauses.append(list(clause))
    start = time.monotonic()
    deadline = start + seconds
    clauses, pool, deficits = axis_encoding(n, target)
    initial = len(clauses)
    clauses.extend(scoped_clauses)
    if all_line_constraints:
        from itertools import combinations
        from line_model import line_variable_ids
        for line in line_variable_ids(n):
            clauses.extend([[-a, -b, -c] for a,b,c in combinations(line, 3)])
    solver = Solver(name=backend, bootstrap_with=clauses)
    fired = threading.Event()
    def stop():
        fired.set()
        solver.interrupt()
    remaining = max(0.0, deadline-time.monotonic())
    timer = threading.Timer(remaining, stop)
    timer.daemon = True
    timer.start()
    iterations = cuts = loaded = 0
    status = 'timeout'
    witness = None
    checkpoint_file = progress_file = None
    last_progress = start
    def record_progress(final=False):
        nonlocal last_progress
        now = time.monotonic()
        if progress_file and (final or now-last_progress >= progress_interval):
            progress_file.write(json.dumps({'n':n,'target':target,'scope_family':search_scope['family'],'elapsed_seconds':round(now-start,3),'iterations':iterations,'cuts_added':cuts,'cuts_loaded':loaded,'status':status if final else 'running'})+'\n')
            progress_file.flush()
            last_progress = now
    try:
        if progress is not None:
            progress_file = open(progress, 'a', encoding='utf-8', buffering=1)
        if checkpoint is not None:
            checkpoint_path = Path(checkpoint)
            if checkpoint_path.exists() and checkpoint_path.stat().st_size:
                with checkpoint_path.open(encoding='utf-8') as f:
                    header = json.loads(f.readline())
                    if not isinstance(header,dict) or header.get('format') != 'no3-geometry-cuts-v1' or header.get('n') != n or type(header.get('n')) is not int:
                        raise ValueError('checkpoint header or grid mismatch')
                    for line in f:
                        if fired.is_set() or time.monotonic() >= deadline:
                            break
                        ids = json.loads(line)
                        if not isinstance(ids,list) or len(ids)!=3 or any(type(v) is not int or v < 1 or v > n*n for v in ids) or len(set(ids))!=3:
                            raise ValueError('invalid checkpoint triple IDs')
                        pts = [((v-1)%n,(v-1)//n) for v in ids]
                        a,b,c = pts
                        if (b[0]-a[0])*(c[1]-a[1]) != (b[1]-a[1])*(c[0]-a[0]):
                            raise ValueError('checkpoint triple is not collinear')
                        solver.add_clause([-v for v in ids])
                        loaded += 1
                        record_progress()
            else:
                with checkpoint_path.open('w',encoding='utf-8') as f:
                    f.write(json.dumps({'format':'no3-geometry-cuts-v1','n':n,'variable_mapping':'y*n+x+1','source':'lazy_sat.py exact geometry', 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})+'\n')
            checkpoint_file = checkpoint_path.open('a',encoding='utf-8',buffering=1024*1024)
        while not fired.is_set() and time.monotonic() < deadline:
            if max_cuts is not None and cuts >= max_cuts:
                status = 'cut_limit'
                break
            record_progress()
            answer = solver.solve_limited(expect_interrupt=True)
            if answer is None or fired.is_set() or time.monotonic() >= deadline:
                break
            if answer is False:
                status = 'unsat_solver_reported'
                break
            iterations += 1
            true_vars = set(v for v in solver.get_model() if 0 < v <= n*n)
            points = [[(v-1)%n, (v-1)//n] for v in sorted(true_vars)]
            candidate = {'n':n,'points':points}
            checked = verify_certificate(candidate)
            if checked['point_count'] != target or checked['errors']:
                raise RuntimeError('SAT model violates cardinality or domain')
            if checked['valid']:
                independent = verify_certificate_bruteforce(candidate)
                if not independent['valid'] or independent['point_count'] != target:
                    raise RuntimeError('independent verifier disagreement')
                status = 'valid_witness'
                witness = {**candidate, 'target':target, 'normalized_sha256': independent['normalized_sha256']}
                break
            for conflict in checked['conflicts']:
                if max_cuts is not None and cuts >= max_cuts:
                    status = 'cut_limit'
                    break
                ids = [_cell(n,*p) for p in conflict['points']]
                solver.add_clause([-v for v in ids])
                if checkpoint_file:
                    checkpoint_file.write(json.dumps(ids,separators=(',',':'))+'\n')
                cuts += 1
                record_progress()
                if fired.is_set() or time.monotonic() >= deadline:
                    break
    finally:
        record_progress(final=True)
        if checkpoint_file:
            checkpoint_file.close()
        if progress_file:
            progress_file.close()
        timer.cancel()
        timer.join()
        solver.delete()
    report = {'n':n,'target':target,'backend':backend,'seed':'backend default; no seed specified',
              'seconds_limit':seconds,'elapsed_seconds':round(time.monotonic()-start,6),
              'status':status,'iterations':iterations,'lazy_cuts_added':cuts,'checkpoint_cuts_loaded':loaded,
              'checkpoint':str(checkpoint) if checkpoint is not None else None,
              'max_new_cuts':max_cuts,'progress':str(progress) if progress is not None else None,
              'initial_row_column_clauses':initial,'initial_total_clauses':len(clauses),
              'initial_scoped_clauses':len(scoped_clauses),'scope':search_scope,
              'initial_variable_count':pool.top,
              'axis_encoding':'exactly_two_per_axis' if target == 2*n else 'independent_single_row_and_column_deficit_indicators',
              'row_deficit_indicator_count':len(deficits['row']),
              'column_deficit_indicator_count':len(deficits['column']),
              'axis_noncell_variable_count':max(0,pool.top-n*n),
              'checkpoint_semantics':'validated real-cell geometry triples only; independent of target; exclusive file ownership required',
              'full_line_constraints_initially':all_line_constraints,
              'timer_interrupt_fired':fired.is_set(),'witness':witness,
              'note':'Timeout is incomplete. UNSAT applies only to the reported scope and is solver-reported without independent proof checking. Only double-verified witnesses are returned.'}
    return report


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if '--diagonal-rowbatch-chain' in arguments:
        arguments.remove('--diagonal-rowbatch-chain')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_rowbatch_chain import main as rowbatch_chain_main
        return rowbatch_chain_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--diagonal-rowbatch-checkpoint-guard' in arguments:
        arguments.remove('--diagonal-rowbatch-checkpoint-guard')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_rowbatch_checkpoint_guard import main as rowbatch_guard_main
        return rowbatch_guard_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--diagonal-secant-chain' in arguments:
        arguments.remove('--diagonal-secant-chain')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_secant_chain import main as diagonal_chain_main
        return diagonal_chain_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--diagonal-secant-checkpoint-guard' in arguments:
        arguments.remove('--diagonal-secant-checkpoint-guard')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_secant_checkpoint_guard import main as checkpoint_guard_main
        return checkpoint_guard_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--diagonal-secant-fast-guard' in arguments:
        arguments.remove('--diagonal-secant-fast-guard')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_secant_fast_guard import main as diagonal_fast_guard_main
        return diagonal_fast_guard_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--diagonal-secant-guard' in arguments:
        arguments.remove('--diagonal-secant-guard')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.diagonal_secant_guard import main as diagonal_guard_main
        return diagonal_guard_main(arguments, started=_PROCESS_STARTED if argv is None else time.monotonic())
    if '--near-quarter-direct-solve' in arguments:
        arguments.remove('--near-quarter-direct-solve')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_direct_solve import main as direct_solve_main
        return direct_solve_main(arguments)
    if '--near-quarter-direct-preflight' in arguments:
        arguments.remove('--near-quarter-direct-preflight')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_direct_preflight import main as direct_preflight_main
        return direct_preflight_main(arguments)
    if '--near-quarter-row-quota-owned-solve' in arguments:
        arguments.remove('--near-quarter-row-quota-owned-solve')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_row_quota_owned_solve import main as owned_row_solve_main
        return owned_row_solve_main(arguments)
    if '--near-quarter-row-quota-owned-preflight' in arguments:
        arguments.remove('--near-quarter-row-quota-owned-preflight')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_row_quota_owned_preflight import main as owned_row_preflight_main
        return owned_row_preflight_main(arguments)
    if '--near-quarter-row-quota-preflight' in arguments:
        arguments.remove('--near-quarter-row-quota-preflight')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_row_quota_preflight import main as row_quota_preflight_main
        return row_quota_preflight_main(arguments)
    if '--near-quarter-compact-solve' in arguments:
        arguments.remove('--near-quarter-compact-solve')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_compact_solve import main as compact_solve_main
        return compact_solve_main(arguments)
    if '--near-quarter-compact-preflight' in arguments:
        arguments.remove('--near-quarter-compact-preflight')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_compact_preflight import main as compact_preflight_main
        return compact_preflight_main(arguments)
    if '--near-quarter-preflight' in arguments:
        arguments.remove('--near-quarter-preflight')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from research.near_quarter_preflight import main as preflight_main
        return preflight_main(arguments)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    parser.add_argument('--target', type=int, help='2*n (default) or 2*n-1')
    parser.add_argument('--symmetry',choices=('diagonal','halfturn'),help='optional restricted invariant family; UNSAT then applies only to that family')
    parser.add_argument('--backend', default='glucose3', choices=('glucose3','minisat22'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--checkpoint', type=Path, help='validated geometry-only JSONL checkpoint; exclusive process ownership required')
    parser.add_argument('--max-cuts', type=int, help='maximum newly added cuts in this invocation')
    parser.add_argument('--progress', type=Path, help='append progress JSONL')
    parser.add_argument('--progress-interval', type=float, default=5.0)
    args = parser.parse_args(arguments)
    if args.output and any(path is not None and args.output.resolve() == path.resolve() for path in (args.checkpoint,args.progress)):
        parser.error('output must differ from checkpoint and progress')
    try:
        options = {'target':args.target,'checkpoint':args.checkpoint,'max_cuts':args.max_cuts,
                   'progress':args.progress,'progress_interval':args.progress_interval}
        if args.symmetry:
            from symmetric_sat import search as symmetric_search
            report = symmetric_search(args.n,args.seconds,'half-turn' if args.symmetry=='halfturn' else 'diagonal',
                                      args.backend,_engine=search,**options)
        else:
            report = search(args.n,args.seconds,args.backend,**options)
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(report, indent=2, sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(payload)
    print(payload)

if __name__ == '__main__':
    sys.exit(main())
