import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.corner_anchor_frontier import anchor_antichain, build_manifest, prepare
from research.embedding_audit import insert_grid_lines, stream_cover_repairs
from research.embedding_worker import load_gapless_chain
from research.guided_repair import blockers
from src.verify import normalized_sha256


class CornerAnchorTests(unittest.TestCase):
    def test_antichain_matches_direct_blocker_hitting(self):
        eligible = [((0,0), ((0,1),(2,3))), ((0,1), ((1,2),)),
                    ((1,0), ((0,1),(2,3),(4,5)))]
        covers, raw, distinct = anchor_antichain(eligible)
        self.assertEqual(raw, 14)
        self.assertLessEqual(len(covers), distinct)
        for size in range(4):
            for deleted in itertools.combinations(range(6), size):
                removed = set(deleted)
                direct = any(all(removed.intersection(pair) for pair in pairs) for _,pairs in eligible)
                represented = any(set(base) <= removed for base in covers)
                self.assertEqual(direct, represented)
        self.assertTrue(all(not set(a) < set(b) for a,b in itertools.permutations(covers, 2)))

    def test_corner_metadata_matches_all_tiny_deletions(self):
        seed = {'n':3, 'points':[[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]}
        manifest = build_manifest(seed, 2)
        points = insert_grid_lines(seed['points'], seed['n'], 0, 0)
        self.assertEqual(points[0], (1,1))
        empty = [p for p in itertools.product(range(4),repeat=2) if p not in points]
        families = [blockers(points,p) for p in empty]
        for size in range(3):
            for deleted in itertools.combinations(range(6), size):
                removed = set(deleted)
                expected = any(all(removed.intersection(pair) for pair in pairs) for pairs in families)
                actual = any(set(a['base_deletion_indices']) <= removed for a in manifest['anchors'])
                self.assertEqual(actual, expected)

    def test_origins_match_existing_engine_and_load_at_zero(self):
        seed = {'n':3, 'points':[[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]}
        scan = {'source_normalized_sha256':normalized_sha256(seed['n'],seed['points'])}
        with tempfile.TemporaryDirectory() as directory:
            manifest = prepare(seed, scan, directory, initial_origins=3, deletion_count=2)
            for anchor in manifest['anchors'][:3]:
                path = Path(directory)/anchor['origin_path']
                _, origin, _, _ = load_gapless_chain(path, seed, scan)
                direct = stream_cover_repairs(seed, scan, (0,0), anchor['base_deletion_indices'],
                                              deletion_count=2,max_cases=0,seconds=30)
                for key in direct:
                    if key != 'elapsed_seconds':
                        self.assertEqual(origin[key], direct[key], key)
                self.assertEqual(origin['next_offset'],0)
                self.assertEqual(origin['completed_deletion_sets'],0)
                self.assertFalse((Path(directory)/anchor['tip_path']).exists())


if __name__ == '__main__':
    unittest.main()
