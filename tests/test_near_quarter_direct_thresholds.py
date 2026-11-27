"""Exact tiny projection checks; no large geometry or native resource trial."""
from dataclasses import FrozenInstanceError
import importlib.util
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.near_quarter_direct_thresholds import (
    CapacityThresholds, shared_capacity_clauses, streamed_cnf, threshold_counts, model_header)
from src.near_quarter_compact import shared_capacity_clauses as baseline_capacity
from src.near_quarter_row_quota import streamed_cnf as baseline_cnf
from src.near_quarter_model import orbit_map,expand
from src.verify import collinear_triples_bruteforce

HAVE_PYSAT = importlib.util.find_spec('pysat') is not None


class DirectThresholdTests(unittest.TestCase):
    def test_threshold_configuration_is_explicit_bounded_and_immutable(self):
        for first,second in ((-1,5),(5,8),(True,5),(5,6.0)):
            with self.assertRaises(ValueError):
                CapacityThresholds(first,second)
        with self.assertRaises(FrozenInstanceError):
            CapacityThresholds().atmost_two = 5
        metadata = threshold_counts(orbit_map(3),CapacityThresholds(6,7))
        self.assertEqual(metadata['capacity_thresholds'],{'atmost_two':6,'conditional_atmost_one':7})
        self.assertEqual(metadata['baseline_direct_light_limit'],5)
        self.assertNotIn('direct_light_limit',metadata)
        self.assertEqual(len(metadata['threshold_source_sha256']),64)
        self.assertNotEqual(model_header(orbit_map(3),CapacityThresholds(5,5)),
                            model_header(orbit_map(3),CapacityThresholds(7,7)))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_threshold_five_reproduces_baseline_exact_clause_stream_and_ids(self):
        from pysat.formula import IDPool
        for light in range(10):
            for guard_count in (0,1,2):
                weights = [(1,3),(2,2)]+[(v,1) for v in range(3,3+light)]
                guards = tuple(range(3+light,3+light+guard_count))
                total = len(weights)+guard_count
                old = list(baseline_capacity(weights,guards,IDPool(start_from=total+1)))
                new = list(shared_capacity_clauses(weights,guards,IDPool(start_from=total+1),CapacityThresholds(5,5)))
                self.assertEqual(new,old,(light,guard_count))
        for n in (3,5,7):
            model = orbit_map(n)
            self.assertEqual(list(streamed_cnf(model,CapacityThresholds(5,5))),list(baseline_cnf(model)))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_exhaustive_synthetic_light_supports_through_eight_all_threshold_pairs(self):
        from pysat.formula import IDPool
        from pysat.solvers import Solver
        settings = [CapacityThresholds(a,b) for a,b in product((5,6,7),repeat=2)]
        # Include lower thresholds to verify trivial supports and retained
        # sequential branches independently of the proposed 5/6/7 cutoffs.
        settings += [CapacityThresholds(0,0),CapacityThresholds(2,2)]
        for light in range(9):
            for guard_count in (0,1,2):
                total = light+guard_count
                weights = [(v,1) for v in range(1,light+1)]
                guards = tuple(range(light+1,total+1))
                for config in settings:
                    with Solver(name='glucose3',bootstrap_with=shared_capacity_clauses(
                            weights,guards,IDPool(start_from=total+1),config)) as solver:
                        for bits in product((False,True),repeat=total):
                            value = sum(bits[:light])
                            expected = value <= 2 and (not any(bits[light:]) or value <= 1)
                            fixed = [v if b else -v for v,b in enumerate(bits,1)]
                            self.assertIs(solver.solve(assumptions=fixed),expected,
                                          (light,guard_count,config,bits))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_mixed_heavy_and_forced_false_weights_all_tiny_assignments(self):
        from pysat.formula import IDPool
        from pysat.solvers import Solver
        for coefficients in ((2,), (3,), (2,2), (3,2,1), (2,)+6*(1,), (3,2)+7*(1,)):
            count = len(coefficients)
            for guard_count in (0,1,2):
                total = count+guard_count
                guards = tuple(range(count+1,total+1))
                for config in (CapacityThresholds(5,5),CapacityThresholds(6,7),CapacityThresholds(7,6),CapacityThresholds(7,7)):
                    with Solver(name='glucose3',bootstrap_with=shared_capacity_clauses(
                            enumerate(coefficients,1),guards,IDPool(start_from=total+1),config)) as solver:
                        for bits in product((False,True),repeat=total):
                            value = sum(w for w,b in zip(coefficients,bits) if b)
                            expected = value <= 2 and (not any(bits[count:]) or value <= 1)
                            fixed = [v if b else -v for v,b in enumerate(bits,1)]
                            self.assertIs(solver.solve(assumptions=fixed),expected,
                                          (coefficients,guard_count,config,bits))

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_complete_n3_n5_n7_all_assignments_project_to_same_exact_geometry(self):
        from pysat.solvers import Solver
        for n in (3,5,7):
            model = orbit_map(n)
            configs = [CapacityThresholds(a,b) for a,b in product((5,6,7),repeat=2)]
            solvers = [Solver(name='glucose3',bootstrap_with=streamed_cnf(model,c)) for c in configs]
            baseline = Solver(name='glucose3',bootstrap_with=baseline_cnf(model))
            try:
                for bits in product((False,True),repeat=len(model['orbits'])):
                    selected = {v for v,b in enumerate(bits,1) if b}
                    diagonal = sum(v > model['four_count'] for v in selected)
                    expected = (diagonal == 1 and len(selected)-diagonal == n//2 and
                                not collinear_triples_bruteforce(expand(model,selected)))
                    fixed = [v if b else -v for v,b in enumerate(bits,1)]
                    self.assertIs(baseline.solve(assumptions=fixed),expected)
                    for config,solver in zip(configs,solvers):
                        self.assertIs(solver.solve(assumptions=fixed),expected,(n,config,bits))
            finally:
                baseline.delete()
                for solver in solvers:
                    solver.delete()

    @unittest.skipUnless(HAVE_PYSAT,'optional python-sat not installed')
    def test_invalid_weights_guards_and_configuration_are_rejected(self):
        from pysat.formula import IDPool
        for weights,guards in (([(1,1),(1,2)],()), ([(0,1)],()), ([(1,0)],()),
                               ([(True,1)],()), ([(1,1)],(1,)), ([(1,1)],(False,))):
            with self.assertRaises(ValueError):
                list(shared_capacity_clauses(weights,guards,IDPool(start_from=10)))
        with self.assertRaises(ValueError):
            list(shared_capacity_clauses([],[],IDPool(),None))


if __name__ == '__main__':
    unittest.main()
