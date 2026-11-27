from collections import Counter
from copy import deepcopy
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import conflict_directed_sixteen_cycle_rebuild157 as m


def collinear(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])


def valid(P):
    return not any(collinear(*t) for t in combinations(P, 3))


def is_cycle(p):
    return all(len({iterate(p, i, j) for j in range(len(p))}) == len(p)
               and iterate(p, i, len(p)) == i for i in range(len(p)))


def iterate(p, i, count):
    for _ in range(count):
        i = p[i]
    return i


def fixture():
    n = 3
    A = {(0, 1), (1, 1), (1, 2), (2, 0), (2, 2)}
    S = A | {(0, 0)}
    F = ((0, 1), (1, 2), (2, 0))
    return n, A, S, F, tuple(sorted(A-set(F)))


def report():
    return {'counters': m.new_counters(), 'diagnostic156': None, 'witness157': None}


def kernel(n=3, R=(), S=None, F=None, limit=1000, check=lambda: None, counters=None):
    F = F or tuple((i, i) for i in range(n))
    S = set(F) if S is None else S
    c = m.new_counters() if counters is None else counters
    u, d = m.root_domains(n, R, S, F, c, lambda: None)
    return m.Constructor(n, R, S, F, d, u, c, check, limit), c


class CoverTests(unittest.TestCase):
    def test_kernels_subcover_completeness_on_tiny_triple_families(self):
        A = {(i, j) for i in range(3) for j in range(3) if i != j}
        triples = list(combinations(sorted(A), 3))
        families = [()] + [(t,) for t in triples]
        families += [(triples[i], triples[j], triples[(i+j) % len(triples)])
                     for i in range(len(triples)) for j in range(i+1, len(triples))]
        subsets = [set(C) for k in range(len(A)+1) for C in combinations(sorted(A), k)
                   if len({p[0] for p in C}) == len(C) == len({p[1] for p in C})]
        for conflicts in families:
            c = m.new_counters(); found = m.cover_kernels(A, conflicts, c, lambda: None)
            self.assertEqual(found, sorted(set(found), key=lambda C: (len(C), C)))
            for C in found:
                self.assertTrue(m.matching_cells(C))
                self.assertTrue(all(set(C) & set(t) for t in conflicts))
            for H in subsets:
                if all(H & set(t) for t in conflicts):
                    self.assertTrue(any(set(C) <= H for C in found))
            self.assertEqual(c['cover_nodes_started'], c['cover_nodes_completed'])
            self.assertLessEqual(c['cover_nodes_started'], sum(3**i for i in range(len(set(conflicts))+1)))
        # Every three-subset must be hit: at least three removals, matching rank two.
        impossible = {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)}
        self.assertEqual(m.cover_kernels(impossible, combinations(sorted(impossible), 3), m.new_counters(), lambda: None), [])

    def test_deterministic_padding_dedup_and_first_eight(self):
        A = {(i, i) for i in range(6)} | {(i, (i+1) % 6) for i in range(6)}
        ordered = sorted(A)
        conflicts = [tuple(ordered[i:i+3]) for i in (0, 4, 8)]
        # Independent recursive specification, then explicit greedy extension.
        def branch(C):
            if all(set(C) & set(t) for t in conflicts):
                return {tuple(sorted(C))}
            t = next(t for t in sorted(conflicts) if not set(C) & set(t))
            return set().union(*(branch(C+(p,)) for p in sorted(t)
                if all(p[0] != q[0] and p[1] != q[1] for q in C)))
        expected = []
        for C in sorted(branch(()), key=lambda C: (len(C), C)):
            C = list(C)
            while len(C) < 4:
                C.append(next(p for p in ordered if all(p[0] != q[0] and p[1] != q[1] for q in C)))
            F = tuple(sorted(C))
            if F not in expected:
                expected.append(F)
        progress = {}; c = m.new_counters()
        actual = m.select_patches(A, conflicts, 4, c, lambda: None, progress=progress)
        self.assertEqual(actual, expected[:8]); self.assertTrue(progress['kernels_complete'])
        self.assertTrue(progress['patch_selection_complete']); self.assertGreater(len(expected), 8)
        self.assertEqual(m.select_patches(A, conflicts, 4, m.new_counters(), lambda: None, max_patches=1), expected[:1])
        for F in actual:
            self.assertEqual(len(F), 4); self.assertTrue(m.matching_cells(F))

    def test_cover_and_padding_interruptions_have_partial_flags(self):
        A = {(i, i) for i in range(4)}; conflicts = [tuple(sorted(A)[:3])]
        for phase in ('cover_nodes', 'padding_cells'):
            c = m.new_counters(); progress = {}
            def check():
                if c[phase+'_started'] == 2:
                    raise TimeoutError
            with self.assertRaises(TimeoutError):
                m.select_patches(A, conflicts, 3, c, check, progress=progress)
            self.assertGreater(c[phase+'_started'], c[phase+'_completed'])
            self.assertNotIn('patch_selection_complete', progress)
            self.assertEqual(progress.get('kernels_complete', False), phase == 'padding_cells')


class GeometryCycleTests(unittest.TestCase):
    def test_domains_equal_determinants_on_noncontiguous_freed_axes(self):
        for n in (3, 4, 5):
            F = ((0, n-1), (n-1, 0))
            for R in ((), ((1, 1),), ((1, 1), (2, 2)) if n > 3 else ((1, 1), (1, 2))):
                if set(R) & set(F):
                    continue
                S = set(R) | set(F) | {(0, 0)}
                c = m.new_counters(); unsafe, domains = m.root_domains(n, R, S, F, c, lambda: None)
                for p in product(range(n), repeat=2):
                    self.assertEqual(bool(unsafe >> (n*p[0]+p[1]) & 1), any(collinear(a, b, p) for a, b in combinations(R, 2)))
                expected = [sum(1 << j for j, (_, y) in enumerate(F)
                            if (x, y) not in S and valid(R+((x, y),))) for x, _ in F]
                self.assertEqual(domains, expected)
                self.assertEqual(c['root_domain_cells_completed'], 4)

    def test_every_proper_length_rejected_final_cycle_accepted(self):
        for k in range(2, 7):
            for length in range(1, k+1):
                sigma = [-1]*k
                for i in range(length-1):
                    sigma[i] = i+1
                self.assertEqual(m.proper_cycle(length-1, 0, sigma), length < k)
            for p in permutations(range(k)):
                self.assertEqual(m.single_cycle(p), is_cycle(p))
        self.assertFalse(m.single_cycle((1, 0, 3, 2)))

    def test_complete_tiny_search_matches_bruteforce_permutations(self):
        for n in range(2, 6):
            F = tuple((i, i) for i in range(n))
            for R in ((), ((0, n-1),)):
                S = set(F) | set(R)
                expected = {frozenset((F[i][0], F[p[i]][1]) for i in range(n))
                            for p in permutations(range(n)) if is_cycle(p)
                            and not {(F[i][0], F[p[i]][1]) for i in range(n)} & S
                            and valid(tuple(R)+tuple((F[i][0], F[p[i]][1]) for i in range(n)))}
                K, c = kernel(n, R, S, F); found = []
                def callback(M):
                    self.assertTrue(valid(tuple(R)+M)); self.assertFalse(set(M) & S)
                    self.assertTrue(m.matching_cells(M))
                    if len(M) == n:
                        found.append(frozenset(M))
                    return False
                self.assertFalse(K.run(callback)); self.assertEqual(set(found), expected)
                self.assertEqual(len(found), len(expected)); self.assertTrue(K.root_restored)
                self.assertEqual(K.sigma, [-1]*n); self.assertEqual(K.path, [])
                self.assertEqual(c['insertions_started'], c['insertions_completed'])
                self.assertEqual(c['rollbacks'], c['insertions_completed'])

    def test_root_perfect_matching_can_have_only_prohibited_subcycles(self):
        K, c = kernel(n=4)
        K.domains = (2, 1, 8, 4)
        cert = m.frozen.maximum_matching(K.domains, 4, c, lambda: None)
        self.assertEqual(cert['matching_size'], 4)
        self.assertFalse(K.run(lambda M: self.fail('proper cycle reached callback')))
        self.assertGreater(c['cycle_pruned_choices'], 0); self.assertEqual(c['full_assignments'], 0)
        self.assertTrue(K.root_restored)

    def test_every_dfs_check_interruption_and_cap_restores_all_state(self):
        calls = [0]
        def count():
            calls[0] += 1
        K, c = kernel(n=4, check=count); K.run(lambda M: False)
        total = calls[0]; starts = c['insertions_started']
        for stop in range(1, total+1):
            seen = [0]
            def check():
                seen[0] += 1
                if seen[0] == stop:
                    raise TimeoutError
            K, c = kernel(n=4, check=check)
            with self.assertRaises(TimeoutError):
                K.run(lambda M: False)
            self.assertTrue(K.root_restored); self.assertEqual(K.path, [])
            self.assertEqual(K.sigma, [-1]*4)
            self.assertGreaterEqual(c['insertions_started'], c['insertions_completed'])
            self.assertEqual(c['insertions_completed'], c['rollbacks'])
        for cap in range(starts+1):
            K, c = kernel(n=4, limit=cap)
            if cap == starts:
                self.assertFalse(K.run(lambda M: False))
            else:
                with self.assertRaises(m.InsertionCap):
                    K.run(lambda M: False)
            self.assertTrue(K.root_restored); self.assertEqual(c['insertions_started'], cap)

    def test_shared_cap_across_separate_patch_kernels_and_first_witness_stop(self):
        counters = m.new_counters()
        K, _ = kernel(counters=counters); self.assertFalse(K.run(lambda M: False))
        first = counters['insertions_started']
        K, _ = kernel(counters=counters, limit=first+1)
        with self.assertRaises(m.InsertionCap):
            K.run(lambda M: False)
        self.assertEqual(counters['insertions_started'], first+1); self.assertTrue(K.root_restored)
        K, c = kernel(); full = []
        def stop(M):
            if len(M) == 3:
                full.append(M); return True
            return False
        self.assertTrue(K.run(stop)); self.assertEqual(len(full), 1)
        self.assertTrue(K.root_restored); self.assertEqual(c['full_assignments'], 1)


class PipelineTests(unittest.TestCase):
    def test_patch_pipeline_first_diagnostic_then_witness(self):
        n, A, S, F, R = fixture(); r = report(); p = m.new_patch_report(0, F); saved = []
        atomic = m.frozen.atomic
        def record(path, doc):
            saved.append((path.name, deepcopy(doc))); atomic(path, doc)
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'atomic', record):
            self.assertTrue(m.search_patch(n, A, S, F, Path(tmp), r, p, lambda: None, {}, 1000))
        self.assertEqual([name for name, _ in saved], ['diagnostic156.json', 'witness157.json'])
        self.assertEqual([len(doc['points']) for _, doc in saved], [4, 5])
        self.assertFalse(saved[0][1]['metadata']['improves_verified_lower_bound'])
        self.assertTrue(saved[1][1]['metadata']['improves_verified_lower_bound'])
        self.assertEqual(saved[1][1]['metadata']['source_deleted'], 4)
        self.assertEqual(tuple(Counter(p[a] for p in saved[1][1]['points']) for a in (0, 1)), m.axes(A, n))
        self.assertTrue(p['complete']); self.assertFalse(p['closure']); self.assertFalse(p['dfs_exhausted'])
        self.assertTrue(p['root_state_restored'])

    def test_patch_partial_phase_flags_and_root_obstruction(self):
        n, A, S, F, R = fixture()
        for phase in ('retained', 'root', 'domains', 'matching'):
            r = report(); p = m.new_patch_report(0, F)
            c = r['counters']
            def check():
                if ((phase == 'retained' and not p['retained_validation_complete'])
                    or (phase == 'root' and c['root_cell_visits_started'] == 2)
                    or (phase == 'domains' and c['root_domain_cells_started'] == 2)
                    or (phase == 'matching' and c['matching_edge_scans_started'] == 1)):
                    raise TimeoutError
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(TimeoutError):
                m.search_patch(n, A, S, F, Path(tmp), r, p, check, {}, 1000)
            self.assertEqual(p['status'], 'timeout'); self.assertFalse(p['complete']); self.assertFalse(p['closure'])
            self.assertEqual(p['root_mask_complete'], phase in ('domains', 'matching'))
            self.assertEqual(p['root_domains_complete'], phase == 'matching')
            self.assertFalse(p['root_matching_complete'])
        r = report(); p = m.new_patch_report(0, F)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(m.search_patch(n, A, set(product(range(n), repeat=2)), F, Path(tmp), r, p, lambda: None, {}, 1000))
        self.assertEqual(p['status'], 'root_matching_obstruction'); self.assertTrue(p['closure'])
        self.assertTrue(p['root_matching_complete']); self.assertEqual(r['counters']['insertions_started'], 0)

    def test_late_valid_witness_saved_no_second_validator_started_late(self):
        n, A, S, F, R = fixture(); M = ((0, 2), (1, 0), (2, 1)); now = [0]
        first = m.frozen.verify_certificate; second = m.frozen.verify_certificate_bruteforce
        def check():
            if now[0] >= 1:
                raise TimeoutError
        def late_second(cert):
            result = second(cert); now[0] = 2; return result
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'verify_certificate_bruteforce', late_second):
            path = Path(tmp)/'witness'
            meta = m.save_candidate(n, A, S, F, R, M, path, 'full_witness', check, {})
            self.assertTrue(path.exists()); self.assertEqual(meta['source_deleted'], len(F)+1)
        now[0] = 0
        def late_first(cert):
            result = first(cert); now[0] = 2; return result
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'verify_certificate', late_first), patch.object(m.frozen, 'verify_certificate_bruteforce') as other:
            with self.assertRaises(TimeoutError):
                m.save_candidate(n, A, S, F, R, M, Path(tmp)/'witness', 'full_witness', check, {})
            other.assert_not_called(); self.assertFalse((Path(tmp)/'witness').exists())

    def test_validator_disagreement_readdition_and_pin_change_rejected(self):
        n, A, S, F, R = fixture(); M = ((0, 2), (1, 0), (2, 1))
        second = m.frozen.verify_certificate_bruteforce
        def wrong(cert):
            result = second(cert); result['valid'] = False; return result
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen, 'verify_certificate_bruteforce', wrong):
            with self.assertRaises(RuntimeError):
                m.save_candidate(n, A, S, F, R, M, Path(tmp)/'witness', 'full_witness', lambda: None, {})
            self.assertFalse((Path(tmp)/'witness').exists())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                m.save_candidate(n, A, S, F, R, F, Path(tmp)/'witness', 'full_witness', lambda: None, {})
            pin = Path(tmp)/'pin'; pin.write_bytes(b'old'); pins = {str(pin): hashlib.sha256(pin.read_bytes()).hexdigest()}
            pin.write_bytes(b'new')
            with self.assertRaises(ValueError):
                m.save_candidate(n, A, S, F, R, M, Path(tmp)/'witness', 'full_witness', lambda: None, pins)

    def test_stubbed_run_shared_deadline_partials_and_final_identity(self):
        # run() is tested only with a tiny loader and width replacement; never n79.
        n, A, S, F, R = fixture()
        conflicts = [t for t in combinations(sorted(A), 3) if collinear(*t)]
        for fail in ('none', 'load', 'identity'):
            now = [0]
            def load(check, pins):
                if fail == 'load':
                    now[0] = 30; check()
                return A, S, conflicts, []
            def search(board, a, s, patch_cells, out, r, p, check, pins, cap):
                self.assertEqual(board, 79); self.assertEqual(cap, 0)
                p['status'] = 'insertion_cap'; raise m.InsertionCap
            def recheck(pins):
                if fail == 'identity':
                    raise ValueError('changed')
            with tempfile.TemporaryDirectory() as tmp, patch.object(m, 'WIDTH', 3), patch.object(m, 'load_sources', load), patch.object(m, 'search_patch', search), patch.object(m.frozen, 'verify_pins', recheck):
                r = m.run(Path(tmp), max_insertions=0, clock=lambda: now[0])
                self.assertEqual(r['status'], {'none': 'insertion_cap', 'load': 'timeout', 'identity': 'error'}[fail])
                self.assertFalse(r['complete']); self.assertFalse(r['closure'])
                self.assertEqual(r['source_validation_complete'], fail != 'load')
                self.assertEqual(r['identity_valid'], fail != 'identity')
                self.assertTrue((Path(tmp)/'report.json').exists())

    def test_invalid_duration_and_caps(self):
        for seconds, cap in ((0, 1000), (26, 1000), (True, 1000), (float('nan'), 1000), (25, -1), (25, 1001), (25, True)):
            with self.assertRaises(ValueError):
                m.run(Path('/unused'), seconds, cap)


if __name__ == '__main__':
    unittest.main()
