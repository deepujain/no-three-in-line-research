"""Fixed generic helper/lifecycle fixtures, not exterior-family constructions.

No production worker imports, actual source reads, or source searches occur.
"""
import hashlib
import json
from pathlib import Path
from itertools import product
from collections import Counter
from research import unimodular_extension_independent_design_tiny as design
from research.nonuniform_insertion_independent_tiny_oracle import triples
from src.verify import verify_certificate, verify_certificate_bruteforce

POSITIVE_CERTIFICATE = {'n':5,'points':[(0,0),(2,0),(1,1),(4,1),(1,3),(4,3),(0,4),(2,4),(3,2)]}
OCCUPIED_POINTS = ((0,0),(1,2),(1,4),(2,1),(2,3),(3,2),(3,4),(4,3))
OCCUPIED_FRAME = ((1,0),(0,1))
OCCUPIED_RAW = {(0,0),(0,1),(4,0),(4,1)}
OCCUPIED_EXCLUDED = {(0,0)}
MATRICES = (((0,1),(1,-1)),((1,-1),(1,0)))


def inverse_cases():
    for frame in MATRICES:
        for t in ((0,2),(1,2),(-2,0),(2,-2)):
            for q in ((-3,-1),(6,4),(0,0),(1,2)):
                u,v=frame
                z=(u[0]*q[0]+u[1]*q[1]+t[0],v[0]*q[0]+v[1]*q[1]+t[1])
                yield {'frame':frame,'translation':t,'added':z,'preimage':q}


def protected_cases():
    for q in product((-2,-1,0,3,4,5),repeat=2):
        yield q,(-1<=q[0]<=4 and -1<=q[1]<=4)


def duplicate_collector_cases():
    """Stubbed collector inputs only; second frame is not a source-fit claim."""
    return [
        {'frame':MATRICES[0],'translation':(0,2),'added':(4,4),'preimage':(6,4)},
        {'frame':MATRICES[1],'translation':(2,-2),'added':(4,4),'preimage':(6,4)},
        {'frame':MATRICES[1],'translation':(2,0),'added':(0,4),'preimage':(4,6)},
        {'frame':MATRICES[0],'translation':(0,2),'added':(4,2),'preimage':(4,4)},
        {'frame':MATRICES[1],'translation':(2,0),'added':(2,4),'preimage':(4,4)},
    ]


def main():
    assert not triples(tuple(POSITIVE_CERTIFICATE['points']))
    checks=[v(POSITIVE_CERTIFICATE) for v in (verify_certificate,verify_certificate_bruteforce)]
    assert all(v['valid'] and v['point_count']==9 for v in checks)
    assert checks[0]['normalized_sha256']==checks[1]['normalized_sha256']
    inverse_count=0
    for case in inverse_cases():
        assert design.inverse(*case['frame'],case['translation'],case['added'])==case['preimage']
        inverse_count+=1
    for case in duplicate_collector_cases():
        assert design.inverse(*case['frame'],case['translation'],case['added'])==case['preimage']
    protected=list(protected_cases())
    assert dict(protected)[(-1,4)] and not dict(protected)[(-2,4)] and not dict(protected)[(-1,5)]
    cx,cy=Counter(p[0] for p in OCCUPIED_POINTS),Counter(p[1] for p in OCCUPIED_POINTS)
    raw={(x,y) for x,y in product(range(5),repeat=2) if cx[x]<2 and cy[y]<2}
    assert raw==OCCUPIED_RAW and raw & set(OCCUPIED_POINTS)==OCCUPIED_EXCLUDED
    # The design helper deliberately removes occupied choices.
    candidates=design.candidates(OCCUPIED_POINTS,4,*OCCUPIED_FRAME)
    assert {entry[2] for entry in candidates}==OCCUPIED_RAW-OCCUPIED_EXCLUDED
    records=duplicate_collector_cases()
    exterior={r['preimage'] for r in records if not(-1<=r['preimage'][0]<=4 and -1<=r['preimage'][1]<=4)}
    assert exterior=={(6,4),(4,6)}
    root=Path(__file__).resolve().parents[1]
    result={'passed':True,'inverse_cases':inverse_count,'protected_cases':len(protected),
            'occupied_raw_choices':4,'occupied_exclusions':1,'collector_records':len(records),
            'distinct_exterior_collector_preimages':2,'positive_fixture_validation':checks,
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'Fixed tiny generic helper/collector fixtures and genuine valid9-on5 validator input. No exterior-family positive claim, actual source read, larger-source search or production comparison.'}
    (root/'data/exterior-affine-independent-edge-fixture-preparation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
