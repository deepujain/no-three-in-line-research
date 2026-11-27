"""Standalone source-bound packed worker and parent-owned acceptance protocol.

Only construct/root/stage operations exist. The unchanged owned_process_guard
supplies host monitoring. Tiny tests inject that boundary; they are not host
RSS/ownership evidence. No automatic retry, scheduler, or shared CLI route.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import signal
import stat
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = ('core', 'state', 'cursor', 'checkpoint', 'model', 'verifier',
                'line-model', 'worker', 'owned-helper')
SOURCE_PATHS = tuple(ROOT/p for p in (
    'research/near_quarter_rowbatch_core.py', 'research/near_quarter_packed_state.py',
    'research/near_quarter_rowbatch_cursor.py', 'research/near_quarter_rowbatch_checkpoint.py',
    'src/near_quarter_model.py', 'src/verify.py', 'src/line_model.py',
    'research/near_quarter_packed_worker.py', 'research/owned_process_guard.py'))
ZERO_HEX = '0'*64
U64 = (1 << 64)-1
JSON_CAP = 16384
HEAD_CAP = 4096
RECEIPT_CAP = 32768
ELIGIBLE = ('constructed', 'root_ready_no_search', 'node_limit_checkpointed',
            'slices_exhausted', 'verified_witness')
STATUS = ELIGIBLE+('soft_deadline', 'cancelled', 'worker_error')
HEAD_KEYS = ('schema', 'chain_id', 'checkpoint_sha256', 'checkpoint_parent_sha256',
             'identity_hex', 'last_stage_id', 'last_job_sha256', 'last_receipt_sha256',
             'map_json_sha256', 'witness_sha256', 'event_sha256')
JOB_KEYS = ('schema', 'stage_id', 'chain_id', 'operation', 'n', 'target', 'adapter',
            'leaf_mode', 'max_new_nodes', 'chain_dir', 'accepted_record', 'declaration',
            'expected_map_json_sha256', 'sources', 'lease_token', 'timing', 'limits')
REPORT_KEYS = ('schema', 'stage_id', 'job_sha256', 'chain_id', 'operation', 'n', 'adapter',
               'mode', 'source_manifest', 'identity_sha256', 'identity_hex',
               'expected_parent', 'candidate_sha256', 'status', 'outer', 'top_phase',
               'nodes_before', 'new_nodes', 'nodes_total', 'completed_slices',
               'declared_slices', 'event_sha256', 'witness_sha256', 'physical',
               'physical_counters_complete', 'domain_counters', 'elapsed_ns', 'error')
WITNESS_KEYS = ('schema', 'n', 'points', 'orbit_ids', 'family', 'map_json_sha256',
                'event_sha256', 'checks')
RECEIPT_KEYS = ('schema', 'stage_id', 'job_sha256', 'chain_id', 'prior_accepted_record',
    'source_manifest', 'report_sha256', 'candidate_sha256', 'witness_sha256', 'event_sha256',
    'search_complete', 'search_performed', 'proposed_status', 'observed_candidate_sha256',
    'physical_counters_complete', 'physical', 'gate', 'timing', 'timing_scope', 'result', 'rejection_reasons')
PHYSICAL_KEYS = ('state_total', 'restore_subset', 'traversal', 'validation_extra', 'physical_total')
STATE_COUNTERS = ('point_attempts', 'pair_lines', 'cell_increments', 'inverse_cells',
                  'points_undone', 'orbit_attempts', 'rejected_orbits', 'aborted_orbits')
DOMAIN_COUNTERS = ('domain_probes', 'batch_probes', 'cursor_checks', 'restore_probes', 'interrupted_scans')
FAMILY = 'odd-grid near-quarter-turn family'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError('fixed object keys differ')
    return value


def integer(value, low=0, high=U64):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('strict integer outside range')
    return value


def hexstr(value, length=64, *, zero=True):
    if (type(value) is not str or len(value) != length or
            any(c not in '0123456789abcdef' for c in value) or
            (not zero and value == '0'*length)):
        raise ValueError('fixed lowercase hexadecimal field')
    return value


def strict_json(raw, cap=JSON_CAP):
    """Bound bytes and nesting before invoking the JSON parser."""
    if type(raw) is not bytes or not 2 <= len(raw) <= cap:
        raise ValueError('JSON byte bound')
    depth, quoted, escaped = 0, False, False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > 5:
                raise ValueError('JSON depth bound')
        elif byte in (93, 125):
            depth -= 1
            if depth < 0:
                raise ValueError('JSON nesting')
    if quoted or depth:
        raise ValueError('JSON nesting')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def reject(_):
        raise ValueError('nonfinite JSON number')
    result = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject)
    if canonical(result) != raw:
        raise ValueError('noncanonical JSON')
    return result


def read_bounded(path, cap, check=lambda: None):
    check()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= cap:
            raise ValueError('artifact type/size bound')
        parts, total = [], 0
        while True:
            check()
            part = os.read(fd, min(65536, cap+1-total))
            if not part:
                break
            parts.append(part)
            total += len(part)
            if total > cap:
                raise ValueError('artifact grew over bound')
        after = os.fstat(fd)
        if (total != before.st_size or before.st_size != after.st_size or
                before.st_mtime_ns != after.st_mtime_ns or before.st_ino != after.st_ino):
            raise ValueError('artifact changed while reading')
        return b''.join(parts)
    finally:
        os.close(fd)


EXECUTING_WORKER_SHA = sha(read_bounded(Path(__file__), 1048576))
OWNED_HELPER_SHA = 'c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48'


def source_manifest(check=lambda: None):
    return dict(zip(SOURCE_NAMES, (sha(read_bounded(p, 1048576, check)) for p in SOURCE_PATHS)))


def source_check(expected, check=lambda: None):
    keys(expected, SOURCE_NAMES)
    for value in expected.values():
        hexstr(value, zero=False)
    if expected['worker'] != EXECUTING_WORKER_SHA or expected['owned-helper'] != OWNED_HELPER_SHA:
        raise ValueError('executing worker/frozen helper identity differs')
    if source_manifest(check) != expected:
        raise ValueError('executing sources differ')


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_all(fd, raw, check):
    offset = 0
    while offset < len(raw):
        check()
        count = os.write(fd, raw[offset:offset+65536])
        if count <= 0:
            raise OSError('write made no progress')
        offset += count


def publish(directory, raw, *, cap, suffix=None, name=None, check=lambda: None,
            fault=lambda _: None):
    """Immutable bounded publication; a duplicate must have identical bytes."""
    if type(raw) is not bytes or not 0 < len(raw) <= cap:
        raise ValueError('publication size bound')
    if name is None:
        if suffix not in ('.witness.json', '.receipt.json'):
            raise ValueError('fixed publication suffix')
        name = sha(raw)+suffix
    elif name not in ('job.json', 'report.json', 'accepted.json'):
        raise ValueError('fixed publication basename')
    destination = Path(directory)/name
    temp = Path(directory)/('.publish-'+secrets.token_hex(16))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        write_all(fd, raw, check)
        fault('after_write')
        check()
        os.fsync(fd)
        fault('after_file_fsync')
        os.close(fd)
        fd = None
        check()
        try:
            os.link(temp, destination, follow_symlinks=False)
        except FileExistsError:
            if read_bounded(destination, cap, check) != raw:
                raise ValueError('immutable content collision')
        fault('after_link')
        check()
        fsync_dir(directory)
        fault('after_directory_fsync')
        os.unlink(temp)
        fsync_dir(directory)
        check()
        return destination
    finally:
        if fd is not None:
            os.close(fd)
        if temp.exists():
            os.unlink(temp)


def declaration(n, diagonals=None, orbits=None, rows=None):
    """Arithmetic-only exact declaration builder; never constructs geometry."""
    integer(n, 3, 79)
    if n % 2 != 1:
        raise ValueError('odd grid required')
    m, four = n//2, (n//2)**2
    d = tuple(range(four+1, four+m+1)) if diagonals is None else tuple(diagonals)
    o = tuple(range(1, four+1)) if orbits is None else tuple(orbits)
    r = tuple(range(n)) if rows is None else tuple(rows)
    values = (n, len(d), *d, *o, *r)
    for v in values:
        integer(v, 0, 65535)
    raw = b''.join(struct.pack('>H', v) for v in values)
    encoded = base64.b64encode(raw).decode('ascii')
    parse_declaration(encoded, n)
    return encoded


def parse_declaration(value, n):
    if type(value) is not str or len(value) > 4376:
        raise ValueError('declaration encoding bound')
    raw = base64.b64decode(value, validate=True)
    if len(raw) > 3282 or len(raw) < 4 or len(raw) % 2 or base64.b64encode(raw).decode('ascii') != value:
        raise ValueError('declaration byte bound/canonical form')
    values = struct.unpack('>'+'H'*(len(raw)//2), raw)
    m, four = n//2, (n//2)**2
    if values[0] != n or values[1] > m or len(values) != 2+values[1]+four+n:
        raise ValueError('declaration exact lengths')
    d = tuple(values[2:2+values[1]])
    o = tuple(values[2+len(d):2+len(d)+four])
    r = tuple(values[2+len(d)+four:])
    if (len(set(d)) != len(d) or not set(d) <= set(range(four+1, four+m+1)) or
            sorted(o) != list(range(1, four+1)) or sorted(r) != list(range(n))):
        raise ValueError('declaration bijections')
    return d, o, r


def validate_head(head):
    keys(head, HEAD_KEYS)
    integer(head['schema'], 1, 1)
    hexstr(head['chain_id'], zero=False)
    for name in ('checkpoint_sha256', 'checkpoint_parent_sha256', 'last_job_sha256',
                 'last_receipt_sha256', 'map_json_sha256'):
        hexstr(head[name])
    if head['checkpoint_sha256'] == ZERO_HEX:
        if any(head[k] is not None for k in ('identity_hex', 'last_stage_id', 'witness_sha256', 'event_sha256')):
            raise ValueError('nonempty genesis')
        if any(head[k] != ZERO_HEX for k in ('checkpoint_parent_sha256', 'last_job_sha256', 'last_receipt_sha256')):
            raise ValueError('nonzero genesis authority')
    else:
        hexstr(head['identity_hex'], 1024, zero=False)
        hexstr(head['last_stage_id'], 32, zero=False)
        hexstr(head['last_job_sha256'], zero=False)
        hexstr(head['last_receipt_sha256'], zero=False)
    for k in ('witness_sha256', 'event_sha256'):
        if head[k] is not None:
            hexstr(head[k], zero=False)
    if (head['witness_sha256'] is None) != (head['event_sha256'] is None):
        raise ValueError('partial witness authority')
    return head


def accepted_job_record(head):
    if head['checkpoint_sha256'] == ZERO_HEX:
        return None
    return {'checkpoint_sha256': head['checkpoint_sha256'],
            'checkpoint_parent_sha256': head['checkpoint_parent_sha256'],
            'chain_id': head['chain_id'], 'identity_hex': head['identity_hex'],
            'preceding_receipt_sha256': head['last_receipt_sha256']}


def validate_job(job):
    keys(job, JOB_KEYS)
    integer(job['schema'], 1, 1)
    hexstr(job['stage_id'], 32, zero=False)
    hexstr(job['chain_id'], zero=False)
    n = integer(job['n'], 3, 79)
    if n % 2 != 1 or job['operation'] not in ('construct', 'root', 'stage'):
        raise ValueError('operation/grid')
    integer(job['target'], 2*n, 2*n)
    integer(job['adapter'], 2, 2)
    integer(job['leaf_mode'], 1, 1)
    integer(job['max_new_nodes'], 1 if job['operation'] == 'stage' else 0,
            10000 if job['operation'] == 'stage' else 0)
    d, _, _ = parse_declaration(job['declaration'], n)
    if job['operation'] == 'root' and not d:
        raise ValueError('root requires a declared slice')
    path = job['chain_dir']
    if (type(path) is not str or len(path.encode('utf-8')) > 1024 or
            not Path(path).is_absolute() or str(Path(path).resolve()) != path):
        raise ValueError('trusted absolute chain path')
    hexstr(job['expected_map_json_sha256'], zero=False)
    keys(job['sources'], SOURCE_NAMES)
    for h in job['sources'].values():
        hexstr(h, zero=False)
    token = keys(job['lease_token'], ('owner_nonce', 'device', 'inode', 'expected_parent'))
    hexstr(token['owner_nonce'], zero=False)
    hexstr(token['expected_parent'])
    integer(token['device'])
    integer(token['inode'])
    accepted = job['accepted_record']
    if accepted is None:
        if token['expected_parent'] != ZERO_HEX:
            raise ValueError('fresh chain parent')
    else:
        keys(accepted, ('checkpoint_sha256', 'checkpoint_parent_sha256', 'chain_id',
                        'identity_hex', 'preceding_receipt_sha256'))
        for k in ('checkpoint_sha256', 'preceding_receipt_sha256', 'chain_id'):
            hexstr(accepted[k], zero=False)
        hexstr(accepted['checkpoint_parent_sha256'])
        hexstr(accepted['identity_hex'], 1024, zero=False)
        if (accepted['chain_id'] != job['chain_id'] or accepted['checkpoint_sha256'] != token['expected_parent'] or
                job['operation'] != 'stage'):
            raise ValueError('resume authority/operation')
    timing = keys(job['timing'], ('invocation_started_ns', 'worker_deadline_ns', 'precommit_deadline_ns'))
    for v in timing.values():
        integer(v, 1)
    start, worker, pre = (timing[k] for k in ('invocation_started_ns', 'worker_deadline_ns', 'precommit_deadline_ns'))
    if not start < worker < pre <= start+30_000_000_000 or pre-worker < 2_000_000_000:
        raise ValueError('absolute timing/reserve bounds')
    limits = keys(job['limits'], ('guard_seconds', 'rss_mib'))
    for k, cap in (('guard_seconds', 30), ('rss_mib', 256)):
        v = limits[k]
        if type(v) not in (float, int) or not math.isfinite(v) or not 0 < v <= cap:
            raise ValueError('resource bounds')
    return job


class Cancellation:
    def __init__(self):
        self.cancelled = False
        self.previous = {}

    def handler(self, _signum, _frame):
        self.cancelled = True

    def __enter__(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            self.previous[sig] = signal.signal(sig, self.handler)
        return self

    def __exit__(self, *_):
        for sig, previous in self.previous.items():
            signal.signal(sig, previous)


def physical_counters(core):
    result = dict.fromkeys(PHYSICAL_KEYS)
    for name in PHYSICAL_KEYS:
        result[name] = {}
    for key in STATE_COUNTERS:
        state = integer(core.state.work[key])
        restore = integer(core.restore_work[key], 0, state)
        extra = integer(core.validation_work[key])
        for group, value in (('state_total', state), ('restore_subset', restore),
                             ('traversal', state-restore), ('validation_extra', extra),
                             ('physical_total', integer(state+extra))):
            result[group][key] = value
    return result


def event_digest(n, points, ids, map_sha):
    return sha(canonical({'n': n, 'points': points, 'orbit_ids': ids,
                          'family': FAMILY, 'map_json_sha256': map_sha}))


def make_witness(core, map_sha, check):
    from src.verify import verify_certificate, verify_certificate_bruteforce
    ids = sorted(core.state.selected)
    four = (core.n//2)**2
    if (len(ids) != core.m+1 or sum(v <= four for v in ids) != core.m or
            sum(v > four for v in ids) != 1):
        raise ValueError('witness orbit family count')
    points = sorted([list(p) for v in ids for p in core.state.model['orbits'][v-1]])
    check()
    a = verify_certificate({'n': core.n, 'points': points})
    check()
    b = verify_certificate_bruteforce({'n': core.n, 'points': points})
    check()
    if (not a['valid'] or not b['valid'] or len(points) != 2*core.n or
            a['normalized_sha256'] != b['normalized_sha256']):
        raise ValueError('independent witness verification failed')
    witness = {'schema': 1, 'n': core.n, 'points': points, 'orbit_ids': ids,
               'family': FAMILY, 'map_json_sha256': map_sha,
               'event_sha256': event_digest(core.n, points, ids, map_sha),
               'checks': [{k: report[k] for k in ('algorithm', 'valid', 'point_count', 'normalized_sha256')}
                          for report in (a, b)]}
    return witness


def worker_main(job_path, expected_sha):
    """Private child entrypoint. Imports/replay/verifiers/publication share budget."""
    started = time.monotonic_ns()
    hexstr(expected_sha, zero=False)
    raw = read_bounded(job_path, JSON_CAP)
    if sha(raw) != expected_sha:
        raise ValueError('external job SHA differs')
    job = validate_job(strict_json(raw))
    stage_dir = Path(job['chain_dir'])/('stage-'+job['stage_id'])
    if Path(job_path) != stage_dir/'job.json' or stage_dir.is_symlink():
        raise ValueError('fixed owned job path')
    with Cancellation() as cancellation:
        def check():
            if cancellation.cancelled:
                from research.near_quarter_packed_state import PackedStop
                raise PackedStop('cancelled')
            if time.monotonic_ns() >= job['timing']['worker_deadline_ns']:
                from research.near_quarter_packed_state import PackedStop
                raise PackedStop('soft_deadline')
        # No target module or optional solver import precedes source authority.
        check()
        source_check(job['sources'], check)
        from research import near_quarter_rowbatch_checkpoint as codec
        from research.near_quarter_rowbatch_core import PackedRowBatchCore, COUNTERS, FOUND, EXHAUSTED
        from research.near_quarter_packed_state import PackedStop
        from src.near_quarter_model import orbit_map
        token = job['lease_token']
        lease = codec.ChainLease.borrow_for_worker(job['chain_dir'],
            expected_parent=bytes.fromhex(token['expected_parent']), chain_id=bytes.fromhex(job['chain_id']),
            nonce=bytes.fromhex(token['owner_nonce']), device=token['device'], inode=token['inode'])
        def publication_check():
            check()
            lease.verify()
        core = candidate = witness_sha = event_sha = manifest = None
        complete = physical_complete = False
        before = 0
        status, error = 'worker_error', None
        elapsed = {}
        try:
            d, o, r = parse_declaration(job['declaration'], job['n'])
            phase_start = time.monotonic_ns()
            if job['accepted_record'] is None:
                core = PackedRowBatchCore(job['n'], diagonal_order=d, orbit_order=o, row_order=r, check=check)
            else:
                record = job['accepted_record']
                core = codec.read_checkpoint(Path(job['chain_dir'])/(record['checkpoint_sha256']+'.nqrb'),
                    trusted_record=codec.TrustedRecord(bytes.fromhex(record['checkpoint_sha256']),
                        bytes.fromhex(record['checkpoint_parent_sha256']), bytes.fromhex(job['chain_id'])),
                    expected_identity=bytes.fromhex(record['identity_hex']), check=check)
                if core.permutation_bytes() != base64.b64decode(job['declaration']):
                    raise ValueError('resume declaration differs')
            manifest = codec.identity(core, check).hex()
            complete = physical_complete = True
            before = core.counts['nodes']
            elapsed['construct_restore'] = time.monotonic_ns()-phase_start
            # Frozen oracle and packed order are compared only in this child.
            phase_start = time.monotonic_ns()
            oracle = orbit_map(job['n'])
            check()
            packed = tuple(core.state.model['orbits'])
            if tuple(oracle['orbits']) != packed:
                raise ValueError('ordered orbit map differs from frozen oracle')
            map_sha = sha(canonical(oracle['orbits']))
            if map_sha != job['expected_map_json_sha256']:
                raise ValueError('historical ordered JSON orbit map differs')
            if core.source_hashes != tuple(bytes.fromhex(job['sources'][name]) for name in SOURCE_NAMES[:7]):
                raise ValueError('checkpoint source slots differ')
            del oracle, packed
            elapsed['map_check'] = time.monotonic_ns()-phase_start
            phase_start = time.monotonic_ns()
            if job['operation'] == 'construct':
                status = 'constructed'
            elif job['operation'] == 'root':
                core.step(check=check)
                status = 'root_ready_no_search'
            else:
                def on_leaf(_selected, _digest):
                    nonlocal witness_sha, event_sha
                    witness = make_witness(core, map_sha, check)
                    data = canonical(witness)
                    source_check(job['sources'], check)
                    publish(lease.directory, data, cap=JSON_CAP, suffix='.witness.json', check=publication_check)
                    witness_sha, event_sha = sha(data), witness['event_sha256']
                outcome = core.run(job['max_new_nodes'], check=check, on_leaf=on_leaf)
                # A resumed terminal is revalidated and delivered without recount.
                if core.outer == FOUND and witness_sha is None:
                    on_leaf(None, None)
                status = {'node_limit': 'node_limit_checkpointed', 'found': 'verified_witness',
                          'declared_slices_exhausted': 'slices_exhausted'}[outcome]
            elapsed['operation'] = time.monotonic_ns()-phase_start
            check()
            source_check(job['sources'], check)
            phase_start = time.monotonic_ns()
            # Failed private validation has unreturned work. Do not claim an
            # exact aggregate unless the entire save returns successfully.
            physical_complete = False
            _, record = codec.save_candidate(core, lease=lease, check=check)
            physical_complete = True
            candidate = record.content_sha256.hex()
            elapsed['save_validation_publication'] = time.monotonic_ns()-phase_start
            source_check(job['sources'], check)
            check()
        except PackedStop as exc:
            status = 'cancelled' if str(exc) == 'cancelled' else 'soft_deadline'
            error = str(exc)
        except Exception as exc:
            status = 'worker_error'
            error = (type(exc).__name__+': '+str(exc)).encode('utf-8')[:512].decode('utf-8', 'ignore')
        try:
            physical = physical_counters(core) if physical_complete else None
            report = {'schema': 1, 'stage_id': job['stage_id'], 'job_sha256': expected_sha,
                'chain_id': job['chain_id'], 'operation': job['operation'], 'n': job['n'], 'adapter': 2,
                'mode': 1, 'source_manifest': job['sources'], 'identity_sha256': sha(bytes.fromhex(manifest)) if manifest else None,
                'identity_hex': manifest, 'expected_parent': token['expected_parent'],
                'candidate_sha256': candidate, 'status': status, 'outer': core.outer if complete else None,
                'top_phase': core.frames[-1].phase if complete and core.frames else None,
                'nodes_before': before if complete else None,
                'new_nodes': core.counts['nodes']-before if complete else None,
                'nodes_total': core.counts['nodes'] if complete else None,
                'completed_slices': core.slice_index if complete else None, 'declared_slices': len(d),
                'event_sha256': event_sha, 'witness_sha256': witness_sha, 'physical': physical,
                'physical_counters_complete': physical_complete, 'domain_counters': dict(core.work) if complete else None,
                'elapsed_ns': {**elapsed, 'child_through_report_preparation': time.monotonic_ns()-started}, 'error': error}
            # Eligible publication stays under the common deadline. A small
            # failure report may survive expiry but conveys no acceptance.
            final_check = publication_check if status in ELIGIBLE else lease.verify
            source_check(job['sources'], final_check)
            publish(stage_dir, canonical(report), cap=JSON_CAP, name='report.json', check=final_check)
            return 0 if status in ELIGIBLE else 2
        finally:
            lease.close_keep_lease()


def validate_physical(value, complete):
    if type(complete) is not bool:
        raise ValueError('counter completeness type')
    if not complete:
        if value is not None:
            raise ValueError('unknown physical work must be null')
        return
    keys(value, PHYSICAL_KEYS)
    for group in value.values():
        keys(group, STATE_COUNTERS)
        for v in group.values():
            integer(v)
    for k in STATE_COUNTERS:
        if (value['restore_subset'][k]+value['traversal'][k] != value['state_total'][k] or
                value['state_total'][k]+value['validation_extra'][k] != value['physical_total'][k]):
            raise ValueError('physical disjoint counter relation')


def validate_witness(raw, expected_sha, job, parsed, event_sha):
    if sha(raw) != expected_sha:
        raise ValueError('witness content hash')
    w = keys(strict_json(raw), WITNESS_KEYS)
    integer(w['schema'], 1, 1)
    integer(w['n'], job['n'], job['n'])
    if w['family'] != FAMILY or w['map_json_sha256'] != job['expected_map_json_sha256']:
        raise ValueError('witness family/map')
    n, m, four = job['n'], job['n']//2, (job['n']//2)**2
    ids, points = w['orbit_ids'], w['points']
    if type(ids) is not list or len(ids) != m+1:
        raise ValueError('witness ID count')
    for value in ids:
        integer(value, 1, four+m)
    if ids != sorted(set(ids)) or sum(v <= four for v in ids) != m or sum(v > four for v in ids) != 1:
        raise ValueError('witness ID family/type')
    selected = [parsed.diagonals[parsed.slice_index]]+[v for frame in parsed.frames for v in frame.incoming]
    if sorted(selected) != ids:
        raise ValueError('witness selected path differs')
    if type(points) is not list or len(points) != 2*n:
        raise ValueError('witness point count')
    for point in points:
        if type(point) is not list or len(point) != 2:
            raise ValueError('witness coordinate shape')
        for coordinate in point:
            integer(coordinate, 0, n-1)
    if points != sorted(points) or len(set(map(tuple, points))) != len(points):
        raise ValueError('witness point order/uniqueness')
    normalized = sha(canonical({'n': n, 'points': points}))
    expected_event = event_digest(n, points, ids, job['expected_map_json_sha256'])
    if w['event_sha256'] != expected_event or event_sha != expected_event:
        raise ValueError('witness event differs')
    if type(w['checks']) is not list or len(w['checks']) != 2:
        raise ValueError('two verifier summaries required')
    for report, algorithm in zip(w['checks'], ('integer_normalized_slopes', 'integer_cross_products')):
        keys(report, ('algorithm', 'valid', 'point_count', 'normalized_sha256'))
        integer(report['point_count'], 2*n, 2*n)
        if report['algorithm'] != algorithm or report['valid'] is not True or report['normalized_sha256'] != normalized:
            raise ValueError('verifier summary differs')
    return w


def validate_report(raw, job, job_sha, prior, check=lambda: None):
    """Cheap bounded parent checks only; no broad-grid construction/replay."""
    from research import near_quarter_rowbatch_checkpoint as codec
    from research.near_quarter_rowbatch_core import BETWEEN, ACTIVE, EXHAUSTED, FOUND, ENTER, LEAF
    report = keys(strict_json(raw), REPORT_KEYS)
    integer(report['schema'], 1, 1)
    for name, expected in (('stage_id', job['stage_id']), ('job_sha256', job_sha),
        ('chain_id', job['chain_id']), ('operation', job['operation']), ('n', job['n']),
        ('adapter', 2), ('mode', 1), ('source_manifest', job['sources']),
        ('expected_parent', job['lease_token']['expected_parent'])):
        if report[name] != expected or (type(expected) is int and type(report[name]) is not int):
            raise ValueError('report authority differs: '+name)
    if report['status'] not in STATUS:
        raise ValueError('unknown report status')
    if report['error'] is not None and (type(report['error']) is not str or len(report['error'].encode('utf-8')) > 512):
        raise ValueError('bounded report error')
    validate_physical(report['physical'], report['physical_counters_complete'])
    if type(report['elapsed_ns']) is not dict or not set(report['elapsed_ns']) <= {
        'construct_restore', 'map_check', 'operation', 'save_validation_publication', 'child_through_report_preparation'}:
        raise ValueError('report timing fields')
    for v in report['elapsed_ns'].values():
        integer(v)
    if report['outer'] is not None:
        integer(report['outer'], 1, 4)
    if report['top_phase'] is not None:
        integer(report['top_phase'], 1, 7)
    if report['status'] not in ELIGIBLE:
        return report, None
    if not report['physical_counters_complete'] or report['error'] is not None:
        raise ValueError('eligible report has incomplete work/error')
    keys(report['domain_counters'], DOMAIN_COUNTERS)
    for v in report['domain_counters'].values():
        integer(v)
    for k in ('nodes_before', 'new_nodes', 'nodes_total', 'completed_slices', 'declared_slices'):
        integer(report[k])
    if report['nodes_before']+report['new_nodes'] != report['nodes_total'] or report['new_nodes'] > job['max_new_nodes']:
        raise ValueError('logical node delta/cap')
    if prior['checkpoint_sha256'] == ZERO_HEX:
        if report['nodes_before'] != 0:
            raise ValueError('fresh logical node baseline')
    else:
        previous_raw = read_bounded(Path(job['chain_dir'])/(prior['checkpoint_sha256']+'.nqrb'), codec.MAX_V1_BYTES, check)
        previous = codec.parse(previous_raw, trusted_record=codec.TrustedRecord(
            bytes.fromhex(prior['checkpoint_sha256']), bytes.fromhex(prior['checkpoint_parent_sha256']),
            bytes.fromhex(job['chain_id'])), expected_identity=bytes.fromhex(prior['identity_hex']), check=check)
        if previous.counts[0] != report['nodes_before']:
            raise ValueError('accepted logical node baseline')
    h = hexstr(report['candidate_sha256'], zero=False)
    ident = bytes.fromhex(hexstr(report['identity_hex'], 1024, zero=False))
    if sha(ident) != report['identity_sha256']:
        raise ValueError('report identity hash')
    if ident[9:11] != bytes((2, 1)) or ident[80:304] != b''.join(bytes.fromhex(job['sources'][k]) for k in SOURCE_NAMES[:7]):
        raise ValueError('adapter/source identity slots')
    from research.near_quarter_rowbatch_core import digest
    if ident[48:80] != digest('NQRB-PERMS-v1', base64.b64decode(job['declaration'])):
        raise ValueError('declaration identity digest')
    if prior['identity_hex'] is not None and prior['identity_hex'] != report['identity_hex']:
        raise ValueError('resume identity changed')
    data = read_bounded(Path(job['chain_dir'])/(h+'.nqrb'), codec.MAX_V1_BYTES, check)
    parsed = codec.parse(data, trusted_record=codec.TrustedRecord(bytes.fromhex(h),
        bytes.fromhex(report['expected_parent']), bytes.fromhex(job['chain_id'])), expected_identity=ident, check=check)
    if (parsed.n != job['n'] or parsed.counts[0] != report['nodes_total'] or parsed.outer != report['outer'] or
            (parsed.frames[-1].phase if parsed.frames else None) != report['top_phase'] or
            parsed.slice_index != report['completed_slices'] or len(parsed.diagonals) != report['declared_slices'] or
            (parsed.diagonals, parsed.orbits, parsed.rows) != parse_declaration(job['declaration'], job['n'])):
        raise ValueError('report/candidate control differs')
    status = report['status']
    if job['operation'] == 'construct':
        if status != 'constructed' or parsed.outer not in (BETWEEN, EXHAUSTED) or parsed.frames or parsed.counts != (0,)*7:
            raise ValueError('construct performed search')
    elif job['operation'] == 'root':
        if (status != 'root_ready_no_search' or parsed.outer != ACTIVE or len(parsed.frames) != 1 or
                parsed.frames[0].phase != ENTER or parsed.counts != (0,)*7 or parsed.slice_index != 0):
            raise ValueError('root performed search')
    elif status not in ('node_limit_checkpointed', 'slices_exhausted', 'verified_witness'):
        raise ValueError('stage status differs')
    if status == 'slices_exhausted' and parsed.outer != EXHAUSTED:
        raise ValueError('false declared exhaustion')
    if status == 'node_limit_checkpointed' and (parsed.outer not in (BETWEEN, ACTIVE) or
            report['new_nodes'] != job['max_new_nodes']):
        raise ValueError('false node limit')
    if status == 'verified_witness':
        if parsed.outer != FOUND or parsed.frames[-1].phase != LEAF:
            raise ValueError('false terminal')
        wh = hexstr(report['witness_sha256'], zero=False)
        eh = hexstr(report['event_sha256'], zero=False)
        validate_witness(read_bounded(Path(job['chain_dir'])/(wh+'.witness.json'), JSON_CAP, check), wh, job, parsed, eh)
    elif report['witness_sha256'] is not None or report['event_sha256'] is not None:
        raise ValueError('nonterminal witness claim')
    return report, parsed


def validate_gate(gate, seconds, rss_mib):
    keys(gate, ('gate_status', 'trigger_gate_status', 'returncode', 'elapsed_seconds',
        'rss_samples', 'monitor_error', 'seconds_limit', 'rss_limit_mib', 'cleanup_status',
        'cleanup_error', 'cleanup_samples', 'cleanup_elapsed_seconds',
        'peak_sampled_rss_kib', 'rss_scope', 'gate_semantics'))
    for name in ('rss_samples', 'cleanup_samples', 'peak_sampled_rss_kib'):
        integer(gate[name], 1)
    for name in ('elapsed_seconds', 'seconds_limit', 'rss_limit_mib', 'cleanup_elapsed_seconds'):
        value = gate[name]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('invalid helper measurement')
    if (gate['gate_status'] != 'exited' or gate['trigger_gate_status'] is not None or
        type(gate['returncode']) is not int or gate['returncode'] != 0 or
        gate['monitor_error'] is not None or gate['cleanup_status'] != 'clean' or
        gate['cleanup_error'] is not None or not 0 < gate['seconds_limit'] <= seconds or
        gate['rss_limit_mib'] != rss_mib or gate['elapsed_seconds'] >= gate['seconds_limit'] or
        gate['peak_sampled_rss_kib'] > rss_mib*1024 or
        gate['rss_scope'] != 'guard parent plus spawned process group and observed descendants; native heap included' or
        gate['gate_semantics'] != 'sampled RSS gate; cleanup included in wall gate; possible sampling overshoot; transient ps excluded'):
        raise ValueError('owned resource/cleanup gate failed')


def validate_receipt(raw, *, head=None, sources=None):
    receipt = keys(strict_json(raw, RECEIPT_CAP), RECEIPT_KEYS)
    integer(receipt['schema'], 1, 1)
    hexstr(receipt['stage_id'], 32, zero=False)
    hexstr(receipt['job_sha256'], zero=False)
    hexstr(receipt['chain_id'], zero=False)
    validate_head(receipt['prior_accepted_record'])
    keys(receipt['source_manifest'], SOURCE_NAMES)
    for h in receipt['source_manifest'].values():
        hexstr(h, zero=False)
    for name in ('report_sha256', 'candidate_sha256', 'witness_sha256', 'event_sha256', 'observed_candidate_sha256'):
        if receipt[name] is not None:
            hexstr(receipt[name], zero=False)
    for name in ('search_complete', 'search_performed'):
        if type(receipt[name]) is not bool:
            raise ValueError('receipt boolean type')
    validate_physical(receipt['physical'], receipt['physical_counters_complete'])
    keys(receipt['timing'], ('invocation_started_ns', 'precommit_cutoff_ns', 'precommit_deadline_ns',
        'setup_ns', 'through_precommit_ns', 'postprocessing_ns'))
    for v in receipt['timing'].values():
        integer(v)
    if type(receipt['timing_scope']) is not str or len(receipt['timing_scope']) > 512:
        raise ValueError('receipt timing scope')
    reasons = receipt['rejection_reasons']
    if (type(reasons) is not list or len(reasons) > 8 or
            any(type(v) is not str or len(v.encode('utf-8')) > 512 for v in reasons)):
        raise ValueError('bounded rejection reasons')
    if receipt['result'] == 'eligible':
        if (reasons or receipt['candidate_sha256'] is None or receipt['report_sha256'] is None or
                receipt['proposed_status'] not in ELIGIBLE or not receipt['physical_counters_complete'] or
                receipt['timing']['precommit_cutoff_ns'] >= receipt['timing']['precommit_deadline_ns']):
            raise ValueError('eligible receipt relations')
    elif receipt['result'] == 'rejected':
        if (not reasons or any(receipt[k] is not None for k in
                ('candidate_sha256', 'witness_sha256', 'event_sha256', 'proposed_status')) or
                receipt['search_complete'] or receipt['search_performed']):
            raise ValueError('rejected receipt claims')
    else:
        raise ValueError('receipt result')
    if head is not None:
        if (receipt['result'] != 'eligible' or sha(raw) != head['last_receipt_sha256'] or
            receipt['stage_id'] != head['last_stage_id'] or receipt['job_sha256'] != head['last_job_sha256'] or
            receipt['chain_id'] != head['chain_id'] or receipt['candidate_sha256'] != head['checkpoint_sha256'] or
            receipt['prior_accepted_record']['checkpoint_sha256'] != head['checkpoint_parent_sha256'] or
            receipt['witness_sha256'] != head['witness_sha256'] or receipt['event_sha256'] != head['event_sha256']):
            raise ValueError('accepted receipt/HEAD authority differs')
    if sources is not None and receipt['source_manifest'] != sources:
        raise ValueError('accepted nine-source identity differs; fresh derivation required')
    return receipt


def _read_head(directory, check=lambda: None):
    raw = read_bounded(Path(directory)/'accepted.json', HEAD_CAP, check)
    return raw, validate_head(strict_json(raw, HEAD_CAP))


def _commit_head(directory, raw, lease, fault):
    """Once replace is attempted, any uncertain outcome conservatively retains lease."""
    lease.verify()
    temp = Path(directory)/('.head-'+secrets.token_hex(16))
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    attempted = False
    try:
        write_all(fd, raw, lease.verify)
        os.fsync(fd)
        os.close(fd)
        fd = None
        fault('before_head_replace')
        lease.verify()
        attempted = True
        os.replace(temp, Path(directory)/'accepted.json')
        fault('after_head_replace')
        fsync_dir(directory)
        fault('after_head_directory_fsync')
        return 'accepted'
    except Exception:
        if attempted:
            return 'acceptance_uncertain'
        raise
    finally:
        if fd is not None:
            os.close(fd)
        if temp.exists():
            os.unlink(temp)


def run_stage(chain_dir, *, stage_id, operation, n, declaration_b64, expected_map_json_sha256,
              expected_parent=ZERO_HEX, max_new_nodes=0, seconds=5, rss_mib=256,
              fault=lambda _: None, _guard=None):
    """One explicit invocation. No host allocation is implied by this API.

    _guard is a tiny/fault-test boundary. Production uses only the unchanged
    owned helper. Complete timing extends through HEAD durability/lease close;
    the immutable receipt stops at the precommit eligibility cutoff.
    """
    started = time.monotonic_ns()
    hexstr(stage_id, 32, zero=False)
    hexstr(expected_parent)
    hexstr(expected_map_json_sha256, zero=False)
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 2 < seconds <= 30:
        raise ValueError('guard duration requires at least2s reserve and <=30s')
    if type(rss_mib) not in (int, float) or not math.isfinite(rss_mib) or not 0 < rss_mib <= 256:
        raise ValueError('RSS cap')
    # Narrow imports allocate no grid geometry.
    from research import near_quarter_rowbatch_checkpoint as codec
    from research.owned_process_guard import guarded_process
    directory = Path(chain_dir).absolute()
    fresh = not directory.exists()
    if directory.is_symlink():
        raise ValueError('symlink chain directory')
    if fresh:
        directory.mkdir(mode=0o700)
    directory = directory.resolve()
    sources = source_manifest()
    if fresh:
        genesis = {'schema': 1, 'chain_id': secrets.token_hex(32), 'checkpoint_sha256': ZERO_HEX,
            'checkpoint_parent_sha256': ZERO_HEX, 'identity_hex': None, 'last_stage_id': None,
            'last_job_sha256': ZERO_HEX, 'last_receipt_sha256': ZERO_HEX,
            'map_json_sha256': expected_map_json_sha256, 'witness_sha256': None, 'event_sha256': None}
        publish(directory, canonical(genesis), cap=HEAD_CAP, name='accepted.json')
    # Read only to learn the chain ID. Authority is reread under the acquired lease.
    _, initial = _read_head(directory)
    lease = codec.ChainLease(directory, expected_parent=bytes.fromhex(expected_parent),
                             chain_id=bytes.fromhex(initial['chain_id']))
    lease.__enter__()
    retain, result, receipt_sha = False, None, None
    try:
        with Cancellation() as cancellation:
            prior_raw, prior = _read_head(directory)
            if prior['checkpoint_sha256'] != ZERO_HEX:
                validate_receipt(read_bounded(directory/(prior['last_receipt_sha256']+'.receipt.json'), RECEIPT_CAP),
                                 head=prior, sources=sources)
            stage_dir = directory/('stage-'+stage_id)
            requested = {'operation': operation, 'n': n, 'declaration': declaration_b64,
                'expected_map_json_sha256': expected_map_json_sha256, 'max_new_nodes': max_new_nodes,
                'sources': sources, 'limits': {'guard_seconds': seconds, 'rss_mib': rss_mib}}
            if prior['last_stage_id'] == stage_id:
                # Idempotence precedes launch and requires original parent/job/receipt.
                old_raw = read_bounded(stage_dir/'job.json', JSON_CAP)
                old = validate_job(strict_json(old_raw))
                if (old['lease_token']['expected_parent'] != expected_parent or
                    any(old[k] != v for k, v in requested.items()) or sha(old_raw) != prior['last_job_sha256']):
                    raise ValueError('different duplicate stage request')
                receipt_raw = read_bounded(directory/(prior['last_receipt_sha256']+'.receipt.json'), RECEIPT_CAP)
                if sha(receipt_raw) != prior['last_receipt_sha256']:
                    raise ValueError('committed receipt hash differs')
                receipt = validate_receipt(receipt_raw, head=prior, sources=sources)
                if (receipt['result'] != 'eligible' or receipt['candidate_sha256'] != prior['checkpoint_sha256'] or
                        receipt['stage_id'] != stage_id or receipt['job_sha256'] != prior['last_job_sha256']):
                    raise ValueError('committed receipt differs')
                result, receipt_sha = 'accepted_idempotent', prior['last_receipt_sha256']
            else:
                if prior['checkpoint_sha256'] != expected_parent or prior['map_json_sha256'] != expected_map_json_sha256:
                    raise ValueError('stale parent/map')
                if operation != 'stage' and expected_parent != ZERO_HEX:
                    raise ValueError('construct/root require fresh chain')
                stage_dir.mkdir(mode=0o700)  # Existing stage is never automatically retried.
                precommit = started+int(seconds*1e9)
                worker_deadline = precommit-2_000_000_000
                job = {'schema': 1, 'stage_id': stage_id, 'chain_id': prior['chain_id'],
                    **{k: requested[k] for k in ('operation', 'n', 'max_new_nodes')},
                    'target': 2*n, 'adapter': 2, 'leaf_mode': 1, 'chain_dir': str(directory),
                    'accepted_record': accepted_job_record(prior), 'declaration': declaration_b64,
                    'expected_map_json_sha256': expected_map_json_sha256, 'sources': sources,
                    'lease_token': {'owner_nonce': lease.nonce.hex(), 'device': lease.stat.st_dev,
                        'inode': lease.stat.st_ino, 'expected_parent': expected_parent},
                    'timing': {'invocation_started_ns': started, 'worker_deadline_ns': worker_deadline,
                        'precommit_deadline_ns': precommit}, 'limits': requested['limits']}
                validate_job(job)
                job_raw = canonical(job)
                publish(stage_dir, job_raw, cap=JSON_CAP, name='job.json', check=lease.verify)
                job_sha = sha(job_raw)
                setup_finished = time.monotonic_ns()
                remaining = (precommit-setup_finished)/1e9
                guard = _guard or guarded_process
                gate = None
                report = None
                reasons = []
                parsed = None
                guard_invoked = False
                try:
                    if cancellation.cancelled or setup_finished >= worker_deadline or remaining <= 0:
                        raise ValueError('setup cancelled/worker deadline elapsed')
                    guard_invoked = True
                    retain = True  # Unknown cleanup stays conservative, including raised helpers.
                    gate = guard([sys.executable, '-m', 'research.near_quarter_packed_worker', '--worker',
                                  str(stage_dir/'job.json'), job_sha], min(seconds, remaining), rss_mib,
                                 stage_dir/'worker.log', cancelled=lambda: cancellation.cancelled)
                    if (type(gate) is dict and gate.get('cleanup_status') == 'clean' and
                            gate.get('cleanup_error') is None and type(gate.get('cleanup_samples')) is int and
                            gate['cleanup_samples'] > 0):
                        retain = False
                    validate_gate(gate, min(seconds, remaining), rss_mib)
                    log_fd = os.open(stage_dir/'worker.log', os.O_RDONLY | os.O_NOFOLLOW)
                    try:
                        info = os.fstat(log_fd)
                        if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
                            raise ValueError('worker log bound/type')
                        os.lseek(log_fd, max(0, info.st_size-4096), os.SEEK_SET)
                        os.read(log_fd, 4096)  # Bounded diagnostic tail; never parse as authority.
                    finally:
                        os.close(log_fd)
                    source_check(sources)
                    report_raw = read_bounded(stage_dir/'report.json', JSON_CAP)
                    report, parsed = validate_report(report_raw, job, job_sha, prior)
                    if report['status'] not in ELIGIBLE:
                        raise ValueError('worker report ineligible')
                    if _read_head(directory)[0] != prior_raw:
                        raise ValueError('accepted parent changed')
                    lease.verify()
                    source_check(sources)
                    fault('before_precommit')
                    # Explicit last eligibility boundary. Subsequent durable I/O
                    # has no hard wall promise and does not rewrite this cutoff.
                    decision_time = time.monotonic_ns()
                    if cancellation.cancelled or decision_time >= precommit:
                        raise ValueError('cancelled/expired before eligibility')
                except Exception as exc:
                    if guard_invoked and gate is None:
                        retain = True
                    reasons.append((type(exc).__name__+': '+str(exc))[:512])
                cutoff = time.monotonic_ns() if reasons else decision_time
                eligible = not reasons
                receipt = {'schema': 1, 'stage_id': stage_id, 'job_sha256': job_sha,
                    'chain_id': prior['chain_id'], 'prior_accepted_record': prior,
                    'source_manifest': sources, 'report_sha256': sha(report_raw) if report is not None else None,
                    'candidate_sha256': report['candidate_sha256'] if eligible else None,
                    'witness_sha256': report['witness_sha256'] if eligible else None,
                    'event_sha256': report['event_sha256'] if eligible else None,
                    'search_complete': eligible and report['status'] == 'slices_exhausted',
                    'search_performed': eligible and operation == 'stage',
                    'proposed_status': report['status'] if eligible else None,
                    'observed_candidate_sha256': report['candidate_sha256'] if report else None,
                    'physical_counters_complete': report['physical_counters_complete'] if report else False,
                    'physical': report['physical'] if report else None, 'gate': gate,
                    'timing': {'invocation_started_ns': started, 'precommit_cutoff_ns': cutoff,
                        'precommit_deadline_ns': precommit, 'setup_ns': setup_finished-started,
                        'through_precommit_ns': cutoff-started,
                        'postprocessing_ns': max(0, cutoff-setup_finished-int((gate or {}).get('elapsed_seconds', 0)*1e9))},
                    'timing_scope': 'receipt ends at precommit eligibility; setup/postprocessing outside sampled helper; '
                        'durable receipt/HEAD coordination may exceed30s; final return measures through lease release',
                    'result': 'eligible' if eligible else 'rejected', 'rejection_reasons': reasons}
                receipt_raw = canonical(receipt)
                validate_receipt(receipt_raw, sources=sources)
                publish(directory, receipt_raw, cap=RECEIPT_CAP, suffix='.receipt.json', check=lease.verify)
                receipt_sha = sha(receipt_raw)
                result = 'rejected'
                if eligible:
                    if _read_head(directory)[0] != prior_raw:
                        raise ValueError('accepted parent changed before commit')
                    head = {'schema': 1, 'chain_id': prior['chain_id'],
                        'checkpoint_sha256': report['candidate_sha256'], 'checkpoint_parent_sha256': expected_parent,
                        'identity_hex': report['identity_hex'], 'last_stage_id': stage_id,
                        'last_job_sha256': job_sha, 'last_receipt_sha256': receipt_sha,
                        'map_json_sha256': expected_map_json_sha256,
                        'witness_sha256': report['witness_sha256'], 'event_sha256': report['event_sha256']}
                    validate_head(head)
                    # Any exception during commit, including temp cleanup,
                    # must preserve ownership until explicit reconciliation.
                    retain = True
                    result = _commit_head(directory, canonical(head), lease, fault)
                    retain = result == 'acceptance_uncertain'
    except BaseException:
        # A helper that raised offers no verified cleanup result.
        if 'gate' in locals() and gate is None and 'setup_finished' in locals():
            retain = True
        raise
    finally:
        if retain:
            lease.close_keep_lease()
        else:
            lease.release()
    finished = time.monotonic_ns()
    return {'result': result, 'receipt_sha256': receipt_sha, 'stage_id': stage_id,
            'lease_retained': retain, 'invocation_started_ns': started,
            'coordination_finished_ns': finished, 'complete_invocation_ns': finished-started,
            'timing_scope': 'through durable HEAD outcome and lease close/release; excludes return serialization/caller receipt'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', nargs=2, metavar=('JOB_PATH', 'EXPECTED_SHA256'))
    parser.add_argument('--request', help='bounded canonical supervisor request JSON')
    args = parser.parse_args(argv)
    if bool(args.worker) == bool(args.request):
        parser.error('choose private worker or explicit supervisor request')
    if args.worker:
        return worker_main(*args.worker)
    request = strict_json(read_bounded(args.request, JSON_CAP))
    keys(request, ('chain_dir', 'stage_id', 'operation', 'n', 'declaration_b64',
                   'expected_map_json_sha256', 'expected_parent', 'max_new_nodes', 'seconds', 'rss_mib'))
    print(canonical(run_stage(**request)).decode('ascii'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
