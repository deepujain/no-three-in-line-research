"""Bounded sequential caller of the existing packed stage protocol.

The existing experiment pool owns this caller's complete elapsed allocation.
Inner receipts are chain evidence, not additional pool experiment charges.
"""
import argparse
import os
from pathlib import Path
import signal
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ''):
    sys.path.insert(0, str(ROOT))
from research import near_quarter_packed_worker as worker

TEMPLATE_KEYS = ('schema', 'chain_dir', 'start_accepted_record', 'n', 'declaration_b64',
    'expected_map_json_sha256', 'source_manifest', 'stage_nodes', 'stage_seconds', 'rss_mib')
EXECUTING_SHA = worker.sha(worker.read_bounded(Path(__file__), 1048576))
RESERVE_NS = 32_000_000_000


class StopNotifications:
    """Remember signals even while run_stage installs its temporary handlers."""
    def __init__(self):
        self.stopped = False
        self.previous = {}
        self.reader = self.writer = None
        self.old_fd = None

    def handler(self, _signum, _frame):
        self.stopped = True

    def __enter__(self):
        self.reader, self.writer = os.pipe()
        try:
            for fd in (self.reader, self.writer):
                os.set_blocking(fd, False)
                os.set_inheritable(fd, False)
            self.old_fd = signal.set_wakeup_fd(self.writer, warn_on_full_buffer=False)
            if self.old_fd != -1:
                raise ValueError('existing signal wakeup fd is incompatible')
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.previous[sig] = signal.signal(sig, self.handler)
            return self
        except BaseException:
            self.__exit__()
            raise

    def drain(self):
        while True:
            try:
                raw = os.read(self.reader, 4096)
            except BlockingIOError:
                break
            if not raw:
                break
            if any(value in (signal.SIGTERM, signal.SIGINT) for value in raw):
                self.stopped = True
        return self.stopped

    def __exit__(self, *_):
        try:
            if self.old_fd is not None:
                signal.set_wakeup_fd(self.old_fd)
        finally:
            try:
                for sig, old in self.previous.items():
                    signal.signal(sig, old)
            finally:
                for fd in (self.reader, self.writer):
                    if fd is not None:
                        os.close(fd)
                self.reader = self.writer = None


def load_template(path, expected_sha):
    worker.hexstr(expected_sha, zero=False)
    raw = worker.read_bounded(path, worker.JSON_CAP)
    if worker.sha(raw) != expected_sha:
        raise ValueError('raw template hash differs')
    template = worker.keys(worker.strict_json(raw), TEMPLATE_KEYS)
    worker.integer(template['schema'], 1, 1)
    directory = template['chain_dir']
    if (type(directory) is not str or len(directory.encode('utf-8')) > 1024 or
            not Path(directory).is_absolute() or str(Path(directory).resolve()) != directory):
        raise ValueError('trusted absolute chain directory required')
    head = worker.validate_head(template['start_accepted_record'])
    if head['checkpoint_sha256'] == worker.ZERO_HEX:
        raise ValueError('preapproved accepted checkpoint required')
    n = worker.integer(template['n'], 3, 79)
    if n % 2 != 1:
        raise ValueError('odd grid required')
    worker.parse_declaration(template['declaration_b64'], n)
    worker.hexstr(template['expected_map_json_sha256'], zero=False)
    worker.source_check(template['source_manifest'])
    worker.integer(template['stage_nodes'], 1, 10000)
    worker.integer(template['stage_seconds'], 30, 30)
    worker.integer(template['rss_mib'], 256, 256)
    return template


def stage_id(run_id, index):
    worker.hexstr(run_id, 32, zero=False)
    worker.integer(index)
    return worker.sha(b'NQ-PACKED-CHAIN-STAGE-v1\0'+bytes.fromhex(run_id)+struct.pack('>Q', index))[:32]


def no_lease(directory):
    if os.path.lexists(directory/'writer.lease'):
        raise ValueError('writer lease exists; explicit reconciliation required')


def check_sources(template):
    if worker.sha(worker.read_bounded(Path(__file__), 1048576)) != EXECUTING_SHA:
        raise ValueError('executing caller source changed')
    worker.source_check(template['source_manifest'])


def audit_head(template, head, *, previous=None, returned=None, expected_stage=None):
    """Reuse bounded worker validators; no grid construction or checkpoint replay."""
    directory = Path(template['chain_dir'])
    if head['map_json_sha256'] != template['expected_map_json_sha256']:
        raise ValueError('HEAD map differs')
    receipt = worker.validate_receipt(worker.read_bounded(
        directory/(head['last_receipt_sha256']+'.receipt.json'), worker.RECEIPT_CAP),
        head=head, sources=template['source_manifest'])
    stage_dir = directory/('stage-'+head['last_stage_id'])
    raw_job = worker.read_bounded(stage_dir/'job.json', worker.JSON_CAP)
    job = worker.validate_job(worker.strict_json(raw_job))
    for key, value in (('chain_dir', template['chain_dir']), ('n', template['n']),
            ('declaration', template['declaration_b64']),
            ('expected_map_json_sha256', template['expected_map_json_sha256']),
            ('sources', template['source_manifest'])):
        if job[key] != value:
            raise ValueError('accepted job/template differs: '+key)
    job_sha = worker.sha(raw_job)
    if job_sha != head['last_job_sha256']:
        raise ValueError('accepted job hash differs')
    raw_report = worker.read_bounded(stage_dir/'report.json', worker.JSON_CAP)
    report, _ = worker.validate_report(raw_report, job, job_sha, receipt['prior_accepted_record'])
    if (worker.sha(raw_report) != receipt['report_sha256'] or
            report['candidate_sha256'] != head['checkpoint_sha256'] or
            report['identity_hex'] != head['identity_hex'] or
            report['status'] != receipt['proposed_status']):
        raise ValueError('accepted report binding differs')
    if previous is not None:
        if (returned['stage_id'] != expected_stage or head['last_stage_id'] != expected_stage or
                returned['receipt_sha256'] != head['last_receipt_sha256'] or
                receipt['prior_accepted_record'] != previous or
                head['chain_id'] != previous['chain_id'] or
                head['identity_hex'] != previous['identity_hex'] or
                head['checkpoint_parent_sha256'] != previous['checkpoint_sha256'] or
                job['accepted_record'] != worker.accepted_job_record(previous) or
                job['operation'] != 'stage' or job['max_new_nodes'] != template['stage_nodes'] or
                job['limits'] != {'guard_seconds': 30, 'rss_mib': 256}):
            raise ValueError('new accepted stage/parent authority differs')
    return report


def run_chain(request_template, template_sha256, run_id, seconds, *, _stage=None,
              _clock=time.monotonic_ns):
    """One exclusive run; injected stage/clock are tiny-test boundaries only."""
    started = _clock()
    worker.integer(seconds, 1, 900)
    worker.hexstr(run_id, 32, zero=False)
    deadline = started+seconds*1_000_000_000
    template = load_template(request_template, template_sha256)
    directory = Path(template['chain_dir'])
    remembered = template['start_accepted_record']
    check_sources(template)
    if worker._read_head(directory)[1] != remembered:
        raise ValueError('initial exact HEAD differs')
    no_lease(directory)
    initial_report = audit_head(template, remembered)
    stage_call = worker.run_stage if _stage is None else _stage
    with StopNotifications() as stops:
        runs = directory/'runs'
        runs.mkdir(mode=0o700, exist_ok=True)
        if runs.is_symlink() or not runs.is_dir():
            raise ValueError('invalid run parent directory')
        run_dir = runs/run_id
        run_dir.mkdir(mode=0o700)  # Exclusive; deliberately no resume mode.
        worker.fsync_dir(runs)
        start_record = {'schema': 1, 'kind': 'packed_chain_start', 'run_id': run_id,
            'runner_sha256': EXECUTING_SHA, 'template_sha256': template_sha256,
            'source_manifest': template['source_manifest'], 'initial_head': remembered,
            'invocation_started_ns': started, 'deadline_ns': deadline, 'seconds': seconds}
        start_raw = worker.canonical(start_record)
        worker.publish(run_dir, start_raw, cap=worker.RECEIPT_CAP, suffix='.receipt.json')
        attempts = accepted = new_nodes = 0
        last_stage = last_receipt = None
        status, error = initial_report['status'], None
        try:
            while status not in ('verified_witness', 'slices_exhausted'):
                if stops.drain():
                    status = 'cancelled'
                    break
                check_sources(template)
                no_lease(directory)
                if worker._read_head(directory)[1] != remembered:
                    raise ValueError('exact remembered HEAD changed')
                if deadline-_clock() < RESERVE_NS:
                    status = 'total_budget_cutoff'
                    break
                if stops.drain():
                    status = 'cancelled'
                    break
                requested_stage = stage_id(run_id, attempts)
                attempts += 1
                last_stage, last_receipt = requested_stage, None
                returned = stage_call(directory, stage_id=requested_stage, operation='stage',
                    n=template['n'], declaration_b64=template['declaration_b64'],
                    expected_map_json_sha256=template['expected_map_json_sha256'],
                    expected_parent=remembered['checkpoint_sha256'],
                    max_new_nodes=template['stage_nodes'], seconds=30, rss_mib=256)
                stops.drain()
                if returned.get('lease_retained') is not False:
                    raise ValueError('returned retained/unknown lease')
                no_lease(directory)
                if returned.get('result') != 'accepted':
                    status = 'stage_stopped'
                    error = str(returned.get('result'))[:512]
                    break
                check_sources(template)
                _, head = worker._read_head(directory)
                report = audit_head(template, head, previous=remembered, returned=returned,
                                    expected_stage=requested_stage)
                remembered = head
                last_receipt = returned['receipt_sha256']
                accepted += 1
                new_nodes += report['new_nodes']
                status = report['status']
                if stops.drain():
                    status = 'cancelled'
                    break
        except Exception as exc:
            status, error = 'stopped_error', (type(exc).__name__+': '+str(exc))[:512]
        finished = _clock()
        summary = {'schema': 1, 'kind': 'packed_chain_final', 'run_id': run_id,
            'status': status, 'error': error, 'runner_sha256': EXECUTING_SHA,
            'template_sha256': template_sha256, 'source_manifest': template['source_manifest'],
            'start_record_sha256': worker.sha(start_raw),
            'initial_head_sha256': worker.sha(worker.canonical(template['start_accepted_record'])),
            'final_validated_head_sha256': worker.sha(worker.canonical(remembered)),
            'attempted_stages': attempts, 'accepted_stages': accepted,
            'accepted_new_nodes': new_nodes, 'last_stage_id': last_stage,
            'last_receipt_sha256': last_receipt, 'invocation_started_ns': started,
            'deadline_ns': deadline, 'summary_prepared_ns': finished,
            'through_summary_preparation_ns': finished-started,
            'timing_scope': 'caller through summary preparation; returned complete caller time also includes final durable publication'}
        summary_raw = worker.canonical(summary)
        worker.publish(run_dir, summary_raw, cap=worker.RECEIPT_CAP, suffix='.receipt.json')
    ended = _clock()
    return dict(summary, summary_sha256=worker.sha(summary_raw),
                complete_caller_ns=ended-started)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-template', required=True)
    parser.add_argument('--template-sha256', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--seconds', required=True, type=int)
    args = parser.parse_args(argv)
    try:
        result = run_chain(args.request_template, args.template_sha256, args.run_id, args.seconds)
        print(worker.canonical(result).decode('ascii'), flush=True)
        return 0 if result['status'] in ('total_budget_cutoff', 'verified_witness', 'slices_exhausted', 'cancelled') else 1
    except Exception as exc:
        print(worker.canonical({'status': 'rejected', 'error': (type(exc).__name__+': '+str(exc))[:512]}).decode('ascii'), flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
