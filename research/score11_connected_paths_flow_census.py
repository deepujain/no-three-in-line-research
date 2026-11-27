"""Safe-cell and exact axis-capacity bounds on 32 approved connected source patches."""
import argparse
from collections import Counter, deque
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
from research.score11_connected_path8 import connected_paths, check_time
from research.diagonal_secant_checkpoint import atomic, encode
from src.trade_search import point_conflicts

MANIFEST = 'data/score11-connected-paths-flow-census-cases.proposal.json'
MATH_AUDIT = 'data/score11-connected-paths-flow-census-independent-arithmetic-audit.json'
PINS = {MANIFEST: '68415d1e67a99fc90c7ca3c0f47db4de8e0c2f9bf9f9fc8d2313ec10857abbe5',
        MATH_AUDIT: '7cc03e2365d6f4bbe020ea6ec7b65ca17837a9325c08bf5ccd72f5723e577c8d'}


def verify_flow_certificate(cells, rows, cols, cert):
    """Independent primal/cut equality suffices to certify maximum cardinality."""
    cells = set(cells)
    if any(x not in rows or y not in cols for x, y in cells):
        raise ValueError('cell outside declared axes')
    selected_list = [tuple(p) for p in cert['selected_cells']]
    selected = set(selected_list)
    reachable_rows = set(cert['reachable_rows'])
    reachable_cols = set(cert['reachable_columns'])
    value = cert['flow_value']
    if (type(value) is not int or value < 0 or len(selected) != len(selected_list)
            or len(selected) != value or not selected <= cells
            or not reachable_rows <= rows.keys() or not reachable_cols <= cols.keys()):
        raise ValueError('invalid primal flow or cut vertices')
    used_rows = Counter(x for x, y in selected)
    used_cols = Counter(y for x, y in selected)
    if any(used_rows[x] > rows[x] for x in rows) or any(used_cols[y] > cols[y] for y in cols):
        raise ValueError('primal flow exceeds axis capacities')
    cut = (sum(cap for x, cap in rows.items() if x not in reachable_rows)
           + sum(1 for x, y in cells if x in reachable_rows and y not in reachable_cols)
           + sum(cap for y, cap in cols.items() if y in reachable_cols))
    if cut != value or cert['cut_capacity'] != cut:
        raise ValueError('primal flow and cut capacity disagree')
    return value


def maximum_axis_flow(cells, rows, cols, deadline=math.inf, clock=time.monotonic):
    """Exact integral augmenting paths; one unit per distinct safe cell."""
    cells = set(cells)
    if (any(type(v) is not int or v < 0 for v in (*rows.values(), *cols.values()))
            or any(x not in rows or y not in cols for x, y in cells)):
        raise ValueError('invalid flow capacities or cells')
    source, sink = (0, -1), (3, -1)
    residual = {source: {}, sink: {}}

    def edge(u, v, cap):
        residual.setdefault(u, {})[v] = cap
        residual.setdefault(v, {})[u] = 0

    for x in sorted(rows):
        edge(source, (1, x), rows[x])
    for x, y in sorted(cells):
        edge((1, x), (2, y), 1)
    for y in sorted(cols):
        edge((2, y), sink, cols[y])
    value = 0
    while True:
        check_time(deadline, clock)
        parent = {source: None}
        queue = deque([source])
        while queue and sink not in parent:
            check_time(deadline, clock)
            u = queue.popleft()
            for v, cap in residual[u].items():
                check_time(deadline, clock)
                if cap > 0 and v not in parent:
                    parent[v] = u
                    queue.append(v)
        if sink not in parent:
            break
        # Every augmenting path contains a unit-capacity cell edge; integrality
        # makes the augment exactly one, including paths using reverse edges.
        vertex = sink
        while vertex != source:
            check_time(deadline, clock)
            previous = parent[vertex]
            residual[previous][vertex] -= 1
            residual[vertex][previous] += 1
            vertex = previous
        value += 1
    cert = {'flow_value': value,
            'selected_cells': [[x, y] for x, y in sorted(cells) if residual[(1, x)][(2, y)] == 0],
            'reachable_rows': [x for x in sorted(rows) if (1, x) in parent],
            'reachable_columns': [y for y in sorted(cols) if (2, y) in parent],
            'cut_capacity': value}
    verify_flow_certificate(cells, rows, cols, cert)
    return cert


def load_manifest(points):
    documents = {}
    for path, digest in PINS.items():
        raw = (ROOT / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('pinned evidence changed: ' + path)
        documents[path] = json.loads(raw)
    manifest = documents[MANIFEST]
    audit = documents[MATH_AUDIT]
    if (manifest['source_bytes_sha256'] != SOURCE_BYTES
            or manifest['source_normalized_sha256'] != SOURCE_NORMALIZED
            or manifest['lengths'] != [10, 12, 16] or manifest['total_cases'] != 32
            or not audit['accepted'] or audit['manifest_sha256'] != PINS[MANIFEST]):
        raise ValueError('manifest source or family mismatch')
    all_cases = manifest['cases']
    for length in (10, 12, 16):
        cycles, paths = connected_paths(points, length=length)
        cases = [c for c in all_cases if c['length'] == length]
        declared = [frozenset(map(tuple, c['deleted'])) for c in cases]
        if (sorted(map(len, cycles)) != [4, 12, 142] or len(cases) != length - 2
                or len(set(declared)) != len(declared) or set(declared) != paths):
            raise ValueError('exact source windows differ from approved manifest')
    if len(all_cases) != 32 or sum(c['candidate_cells'] for c in all_cases) != 1668:
        raise ValueError('declared family arithmetic mismatch')
    return manifest


def run(source, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds, (float, int)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('soft duration must be in (0,25]')
    start = clock()
    deadline = start + seconds
    report = {'method': 'score11_connected_paths_flow_census', 'source_bytes_sha256': SOURCE_BYTES,
              'source_normalized_sha256': SOURCE_NORMALIZED, 'evidence_sha256': PINS,
              'scope': 'All32 fixed-source length10/12/16 windows containing approved C; safe-cell and axis-capacity bounds only; eligible is unresolved geometry.',
              'declared_cases': 32, 'declared_cell_records': 1668,
              'case_completed': 0, 'cell_checks_started': 0, 'cell_checks_completed': 0,
              'closed_cases': 0, 'eligible_cases': 0, 'complete': False,
              'status': 'incomplete',
              'cases': [{'case_id': f'k{k}-{i:02d}', 'status': 'unstarted',
                         'cell_checks_started': 0, 'cell_checks_completed': 0}
                        for k in (10, 12, 16) for i in range(k - 2)]}
    try:
        check_time(deadline, clock)
        points, conflicts = load_source(source)
        check_time(deadline, clock)
        manifest = load_manifest(points)
        report['cases'] = [{**c, 'status': 'unstarted', 'cell_checks_started': 0,
                            'cell_checks_completed': 0} for c in manifest['cases']]
        for case in report['cases']:
            check_time(deadline, clock)
            case['status'] = 'partial_safe_census'
            deleted = set(map(tuple, case['deleted']))
            if len(deleted) != case['length'] or not all(deleted & triple for triple in conflicts):
                raise ValueError('deleted patch does not leave valid retained source')
            retained = points - deleted
            rows = dict(case['row_capacities'])
            cols = dict(case['column_capacities'])
            rc = Counter(x for x, y in retained)
            cc = Counter(y for x, y in retained)
            if (rows != {x: 2 - rc[x] for x, y in deleted}
                    or cols != {y: 2 - cc[y] for x, y in deleted}
                    or len(retained) != case['retained_point_count']):
                raise ValueError('source residual capacities mismatch')
            cells = sorted(set(itertools.product(rows, cols)) - retained)
            if len(cells) != case['candidate_cells']:
                raise ValueError('candidate rectangle count mismatch')
            safe = set()
            for point in cells:
                check_time(deadline, clock)
                case['cell_checks_started'] += 1
                report['cell_checks_started'] += 1
                if not point_conflicts(point, retained):
                    safe.add(point)
                case['cell_checks_completed'] += 1
                report['cell_checks_completed'] += 1
            case['safe_cells'] = [list(p) for p in sorted(safe)]
            case['safe_cell_count'] = len(safe)
            case['safe_original_readditions'] = len(safe & deleted)
            case['safe_new_cells'] = len(safe - points)
            case['status'] = 'partial_flow'
            certificate = maximum_axis_flow(safe, rows, cols, deadline, clock)
            upper = len(retained) + certificate['flow_value']
            case['flow_certificate'] = certificate
            case['final_cardinality_upper_bound'] = upper
            case['classification'] = 'closed_at_most156' if upper <= 156 else 'eligible_unresolved_geometry'
            case['status'] = 'complete'
            report['case_completed'] += 1
            report['closed_cases' if upper <= 156 else 'eligible_cases'] += 1
        report['complete'] = True
        report['status'] = 'complete'
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
    result = run(args.source, args.output_dir, args.seconds)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
