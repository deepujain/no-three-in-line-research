"""Fixed-main-prefix near-quarter pair SAT with bounded lazy three-orbit cuts."""
import argparse
import hashlib
from importlib.metadata import version
import itertools
import json
import math
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_factor_shadow import prefix_paths, mask_and_bounds
from research.near_quarter_packed_worker import source_manifest
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_readonly_probe import probe_orbit
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import verify_certificate,verify_certificate_bruteforce

EXPECTED_IDS=(1522,39,100,130,170,208,366,432,322,340,562,563,524,646,288,827,892,1107,1413,1419)
MASK_HASH='2f18269cb333278f6b6d6459eb653ce886544f797e4adabbbf8f5cab472b3173'


def incompatible_pairs(state, variables, check, counts):
    """Enumerate every pair once; rollback is mandatory even on interruption."""
    base=state.snapshot();cuts=[]
    for i,first in enumerate(variables[:-1]):
        check()
        if not state.push(first): raise RuntimeError('complete-mask first orbit rejected')
        try:
            for j in range(i+1,len(variables)):
                check();counts['pair_started']+=1
                admissible=probe_orbit(state,variables[j],check)
                if not admissible: cuts.append((i+1,j+1))
                counts['pair_completed']+=1
        finally:
            state.rollback_last_orbit()
        if state.snapshot()!=base: raise RuntimeError('pair rollback changed prefix')
    check()
    return cuts


def degree_clauses(demands,edges,check):
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    incidence=[[] for _ in demands]
    for i,(u,v) in enumerate(edges,1):
        check()
        if u==v or not 0<=u<len(demands) or not 0<=v<len(demands): raise ValueError('bad edge')
        incidence[u].append(i);incidence[v].append(i)
    if any(len(a)<d for a,d in zip(incidence,demands)): raise ValueError('degree shortfall')
    pool=IDPool(start_from=len(edges)+1);clauses=[]
    for values,demand in zip(incidence,demands):
        check();clauses.extend(CardEnc.equals(lits=values,bound=demand,vpool=pool,encoding=EncType.seqcounter).clauses)
    check();return clauses,pool


def first_bad_triple(points,check):
    """Exact determinant scan, bounded memory, returning first triple or None."""
    for a,b,c in itertools.combinations(sorted(points),3):
        check()
        if (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0]):
            return a,b,c
    check();return None


def triple_cut(triple,point_to_var):
    ids={point_to_var.get(p) for p in triple}; ids.discard(None)
    if len(ids)!=3: raise RuntimeError('triple not explained by three new orbit variables')
    return tuple(sorted(ids))


def solve_models(solver,state,variables,demands,edges,report,check,fired,deadline,clock,out,*,target_points=158,target_orbits=20,cut_limit=1000):
    """Check complete models and add only necessary distinct three-orbit cuts."""
    known=set();base_points=set(state.points)
    while True:
        check()
        answer=solver.solve_limited(expect_interrupt=True)
        if fired.is_set() or clock()>=deadline or answer is None: raise TimeoutError
        if answer is False:
            report['status']='unsat_solver_reported';report['complete']=True;return
        if answer is not True: raise RuntimeError('unexpected solver response')
        report['model_count']+=1
        model=solver.get_model()
        if model is None: raise RuntimeError('missing solver model')
        chosen={x for x in model if 1<=x<=len(variables)}
        degrees=[0]*len(demands);point_to_var={};points=set(base_points)
        for index in chosen:
            u,v=edges[index-1];degrees[u]+=1;degrees[v]+=1
            for point in state.model['orbits'][variables[index-1]-1]:
                if point in points: raise RuntimeError('overlapping model orbits')
                points.add(point);point_to_var[point]=index
        if degrees!=demands or len(chosen)!=target_orbits or len(points)!=target_points:
            raise RuntimeError('degree model failed independent validation')
        bad=first_bad_triple(points,check)
        if bad is None:
            cert={'n':state.n,'points':[list(point) for point in sorted(points)]}
            checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
            if any(not c['valid'] or c['point_count']!=target_points for c in checks) or checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']:
                raise RuntimeError('witness dual verification failed')
            digest=checks[0]['normalized_sha256']
            cert['metadata']={'method':'fixed_main19_pair_sat','normalized_sha256':digest,'novelty_claim':False}
            atomic(out/('witness-'+digest+'.json'),encode(cert))
            report['witnesses']=1;report['status']='witness';report['complete']=True;return
        cut=triple_cut(bad,point_to_var)
        if cut in known: raise RuntimeError('solver repeated excluded triple')
        known.add(cut);solver.add_clause([-v for v in cut]);report['triple_cuts']+=1
        report.setdefault('triple_cut_ids',[]).append(list(cut))
        report.setdefault('triple_cut_records',[]).append({'ids':list(cut),'points':[list(p) for p in bad]})
        if len(known)>=cut_limit:
            report['status']='cut_limit';return


def dispose_solver(timer,solver):
    """Join an interrupt callback before releasing its native solver."""
    if timer is not None:
        timer.cancel();timer.join()
    if solver is not None:
        solver.delete()


def run(out,seconds,*,clock=time.monotonic):
    from pysat.solvers import Solver
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:
        raise ValueError('invalid soft duration')
    start=clock();deadline=start+seconds
    def check():
        if clock()>=deadline: raise TimeoutError
    report={'scope':'Fixed main depth19 near-quarter prefix; not an unrestricted search.',
            'status':'incomplete','complete':False,'backend':'glucose3','encoding':'seqcounter',
            'python_sat_version':version('python-sat'),'triple_cut_limit':1000,'pair_started':0,'pair_completed':0,
            'pair_cuts':0,'model_count':0,'triple_cuts':0,'witnesses':0}
    local_paths=(Path(__file__).resolve(),ROOT/'research/near_quarter_factor_shadow.py',ROOT/'research/near_quarter_readonly_probe.py',ROOT/'research/near_quarter_radius_factor.py')
    local_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in local_paths}
    baseline_manifest=source_manifest()
    report['local_source_sha256']=local_hashes;report['packed_source_manifest']=baseline_manifest
    pins=[];solver=None;timer=None;fired=threading.Event()
    try:
        paths,pins=prefix_paths(check)
        selected=next(ids for label,depth,ids in paths if label=='main' and depth==19)
        if selected!=EXPECTED_IDS: raise ValueError('selected path mismatch')
        sample=mask_and_bounds(79,selected,check)
        if sample['mask_sha256']!=MASK_HASH or sum(sample['mask'])!=102:
            raise ValueError('complete mask mismatch')
        variables=[i+1 for i,b in enumerate(sample['mask']) if b]
        report['selected_prefix_ids']=list(selected);report['complete_mask_sha256']=sample['mask_sha256']
        report['orbit_variable_ids']=variables
        state=PackedOrbitState(79,check=check)
        for v in selected:
            check()
            if not state.push(v): raise ValueError('prefix reconstruction failed')
        if len(state.points)!=78: raise ValueError('prefix point count mismatch')
        cuts=incompatible_pairs(state,variables,check,report)
        if report['pair_completed']!=5151: raise ValueError('incomplete pair census')
        report['pair_cuts']=len(cuts);report['pair_cut_ids']=[list(c) for c in cuts]
        clauses,pool=degree_clauses(sample['demands'],sample['edges'],check)
        if (pool.top,len(clauses),sum(map(len,clauses)))!=(555,982,2282):
            raise ValueError('degree CNF mismatch')
        report['degree_variables']=pool.top;report['degree_clauses']=len(clauses)
        check();solver=Solver(name='glucose3')
        for clause in clauses:
            check();solver.add_clause(clause)
        for i,j in cuts:
            check();solver.add_clause([-i,-j])
        remaining=deadline-clock()
        if remaining<=0: raise TimeoutError
        def interrupt():
            fired.set();solver.interrupt()
        timer=threading.Timer(remaining,interrupt);timer.daemon=True;timer.start()
        solve_models(solver,state,variables,sample['demands'],sample['edges'],report,check,fired,deadline,clock,out)
    except TimeoutError:
        report['status']='timeout'
    finally:
        dispose_solver(timer,solver)
    for path,digest in pins:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('pinned input changed')
    if source_manifest()!=baseline_manifest or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in local_hashes.items()):
        raise ValueError('source changed during probe')
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.output_dir,a.seconds);print(json.dumps(result,sort_keys=True))
    return 0 if result['status'] in ('witness','unsat_solver_reported') else 2


if __name__=='__main__':sys.exit(main())
