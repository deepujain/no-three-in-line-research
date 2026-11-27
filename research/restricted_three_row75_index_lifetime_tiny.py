"""Index lifetime regression: n4 control stubs plus fully stubbed run boundary.

No actual input. Declared n4 states have independent exact raw scores, but the
optimizer returns scripted nonminima to exercise multiple positive adoptions.
"""
import gc
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import weakref
from research import restricted_three_row75 as w
from research import restricted_three_row_independent_control_preparation as controls
from research import restricted_three_row_independent_worker_audit as support


class TrackedIndex(dict): pass


def drive_lifetime():
    steps,states=controls.plan(lambda:None); refs=[]; peaks=[]; calls=[0]
    def live():
        gc.collect();return sum(ref() is not None for ref in refs)
    def build(points,n,check,work):
        assert live() <= 1, 'old initial index retained before next candidate build'
        p,index,score=w.kernel.build_index(points,n,check,work)
        tracked=TrackedIndex(index);refs.append(weakref.ref(tracked));peaks.append(live())
        assert peaks[-1] <= 2
        return p,tracked,score
    def optimizer(points,index,n,rows,check,work):
        item=steps[calls[0]];calls[0]+=1
        assert w.kernel.normalized_sha256(n,points)==item['state_hash'] and tuple(rows)==item['rows']
        v=item['item']
        return {'score':v[0],'X':v[1],'Y':v[2],'Z':v[3],'points':item['points'],'zero':False,
                'optimum_established':True,'enumeration_exhausted':True,'domains':item['domains']}
    a=w.new_authority(controls.POINTS,4);work={};holder=[build(controls.POINTS,4,lambda:None,work)]
    memory=support.Memory();events=[]
    def observe(event):
        events.append(event)
        assert live()==1, 'initial or previous current index survives completed adoption'
    # Raw replacement functions: MagicMock call histories would themselves
    # retain every index argument and invalidate a lifetime measurement.
    with patch.object(w,'build',build),patch.object(w,'block_optimum',optimizer):
        result=w.drive(a,prepared=holder.pop(),publish=memory.publish,save_move=memory.save,
                       save_zero=memory.zero,observe=observe,work=work)
    assert not holder and result['status']=='block_cap' and result['error'] is None
    assert result['authority']['counters']==states[-1]['counters'] and len(events)==16
    assert result['authority']['counters']['accepted']==4 and live()==0
    return {'started':16,'positive_accepts':4,'indexes_built':len(refs),'maximum_live_tracked_indexes':max(peaks),
            'all_indexes_released_after_drive':True,'scope':'Real n4 geometry/rebuild, scripted optimizer nonminima; memory callbacks.'}


def run_transfer():
    refs=[];tuple_refs=[]
    with tempfile.TemporaryDirectory(prefix='three-row-run-lifetime-') as directory:
        root=Path(directory).resolve();out=root/'out';out.mkdir();(root/'src').mkdir();(root/'data').mkdir()
        (root/'src/verify.py').write_text('synthetic verify source')
        (root/w.HANDOFF_PATH).write_text('synthetic metadata')
        paths=[Path(w.__file__).resolve(),Path(w.kernel.__file__).resolve(),Path(w.shared.__file__).resolve(),
               root/'src/verify.py',root/w.HANDOFF_PATH,Path(sys.executable).resolve()]
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        manifest=root/'pins.json';manifest.write_text(json.dumps(pins))
        authority={'n':4,'U':65,'state_hash':'control','generation':0,'counters':{'started':0,'completed':0,'accepted':0},
                   'cursor':0,'pending':None,'status':'active','artifacts':[],'attempts':[],'orders':{'sha256':'control'},'witness':None}
        class Store:
            def __init__(self,out): self.out=out;self.publications=0;self.last_durable=None;self.uncertain=False
            def publish(self,a,tag):
                self.publications+=1;self.last_durable=w.clone(a);(self.out/'authority.json').write_bytes(w.compact(a))
            def save_move(self,move):raise AssertionError('no move in fully stubbed transfer test')
        def build(*args):
            index=TrackedIndex();refs.append(weakref.ref(index));return (),index,65
        def drive(a,*,prepared,**kwargs):
            # CPython's call stack can hold an additional transient reference;
            # inspect the actual caller locals rather than assuming its count.
            tuple_refs.append(sys.getrefcount(prepared))
            caller=inspect.currentframe().f_back
            retained=[name for name,value in caller.f_locals.items() if value is prepared or value is prepared[1]]
            assert not retained, 'run retains its prepared tuple/index: '+repr(retained)
            assert caller.f_locals['initial_state']==[]
            del caller
            return {'authority':a,'status':'search_deadline','error':None,'attempted_charge':None}
        with patch.object(w,'ROOT',root),patch.object(w,'FileStore',Store),patch.object(w,'load_handoff',lambda *args:((),{})),\
                patch.object(w,'build',build),patch.object(w,'new_authority',lambda *args,**kwargs:authority),patch.object(w,'drive',drive):
            report=w.run(out,manifest,started=0,clock=lambda:1)
        assert report['accepted'],report
        gc.collect();assert all(ref() is None for ref in refs)
    return {'no_initial_tuple_or_index_in_caller_locals':True,'index_released_after_stubbed_run':True,
            'scope':'Fully stubbed loader/index/authority/controller/storage; run ownership boundary only.'}


def main():
    result={'passed':True,'worker_sha256':w.digest(w.__file__),'source_sha256':w.digest(__file__),
            'drive_lifetime':drive_lifetime(),'run_transfer':run_transfer(),'scope':'SOURCE/TINY only, no actual input.'}
    path=w.ROOT/'data/restricted-three-row75-index-lifetime-tiny-v3-final.json'
    if path.exists():raise FileExistsError('preserve lifetime evidence')
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
