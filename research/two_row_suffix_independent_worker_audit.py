"""Independent frozen suffix SOURCE/TINY comparison; never calls loader/run."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from research import two_row_suffix_independent_oracle as oracle
from research import two_row_suffix_independent_preparation as fixtures
from research import two_row_suffix_independent_prefix_fixture as prefix_fixture
from research import two_row_suffix75 as worker

WORKER_SHA='11fc0200742a14f5baa8cfffe85c91b34353b4990608f70efba66cc20dd750a2'
ORACLE_SHA='747965ae9cae6b506b43be7bd8d696fd1fba6c38ba59d6bef2bfefdee7264772'
KERNEL_SHA='0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Memory:
    """Byte/reference simulator only; real durability is a separate review."""
    def __init__(self):self.files={};self.publications=[];self.latest=None;self.moves=[];self.zero_calls=0
    def publish(self,a,tag):
        raw=worker.authority_bytes(a)
        self.latest=raw;self.publications.append((tag,json.loads(raw)['payload']))
    def save(self,name,value):
        raw=oracle.canonical(value)
        assert name not in self.files
        self.files[name]=raw
        return {'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    def save_move(self,move):
        self.moves.append(deepcopy(move))
        return self.save(f"move-{move['generation']}-{move['attempt']}.json",move)
    def save_zero(self,points):
        assert oracle.exact.raw(points)==0
        self.zero_calls+=1
        return self.save('synthetic-zero.json',{'points':points})


def projection(event):
    return {'kind':event['kind'],'rows':[event['choice']] if event['kind']=='row' else event['choice'],
            'minimum':event['minimum'],'strict':event['strict'],'before_hash':event['before_identity']}


def check_authority(actual,expected):
    assert actual['points']==expected['points'] and actual['U']==expected['U']
    assert actual['state_hash']==expected['identity'] and actual['generation']==expected['generation']
    for k in ('row_started','row_completed','pair_started','pair_completed'):
        assert actual['counters'][k]==expected[k]
    assert actual['counters']['accepted']==expected['generation']
    assert actual['row_cursor']==expected['row_cursor'] and actual['pair_cursor']==expected['pair_cursor']
    assert actual['row_sweep_complete']==expected['row_sweep_complete']
    assert actual['pair_scan_complete']==expected['pair_scan_complete']
    assert actual['phase']==('done' if expected['U']==0 or expected['pair_scan_complete'] else expected['phase'])
    orders=actual['orders']
    if orders is not None:
        assert orders['rows']==expected['rows'] and orders['pairs']==expected['pairs']
        assert orders['sha256']==oracle.hashed({'state_hash':expected['identity'],
               'policy':'exact-raw-IJ-M-merged-lex-v3','rows':expected['rows'],'pairs':expected['pairs']})
    else:
        assert actual['row_cursor']==actual['pair_cursor']==0
        assert not actual['row_sweep_complete'] and not actual['pair_scan_complete']
    if expected['pending'] is None:
        assert actual['pending'] is None
    else:
        selected=expected['pending'];record=actual['attempts'][actual['pending']-1]
        assert record['kind']==selected['kind'] and record['cursor']==selected['cursor']
        assert record['state_hash']==selected['state_identity'] and record['outcome']=='pending'
        assert record['rows']==([selected['choice']] if selected['kind']=='row' else selected['choice'])


def drive(a,mem,**kwargs):
    events=[]
    result=worker.drive(a,publish=mem.publish,save_move=mem.save_move,save_zero=mem.save_zero,
                        observe=events.append,**kwargs)
    return result,events


def materialize(a):
    a=worker.clone(a)
    if a['orders'] is None:
        a['orders']=worker.checked_kernel(a)[3]
    return a


def explicit_test_abandon(a):
    """Synthetic recovery decision; production drive intentionally refuses pending."""
    a=worker.clone(a);assert a['pending'] is not None
    a['attempts'][a['pending']-1]['outcome']='abandoned';a['pending']=None
    worker.validate_authority(a)
    return a


def interrupts(points):
    count=0
    def check():
        nonlocal count
        count+=1
    initial=worker.new_authority(points,4);memory=Memory()
    baseline,events=drive(initial,memory,check=check)
    assert baseline['status']=='zero'
    phases=Counter();accepted=0
    for stop in range(1,count+1):
        calls=0;mem=Memory()
        def interrupt():
            nonlocal calls
            calls+=1
            if calls==stop:raise worker.SearchStop('independent_interrupt')
        result,_=drive(initial,mem,check=interrupt)
        assert result['status']=='independent_interrupt'
        expected=initial if mem.latest is None else json.loads(mem.latest)['payload']
        # Ranking materialization may occur in scratch/current representation;
        # no points, counters, cursor or flag may outrun durable authority.
        a=result['authority']
        for key in ('points','U','state_hash','generation','counters','row_cursor','pair_cursor',
                    'row_sweep_complete','pair_scan_complete','pending','attempts','artifacts','witness'):
            assert oracle.canonical(a[key])==oracle.canonical(expected[key]),(stop,key)
        assert oracle.exact.raw(a['points'])==a['U']
        phases[mem.publications[-1][0] if mem.publications else 'before_first_publication']+=1
        accepted+=a['generation']>0
    return {'checks':count,'last_publication_phases':dict(phases),'with_accepted_state':accepted}


def run():
    started=time.monotonic()
    assert sha(worker.__file__)==WORKER_SHA and sha(oracle.__file__)==ORACLE_SHA and sha(worker.kernel.__file__)==KERNEL_SHA
    counts=Counter();trace_digest=hashlib.sha256()
    examples=[]
    for n in (2,3):examples.extend((n,p) for p in sorted(oracle.exact.geometry.states(n)))
    examples.extend(((4,fixtures.LOCAL),(4,fixtures.DENSE)))
    for n,points in examples:
        expected=oracle.run(oracle.fresh(points,n))
        initial=worker.new_authority(points,n,pair_cap=32)
        memory=Memory();actual,events=drive(initial,memory)
        assert actual['status']==expected['state']['status'] and actual['error'] is None
        assert events==[projection(e) for e in expected['events']]
        check_authority(actual['authority'],expected['state'])
        counts['fixtures']+=1;counts['decisions']+=len(events)
        for cut,boundary in enumerate(expected['boundaries']):
            mem=Memory();first,prefix=drive(initial,mem,stop_after=cut)
            check_authority(first['authority'],boundary)
            blob=worker.authority_bytes(first['authority'])
            restored=worker.inspect_recovery(blob,mem.files.__getitem__)
            remaining,suffix=drive(restored,mem)
            assert prefix+suffix==events
            check_authority(remaining['authority'],expected['state'])
            assert remaining['status']==actual['status']
            keys=[(e['before_hash'],e['kind'],tuple(e['rows'])) for e in prefix+suffix]
            assert len(keys)==len(set(keys))
            counts['splits']+=1;counts['after_decision_splits']+=cut>0
        for cut,boundary in enumerate(expected['boundaries'][:-1]):
            mem=Memory();first,_=drive(initial,mem,stop_after=cut)
            p=worker.plan_start(materialize(first['authority']))
            op=oracle.begin(boundary)
            check_authority(p,op)
            restored=worker.inspect_recovery(worker.authority_bytes(p),mem.files.__getitem__)
            refused,none=drive(restored,mem)
            assert refused['status']=='error' and not none and refused['authority']==restored
            resumed,after=drive(explicit_test_abandon(restored),mem)
            reference=oracle.run(oracle.abandon_pending(op))
            assert after==[projection(e) for e in reference['events']]
            check_authority(resumed['authority'],reference['state'])
            counts['pending_refusal_and_lost_charge']+=1
        trace_digest.update(oracle.canonical([n,points,events]))
    cap_results=[]
    for rc,pc in ((0,32),(2,32),(3,0),(3,1)):
        expected=oracle.run(oracle.fresh(fixtures.LOCAL,4,row_cap=rc,pair_cap=pc))
        actual,events=drive(worker.new_authority(fixtures.LOCAL,4,row_cap=rc,pair_cap=pc),Memory())
        assert actual['status']==expected['state']['status'];check_authority(actual['authority'],expected['state'])
        cap_results.append({'row_cap':rc,'pair_cap':pc,'status':actual['status'],'U':actual['authority']['U']})
    for kind in ('row','pair'):
        base=dict(row_started=511 if kind=='row' else 0,row_completed=511 if kind=='row' else 0,
                  pair_started=95 if kind=='pair' else 0,pair_completed=95 if kind=='pair' else 0,accepted=0)
        initial=worker.new_authority(fixtures.LOCAL,4,base=base)
        mem=Memory();a=initial if kind=='row' else drive(initial,mem,stop_after=3)[0]['authority']
        p=worker.plan_start(materialize(a));loaded=worker.inspect_recovery(worker.authority_bytes(p),mem.files.__getitem__)
        actual,_=drive(explicit_test_abandon(loaded),mem)
        assert actual['status']==kind+'_cap' and actual['authority']['points']==a['points']
        assert actual['authority']['counters'][kind+'_started']==a['caps'][kind]
        assert actual['authority']['counters'][kind+'_completed']==a['counters'][kind+'_completed']
        assert actual['authority'][kind+'_cursor']==a[kind+'_cursor']
        counts['last_allowance_lost']+=1
    # Source-supported imported coverage is tested with a tiny real pair
    # nonimprovement reached only under the disclosed Stage1 control stub.
    reference_initial=oracle.fresh(prefix_fixture.POINTS,4,row_used=308,pair_used=32,generation=28,pair_cap=96)
    reference=oracle.run(reference_initial,row_control_stub=True)
    cut=next(i+1 for i,e in enumerate(reference['events']) if e['kind']=='pair')
    covered=reference['boundaries'][cut]
    base={k:covered[k] for k in ('row_started','row_completed','pair_started','pair_completed')}
    base['accepted']=covered['generation']
    imported=worker.new_authority(prefix_fixture.POINTS,4,base=base,pair_prefix=1,row_complete=True)
    assert imported['origin']['basis']=='source_bound_prior_execution_not_independent_minimum_certificate'
    actual,events=drive(imported,Memory())
    expected=oracle.run(covered)
    assert events==[projection(e) for e in expected['events']]
    assert len(events)==1 and events[0]['rows']==[0,2]
    check_authority(actual['authority'],expected['state'])
    counts['imported_completed_prefix_cases']+=1
    for prefix,row_complete in ((7,True),(1,False)):
        try:worker.new_authority(prefix_fixture.POINTS,4,base=base,pair_prefix=prefix,row_complete=row_complete)
        except ValueError:counts['invalid_imported_prefix_rejections']+=1
        else:raise AssertionError('invalid imported prefix accepted')
    # Disclosed stub only for Stage1; pair optimizers remain genuine geometry.
    original=worker.kernel.row_optimum
    def current(points,index,n,row,check,work):
        return {'score':oracle.exact.raw(points),'columns':tuple(x for x,y in points if y==row),
                'points':points,'zero':False,'enumeration_complete':True}
    stub_results=[]
    try:
        worker.kernel.row_optimum=current
        for points in (fixtures.DENSE,prefix_fixture.POINTS):
            reference=oracle.run(oracle.fresh(points,4),row_control_stub=True)
            a=worker.new_authority(points,4);mem=Memory();actual,events=drive(a,mem)
            assert events==[projection(e) for e in reference['events']]
            check_authority(actual['authority'],reference['state'])
            for cut,boundary in enumerate(reference['boundaries']):
                memory=Memory();first,prefix=drive(a,memory,stop_after=cut)
                restored=worker.inspect_recovery(worker.authority_bytes(first['authority']),memory.files.__getitem__)
                remaining,suffix=drive(restored,memory)
                assert prefix+suffix==events
                check_authority(remaining['authority'],reference['state'])
                counts['disclosed_stub_splits']+=1
            stub_results.append({'points':points,'events':events,'status':actual['status']})
    finally:worker.kernel.row_optimum=original
    # Full positive terminal is controller-only: both optimizers return current.
    old_pair=worker.kernel.pair_optimum
    def current_pair(points,index,n,r,s,check,work):
        return {'score':oracle.exact.raw(points),'X':tuple(x for x,y in points if y==r),
                'Y':tuple(x for x,y in points if y==s),'points':points,'zero':False,'enumeration_complete':True}
    try:
        worker.kernel.row_optimum=current;worker.kernel.pair_optimum=current_pair
        terminal,events=drive(worker.new_authority(fixtures.LOCAL,4),Memory())
        authority=terminal['authority']
        assert terminal['status']=='no_strict_descent' and authority['U']==1 and authority['generation']==0
        assert authority['row_sweep_complete'] and authority['pair_scan_complete'] and authority['pending'] is None
        assert authority['row_cursor']==3 and authority['pair_cursor']==6
        counts['positive_terminal_control_stub_cases']+=1
    finally:worker.kernel.row_optimum=original;worker.kernel.pair_optimum=old_pair
    interrupted=[interrupts(fixtures.LOCAL),interrupts(fixtures.DENSE)]
    assert sha(worker.__file__)==WORKER_SHA and sha(oracle.__file__)==ORACLE_SHA and sha(worker.kernel.__file__)==KERNEL_SHA
    return {'passed':True,'scope':'SOURCE/TINY logical comparison only; no actual input/loader/run.',
            'worker_sha256':WORKER_SHA,'oracle_sha256':ORACLE_SHA,'kernel_sha256':KERNEL_SHA,
            'audit_sha256':sha(__file__),'counts':dict(counts),'trace_sha256':trace_digest.hexdigest(),
            'cap_cases':cap_results,'disclosed_stage1_stubs':stub_results,'interruptions':interrupted,
            'elapsed_seconds':time.monotonic()-started,
            'limits':'Memory byte/reference callbacks do not prove filesystem durability or real validator lifecycle. Positive pair and nonimproving pair supplements stub Stage1;87 genuine full-policy traces have no positive terminal or nonimproving pair. Actual historical32-prefix remains source-supported.'}


if __name__=='__main__':
    result=run();path=Path('data/two-row-suffix-independent-worker-audit-v2.json')
    assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='disclosed_stage1_stubs'},sort_keys=True))
    print(sha(path))
