"""Actual adapter main/output handling over closed synthetic inputs; no actual outcomes."""
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
from research import restricted_three_row64_audit_synthetic_fixture_v2 as f

a=f.adapter
ADAPTER_SHA='31ad510c53f3480a339f92b9b9366e7a912daf10e474d99c5b5d4c6ce74bb26d'

def run():
    assert f.digest(Path(a.__file__).read_bytes())==ADAPTER_SHA
    cases=[]
    with tempfile.TemporaryDirectory(prefix='fixed64-audit-main-') as directory:
        root=Path(directory).resolve()
        for mode in ('ordinary','input_digest','receipt_failure','deadline_before_read','late_persistence'):
            x=f.fixture('cap_noaccept');out=root/(mode+'.json');specpath=root/(mode+'-spec.json')
            if mode=='receipt_failure':x['receipt']['independent_reviews_unchanged']=False;f.reseal(x)
            raw=f.pack(x['spec']);specpath.write_bytes(raw);x['files'][str(specpath)]=raw
            sha=f.digest(raw);source=f.ClosedSource(x);now=[26. if mode=='deadline_before_read' else 1.];saved=[]
            save=a.save_result
            def save_result(path,result):
                saved.append(result['accepted']);save(path,result)
                if mode=='late_persistence':now[0]=26.
            argv=['adapter','--inputs',str(specpath),'--inputs-sha256',('0'*64 if mode=='input_digest' else sha),'--output',str(out),'--seconds','25']
            with f.fixture_patches(x),patch.object(a,'DiskSource',lambda:source),patch.object(a,'ENTRY_STARTED',0.),\
                 patch.object(a.time,'monotonic',lambda:now[0]),patch.object(a,'save_result',save_result),patch.object(a.sys,'argv',argv):
                status=a.main()
            result=json.loads(out.read_text());assert status==(0 if mode=='ordinary' else 2)
            assert result['accepted'] is (mode=='ordinary')
            if mode=='ordinary':assert result['input_spec_bytes_sha256']==sha and result['effective_pins']==298
            if mode=='late_persistence':assert saved==[True,False]
            if mode=='deadline_before_read':assert not source.events
            cases.append({'mode':mode,'exit_status':status,'accepted':result['accepted'],'save_sequence':saved,
                          'error':result.get('error'),'output_sha256':f.digest(out.read_bytes())})
    assert f.digest(Path(a.__file__).read_bytes())==ADAPTER_SHA
    return {'passed':True,'adapter_sha256':ADAPTER_SHA,'fixture_sha256':f.digest(Path(f.__file__).read_bytes()),
        'source_sha256':f.digest(Path(__file__).read_bytes()),'cases':cases,
        'scope':'Real main argparse, accepted/error output and bounded write path. Closed byte source, declared n75 geometry/source labels, scripted clock. Actual file writes/fsync only in newly created temporary directory; no crash/owned RSS or actual run acceptance evidence.'}

if __name__=='__main__':
    output=Path('data/restricted-three-row64-audit-main-tiny-v2.json');assert not output.exists();result=run()
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'source_sha256':result['source_sha256'],'cases':len(result['cases'])}))
