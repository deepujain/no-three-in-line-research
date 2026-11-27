"""Author87-fixture cursor/persistence QA. No actual65 artifact is opened."""
from contextlib import ExitStack
from itertools import combinations,product
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import two_row_suffix75 as s
from research import two_row_descent_independent_oracle as oracle

LOCAL=((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
DENSE=((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))


def fixtures():
    for n in (2,3):
        for deficient in range(n):
            for single in range(n):
                for rest in product(tuple(combinations(range(n),2)),repeat=n-1):
                    it=iter(rest)
                    yield n,tuple(sorted((x,y) for y in range(n) for x in ((single,) if y==deficient else next(it))))
    yield 4,LOCAL
    yield 4,DENSE


class Memory:
    def __init__(self,a):self.raw=s.authority_bytes(a);self.files={};self.events=[]
    def publish(self,a,tag):self.raw=s.authority_bytes(a);self.events.append(tag)
    def move(self,value):
        name=f"m{value['generation']}-{value['attempt']}";raw=s.compact(value)
        assert name not in self.files
        self.files[name]=raw
        return {'path':name,'sha256':s.hashed(value),'bytes':len(raw)}
    def zero(self,points):
        value=s.kernel.dual_validate(points,self.n,0,lambda:None);raw=s.compact(value)
        self.files['witness']=raw
        return {'path':'witness','sha256':s.hashed(value),'bytes':len(raw)}
    def drive(self,a,**kwargs):
        self.n=a['n']
        return s.drive(a,publish=self.publish,save_move=self.move,save_zero=self.zero,**kwargs)


def simple_event(e):
    return [e['kind'],e['rows'][0] if e['kind']=='row' else e['rows'],e['minimum'],e['strict']]


def parity():
    counts={'fixtures':0,'decisions':0,'split_boundaries':0,'pending_cases':0,'strict_moves':0}
    for n,points in fixtures():
        counts['fixtures']+=1;a=s.new_authority(points,n);store=Memory(a);trace=[]
        r=store.drive(a,observe=lambda e:trace.append(simple_event(e)))
        expected=oracle.reference_descent(points,n)
        assert trace==s.clone(expected['events']),(n,points,trace,expected['events'])
        assert r['status']=='zero' and r['authority']['U']==0
        assert tuple(map(tuple,r['authority']['points']))==expected['points']
        assert r['authority']['counters']=={k:expected[k.replace('_completed','_started')] for k in s.COUNTERS}
        counts['decisions']+=len(trace);counts['strict_moves']+=expected['accepted']
        for cut in range(len(trace)+1):
            first=Memory(a);events=[];before=first.drive(a,stop_after=cut,observe=lambda e:events.append(simple_event(e)))
            raw=s.authority_bytes(before['authority'])
            restored=s.inspect_recovery(raw,first.files.__getitem__)
            last=first.drive(restored,observe=lambda e:events.append(simple_event(e)))
            assert events==trace and last['authority']['counters']==r['authority']['counters']
            assert last['authority']['points']==r['authority']['points']
            counts['split_boundaries']+=1
            if cut<len(trace):
                # The split authority may have lazily cleared orders after accept.
                active=s.clone(restored)
                if active['orders'] is None:active['orders']=s.checked_kernel(active)[3]
                pending=s.plan_start(active);encoded=s.authority_bytes(pending)
                loaded=s.inspect_recovery(encoded,first.files.__getitem__)
                assert loaded['pending'] is not None
                assert loaded['counters'][loaded['phase']+'_started']==active['counters'][active['phase']+'_started']+1
                assert loaded['row_cursor']==active['row_cursor'] and loaded['pair_cursor']==active['pair_cursor']
                refused=first.drive(loaded)
                assert refused['status']=='error' and refused['decisions']==0
                counts['pending_cases']+=1
    assert counts=={'fixtures':87,'decisions':88,'split_boundaries':175,'pending_cases':88,'strict_moves':62},counts
    return counts


def interruption_and_faults():
    checks=0;faults=0
    for points in (LOCAL,DENSE):
        a=s.new_authority(points,4);full=Memory(a);work={};positions=[]
        full.drive(a,work=work,check=lambda:positions.append(work.get('phase')))
        for stop_at in range(1,len(positions)+1):
            store=Memory(a);work={};counter=[0]
            def check():
                counter[0]+=1
                if counter[0]==stop_at:raise s.SearchStop('synthetic_stop')
            result=store.drive(a,work=work,check=check)
            durable=s.inspect_recovery(store.raw,store.files.__getitem__)
            assert durable['points']==result['authority']['points']
            assert durable['counters']==result['authority']['counters']
            if durable['pending'] is not None:
                assert durable['attempts'][-1]['outcome']=='pending'
            checks+=1
        for tag in ('start','complete','accept','accept_zero'):
            for when in ('before','after'):
                store=Memory(a);original=store.publish;hit=[]
                def publish(value,name):
                    if name==tag and not hit:
                        hit.append(name)
                        if when=='before':raise OSError('synthetic before replacement')
                        original(value,name);raise OSError('synthetic after replacement')
                    original(value,name)
                store.publish=publish
                result=store.drive(a)
                if not hit:continue
                assert result['status']=='error'
                recovered=s.inspect_recovery(store.raw,store.files.__getitem__)
                if when=='after' and tag.startswith('accept'):
                    assert recovered['U']<result['authority']['U']
                    assert not recovered['row_sweep_complete'] and not recovered['pair_scan_complete']
                if tag=='start':assert result['attempted_charge'] is not None
                faults+=1
    return {'cooperative_positions':checks,'publication_fault_cases':faults}


def caps_and_corruptions():
    values=[]
    for rowleft,pairleft in ((0,1),(1,1),(204,0),(204,1)):
        base=dict(row_started=512-rowleft,row_completed=512-rowleft,pair_started=96-pairleft,pair_completed=96-pairleft,accepted=28)
        a=s.new_authority(LOCAL,4,base=base);store=Memory(a);r=store.drive(a)
        assert r['authority']['counters']['row_started']<=512 and r['authority']['counters']['pair_started']<=96
        if rowleft<3:assert r['status']=='row_cap' and not r['authority']['row_sweep_complete']
        elif pairleft==0:assert r['status']=='pair_cap' and r['authority']['row_sweep_complete']
        else:assert r['status']=='zero'
        values.append(r['status'])
    a=s.new_authority(LOCAL,4);mutations=[]
    b=s.clone(a);b['row_cursor']=1;mutations.append(b)
    b=s.clone(a);b['state_hash']='0'*64;mutations.append(b)
    b=s.clone(a);b['orders']['rows'].reverse();b['orders']['sha256']=s.hashed({'state_hash':b['state_hash'],'policy':s.POLICY,'rows':b['orders']['rows'],'pairs':b['orders']['pairs']});mutations.append(b)
    b=s.plan_start(a);b['attempts'][-1]['state_hash']='0'*64;mutations.append(b)
    rejected=0
    for b in mutations:
        try:s.inspect_recovery(s.compact({'payload':b,'payload_sha256':s.hashed(b)}))
        except ValueError:rejected+=1
        else:raise AssertionError('corruption accepted')
    return {'cap_cases':values,'corruptions_rejected':rejected}


def zero_lifecycle(mode):
    points=oracle.pair_optimum(LOCAL,4,0,1)['points']
    with tempfile.TemporaryDirectory(prefix='suffix-zero-tiny-') as directory:
        out=Path(directory);events=[];now=[0];report={'witness_saved':False};calls=[0,0]
        one=s.kernel.verify_certificate;two=s.kernel.verify_certificate_bruteforce;save=s.json_file
        def check():
            if now[0]>=25:raise TimeoutError('synthetic soft deadline')
        def first(c):
            events.append('v1');calls[0]+=1;r=one(c)
            if mode=='late_first':now[0]=26
            return r
        def second(c):
            events.append('v2');calls[1]+=1;r=two(c)
            if mode=='late_second':now[0]=26
            if mode=='disagreement':r['valid']=False
            return r
        def write(path,value,**kwargs):
            events.append(path.name)
            if path.name=='valid149.json' and mode=='save_failure':raise OSError('synthetic save failure')
            if path.name=='raw-zero.json' and mode=='raw_latency':now[0]=26
            ref=save(path,value,**kwargs)
            if path.name=='valid149.json' and mode=='post_save_hash_fault':
                s.kernel.normalized_sha256=lambda *args:(_ for _ in ()).throw(ValueError('synthetic post-save hash failure'))
            return ref
        if mode=='late_zero':now[0]=26
        with patch.object(s.kernel,'verify_certificate',first),patch.object(s.kernel,'verify_certificate_bruteforce',second),patch.object(s.kernel,'normalized_sha256',s.kernel.normalized_sha256),patch.object(s,'json_file',write):
            ref=s.preserve_zero(points,4,out,check,report)
        if mode in ('normal','late_second','raw_latency','post_save_hash_fault'):
            assert ref is not None and report['witness_saved'] and events.index('valid149.json')==events.index('v2')+1
            assert not (out/'raw-zero.json').exists()
        else:assert ref is None and (out/'raw-zero.json').exists()
        if mode=='late_first':assert calls==[1,0]
        if mode=='late_zero':assert calls==[0,0]
        return {'mode':mode,'validator_calls':calls,'witness_saved':report['witness_saved']}


def filesystem():
    with tempfile.TemporaryDirectory(prefix='suffix-fsync-tiny-') as directory:
        a=s.new_authority(DENSE,4);store=s.FileStore(directory);store.publish(a,'initialize')
        report={}
        r=s.drive(a,publish=store.publish,save_move=store.save_move,
                  save_zero=lambda p:s.preserve_zero(p,4,Path(directory),lambda:None,report))
        final=s.inspect_recovery((Path(directory)/'authority.json').read_bytes(),lambda name:(Path(directory)/name).read_bytes())
        assert final==s.clone(r['authority']) and final['U']==0 and report['witness_saved']
        assert store.publications==1+2*r['decisions']<=538
        try:s.json_file(Path(directory)/final['artifacts'][0]['path'],{},immutable=True)
        except FileExistsError:pass
        else:raise AssertionError('immutable artifact overwritten')
        return {'file_and_directory_fsync':True,'publications':store.publications,'orphan_adoption':'never; only checkpoint refs read'}


def charge_and_zero_publication():
    a=s.new_authority(LOCAL,4);store=Memory(a);optimized=[]
    def stopped_publish(value,tag):raise s.SearchStop('synthetic publisher interruption')
    store.publish=stopped_publish
    with patch.object(s.kernel,'row_optimum',side_effect=AssertionError('optimizer before start publication')):
        r=store.drive(a)
    assert r['status']=='error' and r['authority']['counters']['row_started']==0
    assert r['attempted_charge']['row_started']==1 and r['decisions']==0
    store=Memory(a);now=[0];saved=[];publish=store.publish
    def check():
        if now[0]>=23:raise s.SearchStop('search_deadline')
    def late_start(value,tag):
        publish(value,tag)
        if tag=='start':now[0]=24
    store.publish=late_start
    r=store.drive(a,check=check)
    assert r['status']=='search_deadline' and r['authority']['pending']==1
    assert r['authority']['counters']['row_started']==1 and r['authority']['row_cursor']==0
    for mode in ('late_saved_zero','interrupted_zero_publication'):
        store=Memory(a);now[0]=0;publish=store.publish;zero=store.zero
        def save_zero(points):
            ref=zero(points);saved.append('witness')
            if mode=='late_saved_zero':now[0]=24
            return ref
        def publish_zero(value,tag):
            if mode=='interrupted_zero_publication' and tag=='accept_zero':raise s.SearchStop('synthetic zero publication stop')
            publish(value,tag)
        store.zero=save_zero;store.publish=publish_zero
        r=store.drive(a,check=check)
        assert 'witness' in store.files
        if mode=='late_saved_zero':assert r['status']=='zero' and r['authority']['U']==0
        else:assert r['status']=='error' and r['authority']['U']==1 and r['authority']['pending'] is not None
    return {'unresolved_start_publication_fails':True,'late_start_durable_charge':True,
            'late_saved_zero_authority_commits':True,'interrupted_zero_publication_fails':True}


def witness_metadata_failure():
    points=oracle.pair_optimum(LOCAL,4,0,1)['points']
    checked=s.kernel.dual_validate(points,4,0,lambda:None);after_save=[False]
    class MetadataFault(dict):
        def __getitem__(self,key):
            if key=='validators' and after_save[0]:raise ValueError('synthetic witness metadata failure')
            return super().__getitem__(key)
    saved=s.json_file;report={'witness_saved':False}
    def save(*args,**kwargs):
        value=saved(*args,**kwargs);after_save[0]=True;return value
    with tempfile.TemporaryDirectory(prefix='suffix-metadata-tiny-') as directory:
        with patch.object(s.kernel,'dual_validate',return_value=MetadataFault(checked)),patch.object(s,'json_file',save):
            ref=s.preserve_zero(points,4,directory,lambda:None,report)
        assert ref is not None and report['witness_saved'] and report['witness']==ref
        assert 'witness_metadata_error' in report and (Path(directory)/'valid149.json').exists()
        assert not (Path(directory)/'raw-zero.json').exists()
    return {'durable_witness_reference_preserved':True,'explicit_metadata_error':True,
            'acceptance_gate':'Independent run-gating stub verifies rejection; geometry/loader not exercised there.'}


def main():
    result={'passed':True,'worker_sha256':s.digest(s.__file__),'tiny_sha256':s.digest(__file__),
            'parity':parity(),'faults':interruption_and_faults(),'caps_and_corruptions':caps_and_corruptions(),
            'zero_lifecycle':[zero_lifecycle(mode) for mode in ('normal','late_first','late_second','late_zero','disagreement','save_failure','raw_latency','post_save_hash_fault')],
            'filesystem':filesystem(),'scope':'87 synthetic n2..4 geometry fixtures, cursor splits/pending/faults and actual temp-file fsync; no actual65 source or geometry.'}
    result['charge_and_zero_publication']=charge_and_zero_publication()
    result['witness_metadata_failure']=witness_metadata_failure()
    target=s.ROOT/'data/two-row-suffix75-author-tiny-v4.json';target.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
