import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research.corner_anchor_frontier import prepare
from src.verify import normalized_sha256

ROOT=Path(__file__).resolve().parents[1]


class EmbeddingBatchDispatchTest(unittest.TestCase):
    def test_opt_in_subprocess_delegates_arguments_and_records_transitive_source(self):
        seed={'n':2,'points':[[0,0],[0,1],[1,0],[1,1]]}
        scan={'source_normalized_sha256':normalized_sha256(2,seed['points'])}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            prepare(seed,scan,root/'input',initial_origins=0,deletion_count=2)
            (root/'seed.json').write_text(json.dumps(seed));(root/'scan.json').write_text(json.dumps(scan))
            command=[sys.executable,str(ROOT/'research/embedding_worker.py'),'--batch',
                     '--manifest',str(root/'input/manifest.json'),'--seed',str(root/'seed.json'),
                     '--scan',str(root/'scan.json'),'--output',str(root/'batch.json'),
                     '--records-directory',str(root/'records'),'--chunk-cases','1']
            for seconds,cases,expected_offset in [('0','0',0),('1','1',1),('0','0',1)]:
                result=subprocess.run(command+['--seconds',seconds,'--max-cases',cases],
                                      text=True,capture_output=True,check=False)
                self.assertEqual(result.returncode,0,result.stderr)
                report=json.loads(result.stdout.splitlines()[-1])
                self.assertEqual(report['kind'],'corner_anchor_batch_cursor_v1')
                self.assertEqual(report['seconds_budget'],float(seconds))
                self.assertEqual(report['max_cases'],int(cases))
                self.assertEqual(report['current_anchor_next_offset'],expected_offset)
                self.assertEqual(report['batch_source_sha256'],hashlib.sha256((ROOT/'research/corner_batch_worker.py').read_bytes()).hexdigest())
                self.assertEqual(json.loads((root/'batch.json').read_text())['batch_source_sha256'],report['batch_source_sha256'])
            for path in (root/'records').glob('*-start-*-end-*.json'):
                self.assertEqual(json.loads(path.read_text())['batch_source_sha256'],report['batch_source_sha256'])


if __name__=='__main__':unittest.main()
