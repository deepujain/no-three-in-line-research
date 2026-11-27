"""Independent cooperative-interruption and partial-result checks; n4 memory callbacks."""
import hashlib
import json
from pathlib import Path
import resource
import time
from research import restricted_three_row_independent_oracle as oracle
from research import restricted_three_row_independent_worker_audit as support
from research import restricted_three_row75 as worker

WORKER_SHA='87e69fb151cbad1677aab5605aa734f2d38ca8c6c68c2b8b8d7503a8d93b32ce'
FIXTURES=(((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3)),((0,0),(0,1),(0,2),(0,3),(1,1),(2,2),(3,3)))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    started=time.monotonic();assert sha(worker.__file__)==WORKER_SHA;cases=[];cuts=0
    def bound():
        if time.monotonic()-started>10:raise TimeoutError('fixed10-second interruption suite')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>128*1024*1024:raise MemoryError('fixed128MiB target')
    for points in FIXTURES:
        bound();a=worker.new_authority(points,4);calls=0
        def count():
            nonlocal calls
            calls+=1
        m=support.Memory();baseline=worker.drive(a,check=count,publish=m.publish,save_move=m.save,save_zero=m.zero)
        assert baseline['status']=='zero' and baseline['error'] is None
        for position in range(1,calls+1):
            bound();seen=0;mem=support.Memory()
            def interrupt():
                nonlocal seen
                seen+=1
                if seen==position:raise worker.SearchStop('synthetic_interrupt')
            result=worker.drive(a,check=interrupt,publish=mem.publish,save_move=mem.save,save_zero=mem.zero)
            assert result['status']=='synthetic_interrupt' and result['error'] is None
            durable=json.loads(mem.publications[-1][1])['payload'] if mem.publications else a
            assert result['authority']==durable
            assert oracle.raw(result['authority']['points'])==durable['U']
            if mem.publications:assert mem.publications[-1][0]=='start' and durable['pending']==durable['counters']['started']
            cuts+=1
        cases.append({'points':points,'cooperative_positions':calls})
    # Explicit rejection of a positive partial current result before cursor adoption.
    a=worker.new_authority(FIXTURES[1],4);pending=worker.plan_start(a);rows=pending['attempts'][-1]['rows'];t=oracle.tables(a['points'],4,rows)
    partial={'score':a['U'],'X':t['current'][0],'Y':t['current'][1],'Z':t['current'][2],
             'points':a['points'],'zero':False,'optimum_established':True,'enumeration_exhausted':False,'domains':t['domains']}
    saved=worker.clone(pending)
    try:worker.plan_nonimprovement(pending,partial)
    except ValueError as exc:assert 'partial positive' in str(exc)
    else:raise AssertionError('partial positive adopted')
    assert pending==saved
    assert sha(worker.__file__)==WORKER_SHA;bound()
    return {'passed':True,'worker_sha256':WORKER_SHA,'source_sha256':sha(__file__),'cases':cases,
            'interruption_cuts':cuts,'partial_positive_rejection':True,'elapsed_seconds':time.monotonic()-started,
            'limits':'Cooperative-check interruptions with memory callbacks, not filesystem crash points or validator timing. Real n4 traces reach zero directly, so no interruption after a real positive accepted state is claimed.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-interruptions.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'cuts':result['interruption_cuts'],'elapsed':result['elapsed_seconds'],
                     'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
