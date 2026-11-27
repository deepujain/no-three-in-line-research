"""Real fixed64 run orchestration with declared loader/geometry/controller spies."""
from copy import deepcopy
import gc
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import weakref
from research import restricted_three_row64 as worker
from research import restricted_three_row64_independent_synthetic_graph as graph

WORKER_SHA='e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
class Index(dict):pass


def case(mode):
    calls=[];refs=[];stores=[];outputs=[];drive_entered=False;reports_written=0
    points=tuple(map(tuple,graph.NEW_POINTS))
    info=dict(metadata_sha256=worker.HANDOFF_SHA,normalized_sha256=worker.FIXED_STATE,score=64,
              historical_counters=dict(started=16,completed=16,accepted=1))
    a=dict(n=75,points=list(map(list,points)),U=64,state_hash=worker.FIXED_STATE,origin_hash=worker.FIXED_STATE,
           generation=0,counters=dict(started=0,completed=0,accepted=0),cursor=0,pending=None,status='active',
           orders=dict(sha256='d'*64),attempts=[],artifacts=[],witness=None)
    def forbidden(*args,**kwargs):raise AssertionError('unallocated historical geometry/loader/controller')
    with tempfile.TemporaryDirectory(prefix='fixed64-independent-run-') as directory:
        root=Path(directory);out=root/'out';out.mkdir();manifest=root/'pins.json'
        pins={str(root/name):h for name,h in worker.SOURCE_IDENTITIES.items()}
        pins.update({str(Path(worker.__file__).resolve()):WORKER_SHA,str(root/'src/verify.py'):'a'*64,
                     str(Path(sys.executable).resolve()):'b'*64,str(root/worker.HANDOFF_PATH):worker.HANDOFF_SHA})
        if mode=='bad_manifest_input':pins[str(root/worker.HANDOFF_PATH)]='0'*64
        manifest.write_bytes(worker.compact(pins));declared={**pins,str(manifest):sha(manifest)}
        class Store:
            def __init__(self,path):
                self.out=path;self.publications=0;self.last_durable=None;self.uncertain=False;stores.append(self)
            def publish(self,value,tag):
                calls.append('publish:'+tag);self.publications+=1
                if (mode=='initial_publish_fail' and tag=='initialize') or (mode=='final_publish_fail' and tag=='final_stop'):
                    self.uncertain=True;raise OSError('injected publication failure')
                self.last_durable=deepcopy(value);(self.out/'authority.json').write_bytes(worker.compact(value))
            def save_move(self,move):raise AssertionError('no real optimizer/move in orchestration spy')
        def digest(path,check):
            check();key=str(Path(path).resolve())
            if key in declared:
                if mode=='post_pin_drift' and drive_entered and key==str(root/worker.HANDOFF_PATH):return '0'*64
                return declared[key]
            assert key==str(out/'authority.json'),'unexpected digest read '+key
            return sha(path)
        def load(p,check):
            calls.append('load');check()
            assert p==declared
            if mode=='loader_fail':raise ValueError('injected loader failure')
            return points,deepcopy(info)
        def dual(p,n,score,check):
            calls.append('dual');assert p is points and n==75 and score==64;check()
            # This stack condition proves the run boundary itself owns no
            # active association_frame activation; graph lifetime has separate tests.
            frame=inspect.currentframe().f_back
            while frame is not None:
                assert frame.f_code.co_name!='association_frame';frame=frame.f_back
            if mode=='dual_fail':raise ValueError('injected dual validation failure')
            h='0'*64 if mode=='dual_wrong_identity' else worker.FIXED_STATE
            return dict(validators=[dict(normalized_sha256=h),dict(normalized_sha256=h)])
        def build(p,n,check,work):
            calls.append('build');assert p is points and n==75;check()
            if mode=='build_fail':raise ValueError('injected initial build failure')
            work['indexes_started']=1;index=Index();refs.append(weakref.ref(index))
            p=tuple(map(tuple,graph.OLD_POINTS)) if mode=='build_wrong_identity' else points
            return p,index,65 if mode=='build_wrong_score' else 64
        def identity(n,p):
            assert n==75
            return worker.FIXED_STATE if p==points else worker.PREDECESSOR
        def authority(p,n,prepared,check,work):
            calls.append('new_authority');assert p is points and n==75 and prepared[0] is points and prepared[2]==64
            assert prepared[1] is refs[0]();check()
            return deepcopy(a)
        def zero(p,n,path,check,report):
            calls.append('save_zero');assert n==75 and path==out
            ref=dict(path='valid149.json',sha256='c'*64,bytes=1)
            report.update(witness_saved=True,witness=ref,witness_state_hash='zero')
            if mode=='zero_metadata_error':report['witness_metadata_error']='injected metadata error'
            return ref
        def drive(value,*,prepared,**kw):
            nonlocal drive_entered
            drive_entered=True;calls.append('drive')
            assert prepared[0] is points and prepared[1] is refs[0]() and prepared[2]==64
            frame=inspect.currentframe().f_back
            assert frame.f_locals['initial_state']==[]
            assert not [k for k,v in frame.f_locals.items() if v is prepared or v is prepared[1]]
            del frame
            assert value['origin_hash']==worker.FIXED_STATE and value['generation']==0
            assert value['counters']==dict(started=0,completed=0,accepted=0) and value['cursor']==0
            assert value['attempts']==value['artifacts']==[] and value['pending'] is None
            result=dict(authority=value,status='search_deadline',error=None,attempted_charge=None)
            if mode=='drive_error':result.update(status='error',error='injected controller error')
            if mode=='lost_started_charge':result['attempted_charge']=dict(started=1,completed=0,accepted=0)
            if mode in ('saved_witness_old_authority','zero_metadata_error','zero_clean'):
                ref=kw['save_zero'](points)
                if mode!='saved_witness_old_authority':
                    value=deepcopy(value);value.update(U=0,witness=ref,status='zero',generation=1,
                        counters=dict(started=1,completed=1,accepted=1))
                    result.update(authority=value,status='zero',attempted_charge=dict(started=1,completed=0,accepted=0))
            if mode=='uncertain_authority':stores[0].uncertain=True
            return result
        def output(path,value,**kw):
            nonlocal reports_written
            name=Path(path).name;outputs.append(name)
            if mode=='initial_file_fail' and name=='initial.json':raise OSError('injected initial artifact failure')
            if name=='report.json':
                reports_written+=1
                if mode=='report_persist_fail' and reports_written==1:raise OSError('injected report failure')
            Path(path).write_bytes(worker.compact(value))
            return dict(path=name,sha256=sha(path),bytes=Path(path).stat().st_size)
        with patch.object(worker,'ROOT',root),patch.object(worker,'FileStore',Store),patch.object(worker,'digest',digest),\
             patch.object(worker,'load_handoff',load),patch.object(worker.engine.kernel,'dual_validate',dual),\
             patch.object(worker,'build',build),patch.object(worker,'normalized_sha256',identity),\
             patch.object(worker,'new_authority',authority),patch.object(worker,'drive',drive),\
             patch.object(worker,'preserve_zero',zero),patch.object(worker,'json_file',output),\
             patch.object(worker.engine.shared,'load_handoff',forbidden),patch.object(worker.engine,'load_handoff',forbidden),\
             patch.object(worker.engine,'run',forbidden),patch.object(worker.engine.shared,'run',forbidden),\
             patch.object(worker.engine.shared,'drive',forbidden),patch.object(worker.engine.kernel,'build_index',forbidden),\
             patch.object(worker.adapter,'audit',forbidden),patch.object(worker.adapter.chain,'audit_chain',forbidden):
            report=worker.run(out,manifest,started=0,clock=lambda:26 if mode=='deadline_before_load' else 1)
        expected=mode in ('ordinary','zero_clean')
        assert report['accepted'] is expected,(mode,report)
        if expected:assert report['method']=='fixed64_restricted_three_row75' and report['identity_valid'] is True
        for name in ('load','dual','build','new_authority','drive'):assert calls.count(name)<=1,(mode,name,calls)
        filtered=[c for c in calls if c in ('load','dual','build','new_authority','drive')]
        assert filtered==['load','dual','build','new_authority','drive'][:len(filtered)],(mode,calls)
        if mode in ('loader_fail','bad_manifest_input','deadline_before_load'):assert 'dual' not in calls
        if mode in ('dual_fail','dual_wrong_identity'):assert 'build' not in calls
        if mode in ('build_fail','build_wrong_score','build_wrong_identity'):assert 'new_authority' not in calls
        if mode in ('initial_publish_fail','initial_file_fail'):assert 'drive' not in calls
        if mode=='lost_started_charge':assert report['last_attempted_charge']['started']==1 and report['state']['counters']['started']==0
        if mode in ('saved_witness_old_authority','zero_metadata_error'):assert report['witness_saved'] is True
        if mode=='report_persist_fail':assert reports_written==2
        if 'initial.json' in outputs and mode!='initial_file_fail':
            saved=json.loads((out/'initial.json').read_bytes())
            assert saved['score']==64 and saved['state_hash']==worker.FIXED_STATE and saved['counters']==dict(started=0,completed=0,accepted=0)
        gc.collect();assert all(ref() is None for ref in refs),'index retained after wrapper completion'
    return dict(mode=mode,accepted=expected,calls=calls,initial_index_released=True,
                no_stale_prepared_in_run=drive_entered,initial_builds=len(refs))


def run():
    assert sha(worker.__file__)==WORKER_SHA
    modes=('ordinary','zero_clean','loader_fail','dual_fail','dual_wrong_identity','build_fail','build_wrong_score',
           'build_wrong_identity','initial_publish_fail','initial_file_fail','drive_error','lost_started_charge',
           'saved_witness_old_authority','zero_metadata_error','uncertain_authority','final_publish_fail',
           'post_pin_drift','report_persist_fail','deadline_before_load','bad_manifest_input')
    results=[case(mode) for mode in modes]
    assert sha(worker.__file__)==WORKER_SHA
    assert worker.build is worker.engine.build and worker.drive is worker.engine.drive
    assert worker.new_authority is worker.engine.new_authority and worker.FileStore is worker.engine.FileStore
    return dict(passed=True,worker_sha256=WORKER_SHA,source_sha256=sha(__file__),cases=results,
                scope='Real run control flow, manifest decoder and final acceptance gate; loader, geometry, controller and persistence callbacks explicitly declared spies. Genuine temporary manifest/output bytes; source digest labels declared.',
                limitations='No actual input, n75 geometry, optimizer, real zero validation, fsync durability or RSS claim. Initial ownership checked via caller locals and weakrefs; positive-transition lifetime is separately source-bound to frozen v3 evidence.')


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-run-v2.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,cases=len(result['cases']),source_sha256=sha(__file__),evidence_sha256=sha(path))))
