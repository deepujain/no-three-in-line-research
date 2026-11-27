from collections import Counter
import importlib.util
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
if HAVE_PYSAT:
    from research import score11_hard_retention_sat as m
    from pysat.formula import IDPool


@unittest.skipUnless(HAVE_PYSAT, 'optional python-sat unavailable')
class RetentionSatTests(unittest.TestCase):
    @staticmethod
    def source(n):
        return {(x, x) for x in range(n)} | {(x, (x + 1) % n) for x in range(n)}

    def test_hard_retention_projection_with_both_axis_targets(self):
        for n in (2, 3):
            source = self.source(n)
            for target in (2 * n - 1, 2 * n):
                for bound in range(min(3, len(source)) + 1):
                    clauses, stats = m.build_formula(n, target, source, [], bound)
                    self.assertGreaterEqual(stats['initial_variable_count'], n * n)
                    with m.Solver(name='glucose3', bootstrap_with=clauses) as solver:
                        for mask in range(1 << (n * n)):
                            points = {((v - 1) % n, (v - 1) // n) for v in range(1, n * n + 1) if mask >> (v - 1) & 1}
                            expected = (len(points) == target and len(source - points) <= bound
                                        and all(v <= 2 for v in Counter(x for x, y in points).values())
                                        and all(v <= 2 for v in Counter(y for x, y in points).values()))
                            assignment = [v if mask >> (v - 1) & 1 else -v for v in range(1, n * n + 1)]
                            self.assertEqual(solver.solve(assumptions=assignment), expected)

    def test_retention_counter_projection_all_eight_source_literals(self):
        source_ids = [1, 2, 5, 7, 9, 11, 14, 16]
        for bound in range(9):
            pool = IDPool(start_from=17)
            clauses = m.retention_encoding(source_ids, bound, pool)
            self.assertTrue(all(abs(v) in source_ids or abs(v) > 16 for c in clauses for v in c))
            with m.Solver(name='glucose3', bootstrap_with=clauses) as solver:
                for mask in range(256):
                    assignment = [v if mask >> i & 1 else -v for i, v in enumerate(source_ids)]
                    self.assertEqual(solver.solve(assumptions=assignment), 8 - mask.bit_count() <= bound)

    def test_stream_matches_all_tiny_and_long_line_determinants(self):
        fixtures = [{(x, y) for x in range(4) for y in range(4)}, {(i, i) for i in range(13)}]
        for points in fixtures:
            expected = {frozenset((a, b, c)) for a, b, c in itertools.combinations(points, 3)
                        if (b[0] - a[0]) * (c[1] - a[1]) == (b[1] - a[1]) * (c[0] - a[0])}
            triples = list(m.conflict_stream(points))
            self.assertEqual(set(map(frozenset, triples)), expected)
            self.assertEqual(len(triples), len(expected))
        for remaining, batch, expected in ((20000, 256, 256), (7, 256, 7)):
            state = {'scan_complete': False, 'conflict_lower_bound': 0}
            emitted = []
            m.separate(fixtures[-1], emitted.append, state, math.inf, lambda: 0, remaining, batch)
            self.assertEqual(state, {'scan_complete': False, 'conflict_lower_bound': expected})
            self.assertEqual(len(emitted), expected)

    def test_incomplete_stream_and_partial_model_rejected(self):
        with self.assertRaises(TimeoutError):
            list(m.conflict_stream({(0, 0), (1, 1), (2, 2)}, 1, lambda: 1))
        with self.assertRaisesRegex(RuntimeError, 'partial real-cell model'):
            m.model_points([1, -2], 3, 5, self.source(3), 3)
        with self.assertRaisesRegex(RuntimeError, 'duplicate real-cell assignment'):
            m.model_points([1, -1], 3, 5, self.source(3), 3)

    def test_valid_geometry_outside_retention_is_hard_rejected(self):
        n = 3
        source = self.source(n)
        valid = next(set(p) for p in itertools.combinations(list(itertools.product(range(n), repeat=2)), 5)
                     if len(source - set(p)) > 1 and m.verify_certificate_bruteforce({'n': n, 'points': list(p)})['valid'])
        clauses, _ = m.build_formula(n, 5, source, [], 1)
        with m.Solver(name='glucose3', bootstrap_with=clauses) as solver:
            selected = {m._cell(n, *p) for p in valid}
            self.assertFalse(solver.solve(assumptions=[v if v in selected else -v for v in range(1, 10)]))

    def test_saved_invalid_exact_score_requires_both_audits(self):
        points = next(set(p) for p in itertools.combinations(list(itertools.product(range(3), repeat=2)), 5)
                      if m.verify_certificate_bruteforce({'n': 3, 'points': list(p)})['conflict_count'] == 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'best-invalid.json'
            digest = m.audit_and_save(points, 3, 5, self.source(3), 3, 1, path, {}, math.inf, lambda: 0)
            saved = json.loads(path.read_text())
            self.assertFalse(saved['metadata']['valid'])
            self.assertEqual(saved['metadata']['exact_conflict_count'], 1)
            self.assertEqual(saved['metadata']['normalized_sha256'], digest)
            wrong = m.verify_certificate_bruteforce({'n': 3, 'points': list(points)})
            wrong['conflict_count'] = 2
            with patch.object(m, 'verify_certificate_bruteforce', return_value=wrong):
                with self.assertRaisesRegex(RuntimeError, 'dual audit disagreement'):
                    m.audit_and_save(points, 3, 5, self.source(3), 3, 1, Path(directory) / 'bad.json', {}, math.inf, lambda: 0)
            self.assertFalse((Path(directory) / 'bad.json').exists())

    def test_real_tiny_search_dual_verified_witness_and_fresh_cut_artifact(self):
        source = self.source(3)
        conflicts = list(m.conflict_stream(source))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            report = m.search_local(3, 5, source, conflicts, 3, out, 2)
            self.assertEqual(report['status'], 'valid_witness')
            self.assertEqual(report['old_cuts_loaded'], 0)
            witness = json.loads(next(out.glob('witness-*.json')).read_text())
            self.assertTrue(m.verify_certificate_bruteforce(witness)['valid'])
            self.assertLessEqual(len(source - set(map(tuple, witness['points']))), 3)
            evidence = json.loads((out / 'new-geometry-cuts.json').read_text())
            self.assertFalse(evidence['resumption_supported'])
            self.assertEqual(len(evidence['new_cuts']), report['new_cuts'])
            self.assertEqual(evidence['initial_source_clause_count'], len(conflicts))

    def test_late_native_answer_is_unknown_and_timer_joins_before_delete(self):
        source = self.source(3)
        callbacks = []
        lifecycle = []
        timer = Mock()
        timer.join.side_effect = lambda: lifecycle.append('join')
        solver = Mock()
        solver.delete.side_effect = lambda: lifecycle.append('delete')

        def make_timer(remaining, callback):
            callbacks.append(callback)
            return timer

        def late_answer(**kwargs):
            callbacks[0]()
            return True

        solver.solve_limited.side_effect = late_answer
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'Solver', return_value=solver), patch.object(m.threading, 'Timer', side_effect=make_timer):
            report = m.search_local(3, 5, source, [], 3, Path(directory), 1, clock=lambda: 0)
        self.assertEqual(report['status'], 'timeout')
        self.assertEqual(report['candidate_models'], 0)
        solver.get_model.assert_not_called()
        self.assertEqual(lifecycle, ['join', 'delete'])

    def test_cut_limit_and_source_conflict_validation(self):
        source = self.source(3)
        with tempfile.TemporaryDirectory() as directory:
            report = m.search_local(3, 5, source, [], 3, Path(directory), 1, max_new_cuts=0)
        self.assertEqual(report['status'], 'cut_limit')
        self.assertEqual(report['candidate_models'], 0)
        self.assertIsNone(report['best_invalid_score'])
        self.assertEqual(report['source_reference_point_count'], 6)
        with self.assertRaisesRegex(ValueError, 'source conflict is not collinear'):
            m.build_formula(3, 5, source, [[(0, 0), (0, 1), (1, 1)]], 3)

    def test_valid_witness_persists_if_second_validator_finishes_after_soft_deadline(self):
        points = {(0, 1), (1, 0), (2, 0), (1, 2), (2, 2)}
        ticks = [0]
        original = m.verify_certificate_bruteforce

        def late_second(cert):
            result = original(cert)
            ticks[0] = 2
            return result

        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'verify_certificate_bruteforce', side_effect=late_second):
            path = Path(directory) / 'witness.json'
            m.audit_and_save(points, 3, 5, self.source(3), 3, 0, path, {}, 1, lambda: ticks[0])
            self.assertTrue(path.exists())
            self.assertTrue(json.loads(path.read_text())['metadata']['valid'])

    def test_real_native_interrupt_under_same_timer_lifecycle(self):
        pigeons, holes = 19, 18
        variable = lambda p, h: 1 + p * holes + h
        clauses = [[variable(p, h) for h in range(holes)] for p in range(pigeons)]
        clauses += [[-variable(p, h), -variable(q, h)]
                    for h in range(holes) for p, q in itertools.combinations(range(pigeons), 2)]
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'build_formula', return_value=(clauses, {})):
            report = m.search_local(3, 5, self.source(3), [], 3, Path(directory), 0.05)
        self.assertEqual(report['status'], 'timeout')
        self.assertTrue(report['timer_interrupt_fired'])
        self.assertEqual(report['candidate_models'], 0)


if __name__ == '__main__':
    unittest.main()
