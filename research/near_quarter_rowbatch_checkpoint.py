"""Fixed near-quarter row-batch v1 wire codec and private hard-tiny replay.

No accepted-frontier pointer, CLI, process wrapper or production state adapter.
"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import secrets
import stat
import struct

from src.near_quarter_model import check_candidate
from research.near_quarter_rowbatch_cursor import Cursor, NONE, END
from research.near_quarter_rowbatch_core import (
    Frame, TinyRowBatchCore, ZERO, COUNTERS, BETWEEN, ACTIVE, EXHAUSTED, FOUND,
    ENTER, COUNTED, READY, PENDING, WAITING, LEAF, DONE,
    DRAINED, ORBIT_SHORTFALL, ROW_SHORTFALL, TARGET_NONLEAF, TINY_LEAF)

MAGIC = b'NQRBCK01'
MAX_WIRE_BYTES = 1_048_576
MAX_V1_BYTES = 7868
IDENTITY_BYTES = 512
FRAME_BYTES = 96


def grid_bounds(n):
    if type(n) is not int or not 3 <= n <= 79 or n % 2 != 1:
        raise ValueError('schema permits odd grids3..79')
    m = n//2
    return m, m*m, m+m*m, m+1


def require_digest(value, *, nonzero=False):
    if type(value) is not bytes or len(value) != 32 or (nonzero and value == ZERO):
        raise ValueError('expected fixed32-byte digest')
    return value


@dataclass(frozen=True)
class TrustedRecord:
    content_sha256: bytes
    parent_content_sha256: bytes
    chain_id: bytes

    def __post_init__(self):
        require_digest(self.content_sha256, nonzero=True)
        require_digest(self.parent_content_sha256)
        require_digest(self.chain_id, nonzero=True)


@dataclass(frozen=True)
class ParsedFrontier:
    identity: bytes
    parent_hash: bytes
    chain_id: bytes
    n: int
    leaf_mode: int
    adapter: int
    outer: int
    slice_index: int
    counts: tuple
    diagonals: tuple
    orbits: tuple
    rows: tuple
    frames: tuple


def identity(core, check=lambda: None):
    core.check_sources(check)
    out = bytearray(512)
    struct.pack_into('>HHHH', out, 0, 1, core.n, core.m, 2*core.n)
    out[8:15] = bytes((1, 1, core.leaf_mode, 1, 1, 1, 1))
    out[16:48], out[48:80] = core.map_digest, core.perm_digest
    for i, source in enumerate(core.source_hashes):
        out[80+32*i:112+32*i] = source
    return bytes(out)


def _identity_shape(raw):
    if type(raw) is not bytes or len(raw) != 512:
        raise ValueError('identity must have exactly512 bytes')
    version, n, m, target = struct.unpack_from('>HHHH', raw)
    expected_m, four, total, depth = grid_bounds(n)
    if (version != 1 or m != expected_m or target != 2*n or raw[8] != 1 or
            raw[9] not in (1, 2) or raw[10] not in (1, 2) or
            raw[11:15] != bytes((1, 1, 1, 1)) or raw[15] or any(raw[304:])):
        raise ValueError('identity tags/reserved/grid mismatch')
    if (raw[9] == 1 and n not in (3, 5, 7)) or (raw[10] == 2 and raw[9] != 1):
        raise ValueError('adapter/leaf mode outside scope')
    if any(raw[i:i+32] == ZERO for i in range(16, 304, 32)):
        raise ValueError('zero identity digest')
    return n, m, four, total, depth


def _cursor_pack(out, offset, cursor):
    if type(cursor) is not Cursor or any(type(v) is not int for v in (cursor.kind, cursor.i, cursor.j)):
        raise ValueError('invalid cursor types')
    if not (0 <= cursor.kind <= 3 and 0 <= cursor.i <= 1520 and 0 <= cursor.j <= 1520):
        raise ValueError('cursor wire range')
    if cursor.kind in (0, 3) and (cursor.i or cursor.j):
        raise ValueError('invalid cursor sentinel')
    if cursor.kind == 1 and cursor.j:
        raise ValueError('invalid singleton sentinel')
    if cursor.kind == 2 and not cursor.i < cursor.j:
        raise ValueError('invalid pair indices')
    struct.pack_into('>BHH', out, offset, cursor.kind, cursor.i, cursor.j)


def _frame_bytes(frame):
    if type(frame) is not Frame:
        raise ValueError('expected rowbatch frame')
    fields = (frame.phase, frame.row, frame.deficit, frame.domain_length, frame.close_reason)
    if (any(type(v) is not int for v in fields) or not 1 <= frame.phase <= 7 or
            not 0 <= frame.row < 79 or not 0 <= frame.deficit <= 2 or
            not 0 <= frame.domain_length <= 1521 or not 0 <= frame.close_reason <= 5):
        raise ValueError('frame scalar bounds')
    for batch in (frame.incoming, frame.pending):
        if (type(batch) is not tuple or len(batch) > 2 or
                any(type(v) is not int or not 1 <= v <= 1560 for v in batch) or len(set(batch)) != len(batch)):
            raise ValueError('invalid bounded frame batch')
    require_digest(frame.domain_digest)
    require_digest(frame.leaf_digest)
    out = bytearray(96)
    out[0], out[1] = frame.phase, len(frame.incoming)
    for i, value in enumerate(frame.incoming):
        struct.pack_into('>H', out, 2+2*i, value)
    _cursor_pack(out, 6, frame.origin)
    struct.pack_into('>HBH', out, 11, frame.row, frame.deficit, frame.domain_length)
    out[16:48] = frame.domain_digest
    _cursor_pack(out, 48, frame.cursor)
    out[53] = len(frame.pending)
    for i, value in enumerate(frame.pending):
        struct.pack_into('>H', out, 54+2*i, value)
    out[58:90], out[90] = frame.leaf_digest, frame.close_reason
    return bytes(out)


def _frame_parse(raw):
    if len(raw) != 96 or any(raw[91:]):
        raise ValueError('frame length/reserved')
    incoming_count, pending_count = raw[1], raw[53]
    if incoming_count > 2 or pending_count > 2:
        raise ValueError('frame batch length')
    incoming_slots = struct.unpack_from('>HH', raw, 2)
    pending_slots = struct.unpack_from('>HH', raw, 54)
    if any(incoming_slots[incoming_count:]) or any(pending_slots[pending_count:]):
        raise ValueError('nonzero unused batch slots')
    row, deficit, length = struct.unpack_from('>HBH', raw, 11)
    frame = Frame(raw[0], incoming_slots[:incoming_count], Cursor(*struct.unpack_from('>BHH', raw, 6)),
        row, deficit, length, raw[16:48], Cursor(*struct.unpack_from('>BHH', raw, 48)),
        pending_slots[:pending_count], raw[58:90], raw[90])
    if _frame_bytes(frame) != raw:
        raise ValueError('noncanonical frame')
    # Re-encoding the permitted union must reproduce every byte.
    if frame.phase in (ENTER, COUNTED):
        canonical = frame.cleared(frame.phase)
    elif frame.phase in (READY, WAITING, PENDING):
        if frame.deficit not in (1, 2) or frame.domain_digest == ZERO or frame.cursor.kind == NONE:
            raise ValueError('missing active domain')
        if frame.phase == PENDING and (not frame.pending or frame.cursor.kind == END):
            raise ValueError('empty pending candidate')
        canonical = frame.cleared(frame.phase, row=frame.row, deficit=frame.deficit,
            domain_length=frame.domain_length, domain_digest=frame.domain_digest, cursor=frame.cursor,
            pending=frame.pending if frame.phase == PENDING else ())
    elif frame.phase == LEAF:
        if frame.leaf_digest == ZERO:
            raise ValueError('missing leaf digest')
        canonical = frame.cleared(LEAF, leaf_digest=frame.leaf_digest)
    elif frame.phase == DONE:
        reason = frame.close_reason
        if reason == DRAINED:
            if frame.cursor != Cursor(END) or frame.domain_digest == ZERO or frame.deficit not in (1, 2):
                raise ValueError('invalid exhausted frame')
            canonical = frame.cleared(DONE, row=frame.row, deficit=frame.deficit,
                domain_length=frame.domain_length, domain_digest=frame.domain_digest,
                cursor=frame.cursor, close_reason=reason)
        elif reason in (ORBIT_SHORTFALL, TARGET_NONLEAF):
            canonical = frame.cleared(DONE, close_reason=reason)
        elif reason == ROW_SHORTFALL:
            if frame.deficit not in (1, 2):
                raise ValueError('invalid row-prune frame')
            canonical = frame.cleared(DONE, row=frame.row, deficit=frame.deficit, close_reason=reason)
        elif reason == TINY_LEAF:
            if frame.leaf_digest == ZERO:
                raise ValueError('missing acknowledged leaf digest')
            canonical = frame.cleared(DONE, leaf_digest=frame.leaf_digest, close_reason=reason)
        else:
            raise ValueError('missing close reason')
    else:
        raise ValueError('invalid phase')
    if _frame_bytes(canonical) != raw:
        raise ValueError('nonzero inactive phase field')
    return frame


def encode(core, *, parent_hash, chain_id, check=lambda: None):
    if type(core) is not TinyRowBatchCore:
        raise ValueError('reviewed tiny core required')
    m, four, total, depth = grid_bounds(core.n)
    if (len(core.frames) > depth or len(core.diagonals) > m or len(core.orbits) != four or
            len(core.rows) != core.n):
        raise ValueError('in-memory section bounds')
    require_digest(parent_hash)
    require_digest(chain_id, nonzero=True)
    manifest = identity(core, check)
    _identity_shape(manifest)
    check()
    control = bytearray(128)
    struct.pack_into('>BBHHHHH', control, 0, core.outer, 0, core.slice_index,
                     len(core.diagonals), len(core.orbits), len(core.rows), len(core.frames))
    for i, name in enumerate(COUNTERS):
        value = core.counts[name]
        if type(value) is not int or not 0 <= value < 1 << 64:
            raise ValueError('counter wire range')
        struct.pack_into('>Q', control, 12+8*i, value)
    payload = (manifest+parent_hash+chain_id+bytes(control)+
        b''.join(struct.pack('>H', v) for v in (*core.diagonals, *core.orbits, *core.rows))+
        b''.join(_frame_bytes(frame) for frame in core.frames))
    out = MAGIC+struct.pack('>HI', 1, 46+len(payload))+hashlib.sha256(payload).digest()+payload
    # Validate canonical structural shape before returning a candidate blob.
    record = TrustedRecord(hashlib.sha256(out).digest(), parent_hash, chain_id)
    parse(out, trusted_record=record, expected_identity=manifest, check=check)
    return out


def parse(raw, *, trusted_record, expected_identity, check=lambda: None):
    """External raw-byte hash first; bounded structure only, not geometry replay."""
    check()
    if type(trusted_record) is not TrustedRecord:
        raise ValueError('trusted content/parent/chain record required')
    if type(raw) is not bytes or not 750 <= len(raw) <= MAX_WIRE_BYTES:
        raise ValueError('wire type/size bound')
    if hashlib.sha256(raw).digest() != trusted_record.content_sha256:
        raise ValueError('external content hash mismatch')
    check()
    if raw[:8] != MAGIC or struct.unpack_from('>HI', raw, 8) != (1, len(raw)):
        raise ValueError('envelope mismatch')
    if hashlib.sha256(raw[46:]).digest() != raw[14:46]:
        raise ValueError('internal payload hash mismatch')
    manifest = raw[46:558]
    n, m, four, total, depth = _identity_shape(manifest)
    _identity_shape(expected_identity)
    if manifest != expected_identity:
        raise ValueError('source/order/model identity mismatch')
    payload = memoryview(raw)[46:]
    parent, chain = bytes(payload[512:544]), bytes(payload[544:576])
    if parent != trusted_record.parent_content_sha256 or chain != trusted_record.chain_id:
        raise ValueError('trusted parent/chain mismatch')
    outer, reserved, index, d, fc, rc, f = struct.unpack_from('>BBHHHHH', payload, 576)
    if (reserved or any(payload[644:704]) or d > m or fc != four or rc != n or
            f > depth or len(raw) != 46+704+2*(d+four+n)+96*f):
        raise ValueError('control/count/exact-length mismatch')
    if outer in (BETWEEN, EXHAUSTED):
        if f or (outer == BETWEEN and not index < d) or (outer == EXHAUSTED and index != d):
            raise ValueError('empty outer layout mismatch')
    elif outer in (ACTIVE, FOUND):
        if not f or not index < d or (outer == FOUND and manifest[10] != 1):
            raise ValueError('active outer layout mismatch')
    else:
        raise ValueError('unknown outer phase')
    counts = tuple(struct.unpack_from('>Q', payload, 588+8*i)[0] for i in range(7))
    if (counts[3] > counts[2] or counts[1]+sum(counts[4:]) > counts[0] or
            counts[2]-counts[3] < max(0, f-1)):
        raise ValueError('counter relationship mismatch')
    offset = 704
    orders = []
    for length in (d, four, n):
        check()
        orders.append(tuple(struct.unpack_from('>H', payload, offset+2*i)[0] for i in range(length)))
        offset += 2*length
    diagonals, orbits, rows = orders
    if (len(set(diagonals)) != d or not set(diagonals) <= set(range(four+1, total+1)) or
            sorted(orbits) != list(range(1, four+1)) or sorted(rows) != list(range(n))):
        raise ValueError('invalid exact permutation declaration')
    frames = []
    selected = set()
    if f:
        selected.add(diagonals[index])
    for i in range(f):
        check()
        frame = _frame_parse(bytes(payload[offset:offset+96]))
        offset += 96
        if ((i == 0 and (frame.incoming or frame.origin != Cursor(NONE))) or
                (i > 0 and (not frame.incoming or frame.origin.kind not in (1, 2))) or
                (i < f-1 and frame.phase != WAITING) or (i == f-1 and frame.phase == WAITING) or
                frame.row >= n or frame.domain_length > four or
                any(not 1 <= v <= four or v in selected for v in frame.incoming) or
                any(not 1 <= v <= four for v in frame.pending) or
                (frame.close_reason == TINY_LEAF and manifest[10] != 2)):
            raise ValueError('frame/path/phase relation mismatch')
        selected.update(frame.incoming)
        frames.append(frame)
    if len(selected) > m+1 or (outer == FOUND and frames[-1].phase != LEAF):
        raise ValueError('selected bound/FOUND layout mismatch')
    entered = len(frames)-(1 if frames and frames[-1].phase == ENTER else 0)
    if counts[0] < entered:
        raise ValueError('active counts inconsistent')
    if frames:
        top = frames[-1]
        event_counter = 1 if top.phase == LEAF else None
        if top.phase == DONE:
            event_counter = {TINY_LEAF: 1, ORBIT_SHORTFALL: 4,
                             ROW_SHORTFALL: 5, TARGET_NONLEAF: 6}.get(top.close_reason)
        if event_counter is not None and counts[event_counter] == 0:
            raise ValueError('active event counter inconsistent')
    check()
    return ParsedFrontier(manifest, parent, chain, n, manifest[10], manifest[9], outer, index,
                          counts, diagonals, orbits, rows, tuple(frames))


def _restore(parsed, *, check=lambda: None):
    """Privately replay all geometry; no core is returned before complete checks."""
    if type(parsed) is not ParsedFrontier or parsed.adapter != 1:
        raise ValueError('only reviewed tiny replay adapter implemented')
    check()
    core = TinyRowBatchCore(parsed.n, diagonal_order=parsed.diagonals, orbit_order=parsed.orbits,
                            row_order=parsed.rows, leaf_mode=parsed.leaf_mode, check=check)
    if identity(core, check) != parsed.identity:
        raise ValueError('executing source/model identity differs')
    core.restore_mode = True
    if parsed.frames:
        check()
        if not core.state.push(parsed.diagonals[parsed.slice_index]):
            raise ValueError('restored diagonal rejected')
    for i, frame in enumerate(parsed.frames):
        check()
        if i:
            parent = parsed.frames[i-1]
            domain = core._domain(parent, check)
            domain.validate(frame.origin)
            if (domain.batch(frame.origin) != frame.incoming or
                    domain.successor(frame.origin, check) != parent.cursor):
                raise ValueError('parent-child committed cursor mismatch')
            if not core._push_batch(frame.incoming, check) or core.state.rows[parent.row] != 2:
                raise ValueError('incoming child batch rejected/failed row cover')
        leaf = core.state.full_family_leaf()
        target = core.state.four_selected >= core.m
        if frame.phase in (READY, PENDING, WAITING) or (frame.phase == DONE and frame.close_reason == DRAINED):
            if leaf or target:
                raise ValueError('branching metadata on terminal prefix')
            domain = core._domain(frame, check)
            if frame.phase == PENDING and domain.batch(frame.cursor) != frame.pending:
                raise ValueError('restored pending mismatch')
        elif frame.phase == LEAF or (frame.phase == DONE and frame.close_reason == TINY_LEAF):
            if (not leaf or core.leaf_digest() != frame.leaf_digest or
                    not check_candidate(core.state.model, core.state.selected)['valid_full_witness']):
                raise ValueError('restored leaf invalid')
        elif frame.phase == DONE:
            if leaf:
                raise ValueError('pruned frame is actually a leaf')
            if frame.close_reason == TARGET_NONLEAF:
                if not target:
                    raise ValueError('target closure below target')
            else:
                if target:
                    raise ValueError('shortfall closure at target')
                reason, row, domain = core._scan(check)
                if reason != frame.close_reason:
                    raise ValueError('restored prune not justified')
                if reason == ROW_SHORTFALL and (row != frame.row or 2-core.state.rows[row] != frame.deficit):
                    raise ValueError('restored row-prune witness mismatch')
    core.outer, core.slice_index, core.frames = parsed.outer, parsed.slice_index, list(parsed.frames)
    core.counts = dict(zip(COUNTERS, parsed.counts))
    core.restore_mode = False
    core.check_sources(check)
    check()
    return core


def loads(raw, *, trusted_record, expected_identity, check=lambda: None):
    return _restore(parse(raw, trusted_record=trusted_record, expected_identity=expected_identity, check=check), check=check)


def read_checkpoint(path, *, trusted_record, expected_identity, check=lambda: None):
    # Reject malformed authority before touching the checkpoint path.
    if type(trusted_record) is not TrustedRecord:
        raise ValueError('trusted record required')
    check()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 750 <= before.st_size <= MAX_WIRE_BYTES:
            raise ValueError('checkpoint file size/type')
        pieces, size = [], 0
        while True:
            check()
            piece = os.read(fd, min(65536, MAX_WIRE_BYTES+1-size))
            if not piece:
                break
            size += len(piece)
            if size > MAX_WIRE_BYTES:
                raise ValueError('checkpoint grew above cap')
            pieces.append(piece)
        after = os.fstat(fd)
        if (before.st_size != size or before.st_size != after.st_size or
                before.st_mtime_ns != after.st_mtime_ns or before.st_ino != after.st_ino):
            raise ValueError('checkpoint changed while reading')
    finally:
        os.close(fd)
    return loads(b''.join(pieces), trusted_record=trusted_record, expected_identity=expected_identity, check=check)


class ChainLease:
    """Explicit one-writer lease; stale leases fail closed and are never stolen."""
    def __init__(self, directory, *, expected_parent, chain_id):
        self.directory = Path(directory)
        require_digest(expected_parent)
        require_digest(chain_id, nonzero=True)
        self.expected_parent, self.chain_id = expected_parent, chain_id
        self.path = self.directory/'writer.lease'
        self.nonce = secrets.token_bytes(32)
        self.fd = None

    def __enter__(self):
        if not self.directory.is_dir() or self.directory.is_symlink():
            raise ValueError('chain directory must be local directory')
        self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        self.stat = os.fstat(self.fd)
        data = self.nonce+self.chain_id+self.expected_parent
        try:
            _write_all(self.fd, data, lambda: None)
            os.fsync(self.fd)
            _fsync_directory(self.directory)
        except BaseException:
            os.close(self.fd)
            self.fd = None
            # Leave the failed lease for explicit supervisor diagnosis.
            raise
        return self

    def verify(self):
        if self.fd is None:
            raise ValueError('inactive chain lease')
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            current = os.fstat(fd)
            data = os.read(fd, 97)
            if (not stat.S_ISREG(current.st_mode) or current.st_ino != self.stat.st_ino or
                    current.st_dev != self.stat.st_dev or data != self.nonce+self.chain_id+self.expected_parent):
                raise ValueError('lease ownership changed')
        finally:
            os.close(fd)

    def __exit__(self, exc_type, exc, tb):
        try:
            self.verify()
            os.unlink(self.path)
            _fsync_directory(self.directory)
        finally:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None


def _fsync_directory(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_all(fd, data, check):
    offset = 0
    while offset < len(data):
        check()
        count = os.write(fd, data[offset:offset+65536])
        if count <= 0:
            raise OSError('short write without progress')
        offset += count


def save_candidate(core, *, lease, check=lambda: None, fault=lambda boundary: None):
    """Install one immutable candidate. Never update supervisor acceptance."""
    if type(lease) is not ChainLease:
        raise ValueError('matching chain lease required')
    lease.verify()
    check()
    raw = encode(core, parent_hash=lease.expected_parent, chain_id=lease.chain_id, check=check)
    # Fully replay our own candidate before writing; corrupted RAM is not adopted.
    record = TrustedRecord(hashlib.sha256(raw).digest(), lease.expected_parent, lease.chain_id)
    replayed = loads(raw, trusted_record=record, expected_identity=identity(core, check), check=check)
    if (replayed.state.snapshot() != core.state.snapshot() or replayed.frames != core.frames or
            replayed.counts != core.counts or replayed.outer != core.outer or
            replayed.slice_index != core.slice_index):
        raise ValueError('live geometry/frontier differs from replay')
    core.work['restore_probes'] += replayed.work['restore_probes']
    name = record.content_sha256.hex()+'.nqrb'
    destination = lease.directory/name
    temp = lease.directory/('.candidate-'+secrets.token_hex(16))
    fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        _write_all(fd, raw, check)
        fault('after_write')
        os.fsync(fd)
        fault('after_file_fsync')
        os.close(fd)
        fd = None
        check()
        lease.verify()
        try:
            os.link(temp, destination, follow_symlinks=False)
        except FileExistsError:
            existing = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(existing)
                if not stat.S_ISREG(info.st_mode) or info.st_size != len(raw) or os.read(existing, len(raw)+1) != raw:
                    raise ValueError('content-name collision with unequal bytes')
            finally:
                os.close(existing)
        fault('after_link')
        _fsync_directory(lease.directory)
        fault('after_directory_fsync')
        os.unlink(temp)
        _fsync_directory(lease.directory)
        fault('after_temp_unlink')
        core.check_sources(check)
        check()
        return destination, record
    finally:
        if fd is not None:
            os.close(fd)
        if temp.exists():
            os.unlink(temp)
