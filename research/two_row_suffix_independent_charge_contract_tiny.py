"""One real n4 capped pair verifies start-charge versus completed-authority timing."""
import hashlib
import json
from pathlib import Path
from research import two_row_suffix75 as worker
from research import two_row_suffix_independent_authority_audit as independent

WORKER_SHA='fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    assert sha(worker.__file__)==WORKER_SHA
    points=((0,0),(0,1),(1,2),(2,1),(2,3),(3,2),(3,3))
    base={'row_started':308,'row_completed':308,'pair_started':95,'pair_completed':95,'accepted':28}
    a=worker.new_authority(points,4,base=base,row_complete=True,pair_prefix=0)
    publications=[]
    def publish(value,tag):publications.append((tag,worker.clone(value)))
    def forbidden(*args):raise AssertionError('fixture must have no acceptance')
    result=worker.drive(a,publish=publish,save_move=forbidden,save_zero=forbidden)
    assert result['status']=='pair_cap' and result['error'] is None
    assert [tag for tag,value in publications]==['start','complete']
    start,complete=[value for tag,value in publications]
    expected_charge=dict(base,pair_started=96)
    expected_final=dict(base,pair_started=96,pair_completed=96)
    assert start['counters']==result['attempted_charge']==expected_charge
    assert complete['counters']==result['authority']['counters']==expected_final
    assert result['authority']['pending'] is None and result['authority']['attempts'][0]['outcome']=='complete'
    assert independent.recount(result['authority']['points'],4,lambda:None)['U']==a['U']==1
    assert sha(worker.__file__)==WORKER_SHA
    return {'passed':True,'scope':'One synthetic n4 real optimizer; source-supported synthetic imported row coverage; no actual loaders/geometry.',
            'worker_sha256':WORKER_SHA,'source_sha256':sha(__file__),'last_started_charge':result['attempted_charge'],
            'last_completed_authority':result['authority']['counters'],'status':result['status'],
            'geometry':'unchanged independently recounted n4 U1','limits':'Memory publications only; no filesystem or actual-history claim.'}
if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-charge-contract-tiny.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
