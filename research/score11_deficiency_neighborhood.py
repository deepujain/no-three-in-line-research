"""One bounded neighborhood census of the reviewed 157-point deficient state."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import score11_deficiency_walk as base

INPUT = ROOT / 'data/score11-deficiency-walk-seed279157-v1/best-state.json'
INPUT_SHA = '3e8c8e0495f2e2cbf99815c7fbc575ccd808d0e6908091eb6f04e268f42a38f0'
INPUT_NORMALIZED = 'adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c'
AUDIT = ROOT / 'data/score11-deficiency-walk-seed279157-v1-independent-actual-audit.json'
AUDIT_SHA = '419039ebf5828b8fef5b22a0eac29f63e4da4ff203a263aae14c30f704b4faec'


def attempts(points):
    ordered = sorted(points)
    for kind in ('row', 'column'):
        for point in ordered:
            yield kind, (point,)
    for a, b in itertools.combinations(ordered, 2):
        yield 'rectangle', (a, b)


def census(n, points, score, out, *, seconds=25, clock=time.monotonic, started=None,
           input_sha=None, expected_normalized=None, pins=None):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 < seconds <= 25:
        raise ValueError('invalid soft interval')
    start = clock() if started is None else started
    deadline = start + seconds
    report = {'status': 'timeout', 'complete': False, 'n': n, 'initial_score': score,
              'input_bytes_sha256': input_sha, 'input_normalized_sha256': None,
              'seconds': seconds, 'pins': pins, 'best_score': None, 'best_normalized_sha256': None,
              'classes': {k: {'started': 0, 'completed': 0, 'legal': 0, 'illegal': 0, 'deltas': {}}
                          for k in ('row', 'column', 'rectangle')},
              'scope': 'one neighborhood; histogram counts legal attempts; no recursive search'}
    hist = {k: Counter() for k in report['classes']}
    try:
        audited = base.dual_audit(points, n, score, deadline, clock)
        digest = audited[0]['normalized_sha256']
        report['input_normalized_sha256'] = digest
        if expected_normalized is not None and digest != expected_normalized:
            raise ValueError('input normalized identity mismatch')
        best = score
        for kind, old in attempts(points):
            if clock() >= deadline:
                raise TimeoutError('before attempt')
            row = report['classes'][kind]
            row['started'] += 1
            proposal = base.rectangle(points, n, *old) if kind == 'rectangle' else base.relocation(points, n, old[0], kind)
            if proposal is None:
                row['illegal'] += 1
                row['completed'] += 1
                continue
            delta, candidate = proposal
            added = sorted(candidate - points)
            inverse = base.rectangle(candidate, n, *added) if kind == 'rectangle' else base.relocation(candidate, n, added[0], kind)
            if inverse is None or inverse[0] != -delta or inverse[1] != points:
                raise RuntimeError('inverse mismatch')
            row['legal'] += 1
            row['completed'] += 1
            hist[kind][delta] += 1
            candidate_score = score + delta
            if candidate_score < best:
                metadata = {'initial_normalized_sha256': digest, 'input_bytes_sha256': input_sha,
                            'move_kind': kind, 'removed': [list(p) for p in old],
                            'delta': delta, 'pins': pins}
                best_digest = base.audit_save(candidate, n, candidate_score, out, metadata, deadline, clock)
                best = candidate_score
                report['best_score'] = best
                report['best_normalized_sha256'] = best_digest
                if best == 0:
                    report['status'] = 'witness'
                    break
        else:
            report['status'] = 'complete'
            report['complete'] = True
    except TimeoutError as error:
        report['timeout_phase'] = str(error)
    except Exception as error:
        report['status'] = 'error'
        report['error'] = f'{type(error).__name__}: {error}'
    for kind, row in report['classes'].items():
        row['deltas'] = dict(sorted(hist[kind].items()))
        row['improving'] = sum(v for k, v in hist[kind].items() if k < 0)
        row['neutral'] = hist[kind][0]
        row['worsening'] = sum(v for k, v in hist[kind].items() if k > 0)
    report['elapsed_seconds'] = clock() - start
    return report


def recheck_pins(pins):
    for path, expected in pins.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError(f'pinned file changed: {path}')


def finalize_identity(report, pins):
    try:
        recheck_pins(pins)
    except (OSError, ValueError) as error:
        report['status'] = 'error'
        report['complete'] = False
        report['error'] = f'identity recheck failed: {error}'
    return report


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--best', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.best.resolve() == args.report.resolve() or args.best.exists() or args.report.exists():
        parser.error('best and report must be distinct new paths')
    raw = INPUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA or hashlib.sha256(AUDIT.read_bytes()).hexdigest() != AUDIT_SHA:
        raise ValueError('input or audit byte hash mismatch')
    doc = json.loads(raw)
    if doc['n'] != 79 or doc['metadata']['normalized_sha256'] != INPUT_NORMALIZED or doc['metadata']['exact_conflict_count'] != 5:
        raise ValueError('input metadata mismatch')
    points = [tuple(p) for p in doc['points']]
    if len(points) != len(set(points)):
        raise ValueError('duplicate input point')
    pin_paths = ('research/score11_deficiency_neighborhood.py', 'research/score11_deficiency_walk.py', 'src/trade_search.py', 'src/verify.py')
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in pin_paths}
    report = census(79, set(points), 5, args.best, started=started, input_sha=INPUT_SHA,
                    expected_normalized=INPUT_NORMALIZED, pins=pins)
    observed = {ROOT / p: digest for p, digest in pins.items()}
    observed.update({INPUT: INPUT_SHA, AUDIT: AUDIT_SHA})
    finalize_identity(report, observed)
    base.atomic(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['status'] == 'error' else 0


if __name__ == '__main__':
    sys.exit(main())
