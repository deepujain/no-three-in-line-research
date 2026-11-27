"""Independent production geometry/controller SOURCE/TINY comparison, never run/load_handoff."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import resource
import time
from research import restricted_three_row_independent_oracle as oracle
from research import restricted_three_row75 as worker

WORKER_SHA='c737357d7167d096fc368fb656df4430e930287661581b226f7f63b8c266a6bf'
ORACLE_SHA='f63cd423929ed49a3337f23fe0a75cb823ffe9f73689cf27b788505a87b69d9d'
PREP='data/restricted-three-row-independent-preparation.json'
PREP_SHA='15b456f3d0ea283750947c4b621e36cc2da8ce804e3cd40e8b13677bdceea913'
FIXED='data/restricted-three-row-independent-fixed56-preparation.json'
FIXED_SHA='e51f305f97993b2c54e64d48e5e2734f51fd9b89d7022070cdf1d729bec0f748'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(value):return json.loads(oracle.canonical(value))

class Memory:
    def __init__(self):self.blobs={};self.publications=[]
    def publish(self,a,tag):self.publications.append((tag,worker.authority_bytes(a)))
    def save(self,value):
        raw=oracle.canonical(value);name=f'memory-{len(self.blobs)}.json';self.blobs[name]=raw
        return {'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    def zero(self,points):
        assert oracle.raw(points)==0
        return self.save({'synthetic_independently_zero':points})


def projection(a):
    return {k:a[k] for k in ('points','U','state_hash','generation','counters','cursor','pending')}

def independent_path(points,n,check):
    points=oracle.validate(points,n);start=completed=accepted=cursor=0;events=[];states=[]
    while True:
        check();profile=oracle.profile(points,n)
        states.append({'points':normalized(points),'U':profile['U'],'state_hash':profile['state_hash'],'generation':accepted,
                       'counters':{'started':start,'completed':completed,'accepted':accepted},'cursor':cursor,'pending':None})
        if profile['U']==0:return states,events,'zero'
        if start==16:return states,events,'block_cap'
        if cursor==len(profile['blocks']):return states,events,'restricted_candidate_list_exhausted'
        rows=profile['blocks'][cursor];result=oracle.optimum(points,n,rows,check);item=result['minimum'];start+=1;completed+=1
        strict=item[0]<profile['U']
        events.append({'rows':normalized(rows),'minimum':normalized(item),'strict':strict,'before_hash':profile['state_hash']})
        if strict:
            accepted+=1;points=oracle.replaced(result['table'],item[1:]);cursor=0
        else:cursor+=1


def compare_tables(t,e):
    for k in ('retained','base','unary','domains','current','rows'):assert normalized(t[k])==normalized(e[k]),k
    for i,j in oracle.combinations(range(3),2):
        for a,x in enumerate(e['domains'][i]):
            for b,y in enumerate(e['domains'][j]):assert t['C'][i,j][a*len(e['domains'][j])+b]==e['C'][i,j][x,y]
    for a,x in enumerate(e['domains'][0]):
        for b,y in enumerate(e['domains'][1]):
            for c,z in enumerate(e['domains'][2]):assert t['T'][(a*len(e['domains'][1])+b)*len(e['domains'][2])+c]==e['T'][x,y,z]


def run():
    started=time.monotonic()
    pins={worker.__file__:WORKER_SHA,oracle.__file__:ORACLE_SHA,PREP:PREP_SHA,FIXED:FIXED_SHA,__file__:sha(__file__)}
    assert all(sha(p)==s for p,s in pins.items())
    def check():
        if time.monotonic()-started>25:raise TimeoutError('fixed25-second independent source/tiny cap')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>256*1024*1024:raise MemoryError('fixed256MiB target')
    profiles=0
    for n in (2,3,4):
        for points in oracle.all_states(n):
            check();e=oracle.profile(points,n);p,idx,U=worker.kernel.build_index(points,n);a=worker.priorities(p,idx,n)
            assert U==e['U'] and a['I']==e['I']
            for pair,v in e['J'].items():assert a['J'].get(pair,0)==v
            for rows,v in e['K'].items():assert a['K'].get(rows,0)==v
            assert a['M']=={r:e['M'][r] for r in e['blocks']} and tuple(a['blocks'])==e['blocks']
            orders=worker.make_orders(p,idx,n,e['state_hash']);assert normalized(orders['blocks'])==normalized(e['records'])
            assert orders['sha256']==hashlib.sha256(oracle.canonical({'state_hash':e['state_hash'],'policy':worker.POLICY,'blocks':orders['blocks']})).hexdigest()
            profiles+=1
    prep=json.loads(Path(PREP).read_text());fixed=json.loads(Path(FIXED).read_text());table_cases=assignments=0;optima=[]
    for case in prep['cases']+fixed['cases']:
        check();n=case['n'];points=tuple(map(tuple,case['points']));rows=tuple(case['rows'])
        p,idx,U=worker.kernel.build_index(points,n);e=oracle.tables(points,n,rows);t=worker.block_tables(p,idx,n,rows)
        compare_tables(t,e)
        total=sum(map(len,e['current']));actual_choices=list(worker.assignments(t['domains'],total));expected=list(oracle.assignments(e['domains'],total))
        assert actual_choices==expected and actual_choices==sorted(set(actual_choices))
        trace=[(worker.objective(t,*choice),*choice) for choice in actual_choices]
        assert hashlib.sha256(oracle.canonical(trace)).hexdigest()==case['trace_sha256']
        # Oracle preparation already directly recounted every trace assignment. In particular, fixed5/6
        # uses its authenticated trace, avoiding another direct assignment-triple census.
        result=worker.block_optimum(p,idx,n,rows)
        assert normalized((result['score'],result['X'],result['Y'],result['Z']))==case['minimum']
        assert result['optimum_established'] is True and result['enumeration_exhausted'] is (result['score']>0)
        assert normalized(result['points'])==normalized(oracle.replaced(e,case['minimum'][1:]))
        table_cases+=1;assignments+=len(trace);optima.append(case['minimum'])
    fixtures=[]
    for n in (2,3):fixtures.extend((n,p) for p in oracle.all_states(n))
    fixtures.extend((c['n'],tuple(map(tuple,c['points']))) for c in prep['cases'] if c['n']==4)
    fixtures=list(dict.fromkeys(fixtures));decisions=splits=pending=0;all_events=[];positive_accepts=0
    for n,points in fixtures:
        check();expected_states,expected_events,status=independent_path(points,n,check);initial=worker.new_authority(points,n)
        mem=Memory();events=[];result=worker.drive(initial,publish=mem.publish,save_move=mem.save,save_zero=mem.zero,observe=events.append)
        assert result['error'] is None and result['status']==status and events==expected_events
        assert projection(result['authority'])==expected_states[-1]
        all_events.extend(events);decisions+=len(events);positive_accepts+=sum(e['strict'] and e['minimum'][0]>0 for e in events)
        for cut in range(len(events)+1):
            m=Memory();first=[];left=worker.drive(initial,publish=m.publish,save_move=m.save,save_zero=m.zero,observe=first.append,stop_after=cut)
            restored=worker.inspect_recovery(worker.authority_bytes(left['authority']),m.blobs.__getitem__)
            later=[];right=worker.drive(restored,publish=m.publish,save_move=m.save,save_zero=m.zero,observe=later.append)
            assert left['error'] is None and right['error'] is None and first+later==expected_events
            assert projection(right['authority'])==expected_states[-1];splits+=1
        for tag,raw in mem.publications:
            if tag!='start':continue
            restored=worker.inspect_recovery(raw,mem.blobs.__getitem__);m=Memory()
            refused=worker.drive(restored,publish=m.publish,save_move=m.save,save_zero=m.zero)
            assert refused['status']=='error' and not m.publications and projection(refused['authority'])==projection(restored)
            pending+=1
    assert all(sha(p)==s for p,s in pins.items());check()
    return {'passed':True,'scope':'SOURCE/TINY only. n2..4 census/selected fullpolicy traces; exactly authorized fixed5/6 component cases. No loader/run/actual inputs.',
            'source_pins':pins,'profiles':profiles,'table_cases':table_cases,'assignment_comparisons':assignments,
            'controller_fixtures':len(fixtures),'decisions':decisions,'split_reload_cases':splits,'pending_refusals':pending,
            'real_positive_accepts':positive_accepts,'event_trace_sha256':hashlib.sha256(oracle.canonical(all_events)).hexdigest(),
            'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'limits':'Memory artifact callbacks only. No fsync/real-validator timing claim. No full pair-stuck fixture. Global16 cap and artificial positive multiaccept control cases require separate disclosed tests.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-worker-audit-v1.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','profiles','table_cases','assignment_comparisons','decisions','split_reload_cases','real_positive_accepts','elapsed_seconds')}))
    print(json.dumps({'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
