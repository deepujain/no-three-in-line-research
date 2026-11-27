"""Synthetic supplied-byte chain audit tests; no actual discovery/loaders/run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from research import restricted_three_row_independent_chain_audit as chain
from research import restricted_three_row_independent_worker_audit as support
from research import restricted_three_row_independent_control_preparation as control
from research import restricted_three_row75 as worker

WORKER_SHA='d4d3a272ca8691c110b881ba739d31f95a858406c20e711ef588e712ebff794c'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def wrapped(a):return chain.canonical({'payload':a,'payload_sha256':chain.hashed(a)})
class Memory(support.Memory):
    def __init__(self,fail=None):super().__init__();self.fail=fail;self.witness=None;self.moves=[]
    def publish(self,a,tag):
        if tag==self.fail:raise OSError('synthetic publication failure')
        super().publish(a,tag)
    def zero(self,points):
        assert support.oracle.raw(points)==0
        self.witness=self.save({'certificate':{'n':4,'points':points,'claimed_conflict_count':0}});return self.witness
    def move(self,value):
        ref=self.save(value);self.moves.append(ref);return ref

def inspect(a,initial,mem,side=()):
    ini={'n':initial['n'],'points':initial['points'],'score':initial['U'],'state_hash':initial['state_hash']}
    return chain.audit_chain(wrapped(a),ini,mem.blobs,n=initial['n'],initial_hash=initial['state_hash'],initial_score=initial['U'],
                             max_states=17,check=lambda:None,side_outputs=side)

def run():
    start=time.monotonic();assert sha(worker.__file__)==WORKER_SHA;cases={};inputs={}
    def check():
        if time.monotonic()-start>10:raise TimeoutError('fixed10-second preparation')
    def save(name,a,initial,mem,side=()):cases[name]=inspect(a,initial,mem,side);inputs[name]=(deepcopy(a),deepcopy(initial),mem,side)
    for name,points in [('zero',((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))),('dense_zero',control.POINTS)]:
        initial=worker.new_authority(points,4);m=Memory();r=worker.drive(initial,publish=m.publish,save_move=m.move,save_zero=m.zero)
        assert r['error'] is None;save(name,r['authority'],initial,m)
    initial=worker.new_authority(control.POINTS,4);m=Memory();save('initial',initial,initial,m)
    pending=worker.plan_start(initial);save('pending',pending,initial,m)
    steps,states=control.plan(check);original=worker.block_optimum
    def controlled(stop,fail=None):
        idx=0;m=Memory(fail)
        def stub(points,index,n,rows,check=lambda:None,work=None):
            nonlocal idx
            r=steps[idx];assert tuple(rows)==r['rows'];idx+=1;v=r['item']
            return {'score':v[0],'X':v[1],'Y':v[2],'Z':v[3],'points':r['points'],'domains':r['domains'],
                    'zero':False,'optimum_established':True,'enumeration_exhausted':True}
        worker.block_optimum=stub
        try:r=worker.drive(initial,publish=m.publish,save_move=m.move,save_zero=m.zero,stop_after=stop)
        finally:worker.block_optimum=original
        return r,m
    for name,count in [('nonimprovement',1),('first_positive',4),('global_cap',16)]:
        r,m=controlled(count);assert r['error'] is None
        a=deepcopy(r['authority'])
        if count==16:a['status']='block_cap'
        save(name,a,initial,m)
    assert cases['first_positive']['last_start_charge']=={'started':4,'completed':3,'accepted':0}
    assert cases['first_positive']['counters']=={'started':4,'completed':4,'accepted':1}
    r,m=controlled(None,'accept');assert r['status']=='error'
    save('positive_orphan',r['authority'],initial,m,[{'kind':'orphan_move','ref':m.moves[-1]}])
    zinitial=worker.new_authority(((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3)),4);m=Memory('accept_zero')
    r=worker.drive(zinitial,publish=m.publish,save_move=m.move,save_zero=m.zero);assert r['status']=='error'
    save('saved_zero_old_pending',r['authority'],zinitial,m,[{'kind':'saved_witness','ref':m.witness},{'kind':'orphan_move','ref':m.moves[-1]}])
    rejected=[]
    def reject(name,case,mutate):
        a,ini,mem,side=inputs[case];a=deepcopy(a);m=Memory();m.blobs=deepcopy(mem.blobs);mutate(a,m.blobs)
        try:inspect(a,ini,m,side)
        except (ValueError,KeyError,TypeError):rejected.append(name)
        else:raise AssertionError('accepted corruption '+name)
    reject('bool_zero_counter','initial',lambda a,b:a['counters'].__setitem__('accepted',False))
    reject('bool_cursor','initial',lambda a,b:a.__setitem__('cursor',False))
    reject('bool_seq','pending',lambda a,b:a['attempts'][0].__setitem__('seq',True))
    reject('wrong_start_charge','pending',lambda a,b:a['counters'].__setitem__('started',0))
    reject('pending_lost','pending',lambda a,b:a.__setitem__('pending',None))
    reject('wrong_order','pending',lambda a,b:a['attempts'][0].__setitem__('order_hash','0'*64))
    reject('wrong_rows','pending',lambda a,b:a['attempts'][0].__setitem__('rows',[0,2,3]))
    reject('wrong_before_state','pending',lambda a,b:a['attempts'][0].__setitem__('state_hash','0'*64))
    reject('wrong_after_state','first_positive',lambda a,b:a['attempts'][-1].__setitem__('after_hash','0'*64))
    reject('missing_move','first_positive',lambda a,b:a.__setitem__('artifacts',[]))
    reject('bad_move_hash','first_positive',lambda a,b:a['artifacts'][0].__setitem__('sha256','0'*64))
    reject('old_cursor_after_accept','first_positive',lambda a,b:a.__setitem__('cursor',1))
    reject('positive_partial','first_positive',lambda a,b:a['attempts'][-1].__setitem__('enumeration_exhausted',False))
    reject('missing_zero_witness','zero',lambda a,b:a.__setitem__('witness',None))
    reject('unexhausted_cap','initial',lambda a,b:a.__setitem__('status','block_cap'))
    reject('unexhausted_list','initial',lambda a,b:a.__setitem__('status','restricted_candidate_list_exhausted'))
    reject('bad_domain','nonimprovement',lambda a,b:a['attempts'][0]['domains'].__setitem__(0,[0,1,2]))
    reject('bad_minimum_columns','nonimprovement',lambda a,b:a['attempts'][0]['minimum'].__setitem__(1,[False]))
    assert sha(worker.__file__)==WORKER_SHA;check()
    return {'passed':True,'worker_sha256':WORKER_SHA,'helper_sha256':sha(chain.__file__),'source_sha256':sha(__file__),
            'cases':cases,'corruption_rejections':rejected,'elapsed_seconds':time.monotonic()-start,
            'limits':'Memory callbacks/synthetic wrappers. Positive multiaccept/nonimprovement route uses disclosed nonoptimal control stub with real direct point scores, not minimum evidence. No actual input or receipt acceptance.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-chain-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'cases':len(result['cases']),'rejections':len(result['corruption_rejections']),
                     'helper_sha256':sha(chain.__file__),'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
