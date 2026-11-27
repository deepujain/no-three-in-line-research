"""Author tiny geometry/transaction/publication checks; no actual n75 search."""
from contextlib import ExitStack
from dataclasses import replace
from itertools import combinations, product
import json
from pathlib import Path
import random
import tempfile
from unittest.mock import patch
from research import row_block_breakout75 as w


def states(n):
    pairs=tuple(combinations(range(n),2))
    for deficient in range(n):
        for singleton in range(n):
            for rows in product(pairs,repeat=n-1):
                it=iter(rows)
                yield tuple(sorted((x,y) for y in range(n) for x in ((singleton,) if y==deficient else next(it))))


def direct(points,weights):
    raw=weighted=0
    for a,b,c in combinations(points,3):
        if (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]):
            raw+=1; weight=1
            for (aa,bb,cc),value in weights.items():
                if all(aa*x+bb*y==cc for x,y in (a,b,c)):weight=value;break
            weighted+=weight
    return raw,weighted


def geometry():
    counts=dict(states=0,weighted_states=0,row_outcomes=0,migrations=0)
    for n in (2,3,4):
        weights={(1,0,c):2+c for c in range(n)};weights[(1,-1,0)]=9
        for number,points in enumerate(states(n)):
            _,index,raw,weighted,_=w.build_index(points,n)
            assert (raw,weighted)==direct(points,{})
            counts['states']+=1
            if number>=24:continue
            _,index,raw,weighted,_=w.build_index(points,n,weights)
            assert (raw,weighted)==direct(points,weights);counts['weighted_states']+=1
            for row in range(n):
                costs=w.row_costs(points,index,row,weights,n)
                old=tuple(x for x,y in points if y==row); retained=tuple(p for p in points if p[1]!=row)
                expected=[]
                for xs in combinations(range(n),len(old)):
                    changed=retained+tuple((x,row) for x in xs);score=direct(changed,weights)
                    assert score==(raw+sum(costs['unweighted'][x] for x in xs)-sum(costs['unweighted'][x] for x in old),
                                   weighted+sum(costs['weighted'][x] for x in xs)-sum(costs['weighted'][x] for x in old))
                    counts['row_outcomes']+=1
                    if xs!=old:expected.append((sum(costs['weighted'][x] for x in xs),xs))
                minimum,ties=w.best_row_alternatives(points,row,costs,n)
                if expected:
                    best=min(score for score,_ in expected);assert minimum==best and ties==[xs for score,xs in expected if score==best]
                else:assert minimum is None and not ties
            deficient=next(r for r in range(n) if sum(y==r for _,y in points)==1)
            for donor in points:
                if donor[1]==deficient:continue
                for x in range(n):
                    target=(x,deficient)
                    if target in points:continue
                    delta=w.migration_delta(points,donor,target,weights)
                    score=direct(tuple(p for p in points if p!=donor)+(target,),weights)
                    assert score==(raw+delta['unweighted'],weighted+delta['weighted']);counts['migrations']+=1
    return counts


def seeded(seed):
    rng=random.Random(seed);return w.initial_boundary(4,rng),rng


def transaction_tests():
    b,rng=seeded(0);best,_=seeded(1)
    b=replace(b,best_points=best.points,best_unweighted=best.unweighted,best_weighted_at_capture=best.weighted)
    checkpoints=0
    for phase in ('row_before_draw','row_after_draw','row_costs','row_alternatives','row_tie_before_draw','row_tie_after_draw',
                  'index_build','penalty_precheck','penalty_copy','penalty_update','precommit'):
        work={}; rng.setstate(b.rng_state); before=w.checkpoint_bytes(b,{})
        def stop():
            if work.get('phase')==phase:raise w.SearchStop(phase)
        try:w.propose_transition(b,rng,policy=w.Policy(penalty_period=1),check=stop,work=work);raise AssertionError('missed phase '+phase)
        except w.SearchStop:pass
        assert rng.getstate()==b.rng_state and w.checkpoint_bytes(b,{})==before;checkpoints+=1
    for policy in (w.Policy(penalty_period=1,max_weight_keys=0),w.Policy(penalty_period=1,max_weight=1)):
        rng.setstate(b.rng_state)
        try:w.propose_transition(b,rng,policy=policy);raise AssertionError('weight cap failed')
        except w.WeightCap:pass
        assert rng.getstate()==b.rng_state and not b.weights
    migration_logical=dict(b.logical);migration_logical.update(transitions=15,row_transitions=15)
    migration=replace(b,logical=migration_logical)
    for phase in ('migration_sampling','migration_before_draw','migration_after_draw','migration_sample_complete','index_build'):
        work={};rng.setstate(migration.rng_state)
        def stop():
            if work.get('phase')==phase:raise w.SearchStop(phase)
        try:w.propose_transition(migration,rng,check=stop,work=work);raise AssertionError('migration interruption missed')
        except w.SearchStop:pass
        assert rng.getstate()==migration.rng_state;checkpoints+=1
    # Test-only checkpoint restoration; production has no import/resume API.
    b,rng=seeded(2);b=w.propose_transition(b,rng);payload=json.loads(w.checkpoint_bytes(b,{}))
    metadata=payload['metadata'];restored_rng=random.Random();state=payload['rng'];restored_rng.setstate((state[0],tuple(state[1]),state[2]))
    restored=w.make_boundary(payload['current'],4,restored_rng,weights={tuple(row[:3]):row[3] for row in payload['weights']})
    restored=replace(restored,best_points=tuple(map(tuple,payload['best'])),best_unweighted=metadata['best_unweighted'],
                     best_weighted_at_capture=metadata['best_weighted_at_capture'],best_weight_epoch=metadata['best_weight_epoch'],
                     stagnation=metadata['stagnation'],logical=metadata['logical'])
    a=w.propose_transition(b,rng);c=w.propose_transition(restored,restored_rng)
    assert w.checkpoint_bytes(a,{})==w.checkpoint_bytes(c,{})
    return {'rollback_phases':checkpoints,'weight_caps':2,'split_roundtrips':1}


def lifecycle(mode):
    with tempfile.TemporaryDirectory(prefix='row-block-tiny-') as directory:
        root=Path(directory);(root/'src').mkdir();(root/'src/verify.py').write_text('synthetic source pin')
        sentinel=root/'sentinel';sentinel.write_text('unchanged');manifest=root/'pins.json';out=root/'output';out.mkdir()
        pins={str(Path(w.__file__).resolve()):w.digest(w.__file__),'src/verify.py':w.digest(root/'src/verify.py'),
              str(Path(w.sys.executable).resolve()):w.digest(w.sys.executable),str(Path(w.random.__file__).resolve()):w.digest(w.random.__file__),
              'sentinel':w.digest(sentinel)}
        manifest.write_text(json.dumps(pins));state={'now':0,'second_calls':0,'events':[],'checkpoint_writes':0}
        initial,advance,first,second,atomic,serialize=w.initial_boundary,w.propose_transition,w.verify_certificate,w.verify_certificate_bruteforce,w.atomic_bytes,w.checkpoint_bytes
        def initialize(n,rng,**kwargs):
            local=random.Random(0);b=initial(4,local)
            if mode in ('zero','late_first','late_second','disagreement','late_raw_zero','checkpoint_failure','witness_then_pin_drift'):
                while b.unweighted:b=advance(b,local)
            rng.setstate(b.rng_state)
            if mode=='late_raw_zero':state['now']=26
            return b
        def transition(b,rng,**kwargs):
            if mode=='pin_drift':sentinel.write_text('changed')
            raise w.SearchStop('synthetic_completed_prefix_stop')
        def validator1(candidate):
            value=first(candidate)
            if mode=='late_first':state['now']=26
            return value
        def validator2(candidate):
            state['second_calls']+=1;state['events'].append('validator2');value=second(candidate)
            if mode=='late_second':state['now']=26
            if mode=='disagreement':value['valid']=not value['valid']
            return value
        def save(path,raw):
            state['events'].append(path.name)
            if path.name=='completed-boundary.json':
                state['checkpoint_writes']+=1
                if mode=='checkpoint_failure':raise OSError('synthetic checkpoint failure')
            atomic(path,raw)
            if path.name=='valid149.json' and mode=='witness_then_pin_drift':sentinel.write_text('changed')
        def checkpoint(*args,**kwargs):
            if mode=='serialization_failure':raise ValueError('synthetic serialization failure')
            return serialize(*args,**kwargs)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(w,ROOT=root,N=4,MAX_STEPS=2))
            for name,value in (('initial_boundary',initialize),('propose_transition',transition),('verify_certificate',validator1),
                               ('verify_certificate_bruteforce',validator2),('atomic_bytes',save),('checkpoint_bytes',checkpoint)):
                stack.enter_context(patch.object(w,name,value))
            report=w.run(out,manifest,clock=lambda:state['now'],started=0)
        assert json.loads((out/'report.json').read_text())==json.loads(json.dumps(report))
        if mode in ('normal','zero'):assert report['accepted'] and report['checkpoint_saved']
        else:assert not report['accepted'],(mode,report)
        if mode in ('late_first','late_raw_zero'):
            assert state['second_calls']==0 and report['checkpoint_saved'] and report['validation']=='unverified_zero_candidate'
        if mode in ('zero','late_second','checkpoint_failure','witness_then_pin_drift'):
            assert report['witness_saved'] and (out/'valid149.json').exists()
            assert state['events'].index('valid149.json')==state['events'].index('validator2')+1
        if mode=='late_second':assert report['checkpoint_saved']
        if mode=='disagreement':assert not report['witness_saved']
        if report['checkpoint_saved']:
            raw=(out/'completed-boundary.json').read_bytes()
            assert len(raw)==report['checkpoint_bytes'] and w.digest(out/'completed-boundary.json')==report['checkpoint_sha256']
            assert len(raw)<=w.CHECKPOINT_CAP
        return {'mode':mode,'status':report['status'],'accepted':report['accepted'],'witness_saved':report['witness_saved'],'checkpoint_saved':report['checkpoint_saved']}


def main():
    result={'passed':True,'worker_sha256':w.digest(w.__file__),'tiny_sha256':w.digest(__file__),'geometry':geometry(),
            'transactions':transaction_tests(),'lifecycle':[lifecycle(mode) for mode in ('normal','zero','late_first','late_second','late_raw_zero',
            'disagreement','checkpoint_failure','serialization_failure','pin_drift','witness_then_pin_drift')],
            'scope':'Synthetic n2..4 geometry, transaction boundaries and isolated n4 shutdown; no actual n75 geometry/search or production checkpoint import.'}
    target=Path(__file__).resolve().parents[1]/'data/row-block-breakout75-author-tiny-v2.json';target.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
