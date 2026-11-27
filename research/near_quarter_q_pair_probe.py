"""One checkpoint-free Q degree-plus-pair relaxation; no lazy triples or DFS."""
import argparse
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_factor_shadow import mask_and_bounds
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_prefix_pair_sat import incompatible_pairs, degree_clauses
from research.near_quarter_packed_worker import source_manifest
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import normalized_sha256

Q=(1522,100,130,170,208,366,432,322,340,562,563,524,646,288,827,892,1107)
MAP_HASH='71b8293298da69ac9a959ef3dde69728962acb1d7b35f1fdbb85a15932a08fea'


def bounded_mask(mask):
    if any(type(x) is not int or x not in (0,1) for x in mask):raise ValueError('invalid complete mask')
    variables=[i+1 for i,b in enumerate(mask) if b]
    return None if len(variables)>320 else variables


def validate_incidence(variables,edges,demands):
    if (len(demands)!=40 or any(type(d) is not int or not 0<=d<=2 for d in demands)
            or sum(demands)!=46 or len(edges)!=len(variables)):
        raise ValueError('invalid Q incidence dimensions or demands')
    for edge in edges:
        if not isinstance(edge,(tuple,list)) or len(edge)!=2:
            raise ValueError('invalid Q edge')
        u,v=edge
        if type(u) is not int or type(v) is not int or not 0<=u<40 or not 0<=v<40 or u==v:
            raise ValueError('invalid Q edge endpoints')


def validate_pair_census(cuts,m,started,completed):
    count=m*(m-1)//2
    if started!=count or completed!=count:
        raise ValueError('incomplete pair census')
    if len(set(cuts))!=len(cuts) or any(type(a) is not int or type(b) is not int or not 1<=a<b<=m for a,b in cuts):
        raise ValueError('invalid pair cut identities')


def native_answer(solver,variables,edges,demands,pair_cuts,deadline,clock,*,expected_selected=23):
    remaining=deadline-clock()
    if remaining<=0:return {'status':'unknown'}
    fired=threading.Event()
    def stop():fired.set();solver.interrupt()
    timer=threading.Timer(remaining,stop);timer.daemon=True;timer.start()
    try:answer=solver.solve_limited(expect_interrupt=True)
    finally:timer.cancel();timer.join()
    if fired.is_set() or clock()>=deadline or answer is None:return {'status':'unknown'}
    if answer is False:return {'status':'unsat_solver_reported','basis':'trusted_native_solver_no_proof'}
    if answer is not True:raise RuntimeError('unexpected solver response')
    model=solver.get_model()
    if model is None:raise RuntimeError('missing native model')
    chosen={x for x in model if 1<=x<=len(variables)}
    degree=[0]*len(demands)
    for i in chosen:
        u,v=edges[i-1];degree[u]+=1;degree[v]+=1
    if degree!=demands or len(chosen)!=expected_selected or any(a in chosen and b in chosen for a,b in pair_cuts):
        raise RuntimeError('native relaxation model failed independent checking')
    if clock()>=deadline:return {'status':'unknown'}
    return {'status':'sat_relaxation_only','selected_local_ids':sorted(chosen)}


def run(out,seconds,*,clock=time.monotonic):
    from pysat.solvers import Solver
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:
        raise ValueError('invalid soft duration')
    start=clock();deadline=start+seconds
    def check():
        if clock()>=deadline:raise TimeoutError
    local_paths=(Path(__file__).resolve(),ROOT/'research/near_quarter_factor_shadow.py',ROOT/'research/near_quarter_prefix_pair_sat.py',ROOT/'research/near_quarter_readonly_probe.py')
    local_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in local_paths}
    before=source_manifest()
    report={'scope':'Single published Q retained near-quarter prefix; degree-plus-pair relaxation only.',
            'status':'incomplete','complete':False,'selected_prefix_ids':list(Q),'map_sha256':MAP_HASH,
            'backend':'glucose3','encoding':'seqcounter','python_sat_version':version('python-sat'),
            'local_source_sha256':local_hashes,'packed_source_manifest':before,
            'pair_started':0,'pair_completed':0,'pair_cuts':0,'mask_complete':False}
    try:
        state=PackedOrbitState(79,check=check)
        if state.map_digest.hex()!=MAP_HASH:raise ValueError('canonical orbit map mismatch')
        for var in Q:
            check()
            if not state.push(var):raise ValueError('Q reconstruction failed')
        if len(state.points)!=66:raise ValueError('Q point count mismatch')
        report['points_sha256']=normalized_sha256(79,state.points)
        sample=mask_and_bounds(79,Q,check)
        if len(sample['mask'])!=1521:raise ValueError('complete mask dimension mismatch')
        report['mask_complete']=True;report['mask_sha256']=sample['mask_sha256'];report['mask_count']=sum(sample['mask'])
        variables=bounded_mask(sample['mask'])
        if variables is None:
            report['status']='mask_capacity'
        else:
            report['orbit_variable_ids']=variables;report['demands']=sample['demands'];report['edges']=sample['edges']
            validate_incidence(variables,sample['edges'],sample['demands'])
            cuts=incompatible_pairs(state,variables,check,report)
            validate_pair_census(cuts,len(variables),report['pair_started'],report['pair_completed'])
            report['pair_cuts']=len(cuts);report['pair_cut_ids']=[list(c) for c in cuts]
            try:clauses,pool=degree_clauses(sample['demands'],sample['edges'],check)
            except ValueError as exc:
                if str(exc)=='degree shortfall':clauses=pool=None;report['status']='degree_shortfall'
                else:raise
            if clauses is not None:
                m=len(variables);literal_count=sum(map(len,clauses))
                if pool.top>9*m or len(clauses)>16*m or literal_count>48*m:raise ValueError('degree formula exceeds reviewed bound')
                report['degree_variables']=pool.top;report['degree_clauses']=len(clauses);report['degree_literals']=literal_count
                check();solver=Solver(name='glucose3')
                try:
                    for clause in clauses:check();solver.add_clause(clause)
                    for a,b in cuts:check();solver.add_clause([-a,-b])
                    answer=native_answer(solver,variables,sample['edges'],sample['demands'],cuts,deadline,clock)
                    report.update(answer)
                    report['complete']=answer['status'] in ('sat_relaxation_only','unsat_solver_reported')
                finally:solver.delete()
    except TimeoutError:report['status']='timeout'
    if source_manifest()!=before or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in local_hashes.items()):
        raise ValueError('source changed during probe')
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report));return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    report=run(a.output_dir,a.seconds);print(json.dumps(report,sort_keys=True))
    return 0 if report['complete'] else 2


if __name__=='__main__':sys.exit(main())
