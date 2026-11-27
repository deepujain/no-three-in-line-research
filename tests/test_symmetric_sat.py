import importlib.util
import itertools
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
HAVE_PYSAT = importlib.util.find_spec('pysat') is not None


@unittest.skipUnless(HAVE_PYSAT,'optional python-sat is not installed')
class SymmetricSatTests(unittest.TestCase):
    def test_existing_entrypoint_delegates_without_changing_default(self):
        source = Path(__file__).resolve().parents[1]/'src/lazy_sat.py'
        for flag,target,family in [('diagonal',5,'main_diagonal_reflection'),
                                   ('halfturn',6,'half_turn_rotation')]:
            result = subprocess.run([sys.executable,str(source),'--n','3','--seconds','1',
                                     '--symmetry',flag],capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0,result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['status'],'valid_witness')
            self.assertEqual(report['target'],target)
            self.assertEqual(report['scope']['family'],family)
            self.assertGreaterEqual(report['wrapper_elapsed_seconds'],report['symmetry_compile_seconds'])
    def test_every_small_assignment_matches_exact_restricted_geometry(self):
        from lazy_sat import axis_encoding
        from symmetric_sat import symmetry_encoding
        from pysat.solvers import Solver
        from verify import verify_certificate_bruteforce
        for n in range(2,5):
            grid = [(x,y) for y in range(n) for x in range(n)]
            geometry = []
            for a,b,c in itertools.combinations(range(n*n),3):
                ax,ay = grid[a];bx,by = grid[b];cx,cy = grid[c]
                if (bx-ax)*(cy-ay)==(by-ay)*(cx-ax):
                    geometry.append([-(a+1),-(b+1),-(c+1)])
            for symmetry in ('diagonal','half-turn'):
                target,extra,scope = symmetry_encoding(n,symmetry)
                axes,_,_ = axis_encoding(n,target)
                with Solver(name='glucose3',bootstrap_with=axes+extra+geometry) as solver:
                    for mask in range(1 << (n*n)):
                        selected = {grid[i] for i in range(n*n) if mask & (1<<i)}
                        image = {(y,x) for x,y in selected} if symmetry=='diagonal' else {(n-1-x,n-1-y) for x,y in selected}
                        expected = (len(selected)==target and selected==image
                                    and verify_certificate_bruteforce({'n':n,'points':sorted(selected)})['valid'])
                        assumptions = [i+1 if mask & (1<<i) else -(i+1) for i in range(n*n)]
                        self.assertEqual(solver.solve(assumptions=assumptions),expected,(n,symmetry,mask))
                self.assertTrue(scope['restricted'])
                self.assertTrue(all(type(v) is int and 1 <= abs(v) <= n*n for clause in extra for v in clause))

    def test_diagonal_point_and_deficit_index_are_not_forced_equal_or_different(self):
        from lazy_sat import axis_encoding
        from symmetric_sat import symmetry_encoding
        from pysat.solvers import Solver
        from verify import verify_certificate_bruteforce
        examples = [(3,[(0,0),(0,1),(1,0),(1,2),(2,1)]),
                    (4,[(0,1),(1,0),(0,2),(2,0),(1,2),(2,1),(3,3)])]
        for n,points in examples:
            self.assertTrue(verify_certificate_bruteforce({'n':n,'points':points})['valid'])
            target,extra,_ = symmetry_encoding(n,'diagonal')
            axes,_,_ = axis_encoding(n,target)
            true_ids = {y*n+x+1 for x,y in points}
            with Solver(name='glucose3',bootstrap_with=axes+extra) as solver:
                self.assertTrue(solver.solve(assumptions=[v if v in true_ids else -v for v in range(1,n*n+1)]))

    def test_tiny_witnesses_are_symmetric_and_double_verified(self):
        from symmetric_sat import search
        from verify import verify_certificate,verify_certificate_bruteforce
        for n in (2,3,4):
            for symmetry in ('diagonal','half-turn'):
                report = search(n,1,symmetry,all_line_constraints=True)
                self.assertEqual(report['status'],'valid_witness',report)
                certificate = report['witness']
                self.assertTrue(verify_certificate(certificate)['valid'])
                self.assertTrue(verify_certificate_bruteforce(certificate)['valid'])
                points = set(map(tuple,certificate['points']))
                transformed = {(y,x) for x,y in points} if symmetry=='diagonal' else {(n-1-x,n-1-y) for x,y in points}
                self.assertEqual(points,transformed)
                self.assertEqual(len(points),2*n-1 if symmetry=='diagonal' else 2*n)
                self.assertGreater(report['memory_telemetry']['peak_process_rss_bytes'],0)

    def test_scoped_clauses_never_enter_reusable_geometry_checkpoint(self):
        from lazy_sat import search as unrestricted
        from symmetric_sat import search
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)/'geometry.jsonl'
            checkpoint.write_text(json.dumps({'format':'no3-geometry-cuts-v1','n':3})+'\n'+json.dumps([1,5,9])+'\n')
            first = search(3,1,'diagonal',checkpoint=checkpoint)
            second = search(3,1,'half-turn',checkpoint=checkpoint)
            third = unrestricted(3,1,target=6,checkpoint=checkpoint)
            self.assertEqual(first['status'],'valid_witness')
            self.assertEqual(second['status'],'valid_witness')
            self.assertEqual(third['status'],'valid_witness')
            self.assertNotEqual(first['scope']['family'],second['scope']['family'])
            self.assertEqual(third['scope']['family'],'unrestricted')
            for line in checkpoint.read_text().splitlines()[1:]:
                ids = json.loads(line)
                self.assertEqual(len(ids),3)
                self.assertTrue(all(type(v) is int and 1 <= v <= 9 for v in ids))
                a,b,c = [((v-1)%3,(v-1)//3) for v in ids]
                self.assertEqual((b[0]-a[0])*(c[1]-a[1]),(b[1]-a[1])*(c[0]-a[0]))

    def test_unsat_scope_is_explicit_and_hook_rejects_auxiliary_literals(self):
        from lazy_sat import search
        report = search(2,1,extra_clauses=[[]],scope={'family':'contradictory_test_family'})
        self.assertEqual(report['status'],'unsat_solver_reported')
        self.assertEqual(report['scope']['family'],'contradictory_test_family')
        self.assertIn('only to the reported scope',report['note'])
        with self.assertRaises(ValueError):
            search(2,1,extra_clauses=[])
        for clause in ([5],[-5],[0],[True]):
            with self.assertRaises(ValueError):
                search(2,1,extra_clauses=[clause],scope={'family':'test'})

    def test_invalid_families_and_targets(self):
        from symmetric_sat import symmetry_encoding,search
        with self.assertRaises(ValueError):
            symmetry_encoding(3,'quarter-turn')
        with self.assertRaises(ValueError):
            search(3,1,'diagonal',target=6)
        with self.assertRaises(ValueError):
            search(3,1,'half-turn',target=5)


if __name__=='__main__':
    unittest.main()
