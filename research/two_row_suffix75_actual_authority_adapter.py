"""Fixed suffix audit adapter. Only Root may execute under its separate owned allocation."""
import time
ENTRY_STARTED=time.monotonic()
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import two_row_suffix_independent_authority_audit as chain
REPORT='data/two-row-suffix75-v1/report.json'
RECEIPT='data/experiments/shepherd-two-row-suffix75-v1.json'
MANIFEST='data/two-row-suffix75-source-pins.json'
AUTHORITY='data/two-row-suffix75-v1/authority.json'
INITIAL='data/two-row-suffix75-v1/initial.json'
EXPECTED={
 REPORT:'d721f912f05a95cefe5d82671001430501940405e2f6bab0304d02c87bf8053c',
 RECEIPT:'59fd93d495ccbe332f9e2c14937d51a09d8d799476ad1389e2a8b833bb284c11',
 MANIFEST:'1267a677d750c3d0b8cd0286d115768b4d268c349a9403ec73f295bf4e77d571',
 AUTHORITY:'c8929d504610321357cbeb31e110db043cfd5c0addb7a2b0a3ca614f5d1a5174',
}
WORKER_SHA='fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'
HELPER_SHA='4fc03f19b7f4e1323cff650615ad4cabca88ca6680450b1bbed080986ab7782a'
KERNEL_SHA='0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
STATE='25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c'
HANDOFF_SHA='f966e46cdd62fc22f48e0415a8b851b6f5dc021bd19b798ca3c2e6526cca910e'
BASE={'row_started':308,'row_completed':308,'pair_started':32,'pair_completed':32,'accepted':28}


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
    argv = [str(ROOT/'.venv/bin/python'),'research/two_row_suffix75.py','--seconds','25',
            '--output-dir','data/two-row-suffix75-v1','--source-pins',MANIFEST]
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
        raise ValueError('unclean suffix guard')
    times = [report.get('elapsed_seconds'),gate.get('elapsed_seconds'),job.get('elapsed_seconds')]
    if (any(type(x) not in (int,float) or not math.isfinite(x) for x in times)
            or not 0 <= times[0] < 25 or not 0 < times[1] < 30 or not times[0] <= times[1] <= times[2] <= 30):
        raise ValueError('suffix elapsed binding')
    return {'elapsed_seconds':gate['elapsed_seconds'],'peak_sampled_rss_kib':gate['peak_sampled_rss_kib'],
            'rss_note':'Sampled RSS observation; not a proved unsampled maximum.'}

def authenticated(path,expected,check,cap=2*1024*1024):
    check();path=Path(path)
    if path.stat().st_size>cap:raise ValueError('authenticated input byte cap')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('authenticated input identity')
    check();return raw,json.loads(raw)


def audit(check):
    if digest(chain.__file__,check)!=HELPER_SHA:raise ValueError('authority helper source pin')
    source_sha=digest(__file__,check)
    docs={name:authenticated(ROOT/name,sha,check) for name,sha in EXPECTED.items()}
    report,job,manifest=(docs[p][1] for p in (REPORT,RECEIPT,MANIFEST))
    raw=docs[AUTHORITY][0];a=docs[AUTHORITY][1]['payload']
    pins=normalized_pins(manifest);manifest_path=str((ROOT/MANIFEST).resolve())
    if len(pins)!=166:raise ValueError('expected166 manifest entries before manifest self pin')
    if manifest_path in pins:raise ValueError('manifest self pin')
    pins[manifest_path]=EXPECTED[MANIFEST]
    if pins!=normalized_pins(report.get('pins')) or pins!=normalized_pins(job.get('sources_before')):
        raise ValueError('report/receipt/source manifest pin association')
    runtime=str(Path(sys.executable).resolve())
    mandatory={str(ROOT/'research/two_row_suffix75.py'):WORKER_SHA,
               str(ROOT/'research/two_row_descent75.py'):KERNEL_SHA,
               str(ROOT/'data/two-row-suffix75-input-identities.json'):HANDOFF_SHA}
    if len(pins)!=167 or any(pins.get(k)!=v for k,v in mandatory.items()) or runtime not in pins or str(ROOT/'src/verify.py') not in pins:
        raise ValueError('mandatory exact source/runtime/input pins')
    for name,sha in pins.items():
        if digest(name,check)!=sha:raise ValueError('suffix source/input/runtime drift')
    resource=clean_receipt(report,job)
    chain.integer_fields(report,('n','k','row_cap','pair_cap','new_row_cap','new_pair_cap','authority_publications','authority_bytes'))
    if (report.get('method')!='fixed65_cursor_two_row_suffix75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('closure') is not False
            or report.get('witness_saved') is not False or report.get('authority_uncertain') is not False
            or report.get('status')!='pair_cap' or report['n']!=75 or report['k']!=149
            or report['row_cap']!=512 or report['pair_cap']!=96 or report['new_row_cap']!=204 or report['new_pair_cap']!=64
            or report.get('soft_seconds')!=25 or report.get('search_seconds')!=23
            or report['authority_publications']!=130 or report.get('authority_sha256')!=EXPECTED[AUTHORITY]
            or report['authority_bytes']!=len(raw)
            or any(k in report for k in ('error','search_error','authority_identity_error','witness_metadata_error','final_error','witness','raw_zero'))):
        raise ValueError('fixed completed suffix report association')
    fields=('n','U','state_hash','generation','counters','phase','row_cursor','pair_cursor',
            'row_sweep_complete','pair_scan_complete','pending','status')
    if (chain.canonical(report.get('state'))!=chain.canonical({k:a[k] for k in fields})
            or chain.canonical(report.get('attempts'))!=chain.canonical(a['attempts'])
            or report.get('artifacts')!=a['artifacts'] or report.get('order_sha256')!=a['orders']['sha256']):
        raise ValueError('report/durable authority exact association')
    handoff=report.get('handoff')
    if (type(handoff) is not dict or handoff.get('metadata_sha256')!=HANDOFF_SHA
            or handoff.get('normalized_sha256')!=STATE or type(handoff.get('score')) is not int or handoff['score']!=65
            or type(handoff.get('historical_pair_prefix')) is not int or handoff['historical_pair_prefix']!=32
            or handoff.get('coverage_basis')!='source_bound_prior_execution_not_independent_minimum_certificate'):
        raise ValueError('fixed65 historical handoff association')
    initial_sha=digest(ROOT/INITIAL,check)
    _,initial=authenticated(ROOT/INITIAL,initial_sha,check,16384)
    if (chain.canonical(initial.get('handoff'))!=chain.canonical(handoff)
            or chain.canonical(initial.get('counters'))!=chain.canonical(BASE)
            or type(initial.get('pair_cursor')) is not int or initial['pair_cursor']!=32
            or initial.get('order_sha256')!=a['orders']['sha256']):
        raise ValueError('initial fixed-state/handoff/order association')
    # No artifact discovery or alternate starting input. This exact run declares no moves/witnesses.
    if a['artifacts']!=[] or a['witness'] is not None:raise ValueError('fixed no-accept suffix artifact boundary')
    result=chain.audit_authority(raw,initial,{},n=75,expected_initial_hash=STATE,expected_initial_score=65,
        expected_base=BASE,historical_pair_prefix=32,historical_row_complete=True,max_states=1,check=check)
    expected_counts=dict(BASE,pair_started=96,pair_completed=96)
    expected_last_charge=dict(expected_counts,pair_completed=95)
    if (result['accepted_scores']!=[65] or result['accepted_state_hashes']!=[STATE] or result['new_accepted_moves']!=0
            or result['new_attempts']!=64 or result['abandoned_starts']!=0 or result['pending_attempt'] is not None
            or result['counters']!=expected_counts or result['durable_status']!='pair_cap'
            or result['recorded_nonimprovements_not_independent_minima']!=64
            or a['phase']!='pair' or a['row_sweep_complete'] is not True or a['pair_scan_complete'] is not False
            or a['pair_cursor']!=96 or chain.canonical(report.get('last_attempted_charge'))!=chain.canonical(expected_last_charge)
            or any(r['kind']!='pair' or r['outcome']!='complete' or r['cursor']!=31+r['seq'] for r in a['attempts'])):
        raise ValueError('exact64 newly completed pair records and unchanged endpoint')
    for name,sha in pins.items():
        if digest(name,check)!=sha:raise ValueError('post-audit suffix pin drift')
    for name,sha in {**EXPECTED,INITIAL:initial_sha}.items():
        if digest(ROOT/name,check)!=sha:raise ValueError('post-audit artifact drift')
    if digest(chain.__file__,check)!=HELPER_SHA or digest(__file__,check)!=source_sha:raise ValueError('audit source drift')
    check()
    return {'accepted':True,'scope':'One independent direct endpoint/ranking recount plus saved ledger/receipt/pin association; no optimizer replay.',
            'authority_audit':result,'suffix_resources':resource,'suffix_pins_checked':len(pins),
            'suffix_artifact_hashes':EXPECTED,'initial_sha256':initial_sha,'audit_source_sha256':source_sha,
            'authority_helper_sha256':HELPER_SHA,'runtime_path':runtime,'runtime_sha256':pins[runtime],
            'receipt_acceptance_checked':True,'final_status':'pair_cap','local_minimum_claim':'None independently established. Historical32 and newly recorded64 minima remain source-supported execution, not exclusion proof.',
            'construction_result':'Unchanged positive U65 diagnostic; no149 witness. No continuation allocation.'}


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

if __name__=='__main__':sys.exit(main())
