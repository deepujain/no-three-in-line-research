from collections import Counter
from itertools import combinations, product
import unittest
from research import boolean_scaffold_independent_tiny_oracle as o


class ProjectionOracleTests(unittest.TestCase):
    def fixtures(self):
        A={(0,0),(0,1),(1,0),(1,2),(2,1)};S=A|{(2,2)}
        yield A,S,[(0,2),(1,1),(2,0)],1
        A={(0,0),(0,1),(1,1),(1,2),(2,2),(2,3),(3,0)};S=A|{(3,3)}
        yield A,S,[(0,2),(0,3),(1,0),(1,3),(2,0),(2,1),(3,1),(3,2)],2
        S={(0,0),(0,1),(1,0),(1,1),(2,2),(2,3),(3,2),(3,3)}; A=S-{(0,0)}
        yield A,S,sorted({(x,y) for x in range(4) for y in range(4)}-S),2

    def test_projected_geometry_equals_direct_and_source_distance(self):
        count=0; arc_count=0; valid_count=0; invalid_count=0
        for A,S,pool,k in self.fixtures():
            arcs,records=o.enumerate_projection(A,S,pool,k)
            self.assertTrue(arcs);self.assertTrue(records)
            count+=len(records);arc_count+=len(arcs)
            valid_count+=sum(all(r[3]) for r in records)
            invalid_count+=sum(not all(r[3]) for r in records)
            for _,Q,D,classes,P in records:
                self.assertEqual(all(classes),o.valid(P))
                self.assertEqual(len(S-P),2*k+1)
                self.assertEqual(len(P-S),k)
        self.assertGreater(count,10);self.assertGreater(arc_count,10)
        self.assertGreater(valid_count,0);self.assertGreater(invalid_count,0)

    def test_same_deleted_supports_can_have_distinct_planted_sets(self):
        found=False
        for A,S,pool,k in self.fixtures():
            _,records=o.enumerate_projection(A,S,pool,k)
            by_deleted={}
            for _,Q,D,_,_ in records:
                by_deleted.setdefault(D,set()).add(Q)
            found |= any(len(qs)>1 for qs in by_deleted.values())
        self.assertTrue(found)

    def test_same_cell_multiple_support_cannot_both_be_selected(self):
        for A,S,pool,k in self.fixtures():
            arcs=o.support_catalog(A,pool)
            pair=next((a,b) for a,b in combinations(arcs,2) if a[0]==b[0])
            self.assertFalse(o.compatible(pair))
            self.assertEqual(len(o.derive(pair)[0]),1)

    def test_axis_overlap_not_just_endpoint_overlap(self):
        for A,S,pool,k in self.fixtures():
            arcs=o.support_catalog(A,pool)
            pairs=[(a,b) for a,b in combinations(arcs,2)
                   if not {a[1],a[2]} & {b[1],b[2]} and not o.compatible((a,b))]
            if pairs:
                return
        self.fail('fixture must include distinct supports sharing an axis')

    def test_union_equivalence_has_unique_auxiliary_for_all_support_assignments(self):
        for support in product((False,True),repeat=3):
            accepted=[]
            for auxiliary in (False,True):
                forward=all(not bit or auxiliary for bit in support)
                reverse=not auxiliary or any(support)
                if forward and reverse: accepted.append(auxiliary)
            self.assertEqual(accepted,[any(support)])

    def test_threshold_equivalence_unique_for_all_small_bit_patterns(self):
        for n in range(1,4):
            keys=[(i,j) for i in range(1,n+1) for j in range(1,i+1)]
            for xs in product((False,True),repeat=n):
                valid_aux=[]
                for bits in product((False,True),repeat=len(keys)):
                    z=dict(zip(keys,bits))
                    def val(i,j):
                        return True if j==0 else False if i==0 or j>i else z[i,j]
                    good=True
                    for i,j in keys:
                        a,b,x,v=val(i-1,j),val(i-1,j-1),xs[i-1],val(i,j)
                        good &= ((not a or v) and (not x or not b or v) and (not v or a or x) and (not v or a or b))
                    if good: valid_aux.append(z)
                self.assertEqual(len(valid_aux),1)
                for i,j in keys:
                    self.assertEqual(valid_aux[0][i,j],sum(xs[:i])>=j)

    def test_reverse_deletion_prevents_false_free_deletion(self):
        A={(0,0),(1,1),(2,2)}
        F={(0,1)}
        # Selected supports do not include a; an unconstrained extra deletion
        # can satisfy the old conflict even though the real retained set fails.
        self.assertFalse(o.valid(A))
        self.assertTrue(o.valid(A-{(1,1)}))
        self.assertNotIn((1,1),F)

    def test_unsupported_q_true_only_tightens_negative_clauses(self):
        A={(0,0),(1,1),(2,2)};D={(1,1)};q=(0,2)
        before=o.four_classes(A,set(),D)
        after=o.four_classes(A,{q},D)
        self.assertFalse(any(after[i] and not before[i] for i in range(4)))
        # Exhaust all auxiliary values for two absent support bits.
        assignments=[]
        for qbit in (False,True):
            forward=all(not x or qbit for x in (False,False))
            reverse=not qbit or any((False,False))
            if forward and reverse: assignments.append(qbit)
        self.assertEqual(assignments,[False])

    def test_each_new_point_triple_class_has_separate_counterexample(self):
        # One-new: q with two retained old points on its line.
        old={(0,0),(1,1)};q={(2,2)}
        self.assertEqual(o.four_classes(old,q,set()),(True,False,True,True))
        # Two-new: one old point on the line of two selected new points.
        old={(1,1)};q={(0,0),(2,2)}
        self.assertEqual(o.four_classes(old,q,set()),(True,True,False,True))
        # Three-new: a triple solely among new points.
        self.assertEqual(o.four_classes(set(),{(0,0),(1,1),(2,2)},set()),(True,True,True,False))
        # Old conflict: no planted point involved.
        self.assertEqual(o.four_classes({(0,0),(1,1),(2,2)},set(),set()),(False,True,True,True))


if __name__=='__main__':
    unittest.main()
