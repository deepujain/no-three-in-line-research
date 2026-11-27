"""Independent determinant census/prefix oracles; tiny boards only."""
from collections import Counter
from copy import deepcopy
from itertools import combinations,product
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from research import score11_deficiency_neighborhood as m
from research.deficiency_move_tiny_oracle import deficiency,triples


def catalog(P,n):
    r,c=deficiency(P,n);ordered=sorted(P)
    for kind,axis,d in [('row',0,r),('column',1,c)]:
        for p in ordered:
            q=(d,p[1]) if axis==0 else (p[0],d)
            yield kind,(p,),None if q in P else (P-{p})|{q}
    for a,b in combinations(ordered,2):
        crossed={(a[0],b[1]),(b[0],a[1])}
        legal=a[0]!=b[0] and a[1]!=b[1] and not crossed&P
        yield 'rectangle',(a,b),(P-{a,b})|crossed if legal else None


class IndependentCensusTests(unittest.TestCase):
    def test_every_tiny_catalog_determinant_histogram_prefix_and_duplicates(self):
        states=completed=witnesses=0
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'best'
            for n in (2,3,4):
                for chosen in combinations(product(range(n),repeat=2),2*n-1):
                    P=set(chosen)
                    if any(max(Counter(p[i] for p in P).values())>2 for i in (0,1)):continue
                    states+=1;score=len(triples(P));best=score;expected={k:Counter() for k in ('row','column','rectangle')};hist={k:Counter() for k in expected};seen=set()
                    records=list(catalog(P,n))
                    for kind,old,Q in records:
                        if Q is not None:
                            self.assertNotIn(frozenset(Q),seen);seen.add(frozenset(Q))
                    wanted='complete'
                    for kind,old,Q in records:
                        e=expected[kind];e['started']+=1;e['completed']+=1
                        if Q is None:e['illegal']+=1;continue
                        e['legal']+=1;delta=len(triples(Q))-score;hist[kind][delta]+=1
                        if score+delta<best:
                            best=score+delta
                            if best==0:wanted='witness';break
                    before=frozenset(P);result=m.census(n,P,score,path,clock=lambda:0)
                    self.assertEqual(frozenset(P),before);self.assertEqual(result['status'],wanted)
                    if wanted=='complete':completed+=1;self.assertTrue(result['complete'])
                    else:witnesses+=1;self.assertFalse(result['complete'])
                    for kind in expected:
                        row=result['classes'][kind]
                        for key in ('started','completed','legal','illegal'):self.assertEqual(row[key],expected[kind][key])
                        self.assertEqual(row['deltas'],dict(hist[kind]));self.assertEqual(row['legal'],sum(hist[kind].values()))
                        self.assertEqual(row['improving'],sum(v for d,v in hist[kind].items() if d<0))
                        self.assertEqual(row['neutral'],hist[kind][0]);self.assertEqual(row['worsening'],sum(v for d,v in hist[kind].items() if d>0))
                    self.assertEqual(result['best_score'],best if best<score else None)
                    if best<score:
                        doc=json.loads(path.read_text());self.assertEqual(len(triples(set(map(tuple,doc['points'])))),best)
                        self.assertEqual(doc['metadata']['exact_conflict_count'],best);self.assertEqual(len(doc['validators']),2)
                        path.unlink()
                    else:self.assertFalse(path.exists())
        self.assertEqual(states,865);self.assertEqual(completed+witnesses,865)

    def test_deadline_before_each_class_and_during_inverse(self):
        P={(0,0),(0,1),(1,0)};attempts=m.attempts
        for target in ('row','column','rectangle'):
            now=[0]
            def until(points):
                for kind,old in attempts(points):
                    if kind==target:now[0]=26
                    yield kind,old
            with tempfile.TemporaryDirectory() as tmp,patch.object(m,'attempts',until):
                r=m.census(2,P,0,Path(tmp)/'best',clock=lambda:now[0])
            self.assertEqual(r['status'],'timeout');self.assertFalse(r['complete']);self.assertEqual(r['classes'][target]['started'],0)
        real=m.base.relocation
        def inverse_timeout(points,n,p,axis):
            if points!=P:raise TimeoutError('during inverse')
            return real(points,n,p,axis)
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.base,'relocation',inverse_timeout):
            r=m.census(2,P,0,Path(tmp)/'best',clock=lambda:0)
        row=r['classes']['row'];self.assertEqual((row['started'],row['completed'],row['legal'],row['illegal']),(2,1,0,1));self.assertEqual(row['deltas'],{});self.assertEqual(r['status'],'timeout')

    def test_late_valid_witness_saved_and_failure_not_promoted(self):
        P={(0,0),(0,1),(1,0),(1,1),(2,2)};now=[0];real=m.base.verify_certificate_bruteforce
        def late(cert):
            r=real(cert)
            if r['valid']:now[0]=26
            return r
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.base,'verify_certificate_bruteforce',late):
            r=m.census(3,P,len(triples(P)),Path(tmp)/'best',clock=lambda:now[0]);saved=json.loads((Path(tmp)/'best').read_text())
        self.assertEqual(r['status'],'witness');self.assertFalse(r['complete']);self.assertTrue(saved['metadata']['valid'])
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.base,'audit_save',side_effect=RuntimeError('validator disagreement')):
            r=m.census(3,P,len(triples(P)),Path(tmp)/'best',clock=lambda:0)
            self.assertFalse((Path(tmp)/'best').exists())
        self.assertEqual(r['status'],'error');self.assertIsNone(r['best_score']);self.assertFalse(r['complete'])

    def test_missing_or_changed_pins_fail_closed_without_touching_best(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input';p.write_bytes(b'original');best=Path(tmp)/'best';best.write_bytes(b'saved validated state')
            pins={p:hashlib.sha256(p.read_bytes()).hexdigest()}
            for remove in (False,True):
                if remove:p.unlink()
                else:p.write_bytes(b'changed')
                r=m.finalize_identity({'status':'complete','complete':True},pins)
                self.assertEqual(r['status'],'error');self.assertFalse(r['complete']);self.assertEqual(best.read_bytes(),b'saved validated state')


if __name__=='__main__':unittest.main()
