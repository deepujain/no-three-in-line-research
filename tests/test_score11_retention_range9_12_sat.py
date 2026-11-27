import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pysat.solvers import Solver
from pysat.formula import IDPool
from research import score11_retention_range9_12_sat as m
from research import score11_retention_range7_8_sat as prior


class Range912Tests(unittest.TestCase):
    def test_all_12_source_bits_enforce_range(self):
        pool=IDPool(start_from=13)
        clauses,upper,lower=m.range_encoding(range(1,13),9,12,pool)
        self.assertGreater(lower,0)
        with Solver(name='glucose3',bootstrap_with=clauses) as solver:
            for bits in itertools.product((False,True),repeat=12):
                assumptions=[i if bit else -i for i,bit in enumerate(bits,1)]
                deleted=sum(not bit for bit in bits)
                self.assertEqual(solver.solve(assumptions=assumptions),9<=deleted<=12)

    def test_14_source_bits_check_both_outside_boundaries(self):
        pool=IDPool(start_from=15)
        clauses,_,_=m.range_encoding(range(1,15),9,12,pool)
        with Solver(name='glucose3',bootstrap_with=clauses) as solver:
            for bits in itertools.product((False,True),repeat=14):
                assumptions=[i if bit else -i for i,bit in enumerate(bits,1)]
                deleted=sum(not bit for bit in bits)
                self.assertEqual(solver.solve(assumptions=assumptions),9<=deleted<=12)

    def test_range_decoder_rejects_outside_model_even_if_axis_valid(self):
        # A 3x3 target5 degree-valid selection with four retained source cells.
        source={(0,0),(1,0),(1,1),(2,1),(2,2),(0,2)}
        chosen={(0,0),(1,0),(1,1),(2,1),(2,2)}
        model=[i if ((i-1)%3,(i-1)//3) in chosen else -i for i in range(1,10)]
        self.assertEqual(m.range_model_points(model,3,5,source,1,1),chosen)
        with self.assertRaises(RuntimeError):m.range_model_points(model,3,5,source,2,3)

    def test_small_axis_models_obey_both_range_bounds(self):
        from collections import Counter
        n=5;source={(r,c) for r in range(n) for c in (r,(r+1)%n)}
        clauses,stats=m.build_range_formula(n,9,source,[],9,10)
        self.assertGreater(stats['initial_variable_count'],stats['axis_variable_top'])
        with Solver(name='glucose3',bootstrap_with=clauses) as solver:
            self.assertTrue(solver.solve())
            points=m.range_model_points(solver.get_model(),n,9,source,9,10)
            self.assertEqual(len(points),9)
            self.assertTrue(9<=len(source-points)<=10)
            self.assertTrue(all(v<=2 for v in Counter(x for x,y in points).values()))
            self.assertTrue(all(v<=2 for v in Counter(y for x,y in points).values()))

    def test_distinct_cli_scope_and_frozen_helper(self):
        sentinel=object()
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.frozen,'load_source',return_value=(set(),[])),patch.object(m,'normalized_sha256',return_value=m.frozen.SOURCE_NORMALIZED),patch.object(m,'search_range',return_value=sentinel) as search:
            self.assertIs(m.run(Path('unused'),Path(tmp),1),sentinel)
            self.assertEqual(search.call_args.args[0:6],(79,157,set(),[],9,12))
        self.assertIs(m.separate,m.frozen.separate)
        self.assertIsNot(m.search_range,prior.search_range)


if __name__=='__main__':unittest.main()
