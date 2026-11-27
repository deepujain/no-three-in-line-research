"""Bounded two-move census from exactly three reviewed deficient-state exits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import score11_deficiency_walk as base
from research import score11_deficiency_neighborhood as one

MANIFEST = ROOT / 'data/score11-deficiency-neighborhood-v1-independent-plus1-exit-manifest.json'
MANIFEST_SHA = '717c6c1fb2debc0d446cb67922670c4ad97643b34a54aaaae653e6d1b0f0b71b'
AUDIT = ROOT / 'data/score11-deficiency-neighborhood-v1-independent-actual-audit.json'
AUDIT_SHA = 'edec993b9493b73d90b879f682fb6624176c75d8796d18f2cce94ea5800f1350'
MAX_MAP = 37684


def bitkey(points, n):
    key = 0
    for x, y in points:
        key |= 1 << (n * x + y)
    return key


def second_census(n, initial, initial_score, parents, out, *, seconds=25, clock=time.monotonic,
                  started=None, input_sha=None, pins=None, expected_initial=None):
    """parents are (points, score, normalized identity, move kind, removed cells)."""
    if len(parents) != 3 or isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 < seconds <= 25:
        raise ValueError('expected three parents and bounded soft interval')
    start = clock() if started is None else started
    deadline = start + seconds
    report = {'status': 'timeout', 'complete': False, 'n': n, 'initial_score': initial_score,
              'input_bytes_sha256': input_sha, 'seconds': seconds, 'pins': pins,
              'best_score': None, 'best_normalized_sha256': None,
              'parents': [{'normalized_sha256': p[2], 'classes': {k: {'started': 0, 'completed': 0, 'legal': 0, 'illegal': 0, 'deltas': {}} for k in ('row', 'column', 'rectangle')}} for p in parents],
              'novel_histogram': {}, 'generated_unique_histogram': {},
              'novel_first_insertions': 0, 'preexisting_occurrences': 0,
              'backtrack_occurrences': 0, 'exit_occurrences': 0, 'same_parent_repeats': 0,
              'cross_parent_revisits': 0, 'map_size': 0, 'preseed_complete': False,
              'scope': 'three exact parents; two moves only; no global claim'}
    novel_hist, unique_hist = Counter(), Counter()
    hist = [{k: Counter() for k in ('row', 'column', 'rectangle')} for _ in parents]
    entries = {}
    try:
        audited = base.dual_audit(initial, n, initial_score, deadline, clock)
        report['initial_normalized_sha256'] = audited[0]['normalized_sha256']
        if expected_initial is not None and report['initial_normalized_sha256'] != expected_initial:
            raise ValueError('initial normalized identity mismatch')
        initial_key = bitkey(initial, n)
        entries[initial_key] = [initial_score, 0, 'initial']
        exit_keys = set()
        for points, score, digest, kind, removed in parents:
            verified = base.dual_audit(points, n, score, deadline, clock)
            if verified[0]['normalized_sha256'] != digest or score != initial_score + 1:
                raise ValueError('parent identity or score mismatch')
            proposal = base.rectangle(initial, n, *removed) if kind == 'rectangle' else base.relocation(initial, n, removed[0], kind)
            if proposal is None or proposal[0] != 1 or proposal[1] != points:
                raise ValueError('parent move mismatch')
            key = bitkey(points, n)
            if key in entries:
                raise ValueError('duplicate parent or initial')
            exit_keys.add(key)
            entries[key] = [score, 0, 'exit']
        report['preseed_complete'] = True
        best = initial_score
        for parent_index, (points, score, digest, _, _) in enumerate(parents):
            for kind, old in one.attempts(points):
                if clock() >= deadline:
                    raise TimeoutError('before attempt')
                row = report['parents'][parent_index]['classes'][kind]
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
                candidate_score = score + delta
                key = bitkey(candidate, n)
                bit = 1 << parent_index
                preexisting = key in entries
                if not preexisting:
                    if len(entries) >= MAX_MAP:
                        raise RuntimeError('map cap exceeded')
                    entries[key] = [candidate_score, 0, 'novel']
                    report['novel_first_insertions'] += 1
                    novel_hist[candidate_score] += 1
                entry = entries[key]
                if entry[0] != candidate_score:
                    raise RuntimeError('duplicate score mismatch')
                if entry[1] & bit:
                    report['same_parent_repeats'] += 1
                    raise RuntimeError('same-parent repeated neighbor')
                if preexisting:
                    report['preexisting_occurrences'] += 1
                if entry[1]:
                    report['cross_parent_revisits'] += 1
                else:
                    unique_hist[candidate_score] += 1
                entry[1] |= bit
                if key == initial_key:
                    report['backtrack_occurrences'] += 1
                if key in exit_keys:
                    report['exit_occurrences'] += 1
                row['legal'] += 1
                row['completed'] += 1
                hist[parent_index][kind][delta] += 1
                if candidate_score < best:
                    meta = {'input_sha256': input_sha, 'parent_index': parent_index,
                            'parent_normalized_sha256': digest, 'move_kind': kind,
                            'removed': [list(p) for p in old], 'delta': delta, 'pins': pins}
                    best_digest = base.audit_save(candidate, n, candidate_score, out, meta, deadline, clock)
                    best = candidate_score
                    report['best_score'], report['best_normalized_sha256'] = best, best_digest
                    if best == 0:
                        report['status'] = 'witness'
                        break
            if report['status'] == 'witness':
                break
        else:
            report['status'] = 'complete'
            report['complete'] = True
    except TimeoutError as error:
        report['timeout_phase'] = str(error)
    except Exception as error:
        report['status'] = 'error'
        report['error'] = f'{type(error).__name__}: {error}'
    report['map_size'] = len(entries)
    report['novel_histogram'] = dict(sorted(novel_hist.items()))
    report['generated_unique_histogram'] = dict(sorted(unique_hist.items()))
    for i, parent in enumerate(report['parents']):
        for kind, row in parent['classes'].items():
            row['deltas'] = dict(sorted(hist[i][kind].items()))
    report['elapsed_seconds'] = clock() - start
    return report


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--best', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.best.resolve() == args.report.resolve() or args.best.exists() or args.report.exists():
        parser.error('best and report must be distinct new paths')
    fixed = {one.INPUT: one.INPUT_SHA, MANIFEST: MANIFEST_SHA, AUDIT: AUDIT_SHA}
    one.recheck_pins(fixed)
    document = json.loads(one.INPUT.read_bytes())
    if document['n'] != 79 or document['metadata']['normalized_sha256'] != one.INPUT_NORMALIZED:
        raise ValueError('initial identity mismatch')
    original = [tuple(p) for p in document['points']]
    if len(original) != len(set(original)):
        raise ValueError('duplicate initial point')
    manifest = json.loads(MANIFEST.read_bytes())
    if not manifest['accepted'] or manifest['complete_exit_count'] != 3 or len(manifest['exits']) != 3 or manifest['input_sha256'] != one.INPUT_SHA:
        raise ValueError('exit manifest mismatch')
    parents = []
    for exit_doc in manifest['exits']:
        path = (ROOT / exit_doc['path']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('invalid exit path')
        fixed[path] = exit_doc['sha256']
        one.recheck_pins({path: exit_doc['sha256']})
        state = json.loads(path.read_bytes())
        ps = [tuple(p) for p in state['points']]
        if len(ps) != len(set(ps)) or state['n'] != 79:
            raise ValueError('invalid parent state')
        parents.append((set(ps), 6, exit_doc['normalized_sha256'], exit_doc['kind'], tuple(tuple(p) for p in exit_doc['removed'])))
    pin_paths = ('research/score11_deficiency_second_neighborhood.py', 'research/score11_deficiency_neighborhood.py', 'research/score11_deficiency_walk.py', 'src/trade_search.py', 'src/verify.py')
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in pin_paths}
    report = second_census(79, set(original), 5, parents, args.best, started=started, input_sha=one.INPUT_SHA, pins=pins, expected_initial=one.INPUT_NORMALIZED)
    fixed.update({ROOT / p: digest for p, digest in pins.items()})
    one.finalize_identity(report, fixed)
    base.atomic(args.report, report)
    print(json.dumps(report, sort_keys=True))
    return 1 if report['status'] == 'error' else 0


if __name__ == '__main__':
    sys.exit(main())
