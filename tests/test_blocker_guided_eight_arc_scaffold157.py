from copy import deepcopy
import hashlib
from itertools import combinations, permutations, product
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import blocker_guided_eight_arc_scaffold157 as m


def determinant(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def conflicts(A):
    return [t for t in combinations(sorted(A), 3) if not determinant(*t)]


def valid(P):
    return not conflicts(P)


def matching(P):
    return len({p[0] for p in P}) == len(P) == len({p[1] for p in P})


def cycle(p):
    if sorted(p) != list(range(len(p))):
        return False
    seen = set(); cursor = 0
    for _ in p:
        seen.add(cursor); cursor = p[cursor]
    return len(seen) == len(p) and cursor == 0


def fixture(extra=()):
    A = tuple(sorted({(i, i) for i in range(4)} | set(extra)))
    S = set(A) | {(0, 1)}
    return 4, A, S


def prepare(n, A, S, k=2, pool_limit=64):
    c = m.new_counters()
    pool = m.make_pool(n, A, S, 2*k, c, lambda: None, limit=pool_limit)
    arcs = m.make_arcs(A, pool, c, lambda: None)
    tables = m.make_tables(A, pool, c, lambda: None)
    old = m.conflict_masks(A, conflicts(A))
    return pool, arcs, tables, old, c


def make_kernel(n=4, extra=(), limit=4096, check=lambda: None):
    n, A, S = fixture(extra)
    pool, arcs, tables, old, c = prepare(n, A, S)
    return m.Constructor(A, pool, arcs, tables, old, c, check, 2, limit), c


def brute_scaffolds(A, S, pool, arcs, k):
    answer = set()
    for ids in combinations(range(len(arcs)), k):
        F = [A[i] for ai in ids for i in (arcs[ai].a, arcs[ai].b)]
        Q = [pool[arcs[ai].pool].point for ai in ids]
        if (len(set(F)) == 2*k and matching(F) and len(set(Q)) == k
                and matching(Q) and not set(Q) & S and valid((set(A)-set(F)) | set(Q))):
            answer.add(ids)
    return answer


class PoolTests(unittest.TestCase):
    def test_exact_direction_cliques_include_four_point_lines(self):
        A = ((0, 0), (0, 3), (1, 1), (2, 2), (3, 3))
        for point in set(product(range(5), repeat=2))-set(A):
            c = m.new_counters(); buckets = m.partition(A, point, c, lambda: None)
            actual = {pair for mask in buckets for pair in combinations(m.frozen.columns(mask), 2)}
            expected = {(i, j) for i, j in combinations(range(len(A)), 2)
                        if determinant(A[i], A[j], point) == 0}
            self.assertEqual(actual, expected)
            lower = sum(mask.bit_count()-1 for mask in buckets)
            minimum = min(len(F) for size in range(len(A)+1)
                          for F in combinations(range(len(A)), size)
                          if all(i in F or j in F for i, j in expected))
            self.assertEqual(lower, minimum)
            self.assertEqual(c['directions_completed'], len(A))
        buckets = m.partition(A, (4, 4), m.new_counters(), lambda: None)
        self.assertIn(4, [b.bit_count() for b in buckets])

    def test_pool_rank_truncation_pair_bounds_and_support_order(self):
        n, A, S = fixture(((0, 3), (1, 2)))
        c = m.new_counters(); progress = {}
        all_pool = m.make_pool(n, A, S, 4, c, lambda: None, progress=progress)
        small = m.make_pool(n, A, S, 4, m.new_counters(), lambda: None, limit=3)
        self.assertEqual(small, all_pool[:3]); self.assertTrue(progress['pool_scan_complete'])
        self.assertEqual(list(all_pool), sorted(all_pool, key=lambda p: (p.lower, p.point)))
        self.assertEqual(c['pool_cells_completed'], n*n-len(S))
        self.assertEqual(c['directions_completed'], (n*n-len(S))*len(A))
        for cell in all_pool:
            self.assertLessEqual(len(cell.pairs), 2*cell.lower)
            self.assertTrue(all(mask.bit_count() <= 4 for mask in cell.buckets))
        arcs = m.make_arcs(A, all_pool, c, lambda: None)
        expected = sorted((pi, a, b) for pi, cell in enumerate(all_pool)
                          for a, x in enumerate(A) for b, y in enumerate(A)
                          if x[0] == cell.point[0] and y[1] == cell.point[1])
        self.assertEqual([(a.pool, a.a, a.b) for a in arcs], expected)
        self.assertLessEqual(len(arcs), 4*len(all_pool))

    def test_pair_tables_equal_direct_determinants(self):
        n, A, S = fixture(((0, 3), (1, 2)))
        pool, arcs, tables, old, c = prepare(n, A, S)
        for (i, j), (old_mask, new_mask) in tables.items():
            p, q = pool[i].point, pool[j].point
            self.assertEqual(old_mask, sum(1 << a for a, r in enumerate(A) if determinant(p, q, r) == 0))
            self.assertEqual(new_mask, sum(1 << a for a, r in enumerate(pool) if a not in (i, j) and determinant(p, q, r.point) == 0))
        self.assertEqual(c['table_old_points_completed'], len(tables)*len(A))
        self.assertEqual(c['table_pool_points_completed'], len(tables)*len(pool))

    def test_pool_capacity_and_partial_preprocess_counters(self):
        n, A, S = fixture(); pool, arcs, tables, old, c = prepare(n, A, S)
        cert = m.pool_capacity(n, pool, c, lambda: None)
        best = max(len(M) for k in range(n+1) for M in combinations([p.point for p in pool], k) if matching(M))
        self.assertEqual(cert['matching_size'], best)
        for phase in ('directions', 'table_old_points', 'table_pool_points'):
            c = m.new_counters(); progress = {}
            def check():
                if c[phase+'_started'] == 2:
                    raise TimeoutError
            with self.assertRaises(TimeoutError):
                if phase == 'directions':
                    m.make_pool(n, A, S, 4, c, check, progress=progress)
                else:
                    m.make_tables(A, pool, c, check)
            self.assertEqual(c[phase+'_started'], 2); self.assertEqual(c[phase+'_completed'], 1)
            self.assertFalse(progress.get('pool_scan_complete', False))


class ScaffoldTests(unittest.TestCase):
    def test_complete_tiny_scaffold_sets_equal_exhaustive_deletions(self):
        for extra in ((), ((0, 3),), ((0, 3), (1, 2)), ((0, 3), (1, 2), (2, 0))):
            n, A, S = fixture(extra); pool, arcs, tables, old, c = prepare(n, A, S)
            expected = brute_scaffolds(A, S, pool, arcs, 2)
            K = m.Constructor(A, pool, arcs, tables, old, c, lambda: None, 2)
            found = []
            self.assertFalse(K.run(lambda ids: found.append(tuple(sorted(ids))) or False))
            self.assertEqual(set(found), expected); self.assertTrue(K.root_restored)
            self.assertEqual(K.path, []); self.assertEqual(c['arc_admissions'], c['arc_rollbacks'])
            self.assertEqual(c['arc_attempts_started'], c['arc_attempts_completed'])
            for ids in set(found):
                result = m.scaffold(A, S, pool, arcs, ids, old, tables, lambda: None)
                self.assertTrue(valid(result[5])); self.assertEqual(len(result[3]), 4)
                self.assertEqual(len(result[1]), 2)

    def test_requirement_priority_and_overlap_uses_maximum(self):
        cells = (m.PoolCell((0, 0), 1, (3,), (3,)),
                 m.PoolCell((1, 1), 1, (3,), (3,)))
        c = m.new_counters()
        self.assertEqual(m.remaining_bound(cells, 3, 0, c, lambda: None), 1)
        self.assertEqual(m.remaining_bound(cells, 3, 1, c, lambda: None), 0)
        self.assertEqual(m.requirement(cells, (12,), 0, 3, 16, c, lambda: None), 16)
        self.assertEqual(m.requirement(cells, (12,), 0, 3, 0, c, lambda: None), 3)
        self.assertEqual(m.requirement(cells, (12,), 1, 3, 0, c, lambda: None), 12)
        self.assertEqual(m.requirement(cells, (12,), 5, 3, 0, c, lambda: None), 0)

    def test_every_checked_dfs_interruption_restores_path(self):
        calls = [0]
        def count():
            calls[0] += 1
        K, c = make_kernel(check=count); K.run(lambda ids: False)
        for stop in range(1, calls[0]+1):
            seen = [0]
            def check():
                seen[0] += 1
                if seen[0] == stop:
                    raise TimeoutError
            K, c = make_kernel(check=check)
            with self.assertRaises(TimeoutError):
                K.run(lambda ids: False)
            self.assertTrue(K.root_restored); self.assertEqual(K.path, [])
            self.assertEqual(c['arc_admissions'], c['arc_rollbacks'])
            self.assertGreaterEqual(c['arc_attempts_started'], c['arc_attempts_completed'])

    def test_cap_zero_through_exhaustion_and_every_examined_record_charged(self):
        K, c = make_kernel(); K.run(lambda ids: False); total = c['arc_attempts_started']
        for cap in range(total+1):
            K, c = make_kernel(limit=cap)
            if cap == total:
                self.assertFalse(K.run(lambda ids: False))
            else:
                with self.assertRaises(m.ArcCap):
                    K.run(lambda ids: False)
            self.assertEqual(c['arc_attempts_started'], cap); self.assertTrue(K.root_restored)
        # Even a non-covering record is examined and charged; no admission is needed.
        K, c = make_kernel(limit=1); K.conflicts = (1 << 100,)
        with self.assertRaises(m.ArcCap):
            K.run(lambda ids: False)
        self.assertEqual(c['arc_attempts_started'], 1); self.assertEqual(c['arc_admissions'], 0)

    def test_shared_4096_attempts_across_tiny_kernels(self):
        K, c = make_kernel(); shared = m.new_counters(); runs = 0
        while True:
            K.c = shared
            runs += 1
            try:
                K.run(lambda ids: False)
            except m.ArcCap:
                break
        self.assertGreater(runs, 1); self.assertEqual(shared['arc_attempts_started'], 4096)
        self.assertEqual(shared['arc_attempts_completed'], 4096)
        self.assertTrue(K.root_restored); self.assertEqual(shared['arc_admissions'], shared['arc_rollbacks'])

    def test_requirement_driven_orders_are_not_forced_increasing(self):
        K, c = make_kernel(); orders = []
        K.run(lambda ids: orders.append(ids) or False)
        self.assertTrue(any(tuple(sorted(ids)) != ids for ids in orders))
        with self.assertRaises(TypeError):
            K.tables[(0, 1)] = (0, 0)


class RootTests(unittest.TestCase):
    def test_all_tiny_directed_graphs_cycles_equal_permutations(self):
        for bits in range(1 << 9):
            domains = tuple((bits >> (3*i)) & 7 for i in range(3))
            expected = [p for p in permutations(range(3)) if cycle(p) and all(domains[i] >> p[i] & 1 for i in range(3))]
            c = m.new_counters(); actual = m.root_cycle(domains, c, lambda: None)
            self.assertEqual(actual is not None, bool(expected))
            if actual is not None:
                self.assertIn(actual, expected)
            self.assertLessEqual(c['root_cycle_edges_started'], 6)
        self.assertIsNone(m.root_cycle((1, 2, 4), m.new_counters(), lambda: None))

    def test_pipeline_saves_ready_not_witness_and_preserves_axes(self):
        n, A, S = fixture(); r = m.new_report()
        with tempfile.TemporaryDirectory() as tmp:
            m.execute(n, A, S, conflicts(A), Path(tmp), r, lambda: None, {}, seed_count=2)
            self.assertEqual(r['status'], 'ready'); self.assertTrue(r['complete'])
            self.assertTrue(r['root_state_restored']); self.assertFalse(r['closure'])
            self.assertTrue((Path(tmp)/'root-ready149.json').exists())
            self.assertFalse((Path(tmp)/'witness157.json').exists())
        meta = r['ready_scaffold']
        self.assertEqual(meta['source_deleted'], 5); self.assertEqual(meta['new_points_outside_source'], 2)
        self.assertFalse(meta['is_full_witness']); self.assertFalse(meta['improves_verified_lower_bound'])
        self.assertFalse(meta['residual_plan_joint_geometry_checked'])
        self.assertTrue(cycle(meta['tau'])); self.assertEqual(len(meta['deleted_from_A']), 4)
        root = r['roots'][-1]
        self.assertTrue(root['root_matching_complete']); self.assertTrue(root['root_cycle_complete'])
        self.assertTrue(root['dual_validation_complete']); self.assertFalse(root['closure'])
        root_edges = sum(sum(len(row) for row in item['root_domains']) for item in r['roots'])
        final_edges = sum(len(row) for row in root['root_domains'])
        self.assertEqual(r['counters']['certificate_edge_checks_completed'],
                         len(r['pool'])+root_edges+final_edges)
        self.assertEqual(r['arithmetic_bounds']['root_certificate_checks_including_final_save'], 320)

    def test_root_domains_equal_determinants_and_cycle_expands(self):
        n, A, S = fixture(); pool, arcs, tables, old, c = prepare(n, A, S)
        ids = next(iter(brute_scaffolds(A, S, pool, arcs, 2)))
        ids, Q, supports, F, R, P, forced = m.scaffold(A, S, pool, arcs, ids, old, tables, lambda: None)
        progress = {}; domains = m.residual_domains(n, P, S, supports, c, lambda: None, progress)
        direct = tuple(sum(1 << j for j, (a, _) in enumerate(supports)
                           if (b[0], a[1]) not in S and valid(set(P) | {(b[0], a[1])}))
                       for _, b in supports)
        self.assertEqual(domains, direct); self.assertTrue(progress['root_domains_complete'])
        for tau in permutations(range(2)):
            label = {p: i for i, p in enumerate(F)}; sigma = [-1]*4
            for i, (a, b) in enumerate(supports):
                sigma[label[a]] = label[b]; sigma[label[b]] = label[supports[tau[i]][0]]
            self.assertEqual(cycle(sigma), cycle(tau))

    def test_four_root_cap_and_same_F_different_Q_are_distinct(self):
        n, A, S = fixture(); r = m.new_report(); visited = []
        def reject(board, a, s, pool, arcs, ids, old, tables, out, report, root, check, pins):
            visited.append(tuple(sorted(pool[arcs[i].pool].point for i in ids)))
            root.update(status='root_matching_obstruction', complete=True, closure=True)
            return False
        with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'check_root', reject):
            with self.assertRaises(m.RootCheckCap):
                m.execute(n, A, S, conflicts(A), Path(tmp), r, lambda: None, {}, seed_count=2)
        self.assertEqual(len(r['roots']), 4); self.assertEqual(len(set(visited)), 4)
        self.assertTrue(r['root_state_restored']); self.assertIsNone(r['ready_scaffold'])
        self.assertFalse(r['complete']); self.assertFalse(r['closure'])

    def test_late_validator_two_persists_ready_and_no_post_save_work(self):
        n, A, S = fixture(); now = [0]; second = m.frozen.verify_certificate_bruteforce
        def late(cert):
            result = second(cert); now[0] = 2; return result
        def check():
            if now[0] >= 1:
                raise TimeoutError
        r = m.new_report()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'verify_certificate_bruteforce', late):
            m.execute(n, A, S, conflicts(A), Path(tmp), r, check, {}, seed_count=2)
            self.assertTrue((Path(tmp)/'root-ready149.json').exists())
        self.assertEqual(r['status'], 'ready'); self.assertTrue(r['roots'][-1]['dual_validation_complete'])
        self.assertTrue(r['root_state_restored'])

    def test_validator_boundary_write_failure_and_pin_mutation(self):
        n, A, S = fixture(); first = m.frozen.verify_certificate
        now = [0]
        def late_first(cert):
            value = first(cert); now[0] = 2; return value
        def check():
            if now[0] >= 1:
                raise TimeoutError
        r = m.new_report()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'verify_certificate', late_first), patch.object(m.frozen, 'verify_certificate_bruteforce') as other:
            with self.assertRaises(TimeoutError):
                m.execute(n, A, S, conflicts(A), Path(tmp), r, check, {}, seed_count=2)
            other.assert_not_called(); self.assertFalse((Path(tmp)/'root-ready149.json').exists())
        self.assertTrue(r['root_state_restored']); self.assertFalse(r['roots'][-1]['complete'])
        r = m.new_report()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'atomic', side_effect=OSError('disk')):
            with self.assertRaises(OSError):
                m.execute(n, A, S, conflicts(A), Path(tmp), r, lambda: None, {}, seed_count=2)
        self.assertTrue(r['root_state_restored']); self.assertEqual(r['roots'][-1]['status'], 'error')
        self.assertIsNone(r['ready_scaffold'])
        with tempfile.TemporaryDirectory() as tmp:
            pin = Path(tmp)/'pin'; pin.write_bytes(b'old'); pins = {str(pin): hashlib.sha256(pin.read_bytes()).hexdigest()}; pin.write_bytes(b'changed')
            r = m.new_report()
            with self.assertRaises(ValueError):
                m.execute(n, A, S, conflicts(A), Path(tmp), r, lambda: None, pins, seed_count=2)
            self.assertFalse((Path(tmp)/'root-ready149.json').exists()); self.assertTrue(r['root_state_restored'])

    def test_root_phase_timeouts_leave_no_closure(self):
        n, A, S = fixture()
        for phase in ('root_cell_visits', 'root_domain_cells', 'root_cycle_edges'):
            r = m.new_report()
            def check():
                if r['counters'][phase+'_started'] == 1:
                    raise TimeoutError
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(TimeoutError):
                m.execute(n, A, S, conflicts(A), Path(tmp), r, check, {}, seed_count=2)
            self.assertEqual(r['roots'][-1]['status'], 'timeout')
            self.assertFalse(r['roots'][-1]['complete']); self.assertFalse(r['roots'][-1]['closure'])
            self.assertTrue(r['root_state_restored']); self.assertIsNone(r['ready_scaffold'])


class TopLevelTests(unittest.TestCase):
    def test_stubbed_run_timeout_caps_error_and_final_pins(self):
        # No fixed input is loaded. These stubs perform no n79 construction.
        for failure in (TimeoutError, m.ArcCap, m.RootCheckCap, ValueError):
            r = None
            with tempfile.TemporaryDirectory() as tmp, patch.object(m.prior, 'load_sources', return_value=(set(), set(), [], [])), patch.object(m, 'execute', side_effect=failure):
                r = m.run(Path(tmp), clock=lambda: 0)
                self.assertEqual(r['status'], {TimeoutError: 'timeout', m.ArcCap: 'arc_attempt_cap', m.RootCheckCap: 'root_check_cap', ValueError: 'error'}[failure])
                self.assertFalse(r['complete']); self.assertFalse(r['closure'])
                self.assertTrue((Path(tmp)/'report.json').exists())
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.prior, 'load_sources', return_value=(set(), set(), [], [])), patch.object(m, 'execute'), patch.object(m.frozen, 'verify_pins', side_effect=ValueError('changed')):
            r = m.run(Path(tmp), clock=lambda: 0)
            self.assertEqual(r['status'], 'error'); self.assertFalse(r['identity_valid'])
            self.assertFalse(r['complete']); self.assertFalse(r['closure'])

    def test_invalid_duration_and_limits(self):
        for value in (0, 26, True, float('nan')):
            with self.assertRaises(ValueError):
                m.run(Path('/unused'), value)
        for kwargs in ({'seed_count': 0}, {'arc_limit': 4097}, {'root_limit': 5}):
            with self.assertRaises(ValueError):
                m.execute(2, (), set(), [], Path('/unused'), m.new_report(), lambda: None, {}, **kwargs)


if __name__ == '__main__':
    unittest.main()
