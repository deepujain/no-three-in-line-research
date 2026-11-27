"""Opt-in tiny host checks; root runs only after independent helper review.

OWNED_GUARD_HOST_TESTS=1 .venv/bin/python -m unittest tests.test_owned_process_guard_host -v
No numerical model, build, or solver is imported.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.owned_process_guard import guarded_process


@unittest.skipUnless(os.environ.get('OWNED_GUARD_HOST_TESTS') == '1', 'explicit reviewed host trial only')
class OwnedGuardHostTests(unittest.TestCase):
    def run_child(self, code, seconds=2, rss_mib=256):
        with tempfile.TemporaryDirectory() as directory:
            return guarded_process([sys.executable, '-c', code], seconds, rss_mib,
                                   Path(directory)/'worker.log')

    def test_normal_completion_and_empty_cleanup(self):
        report = self.run_child('import time; time.sleep(.15)')
        self.assertEqual(report['gate_status'], 'exited', report)
        self.assertEqual(report['cleanup_status'], 'clean', report)
        self.assertGreater(report['rss_samples'], 0)

    def test_wall_limit_kills_and_reaps(self):
        report = self.run_child('import time; time.sleep(10)', seconds=.15)
        self.assertEqual(report['gate_status'], 'wall_limit', report)
        self.assertEqual(report['cleanup_status'], 'clean', report)
        self.assertLess(report['returncode'], 0)

    def test_native_rss_limit_kills_and_reaps(self):
        report = self.run_child('import time; time.sleep(10)', rss_mib=.001)
        self.assertEqual(report['gate_status'], 'rss_limit', report)
        self.assertEqual(report['cleanup_status'], 'clean', report)
        self.assertLess(report['returncode'], 0)

    def test_reparented_same_group_descendant_removed_after_root_exit(self):
        report = self.run_child('import subprocess,sys,time; '
            'subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"]); '
            'time.sleep(.15)')
        self.assertEqual(report['gate_status'], 'exited', report)
        self.assertEqual(report['cleanup_status'], 'clean', report)
        self.assertGreater(report['cleanup_samples'], 1)


if __name__ == '__main__':
    unittest.main()
