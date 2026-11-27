"""Disclosed n4 control-only stubs for positive multiaccept and global16 accounting."""
import hashlib
import json
from pathlib import Path
import resource
import time
from research import restricted_three_row_independent_oracle as oracle
from research import restricted_three_row_independent_worker_audit as support
from research import restricted_three_row75 as worker

WORKER_SHA='87e69fb151cbad1677aab5605aa734f2d38ca8c6c68c2b8b8d7503a8d93b32ce'
POINTS=((0,0),(0,1),(0,2),(0,3),(1,1),(2,2),(3,3))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def plan(check):
    points=POINTS;cursor=accepted=0;steps=[];states=[]
    for attempt in range(16):
        check();p=oracle.profile(points,4);rows=p['blocks'][cursor];t=oracle.tables(points,4,rows)
        item=(p['U'],*t['current'])
        if cursor==len(p['blocks'])-1:
            choices=[]
            for cols in oracle.assignments(t['domains'],sum(map(len,t['current']))):
                score=oracle.raw(oracle.replaced(t,cols))
                if 0<score<p['U']:choices.append((score,*cols))
            if choices:item=min(choices,key=lambda v:(-v[0],*v[1:]))
        strict=item[0]<p['U'];after=oracle.replaced(t,item[1:]) if strict else points
        steps.append({'state_hash':p['state_hash'],'rows':rows,'cursor':cursor,'before':p['U'],'item':item,
                      'domains':t['domains'],'points':after,'strict':strict})
        if strict:accepted+=1;cursor=0;points=after
        else:cursor+=1
        states.append({'points':support.normalized(points),'U':oracle.raw(points),'state_hash':oracle.identity(4,points),
                       'generation':accepted,'counters':{'started':attempt+1,'completed':attempt+1,'accepted':accepted},
                       'cursor':cursor,'pending':None})
        if cursor==len(oracle.profile(points,4)['blocks']):break
    return steps,states

def run():
    start=time.monotonic();assert sha(worker.__file__)==WORKER_SHA
    def check():
        if time.monotonic()-start>10:raise TimeoutError('fixed10-second control preparation cap')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>128*1024*1024:raise MemoryError('fixed128MiB target')
    steps,states=plan(check)
    assert len(steps)==16 and states[-1]['U']>0 and states[-1]['counters']['accepted']>1
    original=worker.block_optimum;observed=[]
    def execute(a,m,offset=0,stop=None):
        cursor=offset;events=[]
        def stub(points,index,n,rows,check=lambda:None,work=None):
            nonlocal cursor
            item=steps[cursor];assert oracle.identity(n,points)==item['state_hash'] and tuple(rows)==item['rows'];cursor+=1
            val=item['item']
            return {'score':val[0],'X':val[1],'Y':val[2],'Z':val[3],'points':item['points'],'zero':False,
                    'optimum_established':True,'enumeration_exhausted':True,'domains':item['domains']}
        worker.block_optimum=stub
        try:return worker.drive(a,publish=m.publish,save_move=m.save,save_zero=m.zero,observe=events.append,stop_after=stop),events
        finally:worker.block_optimum=original
    initial=worker.new_authority(POINTS,4);mem=support.Memory();result,events=execute(initial,mem)
    assert result['status']=='block_cap' and result['error'] is None and support.projection(result['authority'])==states[-1]
    expected=[{'rows':list(s['rows']),'minimum':support.normalized(s['item']),'strict':s['strict'],'before_hash':s['state_hash']} for s in steps]
    assert events==expected
    for cut in range(17):
        check();m=support.Memory();left,early=execute(initial,m,stop=cut)
        restored=worker.inspect_recovery(worker.authority_bytes(left['authority']),m.blobs.__getitem__)
        right,later=execute(restored,m,offset=cut)
        assert right['status']=='block_cap' and right['error'] is None and early+later==expected
        assert support.projection(right['authority'])==states[-1]
    pending_stops=0
    for tag,raw in mem.publications:
        if tag!='start':continue
        a=worker.inspect_recovery(raw,mem.blobs.__getitem__);m=support.Memory();r=worker.drive(a,publish=m.publish)
        assert r['status']=='error' and not m.publications and support.projection(r['authority'])==support.projection(a)
        pending_stops+=1
    cap=worker.clone(result['authority'])
    if cap['orders'] is None:
        p,idx,U=worker.kernel.build_index(cap['points'],4);cap['orders']=worker.make_orders(p,idx,4,cap['state_hash'])
    try:worker.plan_start(cap)
    except worker.SearchStop as exc:assert str(exc)=='block_cap'
    else:raise AssertionError('17th start allowed')
    # Genuine nonimproving full terminal under a disclosed current-return optimizer stub.
    def same(points,index,n,rows,check=lambda:None,work=None):
        t=oracle.tables(points,n,rows);v=oracle.raw(points)
        return {'score':v,'X':t['current'][0],'Y':t['current'][1],'Z':t['current'][2],'points':points,'zero':False,
                'optimum_established':True,'enumeration_exhausted':True,'domains':t['domains']}
    worker.block_optimum=same;m=support.Memory()
    try:terminal=worker.drive(initial,publish=m.publish,save_move=m.save,save_zero=m.zero)
    finally:worker.block_optimum=original
    assert terminal['status']=='restricted_candidate_list_exhausted' and terminal['error'] is None
    assert terminal['authority']['counters']['accepted']==0 and terminal['authority']['cursor']==len(oracle.profile(POINTS,4)['blocks'])
    assert sha(worker.__file__)==WORKER_SHA;check()
    return {'passed':True,'scope':'n4 control-only optimizer stubs. Every declared point score and replacement support independently checked; minima are intentionally not actual optima.',
            'worker_sha256':WORKER_SHA,'source_sha256':sha(__file__),'steps':support.normalized(steps),
            'final':states[-1],'split_reload_cases':17,'pending_refusals':pending_stops,'seventeenth_start_rejected':True,
            'positive_terminal_stub_completed':terminal['authority']['counters']['completed'],
            'elapsed_seconds':time.monotonic()-start,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'limits':'These trajectories do not show geometric local minima or pair-stuck escape. Memory callbacks, no filesystem/validator lifecycle claim.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-control-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'accepted':result['final']['counters']['accepted'],'final_score':result['final']['U'],
                     'elapsed':result['elapsed_seconds'],'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
