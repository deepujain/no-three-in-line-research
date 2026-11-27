"""Read-only identity/receipt audit; never imports or invokes a proof checker."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/direct-owned-saved-proof-source-pins.json'
MANIFEST_SHA = 'c23be802dc10b07bd6981f2c6a9c92086cb7d3d5fa280c8f4440311b86aa85d3'
REPORT = 'data/direct-owned-saved-proof-v1/report.json'
RECEIPT = 'data/experiments/shepherd-direct-owned-saved-proof-v1.json'
LOG = 'data/direct-owned-saved-proof-v1/worker.log'
RUNTIME = 'data/fixed-pool-boolean-scaffold-runtime-pins.json'
RUNTIME_SHA = '1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a'
CNF = 'data/fixed-pool-boolean-scaffold157-v1/scaffold.cnf'
CNF_SHA = '855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9'
PROOF = 'data/fixed-pool-boolean-scaffold157-v1/scaffold.rup'
PROOF_SHA = '4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e'


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_bytes())


def main():
    assert sha(MANIFEST) == MANIFEST_SHA
    assert sha(RUNTIME) == RUNTIME_SHA
    manifest, runtime = read(MANIFEST), read(RUNTIME)
    report, receipt = read(REPORT), read(RECEIPT)
    for pins in (manifest, runtime['pins'], receipt['sources_before']):
        for name, expected in pins.items():
            assert sha(name) == expected, name
    assert receipt['sources_before'] == manifest
    assert receipt['source_manifest_sha256'] == MANIFEST_SHA
    assert receipt['status'] == 'completed'
    assert receipt['parent_acceptance'] is True and receipt['sources_unchanged'] is True
    assert receipt['reserved_owned_seconds'] == receipt['reserved_parent_validation_seconds'] == 5
    assert 0 < receipt['elapsed_seconds'] < 10
    argv = [runtime['interpreter'], str(ROOT / 'research/direct_owned_saved_proof.py'),
            '--source-pins', str(ROOT / MANIFEST), '--source-pins-sha256', MANIFEST_SHA, '--seconds', '4']
    assert receipt['argv'] == argv
    raw = (ROOT / LOG).read_bytes()
    assert 0 < len(raw) < 65536 and raw.endswith(b'\n')
    worker = json.loads(raw.decode('ascii'))
    assert worker == report['worker_receipt']
    assert sha(LOG) == report['log_sha256'] == receipt['owned_log_sha256']
    assert len(raw) == report['log_bytes']
    assoc = report['caller_log_association']
    assert assoc['absolute_path'] == receipt['owned_log_path'] == str(ROOT / LOG)
    assert assoc['sha256'] == sha(LOG) and assoc['argv'] == argv
    assert assoc['job_id'] == receipt['job']['id'] == 'shepherd-direct-owned-saved-proof-v1'
    assert assoc['single_owned_guard_call'] is True
    gate = receipt['gate']
    assert gate == report['owned_gate']
    assert report['canonical_guard_sha256'] == hashlib.sha256(
        json.dumps(gate, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert gate['gate_status'] == 'exited' and type(gate['returncode']) is int and gate['returncode'] == 0
    assert gate['cleanup_status'] == 'clean'
    assert gate['cleanup_error'] is gate['monitor_error'] is gate['trigger_gate_status'] is None
    assert gate['seconds_limit'] == 5 and gate['rss_limit_mib'] == 256
    assert 0 < gate['elapsed_seconds'] < 5 and 0 <= gate['cleanup_elapsed_seconds'] <= 1
    assert 0 < gate['peak_sampled_rss_kib'] <= 256*1024 and gate['rss_samples'] > 0
    assert report['accepted'] is report['closure'] is report['independent_parent_pins_verified'] is True
    assert report['status'] == 'certified_saved_fixed_pool_unsat'
    assert report['source_pins_sha256'] == worker['source_pins_sha256'] == MANIFEST_SHA
    assert worker['accepted'] is worker['closure'] is worker['identity_valid'] is True
    assert worker['pins_verified_before'] is worker['pins_verified_after'] is True
    assert worker['status'] == 'checked_direct_owned_saved_proof'
    assert worker['protocol'] == 'direct-owned-monotonic-rup-v1'
    assert worker['runtime_manifest_sha256'] == RUNTIME_SHA
    assert worker['checker_invocations'] == 1 and worker['sat_invocations'] == 0
    assert worker['log_cap_bytes'] == 65536 and worker['cooperative_seconds'] == 4
    assert 0 < worker['elapsed_seconds'] < 4
    identity = worker['owned_identity']
    assert identity['pid'] == identity['pgid'] == identity['sid'] > 0
    assert identity['shared_regular_log'] is True
    assert worker['checker_origin'] == str(ROOT / 'research/monotonic_rup_checker.py')
    assert worker['checker_sha256'] == report['checker_sha256'] == sha('research/monotonic_rup_checker.py')
    proof = worker['proof_check']
    assert proof['accepted'] is proof['closure'] is proof['full_parse_complete'] is True
    assert proof['status'] == 'checked_monotonic_rup_unsat'
    assert proof['failure_line'] is proof['failure_clause'] is None
    assert proof['cnf_sha256'] == proof['expected_cnf_sha256'] == report['cnf_sha256'] == sha(CNF) == CNF_SHA
    assert proof['proof_sha256'] == proof['expected_proof_sha256'] == report['proof_sha256'] == sha(PROOF) == PROOF_SHA
    assert proof['cnf_bytes'] == (ROOT / CNF).stat().st_size == 187965
    assert proof['proof_bytes'] == (ROOT / PROOF).stat().st_size == 44475
    assert proof['records'] == proof['checked_empty_line'] == 2891
    assert proof['additions'] == 180 and proof['deletions'] == 2711
    assert proof['records'] == proof['additions'] + proof['deletions']
    old = read('data/fixed-pool-boolean-scaffold157-v1/report.json')
    assert old['cnf']['sha256'] == CNF_SHA and old['cnf']['variables'] == proof['variables'] == 2645
    assert proof['retained_clauses'] == old['cnf']['clauses'] + proof['additions'] == 13294
    assert proof['active_clauses'] == proof['retained_clauses'] - proof['deletions'] == 10583
    assert proof['retained_literals'] == 34044 and proof['work'] == 41899584 <= 50000000
    assert len(old['pool']) == 64 and old['support_arc_count'] == 246 and old['seed_count'] == 8
    assert old['fixed_preprocessing_complete'] is old['source_validation_complete'] is old['identity_valid'] is True
    result = {
        'passed': True, 'audit': 'receipt/log/hash/scope only; no checker or SAT rerun',
        'manifest_pins_checked': len(manifest), 'runtime_pins_checked': len(runtime['pins']),
        'receipt_source_pins_checked': len(receipt['sources_before']),
        'artifacts': {name: sha(name) for name in (MANIFEST, REPORT, RECEIPT, LOG, CNF, PROOF)},
        'guard': gate, 'worker_elapsed_seconds': worker['elapsed_seconds'],
        'receipt_total_elapsed_seconds': receipt['elapsed_seconds'],
        'proof_receipt': proof,
        'scope': 'Certified UNSAT only for exact immutable fixed64-cell/246-support eight-support scaffold CNF. No149/157 witness, unrestricted exclusion, other pool, or new bound.',
        'provenance_limit': 'Caller job/log association is recorded and consistent; historical guard does not independently bind log path/hash or PID.'}
    output = ROOT / 'data/direct-owned-proof-independent-actual-audit.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'manifest_pins_checked', 'runtime_pins_checked', 'receipt_source_pins_checked', 'artifacts')}, indent=2))


if __name__ == '__main__':
    main()
