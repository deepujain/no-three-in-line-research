"""Synthetic metadata-only adapter tests. All input I/O and geometry are replaced explicitly."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from research import two_row_suffix75_actual_authority_adapter as adapter

ADAPTER_SHA='1957377699f9fa516d74d592994f8120657f9c72b64210ab0aef2c205ee99c8e'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    assert sha(adapter.__file__)==ADAPTER_SHA
    root=adapter.ROOT;runtime=str(Path(sys.executable).resolve());fake_sha='a'*64
    manifest={str(root/'research/two_row_suffix75.py'):adapter.WORKER_SHA,
              str(root/'research/two_row_descent75.py'):adapter.KERNEL_SHA,
              str(root/'data/two-row-suffix75-input-identities.json'):adapter.HANDOFF_SHA,
              runtime:fake_sha,str(root/'src/verify.py'):fake_sha}
    for i in range(166-len(manifest)):manifest[f'/synthetic-only/pin-{i}']=fake_sha
    pins=dict(manifest);pins[str(root/adapter.MANIFEST)]=adapter.EXPECTED[adapter.MANIFEST]
    assert len(manifest)==166 and len(pins)==167
    counts=dict(adapter.BASE,pair_started=96,pair_completed=96)
    handoff={'metadata_sha256':adapter.HANDOFF_SHA,'normalized_sha256':adapter.STATE,'score':65,
             'historical_pair_prefix':32,'coverage_basis':'source_bound_prior_execution_not_independent_minimum_certificate'}
    attempts=[{'kind':'pair','outcome':'complete','seq':i,'cursor':31+i} for i in range(1,65)]
    state={'n':75,'U':65,'state_hash':adapter.STATE,'generation':28,'counters':counts,'phase':'pair',
           'row_cursor':3,'pair_cursor':96,'row_sweep_complete':True,'pair_scan_complete':False,'pending':None,'status':'pair_cap'}
    authority=dict(state,attempts=attempts,artifacts=[],witness=None,orders={'sha256':fake_sha})
    raw=b'SYNTHETIC AUTHORITY PLACEHOLDER: GEOMETRY STUBBED'
    report=dict(method='fixed65_cursor_two_row_suffix75',accepted=True,identity_valid=True,closure=False,witness_saved=False,
                authority_uncertain=False,status='pair_cap',n=75,k=149,row_cap=512,pair_cap=96,new_row_cap=204,new_pair_cap=64,
                soft_seconds=25,search_seconds=23,authority_publications=130,authority_sha256=adapter.EXPECTED[adapter.AUTHORITY],
                authority_bytes=len(raw),state=state,attempts=attempts,artifacts=[],order_sha256=fake_sha,handoff=handoff,
                last_attempted_charge=dict(counts,pair_completed=95),pins=pins,elapsed_seconds=3)
    gate={'returncode':0,'seconds_limit':30,'rss_limit_mib':256,'peak_sampled_rss_kib':100,'rss_samples':2,
          'cleanup_samples':1,'gate_status':'exited','cleanup_status':'clean','cleanup_error':None,'monitor_error':None,
          'trigger_gate_status':None,'elapsed_seconds':4}
    job={'argv':[str(root/'.venv/bin/python'),'research/two_row_suffix75.py','--seconds','25','--output-dir',
                 'data/two-row-suffix75-v1','--source-pins',adapter.MANIFEST],
         'status':'completed','sources_unchanged':True,'source_manifest_sha256':adapter.EXPECTED[adapter.MANIFEST],
         'gate':gate,'elapsed_seconds':5,'sources_before':pins}
    initial={'handoff':handoff,'counters':adapter.BASE,'pair_cursor':32,'order_sha256':fake_sha}
    chain_result={'accepted_scores':[65],'accepted_state_hashes':[adapter.STATE],'new_accepted_moves':0,
                  'new_attempts':64,'abandoned_starts':0,'pending_attempt':None,'counters':counts,
                  'durable_status':'pair_cap','recorded_nonimprovements_not_independent_minima':64}
    baseline={adapter.REPORT:report,adapter.RECEIPT:job,adapter.MANIFEST:manifest,adapter.AUTHORITY:{'payload':authority},adapter.INITIAL:initial}
    original=(adapter.digest,adapter.authenticated,adapter.chain.audit_authority)
    def execute(mutate=None):
        docs=deepcopy(baseline);derived=deepcopy(chain_result)
        if mutate:mutate(docs,derived)
        def digest(path,check):
            check();name=str(Path(path).resolve())
            if name==str(Path(adapter.chain.__file__).resolve()):return adapter.HELPER_SHA
            if name==str(Path(adapter.__file__).resolve()):return ADAPTER_SHA
            for p,s in adapter.EXPECTED.items():
                if name==str((root/p).resolve()):return s
            if name==str((root/adapter.INITIAL).resolve()):return fake_sha
            return pins[name]
        def authenticated(path,expected,check,cap=2*1024*1024):
            check();name=str(Path(path).relative_to(root))
            assert expected==digest(path,check)
            return (raw if name==adapter.AUTHORITY else b'SYNTHETIC METADATA'),docs[name]
        def geometry_stub(*args,**kwargs):
            assert args[0]==raw and kwargs['max_states']==1 and kwargs['n']==75 and kwargs['expected_initial_score']==65
            return derived
        adapter.digest=digest;adapter.authenticated=authenticated;adapter.chain.audit_authority=geometry_stub
        try:return adapter.audit(lambda:None)
        finally:adapter.digest,adapter.authenticated,adapter.chain.audit_authority=original
    assert execute()['accepted'] is True
    corruptions={
        'regression_old165_manifest':lambda d,c:d[adapter.MANIFEST].pop('/synthetic-only/pin-0'),
        'unexpected167_manifest':lambda d,c:d[adapter.MANIFEST].__setitem__('/synthetic-only/extra',fake_sha),
        'last_charge_completed94':lambda d,c:d[adapter.REPORT]['last_attempted_charge'].__setitem__('pair_completed',94),
        'last_charge_completed96':lambda d,c:d[adapter.REPORT]['last_attempted_charge'].__setitem__('pair_completed',96),
        'last_charge_started95':lambda d,c:d[adapter.REPORT]['last_attempted_charge'].__setitem__('pair_started',95),
        'receipt_argv':lambda d,c:d[adapter.RECEIPT]['argv'].__setitem__(1,'wrong.py'),
        'receipt_returncode':lambda d,c:d[adapter.RECEIPT]['gate'].__setitem__('returncode',1),
        'receipt_bool_returncode':lambda d,c:d[adapter.RECEIPT]['gate'].__setitem__('returncode',False),
        'receipt_dirty_cleanup':lambda d,c:d[adapter.RECEIPT]['gate'].__setitem__('cleanup_status','error'),
        'receipt_over_wall':lambda d,c:d[adapter.RECEIPT]['gate'].__setitem__('elapsed_seconds',31),
        'receipt_over_rss':lambda d,c:d[adapter.RECEIPT]['gate'].__setitem__('peak_sampled_rss_kib',262145),
        'receipt_sources_changed':lambda d,c:d[adapter.RECEIPT].__setitem__('sources_unchanged',False),
        'receipt_manifest':lambda d,c:d[adapter.RECEIPT].__setitem__('source_manifest_sha256','0'*64),
        'report_rejected':lambda d,c:d[adapter.REPORT].__setitem__('accepted',False),
        'report_uncertain_authority':lambda d,c:d[adapter.REPORT].__setitem__('authority_uncertain',True),
        'report_wrong_publications':lambda d,c:d[adapter.REPORT].__setitem__('authority_publications',129),
        'report_wrong_authority_hash':lambda d,c:d[adapter.REPORT].__setitem__('authority_sha256','0'*64),
        'report_bad_bytes':lambda d,c:d[adapter.REPORT].__setitem__('authority_bytes',1),
        'report_metadata_error':lambda d,c:d[adapter.REPORT].__setitem__('witness_metadata_error','synthetic'),
        'report_state_mismatch':lambda d,c:d[adapter.REPORT].__setitem__('state',{}),
        'report_pin_mismatch':lambda d,c:d[adapter.REPORT].__setitem__('pins',{}),
        'initial_order_mismatch':lambda d,c:d[adapter.INITIAL].__setitem__('order_sha256','0'*64),
        'initial_prefix_mismatch':lambda d,c:d[adapter.INITIAL].__setitem__('pair_cursor',33),
        'initial_handoff_mismatch':lambda d,c:d[adapter.INITIAL].__setitem__('handoff',{}),
        'unexpected_accepted_chain':lambda d,c:c.__setitem__('new_accepted_moves',1),
        'wrong_endpoint_score':lambda d,c:c.__setitem__('accepted_scores',[64]),
        'wrong_attempt_count':lambda d,c:c.__setitem__('new_attempts',63),
        'pending_leftover':lambda d,c:c.__setitem__('pending_attempt',64),
    }
    rejected=[]
    for name,mutate in corruptions.items():
        try:execute(mutate)
        except (ValueError,KeyError,TypeError):rejected.append(name)
        else:raise AssertionError('accepted corruption: '+name)
    assert sha(adapter.__file__)==ADAPTER_SHA
    return {'passed':True,'scope':'Synthetic metadata only, all adapter file/hash I/O replaced; direct-chain audit stubbed. No actual input or n75 geometry.',
            'adapter_sha256':ADAPTER_SHA,'preparation_sha256':sha(__file__),'positive_association_cases':1,'manifest_entries':166,'effective_pins_including_manifest':167,
            'rejected_corruptions':rejected,'limits':'This exercises metadata association predicates, not actual filesystem hashing, direct geometry, report durability or guard runtime behavior.'}

if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-adapter-preparation-v3.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'rejections':len(result['rejected_corruptions']),'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
