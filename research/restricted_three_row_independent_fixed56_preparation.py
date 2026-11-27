"""Exactly four Root-authorized synthetic n5/n6 component fixtures; no census/search."""
import hashlib
import json
from pathlib import Path
import resource
import time
from research import restricted_three_row_independent_oracle as oracle

ORACLE_SHA='f63cd423929ed49a3337f23fe0a75cb823ffe9f73689cf27b788505a87b69d9d'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    started=time.monotonic();source=sha(__file__);assert sha(oracle.__file__)==ORACLE_SHA
    def check():
        if time.monotonic()-started>10:raise TimeoutError('fixed10-second component cap')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>128*1024*1024:raise MemoryError('fixed128MiB target exceeded')
    results=[];tripletests=0;high_current=0;nonzero_base=0;nonzero_unary=0
    for n in (5,6):
        points=tuple(sorted((x,y) for y in range(n) for x in (0,1) if (x,y)!=(1,0)))
        for rows in ((0,1,2),(1,2,3)):
            check();result=oracle.optimum(points,n,rows,check);t=result['table']
            tripletests+=result['count']*((2*n-1)*(2*n-2)*(2*n-3)//6)
            nonzero_base+=t['base']>0;nonzero_unary+=sum(v>0 for row in t['unary'] for v in row)
            for i,cols in enumerate(t['current']):
                assert set(cols)<=set(t['domains'][i]) and len(t['domains'][i])==4
                high_current+=sum(t['unary'][i][x]>min(t['unary'][i]) for x in cols)
                missing=sorted(set(range(n))-set(cols),key=lambda x:(t['unary'][i][x],x))
                assert t['domains'][i]==tuple(sorted((*cols,*missing[:4-len(cols)])))
            results.append({'n':n,'points':points,'rows':rows,'base':t['base'],'unary':t['unary'],'current':t['current'],
                            'domains':t['domains'],'minimum':result['minimum'],'assignments':result['count'],
                            'first_zero_index':result['first_zero_index'],'trace_sha256':result['trace_sha256']})
    assert len(results)==4 and tripletests<=285120 and high_current>0 and nonzero_base>0 and nonzero_unary>0
    assert source==sha(__file__) and sha(oracle.__file__)==ORACLE_SHA;check()
    return {'passed':True,'scope':'Only four explicitly authorized fixed P5/P6 cases and selected rows012/123; no census or optimizer search.',
            'source_sha256':source,'oracle_sha256':ORACLE_SHA,'cases':results,'direct_assignment_tripletests':tripletests,
            'high_unary_current_columns_retained':high_current,'nonzero_base_cases':nonzero_base,'positive_unary_entries':nonzero_unary,
            'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'command':'.venv/bin/python -m research.restricted_three_row_independent_fixed56_preparation',
            'limits':'Component reduction only; no production parity, pair-stuck fixture, actual geometry or selected-family expansion.'}
if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-fixed56-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'cases':len(result['cases']),'direct_assignment_tripletests':result['direct_assignment_tripletests'],
                     'elapsed':result['elapsed_seconds'],'peak_rss_bytes':result['peak_rss_bytes'],'source_sha256':sha(__file__),'evidence_sha256':sha(path)}))
