from itertools import combinations,product
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import near_quarter_tiny_batches as batches
from research.near_quarter_tiny_secants import TinyOrbitState
from src.near_quarter_model import orbit_map,expand
from src.verify import collinear_triples_bruteforce

EVIDENCE = {}


class QuotaState:
    """Abstract row-quota fixture only; not claimed to be physical geometry."""
    def __init__(self,incidences,target=3):
        self.n,self.target = 3,target
        self.model = {'orbits':[tuple((i,row) for i,row in enumerate(rows)) for rows in incidences],
                      'four_count':len(incidences)}
        self.rows,self.selected = [0]*3,[]
    @property
    def four_selected(self): return len(self.selected)
    def snapshot(self): return tuple(self.rows),tuple(self.selected)
    def push(self,variable):
        if variable in self.selected or len(self.selected) >= self.target:
            return False
        weights = [sum(y == row for x,y in self.model['orbits'][variable-1]) for row in range(3)]
        if any(self.rows[row]+weights[row] > 2 for row in range(3)):
            return False
        self.rows = [self.rows[row]+weights[row] for row in range(3)]
        self.selected.append(variable)
        return True
    def pop(self):
        variable = self.selected.pop()
        for x,y in self.model['orbits'][variable-1]: self.rows[y] -= 1
    def full_family_leaf(self): return len(self.selected) == self.target and self.rows == [2,2,2]


class TinyBatchTests(unittest.TestCase):
    def test_row_batches_are_complete_unordered_covers_without_global_id_restriction(self):
        domain = [8,2,6,1]
        weights = {8:1,2:2,6:1,1:1}
        self.assertEqual(list(batches.row_fill_batches(domain,weights,1,3)),[(8,),(6,),(1,)])
        self.assertEqual(list(batches.row_fill_batches(domain,weights,2,3)),[(2,),(8,6),(8,1),(6,1)])
        self.assertEqual(list(batches.row_fill_batches(domain,weights,2,1)),[(2,)])
        self.assertEqual(list(batches.row_fill_batches(domain,weights,2,0)),[])
        for bad_domain,bad_weights in ((list(range(13)),{v:1 for v in range(13)}),([1],{1:True})):
            with self.assertRaises(ValueError):
                list(batches.row_fill_batches(bad_domain,bad_weights,2,2))

    def test_exact_real_geometry_census_is_unique_under_forward_reverse_orders(self):
        for n in (3,5,7):
            model = orbit_map(n)
            expected = set()
            for four in combinations(range(1,model['four_count']+1),n//2):
                for diagonal in range(model['four_count']+1,len(model['orbits'])+1):
                    chosen = tuple(sorted((*four,diagonal)))
                    if not collinear_triples_bruteforce(expand(model,chosen)):
                        expected.add(chosen)
            forward = batches.tiny_batch_traversal(n)
            reverse = batches.tiny_batch_traversal(n,
                orbit_order=list(reversed(range(1,model['four_count']+1))),
                diagonal_order=list(reversed(range(model['four_count']+1,len(model['orbits'])+1))),
                row_order=list(reversed(range(n))))
            for report in (forward,reverse):
                self.assertTrue(report['complete'])
                self.assertEqual(report['status'],'tiny_slices_exhausted')
                self.assertEqual({tuple(ids) for ids in report['unique_sets']},expected)
                self.assertEqual(report['full_leaf_visits'],len(expected))
                self.assertEqual(report['duplicate_leaf_visits'],0)
                self.assertTrue(report['empty_state_restored'])
            self.assertNotEqual(forward['order_identity_sha256'],reverse['order_identity_sha256'])
            EVIDENCE[n] = {'expected_full_sets':len(expected),'forward':forward,'reverse':reverse}

    def test_abstract_quota_fixtures_exercise_many_unique_leaves_and_weight_two_batches(self):
        fixtures = [[(0,1),(1,2),(0,2)],
                    [(0,1),(0,1),(1,2),(1,2),(0,2),(0,2),(0,0),(1,1),(2,2)]]
        details = []
        for incidences in fixtures:
            expected = set()
            for chosen in combinations(range(1,len(incidences)+1),3):
                loads = [sum(incidences[v-1].count(row) for v in chosen) for row in range(3)]
                if loads == [2,2,2]: expected.add(chosen)
            for reverse in (False,True):
                state = QuotaState(incidences)
                empty = state.snapshot()
                found = []
                budget = batches.TinyBudget(10000,5,lambda:0)
                orbits = list(range(1,len(incidences)+1))
                rows = [0,1,2]
                if reverse: orbits.reverse(); rows.reverse()
                batches._enumerate_slice(state,orbits,rows,3,budget,
                    lambda s: found.append(tuple(sorted(s.selected))))
                self.assertEqual(set(found),expected)
                self.assertEqual(len(found),len(expected))
                self.assertEqual(state.snapshot(),empty)
                self.assertEqual(budget.status,'running')
                details.append({'abstract_fixture_orbits':len(incidences),'reverse':reverse,
                                'unique_sets':len(found),'nodes':budget.nodes})
        EVIDENCE['abstract_quota'] = details

    def test_every_tiny_admissible_two_orbit_transaction_restores_on_accept_or_reject(self):
        transactions = rejected = 0
        for n in (3,5,7):
            model = orbit_map(n)
            for bits in product((False,True),repeat=len(model['orbits'])):
                state = TinyOrbitState(n)
                if not all(state.push(v) for v,b in enumerate(bits,1) if b):
                    continue
                for first,second in combinations(range(1,len(model['orbits'])+1),2):
                    if first in state.selected or second in state.selected: continue
                    before = state.snapshot()
                    candidate = state.selected+[first,second]
                    four = sum(v <= model['four_count'] for v in candidate)
                    expected = (four <= n//2 and len(candidate)-four <= 1 and
                                not collinear_triples_bruteforce(expand(model,candidate)))
                    for batch in ((first,second),(second,first)):
                        accepted = batches.push_batch(state,batch)
                        transactions += 1
                        self.assertIs(accepted,expected,(n,state.selected,batch))
                        if accepted: batches.pop_batch(state,batch)
                        else: rejected += 1
                        self.assertEqual(state.snapshot(),before)
        self.assertGreater(rejected,0)
        EVIDENCE['transactions'] = {'attempts':transactions,'rejected':rejected}

    def test_batch_failure_exception_unwinds_prior_successful_orbit(self):
        state = QuotaState([(0,1),(1,2),(0,2)])
        empty = state.snapshot()
        real_push = state.push
        def injected(variable):
            if variable == 2: raise RuntimeError('injected before mutation')
            return real_push(variable)
        with patch.object(state,'push',side_effect=injected),self.assertRaises(RuntimeError):
            batches.push_batch(state,(1,2))
        self.assertEqual(state.snapshot(),empty)

    def test_node_and_timeout_limits_are_incomplete_and_unwind_batches(self):
        limited = batches.tiny_batch_traversal(3,max_nodes=1)
        self.assertEqual(limited['status'],'tiny_node_limit')
        self.assertFalse(limited['complete'])
        self.assertEqual(limited['nodes'],1)
        self.assertTrue(limited['empty_state_restored'])
        state = QuotaState([(0,1),(1,2),(0,2)])
        empty = state.snapshot()
        expired = [False]
        budget = batches.TinyBudget(100,1,lambda:2 if expired[0] else 0)
        real_push = batches.push_batch
        def expire_after_batch(current,batch):
            success = real_push(current,batch)
            if success: expired[0] = True
            return success
        with patch.object(batches,'push_batch',side_effect=expire_after_batch):
            batches._enumerate_slice(state,[1,2,3],[0,1,2],3,budget,
                lambda s:self.fail('timeout must not publish a leaf'))
        self.assertEqual(budget.status,'tiny_timeout')
        self.assertEqual(state.snapshot(),empty)

    def test_hard_tiny_boundary_and_invalid_orders(self):
        for n in (9,71,79,True):
            with self.assertRaises(ValueError): batches.tiny_batch_traversal(n)
        for kwargs in ({'orbit_order':[]},{'max_nodes':10001},{'seconds':6}):
            with self.assertRaises(ValueError): batches.tiny_batch_traversal(3,**kwargs)


if __name__ == '__main__': unittest.main()
