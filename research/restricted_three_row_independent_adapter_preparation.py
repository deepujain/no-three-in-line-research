"""Synthetic metadata association for three-row adapter; no actual input or geometry."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from research import restricted_three_row_actual_chain_adapter as adapter


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fixture(manifest_count=228,mode='cap'):
    root=adapter.ROOT;runtime=str(Path(sys.executable).resolve());fake='a'*64
    manifest={str(root/'research/restricted_three_row75.py'):adapter.WORKER_SHA,str(root/'research/two_row_descent75.py'):adapter.KERNEL_SHA,
              str(root/'research/two_row_suffix75.py'):adapter.SHARED_SHA,str(root/'data/two-row-suffix75-input-identities.json'):adapter.HANDOFF_SHA,
              runtime:fake,str(root/'src/verify.py'):fake}
    for i in range(manifest_count-len(manifest)):manifest[f'/synthetic-only/source-{i}']=fake
    pins=dict(manifest);pins[str(root/adapter.MANIFEST)]=adapter.EXPECTED[adapter.MANIFEST]
    assert len(manifest)==manifest_count and len(pins)==manifest_count+1
    counts={'started':16,'completed':16,'accepted':1};charge={'started':16,'completed':15,'accepted':0};status='block_cap';pending=None;U=64;orders=None;refs=[]
    if mode=='pending':counts={'started':1,'completed':0,'accepted':0};charge=dict(counts);status='search_deadline';pending=1;U=65;orders={'sha256':fake}
    if mode=='nostart':counts=dict.fromkeys(counts,0);charge=None;status='search_deadline';U=65;orders={'sha256':fake}
    witness=None
    if mode=='zero':counts={'started':1,'completed':1,'accepted':1};charge={'started':1,'completed':0,'accepted':0};status='zero';U=0;witness={'path':'valid149.json','sha256':fake,'bytes':1}
    a={'n':75,'U':U,'state_hash':fake,'generation':counts['accepted'],'counters':counts,'cursor':0,'pending':pending,'status':status,
       'orders':orders,'attempts':[],'artifacts':refs,'witness':witness}
    result={'last_start_charge':charge,'pending_attempt':pending,'durable_U':U,'counters':counts}
    handoff={'metadata_sha256':adapter.HANDOFF_SHA,'normalized_sha256':adapter.STATE,'score':65,'historical_pair_prefix':32,
             'coverage_basis':'source_bound_prior_execution_not_independent_minimum_certificate'}
    initial={'handoff':deepcopy(handoff),'counters':dict.fromkeys(counts,0)}
    raw=b'SYNTHETIC AUTHORITY PLACEHOLDER; GEOMETRY IS OUTSIDE THIS ASSOCIATION TEST'
    report={'method':'fixed65_restricted_three_row75','accepted':True,'identity_valid':True,'closure':False,'authority_uncertain':False,
            'n':75,'k':149,'block_cap':16,'soft_seconds':25,'search_seconds':23,'authority_bytes':len(raw),
            'authority_sha256':adapter.EXPECTED[adapter.AUTHORITY],'state':{k:a[k] for k in ('n','U','state_hash','generation','counters','cursor','pending','status')},
            'attempts':[],'artifacts':refs,'order_sha256':None if orders is None else fake,'status':status,'witness_saved':U==0,
            'authority_publications':2+counts['started']+counts['completed'],'work':{'indexes_started':1},'handoff':handoff,'pins':pins,'elapsed_seconds':3}
    if charge is not None:report['last_attempted_charge']=deepcopy(charge)
    if witness:report['witness']=deepcopy(witness)
    job={'argv':[str(root/'.venv/bin/python'),'research/restricted_three_row75.py','--seconds','25','--output-dir',adapter.DIRECTORY,'--source-pins',adapter.MANIFEST],
         'status':'completed','sources_unchanged':True,'source_manifest_sha256':adapter.EXPECTED[adapter.MANIFEST],'sources_before':pins,'elapsed_seconds':5,
         'gate':{'returncode':0,'seconds_limit':30,'rss_limit_mib':256,'peak_sampled_rss_kib':1024,'rss_samples':3,'cleanup_samples':1,
                 'gate_status':'exited','cleanup_status':'clean','cleanup_error':None,'monitor_error':None,'trigger_gate_status':None,'elapsed_seconds':4}}
    return report,job,manifest,a,initial,deepcopy(adapter.EXPECTED),raw,result,runtime

def run():
    source=sha(__file__);adapter_sha=sha(adapter.__file__);positive=[]
    for size,mode in ((6,'cap'),(228,'cap'),(228,'pending'),(228,'nostart'),(228,'zero')):
        values=fixture(size,mode);pins,resource,count=adapter.associated(*values)
        assert count==size and len(pins)==size+1;positive.append({'manifest_entries':size,'effective_pins':len(pins),'mode':mode})
    corruptions={
        'last_completed14':lambda v:v[0]['last_attempted_charge'].__setitem__('completed',14),
        'last_completed16':lambda v:v[0]['last_attempted_charge'].__setitem__('completed',16),
        'last_accepted1':lambda v:v[0]['last_attempted_charge'].__setitem__('accepted',1),
        'last_started15':lambda v:v[0]['last_attempted_charge'].__setitem__('started',15),
        'manifest_missing_original':lambda v:v[2].pop('/synthetic-only/source-0'),
        'manifest_self_present':lambda v:v[2].__setitem__(str(adapter.ROOT/adapter.MANIFEST),adapter.EXPECTED[adapter.MANIFEST]),
        'report_missing_self_pin':lambda v:v[0].__setitem__('pins',dict(v[2])),
        'receipt_pin_mismatch':lambda v:v[1].__setitem__('sources_before',{}),
        'wrong_argv':lambda v:v[1]['argv'].__setitem__(1,'wrong.py'),
        'receipt_returncode':lambda v:v[1]['gate'].__setitem__('returncode',1),
        'bool_returncode':lambda v:v[1]['gate'].__setitem__('returncode',False),
        'dirty_cleanup':lambda v:v[1]['gate'].__setitem__('cleanup_status','error'),
        'wall_limit':lambda v:v[1]['gate'].__setitem__('elapsed_seconds',31),
        'rss_limit':lambda v:v[1]['gate'].__setitem__('peak_sampled_rss_kib',262145),
        'source_drift':lambda v:v[1].__setitem__('sources_unchanged',False),
        'report_failure':lambda v:v[0].__setitem__('accepted',False),
        'metadata_error':lambda v:v[0].__setitem__('witness_metadata_error','x'),
        'uncertain_authority':lambda v:v[0].__setitem__('authority_uncertain',True),
        'wrong_authority_hash':lambda v:v[0].__setitem__('authority_sha256','0'*64),
        'wrong_state':lambda v:v[0].__setitem__('state',{}),
        'wrong_publications':lambda v:v[0].__setitem__('authority_publications',33),
        'indexes_over_cap':lambda v:v[0]['work'].__setitem__('indexes_started',18),
        'wrong_handoff':lambda v:v[4].__setitem__('handoff',{}),
        'wrong_initial_counts':lambda v:v[4]['counters'].__setitem__('accepted',1),
        'cap_pending':lambda v:v[7].__setitem__('pending_attempt',16),
    }
    rejected=[]
    for name,mutate in corruptions.items():
        values=list(deepcopy(fixture()));mutate(values)
        try:adapter.associated(*values)
        except (ValueError,KeyError,TypeError):rejected.append(name)
        else:raise AssertionError('corruption accepted '+name)
    assert sha(__file__)==source and sha(adapter.__file__)==adapter_sha
    return {'passed':True,'source_sha256':source,'adapter_sha256':adapter_sha,'positive_cases':positive,'corruption_rejections':rejected,
            'scope':'Pure synthetic metadata association only; no actual reads, n75 coordinates, byte-hashing or geometry execution.',
            'limits':'Does not test actual filesystem/guard behavior. Pure chain helper is tested separately; this harness passes declared chain results.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-adapter-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'positive':len(result['positive_cases']),'rejections':len(result['corruption_rejections']),
                     'adapter_sha256':sha(adapter.__file__),'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
