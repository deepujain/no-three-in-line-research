"""Unrun bounded fake/source lifetime proposal; never validates real geometry.

The primary input is explicitly empty under a patched validator. Independent
owner loops use only empty fake tables. This is control-flow evidence, not a
reachable-state, line-correctness, resource, durability or timing proof.
"""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
import weakref
from research import full_complement_row75_core as core
from research import full_complement_row75_primary as primary
from research import full_complement_row75_independent as independent

PINS = {
    'full_complement_row75_core.py':'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b',
    'full_complement_row75_primary.py':'2780666ac7f2a1d31e4b735135164fd4f0baf6c06b1424fb6eff405d01006e0e',
    'full_complement_row75_independent.py':'c8fcea3629d5a4d3ccac5f92d925a3e88306fa3e747b40f109142d310dbe07e3',
    'full_complement_row75_driver.py':'970eacf3f4a9e95141d83a227cffc3a835eca14c746dbd08860fc089ca999ffc'}
POINTS = ((0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,1),(1,2),(1,3))


def identities():
    for name,expected in PINS.items():
        path = Path(__file__).parent/name
        core.require(path.stat().st_size <= 128*1024,'source size bound')
        core.require(core.sha(path.read_bytes()) == expected,'frozen source '+name)


def forbidden(*args,**kwargs):
    raise AssertionError('real geometric operation reached')


class FakeBudget:
    """Retains no graph arguments; does not claim real graph accounting."""
    def __init__(self,fail=False):
        self.fail = fail
        self.calls = 0
    def checkpoint(self):
        pass
    def charge(self,kind,component):
        core.require(kind == 'comparisons','fake loop reached geometry charge')
    def check_graph(self,*roots):
        self.calls += 1
        if self.fail:
            raise RuntimeError('scripted graph failure')


def primary_case(fail):
    observed = {'returns':0,'cleared':False,'escaped':False}
    def trace(frame,event,arg):
        if frame.f_code is primary.costs.__code__ and event == 'return':
            table = frame.f_locals['table']
            observed['returns'] += 1
            observed['cleared'] = type(table) is dict and len(table) == 0
            observed['escaped'] = type(arg) is dict and any(value is table for value in arg.values())
        return trace
    previous = sys.gettrace()
    core.require(previous is None,'no existing tracer may be displaced')
    budget = FakeBudget(fail)
    try:
        with patch.object(core,'validate_points',lambda values,n:()),patch.object(primary,'line_key',forbidden):
            sys.settrace(trace)
            try:
                result = primary.costs((),5,budget)
            finally:
                sys.settrace(previous)
    except RuntimeError as error:
        core.require(fail and str(error) == 'scripted graph failure','expected primary failure')
    else:
        core.require(not fail and result == {'baseline':0,'costs':[[0]*5 for _ in range(5)]},'fake primary return')
    core.require(observed == {'returns':1,'cleared':True,'escaped':False},'primary owner cleanup')
    core.require(set(vars(budget)) == {'fail','calls'},'fake graph sink retained no alias')
    return {'scripted_error':fail,'primary_table_empty_at_return':True,'table_absent_from_return':True}


class FakeTable(dict):
    """Weak-referenceable empty owner; not accepted by the real graph walker."""


def independent_case(phase,fail):
    references = []
    def table(*args,**kwargs):
        core.require(all(reference() is None for reference in references),'previous table alias survives next map')
        result = FakeTable()
        references.append(weakref.ref(result))
        core.require(len(references) <= 5,'bounded fake table creations')
        return result
    budget = FakeBudget(fail)
    records = [{'row':row,'current':tuple(x for x,y in POINTS if y == row),
                'best':tuple(x for x,y in POINTS if y == row),'best_score':0} for row in range(5)]
    try:
        with patch.object(independent,'_endpoint_table',table),patch.object(independent,'_direction_line',forbidden),\
             patch.object(independent,'_endpoint_count',forbidden),patch.object(independent,'_target_column',forbidden):
            if phase == 'retained':
                result = independent.verify_profiles(POINTS,5,[[0]*5 for _ in range(5)],records,0,budget)
                core.require(result['verified_cells'] == 25,'fake retained loop complete')
            else:
                core.require(independent.endpoint_raw(POINTS,5,budget) == 0,'fake candidate endpoint return')
    except RuntimeError as error:
        core.require(fail and str(error) == 'scripted graph failure','expected independent failure')
    else:
        core.require(not fail,'scripted independent failure was reached')
    core.require(len(references) == (5 if phase == 'retained' and not fail else 1),'exact fake owner count')
    core.require(all(reference() is None for reference in references),'independent owner or alias survives return')
    core.require(set(vars(budget)) == {'fail','calls'},'fake graph sink retained no alias')
    return {'phase':phase,'scripted_error':fail,'tables_created':len(references),'all_owners_and_aliases_dead':True}


def run():
    identities()
    results = [primary_case(fail) for fail in (False,True)]
    results.extend(independent_case(phase,fail) for phase in ('retained','candidate') for fail in (False,True))
    identities()
    return {'passed':True,'source_pins':PINS,'source_sha256':core.sha(Path(__file__).read_bytes()),
            'cases':results,'real_geometric_operations':0,'resource_envelope_executed':False,
            'scope':__doc__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('immutable evidence exists')
    raw = (json.dumps(run(),sort_keys=True,indent=2)+'\n').encode('ascii')
    core.require(len(raw) <= 64*1024,'fake lifetime evidence cap')
    with args.output.open('xb') as output:
        core.require(output.write(raw) == len(raw),'complete evidence write')


if __name__ == '__main__':
    main()
