"""Fixed saved-census audit by independent determinant/secant partition, not a search."""
from collections import Counter,defaultdict
from itertools import combinations
from math import gcd
from pathlib import Path
import hashlib
import json
import time
from research.near_quarter_packed_worker import validate_gate
from src.verify import verify_certificate,verify_certificate_bruteforce

ROOT=Path(__file__).resolve().parents[1]
REPORT='data/score11-deficiency-neighborhood-v1/report.json'
RECEIPT='data/experiments/shepherd-score11-deficiency-neighborhood-v1.json'
INPUT='data/score11-deficiency-walk-seed279157-v1/best-state.json'
INPUT_AUDIT='data/score11-deficiency-walk-seed279157-v1-independent-actual-audit.json'
PINS='data/score11-deficiency-neighborhood-source-pins.json'

def h(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def compact(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def normalized(P):return hashlib.sha256(compact({'n':79,'points':sorted(P)}).encode()).hexdigest()
def bad(a,b,c):return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
def triple(a,b,c):return tuple(sorted((a,b,c)))
def canonical_conflicts(r):return sorted(tuple(sorted(map(tuple,c['points']))) for c in r['conflicts'])


def audit():
    started=time.monotonic();r=read(REPORT);e=read(RECEIPT)
    assert h(REPORT)=='fc633b9b70a5b1801656c84beb62733152e38a5ea1a251ab1fd3a4f5c9ace183'
    assert h(RECEIPT)=='4a1111335c2bb28b2bd24b1adea35be0f9e321ea53587e3cd99d48320c611736'
    validate_gate(e['gate'],30,256)
    assert e['status']=='completed' and e['sources_unchanged'] and r['status']=='complete' and r['complete']
    pins=read(PINS)
    if 'files' in pins:pins=pins['files']
    for p,d in e['sources_before'].items():assert h(p)==d,p
    for p,d in pins.items():assert h(p)==d,p
    for p,d in r['pins'].items():assert h(p)==d,p
    assert h(INPUT)==r['input_bytes_sha256']=='3e8c8e0495f2e2cbf99815c7fbc575ccd808d0e6908091eb6f04e268f42a38f0'
    assert h(INPUT_AUDIT)=='419039ebf5828b8fef5b22a0eac29f63e4da4ff203a263aae14c30f704b4faec'
    doc=read(INPUT);P=set(map(tuple,doc['points']));ordered=sorted(P)
    assert doc['n']==79 and len(P)==len(doc['points'])==157
    assert all(type(c)is int and 0<=c<79 for p in P for c in p)
    axes=[Counter(p[i] for p in P) for i in (0,1)]
    assert all([q[i] for i in range(79)]==[2]*78+[1] for q in axes)
    assert normalized(P)==r['input_normalized_sha256']=='adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c'
    original=[t for t in combinations(ordered,3) if bad(*t)]
    assert len(original)==r['initial_score']==5
    # Independently group all fixed source points by exact unoriented direction
    # from a new cell. This enumerates every base-point pair collinear with it.
    pair_cache={}
    def secant_pairs(p):
        if p not in pair_cache:
            groups=defaultdict(list)
            for q in ordered:
                dx,dy=q[0]-p[0],q[1]-p[1];d=gcd(dx,dy);assert d
                dx//=d;dy//=d
                if dx<0 or dx==0 and dy<0:dx=-dx;dy=-dy
                groups[dx,dy].append(q)
            pairs=[(a,b) for group in groups.values() for a,b in combinations(group,2)]
            assert all(bad(p,a,b) for a,b in pairs)
            pair_cache[p]=pairs
        return pair_cache[p]
    def conflicts(removed,added):
        # Partition every possible triple by its number (0,1,2) of new cells.
        result=[t for t in original if not set(t)&removed]
        for p in added:
            result.extend(triple(p,a,b) for a,b in secant_pairs(p) if a not in removed and b not in removed)
        if len(added)==2:
            a,b=sorted(added)
            result.extend(triple(a,b,p) for p in ordered if p not in removed and bad(a,b,p))
        assert len(set(result))==len(result) and all(bad(*t) for t in result)
        return sorted(result)
    def attempts():
        for kind,axis in [('row',0),('column',1)]:
            for p in ordered:
                dest=(78,p[1]) if axis==0 else (p[0],78)
                yield kind,(p,),None if dest in P else {dest}
        for a,b in combinations(ordered,2):
            cross={(a[0],b[1]),(b[0],a[1])}
            yield 'rectangle',(a,b),None if a[0]==b[0] or a[1]==b[1] or cross&P else cross
    counts={k:Counter() for k in ('row','column','rectangle')};hist={k:Counter() for k in counts}
    seen=set();certificates=[];exits=[];catalog_hash=hashlib.sha256()
    exitdir=ROOT/'data/score11-deficiency-neighborhood-v1-independent-exits';exitdir.mkdir(exist_ok=True)
    for index,(kind,old,added) in enumerate(attempts(),1):
        counts[kind]['attempts']+=1
        catalog_hash.update((compact({'kind':kind,'removed':old,'added':sorted(added) if added is not None else None})+'\n').encode())
        if added is None:counts[kind]['illegal']+=1;continue
        removed=set(old);signature=(tuple(sorted(removed)),tuple(sorted(added)))
        assert signature not in seen;seen.add(signature)
        assert removed<=P and not added&P and len(removed)==len(added) and 1<=len(removed)<=2
        Q=(P-removed)|added
        assert len(Q)==157
        for axis in (0,1):assert sorted(Counter(p[axis] for p in Q).values())==[1]+[2]*78
        # The inverse cell difference returns P exactly; actual inverse legality
        # follows from the independently checked endpoints/capacity catalog.
        assert (Q-added)|removed==P
        T=conflicts(removed,added);score=len(T)
        assert score>=6
        for t in T[:6]:assert len(set(t))==3 and set(t)<=Q and bad(*t)
        certificates.append({'catalog_index':index,'kind':kind,'removed':old,'added':sorted(added),'six_collinear_triples':T[:6]})
        counts[kind]['legal']+=1;hist[kind][score-5]+=1
        if score==6:
            cert={'n':79,'points':[list(p) for p in sorted(Q)]}
            checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
            assert all(not c['valid'] and not c['errors'] and c['point_count']==157 and c['conflict_count']==6 for c in checks)
            assert canonical_conflicts(checks[0])==canonical_conflicts(checks[1])==T
            assert checks[0]['normalized_sha256']==checks[1]['normalized_sha256']==normalized(Q)
            cert['metadata']={'method':'independent_fixed_neighborhood_exit_audit','valid':False,'exact_conflict_count':6,'delta':1,'catalog_index':index,'kind':kind,'removed':old,'added':sorted(added),'input_normalized_sha256':normalized(P),'normalized_sha256':normalized(Q),'novelty_claim':False}
            cert['validators']=checks
            path=exitdir/('exit-'+str(index)+'-'+kind+'.json');path.write_text(json.dumps(cert,sort_keys=True,indent=2)+'\n')
            exits.append({**cert['metadata'],'path':str(path.relative_to(ROOT)),'sha256':h(path)})
    assert len(certificates)==12247 and len(exits)==3
    for kind,total,legal,illegal in [('row',157,155,2),('column',157,155,2),('rectangle',12246,11937,309)]:
        expected=r['classes'][kind];assert counts[kind]=={'attempts':total,'legal':legal,'illegal':illegal}
        assert expected['started']==expected['completed']==total and expected['legal']==legal and expected['illegal']==illegal
        assert dict(hist[kind])=={int(k):v for k,v in expected['deltas'].items()}
        assert expected['improving']==expected['neutral']==0 and expected['worsening']==legal
    assert r['best_score'] is None and r['best_normalized_sha256'] is None
    assert not (ROOT/'data/score11-deficiency-neighborhood-v1/best-state.json').exists()
    certificate={'schema':'fixed_deficiency_neighborhood_six_triples_v1','input_sha256':h(INPUT),'input_normalized_sha256':normalized(P),'source_score':5,'catalog_order':'row lex cells, column lex cells, rectangle lex unordered pairs','catalog_sha256':catalog_hash.hexdigest(),'legal_neighbors':12247,'minimum_neighbor_score_lower_bound':6,'neighbors':certificates}
    cp='data/score11-deficiency-neighborhood-v1-independent-local-minimum-certificate.json';(ROOT/cp).write_text(compact(certificate)+'\n')
    mp='data/score11-deficiency-neighborhood-v1-independent-plus1-exit-manifest.json'
    manifest={'schema':'fixed_deficiency_plus_one_exits_v1','accepted':True,'input_sha256':h(INPUT),'input_normalized_sha256':normalized(P),'input_exact_score':5,'census_report_sha256':h(REPORT),'local_minimum_certificate_sha256':h(cp),'exact_exit_score':6,'complete_exit_count':3,'exits':exits,'scope':'Exactly the three score6 neighbors in this fixed one-step catalog; no second neighborhood searched.'}
    (ROOT/mp).write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    result={'plus_one_exit_manifest':{'path':mp,'sha256':h(mp)},'accepted':True,'complete':True,'decision':'independently certify this exact input is a strict local minimum under the three specified one-step moves; entire histogram independently reproduced','input_sha256':{p:h(p) for p in (REPORT,RECEIPT,INPUT,INPUT_AUDIT,PINS)},'source_pins_verified':len(pins),'receipt_source_pins_verified':len(e['sources_before']),'independent_source_points':157,'independent_source_score':5,'independent_catalog_attempts':12560,'independent_legal_neighbors':12247,'independent_classes':{k:{**counts[k],'deltas':dict(sorted(hist[k].items()))} for k in counts},'independent_catalog_sha256':catalog_hash.hexdigest(),'certificate':{'path':cp,'sha256':h(cp),'bytes':(ROOT/cp).stat().st_size,'neighbors_with_six_explicit_determinant_triples':len(certificates)},'exact_delta_plus_one_exits':exits,'independent_minimum_neighbor_score':6,'independent_new_cells_with_secant_cache':len(pair_cache),'full_histogram_independently_reproduced':True,'method':'Independent move catalog and exact triple partition by0/1/2new cells; source triples by full determinants, secant pairs by independent primitive directions and determinant checks; six explicit integer triples verified per legal neighbor. Only the three exact score6 exits receive both full production validators. No production move, delta, or census scorer is called.','gate':e['gate'],'solver_replayed':False,'search_performed':False,'scope':'One fixed157-point score5 input and exactly the specified12560 one-step attempts only. Strict local minimum and three score6 exits; no component closure, multi-step obstruction, optimality, global bound or nonexistence result.','audit_source_sha256':h(Path(__file__)),'elapsed_seconds':time.monotonic()-started}
    ap='data/score11-deficiency-neighborhood-v1-independent-actual-audit.json';(ROOT/ap).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('gate','independent_classes')},sort_keys=True));print('audit_sha256',h(ap))


if __name__=='__main__':audit()
