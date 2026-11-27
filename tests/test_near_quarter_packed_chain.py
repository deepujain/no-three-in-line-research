"""Tiny protocol/fault coverage; synchronous fake guard is not host RSS evidence."""
import copy
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

from research import near_quarter_packed_chain as chain
from research import near_quarter_packed_worker as worker
from src.near_quarter_model import orbit_map
from tests import test_near_quarter_packed_worker as worker_tests


class ChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)/'chain'
        self.calls = 0
        self.stage_calls = []
        self.prepare()

    fake_guard = worker_tests.WorkerTests.fake_guard

    def prepare(self, n=3, quota=1):
        self.n = n
        self.declaration = worker.declaration(n)
        self.map_sha = worker.sha(worker.canonical(orbit_map(n)['orbits']))
        root = worker.run_stage(self.directory, stage_id='f'*32, operation='root', n=n,
            declaration_b64=self.declaration, expected_map_json_sha256=self.map_sha,
            max_new_nodes=0, seconds=30, rss_mib=256, _guard=self.fake_guard)
        self.assertEqual(root['result'], 'accepted')
        self.template = {'schema': 1, 'chain_dir': str(self.directory.resolve()),
            'start_accepted_record': worker._read_head(self.directory)[1], 'n': n,
            'declaration_b64': self.declaration, 'expected_map_json_sha256': self.map_sha,
            'source_manifest': worker.source_manifest(), 'stage_nodes': quota,
            'stage_seconds': 30, 'rss_mib': 256}
        self.write_template()

    def write_template(self):
        self.template_path = Path(self.tmp.name)/'template.json'
        raw = worker.canonical(self.template)
        self.template_path.write_bytes(raw)
        self.template_sha = worker.sha(raw)

    def stage(self, directory, **kwargs):
        self.stage_calls.append(copy.deepcopy(kwargs))
        return worker.run_stage(directory, **kwargs, _guard=self.fake_guard)

    def run_chain(self, seconds=120, run_id='1'*32, **kwargs):
        return chain.run_chain(self.template_path, self.template_sha, run_id, seconds,
                               _stage=kwargs.pop('_stage', self.stage), **kwargs)

    def test_exact_sequential_witness_and_exclusive_run_id(self):
        result = self.run_chain()
        self.assertEqual((result['status'], result['attempted_stages'], result['accepted_stages'],
                          result['accepted_new_nodes']), ('verified_witness', 2, 2, 2))
        previous = self.template['start_accepted_record']
        for index, call in enumerate(self.stage_calls):
            self.assertEqual(call['stage_id'], chain.stage_id('1'*32, index))
            self.assertEqual(call['expected_parent'], previous['checkpoint_sha256'])
            self.assertEqual((call['max_new_nodes'], call['seconds'], call['rss_mib']), (1, 30, 256))
            receipt = next(worker.strict_json(p.read_bytes(), worker.RECEIPT_CAP)
                for p in self.directory.glob('*.receipt.json')
                if worker.strict_json(p.read_bytes(), worker.RECEIPT_CAP)['stage_id'] == call['stage_id'])
            self.assertEqual(receipt['prior_accepted_record'], previous)
            previous = dict(previous, checkpoint_sha256=receipt['candidate_sha256'],
                checkpoint_parent_sha256=previous['checkpoint_sha256'],
                last_stage_id=receipt['stage_id'], last_job_sha256=receipt['job_sha256'],
                last_receipt_sha256=worker.sha(worker.canonical(receipt)),
                witness_sha256=receipt['witness_sha256'], event_sha256=receipt['event_sha256'])
        runs = self.directory/'runs'/('1'*32)
        self.assertEqual(runs.stat().st_mode & 0o777, 0o700)
        self.assertEqual(len(list(runs.glob('*.receipt.json'))), 2)
        with self.assertRaises(ValueError):  # Initial exact HEAD is now stale.
            self.run_chain()
        self.template['start_accepted_record'] = worker._read_head(self.directory)[1]
        self.write_template()
        with self.assertRaises(FileExistsError):
            self.run_chain()

    def test_tiny_exhaustion(self):
        for n, expected in ((5, 4), (7, 11)):
            self.directory = Path(self.tmp.name)/str(n)
            self.prepare(n)
            self.stage_calls.clear()
            result = self.run_chain()
            self.assertEqual(result['status'], 'slices_exhausted')
            self.assertEqual(result['accepted_new_nodes'], expected)
            self.assertEqual(result['accepted_stages'], len(self.stage_calls))

    def test_strict_template_hash_shape_fixed_limits(self):
        with self.assertRaises(ValueError):
            chain.load_template(self.template_path, '2'*64)
        original = copy.deepcopy(self.template)
        for field, value in (('schema', True), ('stage_seconds', 29), ('rss_mib', 255),
                             ('stage_nodes', False), ('n', 4), ('extra', 1)):
            self.template = copy.deepcopy(original)
            self.template[field] = value
            self.write_template()
            with self.assertRaises(ValueError):
                self.run_chain()
        self.assertEqual(self.stage_calls, [])

    def test_budget_before_and_after_stage(self):
        result = self.run_chain(seconds=31)
        self.assertEqual((result['status'], result['attempted_stages']), ('total_budget_cutoff', 0))
        self.assertEqual(self.stage_calls, [])
        times = iter((0, 0, 89_000_000_001, 90_000_000_000, 91_000_000_000))
        result = self.run_chain(run_id='2'*32, _clock=lambda: next(times))
        self.assertEqual((result['status'], result['accepted_stages']), ('total_budget_cutoff', 1))

    def test_reject_uncertain_idempotent_and_retained_lease_stop(self):
        for index, (status, retained) in enumerate((('rejected', False),
                ('acceptance_uncertain', True), ('accepted_idempotent', False), ('accepted', True))):
            def stage(directory, **kwargs):
                self.stage_calls.append(kwargs)
                return {'result': status, 'lease_retained': retained, 'stage_id': kwargs['stage_id'],
                        'receipt_sha256': '4'*64}
            result = self.run_chain(run_id=f'{index+2:032x}', _stage=stage)
            self.assertEqual((result['attempted_stages'], result['accepted_stages']), (1, 0))
            self.assertIn(result['status'], ('stage_stopped', 'stopped_error'))

    def test_existing_lease_rejects_before_call(self):
        (self.directory/'writer.lease').write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError, 'lease exists'):
            self.run_chain()
        self.assertEqual(self.stage_calls, [])

    def test_changed_sources_and_self_stop(self):
        for name in ('sources', 'caller'):
            def stage(directory, **kwargs):
                result = self.stage(directory, **kwargs)
                patcher = (mock.patch.object(worker, 'source_check', side_effect=ValueError('changed'))
                           if name == 'sources' else mock.patch.object(chain, 'EXECUTING_SHA', '2'*64))
                patcher.start()
                self.addCleanup(patcher.stop)
                return result
            result = self.run_chain(run_id=('3' if name == 'sources' else '4')*32, _stage=stage)
            self.assertEqual((result['status'], result['attempted_stages']), ('stopped_error', 1))
            mock.patch.stopall()
            self.template['start_accepted_record'] = worker._read_head(self.directory)[1]
            self.write_template()

    def test_returned_stage_receipt_and_exact_prior_binding(self):
        for index, kind in enumerate(('stage', 'receipt', 'prior', 'lease')):
            self.directory = Path(self.tmp.name)/('binding-'+kind)
            self.prepare()
            def stage(directory, **kwargs):
                result = self.stage(directory, **kwargs)
                if kind == 'stage':
                    result['stage_id'] = '8'*32
                elif kind == 'receipt':
                    result['receipt_sha256'] = '8'*64
                elif kind == 'lease':
                    (directory/'writer.lease').write_bytes(b'unexpected')
                else:
                    # A different full HEAD must never be adopted as the next authority.
                    raw, head = worker._read_head(directory)
                    head['chain_id'] = '8'*64
                    (directory/'accepted.json').write_bytes(worker.canonical(head))
                return result
            result = self.run_chain(run_id=f'{index+20:032x}', _stage=stage)
            self.assertEqual((result['status'], result['attempted_stages'], result['accepted_stages']),
                             ('stopped_error', 1, 0))

    def test_real_sigterm_during_inner_accepted_commit(self):
        old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
        boundaries = []
        def stage(directory, **kwargs):
            self.stage_calls.append(kwargs)
            def fault(boundary):
                if boundary == 'after_head_replace':
                    boundaries.append(boundary)
                    signal.raise_signal(signal.SIGTERM)
            return worker.run_stage(directory, **kwargs, _guard=self.fake_guard, fault=fault)
        result = self.run_chain(_stage=stage)
        self.assertEqual(boundaries, ['after_head_replace'])
        self.assertEqual((result['status'], result['attempted_stages'], result['accepted_stages']),
                         ('cancelled', 1, 1))
        self.assertFalse((self.directory/'writer.lease').exists())
        self.assertEqual({sig: signal.getsignal(sig) for sig in old_handlers}, old_handlers)
        old_fd = signal.set_wakeup_fd(-1)
        self.assertEqual(old_fd, -1)

    def test_incompatible_wakeup_fd_restored_and_own_pipe_closed(self):
        reader, writer = os.pipe()
        os.set_blocking(writer, False)
        previous = signal.set_wakeup_fd(writer)
        handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
        observed = []
        real_pipe = os.pipe
        def pipe():
            pair = real_pipe()
            observed.extend(pair)
            return pair
        try:
            with mock.patch.object(chain.os, 'pipe', side_effect=pipe):
                with self.assertRaisesRegex(ValueError, 'incompatible'):
                    self.run_chain()
            self.assertEqual(signal.set_wakeup_fd(writer), writer)
            self.assertEqual({sig: signal.getsignal(sig) for sig in handlers}, handlers)
            for fd in observed:
                with self.assertRaises(OSError):
                    os.fstat(fd)
            self.assertEqual(self.stage_calls, [])
        finally:
            signal.set_wakeup_fd(previous)
            os.close(reader)
            os.close(writer)


if __name__ == '__main__':
    unittest.main()
