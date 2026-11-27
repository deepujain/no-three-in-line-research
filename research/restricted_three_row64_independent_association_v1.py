"""Independent fixed64 semantic association review on the declared52-role graph."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row64 as worker
from research import restricted_three_row64_independent_synthetic_graph as graph
from research import restricted_three_row64_independent_byte_fixture as byte_fixture

WORKER_SHA='5989d8c19e1b9168dd157a30de4c05ff1d345a8d33970c1daeabd8ae900ebcd0'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reseal(v,mirror=False):
    d=v['docs'];a=d[worker.AUTHORITY]['payload']
    d[worker.AUTHORITY]['payload_sha256']=worker.hashed(a)
    raw=byte_fixture.pad(worker.compact(d[worker.AUTHORITY]),9297)
    identity=hashlib.sha256(raw).hexdigest();v['authority_raw']=raw
    v['metadata']['artifacts'][worker.AUTHORITY]=identity
    v['pins'][str(worker.ROOT/worker.AUTHORITY)]=identity
    d[worker.REPORT]['authority_sha256']=identity;d[worker.REPORT]['authority_bytes']=len(raw)
    d[worker.AUDIT]['artifact_hashes'][worker.AUTHORITY]=identity
    if mirror:
        d[worker.REPORT]['attempts']=deepcopy(a['attempts'])
        d[worker.AUDIT]['chain']['observations']=[{k:r[k] for k in ('seq','state_hash','rows','cursor','outcome')} for r in a['attempts']]


def fixture():
    v=graph.fixture();v['metadata']['artifact_byte_sizes']=byte_fixture.contract_sizes()
    v['pins'][str(worker.ROOT/worker.HANDOFF_PATH)]=worker.HANDOFF_SHA
    reseal(v)
    return v


def associated(v):
    # Declared n75 metadata deliberately carries only an already approved n4
    # point pair. These spies establish identity links, not geometry/row shape.
    old=tuple(map(tuple,graph.OLD_POINTS));new=tuple(map(tuple,graph.NEW_POINTS))
    def normalize(values,n):
        assert n==75
        return tuple(tuple(p) for p in values)
    def identity(n,points):
        assert n==75
        p=tuple(map(tuple,points))
        if p==old:return worker.PREDECESSOR
        if p==new:return worker.FIXED_STATE
        raise ValueError('unrecognized synthetic structural identity')
    def forbidden(*args,**kwargs):raise AssertionError('forbidden actual/historical geometry or loader')
    with patch.object(worker,'validate_points',normalize),patch.object(worker,'normalized_sha256',identity),\
         patch.object(worker.engine.kernel,'validate_points',normalize),patch.object(worker.engine.kernel,'normalized_sha256',identity),\
         patch.object(worker.engine.kernel,'dual_validate',forbidden),patch.object(worker.engine.kernel,'build_index',forbidden),\
         patch.object(worker.engine.shared,'load_handoff',forbidden),patch.object(worker.engine,'run',forbidden),\
         patch.object(worker.adapter,'audit',forbidden),patch.object(worker.adapter.chain,'audit_chain',forbidden):
        return worker.associate_documents(v['docs'],v['metadata'],v['pins'],v['authority_raw'],runtime=v['runtime'])


def run():
    assert sha(worker.__file__)==WORKER_SHA
    sources={str(Path(p).relative_to(worker.ROOT)):sha(p) for p in (__file__,worker.__file__,graph.__file__,byte_fixture.__file__)}
    v=fixture();points,info=associated(v)
    assert points==tuple(map(tuple,graph.NEW_POINTS)) and info['score']==64
    assert set(v['docs'][worker.INITIAL])=={'n','points','score','state_hash','counters','order_sha256','handoff'}
    assert points is not v['docs'][worker.MOVE]['points']
    def doc(name,key,value):return lambda v:v['docs'][name].__setitem__(key,value)
    def authority(key,value):
        def mutate(v):v['docs'][worker.AUTHORITY]['payload'].__setitem__(key,value);reseal(v,True)
        return mutate
    def record(seq,key,value):
        def mutate(v):v['docs'][worker.AUTHORITY]['payload']['attempts'][seq-1].__setitem__(key,value);reseal(v,True)
        return mutate
    mutations={
        'metadata_wrong_score':lambda v:v['metadata'].__setitem__('unweighted_score',65),
        'metadata_bool_n':lambda v:v['metadata'].__setitem__('n',True),
        'metadata_missing_role':lambda v:v['metadata']['artifacts'].pop(worker.INITIAL),
        'metadata_bad_digest':lambda v:v['metadata']['artifacts'].__setitem__(worker.INITIAL,'bad'),
        'metadata_bool_size':lambda v:v['metadata']['artifact_byte_sizes'].__setitem__(worker.INITIAL,True),
        'metadata_wrong_aggregate':lambda v:v['metadata']['artifact_byte_sizes'].__setitem__(worker.INITIAL,1),
        'missing_input_pin':lambda v:v['pins'].pop(str(worker.ROOT/worker.MOVE)),
        'missing_source_pin':lambda v:v['pins'].pop(str(worker.ROOT/'research/restricted_three_row75.py')),
        'old_metadata_identity':lambda v:v['docs'][worker.OLD_METADATA]['artifacts'].__setitem__(graph.OLD_REPORT,'0'*64),
        'old_report_failure':doc(graph.OLD_REPORT,'accepted',False),
        'initial_missing_key':lambda v:v['docs'][worker.INITIAL].pop('order_sha256'),
        'initial_invented_generation':doc(worker.INITIAL,'generation',0),
        'initial_invented_cursor':doc(worker.INITIAL,'cursor',0),
        'initial_wrong_order':doc(worker.INITIAL,'order_sha256','0'*64),
        'initial_bool_counter':lambda v:v['docs'][worker.INITIAL]['counters'].__setitem__('accepted',False),
        'initial_wrong_points':doc(worker.INITIAL,'points',deepcopy(graph.NEW_POINTS)),
        'authority_wrong_origin':authority('origin_hash','0'*64),
        'authority_wrong_state':authority('state_hash',worker.PREDECESSOR),
        'authority_bool_generation':authority('generation',True),
        'authority_pending':authority('pending',16),
        'authority_old_cursor':authority('cursor',16),
        'record_bool_sequence':record(1,'seq',True),
        'record_wrong_sequence':record(2,'seq',3),
        'record_wrong_cursor':record(2,'cursor',0),
        'record_wrong_prior_order':record(2,'order_hash','0'*64),
        'record_bad_order_schema':record(2,'order_hash','bad'),
        'record_wrong_after_state':record(2,'after_hash','0'*64),
        'record_partial_positive':record(2,'enumeration_exhausted',False),
        'record_missing_current_column':record(2,'domains',[[0,2,3,4],[0,1,2,3],[0,1,2,3]]),
        'record_bool_column':record(2,'minimum',[65,[False,1],[0,2],[0,3]]),
        'record_wrong_selected_load':record(2,'minimum',[65,[0],[0,2],[0,3]]),
        'move_wrong_columns':doc(worker.MOVE,'points',deepcopy(graph.OLD_POINTS)),
        'move_wrong_old_cursor':doc(worker.MOVE,'old_cursor',14),
        'move_missing_field':lambda v:v['docs'][worker.MOVE].pop('domains'),
        'audit_failed':doc(worker.AUDIT,'accepted',False),
        'audit_wrong_count':doc(worker.AUDIT,'effective_pins',228),
        'audit_bool_states':lambda v:v['docs'][worker.AUDIT]['chain'].__setitem__('unique_states_recounted',True),
        'audit_wrong_scores':lambda v:v['docs'][worker.AUDIT]['chain'].__setitem__('accepted_scores',[65,63]),
        'audit_wrong_runtime':doc(worker.AUDIT,'runtime_sha256','0'*64),
        'audit_wrong_helper':doc(worker.AUDIT,'helper_sha256','0'*64),
        'audit_missing_artifact':lambda v:v['docs'][worker.AUDIT]['artifact_hashes'].pop(worker.MOVE),
        'audit_wrong_observation':lambda v:v['docs'][worker.AUDIT]['chain']['observations'][0].__setitem__('cursor',1),
        'audit_wrong_resource':lambda v:v['docs'][worker.AUDIT]['resources'].__setitem__('peak_sampled_rss_kib',1),
        'report_postcompletion_charge':doc(worker.REPORT,'last_attempted_charge',dict(started=16,completed=16,accepted=1)),
        'report_failed':doc(worker.REPORT,'accepted',False),
        'receipt_failed':lambda v:v['docs'][worker.RECEIPT]['gate'].__setitem__('returncode',1),
        'guard_nested_shape':doc(worker.GUARD,'gate',graph.gate()),
        'guard_wrong_argv':lambda v:v['docs'][worker.GUARD]['argv'].__setitem__(1,'wrong.py'),
        'guard_wrong_audit':doc(worker.GUARD,'audit_output_sha256','0'*64),
        'guard_missing_source':lambda v:v['docs'][worker.GUARD]['source_pins'].pop(graph.AUDIT_HELPER),
        'guard_extra_source':lambda v:v['docs'][worker.GUARD]['source_pins'].__setitem__('research/extra.py','0'*64),
        'guard_bad_cleanup_time':doc(worker.GUARD,'cleanup_elapsed_seconds',-1),
    }
    # A true nested guard replaces the flat object; merely adding an ignored
    # descriptive field is not a malformed producer contract.
    mutations['guard_nested_shape']=lambda v:v['docs'].__setitem__(worker.GUARD,{'status':'completed','gate':graph.gate()})
    rejected=[];unexpected=[]
    for name,mutate in mutations.items():
        v=fixture();mutate(v)
        try:associated(v)
        except (ValueError,KeyError,TypeError) as error:rejected.append(dict(case=name,error=str(error)))
        else:unexpected.append(name)
    assert sha(worker.__file__)==WORKER_SHA
    return dict(passed=not unexpected,sources=sources,baseline=True,mutation_count=len(mutations),rejections=rejected,
                unexpected_acceptances=unexpected,
                scope='Real new associate_documents, real frozen historical/run association and authority validator; explicit structural identity spies on approved n4pair with declared65/64metadata. No actual inputs, geometry or optimizer.',
                limitations='Authority envelope bytes are genuinely hashed; other role digests are declared labels. This tests semantic associations, not actual saved-state acceptance or complete loader/run orchestration.')


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-association-v1.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],mutations=result['mutation_count'],rejections=len(result['rejections']),
                         unexpected=result['unexpected_acceptances'],source_sha256=sha(__file__),evidence_sha256=sha(path))))
