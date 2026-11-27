"""Bounded seeded neutral walk from a valid certificate; no scheduler.

Each completed pass deletes 6..12 points (clipped for tiny fixtures), then
scans shuffled vacant cells greedily. Equal-size valid states may become the
walk state; the best certificate is kept independently. Wall-clock stopping
is not deterministic. Improvements are dual-verified and atomically saved.
"""
import argparse
from collections import Counter, OrderedDict
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.search import _candidate_cost
from src.verify import verify_certificate, verify_certificate_bruteforce
from research.diagonal_secant_checkpoint import atomic, encode


def checked(n, points):
    certificate = {'n': n, 'points': [list(p) for p in sorted(points)]}
    fast = verify_certificate(certificate)
    slow = verify_certificate_bruteforce(certificate)
    if not (fast['valid'] and slow['valid'] and fast['normalized_sha256'] == slow['normalized_sha256']):
        raise ValueError('certificate failed dual verification')
    return certificate, fast['normalized_sha256']


def walk(n, seconds, seed, initial, output, *, history_limit=4096, clock=time.monotonic,
         rng=None, on_pass=None):
    if type(n) is not int or n < 2 or type(seed) is not int:
        raise ValueError('invalid grid or seed')
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('invalid seconds')
    if type(history_limit) is not int or history_limit < 1:
        raise ValueError('invalid history limit')
    started = clock(); deadline = started + seconds
    initial_checks = (verify_certificate(initial), verify_certificate_bruteforce(initial))
    if not all(c['valid'] for c in initial_checks) or initial_checks[0]['normalized_sha256'] != initial_checks[1]['normalized_sha256']:
        raise ValueError('invalid initial certificate')
    best, best_hash = checked(n, initial['points'])
    current = [tuple(p) for p in best['points']]
    current_hash = best_hash
    target = min(n*n, 2*n)
    if len(current) > target:
        raise ValueError('initial exceeds target')
    rng = rng if rng is not None else random.Random(seed)
    history = OrderedDict([(current_hash, None)])
    counts = Counter(); sizes = Counter(); partial_sizes = Counter()
    evaluations = 0; evictions = 0; improvements = []
    while len(best['points']) < target and clock() < deadline:
        count = len(current)
        low, high = min(6, count), min(12, count)
        if not count:
            break
        deleted = rng.randint(low, high)
        removed = set(rng.sample(range(count), deleted))
        trial = [point for i, point in enumerate(current) if i not in removed]
        occupied = set(trial)
        candidates = [(x, y) for x in range(n) for y in range(n) if (x, y) not in occupied]
        rng.shuffle(candidates)
        complete = True
        for point in candidates:
            if clock() >= deadline:
                complete = False
                break
            evaluations += 1
            if _candidate_cost(trial, -1, point) == 0:
                trial.append(point)
                if len(trial) > len(best['points']):
                    candidate, digest = checked(n, trial)
                    candidate['metadata'] = {'method': 'neutral_deletion_greedy_repair',
                                             'seed': seed, 'normalized_sha256': digest,
                                             'novelty_claim': False}
                    atomic(Path(output), encode(candidate))
                    best, best_hash = candidate, digest
                    improvements.append({'point_count': len(trial), 'normalized_sha256': digest})
                    if len(best['points']) == target:
                        break
        if not complete:
            partial_sizes[deleted] += 1; counts['partial'] += 1
            break
        sizes[deleted] += 1; counts['completed'] += 1
        if len(trial) == len(current):
            candidate, digest = checked(n, trial)
            if digest == current_hash:
                counts['same_state'] += 1
            else:
                counts['different_state'] += 1
                if digest in history:
                    counts['seen_in_cache'] += 1
                    history.move_to_end(digest)
                else:
                    counts['new_to_cache'] += 1
                    history[digest] = None
                    if len(history) > history_limit:
                        history.popitem(last=False); evictions += 1
                if rng.random() < 0.5:
                    current = [tuple(p) for p in candidate['points']]
                    current_hash = digest; counts['neutral_accepted'] += 1
                else:
                    counts['neutral_rejected'] += 1
        elif len(trial) < len(current):
            counts['smaller_trial'] += 1
        if len(trial) > len(current):
            current = [tuple(p) for p in best['points']]; current_hash = best_hash
        if on_pass is not None:
            on_pass({'deletions': deleted, 'trial_size': len(trial), 'walk_hash': current_hash})
    # Save the best even if no improvement occurred; atomic replacement never
    # makes a previously persisted improvement smaller.
    best['metadata'] = dict(best.get('metadata', {}), method='neutral_deletion_greedy_repair',
                            seed=seed, normalized_sha256=best_hash, novelty_claim=False)
    atomic(Path(output), encode(best))
    return {'n': n, 'seed': seed, 'seconds_budget': seconds, 'elapsed_seconds': clock()-started,
            'initial_count': len(initial['points']), 'best_count': len(best['points']),
            'best_normalized_sha256': best_hash, 'walk_normalized_sha256': current_hash,
            'deletion_histogram_completed': dict(sorted(sizes.items())),
            'deletion_histogram_partial': dict(sorted(partial_sizes.items())),
            'counts': dict(counts), 'candidate_evaluations': evaluations,
            'hash_cache_capacity': history_limit, 'hash_cache_size': len(history),
            'hash_cache_evictions': evictions, 'improvements': improvements,
            'stopping_reason': 'target_reached' if len(best['points']) == target else 'time_budget',
            'reproducibility': 'seeded choices; wall-clock stopping affects results',
            'novelty_claim': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n', type=int, required=True); p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--seed', type=int, required=True); p.add_argument('--initial', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--report', type=Path, required=True)
    p.add_argument('--history-limit', type=int, default=4096)
    args = p.parse_args()
    if args.output.resolve() == args.initial.resolve() or args.report.resolve() in (args.initial.resolve(), args.output.resolve()):
        p.error('input, output and report must differ')
    result = walk(args.n, args.seconds, args.seed, json.loads(args.initial.read_text()), args.output,
                  history_limit=args.history_limit)
    atomic(args.report, encode(result)); print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
