"""One bounded blocker-guided scaffold-feasibility gate; no completion DFS."""
import argparse
from dataclasses import dataclass
import hashlib
from itertools import combinations, permutations, product
import json
import math
from pathlib import Path
import sys
import time
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import conflict_directed_sixteen_cycle_rebuild157 as prior
frozen = prior.frozen
SEED_COUNT = 8
POOL_LIMIT = 64
ARC_LIMIT = 4096
ROOT_LIMIT = 4


class ArcCap(Exception):
    pass


class RootCheckCap(Exception):
    pass


@dataclass(frozen=True)
class PoolCell:
    point: tuple
    lower: int
    buckets: tuple
    pairs: tuple


@dataclass(frozen=True)
class Arc:
    pool: int
    a: int
    b: int
    old_mask: int
    rows: int
    cols: int


def new_counters():
    c = frozen.new_counters()
    names = ('pool_cells', 'directions', 'pool_bucket_checks', 'support_choices',
             'table_old_points', 'table_pool_points', 'arc_attempts', 'pair_lookups',
             'forced_points', 'bucket_bounds', 'clauses', 'root_checks',
             'root_cycle_orders', 'root_cycle_edges')
    for name in names:
        c.update({name+'_'+phase: 0 for phase in ('started', 'completed')})
    c.update(arc_admissions=0, arc_rollbacks=0, maximum_seeded=0,
             complete_scaffold_orderings=0, duplicate_scaffolds=0)
    return c


def tick(c, name, check):
    c[name+'_started'] += 1
    check()


def done(c, name):
    c[name+'_completed'] += 1


def determinant(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])


def partition(A, point, c, check):
    """Old-point index masks on primitive unoriented lines through point."""
    groups = {}
    for i, (x, y) in enumerate(A):
        tick(c, 'directions', check)
        dx, dy = x-point[0], y-point[1]
        divisor = math.gcd(dx, dy)
        if not divisor:
            raise ValueError('candidate is an old point')
        dx //= divisor; dy //= divisor
        if dx < 0 or dx == 0 and dy < 0:
            dx = -dx; dy = -dy
        groups[(dx, dy)] = groups.get((dx, dy), 0) | 1 << i
        done(c, 'directions')
    return tuple(sorted((mask for mask in groups.values() if mask.bit_count() > 1),
                        key=lambda mask: tuple(frozen.columns(mask))))


def make_pool(n, A, S, budget, c, check, *, limit=POOL_LIMIT, progress=None):
    if type(limit) is not int or not 1 <= limit <= POOL_LIMIT:
        raise ValueError('invalid pool limit')
    result = []
    for point in product(range(n), repeat=2):
        if point in S:
            continue
        tick(c, 'pool_cells', check)
        buckets = partition(A, point, c, check)
        lower = 0
        for mask in buckets:
            tick(c, 'pool_bucket_checks', check)
            if mask.bit_count() > 4:
                raise ValueError('old line exceeds the exact-five-conflict assumption')
            lower += mask.bit_count()-1
            done(c, 'pool_bucket_checks')
        if lower <= budget:
            pairs = sorted(pair for mask in buckets
                           for pair in combinations(frozen.columns(mask), 2))
            cell = PoolCell(point, lower, buckets,
                            tuple((1 << i) | (1 << j) for i, j in pairs))
            result.append(cell)
            result.sort(key=lambda item: (item.lower, item.point))
            if len(result) > limit:
                result.pop()
        done(c, 'pool_cells')
    if progress is not None:
        progress['pool_scan_complete'] = True
        progress['pool'] = [{'point': list(p.point), 'lower': p.lower} for p in result]
    return tuple(result)


def pool_capacity(n, pool, c, check):
    domains = [0]*n
    for cell in pool:
        check()
        domains[cell.point[0]] |= 1 << cell.point[1]
    return frozen.maximum_matching(domains, n, c, check)


def make_arcs(A, pool, c, check):
    row_index = {}; col_index = {}
    for i, (row, col) in enumerate(A):
        check()
        row_index.setdefault(row, []).append(i)
        col_index.setdefault(col, []).append(i)
    result = []
    for pi, cell in enumerate(pool):
        row, col = cell.point
        for a, b in product(row_index.get(row, ()), col_index.get(col, ())):
            tick(c, 'support_choices', check)
            if a == b or A[a][0] == A[b][0] or A[a][1] == A[b][1]:
                raise ValueError('outside-source support pair is not a matching')
            result.append(Arc(pi, a, b, (1 << a) | (1 << b),
                              (1 << A[a][0]) | (1 << A[b][0]),
                              (1 << A[a][1]) | (1 << A[b][1])))
            done(c, 'support_choices')
    return tuple(sorted(result, key=lambda arc: (pool[arc.pool].lower,
                        pool[arc.pool].point, A[arc.a], A[arc.b])))


def make_tables(A, pool, c, check):
    tables = {}
    for i, j in combinations(range(len(pool)), 2):
        p, q = pool[i].point, pool[j].point
        old = new = 0
        for a, point in enumerate(A):
            tick(c, 'table_old_points', check)
            if determinant(p, q, point) == 0:
                old |= 1 << a
            done(c, 'table_old_points')
        for a, cell in enumerate(pool):
            tick(c, 'table_pool_points', check)
            if a not in (i, j) and determinant(p, q, cell.point) == 0:
                new |= 1 << a
            done(c, 'table_pool_points')
        tables[(i, j)] = (old, new)
    return tables


def conflict_masks(A, conflicts):
    index = {point: i for i, point in enumerate(A)}
    triples = sorted(set(tuple(sorted(t)) for t in conflicts))
    if any(len(t) != 3 or len(set(t)) != 3 or any(p not in index for p in t) for t in triples):
        raise ValueError('invalid old conflict triple')
    return tuple(sum(1 << index[p] for p in t) for t in triples)


def matching_mask(A, mask, c, check):
    rows = cols = 0
    for i in frozen.columns(mask):
        tick(c, 'forced_points', check)
        row, col = A[i]
        if rows >> row & 1 or cols >> col & 1:
            done(c, 'forced_points')
            return False
        rows |= 1 << row; cols |= 1 << col
        done(c, 'forced_points')
    return True


def remaining_bound(pool, Q, mandatory, c, check):
    """Maximum over anchors, never the invalid sum across anchors."""
    maximum = 0
    for pi in frozen.columns(Q):
        value = 0
        for bucket in pool[pi].buckets:
            tick(c, 'bucket_bounds', check)
            value += max(0, (bucket & ~mandatory).bit_count()-1)
            done(c, 'bucket_bounds')
        maximum = max(maximum, value)
    return maximum


def requirement(pool, conflicts, F, Q, U, c, check):
    unit = U & ~F
    if unit:
        return unit & -unit
    for pi in frozen.columns(Q):
        for pair in pool[pi].pairs:
            tick(c, 'clauses', check)
            hit = bool(pair & F)
            done(c, 'clauses')
            if not hit:
                return pair
    for triple in conflicts:
        tick(c, 'clauses', check)
        hit = bool(triple & F)
        done(c, 'clauses')
        if not hit:
            return triple
    return 0


class Constructor:
    """Pure scaffold kernel. A callback may collect tiny scaffold orderings.

    Production callback alone owns the four-key/root-check cap. This kernel
    never performs root geometry or a completion DFS and stores no visited set.
    """
    def __init__(self, A, pool, arcs, tables, conflicts, c, check,
                 seed_count=SEED_COUNT, limit=ARC_LIMIT):
        if type(seed_count) is not int or not 1 <= seed_count <= SEED_COUNT:
            raise ValueError('invalid seed count')
        if type(limit) is not int or not 0 <= limit <= ARC_LIMIT:
            raise ValueError('invalid shared arc cap')
        self.A = tuple(A); self.pool = tuple(pool); self.arcs = tuple(arcs)
        self.tables = MappingProxyType(dict(tables)); self.conflicts = tuple(conflicts); self.c = c
        self.check = check; self.k = seed_count; self.limit = limit
        self.path = []; self.root_restored = False

    def run(self, on_scaffold):
        before = (self.A, self.pool, self.arcs, self.tables, self.conflicts)

        def dfs(F, Q, U, rows, cols):
            self.check()
            needed = requirement(self.pool, self.conflicts, F, Q, U, self.c, self.check)
            if len(self.path) == self.k:
                if needed:
                    return False
                self.c['complete_scaffold_orderings'] += 1
                return bool(on_scaffold(tuple(self.path)))
            for ai, arc in enumerate(self.arcs):
                if self.c['arc_attempts_started'] >= self.limit:
                    raise ArcCap
                tick(self.c, 'arc_attempts', self.check)
                if ((needed and not arc.old_mask & needed) or Q >> arc.pool & 1
                        or rows & arc.rows or cols & arc.cols):
                    done(self.c, 'arc_attempts'); continue
                next_U = U; bad = False
                for pi in frozen.columns(Q):
                    tick(self.c, 'pair_lookups', self.check)
                    old, new = self.tables[tuple(sorted((pi, arc.pool)))]
                    next_U |= old
                    bad = bool(new & Q)
                    done(self.c, 'pair_lookups')
                    if bad:
                        break
                next_F = F | arc.old_mask; next_Q = Q | 1 << arc.pool
                T = next_F | next_U
                if (bad or T.bit_count() > 2*self.k
                        or not matching_mask(self.A, T, self.c, self.check)
                        or T.bit_count()+remaining_bound(self.pool, next_Q, T, self.c, self.check) > 2*self.k):
                    done(self.c, 'arc_attempts'); continue
                done(self.c, 'arc_attempts')
                self.path.append(ai); self.c['arc_admissions'] += 1
                self.c['maximum_seeded'] = max(self.c['maximum_seeded'], len(self.path))
                try:
                    if dfs(next_F, next_Q, next_U, rows | arc.rows, cols | arc.cols):
                        return True
                finally:
                    if self.path.pop() != ai:
                        raise RuntimeError('scaffold rollback mismatch')
                    self.c['arc_rollbacks'] += 1
            return False

        try:
            return dfs(0, 0, 0, 0, 0)
        finally:
            self.root_restored = (not self.path and before ==
                (self.A, self.pool, self.arcs, self.tables, self.conflicts))
            if not self.root_restored:
                raise RuntimeError('scaffold root not restored')


def scaffold(A, S, pool, arcs, selected, conflicts, tables, check):
    """Direct family and all-four-class invariants, before root geometry."""
    selected = tuple(sorted(selected, key=lambda ai: pool[arcs[ai].pool].point))
    Q = tuple(pool[arcs[ai].pool].point for ai in selected)
    supports = tuple((A[arcs[ai].a], A[arcs[ai].b]) for ai in selected)
    F = {p for pair in supports for p in pair}
    if (len(F) != 2*len(selected) or not prior.matching_cells(F)
            or not prior.matching_cells(Q) or set(Q) & set(S)
            or any(q != (a[0], b[1]) for q, (a, b) in zip(Q, supports))):
        raise RuntimeError('scaffold support/source invariant failed')
    Fmask = sum(1 << i for i, p in enumerate(A) if p in F)
    Qmask = sum(1 << arcs[ai].pool for ai in selected)
    for triple in conflicts:
        check()
        if not triple & Fmask:
            raise RuntimeError('unhit old conflict')
    for ai in selected:
        for bucket in pool[arcs[ai].pool].buckets:
            check()
            if (bucket & ~Fmask).bit_count() > 1:
                raise RuntimeError('unhit one-new blocker')
    forced = 0
    for a, b in combinations(selected, 2):
        check()
        old, new = tables[tuple(sorted((arcs[a].pool, arcs[b].pool)))]
        forced |= old
        if old & ~Fmask or new & Qmask:
            raise RuntimeError('two-new/all-new invariant failed')
    R = tuple(p for p in A if p not in F)
    P = tuple(sorted(set(R) | set(Q)))
    return selected, Q, supports, tuple(sorted(F)), R, P, forced


def residual_domains(n, P, S, supports, c, check, progress):
    unsafe = 0
    for a, b in combinations(P, 2):
        unsafe = frozen.scan_line(n, a, b, unsafe, 'root', c, check)
    progress['root_mask_complete'] = True
    progress['root_unsafe_hex'] = hex(unsafe)
    domains = []
    for _, b in supports:
        mask = 0
        for j, (a, _) in enumerate(supports):
            tick(c, 'root_domain_cells', check)
            point = (b[0], a[1])
            if point not in S and not unsafe >> (n*point[0]+point[1]) & 1:
                mask |= 1 << j
            done(c, 'root_domain_cells')
        domains.append(mask)
    progress['root_domains_complete'] = True
    progress['root_domains'] = [list(frozen.columns(mask)) for mask in domains]
    return tuple(domains)


def root_cycle(domains, c, check):
    k = len(domains)
    for tail in permutations(range(1, k)):
        tick(c, 'root_cycle_orders', check)
        order = (0,)+tail; good = True
        edges = tuple(zip(order, order[1:]+(0,)))
        for i, j in edges:
            tick(c, 'root_cycle_edges', check)
            good = bool(domains[i] >> j & 1)
            done(c, 'root_cycle_edges')
            if not good:
                break
        done(c, 'root_cycle_orders')
        if good:
            tau = [-1]*k
            for i, j in edges:
                tau[i] = j
            return tuple(tau)
    return None


def save_ready(n, A, S, F, R, Q, supports, domains, cover, tau, forced,
               path, check, pins, c):
    A = set(A); S = set(S); F = set(F); R = set(R); Q = tuple(Q)
    P = R | set(Q); k = len(Q)
    if (not A < S or len(S-A) != 1 or F != {p for pair in supports for p in pair}
            or len(F) != 2*k or not prior.matching_cells(F) or R != A-F
            or not prior.matching_cells(Q) or set(Q) & S or len(P) != len(A)-k
            or P & S != R or len(S-P) != 2*k+1 or len(P-S) != k
            or not prior.single_cycle(tau) or len(tau) != k
            or any(q != (a[0], b[1]) for q, (a, b) in zip(Q, supports))):
        raise RuntimeError('ready scaffold family/distance invariant failed')
    expected = tuple(side.copy() for side in prior.axes(A, n))
    for a, b in supports:
        expected[0][b[0]] -= 1; expected[1][a[1]] -= 1
    if any(any(actual[i] != expected[a][i] for i in range(n))
           for a, actual in enumerate(prior.axes(P, n))):
        raise RuntimeError('ready scaffold degree invariant failed')
    frozen.validate_matching_cover(domains, k, cover, check, c)
    if cover['matching_size'] != k or any(not domains[i] >> tau[i] & 1 for i in range(k)):
        raise RuntimeError('ready capacity/cycle certificate failed')
    plan = tuple((supports[i][1][0], supports[tau[i]][0][1]) for i in range(k))
    if (not prior.matching_cells(plan) or set(plan) & (S | set(Q))
            or any(sum(p[a] == axis for p in P | set(plan)) != sum(p[a] == axis for p in A)
                   for a in (0, 1) for axis in range(n))):
        raise RuntimeError('ready root plan axis/source invariant failed')
    frozen.verify_pins(pins)
    cert, reports = frozen.dual_valid(P, n, check)
    metadata = {'method': 'blocker_guided_eight_arc_scaffold157',
        'kind': 'root_ready_scaffold', 'valid': True, 'point_count': len(P),
        'normalized_sha256': reports[0]['normalized_sha256'],
        'source_deleted': len(S-P), 'source_retained': len(P & S),
        'new_points_outside_source': len(P-S), 'completion_target': len(A),
        'improves_verified_lower_bound': False, 'is_full_witness': False,
        'residual_plan_joint_geometry_checked': False, 'novelty_claim': False,
        'deleted_from_A': [list(p) for p in sorted(F)],
        'retained': [list(p) for p in sorted(R)], 'planted': [list(p) for p in Q],
        'supports': [[list(a), list(b)] for a, b in supports],
        'forced_old_mask_hex': hex(forced),
        'old_mask_indexing': 'Bit i indexes sorted pinned A coordinates.',
        'residual_domains': [list(frozen.columns(mask)) for mask in domains],
        'residual_matching_cover': cover, 'tau': list(tau),
        'residual_plan': [list(p) for p in plan], 'pins': dict(pins)}
    cert.update(metadata=metadata, validators=reports)
    # No post-validator-two deadline check: save completed ready evidence now.
    frozen.atomic(path, cert)
    return metadata


def root_report(key):
    return {'key': list(key), 'status': 'incomplete', 'complete': False,
            'closure': False, 'invariants_complete': False, 'root_mask_complete': False,
            'root_domains_complete': False, 'root_matching_complete': False,
            'root_cycle_complete': False, 'dual_validation_complete': False,
            'scope': 'Only this exact F and planted Q; no claim for another Q on F.'}


def check_root(n, A, S, pool, arcs, selected, conflicts, tables, out, report,
               root, check, pins):
    c = report['counters']; tick(c, 'root_checks', check)
    try:
        selected, Q, supports, F, R, P, forced = scaffold(A, S, pool, arcs,
            selected, conflicts, tables, check)
        root.update(invariants_complete=True, deleted=[list(p) for p in F],
                    planted=[list(p) for p in Q])
        domains = residual_domains(n, P, S, supports, c, check, root)
        cover = frozen.maximum_matching(domains, len(Q), c, check)
        root.update(root_matching_complete=True, matching_cover=cover)
        if cover['matching_size'] < len(Q):
            root.update(status='root_matching_obstruction', complete=True, closure=True)
            done(c, 'root_checks'); return False
        tau = root_cycle(domains, c, check)
        root.update(root_cycle_complete=True, tau=None if tau is None else list(tau))
        if tau is None:
            root.update(status='root_cycle_obstruction', complete=True, closure=True)
            done(c, 'root_checks'); return False
        report['ready_scaffold'] = save_ready(n, A, S, F, R, Q, supports,
            domains, cover, tau, forced, out/'root-ready149.json', check, pins, c)
        root.update(status='ready', complete=True, dual_validation_complete=True)
        done(c, 'root_checks'); return True
    except TimeoutError:
        root['status'] = 'timeout'; raise
    except Exception:
        root['status'] = 'error'; raise


def execute(n, A, S, conflicts, out, report, check, pins, *, seed_count=SEED_COUNT,
            pool_limit=POOL_LIMIT, arc_limit=ARC_LIMIT, root_limit=ROOT_LIMIT):
    """Tiny-fixture entry point; actual caller uses only the fixed constants."""
    if type(root_limit) is not int or not 1 <= root_limit <= ROOT_LIMIT:
        raise ValueError('invalid root cap')
    if type(seed_count) is not int or not 1 <= seed_count <= SEED_COUNT:
        raise ValueError('invalid seed count')
    if type(arc_limit) is not int or not 0 <= arc_limit <= ARC_LIMIT:
        raise ValueError('invalid arc cap')
    A = tuple(sorted(frozen.cells(A, n))); S = frozen.cells(S, n)
    if not set(A) <= S:
        raise ValueError('old points not contained in source')
    prior.axes(A, n)
    c = report['counters']; clauses = conflict_masks(A, conflicts)
    pool = make_pool(n, A, S, 2*seed_count, c, check,
                     limit=pool_limit, progress=report)
    cover = pool_capacity(n, pool, c, check)
    report.update(pool_matching_complete=True, pool_matching_cover=cover)
    if cover['matching_size'] < seed_count:
        report.update(status='pool_capacity_obstruction', complete=True)
        return
    arcs = make_arcs(A, pool, c, check)
    report.update(supports_complete=True, support_arc_count=len(arcs))
    tables = make_tables(A, pool, c, check)
    report['pair_tables_complete'] = True
    seen = set(); kernel = Constructor(A, pool, arcs, tables, clauses, c,
                                      check, seed_count, arc_limit)

    def on_scaffold(selected):
        key = tuple(sorted(selected))
        if key in seen:
            c['duplicate_scaffolds'] += 1
            return False
        if len(seen) >= root_limit:
            raise RootCheckCap
        seen.add(key)
        root = root_report(key); report['roots'].append(root)
        ready = check_root(n, A, S, pool, arcs, selected, clauses, tables,
                           out, report, root, check, pins)
        if ready:
            return True
        if len(seen) == root_limit:
            raise RootCheckCap
        return False

    try:
        ready = kernel.run(on_scaffold)
        report.update(status='ready' if ready else 'pool_scaffolds_exhausted',
                      complete=True, scaffold_search_exhausted=not ready)
    finally:
        report['root_state_restored'] = kernel.root_restored


def new_report(seconds=25):
    return {'method': 'blocker_guided_eight_arc_scaffold157', 'n': 79,
        'status': 'incomplete', 'complete': False, 'closure': False,
        'shared_soft_seconds': seconds, 'pool_limit': POOL_LIMIT,
        'arc_limit': ARC_LIMIT, 'root_limit': ROOT_LIMIT, 'seed_count': SEED_COUNT,
        'source_validation_complete': False, 'pool_scan_complete': False,
        'pool_matching_complete': False, 'supports_complete': False,
        'pair_tables_complete': False, 'scaffold_search_exhausted': False,
        'root_state_restored': None, 'roots': [], 'ready_scaffold': None,
        'counters': new_counters(),
        'scope': 'Only first64 L/coordinate pool;4096 examined arcs;4 distinct F/Q roots. Root-ready149 only, no completion DFS, full witness, broad exclusion, rerank, retry or automatic continuation.',
        'arithmetic_bounds': {'point_direction_visits': 955031,
            'pool_matching_augmentation_edges': 5056, 'pool_cover_traversal_edges': 64,
            'pool_certificate_checks': 64,
            'pool_pair_table_checks': 445536, 'support_arc_records': 256,
            'pair_lookups': 28672, 'forced_point_checks': 65536,
            'bucket_bound_checks': 524288, 'clause_checks': 1069317,
            'root_line_cell_visits': 3484216, 'root_domain_decisions': 256,
            'root_matching_augmentation_edges': 2048, 'root_cover_traversal_edges': 256,
            'root_certificate_checks_including_final_save': 320,
            'root_cycle_edge_checks': 161280}}


def run(out, seconds=25, *, clock=time.monotonic, started=None):
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or not 0 < seconds <= 25):
        raise ValueError('invalid shared duration')
    start = clock() if started is None else started; deadline = start+seconds

    def check():
        if clock() >= deadline:
            raise TimeoutError('shared soft deadline')

    pins = {}; report = new_report(seconds)
    try:
        for path in (Path(__file__).resolve(), Path(prior.__file__).resolve(),
                     Path(frozen.__file__).resolve(), ROOT/'src/verify.py'):
            check(); pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        A, S, conflicts, validation = prior.load_sources(check, pins)
        report.update(source_validation_complete=True, input_validation=validation,
            input_normalized_sha256=prior.INPUT_NORMALIZED,
            source_normalized_sha256=prior.SOURCE_NORMALIZED)
        execute(79, A, S, conflicts, out, report, check, pins)
    except TimeoutError:
        report['status'] = 'timeout'
    except ArcCap:
        report['status'] = 'arc_attempt_cap'
    except RootCheckCap:
        report['status'] = 'root_check_cap'
    except Exception as error:
        report.update(status='error', error=f'{type(error).__name__}: {error}')
    try:
        frozen.verify_pins(pins)
    except (OSError, ValueError) as error:
        report.update(status='error', complete=False, closure=False, identity_valid=False,
                      error=f'final identity recheck: {error}')
    else:
        report['identity_valid'] = True
    report['pins'] = pins; report['elapsed_seconds'] = clock()-start
    frozen.atomic(out/'report.json', report)
    return report


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=25)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.output_dir, args.seconds, started=started)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['status'] == 'error' else (0 if report['complete'] else 2)


if __name__ == '__main__':
    sys.exit(main())
