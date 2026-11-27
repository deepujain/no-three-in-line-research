"""Deterministic cleanup tests; no solver, host ps, or actual process signals."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import owned_process_guard as guard

PARENT = 900
ROOT_PID = 100


class FakeProcess:
    pid = ROOT_PID
    def __init__(self, returncode=0):
        self.returncode = returncode
    def poll(self):
        return self.returncode


def rows(*children):
    return {r.pid: r for r in [guard.ProcessRow(PARENT, 1, 800, 4000, 'S'), *children]}


def child(pid=ROOT_PID, ppid=PARENT, pgid=ROOT_PID, rss=2000, stat='S'):
    return guard.ProcessRow(pid, ppid, pgid, rss, stat)


class OwnedGuardTests(unittest.TestCase):
    def setUp(self):
        self.patches = [patch.object(guard.os, 'getpid', return_value=PARENT),
                        patch.object(guard.os, 'getpgrp', return_value=800),
                        patch.object(guard.os, 'getsid', return_value=ROOT_PID),
                        patch.object(guard.os, 'getpgid', return_value=ROOT_PID),
                        patch.object(guard.time, 'sleep')]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def cleanup_case(self, snapshots, process=None, **kwargs):
        process = process or FakeProcess()
        with patch.object(guard, 'process_snapshot', side_effect=snapshots), \
             patch.object(guard.os, 'killpg') as kill:
            report = guard.cleanup_owned_process(process, max_samples=len(snapshots), **kwargs)
        return report, kill

    def test_reaped_and_fresh_empty_skips_signal(self):
        report, kill = self.cleanup_case([rows()])
        self.assertEqual(report['cleanup_status'], 'clean')
        kill.assert_not_called()

    def test_empty_snapshot_does_not_hide_live_unreaped_root(self):
        report, kill = self.cleanup_case([rows(), rows()], FakeProcess(None))
        self.assertEqual(report['cleanup_status'], 'error')
        kill.assert_not_called()

    def test_live_group_killed_then_verified_empty(self):
        process = FakeProcess(None)
        def snapshot(timeout):
            if process.returncode is None:
                return rows(child())
            return rows()
        with patch.object(guard, 'process_snapshot', side_effect=snapshot), \
             patch.object(guard.os, 'killpg', side_effect=lambda *a: setattr(process, 'returncode', -9)) as kill:
            report = guard.cleanup_owned_process(process, max_samples=3)
        self.assertEqual(report['cleanup_status'], 'clean')
        self.assertEqual(process.returncode, -9)
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)

    def test_live_eperm_is_failure_even_if_later_empty(self):
        with patch.object(guard, 'process_snapshot', side_effect=[rows(child()), rows(child()), rows()]), \
             patch.object(guard.os, 'killpg', side_effect=PermissionError('denied')):
            report = guard.cleanup_owned_process(FakeProcess(), max_samples=3)
        self.assertEqual(report['cleanup_status'], 'error')
        self.assertIn('PermissionError', report['cleanup_error'])

    def test_eperm_exit_race_requires_fresh_empty_and_reaped(self):
        with patch.object(guard, 'process_snapshot', side_effect=[rows(child()), rows()]), \
             patch.object(guard.os, 'killpg', side_effect=PermissionError('exit race')):
            report = guard.cleanup_owned_process(FakeProcess(), max_samples=2)
        self.assertEqual(report['cleanup_status'], 'clean')
        self.assertEqual(report['cleanup_samples'], 2)

    def test_eperm_then_monitor_denial_fails(self):
        with patch.object(guard, 'process_snapshot', side_effect=[rows(child()), PermissionError('ps denied')]), \
             patch.object(guard.os, 'killpg', side_effect=PermissionError('exit race')):
            report = guard.cleanup_owned_process(FakeProcess(), max_samples=2)
        self.assertEqual(report['cleanup_status'], 'error')
        self.assertIn('ps denied', report['cleanup_error'])

    def test_esrch_is_refreshed_not_called_empty(self):
        with patch.object(guard, 'process_snapshot', side_effect=[rows(child()), rows()]) as snapshot, \
             patch.object(guard.os, 'getsid', side_effect=ProcessLookupError()), \
             patch.object(guard.os, 'killpg') as kill:
            report = guard.cleanup_owned_process(FakeProcess(), max_samples=2)
        self.assertEqual(report['cleanup_status'], 'clean')
        self.assertEqual(snapshot.call_count, 2)
        kill.assert_not_called()
        report, _ = self.cleanup_case([rows(child())])
        self.assertEqual(report['cleanup_status'], 'error')

    def test_reparented_descendant_in_original_group_is_removed(self):
        report, kill = self.cleanup_case([rows(child(101, 1)), rows()])
        self.assertEqual(report['cleanup_status'], 'clean')
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)

    def test_observed_secondary_group_fails_but_owned_group_is_cleaned(self):
        tracker = guard.OwnedProcessTracker(ROOT_PID)
        with patch.object(guard.os, 'getpgid', side_effect=lambda pid: ROOT_PID if pid == ROOT_PID else 101):
            first = tracker.inspect(FakeProcess(), rows(child(), child(101, ROOT_PID, 101)))
            self.assertTrue(first.errors)
            with patch.object(guard, 'process_snapshot', side_effect=[rows(child(101, 1, 101)), rows()]), \
                 patch.object(guard.os, 'killpg') as kill:
                report = guard.cleanup_owned_process(FakeProcess(), tracker, max_samples=2)
        self.assertEqual(report['cleanup_status'], 'error')
        kill.assert_called_once_with(101, signal.SIGKILL)

    def test_foreign_session_never_signaled(self):
        with patch.object(guard.os, 'getsid', return_value=777):
            report, kill = self.cleanup_case([rows(child()), rows()])
        self.assertEqual(report['cleanup_status'], 'error')
        kill.assert_not_called()

    def test_guard_group_never_signaled(self):
        tracker = guard.OwnedProcessTracker(ROOT_PID)
        tracker.observed.add(101)
        with patch.object(guard, 'process_snapshot', side_effect=[rows(child(101, 1, 800)), rows()]), \
             patch.object(guard.os, 'killpg') as kill:
            report = guard.cleanup_owned_process(FakeProcess(), tracker, max_samples=2)
        self.assertEqual(report['cleanup_status'], 'error')
        kill.assert_not_called()

    def test_identity_permission_failure_never_signals(self):
        with patch.object(guard.os, 'getsid', side_effect=PermissionError('sid denied')):
            report, kill = self.cleanup_case([rows(child())])
        self.assertEqual(report['cleanup_status'], 'error')
        self.assertIn('sid denied', report['cleanup_error'])
        kill.assert_not_called()

    def test_zombie_is_not_empty_and_cleanup_is_bounded(self):
        report, kill = self.cleanup_case([rows(child(rss=0, stat='Z'))]*3)
        self.assertEqual(report['cleanup_status'], 'error')
        self.assertEqual(report['cleanup_samples'], 3)
        kill.assert_not_called()

    def test_group_change_between_snapshot_and_identity_refreshes(self):
        with patch.object(guard.os, 'getpgid', return_value=101):
            report, kill = self.cleanup_case([rows(child())])
        self.assertEqual(report['cleanup_status'], 'error')
        kill.assert_not_called()

    def test_snapshot_parser_rejects_malformed_and_missing_guard(self):
        valid = f'{PARENT} 1 800 4000 S\n'
        bad = ['', '100 1\n', valid+valid, valid+'100 1 100 -1 S\n',
               valid+'100 1 100 1000 invalid\n', f'{PARENT} 1 800 0 S\n']
        for output in bad:
            with self.subTest(output=output), patch.object(guard.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 0, output, '')):
                with self.assertRaises(ValueError):
                    guard.process_snapshot()

    def test_owned_zero_live_rss_invalid_but_zero_rss_zombie_allowed(self):
        tracker = guard.OwnedProcessTracker(ROOT_PID)
        with self.assertRaises(ValueError):
            tracker.inspect(FakeProcess(), rows(child(rss=0)))
        self.assertFalse(tracker.inspect(FakeProcess(), rows(child(rss=0, stat='Z'))).live)

    def guard_case(self, cleanup=None, *, process=None, popen_error=None, cancelled=None):
        process = process or FakeProcess()
        cleanup = cleanup or {'cleanup_status':'clean', 'cleanup_error':None,
                              'peak_sampled_rss_kib':4000, 'cleanup_samples':1,
                              'cleanup_elapsed_seconds':0}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', side_effect=popen_error, return_value=process), \
             patch.object(guard, 'cleanup_owned_process', return_value=cleanup) as clean:
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log', cancelled=cancelled)
        return report, clean

    def test_launch_failure_is_terminal_without_cleanup(self):
        report, clean = self.guard_case(popen_error=OSError('launch denied'))
        self.assertEqual(report['gate_status'], 'launch_error')
        clean.assert_not_called()

    def test_no_sample_does_not_succeed(self):
        report, _ = self.guard_case()
        self.assertEqual(report['gate_status'], 'monitor_error')

    def test_cleanup_failure_overrides_normal_child_exit(self):
        report, _ = self.guard_case({'cleanup_status':'error', 'cleanup_error':'denied',
                                    'peak_sampled_rss_kib':4000})
        self.assertEqual(report['gate_status'], 'cleanup_error')

    def test_cleanup_crossing_wall_cap_fails(self):
        def cleanup(*args):
            times[0] = 2
            return {'cleanup_status':'clean', 'cleanup_error':None, 'peak_sampled_rss_kib':4000}
        times = [0]
        with patch.object(guard.time, 'monotonic', side_effect=lambda: times[0]), \
             patch.object(guard, 'cleanup_owned_process', side_effect=cleanup), \
             tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=FakeProcess()):
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log')
        self.assertEqual(report['gate_status'], 'wall_limit')

    def test_cleanup_rss_peak_cannot_succeed(self):
        report, _ = self.guard_case({'cleanup_status':'clean', 'cleanup_error':None,
                                    'peak_sampled_rss_kib':300000})
        self.assertEqual(report['gate_status'], 'rss_limit')

    def test_cancelled_before_launch_is_terminal(self):
        report, clean = self.guard_case(cancelled=lambda: True)
        self.assertEqual(report['gate_status'], 'cancelled')
        clean.assert_not_called()

    def test_keyboard_interrupt_still_cleans_and_reraises(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=FakeProcess(None)), \
             patch.object(guard, 'process_snapshot', side_effect=KeyboardInterrupt()), \
             patch.object(guard, 'cleanup_owned_process', return_value={'peak_sampled_rss_kib':0}) as clean:
            with self.assertRaises(KeyboardInterrupt):
                guard.guarded_process(['fake'], 1, 256, Path(directory)/'log')
        clean.assert_called_once()


    def test_cleanup_timeout_stops_before_another_snapshot(self):
        with patch.object(guard.time, 'monotonic', side_effect=[0, 2, 2]), \
             patch.object(guard, 'process_snapshot') as snapshot:
            report = guard.cleanup_owned_process(FakeProcess(), timeout=1)
        self.assertEqual(report['cleanup_status'], 'error')
        snapshot.assert_not_called()

    def test_monitor_recovery_cleans_best_effort_but_stays_failure(self):
        report, kill = self.cleanup_case([PermissionError('ps denied'), rows(child()), rows()])
        self.assertEqual(report['cleanup_status'], 'error')
        self.assertIn('ps denied', report['cleanup_error'])
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)

    def test_observed_violation_stays_fatal_after_disappearance(self):
        tracker = guard.OwnedProcessTracker(ROOT_PID)
        with patch.object(guard.os, 'getsid', return_value=777):
            tracker.inspect(FakeProcess(), rows(child()))
        with patch.object(guard, 'process_snapshot', return_value=rows()):
            report = guard.cleanup_owned_process(FakeProcess(), tracker)
        self.assertEqual(report['cleanup_status'], 'error')

    def test_sampled_success_retains_monitor_peak_above_cleanup_peak(self):
        process = FakeProcess(None)
        def snapshot(timeout):
            process.returncode = 0
            return rows(child(rss=10000))
        cleanup = {'cleanup_status':'clean', 'cleanup_error':None, 'peak_sampled_rss_kib':4000}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=process), \
             patch.object(guard, 'process_snapshot', side_effect=snapshot), \
             patch.object(guard, 'cleanup_owned_process', return_value=cleanup):
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log')
        self.assertEqual(report['gate_status'], 'exited')
        self.assertEqual(report['rss_samples'], 1)
        self.assertEqual(report['peak_sampled_rss_kib'], 14000)


    def test_live_monitor_denial_cleans_child_and_stays_failure(self):
        process = FakeProcess(None)
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=process), \
             patch.object(guard, 'process_snapshot', side_effect=[PermissionError('ps denied'), rows(child()), rows()]), \
             patch.object(guard.os, 'killpg', side_effect=lambda *a: setattr(process, 'returncode', -9)) as kill:
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log')
        self.assertEqual(report['gate_status'], 'monitor_error')
        self.assertEqual(report['cleanup_status'], 'clean')
        self.assertEqual(report['returncode'], -9)
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)

    def test_guard_root_exit_cleans_reparented_descendant(self):
        process = FakeProcess(None)
        snapshots = iter([rows(child(), child(101, ROOT_PID)), rows(child(101, 1)), rows()])
        def snapshot(timeout):
            value = next(snapshots)
            process.returncode = 0
            return value
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=process), \
             patch.object(guard, 'process_snapshot', side_effect=snapshot), \
             patch.object(guard.os, 'killpg') as kill:
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log')
        self.assertEqual(report['gate_status'], 'exited')
        self.assertEqual(report['cleanup_status'], 'clean')
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)

    def test_cancel_after_spawn_cleans_and_stays_cancelled(self):
        process = FakeProcess(None)
        cancelled = iter([False, True])
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(guard.subprocess, 'Popen', return_value=process), \
             patch.object(guard, 'process_snapshot', side_effect=[rows(child()), rows()]), \
             patch.object(guard.os, 'killpg', side_effect=lambda *a: setattr(process, 'returncode', -9)) as kill:
            report = guard.guarded_process(['fake'], 1, 256, Path(directory)/'log', cancelled=lambda: next(cancelled))
        self.assertEqual(report['gate_status'], 'cancelled')
        self.assertEqual(report['cleanup_status'], 'clean')
        self.assertEqual(report['returncode'], -9)
        kill.assert_called_once_with(ROOT_PID, signal.SIGKILL)


if __name__ == '__main__':
    unittest.main()
