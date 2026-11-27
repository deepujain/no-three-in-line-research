"""Exact original-host integrations may skip on Linux; integrity errors never skip."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from research import portable_unittest as p


class HostAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.exe = self.root/'original-mac-python'
        self.lib = self.root/'original-mac-extension'
        self.exe.write_bytes(b'python'); self.lib.write_bytes(b'extension')
        self.manifest = self.root/'manifest.json'
        self.manifest.write_text(json.dumps({'interpreter': str(self.exe), 'pins': {
            str(v): hashlib.sha256(v.read_bytes()).hexdigest() for v in (self.exe, self.lib)}}))
        self.sha = hashlib.sha256(self.manifest.read_bytes()).hexdigest()

    def check(self, platform='linux'):
        return p.original_host_runtime_missing(self.root, 'manifest.json', self.sha, platform)

    def test_complete_runtime_runs_even_on_linux(self):
        self.assertEqual(self.check(), [])

    def test_absent_interpreter_on_linux_is_explicit_absence(self):
        self.exe.unlink(); self.lib.unlink()
        self.assertEqual(self.check(), sorted(map(str, (self.exe, self.lib))))

    def test_absence_on_mac_and_partial_runtime_fail(self):
        self.lib.unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete'): self.check()
        self.exe.unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete'): self.check('darwin')

    def test_present_mismatch_fails_despite_absent_interpreter(self):
        self.exe.unlink(); self.lib.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'present host runtime pin changed'): self.check()

    def test_manifest_drift_fails_before_missing_runtime_skip(self):
        self.exe.unlink(); self.manifest.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest changed'): self.check()


class HostSelectionTests(unittest.TestCase):
    def build(self, prefix=''):
        calls = []
        class Dummy(unittest.TestCase):
            def test_body(self): calls.append(self.id())
        def case(name):
            t = Dummy('test_body'); t.id = lambda: prefix+name
            return t
        tests = [case(name) for name in sorted(p.HOST_TESTS)]
        tests.append(case('unrelated.Synthetic.test_unchanged'))
        return unittest.TestSuite(tests), calls

    def execute(self, availability, prefix=''):
        suite, calls = self.build(prefix); p.select_original_host_tests(suite, availability)
        return unittest.TextTestRunner(stream=io.StringIO()).run(suite), calls

    def test_exact_five_skip_and_unrelated_test_runs(self):
        result, calls = self.execute(lambda: ['missing-original-interpreter'])
        self.assertTrue(result.wasSuccessful()); self.assertEqual(len(result.skipped), 5)
        self.assertEqual(calls, ['unrelated.Synthetic.test_unchanged'])

    def test_complete_runtime_runs_every_test_and_accepts_tests_prefix(self):
        result, calls = self.execute(lambda: [], 'tests.')
        self.assertTrue(result.wasSuccessful()); self.assertEqual(result.testsRun, 6)
        self.assertEqual(len(calls), 6); self.assertFalse(result.skipped)

    def test_integrity_errors_never_become_skips(self):
        def mismatch(): raise ValueError('runtime mismatch')
        result, calls = self.execute(mismatch)
        self.assertEqual(len(result.errors), 5); self.assertFalse(result.skipped)
        self.assertEqual(calls, ['unrelated.Synthetic.test_unchanged'])

    def test_missing_and_duplicate_named_targets_fail_closed(self):
        for duplicate in (False, True):
            suite, _ = self.build()
            if duplicate: suite.addTest(list(suite)[0])
            else: suite = unittest.TestSuite(list(suite)[1:])
            with self.assertRaisesRegex(RuntimeError, 'five original-host tests'):
                p.select_original_host_tests(suite, lambda: [])


if __name__ == '__main__': unittest.main()
