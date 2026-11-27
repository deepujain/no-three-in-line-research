"""Bounded all-at-most-five deletions repair for one pinned score-11 state."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.score11_cover_repair import load_source, minimal_covers, search_cover, SOURCE_BYTES, SOURCE_NORMALIZED
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import verify_certificate, verify_certificate_bruteforce

HELPER_HASH = 'd1aa42c4ec2cee2f2df8a9f3f4dff3d1519d2611f41a4ae7d1d02ae87727ea74'
REPORT_HASH = '935a7f30e27c4146e8a3f669e3ade60ec015ea001c0f55572ce4b8d41d2c040a'
ARITHMETIC_HASH = '7952ed2a4dd808f74c1ce27f9851c074930bd8d7330805fb50efc09547fa6242'
EXPECTED = {frozenset(((33,78),(42,24),(78,78))),
            frozenset(((33,78),(57,14),(78,78))),
            frozenset(((33,78),(78,0),(78,78)))}


def deletion_sets(points, covers, deadline, clock):
    """Each size-three minimal cover and all distinct supersets through size five."""
    points = set(points); covers = set(map(frozenset, covers))
    if not covers or any(len(c) != 3 or not c <= points for c in covers):
        raise ValueError('expected size-three covers within source')
    result = set(covers)
    for cover in covers:
        extras = sorted(points-cover)
        for k in (1, 2):
            for selected in itertools.combinations(extras, k):
                if clock() >= deadline:
                    raise TimeoutError
                result.add(cover | frozenset(selected))
    return sorted(result, key=lambda x:(len(x), tuple(sorted(x))))


def run(source, predecessor, arithmetic, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds, bool) or not isinstance(seconds,(float,int)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('soft limit must be in (0,25]')
    started = clock(); deadline = started+seconds
    if hashlib.sha256((ROOT/'research/score11_cover_repair.py').read_bytes()).hexdigest() != HELPER_HASH:
        raise ValueError('helper source hash mismatch')
    prior = predecessor.read_bytes()
    if hashlib.sha256(prior).hexdigest() != REPORT_HASH:
        raise ValueError('predecessor report hash mismatch')
    prior_report = json.loads(prior)
    if not prior_report.get('complete') or prior_report.get('status') != 'complete' or prior_report.get('source_normalized_sha256') != SOURCE_NORMALIZED:
        raise ValueError('predecessor incomplete or wrong source')
    prior_covers = {frozenset(map(tuple,c)) for c in prior_report['covers']}
    if prior_covers != EXPECTED or prior_report.get('cover_count') != 3:
        raise ValueError('predecessor cover mismatch')
    evidence = arithmetic.read_bytes()
    if hashlib.sha256(evidence).hexdigest() != ARITHMETIC_HASH:
        raise ValueError('arithmetic report hash mismatch')
    ar = json.loads(evidence)
    if ar.get('source_sha256') != SOURCE_BYTES or ar.get('all_source_hitting_sets_through5') != 35809 or ar.get('minimal_cover_sizes') != {'3':3} or {frozenset(map(tuple,c)) for c in ar['minimal_covers']} != EXPECTED:
        raise ValueError('arithmetic census mismatch')
    points, conflicts = load_source(source)
    report = {'source_bytes_sha256':SOURCE_BYTES, 'source_normalized_sha256':SOURCE_NORMALIZED,
              'predecessor_sha256':REPORT_HASH, 'arithmetic_sha256':ARITHMETIC_HASH, 'helper_sha256':HELPER_HASH,
              'scope':'All deletion sets of at most five points from this source, followed by all valid insertions to 157 or 158.',
              'complete':False, 'status':'incomplete', 'deletion_set_count':None,
              'completed_deletion_sets':0, 'witness_events':0}
    def emit(pts):
        cert = {'n':79, 'points':[list(p) for p in sorted(pts)]}
        checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
        if any(not c['valid'] or c['point_count'] < 157 for c in checks) or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
            raise RuntimeError('witness dual verification failed')
        digest = checks[0]['normalized_sha256']
        cert['metadata'] = {'method':'score11_at_most_five_deletions', 'source_normalized_sha256':SOURCE_NORMALIZED,
                            'normalized_sha256':digest, 'novelty_claim':False}
        path = out/('witness-'+digest+'.json')
        if path.exists():
            if json.loads(path.read_text()) != cert:
                raise RuntimeError('conflicting witness file')
        else:
            atomic(path, encode(cert))
        report['witness_events'] += 1
    try:
        covers = minimal_covers(conflicts, 5, deadline, clock)
        if set(covers) != EXPECTED:
            raise ValueError('recomputed cover census mismatch')
        deletions = deletion_sets(points, covers, deadline, clock)
        if len(deletions) != 35809 or sum(len(d) == 3 for d in deletions) != 3 or sum(len(d) == 4 for d in deletions) != 462 or sum(len(d) == 5 for d in deletions) != 35344:
            raise ValueError('deletion census mismatch')
        report['deletion_set_count'] = len(deletions)
        report['total_candidate_cells'] = 0; report['total_nodes'] = 0
        for deleted in deletions:
            detail = search_cover(79, points, set(deleted), deadline, clock, emit)
            report['total_candidate_cells'] += detail['candidate_cells']
            report['total_nodes'] += detail['nodes']
            report['completed_deletion_sets'] += 1
        report['status'] = 'complete'; report['complete'] = True
    except TimeoutError:
        report['status'] = 'timeout'
    report['elapsed_seconds'] = clock()-started
    atomic(out/'report.json', encode(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True); p.add_argument('--predecessor', type=Path, required=True)
    p.add_argument('--arithmetic', type=Path, required=True); p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--seconds', type=float, required=True)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = run(args.source, args.predecessor, args.arithmetic, args.output_dir, args.seconds)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
