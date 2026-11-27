"""Restricted first-eight conflict-covering 16-cycle rebuild; one bounded pilot.

Only main/run load the fixed n79 inputs. Pure helpers accept tiny fixtures for
source review; they neither allocate an actual pilot nor resume an old search.
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import source_disjoint_matching_rebuild157 as frozen

INPUT = 'data/score11-deficiency-walk-seed279157-v1/best-state.json'
SOURCE = 'data/trades-n79-seed270079-state.json'
AUDIT = 'data/score11-deficiency-walk-seed279157-v1-independent-actual-audit.json'
INPUT_PINS = {
    INPUT: '3e8c8e0495f2e2cbf99815c7fbc575ccd808d0e6908091eb6f04e268f42a38f0',
    SOURCE: '9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26',
    AUDIT: '419039ebf5828b8fef5b22a0eac29f63e4da4ff203a263aae14c30f704b4faec',
}
INPUT_NORMALIZED = 'adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c'
SOURCE_NORMALIZED = 'f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d'
WIDTH = 16
MAX_PATCHES = 8
MAX_INSERTIONS = 1000
InsertionCap = frozen.InsertionCap


def new_counters():
    counters = frozen.new_counters()
    for name in ('cover_nodes', 'padding_cells', 'cycle_steps'):
        counters.update({name + '_' + phase: 0 for phase in ('started', 'completed')})
    counters.update(cover_leaves=0, distinct_kernels=0, padded_kernels=0,
                    cycle_pruned_choices=0, full_cycle_checks=0)
    return counters


def axes(points, n, *, full=False):
    counts = tuple(Counter(p[a] for p in points) for a in (0, 1))
    if any(any(v > 2 for v in side.values()) for side in counts):
        raise ValueError('axis degree exceeds two')
    if full and (len(points) != 2*n-1 or any(
            sorted(side[i] for i in range(n)) != [1]+[2]*(n-1) for side in counts)):
        raise ValueError('not a direct deficiency state')
    return counts


def matching_cells(points):
    return (len({p[0] for p in points}) == len(points)
            == len({p[1] for p in points}))


def cover_kernels(A, conflicts, counters, check):
    """Every hitting matching contains a generated kernel; not all supersets."""
    conflicts = tuple(sorted(set(tuple(sorted(t)) for t in conflicts)))
    if any(len(t) != 3 or len(set(t)) != 3 or not set(t) <= set(A) for t in conflicts):
        raise ValueError('invalid conflict triple')
    found = set()

    def visit(selected, rows, cols):
        counters['cover_nodes_started'] += 1
        check()
        unhit = next((t for t in conflicts if not set(t).intersection(selected)), None)
        if unhit is None:
            found.add(tuple(sorted(selected)))
            counters['cover_leaves'] += 1
        else:
            for point in unhit:
                check()
                if point[0] not in rows and point[1] not in cols:
                    visit(selected+(point,), rows | {point[0]}, cols | {point[1]})
        counters['cover_nodes_completed'] += 1

    visit((), set(), set())
    result = sorted(found, key=lambda kernel: (len(kernel), kernel))
    counters['distinct_kernels'] = len(result)
    return result


def select_patches(A, conflicts, width, counters, check, max_patches=MAX_PATCHES,
                   progress=None):
    if type(width) is not int or width < 2 or type(max_patches) is not int or not 1 <= max_patches <= MAX_PATCHES:
        raise ValueError('invalid patch dimensions')
    kernels = cover_kernels(A, conflicts, counters, check)
    if progress is not None:
        progress['kernels_complete'] = True
        progress['kernel_count'] = len(kernels)
    patches = []
    seen = set()
    for kernel in kernels:
        check()
        if len(kernel) > width:
            continue
        selected = list(kernel)
        rows = {p[0] for p in selected}
        cols = {p[1] for p in selected}
        while len(selected) < width:
            for point in sorted(A):
                counters['padding_cells_started'] += 1
                check()
                counters['padding_cells_completed'] += 1
                if point[0] not in rows and point[1] not in cols:
                    selected.append(point)
                    rows.add(point[0]); cols.add(point[1])
                    break
            else:
                raise ValueError('matching kernel cannot be padded to requested width')
        counters['padded_kernels'] += 1
        patch = tuple(sorted(selected))
        if patch not in seen:
            patches.append(patch); seen.add(patch)
            if len(patches) == max_patches:
                break
    if progress is not None:
        progress['patch_selection_complete'] = True
    return patches


def proper_cycle(i, j, sigma, check=lambda: None, counters=None):
    """Would arc i->j close a cycle shorter than len(sigma)?"""
    cursor = j
    length = 1
    while True:
        if counters is not None:
            counters['cycle_steps_started'] += 1
        check()
        if counters is not None:
            counters['cycle_steps_completed'] += 1
        if cursor == i:
            return length < len(sigma)
        cursor = sigma[cursor]
        if cursor < 0:
            return False
        length += 1
        if length > len(sigma):
            raise ValueError('partial map already contains a closed cycle')


def single_cycle(sigma):
    if sorted(sigma) != list(range(len(sigma))):
        return False
    seen = set(); cursor = 0
    while cursor not in seen:
        seen.add(cursor); cursor = sigma[cursor]
    return cursor == 0 and len(seen) == len(sigma)


def root_domains(n, R, S, F, counters, check, progress=None):
    unsafe = 0
    for a, b in combinations(R, 2):
        unsafe = frozen.scan_line(n, a, b, unsafe, 'root', counters, check)
    if progress is not None:
        progress['root_mask_complete'] = True
        progress['root_unsafe_hex'] = hex(unsafe)
    domains = []
    for row, _ in F:
        mask = 0
        for j, (_, col) in enumerate(F):
            counters['root_domain_cells_started'] += 1
            check()
            if (row, col) not in S and not unsafe >> (n*row+col) & 1:
                mask |= 1 << j
            counters['root_domain_cells_completed'] += 1
        domains.append(mask)
    if progress is not None:
        progress['root_domains_complete'] = True
        progress['root_domains'] = [list(frozen.columns(mask)) for mask in domains]
    return unsafe, domains


class Constructor:
    """One fixed patch. Callback may collect every tiny completion in tests."""
    def __init__(self, n, R, S, F, domains, unsafe, counters, check, limit):
        if type(limit) is not int or not 0 <= limit <= MAX_INSERTIONS:
            raise ValueError('invalid shared insertion cap')
        self.n = n; self.R = tuple(R); self.S = frozenset(S); self.F = tuple(F)
        self.k = len(F); self.domains = tuple(domains); self.root_unsafe = unsafe
        if (self.k < 2 or not matching_cells(F) or tuple(sorted(F)) != self.F
                or len(domains) != self.k or any(mask < 0 or mask >> self.k for mask in domains)):
            raise ValueError('invalid fixed patch')
        self.counters = counters; self.check = check; self.limit = limit
        self.path = []; self.sigma = [-1]*self.k; self.root_restored = False

    def run(self, on_prefix):
        before = (self.R, self.S, self.F, self.domains, self.root_unsafe)

        def dfs(assigned, used, unsafe):
            self.check(); depth = len(self.path)
            if depth == self.k:
                self.counters['full_cycle_checks'] += 1
                if not single_cycle(self.sigma):
                    raise RuntimeError('completed map is not a single cycle')
                self.counters['full_assignments'] += 1
            if depth in (self.k-1, self.k):
                if on_prefix(tuple(self.path)):
                    if depth != self.k:
                        raise RuntimeError('only a full witness may stop search')
                    return True
            if depth == self.k:
                return False
            choices = []
            for i, (row, _) in enumerate(self.F):
                self.check()
                if assigned >> i & 1:
                    continue
                options = 0
                for j in frozen.columns(self.domains[i] & ~used):
                    col = self.F[j][1]
                    if not unsafe >> (self.n*row+col) & 1:
                        options |= 1 << j
                if not options:
                    self.counters['domain_wipeouts'] += 1
                    return False
                choices.append((options.bit_count(), i, options))
            _, i, options = min(choices)
            for j in frozen.columns(options):
                if proper_cycle(i, j, self.sigma, self.check, self.counters):
                    self.counters['cycle_pruned_choices'] += 1
                    continue
                if self.counters['insertions_started'] >= self.limit:
                    raise InsertionCap
                self.counters['insertions_started'] += 1
                self.check()
                point = (self.F[i][0], self.F[j][1]); following = unsafe
                for other in self.R+tuple(self.path):
                    following = frozen.scan_line(self.n, point, other, following,
                                                 'candidate', self.counters, self.check)
                self.path.append(point); self.sigma[i] = j
                self.counters['insertions_completed'] += 1
                self.counters['maximum_added'] = max(self.counters['maximum_added'], len(self.path))
                stopped = False
                try:
                    stopped = dfs(assigned | 1 << i, used | 1 << j, following)
                    if stopped:
                        return True
                finally:
                    if self.path.pop() != point or self.sigma[i] != j:
                        raise RuntimeError('rollback mismatch')
                    self.sigma[i] = -1
                    self.counters['rollbacks'] += 1
                    if not stopped:
                        self.counters['backtracks'] += 1
            return False

        try:
            return dfs(0, 0, self.root_unsafe)
        finally:
            self.root_restored = (not self.path and self.sigma == [-1]*self.k and
                                  before == (self.R, self.S, self.F, self.domains, self.root_unsafe))
            if not self.root_restored:
                raise RuntimeError('patch root state not restored')


def save_candidate(n, A, S, F, R, M, path, kind, check, pins):
    A = set(A); S = set(S); R = set(R); M = tuple(M); P = R | set(M)
    k = len(F); row_labels = {row: i for i, (row, _) in enumerate(F)}
    col_labels = {col: j for j, (_, col) in enumerate(F)}
    if (not A < S or len(S-A) != 1 or len(F) != len(set(F)) or not set(F) <= A
            or not matching_cells(F) or R != A-set(F) or not matching_cells(M)
            or len(P) != len(R)+len(M) or set(M) & S or P & S != R
            or any(x not in row_labels or y not in col_labels for x, y in M)
            or len(M) not in (k-1, k) or len(S-P) != k+1 or len(P-S) != len(M)):
        raise RuntimeError('candidate family/distance mismatch')
    axes(P, n)
    sigma = [-1]*k
    for row, col in M:
        sigma[row_labels[row]] = col_labels[col]
    if kind == 'full_witness':
        if len(M) != k or not single_cycle(sigma) or axes(P, n, full=True) != axes(A, n, full=True):
            raise RuntimeError('full cycle/degree mismatch')
    elif kind != 'diagnostic156' or len(M) != k-1:
        raise RuntimeError('candidate kind mismatch')
    frozen.verify_pins(pins)
    cert, reports = frozen.dual_valid(P, n, check)
    metadata = {'method': 'conflict_directed_sixteen_cycle_rebuild157', 'kind': kind,
                'valid': True, 'normalized_sha256': reports[0]['normalized_sha256'],
                'deleted_from_A': [list(p) for p in F], 'retained': [list(p) for p in sorted(R)],
                'replacement': [list(p) for p in M], 'sigma': sigma,
                'source_deleted': len(S-P), 'source_retained': len(P & S),
                'new_points_outside_source': len(P-S), 'axis_degrees_preserved': len(M) == k,
                'improves_verified_lower_bound': kind == 'full_witness',
                'novelty_claim': False, 'pins': dict(pins)}
    cert.update(metadata=metadata, validators=reports)
    # A completed second validator may cross the deadline. Save immediately.
    frozen.atomic(path, cert)
    return metadata


def new_patch_report(index, F):
    return {'index': index, 'deleted': [list(p) for p in F], 'status': 'incomplete',
            'complete': False, 'closure': False, 'retained_validation_complete': False,
            'root_mask_complete': False, 'root_domains_complete': False,
            'root_matching_complete': False, 'dfs_exhausted': False,
            'root_state_restored': None}


def search_patch(n, A, S, F, out, report, patch, check, pins, limit):
    R = tuple(sorted(set(A)-set(F))); c = report['counters']; kernel = None
    start = c['insertions_started']
    try:
        if not set(F) <= set(A) or not matching_cells(F):
            raise ValueError('invalid deletion patch')
        frozen.dual_valid(R, n, check)
        patch['retained_validation_complete'] = True
        unsafe, domains = root_domains(n, R, S, F, c, check, patch)
        gate = frozen.maximum_matching(domains, len(F), c, check)
        patch['root_matching_complete'] = True
        patch['root_matching_cover'] = gate
        if gate['matching_size'] < len(F):
            patch.update(status='root_matching_obstruction', complete=True, closure=True)
            return False
        kernel = Constructor(n, R, S, F, domains, unsafe, c, check, limit)

        def on_prefix(M):
            if len(M) == len(F)-1 and report['diagnostic156'] is None:
                report['diagnostic156'] = save_candidate(n, A, S, F, R, M,
                    out/'diagnostic156.json', 'diagnostic156', check, pins)
            if len(M) == len(F):
                report['witness157'] = save_candidate(n, A, S, F, R, M,
                    out/'witness157.json', 'full_witness', check, pins)
                return True
            return False

        stopped = kernel.run(on_prefix)
        patch.update(status='witness' if stopped else 'fixed_patch_exhausted',
                     complete=True, closure=not stopped, dfs_exhausted=not stopped)
        return stopped
    except TimeoutError:
        patch['status'] = 'timeout'; raise
    except InsertionCap:
        patch['status'] = 'insertion_cap'; raise
    except Exception:
        patch['status'] = 'error'; raise
    finally:
        patch['root_state_restored'] = None if kernel is None else kernel.root_restored
        patch['insertions_started'] = c['insertions_started']-start


def load_sources(check, pins):
    docs = {}
    for name, expected in INPUT_PINS.items():
        check(); path = ROOT/name; raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('fixed input/audit bytes mismatch: '+name)
        pins[str(path)] = expected
        if name != AUDIT:
            docs[name] = json.loads(raw)
    a, s = docs[INPUT], docs[SOURCE]
    if a['n'] != 79 or s['n'] != 79:
        raise ValueError('fixed source dimensions mismatch')
    A = frozen.cells([tuple(p) for p in a['points']], 79)
    S = frozen.cells([tuple(p) for p in s['points']], 79)
    if len(A) != 157 or len(S) != 158 or S-A != {(78, 78)} or not A < S:
        raise ValueError('fixed source containment mismatch')
    if axes(A, 79, full=True) != tuple(Counter({**{i: 2 for i in range(78)}, 78: 1}) for _ in range(2)):
        raise ValueError('fixed deficiency locations mismatch')
    if any(Counter(p[a] for p in S) != Counter({i: 2 for i in range(79)}) for a in (0, 1)):
        raise ValueError('fixed full source axes mismatch')
    if frozen.normalized_sha256(79, S) != SOURCE_NORMALIZED:
        raise ValueError('source normalized identity mismatch')
    certificate = {'n': 79, 'points': [list(p) for p in sorted(A)]}
    check(); first = frozen.verify_certificate(certificate)
    check(); second = frozen.verify_certificate_bruteforce(certificate)
    reports = [first, second]
    saved = a['validators']
    if (len(saved) != 2 or any(v['errors'] or v['valid'] or v['point_count'] != 157
            or v['conflict_count'] != 5 or v['normalized_sha256'] != INPUT_NORMALIZED
            for v in reports+saved)
            or any(frozen.canonical_conflicts(v) != frozen.canonical_conflicts(first) for v in reports+saved)
            or a['metadata']['normalized_sha256'] != INPUT_NORMALIZED
            or a['metadata']['exact_conflict_count'] != 5):
        raise RuntimeError('fixed input exact-five-conflict validation disagreement')
    return A, S, frozen.canonical_conflicts(first), reports


def run(out, seconds=25, max_insertions=MAX_INSERTIONS, *, clock=time.monotonic, started=None):
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or not 0 < seconds <= 25):
        raise ValueError('invalid shared duration')
    if type(max_insertions) is not int or not 0 <= max_insertions <= MAX_INSERTIONS:
        raise ValueError('invalid shared insertion cap')
    start = clock() if started is None else started
    deadline = start+seconds

    def check():
        if clock() >= deadline:
            raise TimeoutError('shared soft deadline')

    pins = {}
    report = {'method': 'conflict_directed_sixteen_cycle_rebuild157', 'n': 79,
              'target': 157, 'width': WIDTH, 'max_patches': MAX_PATCHES,
              'max_insertions': max_insertions, 'shared_soft_seconds': seconds,
              'status': 'incomplete', 'complete': False, 'closure': False,
              'source_validation_complete': False, 'kernels_complete': False,
              'patch_selection_complete': False, 'patches': [], 'counters': new_counters(),
              'diagnostic156': None, 'witness157': None,
              'scope': 'Only first eight distinct deterministic greedy-padded matching covers; single sixteen-cycles, outside fixed S. No alternate padding, restart, width change or automatic continuation.'}
    report['arithmetic_bounds'] = {'cover_nodes': 364, 'cover_leaves': 243,
        'padding_cells': 610416, 'root_lines': 78960, 'root_cell_visits': 6237840,
        'root_domain_cells': 2048, 'augmenting_matching_edge_scans': 32768,
        'cover_edge_scans': 2048, 'certificate_edge_checks': 2048,
        'candidate_cell_visits_per_insertion': 12324,
        'candidate_cell_visits': 12324*max_insertions,
        'root_plus_candidate_cell_visits': 6237840+12324*max_insertions,
        'maximum_added': WIDTH}
    try:
        for path in (Path(__file__).resolve(), Path(frozen.__file__).resolve(), ROOT/'src/verify.py'):
            check(); pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        A, S, conflicts, reports = load_sources(check, pins)
        report.update(source_validation_complete=True, input_validation=reports,
                      input_normalized_sha256=INPUT_NORMALIZED,
                      source_normalized_sha256=SOURCE_NORMALIZED)
        patches = select_patches(A, conflicts, WIDTH, report['counters'], check, progress=report)
        report['selected_patches'] = [[list(p) for p in F] for F in patches]
        # Only one patch's geometric state is live. The shared c/clock never reset.
        for index, F in enumerate(patches):
            check()
            patch = new_patch_report(index, F); report['patches'].append(patch)
            if search_patch(79, A, S, F, out, report, patch, check, pins, max_insertions):
                report.update(status='witness', complete=True)
                break
        else:
            report.update(status='selected_families_exhausted' if patches else 'no_matching_kernel',
                          complete=True, closure=True)
    except TimeoutError:
        report['status'] = 'timeout'
    except InsertionCap:
        report['status'] = 'insertion_cap'
    except Exception as error:
        report.update(status='error', error=f'{type(error).__name__}: {error}')
    try:
        frozen.verify_pins(pins)
    except (OSError, ValueError) as error:
        report.update(status='error', complete=False, closure=False, identity_valid=False,
                      error=f'final identity recheck: {error}')
    else:
        report['identity_valid'] = True
    report['pins'] = pins; report['elapsed_seconds'] = clock()-start
    frozen.atomic(out/'report.json', report)
    return report


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=25)
    parser.add_argument('--max-insertions', type=int, default=MAX_INSERTIONS)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = run(args.output_dir, args.seconds, args.max_insertions, started=started)
    print(json.dumps(result, sort_keys=True))
    return 1 if result['status'] == 'error' else (0 if result['complete'] else 2)


if __name__ == '__main__':
    sys.exit(main())
