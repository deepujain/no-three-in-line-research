"""Exact quota completion of six approved score11 source paths; no host run implied."""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.score11_cover_repair import load_source, SOURCE_BYTES, SOURCE_NORMALIZED
from research.diagonal_secant_checkpoint import atomic, encode
from src.trade_search import point_conflicts
from src.verify import verify_certificate, verify_certificate_bruteforce

COVER = frozenset(((33, 78), (78, 78), (78, 0)))
EVIDENCE = {
    'data/score11-connected-patch-arithmetic.json': 'e42e0dfb86c46f11b59b74fb7b0f858ba88439e66455b3da762ca3a2674c3610',
    'data/score11-connected-path8-independent-arithmetic-audit.json': 'd7072171db24b510f9018b883f7e619f4e0a9d9f3a1f159c00fe2ee190e176e0',
    'data/score11-five-deletions-v1-prefix-audit.json': 'ca126bf09bdbbbf9b88a02ace66c4cf6965369579e9b0e78ad2d5f37f0929f17',
    'data/score11-five-suffix-independent-audit.json': '4c713e349c80eab56b6fb8fd2c1a65a76c4c45c34e3bbb86243afd638ee3ed1c',
    'research/score11-five-suffix-combined-actual-review.md': '473c88cd959ffe481341495855da4174e7e305d6493bca813f549dbd3f85354e',
}


def check_time(deadline, clock):
    if clock() >= deadline:
        raise TimeoutError


def source_cycles(points):
    """Traverse a simple bipartite degree-two source graph, retaining edge order."""
    adjacent = defaultdict(list)
    for p in sorted(points):
        adjacent[('r', p[0])].append(p)
        adjacent[('c', p[1])].append(p)
    if any(len(edges) != 2 for edges in adjacent.values()):
        raise ValueError('source incidence must have degree two')
    unused = set(points)
    cycles = []
    while unused:
        first = min(unused)
        vertex = ('r', first[0])
        edge = first
        ordered = []
        while edge in unused:
            unused.remove(edge)
            ordered.append(edge)
            vertex = ('c', edge[1]) if vertex[0] == 'r' else ('r', edge[0])
            edge = next(p for p in adjacent[vertex] if p != edge)
        if edge != first:
            raise ValueError('source incidence does not close a cycle')
        cycles.append(tuple(ordered))
    return cycles


def connected_paths(points, cover=COVER, length=8):
    cycles = source_cycles(points)
    paths = set()
    for cycle in cycles:
        if not cover <= set(cycle):
            continue
        if len(cycle) <= length:
            raise ValueError('path must be shorter than source cycle')
        for i in range(len(cycle)):
            patch = frozenset(cycle[(i + j) % len(cycle)] for j in range(length))
            if cover <= patch:
                paths.add(patch)
    return cycles, paths


def quota_factors(deleted, size, deadline=math.inf, clock=time.monotonic):
    """All exact-size binary rectangle factors under both residual upper quotas.

    A seven-cell factor need not extend to an eight-cell factor.
    """
    deleted = set(deleted)
    rows = sorted({x for x, y in deleted})
    cols = sorted({y for x, y in deleted})
    row_caps = Counter(x for x, y in deleted)
    col_caps = Counter(y for x, y in deleted)
    selected = []
    used = Counter()

    def visit(index, need):
        check_time(deadline, clock)
        if index == len(rows):
            if need == 0:
                yield frozenset(selected)
            return
        x = rows[index]
        remaining_cap = sum(row_caps[r] for r in rows[index + 1:])
        for count in range(max(0, need - remaining_cap), min(row_caps[x], need) + 1):
            for chosen in itertools.combinations(cols, count):
                if any(used[y] >= col_caps[y] for y in chosen):
                    continue
                for y in chosen:
                    selected.append((x, y))
                    used[y] += 1
                yield from visit(index + 1, need - count)
                for y in reversed(chosen):
                    selected.pop()
                    used[y] -= 1
    yield from visit(0, size)


def load_evidence():
    documents = {}
    for name, digest in EVIDENCE.items():
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('evidence hash mismatch: ' + name)
        if name.endswith('.json'):
            documents[name] = json.loads(raw)
    manifest = documents['data/score11-connected-patch-arithmetic.json']
    audit = documents['data/score11-connected-path8-independent-arithmetic-audit.json']
    prefix = documents['data/score11-five-deletions-v1-prefix-audit.json']
    suffix = documents['data/score11-five-suffix-independent-audit.json']
    combined = suffix['combined_coverage']
    if (manifest['source_sha256'] != SOURCE_BYTES
            or manifest['source_normalized_sha256'] != SOURCE_NORMALIZED
            or not audit['accepted'] or audit['manifest_sha256'] != EVIDENCE['data/score11-connected-patch-arithmetic.json']
            or suffix['parent_prefix_audit_sha256'] != EVIDENCE['data/score11-five-deletions-v1-prefix-audit.json']
            or not prefix['accepted_partial_execution'] or not suffix['accepted_suffix_execution']
            or not combined['complete_fixed_source_through5_negative']
            or (combined['completed_prefix'], combined['completed_suffix'], combined['total'], combined['gaps'], combined['overlap']) != (33062, 2747, 35809, 0, 0)
            or prefix['full_order_sha256'] != suffix['full_order_sha256']):
        raise ValueError('accepted cap5/arithmetic evidence linkage mismatch')
    return manifest


def factor_geometry(retained, factor, safe, deadline, clock):
    """Check all new conflict classes; retained validity is independently established."""
    if not factor <= safe:
        return False
    current = set(retained)
    for p in sorted(factor):
        check_time(deadline, clock)
        if p in current or point_conflicts(p, current):
            return False
        current.add(p)
    return True


def save_witness(points, deleted, factor, index, out):
    cert = {'n': 79, 'points': [list(p) for p in sorted(points)]}
    checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
    if (any(not c['valid'] or c['point_count'] not in (157, 158) for c in checks)
            or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']):
        raise RuntimeError('witness dual verification failed')
    digest = checks[0]['normalized_sha256']
    cert['metadata'] = {'method': 'score11_connected_path8', 'source_normalized_sha256': SOURCE_NORMALIZED,
                        'source_bytes_sha256': SOURCE_BYTES, 'template_index': index,
                        'deleted_patch': [list(p) for p in sorted(deleted)],
                        'inserted_factor': [list(p) for p in sorted(factor)],
                        'effective_original_deletions': [list(p) for p in sorted(deleted - factor)],
                        'normalized_sha256': digest, 'novelty_claim': False}
    atomic(out / ('witness-' + digest + '.json'), encode(cert))


def run(source, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('soft duration must be in (0,25]')
    start = clock()
    deadline = start + seconds
    report = {'method': 'score11_connected_path8', 'source_bytes_sha256': SOURCE_BYTES,
              'source_normalized_sha256': SOURCE_NORMALIZED, 'evidence_sha256': EVIDENCE,
              'scope': 'Six exact original eight-edge connected paths only; record counts include duplicate final sets across templates; no global nonexistence claim.',
              'declared_quota_records': 12096, 'declared_after_cap5': 3864,
              'declared_after_cap5_old_triples': 1306, 'complete': False,
              'status': 'incomplete', 'witnesses': 0,
              'templates': [{'index': i, 'status': 'unstarted', 'quota_started': 0,
                             'quota_completed': 0, 'cap5_rejected': 0, 'old_triple_rejected': 0,
                             'geometry_started': 0, 'geometry_completed': 0, 'geometry_rejected': 0,
                             'quota_by_size': {'7': 0, '8': 0},
                             'old_triple_survivors_by_size': {'7': 0, '8': 0}}
                            for i in range(6)]}
    active = None
    try:
        check_time(deadline, clock)
        points, conflicts = load_source(source)
        check_time(deadline, clock)
        manifest = load_evidence()
        cycles, paths = connected_paths(points)
        cases = manifest['eight_edge_paths']['deletion_cases']
        patches = [frozenset(map(tuple, c['deleted'])) for c in cases]
        if sorted(map(len, cycles)) != [4, 12, 142] or len(patches) != 6 or len(set(patches)) != 6 or set(patches) != paths:
            raise ValueError('six approved connected paths mismatch')
        for index, deleted in enumerate(patches):
            check_time(deadline, clock)
            active = report['templates'][index]
            active['status'] = 'partial'
            active['deleted_patch'] = [list(p) for p in sorted(deleted)]
            if not all(deleted & t for t in conflicts):
                raise ValueError('retained source contains an original conflict')
            retained = points - deleted
            cells = set(itertools.product(sorted({x for x, y in deleted}), sorted({y for x, y in deleted})))
            if len(cells) != 20 or cells & retained:
                raise ValueError('approved rectangle mismatch')
            safe = set()
            for p in sorted(cells):
                check_time(deadline, clock)
                if not point_conflicts(p, retained):
                    safe.add(p)
            active['retained_safe_cells'] = len(safe)
            for size in (8, 7):
                for factor in quota_factors(deleted, size, deadline, clock):
                    check_time(deadline, clock)
                    active['quota_started'] += 1
                    effective_deleted = deleted - factor
                    if len(effective_deleted) <= 5:
                        active['cap5_rejected'] += 1
                    elif not all(effective_deleted & t for t in conflicts):
                        active['old_triple_rejected'] += 1
                    else:
                        active['geometry_started'] += 1
                        valid = factor_geometry(retained, factor, safe, deadline, clock)
                        active['geometry_completed'] += 1
                        active['old_triple_survivors_by_size'][str(size)] += 1
                        if valid:
                            save_witness(retained | factor, deleted, factor, index, out)
                            report['witnesses'] += 1
                            report['status'] = 'witness'
                        else:
                            active['geometry_rejected'] += 1
                    active['quota_completed'] += 1
                    active['quota_by_size'][str(size)] += 1
                    if report['witnesses']:
                        break
                if report['witnesses']:
                    break
            if report['witnesses']:
                break
            expected = manifest['eight_edge_paths']['per_template_old_conflict_prefilter'][index]
            if (active['quota_by_size'] != {'7': 1812, '8': 204}
                    or active['cap5_rejected'] != 1372
                    or active['old_triple_survivors_by_size'] != {'7': expected['157']['counts']['old_triples_hit'], '8': expected['158']['counts']['old_triples_hit']}):
                raise ValueError('completed quota census differs from approved arithmetic')
            active['status'] = 'complete'
            active = None
        else:
            report['status'] = 'complete'
            report['complete'] = True
    except TimeoutError:
        report['status'] = 'timeout'
    report['elapsed_seconds'] = clock() - start
    atomic(out / 'report.json', encode(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.source, args.output_dir, args.seconds)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['status'] in ('complete', 'witness') else 2


if __name__ == '__main__':
    sys.exit(main())
