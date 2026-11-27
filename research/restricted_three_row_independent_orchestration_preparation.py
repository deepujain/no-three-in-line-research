"""Synthetic audit() orchestration only: all artifact/hash/geometry operations are stubbed."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row_actual_chain_adapter as adapter
from research import restricted_three_row_independent_adapter_preparation as metadata


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(mode='cap'):
    report,job,manifest,a,initial,expected,raw,result,runtime=deepcopy(metadata.fixture(228,mode))
    order='b'*64
    # These records are metadata placeholders, not a geometry-valid chain. The
    # chain stub below is intentional and cannot establish actual geometry.
    a['attempts']=[{'order_hash':order} for _ in range(a['counters']['started'])]
    report['attempts']=deepcopy(a['attempts'])
    initial['order_sha256']=order if a['attempts'] else a['orders']['sha256']
    artifact=b'SYNTHETIC REFERENCED MOVE, NO POINTS'
    if mode=='cap':
        a['artifacts']=[{'path':'move-001-attempt-016.json','sha256':'c'*64,'bytes':len(artifact)}]
        report['artifacts']=deepcopy(a['artifacts'])
    if mode=='zero':
        a['witness']['bytes']=len(artifact)
        report['witness']=deepcopy(a['witness'])
    return dict(report=report,job=job,manifest=manifest,a=a,initial=initial,expected=expected,
                raw=raw,result=result,runtime=runtime,artifact=artifact)


def invoke(f, fault=None):
    """Run real audit() control flow with closed synthetic input and digest maps."""
    root=adapter.ROOT
    norm=lambda p:str(Path(p).resolve())
    docs={adapter.REPORT:(b'SYNTHETIC REPORT',f['report']),adapter.RECEIPT:(b'SYNTHETIC RECEIPT',f['job']),
          adapter.MANIFEST:(b'SYNTHETIC MANIFEST',f['manifest']),adapter.AUTHORITY:(f['raw'],{'payload':f['a']}),
          adapter.INITIAL:(b'SYNTHETIC INITIAL',f['initial'])}
    # Digest values are declared synthetic labels: no input byte hashing occurs.
    declared=dict(adapter.normalized_pins(f['manifest']))
    declared.update({norm(root/p):s for p,s in f['expected'].items()})
    declared[norm(adapter.chain.__file__)]=adapter.HELPER_SHA
    declared[norm(adapter.chain.common.__file__)]=adapter.COMMON_SHA
    declared[norm(adapter.__file__)]='d'*64
    refs=list(f['a']['artifacts'])+([] if f['a']['witness'] is None else [f['a']['witness']])
    artifact_paths={}
    for ref in refs:
        path=norm(root/adapter.DIRECTORY/ref['path'])
        artifact_paths[path]=ref
        declared[path]=ref['sha256']
    calls={'digest':Counter(),'authenticated':[],'chain':0,'checks':0}
    chain_ran=False
    def check():calls['checks']+=1
    def digest(path, supplied_check):
        assert supplied_check is check
        supplied_check();path=norm(path);calls['digest'][path]+=1
        if path not in declared:raise AssertionError('unexpected digest path '+path)
        if fault=='pre_source_drift' and path==norm(root/'src/verify.py') and not chain_ran:return '0'*64
        if fault=='pre_helper_drift' and path==norm(adapter.chain.__file__) and not chain_ran:return '0'*64
        post_targets={'post_source_drift':norm(root/'src/verify.py'),
                      'post_input_drift':norm(root/adapter.REPORT),
                      'post_artifact_drift':norm(root/adapter.DIRECTORY/'move-001-attempt-016.json'),
                      'post_helper_drift':norm(adapter.chain.__file__),
                      'post_adapter_drift':norm(adapter.__file__)}
        if chain_ran and path==post_targets.get(fault):return '0'*64
        return declared[path]
    def authenticated(path, expected, supplied_check, cap=2*1024*1024):
        assert supplied_check is check
        supplied_check();path=norm(path);calls['authenticated'].append((path,cap))
        if path not in declared or expected!=declared[path]:raise AssertionError('unexpected authentication request')
        for name,value in docs.items():
            if path==norm(root/name):
                assert cap==2*1024*1024
                if fault=='authentication_rejection' and name==adapter.INITIAL:raise ValueError('synthetic authentication rejection')
                return deepcopy(value)
        if path not in artifact_paths:raise AssertionError('unreferenced artifact read')
        assert cap==16384
        return f['artifact'],{}
    def audit_chain(raw,initial,blobs,**kw):
        nonlocal chain_ran
        calls['chain']+=1;chain_ran=True
        assert raw==f['raw'] and initial==f['initial']
        assert blobs=={r['path']:f['artifact'] for r in refs}
        assert kw==dict(n=75,initial_hash=adapter.STATE,initial_score=65,max_states=17,check=check)
        if fault=='chain_rejection':raise ValueError('synthetic independent chain rejection')
        return deepcopy(f['result'])
    with patch.object(adapter,'EXPECTED',f['expected']),patch.object(adapter,'digest',digest),\
         patch.object(adapter,'authenticated',authenticated),patch.object(adapter.chain,'audit_chain',audit_chain):
        answer=adapter.audit(check)
    assert calls['chain']==1 and calls['checks']>0
    assert set(p for p,cap in calls['authenticated'])=={norm(root/p) for p in docs}|set(artifact_paths)
    assert len(calls['authenticated'])==len(docs)+len(refs)
    for path in adapter.normalized_pins(f['manifest']):assert calls['digest'][path]==2
    assert calls['digest'][norm(adapter.chain.__file__)]==2
    assert calls['digest'][norm(adapter.chain.common.__file__)]==2
    assert calls['digest'][norm(adapter.__file__)]==2
    for path in artifact_paths:assert calls['digest'][path]==1
    assert answer['manifest_entries']==228 and answer['effective_pins']==229
    assert answer['chain']==f['result'] and answer['runtime_path']==f['runtime']
    return {'mode':f['a']['status'],'manifest_entries':228,'effective_pins':229,
            'authenticated_documents':len(calls['authenticated']),'chain_calls':calls['chain'],
            'last_start_charge':f['result']['last_start_charge'],'final_counters':f['result']['counters']}


def run():
    paths=[__file__,adapter.__file__,metadata.__file__,adapter.chain.__file__,adapter.chain.common.__file__]
    sources={str(Path(p).relative_to(adapter.ROOT)):sha(p) for p in paths}
    positives=[invoke(fixture(mode)) for mode in ('cap','pending','nostart','zero')]
    mutations={
        'wrong_fixed_identity_keys':lambda f:f['expected'].pop(adapter.INITIAL),
        'malformed_fixed_digest':lambda f:f['expected'].__setitem__(adapter.REPORT,'bad'),
        'wrong_manifest_count':lambda f:f['manifest'].pop('/synthetic-only/source-0'),
        'manifest_self_entry':lambda f:f['manifest'].__setitem__(str(adapter.ROOT/adapter.MANIFEST),f['expected'][adapter.MANIFEST]),
        'pre_report_pin_mismatch':lambda f:f['report'].__setitem__('pins',{}),
        'pre_receipt_pin_mismatch':lambda f:f['job'].__setitem__('sources_before',{}),
        'too_many_references':lambda f:f['a'].__setitem__('artifacts',f['a']['artifacts']*18),
        'reference_path_escape':lambda f:f['a']['artifacts'][0].__setitem__('path','../move.json'),
        'reference_wrong_length':lambda f:f['a']['artifacts'][0].__setitem__('bytes',1),
        'initial_order_mismatch':lambda f:f['initial'].__setitem__('order_sha256','0'*64),
        'postcompletion_charge':lambda f:f['report'].__setitem__('last_attempted_charge',deepcopy(f['a']['counters'])),
        'unsuccessful_report':lambda f:f['report'].__setitem__('accepted',False),
    }
    rejected=[]
    for name,mutate in mutations.items():
        f=fixture();mutate(f)
        try:invoke(f)
        except ValueError as e:rejected.append({'case':name,'error':str(e)})
        else:raise AssertionError('synthetic corruption accepted '+name)
    for fault in ('pre_source_drift','pre_helper_drift','authentication_rejection','chain_rejection',
                  'post_source_drift','post_input_drift','post_artifact_drift','post_helper_drift','post_adapter_drift'):
        try:invoke(fixture(),fault)
        except ValueError as e:rejected.append({'case':fault,'error':str(e)})
        else:raise AssertionError('synthetic fault accepted '+fault)
    assert all(sha(adapter.ROOT/p)==s for p,s in sources.items())
    return {'passed':True,'sources':sources,'positive_cases':positives,'rejections':rejected,
            'scope':'Real audit() orchestration on fully synthetic metadata with closed declared digest, authenticated, and chain stubs. No actual artifact reads, byte authentication, geometry, or optimizer execution.',
            'limitations':'No actual digest correctness, filesystem behavior, authority parser/geometry correctness, owned process guard, or actual outcome acceptance follows. Those are separate source/tiny and Root-owned gates.'}


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-orchestration-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'positive_cases':len(result['positive_cases']),'rejections':len(result['rejections']),
                      'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
