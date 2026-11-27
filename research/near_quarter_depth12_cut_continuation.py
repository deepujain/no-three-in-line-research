"""Exact depth12 cut continuation, then optional fresh11/10; one shared gate."""
import argparse
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import sys
from threading import Event, Timer
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.near_quarter_factor_shadow import mask_and_bounds
from research.near_quarter_ancestor_pair_sat import adaptive_loop
from src.verify import verify_certificate, verify_certificate_bruteforce
from research.near_quarter_prefix_pair_sat import EXPECTED_IDS, incompatible_pairs, degree_clauses, dispose_solver, first_bad_triple, triple_cut
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_packed_worker import source_manifest
from research.diagonal_secant_checkpoint import atomic, encode

DEPTHS = (12, 11, 10)
MASK_CAP = 480
CUT_LIMIT = 1000
PARENT_REPORT = 'data/main-ancestors14-through10-cap480-pair-sat-v1/report.json'
PARENT_RECEIPT = 'data/experiments/shepherd-main-ancestors14-through10-cap480-pair-sat-v1.json'
PARENT_AUDIT = 'data/main-ancestors14-through10-cap480-pair-sat-v1-independent-actual-audit.json'
INPUT_PINS = {
    PARENT_REPORT: 'e559511714586148aee70e687bed57b6473cad5bb423375be987a6b3be829158',
    PARENT_RECEIPT: '62c803caa83ebabea94dc0e40e18d75e3782b250ee1f6726eb035ac568168d38',
    PARENT_AUDIT: '6749da866f32d19ef531487f4f62aca0ff413246d64f5f4f2b16388942195847',
}
PARENT_AUDIT_HASH = INPUT_PINS[PARENT_AUDIT]
MAP_HASH = '71b8293298da69ac9a959ef3dde69728962acb1d7b35f1fdbb85a15932a08fea'
MASK_HASH = '5e626c17d7b036404ef7bca305320ac88e200c083a0af539103c4ae3706454fe'
FROZEN_SOURCES = {
    'research/near_quarter_ancestors14_through10_cap480.py': '697b101b078389da3b5466cb6f90d26d4f534680137e5fd5d8826b22d8726e98',
    'research/near_quarter_ancestors16_15_cap320.py': 'e9ef1770fc88da3698246240dc3716fbd777a255f6c4f4c44f361c3edb8a40c4',
    'research/near_quarter_ancestor_pair_sat.py': '44b9fce2379ad35ce96aab54dae42d4f68a3800f0ef07e47849760ec8f1ae8c3',
    'research/near_quarter_prefix_pair_sat.py': '08c5b8532666145cb890fae7daf4b62960a09a28e6f8c17536984c6c4b4c70f3',
}


def bounded_variables(mask):
    if any(type(x) is not int or x not in (0, 1) for x in mask):
        raise ValueError('incomplete or invalid mask')
    variables = [i + 1 for i, marked in enumerate(mask) if marked]
    return None if len(variables) > MASK_CAP else variables


def prefix_for_depth(selected, depth):
    if selected != EXPECTED_IDS or depth not in DEPTHS:
        raise ValueError('invalid fixed ancestor identity or depth')
    return selected[:depth + 1]


def capacity_bounds(count):
    if type(count) is not int or not 0 <= count <= MASK_CAP:
        raise ValueError('mask count outside reviewed capacity')
    pairs = count * (count - 1) // 2
    return {'primary_variables': count, 'pair_census': pairs,
            'first_orbit_pushes': max(0, count - 1),
            'degree_variables': 9 * count, 'degree_clauses': 16 * count,
            'degree_literals': 48 * count,
            'final_clauses': 16 * count + pairs + CUT_LIMIT,
            'final_literals': 48 * count + 2 * pairs + 3 * CUT_LIMIT}


def validate_formula(demands, edges, count, clauses, pool):
    if (len(edges) != count or any(type(d) is not int or d not in (0, 1, 2) for d in demands)
            or any(type(u) is not int or type(v) is not int or u == v or not 0 <= u < len(demands) or not 0 <= v < len(demands) for u, v in edges)):
        raise ValueError('invalid complete-mask radius incidence')
    bound = capacity_bounds(count)
    literals = sum(map(len, clauses))
    if (pool.top > min(4500, bound['degree_variables'])
            or len(clauses) > min(8000, bound['degree_clauses'])
            or literals > min(24000, bound['degree_literals'])):
        raise ValueError('degree formula exceeds reviewed dynamic bound')
    return literals


def load_seed(check):
    artifacts = {}
    for path, digest in INPUT_PINS.items():
        check()
        raw = (ROOT / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('continuation input hash mismatch: ' + path)
        artifacts[path] = json.loads(raw)
    report, receipt, audit = (artifacts[p] for p in (PARENT_REPORT, PARENT_RECEIPT, PARENT_AUDIT))
    if (audit['report_sha256'] != INPUT_PINS[PARENT_REPORT]
            or audit['receipt_sha256'] != INPUT_PINS[PARENT_RECEIPT]
            or not audit['accepted'] or audit['complete']
            or not receipt['sources_unchanged'] or report['status'] != 'timeout'):
        raise ValueError('continuation predecessor identity mismatch')
    stages = {s['depth']: s for s in report['stages']}
    reviews = {s['depth']: s for s in audit['stages']}
    if any(stages[d]['status'] != 'unsat_solver_reported' for d in (14, 13)):
        raise ValueError('closed predecessor scope mismatch')
    seed = stages[12]
    if (seed['status'] != 'timeout' or seed['complete']
            or seed['selected_prefix_ids'] != list(EXPECTED_IDS[:13])
            or seed['mask_count'] != 369 or seed['complete_mask_length'] != 1521
            or seed['complete_mask_sha256'] != MASK_HASH
            or seed['pair_started'] != 67896 or seed['pair_completed'] != 67896
            or seed['pair_cuts'] != 9539 or seed['triple_cuts'] != 181
            or reviews[12]['independent_pair_checks'] != 67896
            or reviews[12]['independent_complete_mask_sha256'] != MASK_HASH
            or reviews[12]['independent_ternary_cuts_checked'] != 181
            or seed['pair_cut_ids'] != [r['ids'] for r in reviews[12]['pair_rejection_witnesses']]
            or seed['triple_cut_ids'] != reviews[12]['validated_ternary_cut_ids']):
        raise ValueError('continuation predecessor scope mismatch')
    check()
    return seed


def validate_seed(seed, state, variables, mask_hash, check):
    if (state.map_digest.hex() != MAP_HASH or mask_hash != MASK_HASH
            or variables != seed['orbit_variable_ids']
            or seed['selected_prefix_ids'] != list(EXPECTED_IDS[:13])):
        raise ValueError('seed prefix or complete-map mismatch')
    cuts = [tuple(c) for c in seed['pair_cut_ids']]
    if (len(cuts) != 9539 or len(set(cuts)) != len(cuts)
            or any(len(c) != 2 or any(type(v) is not int for v in c) or not 1 <= c[0] < c[1] <= len(variables) for c in cuts)):
        raise ValueError('invalid seeded binary IDs')
    records = seed['triple_cut_records']
    triples = seed['triple_cut_ids']
    if len(records) != 181 or len(triples) != 181 or len(set(map(tuple, triples))) != 181:
        raise ValueError('invalid seeded ternary count or duplicate')
    for record, ids in zip(records, triples, strict=True):
        check()
        if (record['ids'] != ids or len(ids) != 3 or any(type(v) is not int or not 1 <= v <= len(variables) for v in ids)
                or ids != sorted(set(ids))):
            raise ValueError('invalid seeded ternary IDs')
        points = [tuple(p) for p in record['points']]
        if (len(points) != 3 or len(set(points)) != 3
                or any(len(p) != 2 or any(type(c) is not int or not 0 <= c < 79 for c in p) for p in points)):
            raise ValueError('invalid seeded ternary points')
        a, b, c = points
        if (b[0]-a[0])*(c[1]-a[1]) != (b[1]-a[1])*(c[0]-a[0]):
            raise ValueError('seeded ternary not collinear')
        memberships = [next((v for v in ids if p in state.model['orbits'][variables[v-1]-1]), None) for p in points]
        if None in memberships or sorted(memberships) != ids or set(points) & set(state.points):
            raise ValueError('seeded ternary orbit membership mismatch')
    return cuts


def formula_totals(stage):
    if stage['triple_cuts'] != stage['retained_triple_cuts'] + stage['new_triple_cuts']:
        raise ValueError('retained/new/total ternary count mismatch')
    stage['total_triple_cuts'] = stage['triple_cuts']
    stage['final_clauses'] = stage['degree_clauses'] + stage['pair_cuts'] + stage['triple_cuts']
    stage['final_literals'] = stage['degree_literals'] + 2*stage['pair_cuts'] + 3*stage['triple_cuts']



def solve_models(solver,state,variables,demands,edges,report,check,fired,deadline,clock,out,*,target_points=158,target_orbits=20,cut_limit=1000):
    """Check complete models and add only necessary distinct three-orbit cuts."""
    known={tuple(c) for c in report.get('triple_cut_ids', [])};base_points=set(state.points)
    if len(known)!=report['triple_cuts'] or len(known)>cut_limit:raise ValueError('invalid seeded total budget')
    if len(known)==cut_limit:report['status']='cut_limit';return
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
        if any(a in chosen and b in chosen for a,b in report.get('pair_cut_ids', [])):raise RuntimeError('solver violated binary cut')
        if any(set(c)<=chosen for c in known):raise RuntimeError('solver repeated excluded triple')
        bad=first_bad_triple(points,check)
        if bad is None:
            cert={'n':state.n,'points':[list(point) for point in sorted(points)]}
            checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
            if any(not c['valid'] or c['point_count']!=target_points for c in checks) or checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']:
                raise RuntimeError('witness dual verification failed')
            digest=checks[0]['normalized_sha256']
            cert['metadata']={'method':'exact_depth12_cut_continuation','depth':report.get('depth'),'normalized_sha256':digest,'novelty_claim':False}
            atomic(out/('witness-'+digest+'.json'),encode(cert))
            report['witnesses']=1;report['status']='witness';report['complete']=True;return
        cut=triple_cut(bad,point_to_var)
        if cut in known: raise RuntimeError('solver repeated excluded triple')
        known.add(cut);solver.add_clause([-v for v in cut]);report['triple_cuts']+=1;report['new_triple_cuts']+=1
        report.setdefault('triple_cut_ids',[]).append(list(cut))
        report.setdefault('triple_cut_records',[]).append({'ids':list(cut),'points':[list(p) for p in bad]})
        formula_totals(report)
        if len(known)>=cut_limit:
            report['status']='cut_limit';return



def run(out, seconds, *, clock=time.monotonic):
    from pysat.solvers import Solver
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('invalid shared soft duration')
    start = clock()
    deadline = start + seconds

    def check():
        if clock() >= deadline:
            raise TimeoutError

    local_paths = (Path(__file__).resolve(), ROOT / 'research/near_quarter_factor_shadow.py',
                   ROOT / 'research/near_quarter_readonly_probe.py')
    local_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in local_paths}
    for name, digest in FROZEN_SOURCES.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('frozen helper source changed: ' + name)
    local_hashes.update(FROZEN_SOURCES)
    baseline_manifest = source_manifest()
    report = {'method': 'exact_depth12_cut_continuation_then_fresh11_10',
              'scope': 'Exact audited main12 cut continuation; optional fresh11/10 only after preceding unexpired native UNSAT; no frontier writes.',
              'status': 'incomplete', 'complete': False, 'backend': 'glucose3', 'encoding': 'seqcounter',
              'python_sat_version': version('python-sat'), 'mask_capacity': MASK_CAP,
              'triple_cut_limit_per_stage': CUT_LIMIT, 'shared_soft_seconds': seconds,
              'max_stages': 3, 'pair_census_limit_per_stage': 114960, 'new_pair_census_limit_all_stages': 229920, 'new_ternary_cut_limit_all_stages': 2819,
              'local_source_sha256': local_hashes, 'packed_source_manifest': baseline_manifest,
              'parent_audit_sha256': PARENT_AUDIT_HASH, 'immutable_input_sha256': dict(INPUT_PINS),
              'stages': [{'depth': d, 'status': 'unstarted', 'complete': False,
                          'pair_started': 0, 'pair_completed': 0, 'pair_cuts': 0,
                          'model_count': 0, 'triple_cuts': 0, 'retained_triple_cuts': 0, 'new_triple_cuts': 0, 'total_triple_cuts': 0, 'witnesses': 0} for d in DEPTHS]}
    try:
        seed = load_seed(check)
        selected = EXPECTED_IDS

        def run_depth(stage):
            check()
            depth = stage['depth']
            ids = prefix_for_depth(selected, depth)
            stage['selected_prefix_ids'] = list(ids)
            sample = mask_and_bounds(79, ids, check)
            stage['complete_mask_sha256'] = sample['mask_sha256']
            stage['complete_mask_length'] = len(sample['mask'])
            stage['mask_count'] = sum(sample['mask'])
            if len(sample['mask']) != 1521:raise ValueError('incomplete full mask')
            variables = bounded_variables(sample['mask'])
            if variables is None:
                stage['status'] = 'mask_capacity'
                return
            count = len(variables)
            bound = capacity_bounds(count)
            stage['capacity_bounds'] = bound
            stage['orbit_variable_ids'] = variables
            if len(sample['edges']) != count or sum(sample['demands']) != 2 * (39 - depth):
                raise ValueError('residual incidence or demand mismatch')
            state = PackedOrbitState(79, check=check)
            for variable in ids:
                check()
                if not state.push(variable):
                    raise ValueError('fresh prefix reconstruction failed')
            if len(state.points) != 2 + 4 * depth:
                raise ValueError('retained prefix point count mismatch')
            if depth == 12:
                cuts = validate_seed(seed, state, variables, sample['mask_sha256'], check)
                stage['reused_pair_census'] = 67896
                stage['pair_census_provenance'] = INPUT_PINS[PARENT_REPORT]
                stage['retained_triple_cuts'] = stage['triple_cuts'] = 181
                stage['triple_cut_ids'] = json.loads(json.dumps(seed['triple_cut_ids']))
                stage['triple_cut_records'] = json.loads(json.dumps(seed['triple_cut_records']))
                stage['retained_cut_provenance'] = dict(INPUT_PINS)
            else:
                cuts = incompatible_pairs(state, variables, check, stage)
                if (stage['pair_started'] != bound['pair_census'] or stage['pair_completed'] != bound['pair_census']
                        or len(set(cuts)) != len(cuts)
                        or any(not 1 <= i < j <= count for i, j in cuts)):
                    raise ValueError('incomplete or invalid pair census')
            stage['pair_cuts'] = len(cuts)
            stage['pair_cut_ids'] = [list(c) for c in cuts]
            try:
                clauses, pool = degree_clauses(sample['demands'], sample['edges'], check)
            except ValueError as error:
                if str(error) == 'degree shortfall':
                    stage['status'] = 'degree_shortfall'
                    return
                raise
            literals = validate_formula(sample['demands'], sample['edges'], count, clauses, pool)
            stage['degree_variables'] = pool.top
            stage['degree_clauses'] = len(clauses)
            stage['degree_literals'] = literals
            if depth == 12 and (pool.top, len(clauses), literals) != (2823, 5002, 11814):
                raise ValueError('seeded degree formula identity mismatch')
            formula_totals(stage)
            if depth == 12:
                stage['starting_formula_clauses'] = 14722
                stage['starting_formula_literals'] = 31435
                stage['maximum_formula_clauses'] = 15541
                stage['maximum_formula_literals'] = 33892
            solver = timer = None
            fired = Event()
            try:
                check()
                solver = Solver(name='glucose3')
                for clause in clauses:
                    check()
                    solver.add_clause(clause)
                for i, j in cuts:
                    check()
                    solver.add_clause([-i, -j])
                for cut in stage.get('triple_cut_ids', []):
                    check()
                    solver.add_clause([-v for v in cut])
                remaining = deadline - clock()
                if remaining <= 0:
                    raise TimeoutError

                def interrupt():
                    fired.set()
                    solver.interrupt()

                timer = Timer(remaining, interrupt)
                timer.daemon = True
                timer.start()
                solve_models(solver, state, variables, sample['demands'], sample['edges'], stage,
                             check, fired, deadline, clock, out, target_orbits=39 - depth, cut_limit=CUT_LIMIT)
            finally:
                dispose_solver(timer, solver)

        adaptive_loop(report, run_depth)
    except TimeoutError:
        report['status'] = 'timeout'
        for stage in report['stages']:
            if stage['status'] == 'incomplete':
                stage['status'] = 'timeout'
                break
    # Immutable evidence/source rereads also run on cooperative timeout; the
    # unchanged owned outer gate bounds this integrity/publication tail.
    for path, digest in INPUT_PINS.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('immutable continuation input changed')
    if source_manifest() != baseline_manifest or any(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h for p, h in local_hashes.items()):
        raise ValueError('source changed during depth12 continuation')
    report['elapsed_seconds'] = clock() - start
    atomic(out / 'report.json', encode(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = run(args.output_dir, args.seconds)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] in ('witness', 'all_ancestors_unsat_solver_reported') else 2


if __name__ == '__main__':
    sys.exit(main())
