"""Hard-tiny full-row batch traversal; no production worker/checkpoint/CLI.

Only n3/n5/n7 are permitted. The reviewed secant state remains unchanged.
"""
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time

from research.near_quarter_tiny_secants import TinyOrbitState
from src.near_quarter_model import check_candidate


def row_fill_batches(domain,weights,deficit,remaining):
    """Stream complete row covers once in local order, never global ID order."""
    domain = tuple(domain)
    if (deficit not in (1,2) or type(deficit) is not int or type(remaining) is not int or remaining < 0 or
            len(domain) > 12 or len(set(domain)) != len(domain) or
            any(type(v) is not int or type(weights.get(v)) is not int or weights[v] not in (1,2) for v in domain)):
        raise ValueError('invalid row-fill domain')
    if remaining == 0:
        return
    for variable in domain:
        if weights[variable] == deficit:
            yield (variable,)
    if deficit == 2 and remaining >= 2:
        yield from combinations((v for v in domain if weights[v] == 1),2)


def push_batch(state,batch):
    """Strong rollback when any orbit rejects; state push owns point rollback."""
    batch = tuple(batch)
    if len(batch) not in (1,2) or len(set(batch)) != len(batch):
        raise ValueError('batch must contain one or two distinct orbit IDs')
    pushed = 0
    accepted = False
    try:
        for variable in batch:
            if not state.push(variable):
                return False
            pushed += 1
        accepted = True
        return True
    finally:
        if not accepted:
            for _ in range(pushed):
                state.pop()


def pop_batch(state,batch):
    for _ in batch:
        state.pop()


class TinyBudget:
    def __init__(self,max_nodes,seconds,clock=time.monotonic):
        if type(max_nodes) is not int or not 1 <= max_nodes <= 10000:
            raise ValueError('tiny node ceiling must be in 1..10000')
        if isinstance(seconds,bool) or not math.isfinite(seconds) or not 0 < seconds <= 5:
            raise ValueError('tiny seconds must be in (0,5]')
        self.max_nodes,self.clock = max_nodes,clock
        self.deadline = clock()+seconds
        self.nodes = self.probes = self.batches = self.rejected_batches = 0
        self.status = 'running'

    def check(self,*,enter=False):
        if self.status != 'running':
            return False
        if self.clock() >= self.deadline:
            self.status = 'tiny_timeout'
            return False
        if enter:
            if self.nodes >= self.max_nodes:
                self.status = 'tiny_node_limit'
                return False
            self.nodes += 1
        return True


def _enumerate_slice(state,orbits,rows,target_four,budget,on_leaf):
    """Shared hard-tiny traversal, also exercised by abstract quota fixtures."""
    if state.n not in (3,5,7) or len(state.model['orbits']) > 12 or not 1 <= target_four <= 3:
        raise ValueError('slice traversal is tiny-only')
    row_rank = {row:i for i,row in enumerate(rows)}
    def visit():
        if not budget.check(enter=True):
            return
        if state.full_family_leaf():
            on_leaf(state)
            return
        remaining = target_four-state.four_selected
        if remaining <= 0:
            return
        domains = {row:[] for row in rows if state.rows[row] < 2}
        weights = {row:{} for row in domains}
        viable_count = 0
        before = state.snapshot()
        for variable in orbits:
            if not budget.check():
                return
            budget.probes += 1
            if state.push(variable):
                viable_count += 1
                orbit = state.model['orbits'][variable-1]
                for row in domains:
                    contribution = sum(y == row for x,y in orbit)
                    if contribution:
                        domains[row].append(variable)
                        weights[row][variable] = contribution
                state.pop()
            if state.snapshot() != before:
                raise RuntimeError('MRV probe failed to restore state')
        if viable_count < remaining:
            return
        for row,contributions in weights.items():
            if sum(sorted(contributions.values(),reverse=True)[:remaining]) < 2-state.rows[row]:
                return
        if not domains:
            raise RuntimeError('filled rows without exact family leaf')
        row = min(domains,key=lambda r:(len(domains[r]),-(2-state.rows[r]),row_rank[r]))
        deficit = 2-state.rows[row]
        for batch in row_fill_batches(domains[row],weights[row],deficit,remaining):
            if not budget.check():
                return
            budget.batches += 1
            if not push_batch(state,batch):
                budget.rejected_batches += 1
                if state.snapshot() != before:
                    raise RuntimeError('rejected batch mutated state')
                continue
            try:
                if state.rows[row] != 2:
                    raise RuntimeError('accepted batch did not fill chosen row')
                visit()
            finally:
                pop_batch(state,batch)
            if state.snapshot() != before:
                raise RuntimeError('batch pop failed to restore state')
    visit()


def tiny_batch_traversal(n,*,diagonal_order=None,orbit_order=None,row_order=None,
                         max_nodes=10000,seconds=5,clock=time.monotonic):
    state = TinyOrbitState(n)  # Rejects n9/n79 before constructing grid state.
    def permutation(values,expected):
        values = list(expected if values is None else values)
        if any(type(v) is not int for v in values) or sorted(values) != list(expected):
            raise ValueError('orders must be exact declared-domain permutations')
        return values
    four = state.model['four_count']
    diagonals = permutation(diagonal_order,range(four+1,len(state.model['orbits'])+1))
    orbits = permutation(orbit_order,range(1,four+1))
    rows = permutation(row_order,range(n))
    budget = TinyBudget(max_nodes,seconds,clock)
    sources = {name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in (
        ('batch_source',Path(__file__).resolve()),
        ('state_source',Path(TinyOrbitState.push.__code__.co_filename).resolve()),
        ('model_source',Path(check_candidate.__code__.co_filename).resolve()),
        ('verifier_source',Path(__file__).resolve().parents[1]/'src/verify.py'))}
    identity = {'version':'tiny-near-quarter-full-row-batches-v1','n':n,
                'diagonal_order':diagonals,'orbit_order':orbits,'row_order':rows,
                'prune_policy':'global orbit count plus top-r optimistic row load',
                'pair_order':'unordered local candidate permutation, i<j','sources':sources}
    found = set()
    leaf_visits = 0
    def leaf(current):
        nonlocal leaf_visits
        if not check_candidate(current.model,current.selected)['valid_full_witness']:
            raise RuntimeError('full tiny batch leaf failed dual validation')
        leaf_visits += 1
        found.add(tuple(sorted(current.selected)))
    empty = state.snapshot()
    completed_slices = 0
    for diagonal in diagonals:
        if not budget.check():
            break
        if not state.push(diagonal):
            raise RuntimeError('empty diagonal slice rejected')
        try:
            _enumerate_slice(state,orbits,rows,n//2,budget,leaf)
        finally:
            state.pop()
        if state.snapshot() != empty:
            raise RuntimeError('slice did not restore empty state')
        if budget.status != 'running':
            break
        completed_slices += 1
    status = 'tiny_slices_exhausted' if budget.status == 'running' else budget.status
    return {'status':status,'complete':status == 'tiny_slices_exhausted',
            'nodes':budget.nodes,'domain_probes':budget.probes,'batch_attempts':budget.batches,
            'rejected_batches':budget.rejected_batches,'completed_slices':completed_slices,
            'full_leaf_visits':leaf_visits,'unique_sets':[list(ids) for ids in sorted(found)],
            'duplicate_leaf_visits':leaf_visits-len(found),'empty_state_restored':state.snapshot() == empty,
            'identity':identity,'order_identity_sha256':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()}
