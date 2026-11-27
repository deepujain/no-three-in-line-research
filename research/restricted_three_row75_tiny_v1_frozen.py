"""Author finite n2..4 geometry and synthetic interruption QA; no actual input."""
from itertools import combinations, product
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import restricted_three_row75 as s

LOCAL=((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
DENSE=((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))


def collinear(p,q,r): return (p[0]-q[0])*(r[1]-q[1]) == (p[1]-q[1])*(r[0]-q[0])
def triples(points): return [t for t in combinations(points,3) if collinear(*t)]
def raw(points): return len(triples(points))


def fixtures():
    for n in (2,3):
        for deficient in range(n):
            for single in range(n):
                for rest in product(tuple(combinations(range(n),2)),repeat=n-1):
                    it=iter(rest)
                    yield n,tuple(sorted((x,y) for y in range(n) for x in ((single,) if y==deficient else next(it))))
    yield 4,LOCAL
    yield 4,DENSE


def expected_orders(points,n):
    old=triples(points); found={tuple(sorted(p[1] for p in t)) for t in old}
    return [[*rs,sum(any(p[1] in rs for p in t) for t in old),sum(tuple(sorted(p[1] for p in t))==rs for t in old)]
            for rs in sorted(found,key=lambda rs:(-sum(any(p[1] in rs for p in t) for t in old),*rs))]


def brute_assignments(t):
    total=sum(map(len,t['current'])); choices=[]
    for loads in product((1,2),repeat=3):
        if sum(loads)!=total:continue
        choices.extend(product(*(tuple(combinations(d,k)) for d,k in zip(t['domains'],loads))))
    return sorted(choices)


def brute_optimum(points,n,rows):
    retained=tuple(p for p in points if p[1] not in rows)
    domains=[]
    for row in rows:
        current={x for x,y in points if y==row}
        costs={x:sum(collinear((x,row),*pair) for pair in combinations(retained,2)) for x in range(n)}
        added=sorted((costs[x],x) for x in range(n) if x not in current)[:min(4,n)-len(current)]
        domains.append(tuple(sorted(current|{x for u,x in added})))
    current=tuple(tuple(x for x,y in points if y==row) for row in rows)
    t={'domains':domains,'current':current}
    values=[]
    for cols in brute_assignments(t):
        changed=tuple(sorted(retained+tuple((x,row) for row,cs in zip(rows,cols) for x in cs)))
        values.append(((raw(changed),*cols),changed))
    return min(values,key=lambda v:v[0])


class Memory:
    def __init__(self,a): self.raw=s.authority_bytes(a); self.files={}; self.events=[]; self.n=a['n']
    def publish(self,a,tag): self.raw=s.authority_bytes(a); self.events.append(tag)
    def move(self,value):
        name=f"m{value['generation']}-{value['attempt']}"; blob=s.compact(value)
        assert name not in self.files; self.files[name]=blob
        return {'path':name,'sha256':s.hashed(value),'bytes':len(blob)}
    def zero(self,points):
        value=s.kernel.dual_validate(points,self.n,0,lambda:None); blob=s.compact(value)
        assert 'witness' not in self.files; self.files['witness']=blob
        return {'path':'witness','sha256':s.hashed(value),'bytes':len(blob)}
    def drive(self,a,**kwargs): return s.drive(a,publish=self.publish,save_move=self.move,save_zero=self.zero,**kwargs)


def mathematical():
    count={'fixtures':0,'blocks':0,'assignments':0,'K_multiplicity_cases':0,'ternary_positive_entries':0,'deficiency_migrations':0}
    for n,points in fixtures():
        count['fixtures']+=1; p,index,score=s.kernel.build_index(points,n)
        assert score==raw(points)
        ranks=s.priorities(points,index,n); old=triples(points)
        assert ranks['I']==tuple(sum(any(p[1]==r for p in t) for t in old) for r in range(n))
        for pair in combinations(range(n),2):
            assert ranks['J'][pair]==sum(all(any(p[1]==r for p in t) for r in pair) for t in old)
        assert s.make_orders(points,index,n,s.kernel.normalized_sha256(n,points))['blocks']==expected_orders(points,n)
        count['K_multiplicity_cases']+=int(any(k>1 for k in ranks['K'].values()))
        for rows in combinations(range(n),3):
            count['blocks']+=1; t=s.block_tables(points,index,n,rows)
            assert t['base']==raw(t['retained'])
            for i,row in enumerate(rows):
                assert t['unary'][i]==[sum(collinear((x,row),*pair) for pair in combinations(t['retained'],2)) for x in range(n)]
                assert set(t['current'][i])<=set(t['domains'][i])
            for (i,j),table in t['C'].items():
                assert list(table)==[sum(collinear((x,rows[i]),(y,rows[j]),q) for q in t['retained']) for x in t['domains'][i] for y in t['domains'][j]]
            assert list(t['T'])==[int(collinear((x,rows[0]),(y,rows[1]),(z,rows[2]))) for x in t['domains'][0] for y in t['domains'][1] for z in t['domains'][2]]
            count['ternary_positive_entries']+=sum(t['T'])
            choices=list(s.assignments(t['domains'],sum(map(len,t['current']))))
            assert choices==brute_assignments(t)
            assert s.objective(t,*t['current'])==score
            for cols in choices:
                changed=t['retained']+tuple((x,row) for row,cs in zip(rows,cols) for x in cs)
                assert s.objective(t,*cols)==raw(changed)
                count['assignments']+=1
            expected,changed=brute_optimum(points,n,rows); result=s.block_optimum(points,index,n,rows)
            assert (result['score'],result['X'],result['Y'],result['Z'])==expected
            assert result['points']==changed and result['optimum_established']
            if result['score']>0:assert result['enumeration_exhausted']
            if any(len(a)!=len(b) for a,b in zip(t['current'],expected[1:])):count['deficiency_migrations']+=1
    falsifier=((0,0),(0,1),(1,1),(0,2),(1,2)); p,idx,u=s.kernel.build_index(falsifier,3)
    t=s.block_tables(p,idx,3,(0,1,2))
    assert u==s.objective(t,*t['current'])==1 and t['base']==0 and not any(any(v) for v in t['unary'])
    assert not any(any(v) for v in t['C'].values())
    # Artificial unary costs test domain policy only, not reachable n<=4 tables.
    assert s.domain((1,4),[0,999,0,1,999,2],6)==(0,1,2,4)
    assert len(list(s.assignments(((0,1,2,3),)*3,6)))==216
    assert len(list(s.assignments(((0,1,2,3),)*3,5)))==432
    return dict(count,ternary_falsifier=True,artificial_high_unary_current_inclusion=True,
                limitation='n<=4 three-row deletion leaves <=1 retained row; base/unary geometry checks are necessarily zero. No pair-stuck escape claim.')


def parity():
    counts={'fixtures':0,'decisions':0,'strict_moves':0,'splits':0,'pending':0}
    for n,points in fixtures():
        a=s.new_authority(points,n); store=Memory(a); trace=[]
        r=store.drive(a,observe=trace.append)
        current=points; expected=[]; starts=0
        while raw(current) and starts<s.MAX_STARTS:
            changed_state=False
            for record in expected_orders(current,n):
                if starts==s.MAX_STARTS:break
                starts+=1; rows=record[:3]; minimum,changed=brute_optimum(current,n,rows)
                strict=minimum[0]<raw(current)
                expected.append({'rows':rows,'minimum':s.clone(minimum),'strict':strict,'before_hash':s.kernel.normalized_sha256(n,current)})
                if strict:current=changed;changed_state=True;break
            if not changed_state:break
        assert trace==expected and r['authority']['points']==s.clone(current),(n,points,r)
        assert r['error'] is None and r['authority']['counters']['started']==starts
        counts['fixtures']+=1;counts['decisions']+=len(trace);counts['strict_moves']+=sum(e['strict'] for e in trace)
        for cut in range(len(trace)+1):
            store=Memory(a);events=[];first=store.drive(a,stop_after=cut,observe=events.append)
            restored=s.inspect_recovery(store.raw,store.files.__getitem__)
            last=store.drive(restored,observe=events.append)
            assert events==trace and last['authority']['points']==s.clone(current)
            counts['splits']+=1
            if cut<len(trace):
                active=s.clone(restored)
                if active['orders'] is None:
                    p,index,u=s.kernel.build_index(active['points'],n)
                    active['orders']=s.make_orders(p,index,n,active['state_hash'])
                pending=s.plan_start(active); loaded=s.inspect_recovery(s.authority_bytes(pending),store.files.__getitem__)
                assert loaded['counters']['started']==active['counters']['started']+1 and loaded['cursor']==active['cursor']
                assert store.drive(loaded)['status']=='error'; counts['pending']+=1
    return counts


def faults():
    count={'cooperative_interruptions':0,'publication_faults':0}
    for points in (LOCAL,DENSE):
        a=s.new_authority(points,4); store=Memory(a); positions=[]
        store.drive(a,check=lambda:positions.append(1))
        for stop_at in range(1,len(positions)+1):
            memory=Memory(a); checks=[0]
            def check():
                checks[0]+=1
                if checks[0]==stop_at:raise s.SearchStop('tiny_stop')
            r=memory.drive(a,check=check); durable=s.inspect_recovery(memory.raw,memory.files.__getitem__)
            assert durable['points']==r['authority']['points'] and durable['counters']==r['authority']['counters']
            if durable['pending']:assert durable['attempts'][-1]['outcome']=='pending'
            count['cooperative_interruptions']+=1
        for tag in ('start','complete','accept','accept_zero'):
            for when in ('before','after'):
                memory=Memory(a); publish=memory.publish; hit=[]
                def fault(value,name):
                    if tag==name and not hit:
                        hit.append(name)
                        if when=='before':raise OSError('before replacement')
                        publish(value,name);raise OSError('after replacement')
                    publish(value,name)
                memory.publish=fault;r=memory.drive(a)
                if not hit:continue
                assert r['status']=='error'
                durable=s.inspect_recovery(memory.raw,memory.files.__getitem__)
                if when=='after' and tag.startswith('accept'):assert durable['U']<r['authority']['U']
                count['publication_faults']+=1
    a=s.new_authority(LOCAL,4); memory=Memory(a)
    def lost(value,tag):raise s.SearchStop('lost start')
    memory.publish=lost
    with patch.object(s,'block_optimum',side_effect=AssertionError('optimizer before durable charge')):
        r=memory.drive(a)
    assert r['status']=='error' and r['attempted_charge']['started']==1 and r['authority']['counters']['started']==0
    for mode in ('late_start','late_saved_zero','interrupted_zero_publication'):
        memory=Memory(a); now=[0]; publish=memory.publish; zero=memory.zero
        def check():
            if now[0]>=23:raise s.SearchStop('search_deadline')
        def save(points):
            ref=zero(points)
            if mode=='late_saved_zero':now[0]=24
            return ref
        def pub(value,tag):
            if mode=='interrupted_zero_publication' and tag=='accept_zero':raise s.SearchStop('zero publication interruption')
            publish(value,tag)
            if mode=='late_start' and tag=='start':now[0]=24
        memory.publish=pub;memory.zero=save;r=memory.drive(a,check=check)
        if mode=='late_start':assert r['status']=='search_deadline' and r['authority']['pending']==1
        elif mode=='late_saved_zero':assert r['status']=='zero' and r['authority']['U']==0
        else:assert r['status']=='error' and 'witness' in memory.files and r['authority']['pending']
    return dict(count,lost_charge_rejected=True,late_start_charged=True,late_zero_committed=True,saved_zero_publication_interruption_rejected=True)


def caps_and_corruptions():
    a=s.new_authority(DENSE,4); cases=[]
    def reject(value,geometry=True):
        try:s.inspect_recovery(s.compact({'payload':value,'payload_sha256':s.hashed(value)}),geometry=geometry)
        except ValueError:return
        raise AssertionError('corruption accepted')
    for field,value in (('cursor',1),('state_hash','0'*64),('start_cap',17)):
        b=s.clone(a);b[field]=value;reject(b);cases.append(field)
    b=s.plan_start(a);b['attempts'][-1]['state_hash']='0'*64;reject(b);cases.append('pending state')
    b=s.clone(a);b['orders']['blocks'].reverse();b['orders']['sha256']=s.hashed({'state_hash':b['state_hash'],'policy':s.POLICY,'blocks':b['orders']['blocks']});reject(b);cases.append('order reconstruction')
    b=s.clone(a);b['counters']['started']=17;reject(b);cases.append('globalcap')
    b=s.clone(a);b['orders']['padding']='x'*8192;reject(b);cases.append('candidatecap')
    ref={'path':'../orphan','sha256':'0'*64,'bytes':1}
    try:s.valid_ref(ref)
    except ValueError:cases.append('path traversal')
    else:raise AssertionError('path traversal')
    pending=s.plan_start(a);res=s.block_optimum(*s.kernel.build_index(DENSE,4)[:2],4,pending['attempts'][-1]['rows'])
    res['optimum_established']=False
    try:s.prepare_accept(pending,res)
    except ValueError:cases.append('partial optimum')
    else:raise AssertionError('partial optimum accepted')
    try:s.build(DENSE,4,lambda:None,{'indexes_started':17})
    except ValueError:cases.append('index18')
    else:raise AssertionError('18th index allowed')
    return cases


def zero_lifecycle(mode):
    points=brute_optimum(LOCAL,4,(0,1,2))[1]
    assert raw(points)==0
    with tempfile.TemporaryDirectory(prefix='three-row-zero-') as directory:
        out=Path(directory); now=[0];events=[];calls=[0,0];report={}
        one=s.kernel.verify_certificate;two=s.kernel.verify_certificate_bruteforce;save=s.shared.json_file
        def check():
            if now[0]>=25:raise TimeoutError('tiny soft deadline')
        def first(c):
            events.append('v1');calls[0]+=1;result=one(c)
            if mode=='late_first':now[0]=26
            return result
        def second(c):
            events.append('v2');calls[1]+=1;result=two(c)
            if mode=='late_second':now[0]=26
            if mode=='disagreement':result['valid']=False
            return result
        def write(path,value,**kwargs):
            events.append(path.name)
            if path.name=='valid149.json' and mode=='save_failure':raise OSError('tiny save error')
            ref=save(path,value,**kwargs)
            if path.name=='valid149.json' and mode=='post_save_hash_fault':
                s.kernel.normalized_sha256=lambda *args:(_ for _ in ()).throw(ValueError('post-save hash'))
            return ref
        if mode=='late_zero':now[0]=26
        with patch.object(s.kernel,'verify_certificate',first),patch.object(s.kernel,'verify_certificate_bruteforce',second),patch.object(s.kernel,'normalized_sha256',s.kernel.normalized_sha256),patch.object(s.shared,'json_file',write):
            ref=s.preserve_zero(points,4,out,check,report)
        if mode in ('normal','late_second','post_save_hash_fault'):
            assert ref is not None and report['witness_saved'] and events.index('valid149.json')==events.index('v2')+1
        else:assert ref is None and (out/'raw-zero.json').exists()
        if mode=='late_first':assert calls==[1,0]
        if mode=='late_zero':assert calls==[0,0]
        return {'mode':mode,'validator_calls':calls,'witness_saved':report.get('witness_saved',False)}


def witness_metadata_failure():
    points=brute_optimum(LOCAL,4,(0,1,2))[1];checked=s.kernel.dual_validate(points,4,0,lambda:None);after=[False]
    class Broken(dict):
        def __getitem__(self,key):
            if key=='validators' and after[0]:raise ValueError('metadata after save')
            return super().__getitem__(key)
    save=s.shared.json_file;report={}
    def write(*args,**kwargs):
        result=save(*args,**kwargs);after[0]=True;return result
    with tempfile.TemporaryDirectory(prefix='three-row-meta-') as directory:
        with patch.object(s.kernel,'dual_validate',return_value=Broken(checked)),patch.object(s.shared,'json_file',write):
            ref=s.preserve_zero(points,4,directory,lambda:None,report)
        assert ref is not None and report['witness']==ref and report['witness_saved'] and 'witness_metadata_error' in report
        assert (Path(directory)/'valid149.json').exists() and not (Path(directory)/'raw-zero.json').exists()
    return True


def filesystem():
    with tempfile.TemporaryDirectory(prefix='three-row-fsync-') as directory:
        a=s.new_authority(DENSE,4);store=s.FileStore(directory);store.publish(a,'initialize');report={}
        r=s.drive(a,publish=store.publish,save_move=store.save_move,save_zero=lambda p:s.preserve_zero(p,4,directory,lambda:None,report))
        final=s.inspect_recovery((Path(directory)/'authority.json').read_bytes(),lambda name:(Path(directory)/name).read_bytes())
        assert final==s.clone(r['authority']) and final['U']==0 and report['witness_saved']
        assert store.publications==1+2*r['decisions']<=34
        try:s.json_file(Path(directory)/final['artifacts'][0]['path'],{},immutable=True)
        except FileExistsError:pass
        else:raise AssertionError('immutable overwritten')
        with patch.object(s,'atomic_file',side_effect=OSError('fsync uncertainty')):
            try:store.publish(final,'failed')
            except OSError:pass
            else:raise AssertionError('uncertainty not propagated')
        try:store.publish(final,'retry forbidden')
        except ValueError:pass
        else:raise AssertionError('uncertain retry allowed')
        return {'file_directory_fsync':True,'publications':store.publications,'uncertainty_blocks_retry':True}


def main():
    result={'passed':True,'worker_sha256':s.digest(s.__file__),'tiny_sha256':s.digest(__file__),
            'mathematical':mathematical(),'controller_parity':parity(),'faults':faults(),
            'caps_and_corruptions':caps_and_corruptions(),'zero_lifecycle':[zero_lifecycle(m) for m in
                ('normal','late_first','late_second','late_zero','disagreement','save_failure','post_save_hash_fault')],
            'witness_metadata_failure':witness_metadata_failure(),'filesystem':filesystem(),
            'scope':'SOURCE/TINY n2..4 only; no actual65 artifact/loader/geometry, no pair-stuck evidence.'}
    path=s.ROOT/'data/restricted-three-row75-author-tiny-v1.json'
    if path.exists():raise FileExistsError('preserve prior evidence')
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
