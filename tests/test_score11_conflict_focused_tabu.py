from itertools import combinations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import score11_conflict_focused_tabu as m
from research import score11_deficiency_walk as base
from src.verify import collinear_triples_bruteforce


def score(points):
    return len(collinear_triples_bruteforce(sorted(points)))


class FocusedTabuTests(unittest.TestCase):
    def setUp(self):
        self.n=4
        self.source={(x,y) for x in range(4) for y in range(4) if x==y or x+y==3}
        self.initial,self.removed,self.initial_score=base.initialize(self.source,4,score(self.source))

    def test_conflicts_and_every_tiny_move_match_independent_determinants(self):
        self.assertEqual(len(m.conflict_triples(self.initial,lambda:None)),score(self.initial))
        for kind in ('row','column'):
            for p in sorted(self.initial):
                result=m.move(self.initial,4,kind,p,None,lambda:None)
                if result:
                    self.assertEqual(self.initial_score+result[0],score(result[1]))
                    base.axes(result[1],4)
        for a,b in combinations(sorted(self.initial),2):
            result=m.move(self.initial,4,'rectangle',a,b,lambda:None)
            if result:
                self.assertEqual(self.initial_score+result[0],score(result[1]))
                base.axes(result[1],4)
        with self.assertRaises(ValueError):
            m.move(self.initial,4,'row',(-1,-1),None,lambda:None)

    def test_deterministic_prefix_best_and_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/'a',Path(d)/'b']
            for p in paths: p.mkdir()
            results=[m.walk(4,self.initial,self.source,self.initial_score,p,seed=279179,max_steps=8) for p in paths]
            for key in ('status','steps_completed','candidates_completed','classes','accepted','uphill','neutral','downhill','accepted_score_histogram'):
                self.assertEqual(results[0][key],results[1][key])
            self.assertGreater(results[0]['accepted'],0)
            for p,r in zip(paths,results):
                state=json.loads(Path(r['best']['path']).read_text())
                self.assertEqual(score({tuple(x) for x in state['points']}),r['best']['exact_conflict_count'])
                self.assertEqual(state['metadata']['valid'],r['best']['exact_conflict_count']==0)

    def test_sampled_uphill_is_accepted_when_only_admissible_choice(self):
        real=m.move
        def only_uphill(*args):
            result=real(*args)
            return result if result is not None and result[0]>0 else None
        source={(i,i) for i in range(5)} | {(i,(i+1)%5) for i in range(5)}
        initial,_,initial_score=base.initialize(source,5,score(source))
        with tempfile.TemporaryDirectory() as d, patch.object(m,'move',only_uphill):
            result=m.walk(5,initial,source,initial_score,Path(d),max_steps=1)
        self.assertEqual(result['steps_completed'],1)
        self.assertEqual(result['uphill'],1)
        self.assertEqual(result['accepted'],1)

    def test_incomplete_sample_never_selects(self):
        real=m.move; calls=[0]
        def interrupt(*args):
            calls[0]+=1
            if calls[0]==3: raise TimeoutError('partial sample')
            return real(*args)
        with tempfile.TemporaryDirectory() as d, patch.object(m,'move',interrupt):
            result=m.walk(4,self.initial,self.source,self.initial_score,Path(d),max_steps=3)
        self.assertEqual(result['status'],'timeout')
        self.assertEqual(result['steps_started'],1)
        self.assertEqual(result['steps_completed'],0)
        self.assertEqual(result['accepted'],0)
        self.assertEqual(result['candidates_started'],3)
        self.assertEqual(result['candidates_completed'],2)

    def test_late_valid_candidate_saved_and_validator_failure_not_saved(self):
        points={(0,0),(0,1),(1,0)};now=[0]
        second=base.verify_certificate_bruteforce
        def check():
            if now[0]>=1: raise TimeoutError
        def slow(cert):
            result=second(cert);now[0]=2;return result
        with tempfile.TemporaryDirectory() as d, patch.object(base,'verify_certificate_bruteforce',slow):
            result=m.candidate(2,points,0,points|{(1,1)},Path(d),0,['witness','strict_best'],check,{})
            self.assertTrue(json.loads(Path(result['path']).read_text())['metadata']['valid'])
        def wrong(cert):
            result=second(cert);result['conflict_count']+=1;return result
        with tempfile.TemporaryDirectory() as d, patch.object(base,'verify_certificate_bruteforce',wrong):
            with self.assertRaises(RuntimeError):
                m.candidate(2,points,0,points|{(1,1)},Path(d),0,['witness'],lambda:None,{})
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_bounds_reject_bad_input(self):
        with tempfile.TemporaryDirectory() as d:
            for seconds,steps in ((0,1),(26,1),(float('nan'),1),(25,2001),(25,True)):
                with self.assertRaises(ValueError):
                    m.walk(4,self.initial,self.source,self.initial_score,Path(d),seconds=seconds,max_steps=steps)


if __name__=='__main__':
    unittest.main()
