from collections import Counter
from pathlib import Path
import tempfile
import unittest

from research import score11_deficiency_second_neighborhood as two
from research import score11_deficiency_neighborhood as one
from research import score11_deficiency_walk as base
from src.verify import collinear_triples_bruteforce, normalized_sha256


class SecondNeighborhoodTests(unittest.TestCase):
    def setUp(self):
        self.initial = {(0, 0), (0, 1), (1, 0), (1, 2), (2, 2)}
        self.parents = []
        for kind, old in [('column', ((1, 0),)), ('column', ((1, 2),)), ('rectangle', ((0, 1), (1, 2)))]:
            proposal = base.rectangle(self.initial, 3, *old) if kind == 'rectangle' else base.relocation(self.initial, 3, old[0], kind)
            self.assertEqual(proposal[0], 1)
            points = proposal[1]
            self.parents.append((points, 1, normalized_sha256(3, points), kind, old))

    def test_complete_conservation_and_determinant_unique_scores(self):
        with tempfile.TemporaryDirectory() as d:
            report = two.second_census(3, self.initial, 0, self.parents, Path(d) / 'best')
        self.assertEqual(report['status'], 'complete')
        self.assertTrue(report['complete'])
        legal = sum(v['legal'] for p in report['parents'] for v in p['classes'].values())
        self.assertEqual(legal, report['novel_first_insertions'] + report['preexisting_occurrences'])
        self.assertEqual(report['map_size'], 4 + report['novel_first_insertions'])
        self.assertEqual(report['backtrack_occurrences'], 3)
        self.assertEqual(report['same_parent_repeats'], 0)
        generated = {}
        for points, _, _, _, _ in self.parents:
            for kind, old in one.attempts(points):
                proposal = base.rectangle(points, 3, *old) if kind == 'rectangle' else base.relocation(points, 3, old[0], kind)
                if proposal:
                    candidate = proposal[1]
                    generated[frozenset(candidate)] = len(collinear_triples_bruteforce(sorted(candidate)))
        self.assertEqual(report['generated_unique_histogram'], dict(sorted(Counter(generated.values()).items())))
        self.assertGreater(report['cross_parent_revisits'], 0)
        for parent in report['parents']:
            for row in parent['classes'].values():
                self.assertEqual(row['started'], row['completed'])
                self.assertEqual(row['completed'], row['legal'] + row['illegal'])
                self.assertEqual(row['legal'], sum(row['deltas'].values()))

    def test_parent_and_initial_identity_fail_closed(self):
        parents = list(self.parents)
        p = list(parents[0]); p[2] = 'wrong'; parents[0] = tuple(p)
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'best'
            result = two.second_census(3, self.initial, 0, parents, target)
            self.assertEqual(result['status'], 'error')
            self.assertFalse(result['complete'])
            self.assertFalse(target.exists())
            result = two.second_census(3, self.initial, 0, self.parents, target, expected_initial='wrong')
            self.assertEqual(result['status'], 'error')

    def test_timeout_does_not_claim_complete(self):
        tick = [-1]
        def clock():
            tick[0] += 1
            return tick[0]
        with tempfile.TemporaryDirectory() as d:
            report = two.second_census(3, self.initial, 0, self.parents, Path(d) / 'best', seconds=5, clock=clock)
        self.assertEqual(report['status'], 'timeout')
        self.assertFalse(report['complete'])


if __name__ == '__main__':
    unittest.main()
