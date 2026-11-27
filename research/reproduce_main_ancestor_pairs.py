"""Checkpoint-free replay of two fixed public orbit-ID pair relaxations.

The CLI uses saved public IDs and expected evidence hashes only. Source/tiny
preparation alone is not authorization for an actual n79 replay here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_factor_shadow import mask_and_bounds
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_prefix_pair_sat import incompatible_pairs, degree_clauses
from pysat.solvers import Solver

MAIN_IDS=(1522,39,100,130,170,208,366,432,322,340,562,563,524,646,288,827,892,1107,1413,1419)
REPORT_SHA='1e3cc59e60b3e989a41cf46f84a372d1f993891f27048a2cb79db4c959447014'
EXPECTED={
 18: {'mask':'062ecb7cc9d3a4bfb665a381a4b51a846e1a2719b57d5c28933b8a73d65e9cbf','vars':'cba17d11b64a5355008664cf2cd20c07088ac6054066e8f3b3c45d4a3c781eae','pairs':'fff7c9a4e9e197549874a6cb73a31152e131ce22443faf1dd86eb622619536df','pair_count':2307,'degree':(754,1338,3124)},
 17: {'mask':'bb206bd7b50d2f10bafb923fb10652d2dc4f3aa44125a65b8a6d188e5bb13ad3','vars':'b9d662b8ff82eddcacb0b2651e7ca8d5df688fcca43b7e04108363a697fbeb8a','pairs':'aa52ff200a0578cd259582e8e3de7764ddd539741afa096c9c8d40a9891637aa','pair_count':3697,'degree':(1129,2004,4702)},
}


def compact_hash(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def rebuild(n,ids,check):
    """Rebuild one complete mask, pair census, and relaxation; no checkpoint I/O."""
    sample=mask_and_bounds(n,ids,check)
    variables=[i+1 for i,b in enumerate(sample['mask']) if b]
    state=PackedOrbitState(n,check=check)
    for var in ids:
        check()
        if not state.push(var):raise ValueError('invalid published prefix')
    counts={'pair_started':0,'pair_completed':0}
    cuts=incompatible_pairs(state,variables,check,counts)
    if counts['pair_completed']!=len(variables)*(len(variables)-1)//2:
        raise ValueError('incomplete pair census')
    clauses,pool=degree_clauses(sample['demands'],sample['edges'],check)
    return {'mask_sha256':sample['mask_sha256'],'variables':variables,'pair_cuts':cuts,
            'degree_variables':pool.top,'degree_clauses':len(clauses),'degree_literals':sum(map(len,clauses)),
            'formula':clauses+[[-a,-b] for a,b in cuts]}


def solve(formula,deadline,clock=time.monotonic):
    if clock()>=deadline:return 'unknown'
    solver=Solver(name='glucose3');timer=None;fired=threading.Event()
    try:
        for clause in formula:
            if clock()>=deadline:return 'unknown'
            solver.add_clause(clause)
        remaining=deadline-clock()
        if remaining<=0:return 'unknown'
        def stop():fired.set();solver.interrupt()
        timer=threading.Timer(remaining,stop);timer.daemon=True;timer.start()
        try:
            answer=solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel();timer.join();timer=None
        if fired.is_set() or clock()>=deadline or answer is None:return 'unknown'
        return 'sat' if answer is True else 'unsat' if answer is False else 'unknown'
    finally:
        if timer is not None:timer.cancel();timer.join()
        solver.delete()


def reproduce(seconds):
    if not 0<seconds<=25:raise ValueError('seconds must be in (0,25]')
    start=time.monotonic();deadline=start+seconds
    def check():
        if time.monotonic()>=deadline:raise TimeoutError
    results=[]
    for depth in (18,17):
        check();expected=EXPECTED[depth];ids=MAIN_IDS[:depth+1]
        rebuilt=rebuild(79,ids,check)
        if (rebuilt['mask_sha256']!=expected['mask'] or compact_hash(rebuilt['variables'])!=expected['vars']
            or compact_hash(rebuilt['pair_cuts'])!=expected['pairs'] or len(rebuilt['pair_cuts'])!=expected['pair_count']
            or tuple(rebuilt[k] for k in ('degree_variables','degree_clauses','degree_literals'))!=expected['degree']):
            raise ValueError('reconstructed evidence differs')
        status=solve(rebuilt['formula'],deadline)
        results.append({'depth':depth,'solver_status':status,'mask_sha256':rebuilt['mask_sha256'],
                        'pair_cuts':len(rebuilt['pair_cuts'])})
        if status!='unsat':break
    return {'scope':'Two fixed near-quarter prefixes; UNSAT is solver-reported, not a checked proof.',
            'source_report_sha256':REPORT_SHA,
            'complete':len(results)==2 and all(r['solver_status']=='unsat' for r in results),
            'results':results,'elapsed_seconds':time.monotonic()-start}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seconds',type=float,default=25)
    args=p.parse_args()
    try: result=reproduce(args.seconds)
    except TimeoutError:result={'complete':False,'status':'timeout'}
    print(json.dumps(result,sort_keys=True))
    return 0 if result['complete'] else 2


if __name__=='__main__':sys.exit(main())
