"""Fresh pair SAT at fixed main ancestors14 through10, capacity480, at most five stages."""
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
from research.near_quarter_factor_shadow import prefix_paths, mask_and_bounds
from research.near_quarter_ancestor_pair_sat import solve_models, adaptive_loop
from research.near_quarter_prefix_pair_sat import EXPECTED_IDS, incompatible_pairs, degree_clauses, dispose_solver
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_packed_worker import source_manifest
from research.diagonal_secant_checkpoint import atomic, encode

DEPTHS = (14, 13, 12, 11, 10)
MASK_CAP = 480
CUT_LIMIT = 1000
PARENT_AUDIT = 'data/main-ancestors16-15-cap320-pair-sat-v1-independent-actual-audit.json'
PARENT_AUDIT_HASH = '819a813869d14441c3f00b119478cb42d4c3564de90249b4489a9709d7542c27'
FROZEN_SOURCES = {
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


def load_parent_audit(check):
    check()
    raw = (ROOT / PARENT_AUDIT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_AUDIT_HASH:
        raise ValueError('parent actual audit hash mismatch')
    audit = json.loads(raw)
    stages = {s['depth']: s for s in audit['stages']}
    if (not audit.get('accepted') or not audit.get('complete')
            or any(stages[d]['status'] != 'unsat_solver_reported' for d in (16, 15))
            or stages[16]['admissible_orbits'] != 224 or stages[15]['admissible_orbits'] != 256
            or stages[16]['independent_pair_checks'] != 24976 or stages[15]['independent_pair_checks'] != 32640):
        raise ValueError('accepted predecessor scope mismatch')
    check()
    return stages



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
    report = {'method': 'fixed_main_ancestors14_through10_cap480_pair_sat',
              'scope': 'Only main depths14,13,12,11,10; each next stage requires preceding unexpired native UNSAT; no below10 or frontier writes.',
              'status': 'incomplete', 'complete': False, 'backend': 'glucose3', 'encoding': 'seqcounter',
              'python_sat_version': version('python-sat'), 'mask_capacity': MASK_CAP,
              'triple_cut_limit_per_stage': CUT_LIMIT, 'shared_soft_seconds': seconds,
              'max_stages': 5, 'pair_census_limit_per_stage': 114960, 'pair_census_limit_all_stages': 574800,
              'local_source_sha256': local_hashes, 'packed_source_manifest': baseline_manifest,
              'parent_audit_sha256': PARENT_AUDIT_HASH,
              'stages': [{'depth': d, 'status': 'unstarted', 'complete': False,
                          'pair_started': 0, 'pair_completed': 0, 'pair_cuts': 0,
                          'model_count': 0, 'triple_cuts': 0, 'witnesses': 0} for d in DEPTHS]}
    pins = []
    try:
        load_parent_audit(check)
        paths, pins = prefix_paths(check)
        selected = next(ids for label, depth, ids in paths if label == 'main' and depth == 19)
        if selected != EXPECTED_IDS:
            raise ValueError('immutable main19 prefix identity mismatch')

        def run_depth(stage):
            check()
            depth = stage['depth']
            ids = prefix_for_depth(selected, depth)
            stage['selected_prefix_ids'] = list(ids)
            sample = mask_and_bounds(79, ids, check)
            stage['complete_mask_sha256'] = sample['mask_sha256']
            stage['complete_mask_length'] = len(sample['mask'])
            stage['mask_count'] = sum(sample['mask'])
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
    for path, digest in pins:
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('immutable prefix input changed')
    if hashlib.sha256((ROOT / PARENT_AUDIT).read_bytes()).hexdigest() != PARENT_AUDIT_HASH:
        raise ValueError('parent actual audit changed')
    if source_manifest() != baseline_manifest or any(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h for p, h in local_hashes.items()):
        raise ValueError('source changed during capacity480 adapter')
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
