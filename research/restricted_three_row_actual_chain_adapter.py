"""Future fixed-path three-row audit adapter; Root-only actual execution after SOURCE review."""
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
from research import restricted_three_row_independent_chain_audit as chain
REPORT='data/restricted-three-row75-v1/report.json'
RECEIPT='data/experiments/shepherd-restricted-three-row75-v1.json'
MANIFEST='data/restricted-three-row75-source-pins.json'
AUTHORITY='data/restricted-three-row75-v1/authority.json'
INITIAL='data/restricted-three-row75-v1/initial.json'
DIRECTORY='data/restricted-three-row75-v1'
EXPECTED={
 REPORT:'b9edf5e48c259adbbb53b4c23441e923814f859f5566776c220095ebb0d2d45a',
 AUTHORITY:'e97841b317c8854ee50e0252b76d9a3153fef9e39ac8f6108fc841fda68ba55a',
 RECEIPT:'e6a0365371c76a0066397f9a9b01c9c889ea71b56eed5c81773c50a2e0b3344c',
 INITIAL:'2ec89dc7e67e9c63f75300c983a96865f2a2db6964133f71b6f32ec217cb9615',
 MANIFEST:'7d0ab3cc50b2e7349218be5b33ea6897047a69879f27c03693efa7656e16a51d',
}
EXPECTED_MANIFEST_ENTRIES=228
WORKER_SHA='d4d3a272ca8691c110b881ba739d31f95a858406c20e711ef588e712ebff794c'
HELPER_SHA='1c896c070f4892a977fcc639e6d1a13d6c436c3d87b07b8674d8edaa1a221a96'
COMMON_SHA='4fc03f19b7f4e1323cff650615ad4cabca88ca6680450b1bbed080986ab7782a'
KERNEL_SHA='0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
SHARED_SHA='fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'
STATE='25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c'
HANDOFF_SHA='f966e46cdd62fc22f48e0415a8b851b6f5dc021bd19b798ca3c2e6526cca910e'


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

def clean_receipt(report,job,manifest_sha):
    argv = [str(ROOT/'.venv/bin/python'),'research/restricted_three_row75.py','--seconds','25',
            '--output-dir','data/restricted-three-row75-v1','--source-pins',MANIFEST]
    if (job.get('argv') != argv or job.get('status') != 'completed' or job.get('sources_unchanged') is not True
            or job.get('source_manifest_sha256') != manifest_sha):
        raise ValueError('receipt association')
    gate = job.get('gate')
    integer_keys = ('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')
    if type(gate) is not dict or any(type(gate.get(k)) is not int for k in integer_keys):
        raise ValueError('guard schema')
    if (gate.get('gate_status') != 'exited' or gate['returncode'] != 0 or gate.get('cleanup_status') != 'clean'
            or any(gate.get(k) is not None for k in ('cleanup_error','monitor_error','trigger_gate_status'))
            or gate['seconds_limit'] != 30 or gate['rss_limit_mib'] != 256
            or not 0 < gate['peak_sampled_rss_kib'] <= 256*1024 or gate['rss_samples'] < 1 or gate['cleanup_samples'] < 1):
        raise ValueError('unclean three-row guard')
    times = [report.get('elapsed_seconds'),gate.get('elapsed_seconds'),job.get('elapsed_seconds')]
    if (any(type(x) not in (int,float) or not math.isfinite(x) for x in times)
            or not 0 <= times[0] < 25 or not 0 < times[1] < 30 or not times[0] <= times[1] <= times[2] <= 30):
        raise ValueError('three-row elapsed binding')
    return {'elapsed_seconds':gate['elapsed_seconds'],'peak_sampled_rss_kib':gate['peak_sampled_rss_kib'],
            'rss_note':'Sampled RSS observation; not a proved unsampled maximum.'}

def authenticated(path,expected,check,cap=2*1024*1024):
    check();path=Path(path)
    if path.stat().st_size>cap:raise ValueError('authenticated input byte cap')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('authenticated input identity')
    check();return raw,json.loads(raw)

def associated(report,job,manifest,a,initial,expected,authority_raw,result,runtime):
    """Pure metadata association, including M+1 and derived precompletion charge."""
    pins=normalized_pins(manifest);manifest_count=len(pins);self_path=str((ROOT/MANIFEST).resolve())
    if self_path in pins:raise ValueError('manifest self entry')
    pins[self_path]=expected[MANIFEST]
    if len(pins)!=manifest_count+1 or pins!=normalized_pins(report.get('pins')) or pins!=normalized_pins(job.get('sources_before')):
        raise ValueError('manifest plus one report/receipt pin association')
    mandatory={str(ROOT/'research/restricted_three_row75.py'):WORKER_SHA,str(ROOT/'research/two_row_descent75.py'):KERNEL_SHA,
               str(ROOT/'research/two_row_suffix75.py'):SHARED_SHA,str(ROOT/'data/two-row-suffix75-input-identities.json'):HANDOFF_SHA}
    if any(pins.get(k)!=v for k,v in mandatory.items()) or runtime not in pins or str(ROOT/'src/verify.py') not in pins:
        raise ValueError('mandatory fixed source/runtime pins')
    resource=clean_receipt(report,job,expected[MANIFEST])
    chain.integers(report,('n','k','block_cap','authority_publications','authority_bytes'))
    if (report.get('method')!='fixed65_restricted_three_row75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('closure') is not False
            or report.get('authority_uncertain') is not False or report['n']!=75 or report['k']!=149 or report['block_cap']!=16
            or report.get('soft_seconds')!=25 or report.get('search_seconds')!=23
            or report['authority_bytes']!=len(authority_raw) or report.get('authority_sha256')!=expected[AUTHORITY]
            or any(k=='error' or k.endswith('_error') for k in report)):
        raise ValueError('accepted report/source contract')
    fields=('n','U','state_hash','generation','counters','cursor','pending','status')
    if (chain.canonical(report.get('state'))!=chain.canonical({k:a[k] for k in fields})
            or chain.canonical(report.get('attempts'))!=chain.canonical(a['attempts'])
            or chain.canonical(report.get('artifacts'))!=chain.canonical(a['artifacts'])
            or report.get('order_sha256')!=(None if a['orders'] is None else a['orders']['sha256'])):
        raise ValueError('report last-durable authority association')
    charge=result['last_start_charge']
    if charge is None:
        if 'last_attempted_charge' in report:raise ValueError('charge with no start')
    elif chain.canonical(report.get('last_attempted_charge'))!=chain.canonical(charge):raise ValueError('exact precompletion last charge')
    status=report.get('status')
    if status!=a['status'] or status not in ('block_cap','restricted_candidate_list_exhausted','search_deadline','zero'):
        raise ValueError('successful terminal status')
    if status in ('block_cap','restricted_candidate_list_exhausted','zero') and result['pending_attempt'] is not None:
        raise ValueError('successful terminal leaves pending result')
    iszero=result['durable_U']==0
    if (report.get('witness_saved') is not iszero or (iszero and report.get('witness')!=a['witness'])
            or (not iszero and ('witness' in report or a['witness'] is not None)) or 'raw_zero' in report):
        raise ValueError('successful witness/authority association')
    if report['authority_publications']!=2+result['counters']['started']+result['counters']['completed'] or report['authority_publications']>34:
        raise ValueError('exact clean publication accounting')
    work=report.get('work')
    if type(work) is not dict or type(work.get('indexes_started')) is not int or not 1<=work['indexes_started']<=17:
        raise ValueError('index attempt bound')
    handoff=report.get('handoff')
    if (type(handoff) is not dict or handoff.get('metadata_sha256')!=HANDOFF_SHA or handoff.get('normalized_sha256')!=STATE
            or type(handoff.get('score')) is not int or handoff['score']!=65 or handoff.get('historical_pair_prefix')!=32
            or handoff.get('coverage_basis')!='source_bound_prior_execution_not_independent_minimum_certificate'
            or chain.canonical(initial.get('handoff'))!=chain.canonical(handoff)
            or chain.canonical(initial.get('counters'))!=chain.canonical(dict.fromkeys(chain.COUNTERS,0))):
        raise ValueError('fixed65 initial/handoff association')
    return pins,resource,manifest_count


def audit(check):
    identities={'schema':'restricted-three-row-audit-input-v1','artifacts':EXPECTED}
    if (type(identities) is not dict or set(identities)!={'schema','artifacts'} or identities['schema']!='restricted-three-row-audit-input-v1'
            or type(identities['artifacts']) is not dict or set(identities['artifacts'])!={REPORT,RECEIPT,MANIFEST,AUTHORITY,INITIAL}):
        raise ValueError('explicit Root fixed-path identities required')
    expected=identities['artifacts']
    if any(type(s) is not str or len(s)!=64 or any(c not in '0123456789abcdef' for c in s) for s in expected.values()):raise ValueError('expected digest schema')
    helper_paths={chain.__file__:HELPER_SHA,chain.common.__file__:COMMON_SHA};source_sha=digest(__file__,check)
    for path,sha in helper_paths.items():
        if digest(path,check)!=sha:raise ValueError('independent helper source drift')
    docs={name:authenticated(ROOT/name,sha,check) for name,sha in expected.items()}
    report,job,manifest,initial=(docs[p][1] for p in (REPORT,RECEIPT,MANIFEST,INITIAL));raw=docs[AUTHORITY][0];a=docs[AUTHORITY][1]['payload']
    pre_pins=normalized_pins(manifest);manifest_path=str((ROOT/MANIFEST).resolve())
    if len(pre_pins)!=EXPECTED_MANIFEST_ENTRIES or manifest_path in pre_pins:raise ValueError('Root supplied manifest count/self association')
    pre_pins[manifest_path]=expected[MANIFEST]
    if pre_pins!=normalized_pins(report.get('pins')) or pre_pins!=normalized_pins(job.get('sources_before')):raise ValueError('pre-audit pin-set association')
    for path,sha in pre_pins.items():
        if digest(path,check)!=sha:raise ValueError('pre-audit source/input/runtime drift')
    blobs={};artifact_hashes={}
    refs=list(a['artifacts'])+([] if a['witness'] is None else [a['witness']])
    if len(refs)>17:raise ValueError('reference scope')
    for ref in refs:
        name=ref.get('path')
        if type(name) is not str or Path(name).name!=name or name in ('.','..'):raise ValueError('local explicit reference basename')
        path=str(Path(DIRECTORY)/name);blob,_=authenticated(ROOT/path,ref.get('sha256'),check,16384)
        if len(blob)!=ref.get('bytes'):raise ValueError('artifact length binding')
        blobs[name]=blob;artifact_hashes[path]=ref['sha256']
    result=chain.audit_chain(raw,initial,blobs,n=75,initial_hash=STATE,initial_score=65,max_states=17,check=check)
    runtime=str(Path(sys.executable).resolve())
    pins,resource,manifest_count=associated(report,job,manifest,a,initial,expected,raw,result,runtime)
    # The helper already checked the first record against the independently reconstructed
    # initial ranking. If no start exists, current=initial and its materialized order was checked.
    initial_order=(a['attempts'][0]['order_hash'] if a['attempts'] else a['orders']['sha256'])
    if initial.get('order_sha256')!=initial_order:raise ValueError('initial direct candidate hash')
    if pins!=pre_pins:raise ValueError('stable effective pin mapping')
    for path,sha in {**pins,**{str(ROOT/p):s for p,s in expected.items()},**{str(ROOT/p):s for p,s in artifact_hashes.items()},**helper_paths}.items():
        if digest(path,check)!=sha:raise ValueError('post-audit source/artifact drift')
    if digest(__file__,check)!=source_sha:raise ValueError('adapter source drift')
    check()
    return {'accepted':True,'scope':'Independent direct saved-state chain/rankings and exact report/receipt/pin associations; no optimizer replay.',
            'chain':result,'resources':resource,'manifest_entries':manifest_count,'effective_pins':len(pins),
            'artifact_hashes':{**expected,**artifact_hashes},'audit_source_sha256':source_sha,'helper_sha256':HELPER_SHA,
            'common_helper_sha256':COMMON_SHA,'runtime_path':runtime,'runtime_sha256':pins[runtime],
            'limits':'Recorded minima/domain selection remain source-supported, not independently optimized. Receipt acceptance is distinct from Root audit guard completion. No automatic continuation.'}


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
