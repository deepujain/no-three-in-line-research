import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import neutral_repair as nr
from src.verify import verify_certificate, verify_certificate_bruteforce


class FixedRandom:
    def randint(self, a, b):
        self.bounds = (a, b)
        return b
    def sample(self, values, k):
        return list(values)[:k]
    def shuffle(self, values):
        pass
    def random(self):
        return 0.0


class NeutralRepairTests(unittest.TestCase):
    def test_neutral_move_preserves_best_and_counts_clipped_deletions(self):
        initial = {'n': 3, 'points': [[1, 0], [1, 1]]}
        ticks = [0]; rng = FixedRandom()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'best.json'
            with patch.object(nr, '_candidate_cost', side_effect=lambda pts, index, p: 0 if len(pts)<2 else 1):
                result = nr.walk(3, 1, 12, initial, output, rng=rng, clock=lambda:ticks[0],
                                 on_pass=lambda _:ticks.__setitem__(0, 2))
            best = json.loads(output.read_bytes())
        self.assertEqual(rng.bounds, (2, 2))
        self.assertEqual(result['deletion_histogram_completed'], {2:1})
        self.assertEqual(result['counts']['neutral_accepted'], 1)
        self.assertNotEqual(result['walk_normalized_sha256'], result['best_normalized_sha256'])
        self.assertEqual(best['points'], initial['points'])
        self.assertTrue(verify_certificate(best)['valid'])
        self.assertTrue(verify_certificate_bruteforce(best)['valid'])

    def test_improvement_is_published_immediately_before_pass_callback(self):
        initial = {'n':2, 'points':[[0,0],[0,1],[1,0]]}
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'best.json'; seen=[]
            def after_pass(event):
                cert=json.loads(output.read_bytes());seen.append(len(cert['points']))
            result=nr.walk(2, 10, 1, initial, output, rng=FixedRandom(), on_pass=after_pass)
            cert=json.loads(output.read_bytes())
        self.assertEqual(result['best_count'],4)
        self.assertEqual(seen,[4])
        self.assertEqual(result['stopping_reason'],'target_reached')
        self.assertTrue(verify_certificate(cert)['valid'])
        self.assertTrue(verify_certificate_bruteforce(cert)['valid'])

    def test_interrupted_pass_is_not_accepted(self):
        initial={'n':3,'points':[[0,0],[0,1]]}; calls=[0]
        def clock():
            calls[0]+=1
            return 0 if calls[0] <= 3 else 2
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'best.json'
            result=nr.walk(3,1,7,initial,output,rng=FixedRandom(),clock=clock)
            best=json.loads(output.read_bytes())
        self.assertEqual(result['counts']['partial'],1)
        self.assertNotIn('neutral_accepted',result['counts'])
        self.assertEqual(best['points'],initial['points'])

    def test_invalid_initial_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'out'
            for initial in ({'n':3,'points':[[0,0],[0,0]]}, {'n':3,'points':[[0,0],[1,1],[2,2]]}):
                with self.assertRaises(ValueError):nr.walk(3,1,1,initial,path)
            with self.assertRaises(ValueError):nr.walk(3,1,1,{'n':3,'points':[]},path,history_limit=0)
            with self.assertRaises(ValueError):nr.walk(3,1,1,{'n':3,'points':[]},path,max_drawdown=-1)

    def test_downward_transition_and_floor_rejection(self):
        initial = {'n': 3, 'points': [[1, 0], [1, 1]]}
        for floor, accepted in ((1, True), (0, False)):
            ticks = [0]
            with self.subTest(drawdown=floor), tempfile.TemporaryDirectory() as d:
                best = Path(d)/'best'; walk = Path(d)/'walk'
                with patch.object(nr, '_candidate_cost', side_effect=lambda pts, index, p: 0 if not pts else 1):
                    result = nr.walk(3, 1, 12, initial, best, walk_output=walk, max_drawdown=floor,
                                     rng=FixedRandom(), clock=lambda:ticks[0],
                                     on_pass=lambda _:ticks.__setitem__(0, 2))
                self.assertEqual(len(json.loads(best.read_bytes())['points']), 2)
                self.assertEqual(len(json.loads(walk.read_bytes())['points']), 1 if accepted else 2)
                self.assertEqual(result['trial_size_histogram'], {1: 1})
                if accepted:
                    self.assertEqual(result['accepted_delta_histogram'], {-1: 1})
                    self.assertEqual(result['minimum_walk_size'], 1)
                else:
                    self.assertEqual(result['counts']['below_floor'], 1)

    def test_partial_improvement_promotes_walk(self):
        initial = {'n': 3, 'points': [[1, 1]]}; calls = [0]
        def clock():
            calls[0] += 1
            return 0 if calls[0] <= 4 else 2
        with tempfile.TemporaryDirectory() as d:
            best = Path(d)/'best'; walk = Path(d)/'walk'
            result = nr.walk(3, 1, 1, initial, best, walk_output=walk,
                             max_drawdown=1, rng=FixedRandom(), clock=clock)
            self.assertEqual(result['counts']['partial'], 1)
            self.assertEqual(result['counts']['improvement_promotions'], 1)
            self.assertEqual(json.loads(best.read_bytes())['points'], json.loads(walk.read_bytes())['points'])
            self.assertEqual(result['best_count'], 2)

    def test_upward_walk_and_bounded_cache_evictions(self):
        initial = {'n': 3, 'points': [[1, 0], [1, 1]]}; ticks = [0]; passes = [0]
        def after_pass(_):
            passes[0] += 1
            if passes[0] == 2:
                ticks[0] = 2
        with tempfile.TemporaryDirectory() as d:
            with patch.object(nr, '_candidate_cost',
                              side_effect=lambda pts, index, p: 0 if len(pts) < (1 if passes[0] == 0 else 2) else 1):
                result = nr.walk(3, 1, 12, initial, Path(d)/'best', max_drawdown=1,
                                 history_limit=1, rng=FixedRandom(), clock=lambda:ticks[0],
                                 on_pass=after_pass)
        self.assertEqual(result['accepted_delta_histogram'], {-1: 1, 1: 1})
        self.assertEqual(result['hash_cache_size'], 1)
        self.assertEqual(result['hash_cache_evictions'], 2)

    def test_separate_lower_walk_preserves_best_and_provenance(self):
        initial = {'n': 3, 'points': [[0, 0]]}
        incumbent = {'n': 3, 'points': [[1, 0], [1, 1]]}
        with tempfile.TemporaryDirectory() as d:
            best = Path(d)/'best'; walk = Path(d)/'walk'
            result = nr.walk(3, 0, 1, initial, best, incumbent=incumbent,
                             max_drawdown=1, walk_output=walk)
            b = json.loads(best.read_bytes()); w = json.loads(walk.read_bytes())
        self.assertEqual(b['points'], incumbent['points'])
        self.assertEqual(w['points'], initial['points'])
        self.assertEqual(result['initial_incumbent_count'], 2)
        self.assertEqual(result['distance_reference'], 'initial embedded walk coordinates')
        self.assertEqual(result['max_initial_walk_symmetric_difference'], 0)
        self.assertEqual(b['metadata']['initial_walk_embedded_normalized_sha256'], result['initial_walk_embedded_normalized_sha256'])
        self.assertEqual(w['metadata']['initial_incumbent_embedded_normalized_sha256'], result['initial_incumbent_embedded_normalized_sha256'])

    def test_separate_input_rejections(self):
        small = {'n': 3, 'points': [[0, 0]]}; large = {'n': 3, 'points': [[1, 0], [1, 1]]}
        invalid = {'n': 3, 'points': [[0, 0], [0, 0]]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'best'
            for initial, best, drawdown in ((small, large, 0), (large, small, 4), (small, invalid, 4)):
                with self.assertRaises(ValueError):
                    nr.walk(3, 0, 1, initial, p, incumbent=best, max_drawdown=drawdown)
            self.assertFalse(p.exists())

    def test_separate_walk_improvement_updates_best_and_walk(self):
        initial = {'n': 3, 'points': [[1, 1]]}
        incumbent = {'n': 3, 'points': [[1, 0], [1, 1]]}; calls = [0]
        def clock():
            calls[0] += 1
            return 0 if calls[0] <= 6 else 2
        with tempfile.TemporaryDirectory() as d:
            best = Path(d)/'best'; walk = Path(d)/'walk'
            result = nr.walk(3, 1, 1, initial, best, incumbent=incumbent,
                             walk_output=walk, max_drawdown=1, rng=FixedRandom(), clock=clock)
            b = json.loads(best.read_bytes()); w = json.loads(walk.read_bytes())
        self.assertEqual(result['best_count'], 3)
        self.assertEqual(b['points'], w['points'])
        self.assertEqual(result['counts']['improvement_promotions'], 1)


if __name__=='__main__':unittest.main()
