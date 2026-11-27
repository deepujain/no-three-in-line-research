"""Bounded adaptive ancestor pair SAT: main depths 18,17,16 only."""
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
from research.near_quarter_factor_shadow import prefix_paths, mask_and_bounds
from research.near_quarter_prefix_pair_sat import EXPECTED_IDS, incompatible_pairs, degree_clauses, first_bad_triple, triple_cut, dispose_solver
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_packed_worker import source_manifest
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import verify_certificate, verify_certificate_bruteforce

PARENT_AUDIT='data/main19-pair-sat-v1-independent-actual-audit.json'
PARENT_AUDIT_HASH='4c736f3cce8914d23a9b687cb810880b57cb13498cda23b0a944407729cfe9b4'
DEPTHS=(18,17,16)

def solve_models(solver,state,variables,demands,edges,report,check,fired,deadline,clock,out,*,target_points=158,target_orbits=20,cut_limit=1000):
    """Check complete models and add only necessary distinct three-orbit cuts."""
    known=set();base_points=set(state.points)
    while True:
        check()
        answer=solver.solve_limited(expect_interrupt=True)
        if fired.is_set() or clock()>=deadline: raise TimeoutError
        if answer is None:
            report['status']='solver_unknown';return
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
            cert['metadata']={'method':'fixed_main_ancestor_pair_sat','depth':report.get('depth'),'normalized_sha256':digest,'novelty_claim':False}
            atomic(out/('witness-'+digest+'.json'),encode(cert))
            report['witnesses']=1;report['status']='witness';report['complete']=True;return
        cut=triple_cut(bad,point_to_var)
        if cut in known: raise RuntimeError('solver repeated excluded triple')
        known.add(cut);solver.add_clause([-v for v in cut]);report['triple_cuts']+=1
        report.setdefault('triple_cut_ids',[]).append(list(cut))
        report.setdefault('triple_cut_records',[]).append({'ids':list(cut),'points':[list(p) for p in bad]})
        if len(known)>=cut_limit:
            report['status']='cut_limit';return



def bounded_variables(mask):
    if any(type(x) is not int or x not in (0,1) for x in mask):
        raise ValueError('incomplete or invalid mask')
    result=[i+1 for i,marked in enumerate(mask) if marked]
    return None if len(result)>200 else result


def prefix_for_depth(selected, depth):
    if selected!=EXPECTED_IDS or depth not in DEPTHS:
        raise ValueError('invalid ancestor identity or depth')
    return selected[:depth+1]


def adaptive_loop(report, run_depth):
    """Only native UNSAT at a depth authorizes the next shallower depth."""
    for stage in report['stages']:
        stage['status']='incomplete'
        run_depth(stage)
        if stage['status']!='unsat_solver_reported':
            report['status']=stage['status']
            report['complete']=stage['status']=='witness'
            return
    report['status']='all_ancestors_unsat_solver_reported';report['complete']=True


def run(out,seconds,*,clock=time.monotonic):
    from pysat.solvers import Solver
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:
        raise ValueError('invalid soft duration')
    start=clock();deadline=start+seconds
    def check():
        if clock()>=deadline: raise TimeoutError
    local_paths=(Path(__file__).resolve(),ROOT/'research/near_quarter_prefix_pair_sat.py',ROOT/'research/near_quarter_factor_shadow.py',ROOT/'research/near_quarter_readonly_probe.py')
    local_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in local_paths}
    baseline_manifest=source_manifest()
    report={'scope':'Only main committed-prefix ancestors at depths 18,17,16; each next depth requires preceding native UNSAT.',
            'status':'incomplete','complete':False,'backend':'glucose3','encoding':'seqcounter','python_sat_version':version('python-sat'),
            'local_source_sha256':local_hashes,'packed_source_manifest':baseline_manifest,
            'parent_audit_sha256':PARENT_AUDIT_HASH,
            'stages':[{'depth':d,'status':'unstarted','complete':False,'pair_started':0,'pair_completed':0,
                       'pair_cuts':0,'model_count':0,'triple_cuts':0,'witnesses':0} for d in DEPTHS]}
    pins=[]
    try:
        check();raw=(ROOT/PARENT_AUDIT).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=PARENT_AUDIT_HASH: raise ValueError('parent audit hash mismatch')
        audit=json.loads(raw)
        if not audit.get('accepted') or audit.get('independent_pair_checks')!=5151 or audit.get('independent_pair_rejections')!=1445:
            raise ValueError('parent audit mismatch')
        paths,pins=prefix_paths(check)
        selected=next(ids for label,depth,ids in paths if label=='main' and depth==19)
        if selected!=EXPECTED_IDS: raise ValueError('main path identity mismatch')
        def run_depth(stage):
            check(); depth=stage['depth'];ids=prefix_for_depth(selected,depth)
            stage['selected_prefix_ids']=list(ids)
            sample=mask_and_bounds(79,ids,check)
            stage['complete_mask_sha256']=sample['mask_sha256']; stage['mask_count']=sum(sample['mask'])
            variables=bounded_variables(sample['mask'])
            if variables is None:
                stage['status']='mask_capacity';return
            stage['orbit_variable_ids']=variables
            if sum(sample['demands'])!=2*(39-depth): raise ValueError('residual demand mismatch')
            state=PackedOrbitState(79,check=check)
            for var in ids:
                check()
                if not state.push(var): raise ValueError('prefix reconstruction failed')
            if len(state.points)!=2+4*depth: raise ValueError('prefix cardinality mismatch')
            cuts=incompatible_pairs(state,variables,check,stage)
            expected=len(variables)*(len(variables)-1)//2
            if stage['pair_completed']!=expected: raise ValueError('incomplete pair census')
            stage['pair_cuts']=len(cuts);stage['pair_cut_ids']=[list(c) for c in cuts]
            try:
                clauses,pool=degree_clauses(sample['demands'],sample['edges'],check)
            except ValueError as exc:
                if str(exc)=='degree shortfall':
                    stage['status']='degree_shortfall';return
                raise
            literals=sum(map(len,clauses))
            if pool.top>2000 or len(clauses)>4000 or literals>10000:
                raise ValueError('degree formula exceeds reviewed bound')
            stage['degree_variables']=pool.top;stage['degree_clauses']=len(clauses);stage['degree_literals']=literals
            solver=timer=None;fired=threading.Event()
            try:
                check();solver=Solver(name='glucose3')
                for clause in clauses: check();solver.add_clause(clause)
                for i,j in cuts: check();solver.add_clause([-i,-j])
                remaining=deadline-clock()
                if remaining<=0: raise TimeoutError
                def interrupt(): fired.set();solver.interrupt()
                timer=threading.Timer(remaining,interrupt);timer.daemon=True;timer.start()
                solve_models(solver,state,variables,sample['demands'],sample['edges'],stage,check,fired,deadline,clock,out,target_orbits=39-depth)
            finally:
                dispose_solver(timer,solver)
        adaptive_loop(report,run_depth)
    except TimeoutError:
        report['status']='timeout'
        for stage in report['stages']:
            if stage['status']=='incomplete': stage['status']='timeout';break
    for path,digest in pins:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('pinned input changed')
    if hashlib.sha256((ROOT/PARENT_AUDIT).read_bytes()).hexdigest()!=PARENT_AUDIT_HASH: raise ValueError('parent audit changed')
    if source_manifest()!=baseline_manifest or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in local_hashes.items()):
        raise ValueError('source changed during probe')
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report));return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.output_dir,a.seconds);print(json.dumps(result,sort_keys=True))
    return 0 if result['status'] in ('witness','all_ancestors_unsat_solver_reported') else 2


if __name__=='__main__':sys.exit(main())
