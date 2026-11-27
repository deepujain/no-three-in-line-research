import importlib.util
import itertools
from pathlib import Path
import sys
import threading
import tempfile
import json
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
HAVE_PYSAT = importlib.util.find_spec('pysat') is not None


@unittest.skipUnless(HAVE_PYSAT, 'optional python-sat is not installed')
class LazySatTest(unittest.TestCase):
    def test_axis_encoding_matches_all_small_cell_assignments(self):
        from lazy_sat import axis_encoding
        from pysat.solvers import Solver
        for n in range(2,5):
            rows = [sum(1 << (y*n+x) for x in range(n)) for y in range(n)]
            columns = [sum(1 << (y*n+x) for y in range(n)) for x in range(n)]
            for target in (2*n, 2*n-1):
                clauses,pool,deficits = axis_encoding(n,target)
                self.assertTrue(all(v > n*n for family in deficits.values() for v in family))
                self.assertEqual(len(set(v for family in deficits.values() for v in family)),
                                 0 if target == 2*n else 2*n)
                with Solver(name='glucose3',bootstrap_with=clauses) as solver:
                    for mask in range(1 << (n*n)):
                        expected = mask.bit_count() == target and all((mask & axis).bit_count() <= 2 for axis in rows+columns)
                        assignment = [i+1 if mask & (1<<i) else -(i+1) for i in range(n*n)]
                        self.assertEqual(solver.solve(assumptions=assignment),expected,(n,target,mask))

    def test_deficit_intersection_may_be_occupied(self):
        from lazy_sat import axis_encoding, _cell
        from pysat.solvers import Solver
        from verify import verify_certificate, verify_certificate_bruteforce
        points = [(0,1),(1,0),(2,0),(1,2),(2,2)]
        certificate = {'n':3,'points':points}
        self.assertTrue(verify_certificate(certificate)['valid'])
        self.assertTrue(verify_certificate_bruteforce(certificate)['valid'])
        clauses,_,deficits = axis_encoding(3,5)
        selected = {_cell(3,*point) for point in points}
        with Solver(name='glucose3',bootstrap_with=clauses) as solver:
            self.assertTrue(solver.solve(assumptions=[v if v in selected else -v for v in range(1,10)]))
            model = set(v for v in solver.get_model() if v>0)
            self.assertEqual([i for i,v in enumerate(deficits['row']) if v in model],[1])
            self.assertEqual([i for i,v in enumerate(deficits['column']) if v in model],[0])
            self.assertIn(_cell(3,0,1),model)

    def test_deficient_witness_and_shared_geometry_checkpoint(self):
        from lazy_sat import search
        from verify import verify_certificate, verify_certificate_bruteforce
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)/'shared-real-geometry.jsonl'
            checkpoint.write_text(json.dumps({'format':'no3-geometry-cuts-v1','n':3})+'\n'+json.dumps([1,5,9])+'\n')
            for target in (5,6,5):
                report = search(3,1,target=target,checkpoint=checkpoint)
                self.assertEqual(report['status'],'valid_witness',report)
                self.assertEqual(report['target'],target)
                self.assertEqual(len(report['witness']['points']),target)
                self.assertGreaterEqual(report['checkpoint_cuts_loaded'],1)
                self.assertTrue(verify_certificate(report['witness'])['valid'])
                self.assertTrue(verify_certificate_bruteforce(report['witness'])['valid'])
            for line in checkpoint.read_text().splitlines()[1:]:
                self.assertTrue(all(1 <= v <= 9 for v in json.loads(line)))
            self.assertNotIn('target',json.loads(checkpoint.read_text().splitlines()[0]))
        for target in (None,):
            self.assertEqual(search(2,1,target=target)['target'],4)

    def test_invalid_targets_are_rejected(self):
        from lazy_sat import search,axis_encoding
        for target in (0,4,7,True,5.0,'5'):
            with self.assertRaises(ValueError):
                axis_encoding(3,target)
            with self.assertRaises(ValueError):
                search(3,1,target=target)
    def test_full_and_lazy_small_existence(self):
        from lazy_sat import search
        from verify import verify_certificate_bruteforce
        for n in range(2, 5):
            cells = [(x,y) for y in range(n) for x in range(n)]
            expected = any(verify_certificate_bruteforce({'n': n, 'points': list(points)})['valid']
                           for points in itertools.combinations(cells, 2*n))
            self.assertTrue(expected)
            for full in (False, True):
                report = search(n, 5, all_line_constraints=full)
                self.assertEqual(report['status'], 'valid_witness', (n,full,report))
                self.assertEqual(len(report['witness']['points']), 2*n)
                self.assertTrue(verify_certificate_bruteforce(report['witness'])['valid'])

    def test_checkpoint_resume_and_reject_invalid_geometry(self):
        from lazy_sat import search
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / 'cuts.jsonl'
            progress = Path(tmp) / 'progress.jsonl'
            first = search(10, 5, checkpoint=checkpoint, progress=progress, max_cuts=20)
            self.assertEqual(first['status'], 'cut_limit')
            self.assertEqual(first['lazy_cuts_added'], 20)
            resumed = search(10, 5, checkpoint=checkpoint, progress=progress)
            self.assertEqual(resumed['checkpoint_cuts_loaded'], 20)
            self.assertEqual(resumed['status'], 'valid_witness')
            self.assertGreaterEqual(len(progress.read_text().splitlines()), 2)
            header = json.dumps({'format':'no3-geometry-cuts-v1','n':3})
            checkpoint.write_text(header+'\n'+json.dumps([1,2,4])+'\n')
            with self.assertRaisesRegex(ValueError, 'not collinear'):
                search(3, 5, checkpoint=checkpoint)
            checkpoint.write_text(header+'\n'+json.dumps([1,2,100])+'\n')
            with self.assertRaisesRegex(ValueError, 'invalid checkpoint'):
                search(3, 5, checkpoint=checkpoint)
            with self.assertRaisesRegex(ValueError, 'grid mismatch'):
                search(4, 5, checkpoint=checkpoint)

    def test_interrupt_real_native_solve(self):
        from pysat.solvers import Solver
        pigeons, holes = 19,18
        def v(i,j): return i*holes+j+1
        clauses = [[v(i,j) for j in range(holes)] for i in range(pigeons)]
        clauses.extend([[-v(i,j),-v(k,j)] for j in range(holes)
                        for i in range(pigeons) for k in range(i+1,pigeons)])
        fired = threading.Event()
        with Solver(name='glucose3', bootstrap_with=clauses) as solver:
            def interrupt():
                fired.set()
                solver.interrupt()
            timer = threading.Timer(0.05, interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
                timer.join()
            self.assertTrue(fired.is_set(), 'native solver unexpectedly finished before interrupt')
            self.assertIsNone(answer)

if __name__ == '__main__':
    unittest.main()
