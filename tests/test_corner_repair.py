import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from research.corner_repair import persist_certificate, quarter_turn_invariant
from src.verify import normalized_sha256


class CornerPersistenceTest(unittest.TestCase):
    def test_atomic_persistence_accepts_only_verified_target(self):
        valid = {'n':2,'points':[[0,0],[0,1],[1,0],[1,1]]}
        with tempfile.TemporaryDirectory() as tmp:
            path = persist_certificate(valid, 2, (4,), tmp)
            self.assertEqual(path.name, f'corner-witness-{normalized_sha256(2,valid["points"])}.json')
            self.assertEqual(json.loads(path.read_text()), valid)
            before = set(Path(tmp).iterdir())
            invalid = {'n':3,'points':[[0,0],[1,1],[2,2]]}
            with self.assertRaises(ValueError):
                persist_certificate(invalid, 3, (3,), tmp)
            with self.assertRaises(ValueError):
                persist_certificate(valid, 3, (4,), tmp)
            with self.assertRaises(ValueError):
                persist_certificate(valid, 2, (3,), tmp)
            self.assertEqual(set(Path(tmp).iterdir()), before)

    def test_cli_persists_callback_before_audit_returns(self):
        from research import corner_repair
        seed = {'n':2,'points':[[0,0],[0,1],[1,0],[1,1]]}
        witness = {'n':3,'points':[[0,1],[1,0],[2,0],[1,2],[2,2]]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed_path = root / 'seed.json'
            seed_path.write_text(json.dumps(seed))
            output = root / 'result.json'
            def fake_audit(seed, dx, dy, max_deletions, deadline, on_certificate):
                on_certificate(witness, [0])
                self.assertEqual(len(list((root / 'data').glob('corner-witness-*.json'))), 1)
                self.assertFalse(output.exists())
                return {'status':'timeout_incomplete'}
            with patch.object(corner_repair, 'ROOT', root), \
                    patch.object(corner_repair, 'audit_translation', side_effect=fake_audit), \
                    patch('sys.argv',['corner_repair','--seed',str(seed_path),'--seconds','1','--output',str(output)]):
                result = corner_repair.main()
            self.assertEqual(result, 2)
            self.assertEqual(json.loads(output.read_text())['status'], 'timeout_incomplete')

    def test_source_quarter_turn_check(self):
        self.assertTrue(quarter_turn_invariant({'n':2,'points':[[0,0],[0,1],[1,0],[1,1]]}))
        self.assertFalse(quarter_turn_invariant({'n':3,'points':[[0,0]]}))

if __name__ == '__main__':
    unittest.main()
