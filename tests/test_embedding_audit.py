import itertools
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.embedding_audit import (audit, count_conflicts, cut_orbit,
                                      gap_blockers, insert_grid_lines, rotate,
                                      minimal_hitting_sets, repair_low_conflict,
                                      stream_cover_repairs)
from src.verify import verify_certificate_bruteforce, normalized_sha256


def direct_count(points):
    return sum((b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])
               for a,b,c in itertools.combinations(points, 3))


class EmbeddingAuditTests(unittest.TestCase):
    def test_counter_matches_cross_products_for_all_small_sets(self):
        cells = list(itertools.product(range(3), repeat=2))
        for size in range(7):
            for points in itertools.combinations(cells, size):
                self.assertEqual(count_conflicts(points), direct_count(points))

    def test_cut_mapping_intertwines_rotation(self):
        for m in range(2, 6):
            points = list(itertools.product(range(m), repeat=2))
            for a,b in itertools.product(range(m+1), repeat=2):
                left = rotate(insert_grid_lines(points,m,a,b),m+1)
                right = set(insert_grid_lines(rotate(points,m),m,m-b,a))
                self.assertEqual(left,right)

    def test_corners_are_old_translations(self):
        points = [(0,0),(1,0),(0,1),(1,1)]
        for a,b in itertools.product((0,2),repeat=2):
            expected = [(x+(a==0),y+(b==0)) for x,y in points]
            self.assertEqual(insert_grid_lines(points,2,a,b),expected)

    def test_symmetry_scan_matches_full_scan_and_certificates(self):
        seed = {'n':2,'points':list(itertools.product(range(2),repeat=2))}
        quotient = audit(seed,seconds=5,use_symmetry=True)
        full = audit(seed,seconds=5,use_symmetry=False)
        self.assertEqual(quotient['status'],'complete')
        expanded = {tuple(c):r['conflict_count'] for r in quotient['records'] for c in r['equivalent_cuts']}
        expected = {tuple(r['cut']):r['conflict_count'] for r in full['records']}
        self.assertEqual(expanded,expected)
        self.assertEqual(quotient['valid_embedding_count'],full['valid_embedding_count'])
        self.assertTrue(quotient['found_certificates'])
        for certificate in quotient['found_certificates']:
            self.assertTrue(verify_certificate_bruteforce(certificate)['valid'])

    def test_asymmetric_seed_disables_quotient(self):
        seed = {'n':3,'points':[[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]}
        self.assertNotEqual(rotate(seed['points'],3),set(map(tuple,seed['points'])))
        report = audit(seed,seconds=5)
        self.assertFalse(report['symmetry_quotient_used'])
        self.assertEqual(report['total_representatives'],16)

    def test_timeout_is_partial(self):
        seed = {'n':2,'points':list(itertools.product(range(2),repeat=2))}
        report = audit(seed,seconds=0)
        self.assertEqual(report['status'],'timeout_incomplete')
        self.assertEqual(report['completed_representatives'],0)

    def test_minimal_hitting_sets_against_full_subsets(self):
        triples = [(0,1,2),(0,3,4),(1,3,4)]
        for budget in range(4):
            covers = [frozenset(s) for size in range(budget+1)
                      for s in itertools.combinations(range(5),size)
                      if all(set(s).intersection(t) for t in triples)]
            expected = {s for s in covers if not any(t<s for t in covers)}
            self.assertEqual(set(minimal_hitting_sets(triples,budget)),expected)

    def test_repair_matches_full_small_enumeration(self):
        # A valid partial seed becomes collinear after a nonuniform insertion.
        seed = {'n':4,'points':[[0,0],[1,2],[2,3]]}
        record = {'cut':[0,3],'conflict_count':1}
        scan = {'lowest_conflict_invalid_representatives':[record],
                'source_normalized_sha256':normalized_sha256(seed['n'],seed['points'])}
        points = insert_grid_lines(seed['points'],4,*record['cut'])
        result = repair_low_conflict(seed,scan,seconds=5,max_deletions=1,top=1)
        self.assertEqual(result['status'],'complete')
        expected = 0
        for size in range(2):
            for deletion in itertools.combinations(range(3),size):
                retained = [p for i,p in enumerate(points) if i not in deletion]
                pool = [p for p in itertools.product(range(5),repeat=2) if p not in retained]
                for gain in (1,2):
                    expected += sum(direct_count(retained+list(additions))==0
                                    for additions in itertools.combinations(pool,size+gain))
        self.assertEqual(len(result['found_certificates']),expected)

    def test_repair_rejects_invalid_or_mismatched_source(self):
        seed = {'n':2,'points':list(itertools.product(range(2),repeat=2))}
        scan = audit(seed,seconds=5)
        scan['source_normalized_sha256']='wrong hash'
        with self.assertRaisesRegex(ValueError,'hash'):
            repair_low_conflict(seed,scan)
        invalid = {'n':3,'points':[[0,0],[1,1],[2,2]]}
        with self.assertRaisesRegex(ValueError,'validation'):
            repair_low_conflict(invalid,scan)

    def test_streamed_resume_covers_same_sets_and_counts(self):
        seed={'n':4,'points':[[0,0],[1,2],[2,3]]}
        scan={'source_normalized_sha256':normalized_sha256(4,seed['points'])}
        args=(seed,scan,(0,3),[0])
        full=stream_cover_repairs(*args,deletion_count=2,max_cases=3,seconds=5)
        first=stream_cover_repairs(*args,deletion_count=2,max_cases=1,seconds=5)
        second=stream_cover_repairs(*args,deletion_count=2,start_offset=first['next_offset'],
                                   max_cases=1,seconds=5,
                                   expected_source_order_sha256=first['source_order_sha256'])
        self.assertEqual(full['status'],'complete')
        self.assertEqual(first['status'],'case_limit_incomplete')
        self.assertEqual(second['status'],'complete')
        self.assertEqual(second['next_offset'],full['total_deletion_sets'])
        self.assertFalse(full['base_is_unique_minimal_cover_through_budget'])
        for key in full['valid_addition_subsets']:
            self.assertEqual(full['valid_addition_subsets'][key],
                             first['valid_addition_subsets'][key]+second['valid_addition_subsets'][key])
        for cert in full['found_certificates']:
            self.assertTrue(verify_certificate_bruteforce(cert)['valid'])
        with self.assertRaisesRegex(ValueError,'ordered source hash'):
            stream_cover_repairs(*args,deletion_count=2,start_offset=1,max_cases=1,seconds=5)


if __name__ == '__main__':
    unittest.main()
