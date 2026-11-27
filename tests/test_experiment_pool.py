import unittest
import datetime
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from src.experiment_pool import validate_job, supervise


class ExperimentQueueTests(unittest.TestCase):
    def good(self):
        return {'id':'sat-global-g3','script':'src/lazy_sat.py','seconds':60,
                'args':['--n','79'],'hypothesis':'Test global exact cardinality search'}

    def test_valid_manifest(self):
        self.assertEqual(validate_job(self.good())['seconds'],60)

    def test_rejects_unbounded_or_unapproved_commands(self):
        for patch in ({'seconds':0},{'seconds':901},{'seconds':True},
                      {'id':'../escape'},{'script':'/bin/sh'},
                      {'args':['--seconds','9999']},{'args':[1]},{'hypothesis':''}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate_job(dict(self.good(),**patch))

    def test_actual_processes_have_receipts_and_are_not_repeated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'research').mkdir();(root/'src').mkdir()
            (root/'src/lazy_sat.py').write_text('print("finite test experiment")\n')
            deadline=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=10)).isoformat()
            (root/'research/state.json').write_text(json.dumps({'deadline':deadline,
                'initial_research_compute_seconds_reserved':0,'compute_seconds_limit':1000}))
            jobs=[dict(self.good(),id='test-'+str(i),seconds=1,args=[]) for i in range(4)]
            queue=root/'research/queue.json';queue.write_text(json.dumps({'jobs':jobs}))
            with patch('src.experiment_pool.ROOT',root), patch('src.experiment_pool.signal.signal'):
                supervise(queue,poll_seconds=.02)
                receipts={p.name:p.read_text() for p in (root/'data/experiments').glob('*.json')}
                self.assertEqual(len(receipts),4)
                self.assertTrue(all(json.loads(r)['exit_code']==0 for r in receipts.values()))
                self.assertTrue(all(json.loads(r)['elapsed_seconds']>0 for r in receipts.values()))
                supervise(queue,poll_seconds=.02)
                self.assertEqual(receipts,{p.name:p.read_text() for p in (root/'data/experiments').glob('*.json')})

    def test_expired_deadline_launches_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'research').mkdir()
            (root/'research/state.json').write_text(json.dumps({'deadline':'2000-01-01T00:00:00Z'}))
            queue=root/'research/queue.json';queue.write_text(json.dumps({'jobs':[self.good()]}))
            with patch('src.experiment_pool.ROOT',root),patch('src.experiment_pool.signal.signal'):
                supervise(queue,poll_seconds=.01)
            self.assertEqual(json.loads((root/'data/runner-status.json').read_text())['status'],'pilot_deadline')
            self.assertEqual(list((root/'data/experiments').glob('*.json')),[])

    def test_exception_stops_children_and_records_consumed_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'research').mkdir();(root/'src').mkdir()
            (root/'src/lazy_sat.py').write_text('import time\ntime.sleep(60)\n')
            deadline=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=10)).isoformat()
            (root/'research/state.json').write_text(json.dumps({'deadline':deadline,
                'initial_research_compute_seconds_reserved':0,'compute_seconds_limit':1000}))
            queue=root/'research/queue.json';queue.write_text(json.dumps({'jobs':[dict(self.good(),seconds=1)]}))
            def break_manifest(_):
                queue.write_text('{invalid JSON')
            with patch('src.experiment_pool.ROOT',root),patch('src.experiment_pool.signal.signal'),\
                    patch('src.experiment_pool.time.sleep',side_effect=break_manifest):
                with self.assertRaises(json.JSONDecodeError):
                    supervise(queue,poll_seconds=.01)
            receipt=json.loads(next((root/'data/experiments').glob('*.json')).read_text())
            self.assertEqual(receipt['status'],'supervisor_exception_or_exit')
            self.assertIsNotNone(receipt['exit_code'])
            self.assertGreater(receipt['elapsed_seconds'],0)

    def test_unresolved_launch_reservation_blocks_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'research').mkdir();(root/'data/experiments').mkdir(parents=True)
            (root/'research/state.json').write_text(json.dumps({'deadline':'2099-01-01T00:00:00Z'}))
            (root/'data/experiments/unresolved.json').write_text(json.dumps({
                'status':'reserved_before_spawn','elapsed_seconds':31}))
            queue=root/'research/queue.json';queue.write_text(json.dumps({'jobs':[]}))
            with patch('src.experiment_pool.ROOT',root):
                with self.assertRaisesRegex(RuntimeError,'Unresolved launch reservation'):
                    supervise(queue)
