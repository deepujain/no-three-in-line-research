import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'src'))
HAVE_PYSAT = importlib.util.find_spec('pysat') is not None
try:
    subprocess.run(['ps','-axo','pid=,ppid=,pgid=,rss='], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=.5)
    HAVE_PS = True
except (OSError, subprocess.SubprocessError):
    HAVE_PS = False


@unittest.skipUnless(HAVE_PYSAT, 'optional python-sat not installed')
class PreflightDispatchTests(unittest.TestCase):
    def test_only_opt_in_delegates_all_other_arguments_and_return_code(self):
        from lazy_sat import main
        arguments = ['--n','3','--near-quarter-preflight','--seconds','5',
                     '--rss-mib','256','--mode','build','--output','unused.json']
        original = arguments.copy()
        with patch('research.near_quarter_preflight.main', return_value=2) as delegated:
            self.assertEqual(main(arguments), 2)
            delegated.assert_called_once_with([value for value in arguments
                                               if value != '--near-quarter-preflight'])
        self.assertEqual(arguments, original)

    def test_ordinary_cli_help_remains_available(self):
        result = subprocess.run([sys.executable, str(ROOT/'src/lazy_sat.py'), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ('--n','--seconds','--target','--backend','--checkpoint','--symmetry'):
            self.assertIn(option, result.stdout)

    @unittest.skipUnless(HAVE_PS, 'host ps unavailable in this sandbox')
    def test_subprocess_build_only_n3_report_records_transitive_sources(self):
        from research.near_quarter_preflight import sha, MODEL, LINES
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'report.json'
            result = subprocess.run([sys.executable, str(ROOT/'src/lazy_sat.py'),
                '--near-quarter-preflight','--n','3','--mode','build','--seconds','5',
                '--rss-mib','256','--output',str(output)], capture_output=True, text=True,
                timeout=8)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            report = json.loads(output.read_text())
            self.assertEqual(report, json.loads(result.stdout))
            self.assertEqual(report['status'], 'built')
            self.assertTrue(report['build_complete'])
            self.assertEqual(report['clauses'], report['clauses_added'])
            self.assertGreater(report['weighted_lines'], 0)
            self.assertGreater(report['variables'], 0)
            self.assertEqual(report['source_hashes'], {'model_source_sha256':sha(MODEL),
                                                      'line_generator_sha256':sha(LINES)})
            self.assertEqual(report['preflight_source_sha256'], sha(ROOT/'research/near_quarter_preflight.py'))
            self.assertEqual(len(report['model_sha256']), 64)
            self.assertFalse(report['search_performed'])
            self.assertIsNone(report['solver_result'])
            self.assertEqual(report['guard']['seconds_limit'], 5)
            self.assertEqual(report['guard']['rss_limit_mib'], 256)
            self.assertGreater(report['guard']['peak_sampled_rss_kib'], 0)


if __name__ == '__main__':
    unittest.main()
