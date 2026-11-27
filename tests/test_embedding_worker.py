import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.embedding_audit import stream_cover_repairs
from research.embedding_worker import atomic_json, load_gapless_chain, run_worker
from src.verify import normalized_sha256, verify_certificate_bruteforce


class EmbeddingWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)
        self.seed={'n':4,'points':[[0,0],[1,2],[2,3]]}
        self.scan={'source_normalized_sha256':normalized_sha256(4,self.seed['points'])}
        self.previous=stream_cover_repairs(self.seed,self.scan,(0,3),[0],deletion_count=2,max_cases=0,seconds=5)
        self.seed_path=self.directory/'seed.json'
        self.scan_path=self.directory/'scan.json'
        self.previous_path=self.directory/'origin.json'
        self.tip=self.directory/'tip.json'
        for p,value in [(self.seed_path,self.seed),(self.scan_path,self.scan),(self.previous_path,self.previous)]:
            atomic_json(p,value,immutable=True)

    def command(self,previous,max_cases=1):
        return subprocess.run([sys.executable,str(ROOT/'research/embedding_worker.py'),
                               '--previous',str(previous),'--output',str(self.tip),
                               '--seed',str(self.seed_path),'--scan',str(self.scan_path),
                               '--seconds','5','--max-cases',str(max_cases),'--chunk-cases','1'],
                              text=True,capture_output=True,check=False)

    def test_cli_restart_and_stale_previous_never_resets(self):
        origin=self.previous_path.read_bytes()
        first=self.command(self.previous_path)
        self.assertEqual(first.returncode,0,first.stderr)
        first_report=json.loads(first.stdout.splitlines()[-1])
        self.assertEqual(first_report['next_offset'],1)
        self.assertEqual(first_report['status'],'partial')
        # Deliberately pass the old origin again: the durable tip takes priority.
        second=self.command(self.previous_path)
        self.assertEqual(second.returncode,0,second.stderr)
        report=json.loads(second.stdout.splitlines()[-1])
        self.assertEqual(report['next_offset'],2)
        self.assertEqual(report['status'],'complete')
        self.assertEqual(report['completed_this_invocation'],1)
        self.assertEqual(self.previous_path.read_bytes(),origin)
        latest_path,latest,_,ancestors=load_gapless_chain(self.tip,self.seed,self.scan)
        self.assertEqual(len(ancestors),3)
        self.assertEqual(latest['start_offset'],1)
        self.assertTrue(latest_path.exists())
        for path in self.directory.glob('embedding-witness-*.json'):
            self.assertTrue(verify_certificate_bruteforce(json.loads(path.read_text()))['valid'])
        self.assertTrue(list(self.directory.glob('embedding-witness-*.json')))

    def test_relocated_chain_preserves_hash_checks(self):
        import shutil
        run_worker(self.previous_path,self.tip,self.seed,self.scan,seconds=5,max_cases=1,chunk_cases=1)
        moved=self.directory/'moved'
        moved.mkdir()
        for path in self.directory.glob('*.json'):
            shutil.move(str(path),moved/path.name)
        latest,record,_,ancestors=load_gapless_chain(moved/self.tip.name,self.seed,self.scan)
        self.assertEqual(record['next_offset'],1)
        self.assertEqual(latest.parent,moved.resolve())
        self.assertEqual(len(ancestors),2)
        (moved/self.previous_path.name).write_text('tampered')
        with self.assertRaises((ValueError,json.JSONDecodeError)):
            load_gapless_chain(moved/self.tip.name,self.seed,self.scan)

    def test_hash_rejection_before_progress(self):
        self.scan_path.write_text(json.dumps({'source_normalized_sha256':'bad hash'}))
        result=self.command(self.previous_path)
        self.assertEqual(result.returncode,2)
        self.assertIn('hash',result.stderr)
        self.assertFalse(self.tip.exists())

    def test_gap_and_history_tampering_rejected(self):
        invalid=dict(self.previous,start_offset=1,next_offset=1)
        path=self.directory/'gap.json'
        atomic_json(path,invalid,immutable=True)
        with self.assertRaisesRegex(ValueError,'zero-offset origin'):
            load_gapless_chain(path,self.seed,self.scan)
        run_worker(self.previous_path,self.tip,self.seed,self.scan,seconds=5,max_cases=1,chunk_cases=1)
        self.previous_path.write_text(self.previous_path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            load_gapless_chain(self.tip,self.seed,self.scan)

    def test_immutable_records_cannot_be_overwritten(self):
        with self.assertRaises(FileExistsError):
            atomic_json(self.previous_path,{},immutable=True)
        with self.assertRaisesRegex(ValueError,'overwrite'):
            run_worker(self.previous_path,self.previous_path,self.seed,self.scan,seconds=0)


if __name__=='__main__':
    unittest.main()
