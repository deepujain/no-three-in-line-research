"""Coordinate-free required-pin review; no artifact payload reads or worker imports."""
import ast
import hashlib
import json
from pathlib import Path
import sys
from research import restricted_three_row64_manifest_preflight as checker

ROOT=Path(__file__).resolve().parents[1]
CHECKER_SHA='de46849003d1e9aa9c107e164838b894d820de914fa6ff736d49e2560d912c10'
WORKER_SHA='e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
PRIOR_SHA='7d0ab3cc50b2e7349218be5b33ea6897047a69879f27c03693efa7656e16a51d'
METADATA_SHA='2d6ba98abf571bc430f9a6e51a0dec5e99db68246e780ac24a5c8ba65b025ced'
ORIGINAL_SHA='feb16b236a7b4b47220040d75f0f7dea28a2401c9b92cd187e947049e98f5842'


def read(name,expected=None):
    raw=(ROOT/name).read_bytes()
    if expected:assert hashlib.sha256(raw).hexdigest()==expected,name
    return raw


def independent_normalize(mapping):
    result={}
    assert type(mapping) is dict
    for name,value in mapping.items():
        assert type(name) is str and type(value) is str and len(value)==64 and set(value)<=set('0123456789abcdef')
        key=str((ROOT/name).resolve());assert key not in result
        result[key]=value
    return result


def run(manifest):
    read('research/restricted_three_row64_manifest_preflight.py',CHECKER_SHA)
    worker=read('research/restricted_three_row64.py',WORKER_SHA)
    prior=independent_normalize(json.loads(read('data/restricted-three-row75-source-pins.json',PRIOR_SHA)))
    metadata=json.loads(read('data/restricted-three-row64-input-identities.json',METADATA_SHA))
    assert len(prior)==228 and len(metadata['artifacts'])==51
    # Independently recover constants by literal AST evaluation, never importing worker.
    constants={};sources=None
    for node in ast.parse(worker).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('ENGINE_SHA','ADAPTER_SHA','CHAIN_SHA','COMMON_SHA'):constants[name]=ast.literal_eval(node.value)
            if name=='SOURCE_IDENTITIES':
                sources={ast.literal_eval(k):(constants[v.id] if isinstance(v,ast.Name) else ast.literal_eval(v))
                         for k,v in zip(node.value.keys,node.value.values)}
    assert len(sources)==6
    required=dict(prior)
    def merge(values):
        for name,value in independent_normalize(values).items():
            assert name not in required or required[name]==value
            required[name]=value
    merge({'data/restricted-three-row75-source-pins.json':PRIOR_SHA})
    merge(metadata['artifacts']);merge(sources)
    merge({'research/restricted_three_row64.py':WORKER_SHA,'data/restricted-three-row64-input-identities.json':METADATA_SHA})
    assert str(Path(sys.executable).resolve()) in required and str((ROOT/'src/verify.py').resolve()) in required
    contract=checker.read_contract();assert checker.required_pins(contract)==required
    raw=read(manifest);pins=independent_normalize(json.loads(raw));path=(ROOT/manifest).resolve()
    assert len(raw)<=128*1024 and len(pins)<=512 and str(path) not in pins
    assert all(pins.get(name)==sha for name,sha in required.items())
    original=independent_normalize(json.loads(read('data/restricted-three-row64-source-pins.json',ORIGINAL_SHA)))
    assert all(pins.get(name)==sha for name,sha in original.items())
    missing={name:sha for name,sha in required.items() if name not in original}
    assert set(missing)=={str(ROOT/name) for name in (
        'research/restricted_three_row_actual_chain_adapter.py','research/restricted_three_row_independent_chain_audit.py',
        'research/two_row_suffix_independent_authority_audit.py')}
    baseline=checker.preflight(path);rejections=[]
    def reject(label,mutant):
        try:checker.check_manifest(mutant,contract,path)
        except ValueError as exc:rejections.append({'case':label,'error':str(exc)})
        else:raise AssertionError(label)
    reject('original_missing_three',original)
    for name in sources:
        key=str((ROOT/name).resolve());mutant=dict(pins);del mutant[key];reject('missing:'+name,mutant)
        mutant=dict(pins);mutant[key]='0'*64;reject('wrong:'+name,mutant)
    mutant=dict(pins);mutant[str(path.parent/('./'+path.name))]='0'*64;reject('self',mutant)
    mutant=dict(pins);key=str(ROOT/'research/restricted_three_row64.py')
    mutant[str(ROOT)+'/research/./restricted_three_row64.py']=mutant[key];reject('normalized_alias',mutant)
    return {'passed':True,'manifest':manifest,'manifest_sha256':hashlib.sha256(raw).hexdigest(),
        'baseline':baseline,'independent_union_entries':len(required),'original_manifest_sha256':ORIGINAL_SHA,
        'original_entries_preserved':len(original),'original_missing_required':missing,'source_identity_count':len(sources),
        'checker_sha256':CHECKER_SHA,'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rejections':rejections,'rejection_count':len(rejections),
        'scope':'Coordinate-free manifest and identity metadata only, independent literal AST source contract. No worker import, actual payload read/hash, geometry, gate, outcome acceptance or retry.'}


if __name__=='__main__':
    manifest=sys.argv[1];output=Path(sys.argv[2]);result=run(manifest)
    with output.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('passed','manifest_sha256','independent_union_entries','rejection_count','test_sha256')}))
