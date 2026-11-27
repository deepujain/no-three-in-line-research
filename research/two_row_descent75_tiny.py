"""Author synthetic geometry/control/lifecycle checks. Never reads actual inputs."""
from contextlib import ExitStack
from itertools import combinations, product
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import two_row_descent75 as w

LOCAL = ((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
DENSE = ((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3))


def raw(points):
    return sum((b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]) for a,b,c in combinations(points,3))


def states(n):
    for deficient in range(n):
        for singleton in range(n):
            for choices in product(tuple(combinations(range(n),2)),repeat=n-1):
                it = iter(choices)
                yield tuple(sorted((x,y) for y in range(n) for x in ((singleton,) if y==deficient else next(it))))


def geometry():
    counts = {'states':0,'row_optima':0,'pair_optima':0,'partner_ties':0}
    # Independent Math exhausts all3541 states. Author QA uses every n2/n3
    # state and explicit n4 falsifiers, without duplicating that full audit.
    for n,points in [(n,p) for n in (2,3) for p in states(n)]+[(4,LOCAL),(4,DENSE)]:
        points,index,score = w.build_index(points,n)
        assert score == raw(points); counts['states'] += 1
        triples = [t for t in combinations(points,3) if raw(t)]
        priorities = w.priorities(points,index,n)
        assert priorities['I'] == tuple(sum(any(y==r for x,y in t) for t in triples) for r in range(n))
        for row in range(n):
            retained = tuple(p for p in points if p[1]!=row); load = len(points)-len(retained)
            expected = min((raw(retained+tuple((x,row) for x in cols)),cols) for cols in combinations(range(n),load))
            result = w.row_optimum(points,index,n,row)
            assert (result['score'],result['columns']) == expected
            counts['row_optima'] += 1
        for r,s in combinations(range(n),2):
            retained = tuple(p for p in points if p[1] not in (r,s)); total = len(points)-len(retained)
            outer = sorted(X for size in ((2,) if total==4 else (1,2)) for X in combinations(range(n),size))
            assert list(w.outer_sets(n,total)) == outer
            expected = min((raw(retained+tuple((x,r) for x in X)+tuple((y,s) for y in Y)),X,Y)
                           for X in outer for Y in combinations(range(n),total-len(X)))
            result = w.pair_optimum(points,index,n,r,s)
            assert (result['score'],result['X'],result['Y']) == expected
            assert raw(result['points']) == result['score'] <= score
            counts['pair_optima'] += 1
    for costs in product(range(3),repeat=4):
        for b in (1,2):
            expected = min((sum(costs[y] for y in Y),Y) for Y in combinations(range(4),b))
            assert w.best_partner(iter(costs),b) == expected
            counts['partner_ties'] += 1
    return counts


def controls():
    outcomes = []
    for rowcap,paircap in ((0,32),(2,32),(512,0),(512,1),(512,32)):
        result = w.descend(LOCAL,4,rowcap,paircap)
        assert result['row_started'] <= rowcap and result['pair_started'] <= paircap
        assert result['row_completed'] <= result['row_started'] and result['pair_completed'] <= result['pair_started']
        assert raw(result['points']) == result['U']
        if rowcap < 3: assert result['status']=='row_cap' and not result['row_sweep_complete'] and result['points']==tuple(sorted(LOCAL))
        elif paircap==0: assert result['status']=='pair_cap' and result['row_sweep_complete'] and not result['pair_scan_complete']
        else: assert result['U']==0 and result['row_started']==3 and result['pair_started']==1
        outcomes.append({k:result[k] for k in ('status','U','row_started','pair_started','row_sweep_complete','pair_scan_complete')})
    full_events=[]; full_work={}; calls=[]
    w.descend(DENSE,4,commit=full_events.append,work=full_work,check=lambda:calls.append(full_work.get('phase')))
    assert any(e['score']>0 for e in full_events)
    # Every cooperative stop retains only a fully rebuilt committed prefix.
    interrupted = 0
    for stop_at in range(1,len(calls)+1):
        work={}; committed=[]; counter=[0]
        def check():
            counter[0]+=1
            if counter[0]==stop_at: raise w.SearchStop('synthetic_stop')
        result = w.descend(DENSE,4,check=check,commit=committed.append,work=work)
        expected = tuple(sorted(DENSE)) if not committed else committed[-1]['points']
        assert result['points']==expected and result['U'] in (None,raw(expected))
        assert result['row_completed']<=result['row_started']<=512 and result['pair_completed']<=result['pair_started']<=32
        assert result['accepted']==len(committed)
        interrupted += 1
    # The complete no-improvement branch has no real n2..4 positive fixture;
    # this is explicitly a controller-only current-returning optimizer stub.
    def row_stub(points,index,n,row,*args):
        return {'score':raw(points),'columns':tuple(x for x,y in points if y==row),'zero':False}
    def pair_stub(points,index,n,r,s,*args):
        return {'score':raw(points),'X':tuple(x for x,y in points if y==r),'Y':tuple(x for x,y in points if y==s),'zero':False}
    with patch.object(w,'row_optimum',row_stub),patch.object(w,'pair_optimum',pair_stub):
        result=w.descend(LOCAL,4)
    assert result['status']=='no_strict_descent' and result['row_sweep_complete'] and result['pair_scan_complete']
    return {'cap_fixtures':outcomes,'interrupted_check_positions':interrupted,'positive_prefix_moves':sum(e['score']>0 for e in full_events),
            'terminal_branch':'controller stub only, not geometric local-minimum evidence'}


def lifecycle(mode):
    """n4 actual geometry/validators; fixed actual-handoff loader is stubbed.

    The mocked loader bypasses the production97 precondition solely to exercise
    publication branches. These artifacts are never valid input/actual receipts.
    """
    with tempfile.TemporaryDirectory(prefix='two-row-tiny-') as directory:
        root=Path(directory).resolve(); (root/'src').mkdir(); (root/'research').mkdir(); (root/'data').mkdir()
        (root/'src/verify.py').write_text('synthetic verifier pin')
        (root/'research/row_block_breakout75_actual_audit.py').write_text('synthetic audit pin')
        (root/w.HANDOFF_PATH).write_text('synthetic metadata pin')
        sentinel=root/'sentinel'; sentinel.write_text('unchanged')
        manifest=root/'pins.json'; out=root/'output'; out.mkdir()
        pins={str(Path(w.__file__).resolve()):w.digest(w.__file__),str(Path(w.sys.executable).resolve()):w.digest(w.sys.executable)}
        for p in (root/'src/verify.py',root/'research/row_block_breakout75_actual_audit.py',root/w.HANDOFF_PATH,sentinel): pins[str(p)]=w.digest(p)
        manifest.write_text(json.dumps(pins)); events=[]; clock={'now':0}; first=w.verify_certificate; second=w.verify_certificate_bruteforce
        atomic=w.atomic_bytes; descent=w.descend; counters={'first':0,'second':0,'report':0}
        def validator1(candidate):
            counters['first']+=1;events.append('validator1'); result=first(candidate)
            if mode=='late_first':clock['now']=26
            return result
        def validator2(candidate):
            counters['second']+=1;events.append('validator2');result=second(candidate)
            if mode=='late_second':clock['now']=26
            if mode=='disagreement':result['valid']=False
            return result
        def save(path,value):
            events.append(path.name)
            if path.name=='completed-boundary.json' and mode=='boundary_failure': raise OSError('synthetic boundary failure')
            if path.name=='valid149.json' and mode=='witness_save_failure': raise OSError('synthetic witness save failure')
            if path.name=='report.json':
                counters['report']+=1
                if mode=='report_failure' and counters['report']==1: raise OSError('synthetic report failure')
                if mode=='late_report':clock['now']=26
            if path.name=='raw-zero.json' and mode=='raw_write_latency':clock['now']=26
            atomic(path,value)
            if path.name=='valid149.json' and mode=='pin_drift':sentinel.write_text('changed')
        def run_descent(points,n,**kwargs):
            callback=kwargs['commit']
            def commit(event):
                if mode=='late_zero':clock['now']=26
                callback(event)
            kwargs['commit']=commit
            return descent(points,n,**kwargs)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(w,ROOT=root,N=4))
            for name,value in (('load_handoff',lambda pins,check:(tuple(sorted(LOCAL)),{'scope':'synthetic loader stub'})),
                               ('verify_certificate',validator1),('verify_certificate_bruteforce',validator2),('atomic_bytes',save),('descend',run_descent)):
                stack.enter_context(patch.object(w,name,value))
            report=w.run(out,manifest,clock=lambda:clock['now'],started=0)
        assert json.loads((out/'report.json').read_text())==json.loads(json.dumps(report))
        if mode in ('normal','raw_write_latency'):assert report['accepted'] and report['witness_saved'] and 'raw-zero.json' not in events,(mode,report,events)
        else:assert not report['accepted'],(mode,report)
        if mode in ('normal','raw_write_latency','late_second','boundary_failure','report_failure','late_report','pin_drift'):
            assert report['witness_saved'] and (out/'valid149.json').exists()
            assert events.index('valid149.json')==events.index('validator2')+1
        if mode in ('late_first','late_zero','disagreement','witness_save_failure'):
            assert not report['witness_saved'] and report['raw_zero_saved'] and (out/'raw-zero.json').exists()
        if mode=='late_first':assert counters['first']==1 and counters['second']==0
        if mode=='late_zero':assert counters['first']==counters['second']==0
        if mode=='boundary_failure':assert not report['boundary_saved']
        return {'mode':mode,'accepted':report['accepted'],'witness_saved':report['witness_saved'],
                'boundary_saved':report['boundary_saved'],'validator_calls':[counters['first'],counters['second']]}


def malformed_handoff():
    blocked=0
    for malformed in ({},{'schema':'wrong'},{'schema':'two-row-fixed-handoff-identities-v1','n':74}):
        with patch.object(w,'validate_points',side_effect=AssertionError('geometry entered before chain')):
            try:w.authenticate_chain({},malformed,{})
            except ValueError:blocked+=1
            else:raise AssertionError('malformed handoff accepted')
    return {'malformed_metadata_rejected_before_geometry':blocked,'limitation':'Full fixed source chain remains separately reviewed; no actual artifact read.'}


def main():
    result={'passed':True,'worker_sha256':w.digest(w.__file__),'tiny_sha256':w.digest(__file__),
            'geometry':geometry(),'controls':controls(),'handoff':malformed_handoff(),
            'lifecycle':[lifecycle(mode) for mode in ('normal','raw_write_latency','late_first','late_second','late_zero','disagreement',
                         'witness_save_failure','boundary_failure','report_failure','late_report','pin_drift')],
            'scope':'n2..4 synthetic geometry/control/validators and isolated loader-stub lifecycle only; no actual source coordinates or n75 geometry/search.'}
    path=w.ROOT/'data/two-row-descent75-author-tiny-v3.json';path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
