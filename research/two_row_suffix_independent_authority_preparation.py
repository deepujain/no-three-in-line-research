"""Synthetic-only independent authority audit preparation; never invokes actual loaders/run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from research import two_row_suffix75_v2_frozen as worker
from research import two_row_suffix_independent_authority_audit as audit

V2='11fc0200742a14f5baa8cfffe85c91b34353b4990608f70efba66cc20dd750a2'
KERNEL='0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'
LOCAL=((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
DENSE=((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))
PREFIX=((0,0),(0,1),(1,2),(2,1),(2,3),(3,2),(3,3))
BASE={'row_started':308,'row_completed':308,'pair_started':32,'pair_completed':32,'accepted':28}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def clone(value):return json.loads(audit.canonical(value))
def wrapped(a):return audit.canonical({'payload':a,'payload_sha256':audit.hashed(a)})

class Memory:
    def __init__(self,initial,fail=None):self.files={};self.latest=wrapped(initial);self.fail=fail;self.refs=[];self.witness=None
    def save(self,value):
        raw=audit.canonical(value);name=f'artifact-{len(self.files)}.json';self.files[name]=raw
        ref={'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};self.refs.append(ref);return ref
    def publish(self,a,tag):
        if tag==self.fail:raise OSError('synthetic publication failure')
        self.latest=worker.authority_bytes(a)
    def save_zero(self,points):
        self.witness=self.save({'certificate':{'n':4,'points':points,'claimed_conflict_count':0},
                                'synthetic_wrapper_without_validator_claim':True})
        return self.witness

def check(a,mem,initial,side=(),raw=None):
    initial_json={'n':4,'points':initial['points'],'state_hash':initial['state_hash'],'score':initial['U']}
    return audit.audit_authority(raw or wrapped(a),initial_json,mem.files,n=4,
        expected_initial_hash=initial['state_hash'],expected_initial_score=initial['U'],expected_base=initial['base'],
        historical_pair_prefix=initial['origin']['pair_prefix'],historical_row_complete=initial['origin']['row_complete'],
        max_states=12,check=lambda:None,side_outputs=side)

def run():
    assert sha(worker.__file__)==V2 and sha(worker.kernel.__file__)==KERNEL
    hashes={p:sha(p) for p in (__file__,audit.__file__,worker.__file__,worker.kernel.__file__)}
    cases={};sources={}
    def record(name,a,mem,initial,side=()):
        result=check(a,mem,initial,side);cases[name]=result;sources[name]=(clone(a),mem,clone(initial),side)
    for name,points,stop in [('local_zero',LOCAL,None),('dense_positive',DENSE,1),('dense_chain',DENSE,None)]:
        initial=worker.new_authority(points,4,base=BASE);mem=Memory(initial)
        result=worker.drive(initial,publish=mem.publish,save_move=mem.save,save_zero=mem.save_zero,stop_after=stop)
        assert result['error'] is None
        record(name,result['authority'],mem,initial)
    assert cases['dense_positive']['durable_U']>0 and cases['dense_positive']['new_accepted_moves']==1
    assert cases['local_zero']['durable_U']==0 and cases['dense_chain']['durable_U']==0
    # Imported one-pair coverage is synthetic source-supported setup, not actual historical evidence.
    initial=worker.new_authority(PREFIX,4,base=BASE,row_complete=True,pair_prefix=1);mem=Memory(initial)
    record('positive_imported_prefix',initial,mem,initial)
    pending=worker.plan_start(initial);record('pending_charge',pending,mem,initial)
    abandoned=clone(pending);abandoned['attempts'][-1]['outcome']='abandoned';abandoned['pending']=None
    record('abandoned_charge',abandoned,mem,initial)
    again=worker.plan_start(abandoned);record('abandoned_then_pending',again,mem,initial)
    result=worker.drive(initial,publish=mem.publish,save_move=mem.save,save_zero=mem.save_zero)
    assert result['error'] is None
    record('imported_prefix_zero',result['authority'],mem,initial)
    # A disclosed current-column result stub tests a new nonimproving pair record only.
    initial=worker.new_authority(PREFIX,4,base=BASE,row_complete=True);mem=Memory(initial);pending=worker.plan_start(initial)
    rows=pending['attempts'][-1]['rows'];cols=[[x for x,y in initial['points'] if y==r] for r in rows]
    stub={'score':initial['U'],'X':cols[0],'Y':cols[1],'zero':False,'enumeration_complete':True}
    completed=worker.plan_nonimprovement(pending,stub);record('stub_nonimproving_pair',completed,mem,initial)
    for name,points,fail in [('saved_zero_old_pending',LOCAL,'accept_zero'),('positive_orphan_old_pending',DENSE,'accept')]:
        initial=worker.new_authority(points,4,base=BASE);mem=Memory(initial,fail)
        result=worker.drive(initial,publish=mem.publish,save_move=mem.save,save_zero=mem.save_zero)
        assert result['status']=='error'
        durable=json.loads(mem.latest)['payload'];assert durable['U']>0 and durable['pending'] is not None
        side=[{'kind':'orphan_move','ref':mem.refs[-1]}]
        if mem.witness is not None:
            side.append({'kind':'saved_witness','ref':mem.witness})
            cert=json.loads(mem.files[mem.witness['path']])['certificate']
            side.append({'kind':'raw_candidate','ref':mem.save({'n':4,'points':cert['points'],'score':0})})
        record(name,durable,mem,initial,side)
    # Final-stop status comes from run after drive, so audit its cap binding separately.
    cap_base=dict(BASE,pair_started=95,pair_completed=95)
    initial=worker.new_authority(PREFIX,4,base=cap_base,row_complete=True);mem=Memory(initial)
    pending=worker.plan_start(initial);completed=worker.plan_nonimprovement(pending,stub)
    completed['status']='pair_cap';record('final_pair_cap_snapshot',completed,mem,initial)
    fresh=worker.new_authority(LOCAL,4);mem=Memory(fresh);record('fresh_zero_counters',fresh,mem,fresh)
    rejected=[]
    def reject(name,case,mutate):
        a,mem,initial,side=sources[case];a=deepcopy(a);files=deepcopy(mem.files)
        mutate(a,files)
        fake=Memory(initial);fake.files=files
        try:check(a,fake,initial,side)
        except (ValueError,KeyError,TypeError):rejected.append(name)
        else:raise AssertionError('corruption accepted: '+name)
    reject('boolean_counter_equal_zero','fresh_zero_counters',lambda a,f:a['counters'].__setitem__('accepted',False))
    reject('boolean_generation_equal_zero','fresh_zero_counters',lambda a,f:a.__setitem__('generation',False))
    reject('boolean_cursor_equal_zero','fresh_zero_counters',lambda a,f:a.__setitem__('row_cursor',False))
    reject('unexhausted_cap_status','positive_imported_prefix',lambda a,f:a.__setitem__('status','pair_cap'))
    reject('boolean_counter','pending_charge',lambda a,f:a['counters'].__setitem__('accepted',True))
    # Value-preserving Boolean substitutions are tested at numeric zero/one slots.
    reject('boolean_cursor_equal_one','pending_charge',lambda a,f:a.__setitem__('pair_cursor',True))
    reject('boolean_record_seq_equal_one','pending_charge',lambda a,f:a['attempts'][0].__setitem__('seq',True))
    reject('boolean_record_cursor_equal_one','pending_charge',lambda a,f:a['attempts'][0].__setitem__('cursor',True))
    reject('boolean_origin_prefix_equal_one','pending_charge',lambda a,f:a['origin'].__setitem__('pair_prefix',True))
    reject('boolean_final_score_equal_zero','local_zero',lambda a,f:a.__setitem__('U',False))
    reject('boolean_orders_entry','positive_imported_prefix',lambda a,f:a['orders']['pairs'][0].__setitem__(0,False))
    reject('undercharged_start','pending_charge',lambda a,f:a['counters'].__setitem__('pair_started',32))
    reject('wrong_state_identity','pending_charge',lambda a,f:a.__setitem__('state_hash','0'*64))
    reject('stale_attempt_state','pending_charge',lambda a,f:a['attempts'][0].__setitem__('state_hash','0'*64))
    reject('wrong_order_hash','pending_charge',lambda a,f:a['attempts'][0].__setitem__('order_hash','0'*64))
    reject('wrong_cursor','pending_charge',lambda a,f:a['attempts'][0].__setitem__('cursor',0))
    reject('wrong_selected_rows','pending_charge',lambda a,f:a['attempts'][0].__setitem__('rows',[1,3]))
    reject('cleared_pending_charge','pending_charge',lambda a,f:a.__setitem__('pending',None))
    reject('abandoned_cursor_advance','abandoned_charge',lambda a,f:a.__setitem__('pair_cursor',2))
    reject('extra_artifact','dense_positive',lambda a,f:a['artifacts'].append(a['artifacts'][0]))
    reject('missing_artifact','dense_positive',lambda a,f:a.__setitem__('artifacts',[]))
    reject('bad_reference_digest','dense_positive',lambda a,f:a['artifacts'][0].__setitem__('sha256','0'*64))
    reject('wrong_minimum_score','dense_positive',lambda a,f:a['attempts'][-1]['minimum'].__setitem__(0,a['U']+1))
    reject('positive_incomplete','dense_positive',lambda a,f:a['attempts'][-1].__setitem__('enumeration_complete',False))
    reject('missing_zero_witness','local_zero',lambda a,f:a.__setitem__('witness',None))
    reject('forged_nonimprovement','stub_nonimproving_pair',lambda a,f:a['attempts'][0]['minimum'].__setitem__(0,0))
    reject('wrong_status','pending_charge',lambda a,f:a.__setitem__('status','zero'))
    def corrupt_move(a,files):
        ref=a['artifacts'][0];m=json.loads(files[ref['path']]);m['counters']['accepted']=True
        raw=audit.canonical(m);files[ref['path']]=raw;ref.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    reject('rehash_move_boolean_counter','dense_positive',corrupt_move)
    a,mem,initial,side=sources['dense_positive'];document=json.loads(wrapped(a));document['payload_sha256']='0'*64
    try:check(a,mem,initial,raw=audit.canonical(document))
    except ValueError:rejected.append('bad_wrapper_identity')
    else:raise AssertionError('bad wrapper accepted')
    assert hashes=={p:sha(p) for p in hashes}
    return {'passed':True,'scope':'SOURCE/TINY only; all geometry n4; no actual artifacts, loaders or run',
            'source_pins':hashes,'passed_cases':cases,'corruption_rejections':rejected,
            'limits':'Memory publications only. Synthetic witness wrappers establish independent geometry, not validator or filesystem lifecycle. One current-column nonimprovement stub and imported-prefix setup are disclosed. No optimizer replay occurs inside the auditor.'}

if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-authority-preparation-v2.json')
    assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'cases':len(result['passed_cases']),'rejections':len(result['corruption_rejections']),
                      'helper_sha256':sha(audit.__file__),'preparation_sha256':sha(__file__),'evidence_sha256':sha(path)}))
