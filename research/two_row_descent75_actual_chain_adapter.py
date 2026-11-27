"""Fixed pilot adapter: execute only under Root's separate owned audit allocation."""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import two_row_descent_independent_chain_audit as chain

REPORT = 'data/two-row-descent75-v1/report.json'
RECEIPT = 'data/experiments/shepherd-two-row-descent75-v1.json'
MANIFEST = 'data/two-row-descent75-source-pins.json'
BOUNDARY = 'data/two-row-descent75-v1/completed-boundary.json'
EXPECTED = {
    REPORT:'0ddef4aabd00a0ee8ec171e4da17d3ba19ce0647d0f71fa4760b917f13ab2e7e',
    RECEIPT:'2c72b6edd9569216f678af382bb9fc9dd3a403b397b641937099933056919a6d',
    MANIFEST:'f2ad8a6c66780a945af18aace66fb388cc9d4555294f88457c5c903132f82a35',
    BOUNDARY:'ac3b911614a61f85737615884198373db23ec48453ab4435da06c578d84e8076',
}
WORKER_SHA = '0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
HELPER_SHA = 'd0e558e507f74bb4384ddb582d726235e0518fad61b164cc0e72bac99ddc5f59'
INITIAL_ID = '4312bb212dd558efd0f6eb573baa40f3ad19de2b1537e11e7be734fb14b4f168'
FINAL_ID = '25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c'
HANDOFF_SHA = 'e1941ac155bfb723d22835ced79c731644bb3ec426b5df3046c091585300431a'


def digest(path,check):
    check(); h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); block = stream.read(65536)
            if not block:
                return h.hexdigest()
            h.update(block)


def normalized_pins(values):
    if type(values) is not dict or not 1 <= len(values) <= 512:
        raise ValueError('pin mapping')
    pins = {}
    for name,sha in values.items():
        if type(name) is not str or type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('pin schema')
        key = str((ROOT/name).resolve())
        if key in pins:
            raise ValueError('duplicate normalized pin')
        pins[key] = sha
    return pins


def clean_receipt(report,job):
    argv = [str(ROOT/'.venv/bin/python'),'research/two_row_descent75.py','--seconds','25',
            '--output-dir','data/two-row-descent75-v1','--source-pins',MANIFEST]
    if (job.get('argv') != argv or job.get('status') != 'completed' or job.get('sources_unchanged') is not True
            or job.get('source_manifest_sha256') != EXPECTED[MANIFEST]):
        raise ValueError('receipt association')
    gate = job.get('gate')
    integer_keys = ('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')
    if type(gate) is not dict or any(type(gate.get(k)) is not int for k in integer_keys):
        raise ValueError('guard schema')
    if (gate.get('gate_status') != 'exited' or gate['returncode'] != 0 or gate.get('cleanup_status') != 'clean'
            or any(gate.get(k) is not None for k in ('cleanup_error','monitor_error','trigger_gate_status'))
            or gate['seconds_limit'] != 30 or gate['rss_limit_mib'] != 256
            or not 0 < gate['peak_sampled_rss_kib'] <= 256*1024 or gate['rss_samples'] < 1 or gate['cleanup_samples'] < 1):
        raise ValueError('unclean pilot guard')
    times = [report.get('elapsed_seconds'),gate.get('elapsed_seconds'),job.get('elapsed_seconds')]
    if (any(type(x) not in (int,float) or not math.isfinite(x) for x in times)
            or not 0 <= times[0] < 25 or not 0 < times[1] < 30 or not times[0] <= times[1] <= times[2] <= 30):
        raise ValueError('pilot elapsed binding')
    return {'elapsed_seconds':gate['elapsed_seconds'],'peak_sampled_rss_kib':gate['peak_sampled_rss_kib'],
            'rss_note':'Sampled RSS observation; not a proved unsampled maximum.'}


def audit(check):
    if digest(chain.__file__,check) != HELPER_SHA:
        raise ValueError('auditor helper identity')
    audit_source_sha = digest(__file__,check)
    docs = {name:chain.authenticated_json(ROOT/name,sha,check) for name,sha in EXPECTED.items()}
    report,job,manifest,boundary = (docs[p] for p in (REPORT,RECEIPT,MANIFEST,BOUNDARY))
    pins = normalized_pins(manifest); manifest_path = str((ROOT/MANIFEST).resolve())
    if manifest_path in pins:
        raise ValueError('manifest self pin')
    pins[manifest_path] = EXPECTED[MANIFEST]
    if pins != normalized_pins(report.get('pins')) or pins != normalized_pins(job.get('sources_before')):
        raise ValueError('pilot pin-set association')
    runtime = str(Path(sys.executable).resolve())
    if (pins.get(str(ROOT/'research/two_row_descent75.py')) != WORKER_SHA
            or runtime not in pins or str(ROOT/'src/verify.py') not in pins
            or pins.get(str(ROOT/'data/two-row-descent75-input-identities.json')) != HANDOFF_SHA):
        raise ValueError('mandatory worker/runtime/handoff pins')
    for path,sha in pins.items():
        if digest(path,check) != sha:
            raise ValueError('pilot source/input/runtime drift')
    resource = clean_receipt(report,job)
    if (report.get('method') != 'exact_raw_two_row_descent75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('boundary_saved') is not True
            or report.get('closure') is not False or report.get('witness_saved') is not False
            or report.get('status') != 'pair_cap' or report.get('n') != 75 or report.get('k') != 149
            or report.get('row_cap') != 512 or report.get('pair_cap') != 32
            or report.get('soft_seconds') != 25 or report.get('search_seconds') != 23
            or report.get('validation') != 'invalid_research_state'
            or report.get('boundary_sha256') != EXPECTED[BOUNDARY]
            or report.get('boundary_bytes') != (ROOT/BOUNDARY).stat().st_size):
        raise ValueError('fixed pilot report association')
    if (boundary.get('state') != report.get('state') or boundary.get('improvements') != report.get('improvements')
            or boundary.get('policy') != {'row_cap':512,'pair_cap':32}
            or boundary.get('validation') != 'invalid_research_state' or boundary.get('handoff') != report.get('handoff')):
        raise ValueError('boundary/report policy binding')
    handoff = report.get('handoff')
    if (type(handoff) is not dict or handoff.get('handoff_sha256') != HANDOFF_SHA
            or handoff.get('normalized_sha256') != INITIAL_ID or handoff.get('score') != 97):
        raise ValueError('fixed best97 handoff')
    state = report['state']
    if (state.get('status') != 'pair_cap' or state.get('accepted') != 28
            or state.get('row_started') != 308 or state.get('row_completed') != 308
            or state.get('pair_started') != 32 or state.get('pair_completed') != 32
            or state.get('row_sweep_complete') is not True or state.get('pair_scan_complete') is not False):
        raise ValueError('fixed pilot counter/status claims')
    records = report.get('improvements')
    if type(records) is not list or len(records) != 28:
        raise ValueError('complete28-improvement list required')
    snapshots = {}; improvements = []
    for ordinal,meta in enumerate(records,1):
        name = f'data/two-row-descent75-v1/improvement-{ordinal:03d}.json'
        if meta.get('path') != name or meta.get('kind') != 'row':
            raise ValueError('ordered fixed artifact path/kind')
        item = chain.authenticated_json(ROOT/name,meta.get('sha256'),check)
        if meta.get('bytes') != (ROOT/name).stat().st_size:
            raise ValueError('improvement byte count')
        for key in ('score','before_score','before_normalized_sha256','normalized_sha256','kind','rows'):
            if item.get(key) != meta.get(key):
                raise ValueError('improvement/report record binding')
        snapshots[name] = meta['sha256']; improvements.append(item)
    initial_name = 'data/two-row-descent75-v1/initial.json'
    initial_sha = digest(ROOT/initial_name,check)
    initial = chain.authenticated_json(ROOT/initial_name,initial_sha,check)
    if initial.get('handoff') != handoff or initial.get('classification') != 'dual_checked_invalid_research_state':
        raise ValueError('initial provenance binding')
    snapshots[initial_name] = initial_sha
    result = chain.audit_chain(initial,improvements,boundary,n=75,expected_initial_identity=INITIAL_ID,
                               expected_initial_score=97,max_states=29,check=check)
    if (result['scores'][-1] != 65 or result['states'][-1]['normalized_sha256'] != FINAL_ID
            or report.get('current_unweighted') != 65 or report.get('best_unweighted') != 65
            or result['zero_geometry_verified']):
        raise ValueError('independent final65 association')
    for path,sha in pins.items():
        if digest(path,check) != sha:
            raise ValueError('post-audit pilot pin drift')
    for name,sha in {**EXPECTED,**snapshots}.items():
        if digest(ROOT/name,check) != sha:
            raise ValueError('post-audit artifact drift')
    if digest(chain.__file__,check) != HELPER_SHA or digest(__file__,check) != audit_source_sha:
        raise ValueError('audit source drift')
    check()
    return {'accepted':True,'scope':'Independent saved29-state determinant audit; no optimizer or trajectory search replay.',
            'chain':result,'pilot_resources':resource,'pilot_pins_checked':len(pins),'pilot_artifact_hashes':EXPECTED,
            'audited_chain_artifact_hashes':snapshots,'audit_source_sha256':audit_source_sha,
            'chain_helper_sha256':HELPER_SHA,'runtime_path':runtime,'runtime_sha256':pins[runtime],
            'final_status':'pair_cap','row_sweep_execution_claim':True,'pair_scan_complete':False,
            'local_minimum_claim':'None independently established;32-pair cap is partial and coverage not replayed.',
            'construction_result':'No149-point witness; all saved states are positive-score diagnostics.'}


def save_result(path,value):
    raw = (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    if len(raw) > 1024*1024:
        raise ValueError('audit report cap')
    fd,name = tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 25 or args.output.exists():
        raise ValueError('bounded duration and new output path required')
    def check():
        if time.monotonic()-ENTRY_STARTED >= args.seconds:
            raise TimeoutError('independent audit soft deadline')
    try:
        result = audit(check)
        check()
    except Exception as error:
        result = {'accepted':False,'error':f'{type(error).__name__}: {str(error)[:2000]}',
                  'scope':'Independent artifact audit; failure does not authorize retry/search.'}
    result['elapsed_seconds'] = time.monotonic()-ENTRY_STARTED
    save_result(args.output,result)
    if result['accepted'] and time.monotonic()-ENTRY_STARTED >= args.seconds:
        result.update(accepted=False,error='audit report persistence exceeded soft deadline',elapsed_seconds=time.monotonic()-ENTRY_STARTED)
        save_result(args.output,result)
    print(json.dumps({k:result.get(k) for k in ('accepted','error','elapsed_seconds')},sort_keys=True))
    return 0 if result['accepted'] else 2


if __name__ == '__main__':
    sys.exit(main())
