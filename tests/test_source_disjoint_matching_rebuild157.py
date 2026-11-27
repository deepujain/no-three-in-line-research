from collections import Counter
from copy import deepcopy
from itertools import combinations,permutations,product
from pathlib import Path
import hashlib,json,tempfile
import unittest
from unittest.mock import patch
from research import source_disjoint_matching_rebuild157 as m


def bad(a,b,c):return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
def valid(P):return not any(bad(*t) for t in combinations(sorted(P),3))
def pointset(perm):return set(enumerate(perm))
def fixture():return 3,((0,0),(1,1)),{(0,0),(1,1)}
def report():return {'complete':False,'root_mask_complete':False,'root_domains_complete':False,'root_matching_complete':False,'diagnostic156':None,'witness157':None,'counters':m.new_counters()}


class PropagationTests(unittest.TestCase):
    def test_all_tiny_primitive_lines_equal_determinants(self):
        for n in range(2,6):
            board=list(product(range(n),repeat=2))
            for a,b in combinations(board,2):
                actual=list(m.line_cells(n,a,b));expected={p for p in board if bad(a,b,p)}
                self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(set(actual)));self.assertLessEqual(len(actual),n)
                self.assertEqual(list(m.line_cells(n,b,a)),actual)
        with self.assertRaises(ValueError):list(m.line_cells(3,(0,0),(0,0)))

    def test_all_tiny_degree_two_cycle_colorings(self):
        for n in (2,3,4):
            boards={frozenset(pointset(a)|pointset(b)) for a in permutations(range(n)) for b in permutations(range(n)) if all(x!=y for x,y in zip(a,b))}
            for B in boards:
                # Independent edge-component discovery, then exhaustive perfect matchings.
                todo=set(B);components=[]
                while todo:
                    comp={min(todo)};changed=True
                    while changed:
                        following={p for p in B if any(p[0]==q[0] or p[1]==q[1] for q in comp)}
                        changed=following!=comp;comp=following
                    todo-=comp;components.append(comp)
                candidates=[pointset(p) for p in permutations(range(n)) if pointset(p)<=B and all(min(comp) in pointset(p) for comp in components)]
                self.assertEqual(len(candidates),1)
                R,parts=m.deterministic_matching(B,n);self.assertEqual(set(R),candidates[0]);self.assertEqual(sum(p['edges'] for p in parts),2*n)

    def test_tiny_root_masks_domains_and_source_exclusion(self):
        for n in (3,4):
            for perm in permutations(range(n-1)):
                R=tuple(sorted(pointset(perm)))
                if not valid(R):continue
                forbidden=set(R)|{(n-1,0),(0,n-1)};c=m.new_counters();mask,domains=m.root_domains(n,R,forbidden,c,lambda:None)
                for p in product(range(n),repeat=2):
                    unsafe=any(bad(a,b,p) for a,b in combinations(R,2))
                    self.assertEqual(bool(mask>>(n*p[0]+p[1])&1),unsafe)
                    self.assertEqual(bool(domains[p[0]]>>p[1]&1),p not in forbidden and not unsafe)
                self.assertEqual(c['root_domain_cells_completed'],n*n);self.assertEqual(c['root_lines_completed'],(n-1)*(n-2)//2)
                self.assertLessEqual(c['root_cell_visits_completed'],n*c['root_lines_completed'])

    def test_timeout_during_root_line_leaves_partial_counters(self):
        c=m.new_counters()
        def check():
            if c['root_cell_visits_started']==2:raise TimeoutError
        with self.assertRaises(TimeoutError):m.root_domains(3,((0,0),(1,1)),set(),c,check)
        self.assertEqual((c['root_lines_started'],c['root_lines_completed']),(1,0));self.assertEqual((c['root_cell_visits_started'],c['root_cell_visits_completed']),(2,1));self.assertEqual(c['root_domain_cells_started'],0)


class MatchingTests(unittest.TestCase):
    def test_all_512_tiny_graphs_primal_cover_and_bruteforce(self):
        n=3
        for bits in product((0,1),repeat=9):
            domains=[sum(bits[3*r+c]<<c for c in range(3)) for r in range(3)];counter=m.new_counters();cert=m.maximum_matching(domains,n,counter,lambda:None)
            best=max(sum(c>=0 for c in assignment) for assignment in product((-1,0,1,2),repeat=3) if len({c for c in assignment if c>=0})==sum(c>=0 for c in assignment) and all(c<0 or domains[r]>>c&1 for r,c in enumerate(assignment)))
            self.assertEqual(cert['matching_size'],best);self.assertTrue(m.validate_matching_cover(domains,n,cert));self.assertEqual(len(cert['cover_rows'])+len(cert['cover_columns']),best)
            self.assertLessEqual(counter['matching_edge_scans_completed'],n*sum(v.bit_count() for v in domains));self.assertLessEqual(counter['cover_edge_scans_completed'],sum(v.bit_count() for v in domains))
        bad_cert={'matching':[[0,0]],'matching_size':1,'cover_rows':[],'cover_columns':[1]}
        with self.assertRaises(ValueError):m.validate_matching_cover([1,0,0],3,bad_cert)

    def test_timeout_inside_augment_does_not_return_certificate(self):
        c=m.new_counters()
        def check():
            if c['matching_edge_scans_started']==2:raise TimeoutError
        with self.assertRaises(TimeoutError):m.maximum_matching([7]*3,3,c,check)
        self.assertEqual((c['matching_edge_scans_started'],c['matching_edge_scans_completed']),(2,1))


class SearchTests(unittest.TestCase):
    def kernel(self,limit=2000,check=None):
        n,R,F=fixture();c=m.new_counters();unsafe,domains=m.root_domains(n,R,F,c,lambda:None)
        return m.Constructor(n,R,F,domains,unsafe,c,check or (lambda:None),limit),c

    def test_exhaustive_tiny_solutions_equal_permutations_and_every_prefix_valid(self):
        n,R,F=fixture();expected={frozenset(pointset(p)) for p in permutations(range(n)) if not pointset(p)&F and valid(set(R)|pointset(p))}
        kernel,c=self.kernel();found=[]
        def on_prefix(M):
            P=set(R)|set(M);self.assertTrue(valid(P));self.assertEqual(len(P),len(R)+len(M));self.assertEqual(len({p[0] for p in M}),len(M));self.assertEqual(len({p[1] for p in M}),len(M));self.assertFalse(set(M)&F)
            if len(M)==n:found.append(frozenset(M))
            return False
        before=(kernel.R,kernel.domains,kernel.root_unsafe,kernel.forbidden)
        self.assertFalse(kernel.run(on_prefix));self.assertEqual(set(found),expected);self.assertEqual(len(found),len(expected));self.assertEqual(len(found),2)
        self.assertTrue(kernel.root_restored);self.assertEqual(before,(kernel.R,kernel.domains,kernel.root_unsafe,kernel.forbidden));self.assertEqual(kernel.path,[])
        self.assertEqual(c['insertions_started'],c['insertions_completed']);self.assertEqual(c['maximum_added'],3);self.assertEqual(c['rollbacks'],c['insertions_completed'])

    def test_actual_callback_stops_first_full_and_restores(self):
        kernel,c=self.kernel();full=[]
        def stop(M):
            if len(M)==3:full.append(M);return True
            return False
        self.assertTrue(kernel.run(stop));self.assertEqual(len(full),1);self.assertEqual(c['full_assignments'],1);self.assertTrue(kernel.root_restored)

    def test_cap_and_candidate_propagation_timeout_restore(self):
        kernel,c=self.kernel(limit=1)
        with self.assertRaises(m.InsertionCap):kernel.run(lambda M:False)
        self.assertEqual(c['insertions_started'],1);self.assertTrue(kernel.root_restored);self.assertEqual(kernel.path,[])
        kernel,c=self.kernel()
        def check():
            if c['candidate_cell_visits_started']==2:raise TimeoutError
        kernel.check=check
        with self.assertRaises(TimeoutError):kernel.run(lambda M:False)
        self.assertEqual((c['insertions_started'],c['insertions_completed']),(1,0));self.assertTrue(kernel.root_restored);self.assertEqual(kernel.path,[])
        self.assertLessEqual(c['candidate_cell_visits_started'],3*(len(kernel.R)+c['maximum_added'])*c['insertions_started'])

    def test_empty_domain_and_forbidden_root_obstruction(self):
        kernel,c=self.kernel();kernel.domains=(0,)+kernel.domains[1:]
        self.assertFalse(kernel.run(lambda M:False));self.assertEqual(c['domain_wipeouts'],1);self.assertEqual(c['insertions_started'],0)
        r=report();B=set(product(range(2),repeat=2));R,parts=m.deterministic_matching(B,2)
        with tempfile.TemporaryDirectory() as tmp:m.search_anchor(3,B,set(),R,Path(tmp),r,lambda:None,{},2000)
        self.assertEqual(r['status'],'root_matching_obstruction');self.assertTrue(r['complete']);self.assertTrue(r['root_domains_complete']);self.assertTrue(r['root_matching_complete']);self.assertLess(r['root_matching_cover']['matching_size'],3);self.assertEqual(r['counters']['insertions_started'],0)

    def test_tiny_pipeline_persists_first_diagnostic_then_witness(self):
        n,R,B=fixture();r=report();saved=[];atomic=m.atomic
        def record(path,doc):saved.append((Path(path).name,deepcopy(doc)));atomic(path,doc)
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'atomic',record):m.search_anchor(n,B,set(),R,Path(tmp),r,lambda:None,{},2000)
        self.assertEqual(r['status'],'witness');self.assertTrue(r['complete']);self.assertTrue(r['root_state_restored']);self.assertEqual([p for p,_ in saved],['diagnostic156.json','witness157.json'])
        self.assertFalse(saved[0][1]['metadata']['improves_verified_lower_bound']);self.assertTrue(saved[1][1]['metadata']['improves_verified_lower_bound'])
        self.assertEqual([len(d['points']) for _,d in saved],[4,5]);self.assertEqual(r['counters']['full_assignments'],1)


class PublicationTests(unittest.TestCase):
    def candidate(self):
        n,R,B=fixture();M=((0,1),(1,2),(2,0));return n,R,M,B

    def test_distance_extremes_and_late_second_validator_save(self):
        n,R,M,B=self.candidate();now=[0];real=m.verify_certificate_bruteforce
        def late(cert):result=real(cert);now[0]=2;return result
        def check():
            if now[0]>=1:raise TimeoutError
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate_bruteforce',late):
            path=Path(tmp)/'witness';meta=m.save_candidate(n,R,M,B,set(R),path,'full_witness',check,{})
            self.assertTrue(path.exists());self.assertEqual(meta['excluded_source_retained'],len(R));self.assertEqual(meta['published_retained'],len(R));self.assertEqual(meta['new_points_outside_published'],3)
        with tempfile.TemporaryDirectory() as tmp:
            meta=m.save_candidate(n,R,M,B,{(2,2)},Path(tmp)/'witness','full_witness',lambda:None,{})
            self.assertEqual(meta['excluded_source_retained'],0)

    def test_validator_timeout_disagreement_and_source_readdition_rejected(self):
        n,R,M,B=self.candidate();now=[0];real=m.verify_certificate
        def first(cert):result=real(cert);now[0]=2;return result
        def check():
            if now[0]>=1:raise TimeoutError
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate',first),patch.object(m,'verify_certificate_bruteforce') as second:
            path=Path(tmp)/'witness'
            with self.assertRaises(TimeoutError):m.save_candidate(n,R,M,B,set(),path,'full_witness',check,{})
            second.assert_not_called();self.assertFalse(path.exists())
        real_second=m.verify_certificate_bruteforce
        def wrong(cert):r=real_second(cert);r['valid']=False;return r
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'verify_certificate_bruteforce',wrong):
            with self.assertRaises(RuntimeError):m.save_candidate(n,R,M,B,set(),Path(tmp)/'witness','full_witness',lambda:None,{})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):m.save_candidate(n,R,M,B,{M[0]},Path(tmp)/'witness','full_witness',lambda:None,{})

    def test_invalid_cells_caps_and_changed_pins(self):
        for P in ([(0,0),(0,0)],[(True,0)],[(-1,0)]):
            with self.assertRaises(ValueError):m.cells(P,3)
        with self.assertRaises(ValueError):m.deterministic_matching({(0,0)},3)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'p';path.write_bytes(b'before');pins={path:hashlib.sha256(path.read_bytes()).hexdigest()};m.verify_pins(pins);path.write_bytes(b'after')
            with self.assertRaises(ValueError):m.verify_pins(pins)
            for seconds,cap in ((0,2000),(26,2000),(True,2000),(25,2001),(25,-1)):
                with self.assertRaises(ValueError):m.run(Path(tmp),seconds,cap)


if __name__=='__main__':unittest.main()
