"""Exact scan of nonuniform one-row/one-column insertions of a valid seed.

Source order m becomes target order m+1. Cuts a,b range from 0 through m:
x maps to x+(x>=a), y maps to y+(y>=b). This map need not preserve validity.
Verified source C4 symmetry permits quotienting cuts by (a,b)->(m-b,a).
Timeouts retain only completed representatives and explicitly report partial scope.
"""

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
from src.verify import normalized_sha256, verify_certificate, verify_certificate_bruteforce
from src.verify import collinear_triples


class ScanTimeout(Exception):
    pass


def _deadline(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise ScanTimeout


def insert_grid_lines(points, source_n, cut_x, cut_y):
    if type(source_n) is not int or source_n < 1:
        raise ValueError("source_n must be a positive integer")
    if any(type(c) is not int or not 0 <= c <= source_n for c in (cut_x, cut_y)):
        raise ValueError("cuts must be integers from zero through source_n")
    result = []
    for x, y in points:
        if type(x) is not int or type(y) is not int or not (0 <= x < source_n and 0 <= y < source_n):
            raise ValueError("source coordinates must be integers inside the source square")
        result.append((x + (x >= cut_x), y + (y >= cut_y)))
    return result


def rotate(points, n):
    return {(n - 1 - y, x) for x, y in points}


def cut_orbit(cut, source_n):
    orbit = set()
    a, b = cut
    for _ in range(4):
        orbit.add((a, b))
        a, b = source_n - b, a
    return sorted(orbit)


def count_conflicts(points, deadline=None):
    """Count every collinear triple once, anchored at its smallest input index."""
    count = 0
    for i, (x, y) in enumerate(points):
        _deadline(deadline)
        directions = {}
        for xx, yy in points[i + 1:]:
            dx, dy = xx - x, yy - y
            divisor = math.gcd(dx, dy)
            if not divisor:
                raise ValueError("duplicate point")
            dx, dy = dx // divisor, dy // divisor
            if dx < 0 or (dx == 0 and dy < 0):
                dx, dy = -dx, -dy
            key = (dx, dy)
            previous = directions.get(key, 0)
            count += previous
            directions[key] = previous + 1
    return count


def gap_blockers(points, gap):
    """Disjoint blocking index pairs for a valid seed and its unoccupied gap."""
    groups = {}
    for i, (x, y) in enumerate(points):
        dx, dy = x - gap[0], y - gap[1]
        divisor = math.gcd(dx, dy)
        if not divisor:
            raise ValueError("gap occupied")
        dx, dy = dx // divisor, dy // divisor
        if dx < 0 or (dx == 0 and dy < 0):
            dx, dy = -dx, -dy
        groups.setdefault((dx, dy), []).append(i)
    if any(len(group) > 2 for group in groups.values()):
        raise ValueError("gap_blockers requires a valid seed")
    return sorted(tuple(group) for group in groups.values() if len(group) == 2)


def minimal_hitting_sets(triples, budget):
    """All inclusion-minimal triple hitting sets of size at most budget."""
    solutions = set()
    def visit(chosen, uncovered):
        if not uncovered:
            solutions.add(frozenset(chosen))
            return
        if len(chosen) >= budget:
            return
        for index in uncovered[0]:
            visit(chosen | {index}, [triple for triple in uncovered if index not in triple])
    visit(set(), list(triples))
    return sorted((s for s in solutions if not any(t < s for t in solutions)),
                  key=lambda s: (len(s), sorted(s)))


def validate_repair_source(seed, scan):
    checks = [verify_certificate(seed), verify_certificate_bruteforce(seed)]
    if not all(check['valid'] for check in checks):
        raise ValueError('repair source failed independent validation')
    digest = checks[0]['normalized_sha256']
    if scan.get('source_normalized_sha256') != digest:
        raise ValueError('source seed hash does not match scan provenance')
    return digest


def classify_cover_frontier(seed, scan, budget=5, seconds=20):
    """Classify minimal covers without expanding their deletion supersets."""
    digest = validate_repair_source(seed,scan)
    started = time.monotonic()
    deadline = started+seconds
    records = sorted((r for r in scan['records'] if r['conflict_count']),
                     key=lambda r:(r['conflict_count'],r['cut']))
    result = {'audit':'nonuniform_embedding_minimal_cover_classification',
              'source_normalized_sha256':digest,'cover_budget':budget,
              'total_representatives':len(records),'status':'incomplete',
              'records':[],'seconds_budget':seconds}
    try:
        for record in records:
            _deadline(deadline)
            points = insert_grid_lines(seed['points'],seed['n'],*record['cut'])
            triples = collinear_triples(points)
            if len(triples) != record['conflict_count']:
                raise ValueError('scan conflict count does not match source/cut')
            covers = minimal_hitting_sets(triples,budget)
            item = {'cut':record['cut'],'conflict_count':len(triples),
                    'equivalent_cuts':record['equivalent_cuts'],
                    'minimal_covers':[sorted(c) for c in covers],
                    'minimum_cover_size_through_budget':min(map(len,covers),default=None),
                    'exact_budget_deletion_count_upper_bound':sum(
                        math.comb(len(points)-len(c),budget-len(c)) for c in covers)}
            result['records'].append(item)
        result['status']='complete'
    except ScanTimeout:
        result['status']='timeout_incomplete'
    result['elapsed_seconds']=time.monotonic()-started
    return result


def stream_cover_repairs(seed, scan, cut, base_deletion_indices, deletion_count=5,
                        start_offset=0, max_cases=20000, seconds=20,
                        expected_source_order_sha256=None, on_certificate=None):
    """Memory-bounded exact-size supersets of one cover, with numeric resume.

    The resume offset indexes lexicographic combinations of non-base original
    point indices. It advances only when all addition subsets for that deletion
    set finish. At most the first certificate for each target size is retained.
    """
    digest=validate_repair_source(seed,scan)
    ordered_digest=hashlib.sha256(json.dumps({'n':seed['n'],'points':seed['points']},
                                sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if start_offset and expected_source_order_sha256 != ordered_digest:
        raise ValueError('resuming requires matching ordered source hash')
    if any(type(v) is not int or v<0 for v in (deletion_count,start_offset,max_cases)):
        raise ValueError('counts and offsets must be nonnegative integers')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('seconds must be finite and nonnegative')
    started=time.monotonic()
    deadline=started+seconds
    points=insert_grid_lines(seed['points'],seed['n'],*cut)
    n=seed['n']+1
    base=frozenset(base_deletion_indices)
    if any(type(i) is not int or not 0<=i<len(points) for i in base):
        raise ValueError('base indices outside seed')
    if not len(base)<=deletion_count<=len(points):
        raise ValueError('deletion count incompatible with base or seed')
    triples=collinear_triples(points)
    if not all(base.intersection(t) for t in triples):
        raise ValueError('base does not hit all existing conflicts')
    minimal=minimal_hitting_sets(triples,deletion_count)
    optional=[i for i in range(len(points)) if i not in base]
    extra_count=deletion_count-len(base)
    total=math.comb(len(optional),extra_count)
    if start_offset>total:
        raise ValueError('offset exceeds deletion-set count')
    result={'audit':'streamed_single_cover_exact_deletion_repair',
            'source_normalized_sha256':digest,'cut':list(cut),'base_deletion_indices':sorted(base),
            'source_order_sha256':ordered_digest,
            'exact_deletion_count':deletion_count,'total_deletion_sets':total,
            'base_is_unique_minimal_cover_through_budget':minimal==[base],
            'enumeration_order':'lexicographic itertools.combinations of increasing non-base source indices',
            'start_offset':start_offset,'next_offset':start_offset,'completed_deletion_sets':0,
            'max_cases':max_cases,'seconds_budget':seconds,'status':'incomplete',
            'tested_addition_subsets':{str(len(points)+g):0 for g in (1,2)},
            'valid_addition_subsets':{str(len(points)+g):0 for g in (1,2)},
            'max_individually_addable_pool':0,'found_certificates':[]}
    found_sizes=set()
    def collinear(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
    try:
        choices=itertools.islice(itertools.combinations(optional,extra_count),start_offset,None)
        for extras in choices:
            _deadline(deadline)
            if result['completed_deletion_sets']>=max_cases:
                result['status']='case_limit_incomplete'
                break
            deletion=base|set(extras)
            retained=[p for i,p in enumerate(points) if i not in deletion]
            occupied=set(retained)
            columns=[0]*n
            rows=[0]*n
            for x,y in retained:
                columns[x]+=1
                rows[y]+=1
            pool=[p for p in itertools.product([x for x in range(n) if columns[x]<2],
                                               [y for y in range(n) if rows[y]<2])
                  if p not in occupied and not gap_blockers(retained,p)]
            result['max_individually_addable_pool']=max(result['max_individually_addable_pool'],len(pool))
            pair_ok={(a,b):not any(collinear(a,b,c) for c in retained)
                     for a,b in itertools.combinations(pool,2)}
            local_tested={str(len(points)+g):0 for g in (1,2)}
            local_valid={str(len(points)+g):0 for g in (1,2)}
            for gain in (1,2):
                target=str(len(points)+gain)
                for additions in itertools.combinations(pool,deletion_count+gain):
                    _deadline(deadline)
                    local_tested[target]+=1
                    if any(not pair_ok[a,b] for a,b in itertools.combinations(additions,2)):
                        continue
                    if any(collinear(a,b,c) for a,b,c in itertools.combinations(additions,3)):
                        continue
                    local_valid[target]+=1
                    if target not in found_sizes:
                        certificate={'n':n,'points':[list(p) for p in retained+list(additions)],
                                     'metadata':{'method':'streamed_embedding_cover_repair','cut':list(cut),
                                                 'deleted_embedding_indices':sorted(deletion),'novelty_claim':False}}
                        checks=[verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
                        if not all(c['valid'] for c in checks):
                            raise RuntimeError('streamed candidate failed independent verification')
                        certificate['metadata']['normalized_sha256']=checks[0]['normalized_sha256']
                        result['found_certificates'].append(certificate)
                        found_sizes.add(target)
                        if on_certificate:
                            on_certificate(certificate)
            for target in local_tested:
                result['tested_addition_subsets'][target]+=local_tested[target]
                result['valid_addition_subsets'][target]+=local_valid[target]
            result['completed_deletion_sets']+=1
            result['next_offset']+=1
        else:
            result['status']='complete'
    except ScanTimeout:
        result['status']='timeout_incomplete'
    result['elapsed_seconds']=time.monotonic()-started
    return result


def repair_low_conflict(seed, scan, seconds=20, max_deletions=3, top=10):
    """Exact bounded deletion repairs for the selected lowest-conflict cuts.

    All deletion supersets through the budget are included; all additions
    meeting row/column capacity are individually and jointly checked. A timeout
    leaves the current embedding incomplete, never a negative proof for it.
    """
    validate_repair_source(seed,scan)
    started = time.monotonic()
    deadline = started + seconds
    n = seed['n'] + 1
    count = len(seed['points'])
    records = scan['lowest_conflict_invalid_representatives'][:top]
    report = {'audit': 'low_conflict_embedding_exact_deletion_repair',
              'target_n': n, 'max_deletions': max_deletions,
              'source_normalized_sha256': scan['source_normalized_sha256'],
              'selected_cuts': [r['cut'] for r in records],
              'status': 'incomplete', 'embeddings': [], 'found_certificates': [],
              'seconds_budget': seconds, 'model': 'gpt-6-astra', 'reasoning': 'high'}
    try:
        for record in records:
            _deadline(deadline)
            cut = record['cut']
            points = insert_grid_lines(seed['points'], seed['n'], *cut)
            triples = collinear_triples(points)
            if len(triples) != record['conflict_count']:
                raise RuntimeError('independent conflict list differs from scan count')
            minimal = minimal_hitting_sets(triples, max_deletions)
            deletions = set()
            for base in minimal:
                optional = [i for i in range(count) if i not in base]
                for size in range(max_deletions-len(base)+1):
                    for extra in itertools.combinations(optional,size):
                        _deadline(deadline)
                        deletions.add(tuple(sorted(base | set(extra))))
            item = {'cut':cut,'conflict_count':len(triples),'status':'incomplete',
                    'minimal_hitting_sets':[sorted(s) for s in minimal],
                    'deletion_set_count':len(deletions),'completed_deletion_sets':0,
                    'max_individually_addable_pool':0,
                    'max_retained_plus_pool_count':0,
                    'tested_addition_subsets':{str(count+1):0,str(count+2):0}}
            report['embeddings'].append(item)
            for deletion in sorted(deletions,key=lambda d:(len(d),d)):
                _deadline(deadline)
                retained = [p for i,p in enumerate(points) if i not in deletion]
                occupied = set(retained)
                columns = [0]*n
                rows = [0]*n
                for x,y in retained:
                    columns[x] += 1
                    rows[y] += 1
                pool = []
                for candidate in itertools.product([x for x in range(n) if columns[x]<2],
                                                   [y for y in range(n) if rows[y]<2]):
                    if candidate not in occupied and not gap_blockers(retained,candidate):
                        pool.append(candidate)
                item['max_individually_addable_pool'] = max(item['max_individually_addable_pool'],len(pool))
                item['max_retained_plus_pool_count'] = max(item['max_retained_plus_pool_count'],len(retained)+len(pool))
                pair_ok = {}
                def collinear(a,b,c):
                    return (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])
                for a,b in itertools.combinations(pool,2):
                    pair_ok[a,b] = not any(collinear(a,b,c) for c in retained)
                for gain in (1,2):
                    for additions in itertools.combinations(pool,len(deletion)+gain):
                        _deadline(deadline)
                        item['tested_addition_subsets'][str(count+gain)] += 1
                        if any(not pair_ok[a,b] for a,b in itertools.combinations(additions,2)):
                            continue
                        if any(collinear(a,b,c) for a,b,c in itertools.combinations(additions,3)):
                            continue
                        certificate = {'n':n,'points':[list(p) for p in retained+list(additions)],
                                       'metadata':{'method':'nonuniform_embedding_exact_repair','cut':cut,
                                                   'deleted_embedding_indices':list(deletion),
                                                   'novelty_claim':False}}
                        checks = [verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
                        if not all(check['valid'] for check in checks):
                            raise RuntimeError('repair failed independent verification')
                        certificate['metadata']['normalized_sha256'] = checks[0]['normalized_sha256']
                        report['found_certificates'].append(certificate)
                item['completed_deletion_sets'] += 1
            item['status'] = 'complete'
        report['status'] = 'complete'
    except ScanTimeout:
        report['status'] = 'timeout_incomplete'
    report['elapsed_seconds'] = time.monotonic()-started
    return report


def audit(seed, seconds=45, use_symmetry=True, on_certificate=None):
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("seconds must be finite and nonnegative")
    started = time.monotonic()
    deadline = started + seconds
    source_checks = [verify_certificate(seed), verify_certificate_bruteforce(seed)]
    if not all(check['valid'] for check in source_checks):
        raise ValueError("invalid source seed")
    m = seed['n']
    points = list(map(tuple, seed['points']))
    if len(points) != 2 * m:
        raise ValueError("source must contain exactly 2m points")
    invariant = rotate(points, m) == set(points)
    symmetry_used = bool(use_symmetry and invariant)
    all_cuts = list(itertools.product(range(m + 1), repeat=2))
    representatives = [cut for cut in all_cuts
                       if not symmetry_used or cut == min(cut_orbit(cut, m))]
    report = {'audit': 'exact_nonuniform_row_column_insertion',
              'source_n': m, 'target_n': m + 1, 'source_point_count': len(points),
              'source_normalized_sha256': source_checks[0]['normalized_sha256'],
              'source_verified_by_both_methods': True, 'source_c4_invariant': invariant,
              'symmetry_quotient_used': symmetry_used,
              'cut_rotation': '(a,b) -> (source_n-b,a)',
              'total_embeddings': len(all_cuts), 'total_representatives': len(representatives),
              'completed_representatives': 0, 'completed_embeddings_by_proved_symmetry': 0,
              'valid_representatives': [], 'valid_embedding_count': 0,
              'lowest_conflict_invalid_representatives': [], 'records': [],
              'found_certificates': [], 'status': 'incomplete', 'seconds_budget': seconds,
              'model': 'gpt-6-astra', 'reasoning': 'high', 'novelty_claim': False}
    try:
        for cut in representatives:
            _deadline(deadline)
            transformed = insert_grid_lines(points, m, *cut)
            conflicts = count_conflicts(transformed, deadline)
            orbit = cut_orbit(cut, m) if symmetry_used else [cut]
            record = {'cut': list(cut), 'equivalent_cuts': [list(c) for c in orbit],
                      'conflict_count': conflicts}
            if conflicts == 0:
                pairs = gap_blockers(transformed, cut)
                record['gap_blocker_count'] = len(pairs)
                record['gap_blocker_indices'] = [list(pair) for pair in pairs]
                record['normalized_sha256'] = normalized_sha256(m + 1, transformed)
                report['valid_representatives'].append(dict(record))
                report['valid_embedding_count'] += len(orbit)
                if not pairs:
                    certificate = {'n': m + 1, 'points': [list(p) for p in transformed + [cut]],
                                   'metadata': {'method': 'nonuniform_row_column_insertion_plus_gap',
                                                'cut': list(cut), 'novelty_claim': False}}
                    checks = [verify_certificate(certificate), verify_certificate_bruteforce(certificate)]
                    if not all(check['valid'] for check in checks):
                        raise RuntimeError('gap insertion failed independent verification')
                    certificate['metadata']['normalized_sha256'] = checks[0]['normalized_sha256']
                    certificate['metadata']['validation'] = [check['algorithm'] for check in checks]
                    report['found_certificates'].append(certificate)
                    if on_certificate:
                        on_certificate(certificate)
            else:
                best = report['lowest_conflict_invalid_representatives']
                best.append(dict(record))
                best.sort(key=lambda r: (r['conflict_count'], r['cut']))
                del best[10:]
            report['records'].append(record)
            report['completed_representatives'] += 1
            report['completed_embeddings_by_proved_symmetry'] += len(orbit)
        report['status'] = 'complete'
    except ScanTimeout:
        report['status'] = 'timeout_incomplete'
    report['elapsed_seconds'] = time.monotonic() - started
    report['scope'] = ('Only the stated source and single inserted row/column embeddings; '
                       'validity and conflict counts of equivalent cuts follow from checked C4 invariance. '
                       'No conclusion about repairs of invalid embeddings, other seeds, or global existence.')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, default=ROOT / 'data/published-n78.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/embedding-audit.json')
    parser.add_argument('--seconds', type=float, default=45)
    args = parser.parse_args(argv)
    seed = json.loads(args.seed.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def found(certificate):
        a, b = certificate['metadata']['cut']
        path = args.output.parent / f'embedding-candidate-n{certificate["n"]}-cut-{a}-{b}.json'
        path.write_text(json.dumps(certificate, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'event': 'verified_candidate', 'path': str(path),
                          'point_count': len(certificate['points'])}), flush=True)
    report = audit(seed, args.seconds, on_certificate=found)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'elapsed_seconds',
          'completed_representatives', 'completed_embeddings_by_proved_symmetry',
          'valid_embedding_count')}, sort_keys=True))
    return 0 if report['status'] == 'complete' else 2


if __name__ == '__main__':
    sys.exit(main())
