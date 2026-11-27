"""Tiny correctness/fault tests. Fake guard supplies no host resource evidence."""
import base64
import copy
import os
from pathlib import Path
import signal
import tempfile
import types
import unittest
from unittest import mock

from research import near_quarter_packed_worker as worker
from research import near_quarter_rowbatch_checkpoint as codec
from research.near_quarter_rowbatch_core import PackedRowBatchCore, ENTER, FOUND, EXHAUSTED
from src.near_quarter_model import orbit_map


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)/'chain'
        self.calls = 0

    def fake_guard(self, command, seconds, rss_mib, log_path, *, cancelled):
        self.calls += 1
        Path(log_path).write_bytes(b'')
        code = worker.worker_main(command[-2], command[-1])
        return {'gate_status': 'exited' if code == 0 else 'worker_error',
            'trigger_gate_status': None, 'returncode': code, 'elapsed_seconds': .01,
            'rss_samples': 1, 'monitor_error': None, 'seconds_limit': seconds,
            'rss_limit_mib': rss_mib, 'cleanup_status': 'clean', 'cleanup_error': None,
            'cleanup_samples': 1, 'cleanup_elapsed_seconds': .001,
            'peak_sampled_rss_kib': 1024,
            'rss_scope': 'guard parent plus spawned process group and observed descendants; native heap included',
            'gate_semantics': 'sampled RSS gate; cleanup included in wall gate; possible sampling overshoot; transient ps excluded'}

    def run_tiny(self, operation='stage', n=3, quota=2, stage=1, parent=worker.ZERO_HEX,
                 guard=None, fault=lambda _: None, diagonals=None):
        return worker.run_stage(self.directory, stage_id=f'{stage:032x}', operation=operation, n=n,
            declaration_b64=worker.declaration(n, diagonals=diagonals),
            expected_map_json_sha256=worker.sha(worker.canonical(orbit_map(n)['orbits'])),
            expected_parent=parent, max_new_nodes=quota if operation == 'stage' else 0,
            _guard=guard or self.fake_guard, fault=fault)

    def head(self):
        return worker._read_head(self.directory)[1]

    def report(self, stage=1):
        return worker.strict_json((self.directory/f'stage-{stage:032x}'/'report.json').read_bytes())

    def receipt(self, outcome):
        return worker.strict_json((self.directory/(outcome['receipt_sha256']+'.receipt.json')).read_bytes(), worker.RECEIPT_CAP)

    def test_n79_encoding_arithmetic_only(self):
        encoded = worker.declaration(79)
        self.assertEqual(len(base64.b64decode(encoded)), 3282)
        self.assertEqual(len(encoded), 4376)
        d, o, r = worker.parse_declaration(encoded, 79)
        self.assertEqual((len(d), len(o), len(r)), (39, 1521, 79))
        self.assertEqual(46+704+2*(39+1521+79)+96*40, codec.MAX_V1_BYTES)
        with self.assertRaises(ValueError):
            worker.parse_declaration(encoded+'AAAA', 79)

    def test_construct_and_root_zero_search_all_tiny(self):
        for n in (3, 5, 7):
            for operation in ('construct', 'root'):
                self.directory = Path(self.tmp.name)/f'{n}-{operation}'
                result = self.run_tiny(operation, n=n)
                self.assertEqual(result['result'], 'accepted')
                report = self.report()
                self.assertEqual((report['nodes_before'], report['new_nodes'], report['nodes_total']), (0, 0, 0))
                self.assertEqual(report['top_phase'], ENTER if operation == 'root' else None)
                receipt = self.receipt(result)
                self.assertFalse(receipt['search_performed'])
                self.assertFalse(receipt['search_complete'])
                self.assertLessEqual(receipt['timing']['precommit_cutoff_ns'], result['coordination_finished_ns'])
                self.assertFalse((self.directory/'writer.lease').exists())

    def test_zero_slice_construct_and_invalid_root(self):
        result = self.run_tiny('construct', diagonals=[])
        self.assertEqual(result['result'], 'accepted')
        self.assertEqual(self.report()['outer'], EXHAUSTED)
        self.assertFalse(self.receipt(result)['search_complete'])
        self.directory = Path(self.tmp.name)/'empty-root'
        with self.assertRaises(ValueError):
            self.run_tiny('root', diagonals=[])
        self.assertEqual(self.calls, 1)

    def test_witness_resume_idempotence_and_terminal_redelivery(self):
        first = self.run_tiny(quota=1)
        self.assertEqual(first['result'], 'accepted')
        first_head = self.head()
        self.assertEqual(self.report()['status'], 'node_limit_checkpointed')
        self.assertEqual(self.report()['nodes_total'], 1)
        second = self.run_tiny(quota=1, stage=2, parent=first_head['checkpoint_sha256'])
        self.assertEqual(second['result'], 'accepted')
        report = self.report(2)
        self.assertEqual(report['status'], 'verified_witness')
        self.assertEqual((report['nodes_before'], report['new_nodes'], report['nodes_total']), (1, 1, 2))
        witness_hash = self.head()['witness_sha256']
        calls = self.calls
        retry = self.run_tiny(quota=1, stage=2, parent=first_head['checkpoint_sha256'])
        self.assertEqual(retry['result'], 'accepted_idempotent')
        self.assertEqual(calls, self.calls)
        second_head = self.head()
        third = self.run_tiny(quota=1, stage=3, parent=second_head['checkpoint_sha256'])
        self.assertEqual(third['result'], 'accepted')
        self.assertEqual(self.report(3)['new_nodes'], 0)
        self.assertEqual(self.head()['witness_sha256'], witness_hash)
        self.assertEqual(self.report(3)['outer'], FOUND)
        with self.assertRaises(ValueError):
            self.run_tiny(quota=2, stage=3, parent=second_head['checkpoint_sha256'])
        self.assertEqual(self.calls, calls+1)

    def test_declared_tiny_exhaustion(self):
        for n, nodes in ((5, 4), (7, 11)):
            self.directory = Path(self.tmp.name)/str(n)
            result = self.run_tiny(n=n, quota=nodes+1)
            self.assertEqual(result['result'], 'accepted')
            self.assertEqual(self.report()['nodes_total'], nodes)
            self.assertEqual(self.report()['status'], 'slices_exhausted')
            self.assertTrue(self.receipt(result)['search_complete'])

    def test_strict_json_bounds_and_numeric_types(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'[[[[[[0]]]]]]',
                    b'{"a": 1}', b'{} '+b' '*16384):
            with self.assertRaises(ValueError):
                worker.strict_json(raw)
        self.run_tiny('construct')
        job = worker.strict_json((self.directory/f'stage-{1:032x}'/'job.json').read_bytes())
        for key, value in (('n', True), ('target', True), ('max_new_nodes', False), ('adapter', True)):
            bad = copy.deepcopy(job)
            bad[key] = value
            with self.assertRaises(ValueError):
                worker.validate_job(bad)
        bad = copy.deepcopy(job)
        bad['timing']['worker_deadline_ns'] = bad['timing']['precommit_deadline_ns']-1
        with self.assertRaises(ValueError):
            worker.validate_job(bad)
        bad = copy.deepcopy(job)
        bad['sources']['extra'] = '1'*64
        with self.assertRaises(ValueError):
            worker.validate_job(bad)
        with self.assertRaises(ValueError):
            worker.worker_main(str(self.directory/f'stage-{1:032x}'/'job.json'), '1'*64)

    def test_map_and_source_mismatch_reject(self):
        def guard(command, *args, **kwargs):
            with mock.patch.object(worker, 'source_check', side_effect=ValueError('source changed')):
                with self.assertRaises(ValueError):
                    worker.worker_main(command[-2], command[-1])
            raise RuntimeError('worker failed before report')
        result = self.run_tiny(guard=guard)
        self.assertEqual(result['result'], 'rejected')
        self.assertTrue(result['lease_retained'])
        self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)

    def test_source_changes_after_child_and_witness_publication_fault(self):
        def guard(command, *args, **kwargs):
            gate = self.fake_guard(command, *args, **kwargs)
            patcher = mock.patch.object(worker, 'source_check', side_effect=ValueError('late source change'))
            patcher.start()
            self.addCleanup(patcher.stop)
            return gate
        result = self.run_tiny(guard=guard)
        self.assertEqual(result['result'], 'rejected')
        self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)
        mock.patch.stopall()
        self.directory = Path(self.tmp.name)/'orphan-witness'
        original_publish = worker.publish
        def fail_witness(directory, raw, **kwargs):
            path = original_publish(directory, raw, **kwargs)
            if kwargs.get('suffix') == '.witness.json':
                raise OSError('witness durable but acknowledgment not delivered')
            return path
        with mock.patch.object(worker, 'publish', side_effect=fail_witness):
            result = self.run_tiny()
        self.assertEqual(result['result'], 'rejected')
        self.assertEqual(self.report()['outer'], 2)  # ACTIVE, still pending LEAF.
        self.assertIsNone(self.report()['candidate_sha256'])
        self.assertEqual(len(list(self.directory.glob('*.witness.json'))), 1)
        self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)

    def test_common_worker_expiry_does_not_save_after_stop(self):
        from research.near_quarter_packed_state import PackedStop
        def stop_run(*args, **kwargs):
            raise PackedStop('soft_deadline')
        with mock.patch.object(PackedRowBatchCore, 'run', side_effect=stop_run):
            with mock.patch.object(codec, 'save_candidate', side_effect=AssertionError('must not bypass expired budget')):
                result = self.run_tiny()
        self.assertEqual(result['result'], 'rejected')
        self.assertEqual(self.report()['status'], 'soft_deadline')
        self.assertTrue(self.report()['physical_counters_complete'])
        self.assertEqual(list(self.directory.glob('*.nqrb')), [])

    def test_resource_and_cleanup_failure_clear_claims(self):
        for kind in ('rss_limit', 'cleanup_error', 'monitor_error', 'no_samples'):
            self.directory = Path(self.tmp.name)/kind
            def guard(command, *args, **kwargs):
                gate = self.fake_guard(command, *args, **kwargs)
                if kind == 'no_samples':
                    gate['rss_samples'] = 0
                else:
                    gate['gate_status'] = kind
                if kind == 'cleanup_error':
                    gate['cleanup_status'], gate['cleanup_error'] = 'error', 'injected'
                return gate
            result = self.run_tiny(guard=guard)
            self.assertEqual(result['result'], 'rejected')
            receipt = self.receipt(result)
            for field in ('candidate_sha256', 'witness_sha256', 'event_sha256', 'proposed_status'):
                self.assertIsNone(receipt[field])
            self.assertFalse(receipt['search_complete'])
            self.assertEqual(result['lease_retained'], kind == 'cleanup_error')
            self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)

    def test_late_cancellation_and_precommit_expiry(self):
        for kind in ('cancel', 'deadline'):
            self.directory = Path(self.tmp.name)/kind
            patcher = None
            def fault(boundary):
                nonlocal patcher
                if boundary == 'before_precommit':
                    if kind == 'cancel':
                        signal.raise_signal(signal.SIGTERM)
                    else:
                        job = worker.strict_json((self.directory/f'stage-{1:032x}'/'job.json').read_bytes())
                        patcher = mock.patch.object(worker.time, 'monotonic_ns', return_value=job['timing']['precommit_deadline_ns'])
                        patcher.start()
            try:
                result = self.run_tiny(fault=fault)
            finally:
                if patcher:
                    patcher.stop()
            self.assertEqual(result['result'], 'rejected')
            self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)
            self.assertFalse(result['lease_retained'])

    def test_head_faults_before_replace_and_uncertain_after_replace(self):
        for boundary in ('before_head_replace', 'after_head_replace', 'after_head_directory_fsync'):
            self.directory = Path(self.tmp.name)/boundary
            def fault(name):
                if name == boundary:
                    raise OSError('injected durability failure')
            if boundary == 'before_head_replace':
                with self.assertRaises(OSError):
                    self.run_tiny(fault=fault)
                self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)
                self.assertTrue((self.directory/'writer.lease').exists())
            else:
                result = self.run_tiny(fault=fault)
                self.assertEqual(result['result'], 'acceptance_uncertain')
                self.assertTrue(result['lease_retained'])
                self.assertTrue((self.directory/'writer.lease').exists())
                calls = self.calls
                with self.assertRaises(FileExistsError):
                    self.run_tiny()
                self.assertEqual(calls, self.calls)

    def test_head_commit_cleanup_exception_retains_lease(self):
        original_replace, original_unlink = worker.os.replace, worker.os.unlink
        def failed_replace(source, destination):
            if Path(source).name.startswith('.head-'):
                raise OSError('replace outcome injected unknown')
            return original_replace(source, destination)
        def failed_cleanup(path, *args, **kwargs):
            if Path(path).name.startswith('.head-'):
                raise OSError('head-temp cleanup also failed')
            return original_unlink(path, *args, **kwargs)
        with mock.patch.object(worker.os, 'replace', side_effect=failed_replace):
            with mock.patch.object(worker.os, 'unlink', side_effect=failed_cleanup):
                with self.assertRaisesRegex(OSError, 'cleanup also failed'):
                    self.run_tiny()
        self.assertTrue((self.directory/'writer.lease').exists())
        self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)
        calls = self.calls
        with self.assertRaises(FileExistsError):
            self.run_tiny()
        self.assertEqual(self.calls, calls)

    def test_interrupted_private_save_replay_has_unknown_physical_work(self):
        from research.near_quarter_packed_state import PackedOrbitState, PackedStop
        original_loads, original_work_inc = codec.loads, PackedOrbitState._work_inc
        in_private_replay, positive_work_seen = False, False
        def private_loads(*args, **kwargs):
            nonlocal in_private_replay
            in_private_replay = True
            try:
                return original_loads(*args, **kwargs)
            finally:
                in_private_replay = False
        def stop_after_positive_work(state, name):
            nonlocal positive_work_seen
            original_work_inc(state, name)
            if in_private_replay and name == 'point_attempts':
                positive_work_seen = state.work['point_attempts'] > 0
                raise PackedStop('soft_deadline')
        with mock.patch.object(codec, 'loads', side_effect=private_loads):
            with mock.patch.object(PackedOrbitState, '_work_inc', new=stop_after_positive_work):
                result = self.run_tiny('root')
        self.assertTrue(positive_work_seen)
        self.assertEqual(result['result'], 'rejected')
        self.assertEqual(self.report()['status'], 'soft_deadline')
        self.assertFalse(self.report()['physical_counters_complete'])
        self.assertIsNone(self.report()['physical'])
        self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)
        self.assertEqual(list(self.directory.glob('*.nqrb')), [])

    def test_invalid_worker_report_and_log_reject(self):
        for kind in ('node_bool', 'outer_bool', 'candidate', 'witness', 'missing_report', 'oversized_log'):
            self.directory = Path(self.tmp.name)/kind
            def guard(command, *args, **kwargs):
                gate = self.fake_guard(command, *args, **kwargs)
                path = self.directory/f'stage-{1:032x}'/'report.json'
                report = worker.strict_json(path.read_bytes())
                if kind == 'missing_report':
                    path.unlink()
                elif kind == 'oversized_log':
                    Path(args[2]).write_bytes(b'x'*65537)
                elif kind == 'witness':
                    (self.directory/(report['witness_sha256']+'.witness.json')).write_bytes(b'{}')
                elif kind == 'candidate':
                    report['candidate_sha256'] = '1'*64
                    path.write_bytes(worker.canonical(report))
                else:
                    report['nodes_total' if kind == 'node_bool' else 'outer'] = True
                    path.write_bytes(worker.canonical(report))
                return gate
            result = self.run_tiny(guard=guard)
            self.assertEqual(result['result'], 'rejected')
            self.assertEqual(self.head()['checkpoint_sha256'], worker.ZERO_HEX)

    def test_accepted_receipt_nine_source_authority_before_resume(self):
        first = self.run_tiny(quota=1)
        head = self.head()
        receipt = self.receipt(first)
        receipt['source_manifest']['worker'] = 'a'*64
        raw = worker.canonical(receipt)
        changed_sha = worker.sha(raw)
        (self.directory/(changed_sha+'.receipt.json')).write_bytes(raw)
        head['last_receipt_sha256'] = changed_sha
        (self.directory/'accepted.json').write_bytes(worker.canonical(head))
        calls = self.calls
        with self.assertRaisesRegex(ValueError, 'nine-source identity'):
            self.run_tiny(stage=2, quota=1, parent=head['checkpoint_sha256'])
        self.assertEqual(calls, self.calls)
        self.assertFalse((self.directory/'writer.lease').exists())

    def test_failed_private_restore_reports_unknown_physical(self):
        first = self.run_tiny(quota=1)
        head = self.head()
        (self.directory/(head['checkpoint_sha256']+'.nqrb')).write_bytes(b'bad')
        result = self.run_tiny(stage=2, quota=1, parent=head['checkpoint_sha256'])
        self.assertEqual(result['result'], 'rejected')
        report = self.report(2)
        self.assertFalse(report['physical_counters_complete'])
        self.assertIsNone(report['physical'])
        self.assertIsNone(report['nodes_total'])
        self.assertEqual(self.head(), head)

    def test_immutable_publication_faults_and_bounds(self):
        directory = Path(self.tmp.name)
        for boundary in ('after_write', 'after_file_fsync', 'after_link', 'after_directory_fsync'):
            raw = worker.canonical({'boundary': boundary})
            def fault(name):
                if name == boundary:
                    raise OSError('injected')
            with self.assertRaises(OSError):
                worker.publish(directory, raw, cap=worker.JSON_CAP, suffix='.witness.json', fault=fault)
            worker.publish(directory, raw, cap=worker.JSON_CAP, suffix='.witness.json')
            self.assertEqual((directory/(worker.sha(raw)+'.witness.json')).read_bytes(), raw)
        worker.publish(directory, b'{}', cap=10, name='report.json')
        with self.assertRaises(ValueError):
            worker.publish(directory, b'{"a":1}', cap=10, name='report.json')
        with self.assertRaises(ValueError):
            worker.publish(directory, b'x'*11, cap=10, name='report.json')
        symlink = directory/'symlink'
        symlink.symlink_to(directory/'report.json')
        with self.assertRaises(OSError):
            worker.read_bounded(symlink, 10)

    def test_checked_physical_sets_and_overflow(self):
        core = types.SimpleNamespace(state=types.SimpleNamespace(work=dict.fromkeys(worker.STATE_COUNTERS, 3)),
            restore_work=dict.fromkeys(worker.STATE_COUNTERS, 1), validation_work=dict.fromkeys(worker.STATE_COUNTERS, 2))
        physical = worker.physical_counters(core)
        worker.validate_physical(physical, True)
        self.assertTrue(all(v == 2 for v in physical['traversal'].values()))
        core.validation_work[worker.STATE_COUNTERS[0]] = worker.U64
        with self.assertRaises(ValueError):
            worker.physical_counters(core)
        with self.assertRaises(ValueError):
            worker.validate_physical({}, False)


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.owner = codec.ChainLease(self.directory, expected_parent=bytes(32), chain_id=b'c'*32)
        self.owner.__enter__()
        self.addCleanup(self.owner.close_keep_lease)

    def borrow(self, **changes):
        fields = dict(expected_parent=self.owner.expected_parent, chain_id=self.owner.chain_id,
            nonce=self.owner.nonce, device=self.owner.stat.st_dev, inode=self.owner.stat.st_ino)
        fields.update(changes)
        return codec.ChainLease.borrow_for_worker(self.directory, **fields)

    def test_borrower_never_acquires_unlinks_or_releases(self):
        borrowed = self.borrow()
        with self.assertRaises(ValueError):
            borrowed.__enter__()
        with self.assertRaises(ValueError):
            borrowed.release()
        borrowed.__exit__(None, None, None)
        self.owner.verify()
        with self.assertRaises(ValueError):
            borrowed.verify()
        self.owner.release()
        self.assertFalse(self.owner.path.exists())

    def test_bad_borrow_tokens_truncation_and_inode_replacement(self):
        for fields in ({'nonce': b'd'*32}, {'inode': self.owner.stat.st_ino+1},
                       {'chain_id': b'd'*32}, {'expected_parent': b'd'*32}):
            with self.assertRaises(ValueError):
                self.borrow(**fields)
        original = self.owner.path.read_bytes()
        self.owner.path.write_bytes(original[:95])
        with self.assertRaises(ValueError):
            self.borrow()
        self.owner.path.write_bytes(original)
        borrowed = self.borrow()
        replacement = self.directory/'replacement'
        replacement.write_bytes(original)
        os.replace(replacement, self.owner.path)
        with self.assertRaises(ValueError):
            borrowed.verify()
        borrowed.close_keep_lease()
        with self.assertRaises(ValueError):
            self.owner.release()
        self.assertTrue(self.owner.path.exists())

    def test_borrowed_save_checks_ownership_and_write_faults(self):
        core = PackedRowBatchCore(3)
        borrowed = self.borrow()
        self.addCleanup(borrowed.close_keep_lease)
        def fault(boundary):
            if boundary == 'after_write':
                self.owner.path.write_bytes(b'x'*96)
        with self.assertRaises(ValueError):
            codec.save_candidate(core, lease=borrowed, fault=fault)
        self.assertEqual(list(self.directory.glob('*.nqrb')), [])
        self.assertTrue(self.owner.path.exists())

    def test_close_and_acquisition_write_failure_retain_owner(self):
        borrowed = self.borrow()
        fd = borrowed.fd
        with mock.patch.object(codec.os, 'close', side_effect=OSError('close fault')):
            with self.assertRaises(OSError):
                borrowed.close_keep_lease()
        os.close(fd)
        self.owner.verify()
        self.owner.release()
        failed = codec.ChainLease(self.directory, expected_parent=bytes(32), chain_id=b'd'*32)
        with mock.patch.object(codec.os, 'write', side_effect=OSError('write fault')):
            with self.assertRaises(OSError):
                failed.__enter__()
        self.assertTrue(failed.path.exists())
        self.assertIsNone(failed.fd)


if __name__ == '__main__':
    unittest.main()
