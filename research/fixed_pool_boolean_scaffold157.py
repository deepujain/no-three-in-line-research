"""One bounded Boolean gate on the immutable audited 64-cell scaffold pool.

Actual execution requires a separate lead allocation and the unchanged owned
30s/256MiB guard. Importing this module performs no fixed-input reconstruction.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import boolean_scaffold_cnf as cnf
from research import boolean_scaffold_native as native
from research import blocker_guided_eight_arc_scaffold157 as old
prior = old.prior
frozen = old.frozen
REPORT = 'data/blocker-guided-eight-arc-scaffold157-v1/report.json'
FIXED = {
    'research/blocker_guided_eight_arc_scaffold157.py': '5af488fa4f857cb91325677eff67034bb2fcf6f7ed30a32e97ec018808e11b39',
    'research/conflict_directed_sixteen_cycle_rebuild157.py': '714c389795cb3250a13e969910b671e9acb47ffd9054c4754c6ad84b5124dab7',
    'research/source_disjoint_matching_rebuild157.py': '56248d90b13b45dfe6cefbf605cfc9a61e601fffe2f5332217b1cbd2c0f62a09',
    REPORT: 'b98c5d0b4b228d3bba4f625bd1f5e40891db178cd63296f2bb0cffefedb8aea9',
    'data/blocker-guided-eight-arc-scaffold157-v1-independent-actual-audit.json': '828ae6c503a4fe37d8d84b39b9cddf531e747cad7fbf1adc340fdbd108b7564c',
    'research/blocker_guided_eight_arc_scaffold_independent_actual_audit.py': 'c2e712976923f4b04e3a292682b2a848e404d7cca2ef1f34d8a86bda6105a3e3',
}
DESCRIPTORS = '78f575d75e81f2de64bb95fbf411540a0fc57bb1ac8d17d469cefbc549a06d88'
TABLES = 'd901f6448c3910cfd3ebc32c16288871fa224223b87ef1e339bf299addc2d104'


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode()).hexdigest()


def load_fixed(check, pins, report):
    for name, expected in FIXED.items():
        check(); path = ROOT/name
        if cnf.digest(path) != expected: raise ValueError('fixed pin mismatch: '+name)
        pins[str(path)] = expected
    A, S, triples, validation = prior.load_sources(check, pins)
    A = tuple(sorted(A)); saved = json.loads((ROOT/REPORT).read_text()); c = report['counters']
    records = saved['pool']
    if len(records) != 64: raise ValueError('pool cardinality')
    pool = []
    for record in records:
        check(); point = tuple(record['point']); lower = record['lower']
        if (len(point) != 2 or any(type(v) is not int or not 0 <= v < 79 for v in point)
                or point in S or type(lower) is not int): raise ValueError('pool record')
        buckets = old.partition(A, point, c, check)
        if any(mask.bit_count() > 4 for mask in buckets) or sum(mask.bit_count()-1 for mask in buckets) != lower:
            raise ValueError('saved pool L mismatch')
        pairs = sorted(pair for mask in buckets for pair in combinations(cnf.bits(mask), 2))
        pool.append(old.PoolCell(point, lower, buckets, tuple((1 << a) | (1 << b) for a, b in pairs)))
    pool = tuple(pool)
    if len({p.point for p in pool}) != 64 or Counter(p.lower for p in pool) != {2: 2, 3: 24, 4: 38}:
        raise ValueError('pool identity/histogram')
    domains = [0]*79
    for p in pool: domains[p.point[0]] |= 1 << p.point[1]
    frozen.validate_matching_cover(domains, 79, saved['pool_matching_cover'], check, c)
    if saved['pool_matching_cover']['matching_size'] != 24: raise ValueError('pool capacity certificate')
    arcs = old.make_arcs(A, pool, c, check); tables = old.make_tables(A, pool, c, check)
    descriptors = [(pool[e.pool].lower, pool[e.pool].point, A[e.a], A[e.b]) for e in arcs]
    table_records = [[i, j, hex(a), hex(b)] for (i, j), (a, b) in sorted(tables.items())]
    if len(arcs) != 246 or canonical_sha(descriptors) != DESCRIPTORS or canonical_sha(table_records) != TABLES:
        raise ValueError('audited support/table identity mismatch')
    report.update(source_validation_complete=True, fixed_preprocessing_complete=True,
                  input_validation=validation, pool=[{'point': p.point, 'lower': p.lower} for p in pool],
                  descriptor_sha256=DESCRIPTORS, table_sha256=TABLES, support_arc_count=len(arcs))
    return A, S, pool, arcs, tables, old.conflict_masks(A, triples)


def save_scaffold(n, A, S, pool, arcs, tables, conflicts, selected, out, report, check, pins):
    """Independent semantic reconstruction, dual validation, immediate save."""
    selected, Q, supports, F, R, P, forced = old.scaffold(A, S, pool, arcs, selected, conflicts, tables, check)
    k = len(selected); Pset = set(P); Sset = set(S)
    if (k != report['seed_count'] or len(P) != len(A)-k or len(Sset-Pset) != 2*k+1
            or len(Pset-Sset) != k or Pset & Sset != set(R)):
        raise ValueError('decoded scaffold source/count invariant')
    expected = tuple(side.copy() for side in prior.axes(A, n))
    for a, b in supports: expected[0][b[0]] -= 1; expected[1][a[1]] -= 1
    if prior.axes(P, n) != expected: raise ValueError('decoded scaffold axes')
    native.verify_pins(pins)
    cert, validators = frozen.dual_valid(P, n, check)
    metadata = {'method': 'fixed_pool_boolean_scaffold157', 'kind': 'valid_scaffold_diagnostic',
                'valid': True, 'point_count': len(P), 'source_deleted': len(Sset-Pset),
                'source_retained': len(Pset & Sset), 'new_points_outside_source': len(Pset-Sset),
                'is_full_witness': False, 'improves_verified_lower_bound': False,
                'root_ready': False, 'residual_plan_joint_geometry_checked': False,
                'selected_arc_indices': list(selected), 'deleted_from_A': F, 'planted': Q,
                'supports': supports, 'normalized_sha256': validators[0]['normalized_sha256'],
                'cnf': report['cnf'], 'pins': dict(pins)}
    cert.update(metadata=metadata, validators=validators)
    # No deadline, pin hash or optional root operation between validator2 and save.
    frozen.atomic(out/'valid149-diagnostic.json', cert)
    report.update(diagnostic_saved=True, diagnostic_complete=True,
                  diagnostic_normalized_sha256=validators[0]['normalized_sha256'])
    return cert, Q, supports, F, R, P, forced


def optional_root(n, A, S, decoded, out, report, check, pins):
    cert, Q, supports, F, R, P, forced = decoded
    check()  # Fresh deadline after the diagnostic was saved.
    root = {'complete': False, 'scope': 'Only this single returned scaffold.',
            'residual_plan_joint_geometry_checked': False}
    report['root'] = root; c = report['counters']
    domains = old.residual_domains(n, P, S, supports, c, check, root)
    cover = frozen.maximum_matching(domains, len(Q), c, check)
    root.update(matching_complete=True, matching_cover=cover)
    if cover['matching_size'] < len(Q):
        root.update(status='matching_obstruction', complete=True); return False
    tau = old.root_cycle(domains, c, check)
    root.update(cycle_complete=True, tau=tau)
    if tau is None: root.update(status='cycle_obstruction', complete=True); return False
    frozen.validate_matching_cover(domains, len(Q), cover, check, c)
    plan = tuple((supports[i][1][0], supports[tau[i]][0][1]) for i in range(len(Q)))
    if (not prior.single_cycle(tau) or not prior.matching_cells(plan) or set(plan) & (set(S) | set(Q))
            or any(not domains[i] >> tau[i] & 1 for i in range(len(Q)))
            or prior.axes(set(P) | set(plan), n) != prior.axes(A, n)):
        raise ValueError('root readiness invariant')
    check(); native.verify_pins(pins)
    ready = dict(cert); ready['metadata'] = dict(cert['metadata'], kind='root_ready_scaffold',
        root_ready=True, residual_domains=[list(cnf.bits(v)) for v in domains],
        residual_matching_cover=cover, tau=tau, residual_plan=plan,
        residual_plan_joint_geometry_checked=False)
    frozen.atomic(out/'root-ready149.json', ready)
    root.update(status='ready', complete=True); report['ready_saved'] = True
    return True


def child_json(result):
    if result['reason'] != 'exited' or result['returncode'] != 0 or not result['cleanup']['clean']:
        raise RuntimeError('native child incomplete: '+result['reason'])
    obj = json.loads(result['stdout'])
    if not isinstance(obj, dict): raise ValueError('native response')
    return obj


def execute(n, A, S, pool, arcs, tables, conflicts, out, report, check, pins, deadline,
            *, clock=time.monotonic, seed_count=8):
    layout = cnf.Layout(len(arcs), len(pool), len(A), seed_count)
    report['seed_count'] = seed_count; check()
    path = out/'scaffold.cnf'
    report['cnf'] = cnf.write_cnf(path, A, pool, arcs, tables, conflicts, layout, check, report['counters'])
    formula_sha = report['cnf']['sha256']; pins[str(path)] = formula_sha
    check(); seconds = min(10, deadline-clock()-3)
    if seconds <= 0: raise TimeoutError('no SAT slice before validation reserve')
    proof = out/'scaffold.rup'
    command = [sys.executable, str(ROOT/'research/boolean_scaffold_native.py'), '--cnf', str(path),
               '--proof', str(proof), '--cnf-sha256', formula_sha]
    report['sat_invocations'] += 1
    sat = native.run_child(command, seconds, pins, latest_end=deadline-3); report['sat_process'] = sat
    answer = child_json(sat)
    if (answer.get('cnf_sha256') != formula_sha or answer.get('pgid') != os_group()
            or answer.get('sid') != os_session()): raise ValueError('native binding/session mismatch')
    if answer.get('answer') == 'SAT':
        check(); values = cnf.parse_model(answer['model'], layout.variables)
        selected = cnf.verify_model(values, A, pool, arcs, tables, conflicts, layout, check)
        decoded = save_scaffold(n, A, S, pool, arcs, tables, conflicts, selected, out, report, check, pins)
        report['status'] = 'valid_scaffold'
        if optional_root(n, A, S, decoded, out, report, check, pins): report['status'] = 'root_ready'
        report['complete'] = True
    elif answer.get('answer') == 'UNSAT':
        report.update(status='unverified_unsat', closure=False)
        if not proof.is_file() or not 0 < proof.stat().st_size < native.PROOF_CAP:
            raise ValueError('missing/capped proof')
        proof_sha = cnf.digest(proof)
        if proof_sha != answer.get('proof_sha256') or proof.stat().st_size != answer.get('proof_bytes'):
            raise ValueError('native proof binding')
        pins[str(proof)] = proof_sha; check(); seconds = min(5, deadline-clock()-1)
        if seconds <= 0: raise TimeoutError('no independent checker slice')
        command = [sys.executable, str(ROOT/'research/bounded_rup_checker.py'), '--cnf', str(path),
                   '--proof', str(proof), '--cnf-sha256', formula_sha, '--proof-sha256', proof_sha,
                   '--seconds', str(seconds)]
        report['checker_invocations'] += 1
        checked = native.run_child(command, seconds, pins, latest_end=deadline-1); report['checker_process'] = checked
        receipt = child_json(checked)
        if (receipt.get('accepted') is not True or receipt.get('cnf_sha256') != formula_sha
                or receipt.get('proof_sha256') != proof_sha): raise ValueError('checker acceptance binding')
        report.update(status='checked_fixed_pool_unsat', complete=True, closure=True, proof_check=receipt)
    else: raise ValueError('native answer')


def os_group():
    import os
    return os.getpgrp()


def os_session():
    import os
    return os.getsid(0)


def run(out, source_manifest, runtime_manifest, seconds=25, *, started=None, clock=time.monotonic):
    if isinstance(seconds, bool) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('shared duration')
    start = clock() if started is None else started; deadline = start+seconds
    def check():
        if clock() >= deadline: raise TimeoutError('shared soft deadline')
    report = {'method': 'fixed_pool_boolean_scaffold157', 'n': 79, 'status': 'incomplete',
              'complete': False, 'closure': False, 'shared_soft_seconds': seconds,
              'sat_invocations': 0, 'checker_invocations': 0, 'diagnostic_saved': False,
              'diagnostic_complete': False, 'ready_saved': False, 'counters': old.new_counters(),
              'scope': 'Only immutable audited64-cell/246-support fixed-pool scaffold family; '
                       'one SAT call, optional proof checker and at most one residual root. '
                       'No157 witness, baseline improvement, retry or automatic continuation.'}
    pins = {}
    try:
        check()
        sources = json.loads(Path(source_manifest).read_text())
        runtime = native.runtime_contract(runtime_manifest)
        pins.update({str(ROOT/path): sha for path, sha in sources.items()}); pins.update(runtime['pins'])
        required = {str(Path(__file__).resolve()), str(ROOT/'research/boolean_scaffold_cnf.py'),
                    str(ROOT/'research/boolean_scaffold_native.py'), str(ROOT/'research/bounded_rup_checker.py'),
                    str(ROOT/'src/verify.py'), str(Path(sys.executable).resolve())}
        if not required <= pins.keys() or runtime['backend'] != 'PySAT Glucose3 1.8.dev24':
            raise ValueError('missing reviewed backend/source pins')
        for manifest in (source_manifest, runtime_manifest): pins[str(Path(manifest).resolve())] = cnf.digest(manifest)
        check(); native.verify_pins(pins)
        inputs = load_fixed(check, pins, report)
        execute(79, *inputs, out, report, check, pins, deadline, clock=clock)
    except TimeoutError as error:
        report.update(status='timeout', complete=False, closure=False, error=str(error))
    except Exception as error:
        report.update(status='error', complete=False, closure=False, error=f'{type(error).__name__}: {error}')
    try: native.verify_pins(pins)
    except Exception as error:
        report.update(status='error', complete=False, closure=False, identity_valid=False,
                      error='final pin verification: '+str(error))
    else: report['identity_valid'] = True
    report.update(pins=pins, elapsed_seconds=clock()-start)
    frozen.atomic(out/'report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--seconds', type=float, default=25)
    p.add_argument('--source-pins', type=Path, required=True); p.add_argument('--runtime-pins', type=Path, required=True)
    a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(a.output_dir, a.source_pins, a.runtime_pins, a.seconds, started=ENTRY_STARTED)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['status'] == 'error' else 0 if report['complete'] else 2


if __name__ == '__main__': sys.exit(main())
