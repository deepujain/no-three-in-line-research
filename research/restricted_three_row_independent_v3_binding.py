"""Final v3 source binding and preserved independent synthetic-suite rebinding."""
import ast
import hashlib
import json
from pathlib import Path
from research import restricted_three_row_independent_worker_audit as parity
from research import restricted_three_row_independent_control_preparation as control
from research import restricted_three_row_independent_interruptions as interruptions

V2='87e69fb151cbad1677aab5605aa734f2d38ca8c6c68c2b8b8d7503a8d93b32ce'
V3='d4d3a272ca8691c110b881ba739d31f95a858406c20e711ef588e712ebff794c'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    old=Path('research/restricted_three_row75_v2_frozen.py');new=Path(parity.worker.__file__)
    assert sha(old)==V2 and sha(new)==V3
    before=ast.parse(old.read_text());after=ast.parse(new.read_text())
    def functions(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    b,a=functions(before),functions(after)
    assert b.keys()==a.keys() and sorted(k for k in b if b[k]!=a[k])==['drive','run']
    for tree in (before,after):tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in ('drive','run')]
    assert ast.dump(before,include_attributes=False)==ast.dump(after,include_attributes=False)
    parity.WORKER_SHA=control.WORKER_SHA=interruptions.WORKER_SHA=V3
    results={'parity':parity.run(),'control':control.run(),'interruptions':interruptions.run()}
    assert sha(old)==V2 and sha(new)==V3
    return {'passed':True,'v2_sha256':V2,'v3_sha256':V3,'changed_functions':['drive','run'],
            'source_sha256':sha(__file__),'scope':'SOURCE/TINY only, no actual loader/run. Suite expected-worker pins explicitly rebound in memory; original source/evidence preserved.',
            'results':results,'limits':'Mathematical/control parity and source ownership inspection only. Separate lifetime/owned-resource evidence is not independently measured here.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-v3-binding.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'source_sha256':sha(__file__),'evidence_sha256':sha(path),
                     'counts':{k:result['results']['parity'][k] for k in ('profiles','table_cases','assignment_comparisons','decisions','split_reload_cases')}}))
