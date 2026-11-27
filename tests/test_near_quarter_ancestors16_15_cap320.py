from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from research import near_quarter_ancestors16_15_cap320 as m
from research import near_quarter_ancestor_pair_sat as ancestor
from research import near_quarter_prefix_pair_sat as kernel


class Capacity320Tests(unittest.TestCase):
    def test_fixed_prefix_counts_cap_and_frozen_function_reuse(self):
        self.assertEqual(m.DEPTHS, (16, 15))
        self.assertEqual([len(m.prefix_for_depth(m.EXPECTED_IDS, d)) for d in m.DEPTHS], [17, 16])
        self.assertEqual([2 + 4 * d for d in m.DEPTHS], [66, 62])
        self.assertEqual([39 - d for d in m.DEPTHS], [23, 24])
        self.assertIs(m.solve_models, ancestor.solve_models)
        self.assertIs(m.adaptive_loop, ancestor.adaptive_loop)
        self.assertIs(m.incompatible_pairs, kernel.incompatible_pairs)
        self.assertEqual(len(m.bounded_variables([1] * 320 + [0] * 5)), 320)
        self.assertIsNone(m.bounded_variables([1] * 321))
        for invalid in ([True], [2], [-1]):
            with self.assertRaises(ValueError):
                m.bounded_variables(invalid)
        with self.assertRaises(ValueError):
            m.prefix_for_depth(m.EXPECTED_IDS, 14)

    def test_exact_dynamic_capacity_and_degree_formula_bounds(self):
        bounds = m.capacity_bounds(320)
        self.assertEqual((bounds['pair_census'], bounds['first_orbit_pushes']), (51040, 319))
        self.assertEqual((bounds['degree_variables'], bounds['degree_clauses'], bounds['degree_literals']), (2880, 5120, 15360))
        self.assertEqual((bounds['final_clauses'], bounds['final_literals']), (57160, 120440))
        self.assertEqual(m.capacity_bounds(224)['pair_census'], 24976)
        demands, edges = [2, 2, 2], [(0, 1), (1, 2), (0, 2)]
        clauses, pool = m.degree_clauses(demands, edges, lambda: None)
        self.assertEqual(m.validate_formula(demands, edges, 3, clauses, pool), sum(map(len, clauses)))
        with self.assertRaisesRegex(ValueError, 'dynamic bound'):
            m.validate_formula(demands, edges, 3, [], SimpleNamespace(top=28))
        with self.assertRaisesRegex(ValueError, 'dynamic bound'):
            m.validate_formula(demands, edges, 3, [[]] * 49, SimpleNamespace(top=3))
        with self.assertRaisesRegex(ValueError, 'dynamic bound'):
            m.validate_formula(demands, edges, 3, [[1] * 145], SimpleNamespace(top=3))
        for bad_demands, bad_edges in (([3, 0, 0], edges), (demands, [(0, 0)] * 3)):
            with self.assertRaisesRegex(ValueError, 'radius incidence'):
                m.validate_formula(bad_demands, bad_edges, 3, clauses, pool)

    @contextmanager
    def fake_run(self, *, second_status='unsat_solver_reported', incomplete_pairs=False,
                 oversized_second=False, timeout_second=False, bad_formula=False):
        tick = [0]
        events, states, targets, deadlines = [], [], [], []

        class State:
            def __init__(self, n, check):
                self.ids = []
                states.append(self)

            def push(self, variable):
                self.ids.append(variable)
                return True

            @property
            def points(self):
                return tuple((i, 0) for i in range(2 + 4 * (len(self.ids) - 1)))

        class Solver:
            def __init__(self, **kwargs):
                events.append('solver')

            def add_clause(self, clause):
                pass

            def delete(self):
                events.append('delete')

            def interrupt(self):
                events.append('interrupt')

        class Timer:
            def __init__(self, remaining, callback):
                events.append(('timer', remaining))

            def start(self):
                events.append('start')

            def cancel(self):
                events.append('cancel')

            def join(self):
                events.append('join')

        def sample(n, ids, check):
            depth = len(ids) - 1
            if timeout_second and depth == 15:
                raise TimeoutError
            count = 321 if oversized_second and depth == 15 else 24
            vertices = 39 - depth
            edges = [(i, (i + 1) % vertices) for i in range(vertices)]
            edges.extend([(0, 1)] * (count - len(edges)))
            return {'mask': [1] * count, 'mask_sha256': 'mask' + str(depth),
                    'demands': [2] * vertices, 'edges': edges}

        def pairs(state, variables, check, stage):
            events.append('pairs')
            count = len(variables) * (len(variables) - 1) // 2
            stage['pair_started'] = count
            stage['pair_completed'] = count - int(incomplete_pairs)
            return []

        def solve(solver, state, variables, demands, edges, stage, check, fired, deadline, clock, out,
                  *, target_orbits, cut_limit):
            targets.append(target_orbits)
            deadlines.append(deadline)
            self.assertEqual(cut_limit, 1000)
            stage['status'] = 'unsat_solver_reported' if stage['depth'] == 16 else second_status
            stage['complete'] = stage['status'] in ('unsat_solver_reported', 'witness')
            stage['saved_evidence'] = stage['depth']
            tick[0] += 1

        with ExitStack() as stack:
            for name, value in (
                    ('PackedOrbitState', State), ('mask_and_bounds', sample),
                    ('incompatible_pairs', pairs), ('solve_models', solve), ('Timer', Timer),
                    ('source_manifest', lambda: {}),
                    ('prefix_paths', lambda check: ([('main', 19, m.EXPECTED_IDS)], [])),
                    ('load_parent_audit', lambda check: {'admissible_orbits': 24, 'independent_complete_mask_sha256': 'mask16'}),
                    ('degree_clauses', lambda demands, edges, check: ([], SimpleNamespace(top=3001 if bad_formula else len(edges))))):
                stack.enter_context(patch.object(m, name, value))
            stack.enter_context(patch('pysat.solvers.Solver', Solver))
            yield SimpleNamespace(tick=tick, events=events, states=states, targets=targets, deadlines=deadlines)

    def test_two_fresh_stages_targets_shared_deadline_cleanup(self):
        with self.fake_run() as fake, tempfile.TemporaryDirectory() as directory:
            report = m.run(Path(directory), 25, clock=lambda: fake.tick[0])
        self.assertEqual(fake.targets, [23, 24])
        self.assertEqual(fake.deadlines, [25, 25])
        self.assertEqual([event for event in fake.events if isinstance(event, tuple)], [('timer', 25), ('timer', 24)])
        self.assertEqual(len(fake.states), 2)
        self.assertNotEqual(id(fake.states[0]), id(fake.states[1]))
        self.assertEqual([event for event in fake.events if event in ('cancel', 'join', 'delete')], ['cancel', 'join', 'delete'] * 2)
        self.assertEqual(report['status'], 'all_ancestors_unsat_solver_reported')
        self.assertTrue(report['complete'])
        self.assertEqual([s['pair_completed'] for s in report['stages']], [276, 276])

    def test_incomplete_pairs_and_excess_degree_formula_block_solver(self):
        for settings, message in (({'incomplete_pairs': True}, 'pair census'), ({'bad_formula': True}, 'dynamic bound')):
            with self.fake_run(**settings) as fake, tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, message):
                    m.run(Path(directory), 25, clock=lambda: 0)
            self.assertNotIn('solver', fake.events)

    def test_later_mask_or_timeout_retains_completed_first_stage(self):
        for settings, expected in (({'oversized_second': True}, 'mask_capacity'), ({'timeout_second': True}, 'timeout')):
            with self.fake_run(**settings) as fake, tempfile.TemporaryDirectory() as directory:
                report = m.run(Path(directory), 25, clock=lambda: fake.tick[0])
            self.assertFalse(report['complete'])
            self.assertEqual(report['status'], expected)
            self.assertEqual(report['stages'][0]['status'], 'unsat_solver_reported')
            self.assertEqual(report['stages'][0]['saved_evidence'], 16)
            self.assertEqual(report['stages'][1]['status'], expected)
            self.assertEqual(fake.targets, [23])
            self.assertEqual(fake.events.count('solver'), 1)

    def test_unsat_only_advance_no_third_stage(self):
        for status in ('solver_unknown', 'timeout', 'cut_limit', 'mask_capacity', 'degree_shortfall', 'witness'):
            report = {'status': 'incomplete', 'complete': False,
                      'stages': [{'depth': d, 'status': 'unstarted'} for d in m.DEPTHS]}
            visited = []

            def stop(stage):
                visited.append(stage['depth'])
                stage['status'] = status

            m.adaptive_loop(report, stop)
            self.assertEqual(visited, [16])
            self.assertEqual(report['stages'][1]['status'], 'unstarted')
            self.assertEqual(report['status'], status)


if __name__ == '__main__':
    unittest.main()
