"""Future fixed64 adapter tests: closed synthetic inputs and approved n4 controls only."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import restricted_three_row64_audit_synthetic_fixture_v2 as f

a=f.adapter;c=f.chain
ADAPTER_SHA='31ad510c53f3480a339f92b9b9366e7a912daf10e474d99c5b5d4c6ce74bb26d'

def align_authority(x):
    value=x['authority'];raw=f.wrapped(value);r=x['report']
    r.update(authority_sha256=f.digest(raw),authority_bytes=len(raw),state={k:deepcopy(value[k]) for k in ('n','U','state_hash','generation','counters','cursor','pending','status')},
        attempts=deepcopy(value['attempts']),artifacts=deepcopy(value['artifacts']),order_sha256=None if value['orders'] is None else value['orders']['sha256'])
    f.reseal(x)


def align_manifest(x):
    raw=f.pack(x['manifest']);sha=f.digest(raw);pins=dict(x['manifest']);pins[str(a.ROOT/x['paths']['manifest'])]=sha
    x['report']['pins']=deepcopy(pins);x['receipt']['sources_before']=deepcopy(pins);x['receipt']['source_manifest_sha256']=sha
    x['receipt']['preflight'].update(manifest_sha256=sha,manifest_bytes=len(raw),manifest_entries=len(x['manifest']),effective_entries_after_self=len(x['manifest'])+1)
    f.reseal(x)


def execute(x,source=None):
    with f.fixture_patches(x) as calls:
        result=a.audit(x['spec'],lambda:None,f.ClosedSource(x) if source is None else source)
    return result,calls


def run():
    assert f.digest(Path(a.__file__).read_bytes())==ADAPTER_SHA
    results=[];tiny=[];rejections=[]
    # Same already approved scripted route: no optimizer, fixture enumeration or search.
    for mode in ('nostart','pending','complete','positive','cap'):
        x=f.chain_fixture(mode,False)
        result=c.audit_chain(f.wrapped(x['authority']),x['initial'],x['blobs'],n=4,initial_hash=x['initial']['state_hash'],
            initial_score=8,max_states=17,check=lambda:None)
        assert result['last_start_charge']==x['last_charge']
        tiny.append({'mode':mode,'scores':result['accepted_scores'],'states':result['unique_states_recounted'],'counts':result['counters']})
    for mode in ('nostart','pending','complete','positive','cap','zero','cap_noaccept'):
        x=f.fixture(mode);source=f.ClosedSource(x);result,calls=execute(x,source)
        assert result['accepted'] and result['chain']['last_start_charge']==x['last_charge']
        assert result['manifest_entries']==297 and result['effective_pins']==298
        assert len(calls)==result['chain']['unique_states_recounted']
        if mode=='cap':assert x['authority']['orders'] is None and result['chain']['counters']=={'started':16,'completed':16,'accepted':4}
        expected_reads={str(a.ROOT/x['paths'][role]) for role in x['paths']}|{str(a.ROOT/a.HANDOFF_PATH)}|{str(a.ROOT/x['directory']/name) for name in x['blobs']}
        assert {path for op,path in source.events if op=='read'}==expected_reads
        results.append({'mode':mode,'states':len(calls),'last_start_charge':result['chain']['last_start_charge'],
            'counts':result['chain']['counters'],'effective_pins':result['effective_pins']})
    for size in (244,512):
        result,_=execute(f.fixture('nostart',size));assert result['manifest_entries']==size and result['effective_pins']==size+1
        results.append({'mode':'dynamic_manifest','manifest_entries':size,'effective_pins':size+1})
    def reject(name,mutate,mode='cap',align=None):
        x=f.fixture(mode);mutate(x)
        if align is not None:align(x)
        else:f.reseal(x)
        try:execute(x)
        except (ValueError,KeyError,TypeError,AssertionError,OSError) as exc:rejections.append({'case':name,'error':str(exc)[:200]})
        else:raise AssertionError('unexpected acceptance '+name)
    for key,value in [('method','fixed65_restricted_three_row75'),('accepted',False),('identity_valid',False),('closure',True),
        ('authority_uncertain',True),('authority_sha256','0'*64),('authority_bytes',1),('authority_publications',33),
        ('witness_metadata_error','injected'),('n',True),('elapsed_seconds',25),('state',{}),('attempts',[]),('artifacts',[]),('order_sha256','0'*64)]:
        reject('report_'+key,lambda x,k=key,v=value:x['report'].__setitem__(k,v))
    for key,value in [('score',65),('artifact_count',50),('metadata_sha256','0'*64),('normalized_sha256','0'*64),
        ('predecessor_normalized_sha256','0'*64),('prior_manifest_sha256','0'*64),('prior_audit_sha256','0'*64),
        ('historical_counters',{'started':16,'completed':16,'accepted':True}),('coverage_basis','active coverage')]:
        def mutate(x,k=key,v=value):
            x['report']['handoff'][k]=v;x['initial']['handoff'][k]=deepcopy(v)
        reject('handoff_'+key,mutate)
    reject('initial_generation_key',lambda x:x['initial'].__setitem__('generation',0))
    reject('initial_cursor_key',lambda x:x['initial'].__setitem__('cursor',0))
    reject('initial_bool_counter',lambda x:x['initial']['counters'].__setitem__('accepted',False))
    reject('initial_wrong_order_no_start',lambda x:x['initial'].__setitem__('order_sha256','0'*64),'nostart')
    reject('initial_wrong_order_after_accept',lambda x:x['initial'].__setitem__('order_sha256','0'*64))
    reject('final_counts_as_charge',lambda x:x['report'].__setitem__('last_attempted_charge',deepcopy(x['authority']['counters'])))
    reject('charge_on_no_start',lambda x:x['report'].__setitem__('last_attempted_charge',dict.fromkeys(c.COUNTERS,0)),'nostart')
    reject('missing_charge',lambda x:x['report'].pop('last_attempted_charge'))
    reject('bool_charge',lambda x:x['report']['last_attempted_charge'].__setitem__('accepted',True))
    for key,value in [('returncode',False),('cleanup_status','error'),('cleanup_error','error'),('monitor_error','error'),
        ('trigger_gate_status','rss'),('elapsed_seconds',31),('cleanup_elapsed_seconds',False),('peak_sampled_rss_kib',262145),
        ('rss_samples',0),('cleanup_samples',0),('seconds_limit',31),('rss_limit_mib',257)]:
        reject('gate_'+key,lambda x,k=key,v=value:x['receipt']['gate'].__setitem__(k,v))
    reject('wrong_argv',lambda x:x['receipt']['argv'].__setitem__(1,'wrong.py'))
    reject('source_change',lambda x:x['receipt'].__setitem__('sources_unchanged',False))
    reject('receipt_self_missing',lambda x:x['receipt']['sources_before'].pop(str(a.ROOT/x['paths']['manifest'])))
    reject('receipt_manifest_digest',lambda x:x['receipt'].__setitem__('source_manifest_sha256','0'*64))
    reject('receipt_elapsed_order',lambda x:x['receipt'].__setitem__('elapsed_seconds',1.))
    reject('work_indexes18',lambda x:x['report']['work'].__setitem__('indexes_started',18))
    reject('work_indexes_bool',lambda x:x['report']['work'].__setitem__('indexes_started',True))
    reject('manifest_self',lambda x:x['manifest'].__setitem__(str(a.ROOT/x['paths']['manifest']),'0'*64),align=align_manifest)
    for name in list(a.SOURCE_PINS)+[a.HANDOFF_PATH,'src/verify.py',f.fixture()['runtime']]:
        key=str((a.ROOT/name).resolve())
        reject('missing_pin:'+name,lambda x,k=key:x['manifest'].pop(k),align=align_manifest)
    reject('closure_pin_missing',lambda x:x['manifest'].pop(str(a.ROOT/'synthetic-closure/input-00.json')),align=align_manifest)
    reject('normalized_manifest_alias',lambda x:x['manifest'].__setitem__(str(a.ROOT)+'/research/./restricted_three_row64.py',a.WORKER_SHA),align=align_manifest)
    for label,mutate in [
        ('bool_seq',lambda x:x['authority']['attempts'][0].__setitem__('seq',True)),
        ('wrong_cursor',lambda x:x['authority']['attempts'][0].__setitem__('cursor',1)),
        ('wrong_order',lambda x:x['authority']['attempts'][0].__setitem__('order_hash','0'*64)),
        ('wrong_ordinal',lambda x:x['authority']['attempts'][0].__setitem__('seq',2)),
        ('lost_pending_charge',lambda x:x['authority']['counters'].__setitem__('started',0)),
        ('old_cursor_after_accept',lambda x:x['authority'].__setitem__('cursor',1)),
        ('missing_accepted_ref',lambda x:x['authority']['artifacts'].pop()),
        ('partial_positive',lambda x:x['authority']['attempts'][-1].__setitem__('enumeration_exhausted',False)),
        ('bool_selected_column',lambda x:x['authority']['attempts'][0]['minimum'][1].__setitem__(0,False)),
        ('reference_parent_path',lambda x:x['authority']['artifacts'][0].__setitem__('path','../bad.json')),
        ('reference_bool_bytes',lambda x:x['authority']['artifacts'][0].__setitem__('bytes',True)),
        ('bad_reference_hash',lambda x:x['authority']['artifacts'][0].__setitem__('sha256','0'*64)),
    ]:reject('helper_'+label,mutate,align=align_authority)
    reject('zero_witness_missing',lambda x:x['authority'].__setitem__('witness',None),'zero',align_authority)
    reject('saved_witness_not_accepted',lambda x:x['report'].__setitem__('witness_saved',False),'zero')
    for key,value in [('passed',False),('manifest_entries',228),('effective_entries_after_self',297),('mandatory_union_entries',243),
        ('worker_source_identities',5),('fixed_artifact_roles',50),('inherited_manifest_entries',229),
        ('prior_manifest_self_required',False),('runtime_verifier_worker_metadata_required',False),
        ('manifest_sha256','0'*64),('manifest_bytes',1)]:
        reject('preflight_'+key,lambda x,k=key,v=value:x['receipt']['preflight'].__setitem__(k,v))
    reject('reviews_changed',lambda x:x['receipt'].__setitem__('independent_reviews_unchanged',False))
    reject('review_pin_missing',lambda x:x['receipt']['independent_review_pins'].pop(next(iter(a.REVIEW_PINS))))
    reject('review_pin_digest',lambda x:x['receipt']['independent_review_pins'].__setitem__(next(iter(a.REVIEW_PINS)),'0'*64))
    reject('external_review_added_to_worker_pinmap',lambda x:x['receipt']['sources_before'].update({str(a.ROOT/name):sha for name,sha in a.REVIEW_PINS.items()}))
    reject('noaccept_charge_completed16',lambda x:x['report']['last_attempted_charge'].__setitem__('completed',16),'cap_noaccept')
    reject('noaccept_charge_accepted1',lambda x:x['report']['last_attempted_charge'].__setitem__('accepted',1),'cap_noaccept')
    x=f.fixture('cap_noaccept');result,calls=execute(x)
    assert result['chain']['counters']=={'started':16,'completed':16,'accepted':0}
    assert result['chain']['last_start_charge']=={'started':16,'completed':15,'accepted':0}
    assert result['chain']['cursor']==16 and result['chain']['durable_U']==64 and len(calls)==1
    # Explicit spec mutations preserve the genuine fixture bytes.
    for label,mutate in [
        ('count_bool',lambda s:s.__setitem__('manifest_entries',True)),
        ('count_wrong',lambda s:s.__setitem__('manifest_entries',228)),
        ('extra_role',lambda s:s['artifacts'].__setitem__('extra',dict(s['artifacts']['initial']))),
        ('length_wrong',lambda s:s['artifacts']['initial'].__setitem__('bytes',1)),
        ('digest_wrong',lambda s:s['artifacts']['initial'].__setitem__('sha256','0'*64)),
        ('path_parent',lambda s:s['artifacts']['initial'].__setitem__('path','../initial.json')),
        ('directory_mismatch',lambda s:s['artifacts']['initial'].__setitem__('path','other/initial.json')),
    ]:
        x=f.fixture();mutate(x['spec'])
        try:execute(x)
        except (ValueError,KeyError,TypeError,AssertionError) as exc:rejections.append({'case':'spec_'+label,'error':str(exc)[:200]})
        else:raise AssertionError(label)
    for label,make_source in [
        ('read_failure',lambda x:f.ClosedSource(x,fail_read=str(a.ROOT/x['paths']['authority']))),
        ('runtime_pre_drift',lambda x:f.ClosedSource(x,drift=(x['runtime'],1))),
        ('runtime_post_drift',lambda x:f.ClosedSource(x,drift=(x['runtime'],2))),
        ('adapter_post_drift',lambda x:f.ClosedSource(x,drift=(a.__file__,2))),
        ('helper_pre_drift',lambda x:f.ClosedSource(x,drift=(str(a.ROOT/next(iter(a.HELPER_PINS))),1))),
        ('external_review_post_drift',lambda x:f.ClosedSource(x,drift=(str(a.ROOT/list(a.REVIEW_PINS)[1]),2))),
        ('artifact_post_drift',lambda x:f.ClosedSource(x,drift=(str(a.ROOT/x['directory']/next(iter(x['blobs']))),1))),
    ]:
        x=f.fixture()
        try:execute(x,make_source(x))
        except (ValueError,KeyError,TypeError,AssertionError,OSError) as exc:rejections.append({'case':label,'error':str(exc)[:200]})
        else:raise AssertionError(label)
    disk=[]
    with tempfile.TemporaryDirectory(prefix='fixed64-audit-bytes-') as directory:
        path=Path(directory)/'synthetic.json';raw=b'{"synthetic":true}';path.write_bytes(raw)
        assert a.DiskSource().read(path,f.digest(raw),lambda:None,len(raw),len(raw))[1]=={'synthetic':True}
        disk.append('valid')
        for label,value,sha,cap,length in [('digest',raw,'0'*64,len(raw),len(raw)),('cap',raw,f.digest(raw),len(raw)-1,len(raw)),
            ('length',raw,f.digest(raw),len(raw),len(raw)-1),('duplicate',b'{"a":1,"a":2}',None,100,None),
            ('nan',b'{"a":NaN}',None,100,None),('nonascii',b'{"a":"\xff"}',None,100,None)]:
            path.write_bytes(value)
            try:a.DiskSource().read(path,f.digest(value) if sha is None else sha,lambda:None,cap,length)
            except (ValueError,UnicodeError):disk.append(label)
            else:raise AssertionError(label)
    assert f.digest(Path(a.__file__).read_bytes())==ADAPTER_SHA
    return {'passed':True,'adapter_sha256':ADAPTER_SHA,'fixture_sha256':f.digest(Path(f.__file__).read_bytes()),
        'source_sha256':f.digest(Path(__file__).read_bytes()),'approved_control_evidence_sha256':f.CONTROL_SHA,
        'genuine_n4_helper_cases':tiny,'full_synthetic_audit_cases':results,'rejection_count':len(rejections),'rejections':rejections,
        'real_disk_source_cases':disk,'limitations':'Actual full audit control flow and helper fold over genuine outcome bytes, with explicit structural/identity/geometry spies for n75 and declared source digest labels. Metadata pin rebound to genuine synthetic metadata. Genuine n4 direct recounts reuse approved saved control route only; declared zero is not zero geometry evidence. No actual inputs, optimizer, new fixture search, physical runtime/owned guard or RSS evidence.'}

if __name__=='__main__':
    output=Path('data/restricted-three-row64-audit-source-tiny-v2.json')
    assert not output.exists()
    result=run();output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','adapter_sha256','rejection_count','source_sha256','fixture_sha256')}))
