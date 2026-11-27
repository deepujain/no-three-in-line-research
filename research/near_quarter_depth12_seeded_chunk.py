"""One explicit exact-depth12 seeded chunk; allocation and any next chunk are external."""
import argparse
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import sys
from threading import Event, Timer
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import near_quarter_depth12_cut_continuation as frozen
from research.near_quarter_packed_worker import validate_gate

METHOD='exact_depth12_explicit_seed_single_chunk'
ANCHOR_REPORT='data/main-depth12-cut-continuation-v1/report.json'
ANCHOR_RECEIPT='data/experiments/shepherd-main-depth12-cut-continuation-v1.json'
ANCHOR_AUDIT='data/main-depth12-cut-continuation-v1-independent-actual-audit.json'
BASE_AUDIT=frozen.PARENT_AUDIT
FIXED_PINS={
    ANCHOR_REPORT:'72d9237f7168082bef2fecf31665cdd454f3397f9db36e1f225e8abdf199542a',
    ANCHOR_RECEIPT:'ca7381b73cef16fb609a4eee19d02166d663481695062bfa39b813f51fd62c57',
    ANCHOR_AUDIT:'edb747a974558ec8864c43565ae6e5fb3f4b5c5ebdf68658886370805be9b4db',
    BASE_AUDIT:'6749da866f32d19ef531487f4f62aca0ff413246d64f5f4f2b16388942195847',
}
FROZEN_SOURCES={**frozen.FROZEN_SOURCES,
    'research/near_quarter_depth12_cut_continuation.py':'797de26c12bcf09a6e9d1ce017c49e200bfa55f6a0dc9b6677d282cca7c55bdc'}
PREFIX=list(frozen.EXPECTED_IDS[:13])
MAP_HASH=frozen.MAP_HASH
MASK_HASH=frozen.MASK_HASH
PRIMARY_COUNT=369
ANCHOR_CUT_COUNT=487
BINARY_COUNT=9539
PAIR_CENSUS=67896
CUT_LIMIT=1000
DEGREE_COUNTS=(2823,5002,11814)
REPORT_LIMIT=2*1024*1024
RECEIPT_LIMIT=256*1024
FIXED_AUDIT_LIMIT=16*1024*1024


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def resolve(path):return (ROOT/Path(path)).resolve()


def read_pinned(path,expected,limit,check,pins):
    check();path=resolve(path)
    if (not isinstance(expected,str) or len(expected)!=64
            or any(c not in '0123456789abcdef' for c in expected)):
        raise ValueError('invalid explicit SHA256')
    if path.stat().st_size>limit:raise ValueError('seed artifact exceeds byte bound')
    raw=path.read_bytes()
    if len(raw)>limit or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('seed artifact hash/size mismatch')
    if str(path) in pins and pins[str(path)]!=expected:raise ValueError('conflicting input pins')
    pins[str(path)]=expected
    value=json.loads(raw);check();return value


def stage_from(report):
    stages=report['stages']
    if not stages or stages[0]['depth']!=12:raise ValueError('wrong seed depth')
    if any(s['status']!='unstarted' for s in stages[1:]):raise ValueError('seed searched another depth')
    return stages[0]


def validate_receipt(report_path,report,receipt,check,pins):
    if receipt['status']!='completed' or receipt['sources_unchanged'] is not True:
        raise ValueError('seed receipt incomplete or changed')
    gate=receipt['gate']
    if type(gate['returncode']) is not int or gate['returncode'] not in (0,2):raise ValueError('seed execution failed')
    expected_code=(0 if (report['complete'] or report['status']=='cut_limit') else 2) if report['method']==METHOD else (0 if report['status'] in ('witness','all_ancestors_unsat_solver_reported') else 2)
    if gate['returncode']!=expected_code:raise ValueError('seed report/receipt outcome mismatch')
    expected_gate='exited' if gate['returncode']==0 else 'worker_error'
    if gate['gate_status']!=expected_gate:raise ValueError('seed gate status mismatch')
    validate_gate({**gate,'gate_status':'exited','returncode':0},30,256)
    argv=receipt['argv']
    if argv.count('--output-dir')!=1 or resolve(argv[argv.index('--output-dir')+1])/'report.json'!=resolve(report_path):
        raise ValueError('seed receipt output provenance mismatch')
    source='research/near_quarter_depth12_cut_continuation.py' if report['method']!=METHOD else 'research/near_quarter_depth12_seeded_chunk.py'
    if source not in argv or source not in receipt['sources_before']:
        raise ValueError('seed receipt source provenance mismatch')
    if report['local_source_sha256'].get(source)!=receipt['sources_before'][source]:
        raise ValueError('seed local source provenance mismatch')
    if any(receipt['sources_before'].get(name)!=expected for name,expected in report['local_source_sha256'].items()):
        raise ValueError('seed helper source provenance mismatch')
    if report['packed_source_manifest']!=frozen.source_manifest():raise ValueError('seed packed source manifest changed')
    for name,expected in receipt['sources_before'].items():
        check();path=resolve(name)
        if digest(path)!=expected:raise ValueError('seed receipt source changed: '+name)
        if str(path) in pins and pins[str(path)]!=expected:raise ValueError('conflicting source pins')
        pins[str(path)]=expected
    if report['method']==METHOD:
        declared=report['seed_input']
        for option,key in (('--seed-report','report'),('--seed-report-sha256','report_sha256'),('--seed-receipt','receipt'),('--seed-receipt-sha256','receipt_sha256')):
            if argv.count(option)!=1:raise ValueError('missing explicit seed execution provenance')
            actual=argv[argv.index(option)+1]
            if (resolve(actual)!=resolve(declared[key]) if key in ('report','receipt') else actual!=declared[key]):
                raise ValueError('seed execution predecessor provenance mismatch')


def load_seed(report_path,report_sha,receipt_path,receipt_sha,check,pins):
    fixed={}
    for name,expected in FIXED_PINS.items():
        fixed[name]=read_pinned(name,expected,FIXED_AUDIT_LIMIT if 'audit' in name else (RECEIPT_LIMIT if name==ANCHOR_RECEIPT else REPORT_LIMIT),check,pins)
    anchor=stage_from(fixed[ANCHOR_REPORT]);audit=fixed[ANCHOR_AUDIT]
    if (not audit['accepted'] or audit['report_sha256']!=FIXED_PINS[ANCHOR_REPORT]
            or audit['receipt_sha256']!=FIXED_PINS[ANCHOR_RECEIPT]
            or audit['total_ternary_cuts']!=ANCHOR_CUT_COUNT):raise ValueError('fixed anchor audit mismatch')
    validate_receipt(ANCHOR_REPORT,fixed[ANCHOR_REPORT],fixed[ANCHOR_RECEIPT],check,pins)
    base=next(s for s in fixed[BASE_AUDIT]['stages'] if s['depth']==12)
    if (not fixed[BASE_AUDIT]['accepted'] or base['independent_pair_checks']!=PAIR_CENSUS
            or base['independent_complete_mask_sha256']!=MASK_HASH):raise ValueError('fixed binary audit mismatch')
    binaries=[r['ids'] for r in base['pair_rejection_witnesses']]
    report=read_pinned(report_path,report_sha,REPORT_LIMIT,check,pins)
    receipt=read_pinned(receipt_path,receipt_sha,RECEIPT_LIMIT,check,pins)
    if report_sha!=FIXED_PINS[ANCHOR_REPORT] and report['method']!=METHOD:raise ValueError('unrecognized seed method')
    validate_receipt(report_path,report,receipt,check,pins)
    seed=stage_from(report)
    if report_sha!=FIXED_PINS[ANCHOR_REPORT]:
        parent=report['seed_input']
        prior=read_pinned(parent['report'],parent['report_sha256'],REPORT_LIMIT,check,pins)
        prior_receipt=read_pinned(parent['receipt'],parent['receipt_sha256'],RECEIPT_LIMIT,check,pins)
        validate_receipt(parent['report'],prior,prior_receipt,check,pins)
        previous=stage_from(prior)
        count=previous['triple_cuts']
        if (seed['retained_triple_cuts']!=count or seed['triple_cut_ids'][:count]!=previous['triple_cut_ids']
                or seed['triple_cut_records'][:count]!=previous['triple_cut_records']):
            raise ValueError('seed lost or changed predecessor cuts')
    return seed,anchor,binaries


def validate_constraints(seed,anchor,binaries,state,variables,mask_hash,check):
    if (state.map_digest.hex()!=MAP_HASH or mask_hash!=MASK_HASH
            or seed['selected_prefix_ids']!=PREFIX or seed['complete_mask_length']!=1521
            or seed['complete_mask_sha256']!=MASK_HASH or seed['mask_count']!=PRIMARY_COUNT
            or variables!=anchor['orbit_variable_ids'] or variables!=seed['orbit_variable_ids']
            or len(variables)!=PRIMARY_COUNT):raise ValueError('seed prefix/map/mask mismatch')
    cuts=seed['pair_cut_ids']
    if (len(cuts)!=BINARY_COUNT or cuts!=binaries or len(set(map(tuple,cuts)))!=len(cuts)
            or any(len(c)!=2 or any(type(v)is not int for v in c) or not 1<=c[0]<c[1]<=len(variables) for c in cuts)):
        raise ValueError('seed binary identity mismatch')
    ids=seed['triple_cut_ids'];records=seed['triple_cut_records'];total=seed['triple_cuts']
    if (type(total)is not int or not ANCHOR_CUT_COUNT<=total<=CUT_LIMIT or len(ids)!=total or len(records)!=total
            or any(type(seed[k]) is not int or seed[k]<0 for k in ('retained_triple_cuts','new_triple_cuts','total_triple_cuts'))
            or seed['retained_triple_cuts']+seed['new_triple_cuts']!=total or seed['total_triple_cuts']!=total
            or len(set(map(tuple,ids)))!=total):raise ValueError('seed ternary count/duplicate mismatch')
    if (ids[:ANCHOR_CUT_COUNT]!=anchor['triple_cut_ids'] or records[:ANCHOR_CUT_COUNT]!=anchor['triple_cut_records']):
        raise ValueError('seed changed initial cut anchor')
    for record,cut in zip(records,ids,strict=True):
        check()
        if (record['ids']!=cut or len(cut)!=3 or any(type(v)is not int or not 1<=v<=len(variables) for v in cut)
                or cut!=sorted(set(cut))):raise ValueError('invalid seeded ternary IDs')
        points=[tuple(p) for p in record['points']]
        if (len(points)!=3 or len(set(points))!=3
                or any(len(p)!=2 or any(type(c)is not int or not 0<=c<79 for c in p) for p in points)):
            raise ValueError('invalid seeded ternary points')
        a,b,c=points
        if (b[0]-a[0])*(c[1]-a[1])!=(b[1]-a[1])*(c[0]-a[0]):raise ValueError('seeded ternary not collinear')
        memberships=[next((v for v in cut if p in state.model['orbits'][variables[v-1]-1]),None) for p in points]
        if None in memberships or sorted(memberships)!=cut or set(points)&set(state.points):raise ValueError('seeded ternary membership mismatch')
    return [tuple(c) for c in cuts]


def verify_immutable(pins):
    for path,expected in pins.items():
        if digest(path)!=expected:raise ValueError('immutable source/input changed: '+path)


def run(out,seconds,seed_report,seed_report_sha256,seed_receipt,seed_receipt_sha256,*,clock=time.monotonic):
    from pysat.solvers import Solver
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:raise ValueError('invalid shared soft duration')
    start=clock();deadline=start+seconds
    def check():
        if clock()>=deadline:raise TimeoutError
    inputs={};local={name:digest(ROOT/name) for name in (str(Path(__file__).resolve().relative_to(ROOT)),'research/near_quarter_factor_shadow.py','research/near_quarter_readonly_probe.py')}
    for name,expected in FROZEN_SOURCES.items():
        if digest(ROOT/name)!=expected:raise ValueError('frozen source changed')
    local.update(FROZEN_SOURCES);manifest=frozen.source_manifest()
    stage={'depth':12,'status':'incomplete','complete':False,'pair_started':0,'pair_completed':0,'pair_cuts':0,'model_count':0,'witnesses':0,'retained_triple_cuts':0,'new_triple_cuts':0,'triple_cuts':0,'total_triple_cuts':0}
    report={'method':METHOD,'scope':'Exact depth12 only; one explicit seed chunk; zero pair probes; no retry or other depths.','status':'incomplete','complete':False,'backend':'glucose3','encoding':'seqcounter','python_sat_version':version('python-sat'),'shared_soft_seconds':seconds,'max_stages':1,'triple_cut_limit_per_stage':CUT_LIMIT,'parent_audit_sha256':FIXED_PINS[BASE_AUDIT],'local_source_sha256':local,'packed_source_manifest':manifest,'seed_input':{'report':str(resolve(seed_report)),'report_sha256':seed_report_sha256,'receipt':str(resolve(seed_receipt)),'receipt_sha256':seed_receipt_sha256},'fixed_input_sha256':dict(FIXED_PINS),'stages':[stage]}
    try:
        seed,anchor,binaries=load_seed(seed_report,seed_report_sha256,seed_receipt,seed_receipt_sha256,check,inputs)
        sample=frozen.mask_and_bounds(79,tuple(PREFIX),check)
        if len(sample['mask'])!=1521:raise ValueError('incomplete full mask')
        variables=frozen.bounded_variables(sample['mask'])
        if variables is None:raise ValueError('fixed primary capacity mismatch')
        state=frozen.PackedOrbitState(79,check=check)
        for variable in PREFIX:
            check()
            if not state.push(variable):raise ValueError('fresh prefix reconstruction failed')
        if len(state.points)!=50:raise ValueError('retained point count mismatch')
        cuts=validate_constraints(seed,anchor,binaries,state,variables,sample['mask_sha256'],check)
        stage.update(selected_prefix_ids=list(PREFIX),complete_mask_length=1521,complete_mask_sha256=sample['mask_sha256'],mask_count=len(variables),orbit_variable_ids=variables,pair_cuts=len(cuts),pair_cut_ids=[list(c) for c in cuts],reused_pair_census=PAIR_CENSUS,binary_provenance=FIXED_PINS[BASE_AUDIT],retained_triple_cuts=seed['triple_cuts'],triple_cuts=seed['triple_cuts'],total_triple_cuts=seed['triple_cuts'],triple_cut_ids=json.loads(json.dumps(seed['triple_cut_ids'])),triple_cut_records=json.loads(json.dumps(seed['triple_cut_records'])))
        if stage['triple_cuts']==CUT_LIMIT:
            stage['status']='cut_limit'
        else:
            if sum(sample['demands'])!=54 or len(sample['edges'])!=PRIMARY_COUNT:raise ValueError('residual incidence mismatch')
            clauses,pool=frozen.degree_clauses(sample['demands'],sample['edges'],check)
            literals=frozen.validate_formula(sample['demands'],sample['edges'],len(variables),clauses,pool)
            if (pool.top,len(clauses),literals)!=DEGREE_COUNTS:raise ValueError('fixed degree formula mismatch')
            stage.update(degree_variables=pool.top,degree_clauses=len(clauses),degree_literals=literals,starting_formula_clauses=len(clauses)+len(cuts)+stage['triple_cuts'],starting_formula_literals=literals+2*len(cuts)+3*stage['triple_cuts'],maximum_formula_clauses=15541,maximum_formula_literals=33892)
            frozen.formula_totals(stage)
            solver=timer=None;fired=Event()
            try:
                check();solver=Solver(name='glucose3')
                for clause in clauses:
                    check();solver.add_clause(clause)
                for cut in cuts:
                    check();solver.add_clause([-v for v in cut])
                for cut in stage['triple_cut_ids']:
                    check();solver.add_clause([-v for v in cut])
                remaining=deadline-clock()
                if remaining<=0:raise TimeoutError
                def interrupt():fired.set();solver.interrupt()
                timer=Timer(remaining,interrupt);timer.daemon=True;timer.start()
                frozen.solve_models(solver,state,variables,sample['demands'],sample['edges'],stage,check,fired,deadline,clock,out,target_orbits=27,cut_limit=CUT_LIMIT)
            finally:frozen.dispose_solver(timer,solver)
        report['status']=stage['status'];report['complete']=stage['complete']
    except TimeoutError:
        stage['status']=report['status']='timeout'
    verify_immutable(inputs);verify_immutable({str(ROOT/p):h for p,h in local.items()})
    if frozen.source_manifest()!=manifest:raise ValueError('packed source changed')
    report['immutable_input_sha256']=inputs;report['elapsed_seconds']=clock()-start
    frozen.atomic(out/'report.json',frozen.encode(report));return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--seed-report',type=Path,required=True);parser.add_argument('--seed-report-sha256',required=True)
    parser.add_argument('--seed-receipt',type=Path,required=True);parser.add_argument('--seed-receipt-sha256',required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    report=run(args.output_dir,args.seconds,args.seed_report,args.seed_report_sha256,args.seed_receipt,args.seed_receipt_sha256)
    print(json.dumps(report,sort_keys=True));return 0 if report['complete'] or report['status']=='cut_limit' else 2


if __name__=='__main__':sys.exit(main())
