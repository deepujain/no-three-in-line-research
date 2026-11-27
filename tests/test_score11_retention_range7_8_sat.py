from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
if HAVE_PYSAT:
    from research import score11_retention_range7_8_sat as m
    from pysat.formula import IDPool


@unittest.skipUnless(HAVE_PYSAT, 'optional python-sat unavailable')
class RetentionRangeTests(unittest.TestCase):
    @staticmethod
    def source(n):
        return {(x, x) for x in range(n)} | {(x, (x + 1) % n) for x in range(n)}

    @staticmethod
    def assignment(n, points):
        selected = {m.frozen._cell(n, *p) for p in points}
        return [v if v in selected else -v for v in range(1, n * n + 1)]

    def test_range7_8_and_smaller_ranges_exhaust_source_literal_projection(self):
        for count, ranges in ((8, ((7, 8), (0, 0), (2, 5), (8, 8))), (10, ((7, 8),))):
            ids = list(range(1, count + 1))
            for lower, upper in ranges:
                pool = IDPool(start_from=count + 1)
                clauses, upper_count, lower_count = m.range_encoding(ids, lower, upper, pool)
                self.assertEqual(len(clauses), upper_count + lower_count)
                with m.Solver(name='glucose3', bootstrap_with=clauses) as solver:
                    for mask in range(1 << count):
                        chosen = [v if mask >> (v - 1) & 1 else -v for v in ids]
                        self.assertEqual(solver.solve(assumptions=chosen), lower <= count - mask.bit_count() <= upper)

    def test_full_n4_target7_axis_and_intrinsic_range_projection(self):
        n = 4
        source = self.source(n)
        clauses, stats = m.build_range_formula(n, 7, source, [], 7, 8)
        self.assertGreater(stats['initial_retention_lower_clauses'], 0)
        self.assertTrue(all(abs(v) <= stats['initial_variable_count'] for c in clauses for v in c))
        saw = Counter()
        with m.Solver(name='glucose3', bootstrap_with=clauses) as solver:
            for mask in range(1 << 16):
                points = {((v - 1) % n, (v - 1) // n) for v in range(1, 17) if mask >> (v - 1) & 1}
                deleted = len(source - points)
                expected = (len(points) == 7 and 7 <= deleted <= 8
                            and all(v <= 2 for v in Counter(x for x, y in points).values())
                            and all(v <= 2 for v in Counter(y for x, y in points).values()))
                self.assertEqual(solver.solve(assumptions=self.assignment(n, points)), expected)
                if expected:
                    saw[deleted] += 1
        self.assertGreater(saw[7], 0)
        self.assertGreater(saw[8], 0)

    def test_decoder_independently_rejects_d6_and_d10_and_accepts_d7_d8(self):
        n = 4
        source = self.source(n)
        opposite = {(x, (x + shift) % n) for x in range(n) for shift in (2, 3)}
        exchanged = (opposite - {(0, 2), (2, 0)}) | {(0, 0), (2, 2)}
        d6 = exchanged - {(1, 3)}
        self.assertEqual(len(source - d6), 6)
        self.assertEqual(m.frozen.model_points(self.assignment(n, d6), n, 7, source, 8), d6)
        with self.assertRaisesRegex(RuntimeError, 'intrinsic deletion lower bound'):
            m.range_model_points(self.assignment(n, d6), n, 7, source, 7, 8)
        for points in (exchanged - {(0, 0)}, opposite - {(0, 2)}):
            self.assertEqual(m.range_model_points(self.assignment(n, points), n, 7, source, 7, 8), points)
        n = 5
        source = self.source(n)
        d10 = {(x, (x + shift) % n) for x in range(n) for shift in (2, 3)} - {(0, 2)}
        self.assertEqual(len(source - d10), 10)
        with self.assertRaisesRegex(RuntimeError, 'hard retention'):
            m.range_model_points(self.assignment(n, d10), n, 9, source, 7, 8)

    def test_range_saved_candidate_lower_bound_rechecked(self):
        source = self.source(4)
        points = source - {(0, 0)}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.json'
            with self.assertRaisesRegex(RuntimeError, 'intrinsic deletion range'):
                m.audit_range_and_save(points, 4, 7, source, 7, 8, 1, path, {}, 1, lambda: 0)
            self.assertFalse(path.exists())

    def test_exact_counter_arithmetic_on_interior_tiny_bounds(self):
        for count, lower, upper in ((10, 3, 4), (12, 4, 5), (16, 7, 8)):
            pool = IDPool(start_from=count + 1)
            clauses, upper_count, lower_count = m.range_encoding(range(1, count + 1), lower, upper, pool)
            k = count - lower
            self.assertEqual(pool.top, count + upper * (count - upper) + k * (count - k))
            self.assertEqual(upper_count, 2 * upper * (count - upper) + count - 2 * upper)
            self.assertEqual(lower_count, 2 * k * (count - k) + count - 2 * k)
        self.assertEqual(hashlib.sha256(Path(m.frozen.__file__).read_bytes()).hexdigest(), m.FROZEN_KERNEL_SHA)

    def test_real_tiny_search_has_intrinsic_range_metadata_and_fresh_cuts(self):
        source = self.source(3)
        conflicts = list(m.frozen.conflict_stream(source))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            report = m.search_range(3, 5, source, conflicts, 2, 3, out, 2)
            self.assertEqual(report['status'], 'valid_witness')
            self.assertEqual(report['min_effective_source_deletions'], 2)
            self.assertEqual(report['max_effective_source_deletions'], 3)
            self.assertEqual(report['old_cuts_loaded'], 0)
            witness = json.loads(next(out.glob('witness-*.json')).read_text())
            self.assertTrue(m.frozen.verify_certificate_bruteforce(witness)['valid'])
            self.assertTrue(2 <= len(source - set(map(tuple, witness['points']))) <= 3)
            self.assertEqual(witness['metadata']['min_effective_source_deletions'], 2)

    def test_late_native_answer_cleanup_stays_in_new_adapter(self):
        callbacks, lifecycle = [], []
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
        original_timer = m.frozen.threading.Timer
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'Solver', return_value=solver), patch.object(m, 'Timer', side_effect=make_timer):
            report = m.search_range(3, 5, self.source(3), [], 2, 3, Path(directory), 1, clock=lambda: 0)
        self.assertEqual(report['status'], 'timeout')
        solver.get_model.assert_not_called()
        self.assertEqual(lifecycle, ['join', 'delete'])
        self.assertIs(m.frozen.threading.Timer, original_timer)

    def test_real_native_interrupt_and_invalid_range(self):
        pigeons, holes = 19, 18
        variable = lambda p, h: 1 + p * holes + h
        clauses = [[variable(p, h) for h in range(holes)] for p in range(pigeons)]
        clauses += [[-variable(p, h), -variable(q, h)]
                    for h in range(holes) for p, q in itertools.combinations(range(pigeons), 2)]
        with tempfile.TemporaryDirectory() as directory, patch.object(m, 'build_range_formula', return_value=(clauses, {})):
            report = m.search_range(3, 5, self.source(3), [], 2, 3, Path(directory), 0.05)
        self.assertEqual(report['status'], 'timeout')
        self.assertTrue(report['timer_interrupt_fired'])
        for lower, upper in ((8, 7), (-1, 8), (0, 11)):
            with self.assertRaises(ValueError):
                m.range_encoding(range(1, 11), lower, upper, IDPool(start_from=11))


if __name__ == '__main__':
    unittest.main()
