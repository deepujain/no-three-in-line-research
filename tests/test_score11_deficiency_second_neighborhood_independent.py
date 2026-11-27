"""Independent tiny determinant/global-dedup/prefix oracle for three parents."""
from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from research import score11_deficiency_second_neighborhood as m
from research.deficiency_move_tiny_oracle import triples
from tests.test_score11_deficiency_neighborhood_independent import catalog
from src.verify import normalized_sha256


def score(P):return len(triples(P))
def parents_for(P,n):
    result=[];s=score(P)
    for kind,old,Q in catalog(P,n):
        if Q is not None and score(Q)==s+1:
            result.append((Q,s+1,normalized_sha256(n,Q),kind,old))
            if len(result)==3:return result
    return None

def initial_fixture():return {(0,0),(0,1),(1,0),(1,2),(2,2)}


class IndependentSecondTests(unittest.TestCase):
    def run_tiny(self,P,parents,n=3,**kw):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'best';r=m.second_census(n,P,score(P),parents,path,**kw)
            saved=json.loads(path.read_text()) if path.exists() else None
        return r,saved

    def check_conservation(self,r):
        C=sum(c['completed'] for p in r['parents'] for c in p['classes'].values())
        L=sum(c['legal'] for p in r['parents'] for c in p['classes'].values())
        I=sum(c['illegal'] for p in r['parents'] for c in p['classes'].values())
        self.assertEqual(C,L+I);self.assertEqual(L,r['novel_first_insertions']+r['preexisting_occurrences'])
        self.assertEqual(sum(r['novel_histogram'].values()),r['novel_first_insertions'])
        if r['preseed_complete']:self.assertEqual(r['map_size'],4+r['novel_first_insertions'])
        for p in r['parents']:
            for c in p['classes'].values():
                self.assertLessEqual(c['completed'],c['started']);self.assertEqual(c['completed'],c['legal']+c['illegal']);self.assertEqual(c['legal'],sum(c['deltas'].values()))

    def test_complete_independent_catalog_map_and_first_parent(self):
        P=initial_fixture();parents=parents_for(P,3);self.assertEqual(len(parents),3)
        seeded={frozenset(P)}|{frozenset(p[0]) for p in parents};entry={q:[score(set(q)),set()] for q in seeded}
        expected={k:0 for k in ('novel_first_insertions','preexisting_occurrences','backtrack_occurrences','exit_occurrences','same_parent_repeats','cross_parent_revisits')}
        novel=Counter();unique=Counter();classes=[]
        for index,(Q,s,_,_,_) in enumerate(parents):
            rows={k:Counter() for k in ('row','column','rectangle')};hist={k:Counter() for k in rows}
            for kind,old,R in catalog(Q,3):
                c=rows[kind];c['started']+=1;c['completed']+=1
                if R is None:c['illegal']+=1;continue
                key=frozenset(R);value=score(R);c['legal']+=1;hist[kind][value-s]+=1
                if key not in entry:
                    entry[key]=[value,set()];expected['novel_first_insertions']+=1;novel[value]+=1
                else:expected['preexisting_occurrences']+=1
                stored,seen=entry[key];self.assertEqual(stored,value);self.assertNotIn(index,seen)
                if seen:expected['cross_parent_revisits']+=1
                else:unique[value]+=1
                seen.add(index)
                if key==frozenset(P):expected['backtrack_occurrences']+=1
                if key in seeded-{frozenset(P)}:expected['exit_occurrences']+=1
            classes.append((rows,hist))
        before=deepcopy((P,parents));r,saved=self.run_tiny(P,parents,clock=lambda:0)
        self.assertEqual((P,parents),before);self.assertEqual(r['status'],'complete');self.assertIsNone(saved)
        for k,v in expected.items():self.assertEqual(r[k],v)
        self.assertEqual(r['map_size'],len(entry));self.assertEqual(r['novel_histogram'],dict(novel));self.assertEqual(r['generated_unique_histogram'],dict(unique))
        for parent,(rows,hist) in zip(r['parents'],classes):
            for kind,c in parent['classes'].items():
                for k in ('started','completed','legal','illegal'):self.assertEqual(c[k],rows[kind][k])
                self.assertEqual(c['deltas'],dict(hist[kind]))
        self.assertGreater(r['cross_parent_revisits'],0);self.assertEqual(r['backtrack_occurrences'],3);self.check_conservation(r)

    def test_bitkey_injective_all_n3_subsets(self):
        cells=list(product(range(3),repeat=2));keys=set()
        for bits in product((0,1),repeat=9):
            P={p for p,b in zip(cells,bits) if b};key=m.bitkey(P,3)
            self.assertEqual(key,sum(1<<(3*x+y) for x,y in P));self.assertNotIn(key,keys);keys.add(key)
        self.assertEqual(len(keys),512)

    def test_duplicate_scores_and_impossible_same_parent_repeat_fail_with_clean_prefix(self):
        P=initial_fixture();parents=parents_for(P,3);first=parents[0][0];real=m.base.relocation;attempts=m.one.attempts;ready=[False]
        def start(Q):ready[0]=True;yield from attempts(Q)
        def wrong(Q,n,p,axis):
            result=real(Q,n,p,axis)
            if ready[0] and result is not None:
                delta,R=result
                if Q==first and R==P:return delta+1,R
                if Q==P and R==first:return delta-1,R
            return result
        with patch.object(m.one,'attempts',start),patch.object(m.base,'relocation',wrong):r,_=self.run_tiny(P,parents,clock=lambda:0)
        self.assertEqual(r['status'],'error');self.assertIn('duplicate score',r['error']);self.check_conservation(r)
        def repeated(Q):
            chosen=next((kind,old) for kind,old,R in catalog(Q,3) if R is not None)
            yield chosen;yield chosen
        with patch.object(m.one,'attempts',repeated):r,_=self.run_tiny(P,parents,clock=lambda:0)
        self.assertEqual(r['status'],'error');self.assertEqual(r['same_parent_repeats'],1);self.check_conservation(r)

    def test_partial_parent_setup_and_enumeration_deadlines(self):
        P=initial_fixture();parents=parents_for(P,3);real=m.base.dual_audit;calls=[0]
        def setup(*args,**kw):
            calls[0]+=1
            if calls[0]==3:raise TimeoutError('parent setup')
            return real(*args,**kw)
        with patch.object(m.base,'dual_audit',setup):r,_=self.run_tiny(P,parents,clock=lambda:0)
        self.assertEqual(r['status'],'timeout');self.assertFalse(r['preseed_complete']);self.assertEqual(r['map_size'],2);self.check_conservation(r)
        for stop_parent in (0,1,2):
            calls=[-1];now=[0];attempts=m.one.attempts
            def until(Q):
                calls[0]+=1
                if calls[0]==stop_parent:now[0]=26
                yield from attempts(Q)
            with patch.object(m.one,'attempts',until):r,_=self.run_tiny(P,parents,clock=lambda:now[0])
            self.assertEqual(r['status'],'timeout');self.assertTrue(r['preseed_complete']);self.assertEqual(sum(c['started'] for c in r['parents'][stop_parent]['classes'].values()),0);self.check_conservation(r)

    def test_corrupt_or_duplicate_parents_rejected(self):
        P=initial_fixture();parents=parents_for(P,3)
        for mutation in ('digest','score','duplicate','move'):
            ps=deepcopy(parents);v=list(ps[1])
            if mutation=='digest':v[2]='bad'
            elif mutation=='score':v[1]=2
            elif mutation=='move':v[4]=((-1,-1),)
            if mutation=='duplicate':ps[1]=ps[0]
            else:ps[1]=tuple(v)
            r,saved=self.run_tiny(P,ps,clock=lambda:0)
            self.assertEqual(r['status'],'error');self.assertFalse(r['complete']);self.assertIsNone(saved)

    def test_late_witness_and_failed_candidate_audit(self):
        fixture=None
        for chosen in combinations(product(range(4),repeat=2),7):
            P=set(chosen)
            if any(max(Counter(p[i] for p in P).values())>2 for i in (0,1)) or score(P)!=1:continue
            parents=parents_for(P,4)
            if parents is not None and any(R is not None and score(R)==0 for Q,*_ in parents for _,_,R in catalog(Q,4)):
                fixture=(P,parents);break
        self.assertIsNotNone(fixture);P,parents=fixture;real=m.base.verify_certificate_bruteforce;now=[0]
        def late(cert):
            r=real(cert)
            if r['valid']:now[0]=26
            return r
        with patch.object(m.base,'verify_certificate_bruteforce',late):r,saved=self.run_tiny(P,parents,n=4,clock=lambda:now[0])
        self.assertEqual(r['status'],'witness');self.assertFalse(r['complete']);self.assertEqual(r['best_score'],0);self.assertTrue(saved['metadata']['valid']);self.check_conservation(r)
        expected=next((i,kind,old) for i,(Q,*_) in enumerate(parents) for kind,old,R in catalog(Q,4) if R is not None and score(R)==0)
        self.assertEqual((saved['metadata']['parent_index'],saved['metadata']['move_kind'],tuple(map(tuple,saved['metadata']['removed']))),expected)
        with patch.object(m.base,'audit_save',side_effect=TimeoutError('before second validator')):r,saved=self.run_tiny(P,parents,n=4,clock=lambda:0)
        self.assertEqual(r['status'],'timeout');self.assertIsNone(r['best_score']);self.assertIsNone(saved);self.check_conservation(r)


if __name__=='__main__':unittest.main()
