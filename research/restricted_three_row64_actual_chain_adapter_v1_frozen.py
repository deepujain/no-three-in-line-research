"""Fixed64 supplied-input successful-run audit; no search, discovery or recovery.

Actual inputs and execution require a separately frozen Root-supplied spec and
owned allocation. The --inputs-sha256 argument authenticates that exact spec.
"""
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
HELPER_SHA='1c896c070f4892a977fcc639e6d1a13d6c436c3d87b07b8674d8edaa1a221a96'
COMMON_SHA='4fc03f19b7f4e1323cff650615ad4cabca88ca6680450b1bbed080986ab7782a'
HELPER_PINS={'research/restricted_three_row_independent_chain_audit.py':HELPER_SHA,
             'research/two_row_suffix_independent_authority_audit.py':COMMON_SHA}
for _name,_sha in HELPER_PINS.items():
    if hashlib.sha256((ROOT/_name).read_bytes()).hexdigest()!=_sha:raise ValueError('frozen independent source drift')
from research import restricted_three_row_independent_chain_audit as chain
WORKER_SHA='e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
STATE='b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7'
HANDOFF_PATH='data/restricted-three-row64-input-identities.json'
HANDOFF_SHA='2d6ba98abf571bc430f9a6e51a0dec5e99db68246e780ac24a5c8ba65b025ced'
PRIOR_MANIFEST='7d0ab3cc50b2e7349218be5b33ea6897047a69879f27c03693efa7656e16a51d'
PRIOR_AUDIT='ab302755266615a13423b81eb26c887af6a208d643ce1881a478fe5ee591450d'
SOURCE_PINS={**HELPER_PINS,'research/restricted_three_row64.py':WORKER_SHA,
    'research/restricted_three_row75.py':'d4d3a272ca8691c110b881ba739d31f95a858406c20e711ef588e712ebff794c',
    'research/two_row_descent75.py':'0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c',
    'research/two_row_suffix75.py':'fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1',
    'research/restricted_three_row_actual_chain_adapter.py':'0d5537eb46a898a84cb89ba4aceff2a817c122f8b5873492e5cce06e226ad50c'}
HANDOFF={'metadata_sha256':HANDOFF_SHA,'normalized_sha256':STATE,'score':64,
    'predecessor_normalized_sha256':'25540b6e492800d54a1bb2c1abe4d9127b18823a1289b960d7382ef541055c0c',
    'artifact_count':51,'prior_manifest_sha256':PRIOR_MANIFEST,'prior_audit_sha256':PRIOR_AUDIT,
    'historical_counters':{'started':16,'completed':16,'accepted':1},
    'coverage_basis':'historical_execution_not_new_state_coverage'}
ROLE_CAPS={'report':256*1024,'receipt':256*1024,'manifest':128*1024,'authority':1024*1024,'initial':16384}


def require(ok,message):
    if not ok:raise ValueError(message)


def sha_schema(value):
    return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def relative_name(name):
    require(type(name) is str and name and not Path(name).is_absolute() and str(Path(name))==name
            and all(part not in ('.','..') for part in name.split('/')),'normalized relative input path')
    require((ROOT/name).resolve().is_relative_to(ROOT.resolve()),'input path escapes root')
    return name


def decode(raw):
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,'duplicate JSON key');out[key]=value
        return out
    def bad(value):raise ValueError('nonfinite JSON token')
    return json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=bad)


def validate_spec(spec):
    require(type(spec) is dict and set(spec)=={'schema','artifacts','manifest_entries'}
            and spec['schema']=='fixed64-successful-run-audit-input-v1','explicit audit spec')
    require(type(spec['manifest_entries']) is int and 1<=spec['manifest_entries']<=512,'explicit manifest count')
    roles=spec['artifacts'];require(type(roles) is dict and set(roles)==set(ROLE_CAPS),'exact five input roles')
    seen=set()
    for role,item in roles.items():
        require(type(item) is dict and set(item)=={'path','sha256','bytes'},'input descriptor')
        name=relative_name(item['path']);key=str((ROOT/name).resolve())
        require(key not in seen,'aliased input roles');seen.add(key)
        require(sha_schema(item['sha256']) and type(item['bytes']) is int and 0<item['bytes']<=ROLE_CAPS[role],'input byte/hash bounds')
    directory=Path(roles['authority']['path']).parent
    require(directory!=Path('.') and Path(roles['authority']['path']).name=='authority.json','authority path')
    for role in ('initial','report'):
        require(Path(roles[role]['path'])==directory/(role+'.json'),'same explicit run directory')
    return roles,str(directory)


def digest(path,check):
    check(); h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); block = stream.read(65536)
            if not block:
                return h.hexdigest()
            h.update(block)

def normalized_pins(values,cap=513):
    if type(values) is not dict or not 1 <= len(values) <= cap:
        raise ValueError('pin mapping')
    pins = {}
    for name,sha in values.items():
        if type(name) is not str or not 0<len(name)<=1024 or type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('pin schema')
        key = str((ROOT/name).resolve())
        if key in pins:
            raise ValueError('duplicate normalized pin')
        pins[key] = sha
    return pins

def clean_receipt(report,job,manifest_sha,manifest_path,directory):
    argv = [str(ROOT/'.venv/bin/python'),'research/restricted_three_row64.py','--seconds','25',
            '--output-dir',directory,'--source-pins',manifest_path]
    if (job.get('argv') != argv or job.get('status') != 'completed' or job.get('sources_unchanged') is not True
            or job.get('source_manifest_sha256') != manifest_sha
            or any(k=='error' or k.endswith('_error') for k in job)):
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
    cleanup=gate.get('cleanup_elapsed_seconds')
    require(type(cleanup) in (int,float) and math.isfinite(cleanup) and 0<=cleanup<30,'cleanup elapsed')
    times = [report.get('elapsed_seconds'),gate.get('elapsed_seconds'),job.get('elapsed_seconds')]
    if (any(type(x) not in (int,float) or not math.isfinite(x) for x in times)
            or not 0 <= times[0] < 25 or not 0 < times[1] < 30 or not times[0] <= times[1] <= times[2] <= 30):
        raise ValueError('three-row elapsed binding')
    return {'elapsed_seconds':gate['elapsed_seconds'],'peak_sampled_rss_kib':gate['peak_sampled_rss_kib'],
            'rss_note':'Sampled RSS observation; not a proved unsampled maximum.'}

class DiskSource:
    def read(self,name,expected,check,cap,length=None):
        check();path=Path(name)
        require(path.stat().st_size<=cap,'authenticated input byte cap')
        with path.open('rb') as stream:raw=stream.read(cap+1)
        require(len(raw)<=cap and path.stat().st_size==len(raw),'input size drift/cap')
        require(length is None or len(raw)==length,'exact input byte length')
        require(hashlib.sha256(raw).hexdigest()==expected,'authenticated input identity')
        check();return raw,decode(raw)
    def digest(self,name,check):return digest(name,check)


def associated(report,job,manifest,a,initial,spec,authority_raw,result,runtime,metadata):
    """Pure metadata association, including M+1 and derived precompletion charge."""
    roles,directory=validate_spec(spec);manifest_name=roles['manifest']['path'];manifest_sha=roles['manifest']['sha256']
    pins=normalized_pins(manifest,512);manifest_count=len(pins);self_path=str((ROOT/manifest_name).resolve())
    require(manifest_count==spec['manifest_entries'],'Root manifest count')
    if self_path in pins:raise ValueError('manifest self entry')
    pins[self_path]=manifest_sha
    if len(pins)!=manifest_count+1 or pins!=normalized_pins(report.get('pins')) or pins!=normalized_pins(job.get('sources_before')):
        raise ValueError('manifest plus one report/receipt pin association')
    mandatory={str((ROOT/name).resolve()):sha for name,sha in SOURCE_PINS.items()}
    mandatory[str((ROOT/HANDOFF_PATH).resolve())]=HANDOFF_SHA
    if any(pins.get(k)!=v for k,v in mandatory.items()) or runtime not in pins or str((ROOT/'src/verify.py').resolve()) not in pins:
        raise ValueError('mandatory fixed source/runtime pins')
    require(type(metadata) is dict and type(metadata.get('artifacts')) is dict and len(metadata['artifacts'])==51,'fixed metadata closure')
    for name,sha in metadata['artifacts'].items():
        relative_name(name);require(sha_schema(sha) and pins.get(str((ROOT/name).resolve()))==sha,'fixed51 closure pin')
    require(metadata['artifacts'].get('data/restricted-three-row75-source-pins.json')==PRIOR_MANIFEST
            and metadata['artifacts'].get('data/restricted-three-row75-independent-actual-v1-audit.json')==PRIOR_AUDIT,'prior evidence pin')
    resource=clean_receipt(report,job,manifest_sha,manifest_name,directory)
    chain.integers(report,('n','k','block_cap','authority_publications','authority_bytes'))
    if (report.get('method')!='fixed64_restricted_three_row75' or report.get('accepted') is not True
            or report.get('identity_valid') is not True or report.get('closure') is not False
            or report.get('authority_uncertain') is not False or report['n']!=75 or report['k']!=149 or report['block_cap']!=16
            or report.get('soft_seconds')!=25 or report.get('search_seconds')!=23
            or report['authority_bytes']!=len(authority_raw) or report.get('authority_sha256')!=roles['authority']['sha256']
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
    require(type(initial) is dict and set(initial)=={'n','points','score','state_hash','counters','order_sha256','handoff'},'initial seven-key schema')
    require(type(initial['n']) is int and initial['n']==75 and type(initial['score']) is int and initial['score']==64
            and initial['state_hash']==STATE,'fixed64 initial scalars')
    handoff=report.get('handoff')
    if (chain.canonical(handoff)!=chain.canonical(HANDOFF) or chain.canonical(initial['handoff'])!=chain.canonical(HANDOFF)
            or chain.canonical(initial['counters'])!=chain.canonical(dict.fromkeys(chain.COUNTERS,0))):
        raise ValueError('fixed64 initial/handoff association')
    initial_order=(a['attempts'][0]['order_hash'] if a['attempts'] else a['orders']['sha256'])
    require(sha_schema(initial['order_sha256']) and initial['order_sha256']==initial_order,'initial direct candidate hash')
    return pins,resource,manifest_count


def audit(spec,check,source=None):
    roles,directory=validate_spec(spec);source=DiskSource() if source is None else source
    runtime=str(Path(sys.executable).resolve());source_sha=source.digest(__file__,check)
    helpers={str((ROOT/name).resolve()):sha for name,sha in HELPER_PINS.items()}
    for path,sha in helpers.items():require(source.digest(path,check)==sha,'independent helper source drift')
    docs={role:source.read(ROOT/item['path'],item['sha256'],check,ROLE_CAPS[role],item['bytes']) for role,item in roles.items()}
    report,job,manifest,initial=(docs[role][1] for role in ('report','receipt','manifest','initial'))
    raw,envelope=docs['authority'];require(type(envelope) is dict and 'payload' in envelope,'authority envelope')
    a=envelope['payload'];require(type(a) is dict,'authority payload')
    pre_pins=normalized_pins(manifest,512);self_path=str((ROOT/roles['manifest']['path']).resolve())
    require(len(pre_pins)==spec['manifest_entries'] and self_path not in pre_pins,'manifest count/self association')
    pre_pins[self_path]=roles['manifest']['sha256']
    require(pre_pins==normalized_pins(report.get('pins'))==normalized_pins(job.get('sources_before')),'pre-audit pin-set association')
    for path,sha in pre_pins.items():require(source.digest(path,check)==sha,'pre-audit source/input/runtime drift')
    metadata_raw,metadata=source.read(ROOT/HANDOFF_PATH,HANDOFF_SHA,check,10249,10249);del metadata_raw
    # Only explicitly referenced immutable artifacts may be read.
    require(type(a.get('artifacts')) is list and len(a['artifacts'])<=16,'move reference scope')
    refs=list(a['artifacts'])+([] if a.get('witness') is None else [a['witness']])
    require(len(refs)<=17,'reference scope');blobs={};artifact_hashes={}
    for ref in refs:
        require(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'reference schema')
        name=ref['path']
        require(type(name) is str and Path(name).name==name and name not in ('.','..') and name not in blobs,'unique local reference')
        require(sha_schema(ref['sha256']) and type(ref['bytes']) is int and 0<ref['bytes']<=16384,'reference byte/hash bounds')
        path=relative_name(str(Path(directory)/name))
        require(path not in {item['path'] for item in roles.values()},'reference aliases input')
        blob,_=source.read(ROOT/path,ref['sha256'],check,16384,ref['bytes'])
        blobs[name]=blob;artifact_hashes[path]=ref['sha256']
    # The helper uses independent determinant geometry and no production imports.
    result=chain.audit_chain(raw,initial,blobs,n=75,initial_hash=STATE,initial_score=64,max_states=17,check=check)
    pins,resource,manifest_count=associated(report,job,manifest,a,initial,spec,raw,result,runtime,metadata)
    require(pins==pre_pins,'stable effective pin mapping')
    expected={item['path']:item['sha256'] for item in roles.values()}
    post={**pins,**{str((ROOT/p).resolve()):s for p,s in expected.items()},
          **{str((ROOT/p).resolve()):s for p,s in artifact_hashes.items()},**helpers}
    for path,sha in post.items():require(source.digest(path,check)==sha,'post-audit source/artifact drift')
    require(source.digest(__file__,check)==source_sha,'adapter source drift');check()
    return {'accepted':True,'scope':'Independent direct saved-state chain/rankings and exact fixed64 report/receipt/pin associations; no optimizer replay.',
        'chain':result,'resources':resource,'manifest_entries':manifest_count,'effective_pins':len(pins),
        'artifact_hashes':{**expected,**artifact_hashes},'audit_source_sha256':source_sha,'helper_sha256':HELPER_SHA,
        'common_helper_sha256':COMMON_SHA,'runtime_path':runtime,'runtime_sha256':pins[runtime],
        'input_spec_sha256':hashlib.sha256(chain.canonical(spec)).hexdigest(),
        'limits':'Minima/domain selection remain source-supported. Successful-run scope only; no orphan recovery. Overall acceptance also requires Root-owned audit guard with exact output digest. No automatic continuation.'}


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
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--inputs-sha256',required=True)
    parser.add_argument('--seconds',type=float,default=25)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 25 or args.output.exists():
        raise ValueError('bounded duration and new output path required')
    def check():
        if time.monotonic()-ENTRY_STARTED >= args.seconds:
            raise TimeoutError('independent audit soft deadline')
    try:
        require(sha_schema(args.inputs_sha256),'explicit input spec digest')
        spec_raw,spec=DiskSource().read(args.inputs,args.inputs_sha256,check,16384)
        result = audit(spec,check)
        require(digest(args.inputs,check)==args.inputs_sha256,'input spec drift')
        result['input_spec_bytes_sha256']=args.inputs_sha256
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
