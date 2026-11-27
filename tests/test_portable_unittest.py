import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from research import portable_unittest as portable


def sha(data):
    return hashlib.sha256(data).hexdigest()


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = portable.ORIGINAL_RUNTIME + 'pysolvers.cpython-314-darwin.so'
        self.runtime2 = portable.ORIGINAL_RUNTIME + 'pysat/card.py'
        self.normal = 'research/owned.py'
        self.receipt = 'data/receipt.json'
        self.sources = {self.runtime: b'original', self.runtime2: b'card', self.normal: b'source'}
        for name, data in self.sources.items():
            self.write(name, data)
        data = json.dumps({'sources_before': {name: sha(content) for name, content in self.sources.items()}}).encode()
        self.write(self.receipt, data)
        self.pins = {self.receipt: sha(data)}

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def check(self):
        return portable.verify_anchor_availability(self.root, self.pins, self.receipt)

    def test_available_and_absent_runtime(self):
        self.assertEqual(self.check(), [])
        (self.root / self.runtime).unlink()
        self.assertEqual(self.check(), [self.runtime])

    def test_any_present_mismatch_fails_even_with_missing_runtime(self):
        (self.root / self.runtime).unlink()
        self.write(self.runtime2, b'changed')
        with self.assertRaisesRegex(ValueError, 'pinned file changed'):
            self.check()
        self.write(self.runtime2, self.sources[self.runtime2])
        self.write(self.normal, b'changed')
        with self.assertRaisesRegex(ValueError, 'pinned file changed'):
            self.check()

    def test_nonruntime_missing_and_bad_receipt_fail(self):
        (self.root / self.normal).unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()
        self.write(self.normal, self.sources[self.normal])
        self.write(self.receipt, b'bad')
        with self.assertRaisesRegex(ValueError, 'pinned file changed'):
            self.check()



calls = []


class SelectionTests(unittest.TestCase):
    def setUp(self):
        class Target(unittest.TestCase):
            def test_anchor(self):
                calls.append('anchor')
            def id(self):
                return next(iter(portable.TARGETS))
        class Synthetic(unittest.TestCase):
            def test_synthetic(self):
                calls.append('synthetic')
        self.Target, self.Synthetic = Target, Synthetic

    def run_suite(self, availability):
        calls.clear()
        suite = unittest.TestSuite([self.Target('test_anchor'), self.Synthetic('test_synthetic')])
        portable.select_portable_test(suite, availability)
        return unittest.TextTestRunner(stream=io.StringIO()).run(suite)

    def test_missing_skips_exact_target_but_runs_synthetic(self):
        result = self.run_suite(lambda: ['missing-original-runtime'])
        self.assertEqual(calls, ['synthetic'])
        self.assertEqual(len(result.skipped), 1)
        self.assertIn('missing-original-runtime', result.skipped[0][1])
        self.assertTrue(result.wasSuccessful())

    def test_available_runs_both(self):
        result = self.run_suite(lambda: [])
        self.assertEqual(calls, ['anchor', 'synthetic'])
        self.assertEqual(result.skipped, [])
        self.assertTrue(result.wasSuccessful())

    def test_error_is_not_skip_and_synthetic_runs(self):
        def bad():
            raise ValueError('mismatch')
        result = self.run_suite(bad)
        self.assertEqual(calls, ['synthetic'])
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.skipped, [])
        self.assertFalse(result.wasSuccessful())

    def test_missing_or_duplicate_target_fails_closed(self):
        for suite in (unittest.TestSuite([self.Synthetic('test_synthetic')]), unittest.TestSuite([self.Target('test_anchor'), self.Target('test_anchor')])):
            with self.assertRaisesRegex(RuntimeError, 'exactly one'):
                portable.select_portable_test(suite, lambda: [])


if __name__ == '__main__':
    unittest.main()
