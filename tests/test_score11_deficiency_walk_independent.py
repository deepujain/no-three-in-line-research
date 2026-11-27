"""Independent tiny review: direct determinant scoring, every n2..4 degree pattern."""
from collections import Counter
from copy import deepcopy
from itertools import combinations, product
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from research import score11_deficiency_walk as m
from research.deficiency_move_tiny_oracle import deficiency, triples


class IndependentDeficiencyTests(unittest.TestCase):
    def source(self):
        return {(x,y) for x in range(4) for y in range(4) if x==y or x+y==3}

    def test_every_tiny_deficient_state_and_move(self):
        counts=Counter()
        for n in (2,3,4):
            for chosen in combinations(product(range(n),repeat=2),2*n-1):
                P=set(chosen)
                if any(max(Counter(p[a] for p in P).values())>2 for a in (0,1)):continue
                d=deficiency(P,n);score=len(triples(P));old=frozenset(P);counts['states']+=1
                for axis,name in enumerate(('row','column')):
                    for point in sorted(P):
                        dest=tuple(d[axis] if i==axis else point[i] for i in (0,1))
                        legal=point[axis]!=d[axis] and dest not in P
                        proposal=m.relocation(P,n,point,name)
                        self.assertEqual(frozenset(P),old);self.assertEqual(proposal is not None,legal)
                        if legal:
                            delta,Q=proposal;self.assertEqual(Q,(P-{point})|{dest})
                            self.assertEqual(delta,len(triples(Q))-score)
                            nd=deficiency(Q,n);self.assertEqual(nd[axis],point[axis]);self.assertEqual(nd[1-axis],d[1-axis])
                            self.assertEqual(m.relocation(Q,n,dest,name),(-delta,P));counts['relocations']+=1
                for first,second in combinations(sorted(P),2):
                    cross={(first[0],second[1]),(second[0],first[1])}
                    legal=first[0]!=second[0] and first[1]!=second[1] and not cross&P
                    proposal=m.rectangle(P,n,first,second)
                    self.assertEqual(frozenset(P),old);self.assertEqual(proposal is not None,legal)
                    if legal:
                        delta,Q=proposal;self.assertEqual(Q,(P-{first,second})|cross)
                        self.assertEqual(delta,len(triples(Q))-score);self.assertEqual(deficiency(Q,n),d)
                        self.assertEqual(m.rectangle(Q,n,*sorted(cross)),(-delta,P));counts['rectangles']+=1
        self.assertEqual(counts,{'states':865,'relocations':8648,'rectangles':8496})

    def test_nonzero_seeded_prefix_and_each_saved_incumbent(self):
        S=self.source();before=frozenset(S);self.assertEqual(len(triples(S)),8)
        saved=[];atomic=m.atomic
        def capture(path,value):saved.append(deepcopy(value));atomic(path,value)
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'atomic',capture):
            report=m.walk(4,S,8,Path(tmp)/'best',seed=279157,max_proposals=50,clock=lambda:0)
            final=json.loads((Path(tmp)/'best').read_text())
        self.assertEqual(frozenset(S),before)
        self.assertEqual((report['attempted'],report['legal'],report['accepted']),(17,11,9))
        self.assertEqual(report['moves'],{'row':{'attempted':3,'legal':3,'accepted':2},'column':{'attempted':4,'legal':4,'accepted':4},'rectangle':{'attempted':10,'legal':4,'accepted':3}})
        self.assertEqual(report['removed'],[0,0]);self.assertEqual(report['status'],'witness')
        scores=[len(triples(set(map(tuple,d['points'])))) for d in saved]
        self.assertEqual(scores[0],5);self.assertEqual(scores[-1],0)
        self.assertEqual(scores,sorted(set(scores),reverse=True))
        self.assertTrue(any(0<s<5 for s in scores))
        for doc,score in zip(saved,scores):
            self.assertEqual(doc['metadata']['exact_conflict_count'],score)
            self.assertEqual(doc['metadata']['valid'],score==0)
            self.assertEqual(len(doc['validators']),2);deficiency(set(map(tuple,doc['points'])),4)
        self.assertEqual(final['metadata']['normalized_sha256'],report['best_normalized_sha256'])

    def test_invalid_initial_and_cap_are_persisted(self):
        S=self.source()
        with tempfile.TemporaryDirectory() as tmp:
            report=m.walk(4,S,8,Path(tmp)/'best',max_proposals=0,clock=lambda:0)
            doc=json.loads((Path(tmp)/'best').read_text())
        self.assertEqual(report['status'],'proposal_cap');self.assertEqual(report['attempted'],0)
        self.assertEqual(report['best_score'],5);self.assertFalse(doc['metadata']['valid'])
        self.assertEqual(len(triples(set(map(tuple,doc['points'])))),5)

    def test_failed_improvement_preserves_only_validated_best(self):
        S=self.source();real=m.audit_save
        def fail(points,n,score,*args,**kwargs):
            if score<5:raise RuntimeError('synthetic validator disagreement')
            return real(points,n,score,*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'audit_save',fail):
            report=m.walk(4,S,8,Path(tmp)/'best',max_proposals=50,clock=lambda:0)
            doc=json.loads((Path(tmp)/'best').read_text())
        self.assertEqual(report['status'],'error');self.assertEqual(report['best_score'],5)
        self.assertEqual(doc['metadata']['exact_conflict_count'],5)

    def test_equal_count_conflict_mismatch_is_rejected(self):
        S=self.source();P,_,score=m.initialize(S,4,8);real=m.verify_certificate_bruteforce
        def changed(cert):
            r=real(cert);r['conflicts'][0]['points'][0]=[99,99];return r
        with patch.object(m,'verify_certificate_bruteforce',changed),self.assertRaisesRegex(RuntimeError,'disagreement'):
            m.dual_audit(P,4,score,1,lambda:0)

    def test_walk_preserves_late_verified_witness(self):
        S=self.source();now=[0];real=m.verify_certificate_bruteforce
        def late(cert):
            r=real(cert)
            if r['point_count']==7 and r['valid']:now[0]=26
            return r
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate_bruteforce',late):
            r=m.walk(4,S,8,Path(tmp)/'best',max_proposals=50,clock=lambda:now[0])
            self.assertTrue(json.loads((Path(tmp)/'best').read_text())['metadata']['valid'])
        self.assertEqual(r['status'],'witness');self.assertEqual(r['best_score'],0)

    def test_input_domain_and_membership_rejections_do_not_mutate(self):
        P,_,_=m.initialize(self.source(),4,8);old=frozenset(P)
        with self.assertRaises(ValueError):m.relocation(P,4,(-1,0),'row')
        with self.assertRaises(ValueError):m.rectangle(P,4,next(iter(P)),(4,4))
        with self.assertRaises(ValueError):m.rectangle(P,4,next(iter(P)),next(iter(P)))
        for bad in ({(0,0),(1,1)}, {(True,0)}|P):
            with self.assertRaises(ValueError):m.axes(bad,4)
        self.assertEqual(frozenset(P),old)


if __name__=='__main__':unittest.main()
