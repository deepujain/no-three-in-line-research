"""Author SOURCE/TINY association/orchestration checks; no actual input reads.

The semantic graph has declared hash labels and n4 point/identity spies for
historical65/64 metadata. Genuine byte reads are separate closed-source cases.
"""
from copy import deepcopy
import gc
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import weakref
from research import restricted_three_row64 as w
from research import restricted_three_row64_independent_synthetic_graph as graph
from research import restricted_three_row75_tiny as old_tiny


def sizes():
    prefix='data/two-row-descent75-v1/'
    values=[1553,1553,1553,1555,1555,1555,1555,1555,1555,1555,1555,1555,1555,1554,1555,1556,1557,1556,1557,1557,1557,1557,1556,1557,1557,1556,1555,1557]
    result={prefix+f'improvement-{i:03d}.json':v for i,v in enumerate(values,1)}
    result.update(dict(zip((prefix+'report.json',prefix+'completed-boundary.json',prefix+'initial.json',prefix+'best.json'),(25842,12530,1587,2138))))
    result.update({'data/experiments/shepherd-two-row-descent75-v1.json':11817,'data/two-row-descent75-source-pins.json':9707,
        'data/two-row-descent75-independent-chain-actual-audit.json':68150,'data/two-row-descent75-independent-chain-actual-owned-guard.json':1378,
        'research/two_row_descent75_actual_chain_adapter.py':11846,'research/two_row_descent_independent_chain_audit.py':13289,
        'research/two-row-descent75-independent-actual-acceptance-review.md':5695,
        w.OLD_METADATA:5645,w.REPORT:49235,w.RECEIPT:30748,w.MANIFEST:28283,w.AUTHORITY:9297,w.INITIAL:1698,w.MOVE:1743,
        w.AUDIT:6908,w.GUARD:1711,'research/restricted-three-row-independent-actual-audit-preparation-addendum.md':7293,
        w.SOURCE_REVIEW:3129,'research/restricted-three-row75-independent-actual-v1-metadata-review.md':1923})
    assert set(result)==w.ROLES and sum(result.values())==355145
    return result


def refresh_authority(f):
    envelope=f['docs'][w.AUTHORITY];envelope['payload_sha256']=w.hashed(envelope['payload'])
    raw=w.compact(envelope);assert len(raw)<=9297
    raw+=b' '*(9297-len(raw));sha=hashlib.sha256(raw).hexdigest();f['authority_raw']=raw
    f['metadata']['artifacts'][w.AUTHORITY]=sha;f['pins'][str(w.ROOT/w.AUTHORITY)]=sha
    f['docs'][w.REPORT]['authority_sha256']=sha;f['docs'][w.REPORT]['authority_bytes']=len(raw)
    f['docs'][w.AUDIT]['artifact_hashes'][w.AUTHORITY]=sha


def fixture():
    f=graph.fixture();f['metadata']['artifact_byte_sizes']=sizes()
    f['pins'][str(w.ROOT/w.HANDOFF_PATH)]=w.HANDOFF_SHA;refresh_authority(f)
    return f


def associated(f):
    # Only structure/identity are spied; the two historical semantic association
    # helpers execute their real source predicates. No raw score is computed.
    def points(values,n):
        assert n==75
        normalized=tuple(sorted(tuple(p) for p in values))
        assert normalized in (tuple(map(tuple,graph.OLD_POINTS)),tuple(map(tuple,graph.NEW_POINTS)))
        return normalized
    def identity(n,values):
        assert n==75
        return w.FIXED_STATE if list(map(list,values))==graph.NEW_POINTS else w.PREDECESSOR
    def forbidden(*args,**kwargs):raise AssertionError('forbidden actual/historical geometry entrypoint')
    with patch.object(w.engine.kernel,'validate_points',points),patch.object(w.engine.kernel,'normalized_sha256',identity),\
        patch.object(w,'validate_points',points),patch.object(w,'normalized_sha256',identity),\
        patch.object(w.engine.shared,'load_handoff',forbidden),patch.object(w.engine.kernel,'dual_validate',forbidden),\
        patch.object(w.engine.kernel,'build_index',forbidden),patch.object(w.engine,'run',forbidden),\
        patch.object(w.adapter,'audit',forbidden),patch.object(w.adapter.chain,'audit_chain',forbidden):
        return w.associate_documents(f['docs'],f['metadata'],f['pins'],f['authority_raw'],runtime=f['runtime'])


def semantic():
    f=fixture();points,info=associated(f)
    assert list(map(list,points))==graph.NEW_POINTS and info['score']==64 and info['historical_counters']==w.FINAL_COUNTS
    mutators=[('initial generation invented',lambda f:f['docs'][w.INITIAL].update(generation=0)),
        ('initial cursor invented',lambda f:f['docs'][w.INITIAL].update(cursor=0)),
        ('initial order',lambda f:f['docs'][w.INITIAL].update(order_sha256='0'*64)),
        ('charge completions',lambda f:f['docs'][w.REPORT]['last_attempted_charge'].update(completed=16)),
        ('charge accepted',lambda f:f['docs'][w.REPORT]['last_attempted_charge'].update(accepted=1)),
        ('guard nested',lambda f:f['docs'].__setitem__(w.GUARD,{'gate':f['docs'][w.GUARD]})),
        ('guard argv',lambda f:f['docs'][w.GUARD].update(argv=[])),
        ('guard output',lambda f:f['docs'][w.GUARD].update(audit_output_sha256='0'*64)),
        ('guard sources',lambda f:f['docs'][w.GUARD]['source_pins'].pop(w.SOURCE_REVIEW)),
        ('guard cleanup time bool',lambda f:f['docs'][w.GUARD].update(cleanup_elapsed_seconds=False)),
        ('audit resources',lambda f:f['docs'][w.AUDIT]['resources'].update(peak_sampled_rss_kib=2)),
        ('audit runtime',lambda f:f['docs'][w.AUDIT].update(runtime_sha256='0'*64)),
        ('audit helper',lambda f:f['docs'][w.AUDIT].update(helper_sha256='0'*64)),
        ('audit count boolean',lambda f:f['docs'][w.AUDIT]['chain'].update(new_accepted_moves=True)),
        ('audit observation',lambda f:f['docs'][w.AUDIT]['chain']['observations'][0].update(cursor=1)),
        ('audit digest roles',lambda f:f['docs'][w.AUDIT]['artifact_hashes'].pop(w.MOVE)),
        ('old accepted chain',lambda f:f['docs'][graph.OLD_AUDIT]['chain'].update(states_recounted=28)),
        ('old metadata id',lambda f:f['docs'][w.OLD_METADATA]['artifacts'].__setitem__(graph.OLD_BEST,'0'*64)),
        ('prior pin count',lambda f:f['docs'][w.MANIFEST].pop(next(k for k in f['docs'][w.MANIFEST] if 'synthetic-only' in k))),
        ('missing source',lambda f:f['pins'].pop(str(w.ROOT/'research/restricted_three_row75.py'))),
        ('old source drift',lambda f:f['pins'].__setitem__(f['runtime'],'0'*64)),
        ('extra parsed role',lambda f:f['docs'].__setitem__('unexpected',{})),
        ('move event',lambda f:f['docs'][w.MOVE].update(old_cursor=14)),
        ('move columns',lambda f:f['docs'][w.MOVE]['minimum'].__setitem__(1,[0,1])),
        ('active metadata score',lambda f:f['metadata'].update(unweighted_score=65)),
        ('metadata role',lambda f:f['metadata']['artifacts'].pop(w.MOVE)),
        ('metadata bool',lambda f:f['metadata'].update(artifact_count=True)),
        ('metadata aggregate',lambda f:f['metadata']['artifact_byte_sizes'].__setitem__(w.MOVE,1744))]
    rejected=[]
    for name,mutator in mutators:
        case=deepcopy(f);mutator(case)
        try:associated(case)
        except (ValueError,KeyError,TypeError,AssertionError):rejected.append(name)
        else:raise AssertionError('accepted mutation: '+name)
    for name,mutator in [('old selected load',lambda a:a['attempts'][0]['minimum'].__setitem__(1,[0])),
        ('old current exclusion',lambda a:a['attempts'][0]['domains'].__setitem__(0,[0,1,2,4])),
        ('selected bool',lambda a:a['attempts'][0]['minimum'].__setitem__(1,[0,True])),
        ('final cap count',lambda a:a['counters'].update(started=15)),('pending',lambda a:a.update(pending=16))]:
        case=deepcopy(f);mutator(case['docs'][w.AUTHORITY]['payload']);refresh_authority(case)
        try:associated(case)
        except (ValueError,KeyError,TypeError,AssertionError):rejected.append(name)
        else:raise AssertionError('accepted rehashed mutation: '+name)
    return {'valid_graph':True,'initial_seven_keys_accepted':True,'mutations_rejected':rejected,
            'scope':'Declared historical hash labels, structural point/identity spies; real frozen old-association predicates, no geometry/byte claim.'}


def parser_quotas():
    result=[]
    for value,field,limit in [([None]*20,'NODE_CAP',1),([[[0]]],'DEPTH_CAP',1),('x'*1000,'GRAPH_CAP',100),([None]*20,'AUX_CAP',100)]:
        budget=w.GraphBudget();setattr(budget,field,limit)
        try:budget.check(value)
        except ValueError:result.append(field)
        else:raise AssertionError('graph quota not enforced')
    for raw in (b'{"a":0,"a":1}',b'NaN',b'Infinity',b'{"x":-Infinity}'):
        try:w.decode_json(raw)
        except ValueError:pass
        else:raise AssertionError('bad JSON accepted')
    assert w.GraphBudget().check({'a':[0,1,2]})['nodes']>0
    return result


def bytes_reader():
    with tempfile.TemporaryDirectory(prefix='fixed64-byte-reader-') as directory:
        path=Path(directory)/'synthetic.json';raw=b'{"synthetic":true}';path.write_bytes(raw)
        source=w.DiskSource(directory,lambda:None);sha=hashlib.sha256(raw).hexdigest()
        source.scan(path.name,len(raw),sha);assert source.read(path.name,len(raw),sha)==raw
        rejected=0
        for size,digest in ((len(raw)+1,sha),(len(raw),'0'*64)):
            for method in (source.scan,source.read):
                try:method(path.name,size,digest)
                except ValueError:rejected+=1
                else:raise AssertionError('incorrect byte identity accepted')
    return {'genuine_synthetic_scan_and_read':True,'wrong_size_digest_rejections':rejected}


class Index(dict):pass


def run_case(mode):
    refs=[];calls=[];fixture_points=tuple(map(tuple,graph.NEW_POINTS))
    with tempfile.TemporaryDirectory(prefix='fixed64-run-') as directory:
        root=Path(directory).resolve();out=root/'out';out.mkdir();(root/'src').mkdir();(root/'data').mkdir()
        verify=root/'src/verify.py';verify.write_text('synthetic verifier source')
        meta=root/w.HANDOFF_PATH;meta.write_text('synthetic metadata')
        source_ids={str((w.ROOT/name).resolve()):sha for name,sha in w.SOURCE_IDENTITIES.items()}
        paths=list(map(Path,source_ids))+[Path(w.__file__).resolve(),Path(sys.executable).resolve(),verify,meta]
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest=root/'pins.json';manifest.write_text(json.dumps(pins))
        authority={'n':75,'U':64,'state_hash':w.FIXED_STATE,'generation':0,'counters':dict(started=0,completed=0,accepted=0),
                   'cursor':0,'pending':None,'status':'active','artifacts':[],'attempts':[],'orders':{'sha256':'declared'},'witness':None}
        class Store:
            def __init__(self,out):self.out=out;self.publications=0;self.last_durable=None;self.uncertain=False
            def publish(self,a,tag):
                calls.append(tag)
                if mode=='initial_publication' and tag=='initialize':self.uncertain=True;raise OSError('synthetic initial publication failure')
                self.publications+=1;self.last_durable=w.clone(a);(self.out/'authority.json').write_bytes(w.compact(a))
            def save_move(self,m):raise AssertionError('stubbed drive never saves a move')
        def loader(*args):calls.append('association_exit');return fixture_points,{'synthetic':True}
        def dual(points,n,score,check):
            calls.append('dual64');assert (points,n,score)==(fixture_points,75,64)
            if mode=='validation_failure':raise ValueError('synthetic dual disagreement')
            return {'validators':[{'normalized_sha256':'0'*64 if mode=='validation_identity' else w.FIXED_STATE}]}
        def build(points,n,check,work):
            calls.append('build64');work['indexes_started']=1;value=Index();refs.append(weakref.ref(value))
            return points,value,65 if mode=='index_score' else 64
        def init(points,n,*,prepared,**kwargs):calls.append('new_authority');return w.clone(authority)
        def drive(a,*,prepared,**kwargs):
            calls.append('drive');assert calls.index('association_exit')<calls.index('dual64')<calls.index('build64')
            assert a['counters']==dict(started=0,completed=0,accepted=0) and len(refs)==1
            if mode in ('saved_old_authority','metadata_error','saved_zero'):
                ref=kwargs['save_zero'](fixture_points)
                if mode!='saved_old_authority':a.update(U=0,witness=ref,status='zero')
            if mode=='lost_charge':charge=dict(started=1,completed=0,accepted=0)
            else:charge=None
            return {'authority':a,'status':'zero' if a['U']==0 else 'search_deadline','error':None,'attempted_charge':charge}
        def zero(points,n,out,check,report):
            ref={'path':'witness','sha256':'a'*64,'bytes':1};report.update(witness_saved=True,witness=ref)
            if mode=='metadata_error':report['witness_metadata_error']='synthetic'
            return ref
        with patch.object(w,'ROOT',root),patch.object(w,'SOURCE_IDENTITIES',source_ids),patch.object(w,'HANDOFF_SHA',pins[str(meta)]),\
            patch.object(w,'FileStore',Store),patch.object(w,'load_handoff',loader),patch.object(w.engine.kernel,'dual_validate',dual),\
            patch.object(w,'normalized_sha256',lambda *args:w.FIXED_STATE),patch.object(w,'build',build),\
            patch.object(w,'new_authority',init),patch.object(w,'drive',drive),patch.object(w,'preserve_zero',zero):
            result=w.run(out,manifest,started=0,clock=lambda:1)
        assert result['accepted'] is (mode in ('normal','saved_zero')),(mode,result)
        gc.collect();assert all(ref() is None for ref in refs)
        if mode in ('validation_failure','validation_identity'):assert 'build64' not in calls
        if mode=='index_score':assert 'initialize' not in calls
        assert calls.count('dual64')==1 and calls.count('build64')<=1
    return {'mode':mode,'accepted':result['accepted'],'calls':calls,'indexes_released':True}


def main():
    result={'passed':True,'worker_sha256':w.digest(w.__file__),'tiny_sha256':w.digest(__file__),
        'semantic':semantic(),'parser_quotas':parser_quotas(),'bytes_reader':bytes_reader(),
        'orchestration':[run_case(mode) for mode in ('normal','validation_failure','validation_identity','index_score',
            'initial_publication','lost_charge','saved_old_authority','metadata_error','saved_zero')],
        'approved_real_tiny_controller':old_tiny.parity(),
        'scope':'Synthetic declared semantic graph, genuine temporary input bytes, quota checks, fully stubbed fixed64 orchestration and approved n2..4 controller only. No actual input or geometry.'}
    path=w.ROOT/'data/restricted-three-row64-author-tiny-v1.json'
    if path.exists():raise FileExistsError('preserve evidence')
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
