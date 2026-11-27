"""Bounded finite n2..4 oracle preparation; no production imports or actual inputs."""
import hashlib
import json
from pathlib import Path
import resource
import time
from research import restricted_three_row_independent_oracle as oracle


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run():
    started=time.monotonic();pins={p:sha(p) for p in (__file__,oracle.__file__)}
    def check():
        if time.monotonic()-started>20:raise TimeoutError('fixed20-second synthetic preparation cap')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>256*1024*1024:raise MemoryError('fixed256MiB synthetic preparation cap')
    census={};fixtures=[];multiplicity=None;maximum=0
    for n in (2,3,4):
        count=0;digest=hashlib.sha256()
        for index,points in enumerate(oracle.all_states(n)):
            check();profile=oracle.profile(points,n);count+=1;maximum=max(maximum,profile['U'])
            digest.update(oracle.canonical({'points':points,'U':profile['U'],'records':profile['records']}))
            if n<=3 or index%108==0 or index==3455:fixtures.append((n,points))
            if multiplicity is None and any(k>1 for k in profile['K'].values()):multiplicity=(n,points)
        census[n]={'states':count,'direct_profile_digest':digest.hexdigest()}
    assert [census[n]['states'] for n in (2,3,4)]==[4,81,3456]
    assert multiplicity is not None
    fixtures.append(multiplicity)
    fixtures=list(dict.fromkeys(fixtures));cases=[];assignment_count=0;orientation=set();ternary_positive=0;cross_positive=0
    for n,points in fixtures:
        for rows in oracle.combinations(range(n),3):
            check();result=oracle.optimum(points,n,rows,check);table=result['table'];assignment_count+=result['count']
            assert table['base']==0 and not any(v for row in table['unary'] for v in row)
            cross_positive+=sum(v>0 for cross in table['C'].values() for v in cross.values())
            ternary_positive+=sum(v>0 for v in table['T'].values())
            for choice in oracle.assignments(table['domains'],sum(map(len,table['current']))):orientation.add(tuple(map(len,choice)))
            cases.append({'n':n,'points':points,'rows':rows,'minimum':result['minimum'],'assignments':result['count'],
                          'first_zero_index':result['first_zero_index'],'trace_sha256':result['trace_sha256']})
    assert orientation=={(2,2,2),(1,2,2),(2,1,2),(2,2,1)} and ternary_positive and cross_positive
    falsifier=((0,0),(0,1),(1,1),(0,2),(1,2));t=oracle.tables(falsifier,3,(0,1,2))
    assert t['base']==0
    assert oracle.objective(t,*t['current'])==oracle.raw(falsifier)==1
    assert all(v==0 for row in t['unary'] for v in row) and all(v==0 for c in t['C'].values() for v in c.values())
    assert pins=={p:sha(p) for p in pins};check()
    return {'passed':True,'scope':'Finite synthetic n2..4 only; no worker or actual input import/read.',
            'source_pins':pins,'census':census,'fixtures':len(fixtures),'block_cases':len(cases),'assignment_checks':assignment_count,
            'cases':cases,'K_multiplicity_fixture':multiplicity,'load_orientations':sorted(orientation),
            'positive_cross_entries':cross_positive,'positive_ternary_entries':ternary_positive,'ternary_falsifier_score':1,
            'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'limits':'All3541 states are explicitly counted above:4+81+3456. Full literal I/J/K/M census; exhaustive assignments only in selected block fixtures. Retained base and unaries are structurally zero for n<=4/three selected rows. No pair-stuck claim or controller/production parity yet.'}

if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row-independent-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'fixtures':result['fixtures'],'blocks':result['block_cases'],'assignments':result['assignment_checks'],
                     'elapsed':result['elapsed_seconds'],'oracle_sha256':sha(oracle.__file__),'preparation_sha256':sha(__file__),'evidence_sha256':sha(path)}))
