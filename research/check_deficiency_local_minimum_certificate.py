"""Check the saved six-triples-per-neighbor certificate with integers only."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/score11-deficiency-walk-seed279157-v1/best-state.json'
CERT=ROOT/'data/score11-deficiency-neighborhood-v1-independent-local-minimum-certificate.json'
def bad(a,b,c):return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
def check():
    cert=json.loads(CERT.read_text());P=set(map(tuple,json.loads(SOURCE.read_text())['points']));ordered=sorted(P)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==cert['input_sha256']
    assert all(type(c) is int and 0<=c<79 for p in P for c in p)
    assert len(P)==157 and all([Counter(p[a] for p in P)[i] for i in range(79)]==[2]*78+[1] for a in (0,1))
    assert sum(bad(*t) for t in combinations(ordered,3))==5
    def catalog():
        for kind in ('row','column'):
            for p in ordered:
                q=(78,p[1]) if kind=='row' else (p[0],78)
                yield kind,(p,),None if q in P else {q}
        for a,b in combinations(ordered,2):
            A={(a[0],b[1]),(b[0],a[1])}
            yield 'rectangle',(a,b),None if a[0]==b[0] or a[1]==b[1] or A&P else A
    records=iter(cert['neighbors']);legal=0
    for index,(kind,old,added) in enumerate(catalog(),1):
        if added is None:continue
        row=next(records);Q=(P-set(old))|added
        assert row['catalog_index']==index and row['kind']==kind
        assert set(map(tuple,row['removed']))==set(old) and set(map(tuple,row['added']))==added
        witnesses=[tuple(sorted(map(tuple,t))) for t in row['six_collinear_triples']]
        assert len(witnesses)==len(set(witnesses))==6
        assert all(len(t)==len(set(t))==3 and set(t)<=Q and bad(*t) for t in witnesses)
        legal+=1
    assert next(records,None) is None and index==12560 and legal==cert['legal_neighbors']==12247
    return {'accepted':True,'catalog_attempts':index,'legal_neighbors_with_six_determinant_witnesses':legal,'source_score':5,'neighbor_score_lower_bound':6,'certificate_sha256':hashlib.sha256(CERT.read_bytes()).hexdigest(),'scope':'Only the fixed one-step catalog; no neighbor full scores or global conclusion checked.'}
if __name__=='__main__':print(json.dumps(check(),sort_keys=True))
