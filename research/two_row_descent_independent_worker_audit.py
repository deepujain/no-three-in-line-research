"""Independent frozen-production SOURCE/TINY comparison; no actual fixture IO."""
from collections import Counter
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import time
from research import two_row_descent_independent_oracle as oracle
from research import two_row_descent75 as worker

WORKER_SHA = 'e122a497bf2da967c4b35cc043f4a13febbd781a8e7baca9d81cda7f2dfcda41'
ORACLE_SHA = 'fa3ed0628c1a305d368653cc1cc8669839dac81047e31d564c994f3745060842'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_trace(points, n, row_cap=512, pair_cap=32):
    expected = oracle.reference_descent(points, n, row_cap, pair_cap)
    events = []; commits = []
    actual = worker.descend(points, n, row_cap, pair_cap, observe=events.append, commit=commits.append)
    for key in ('points', 'U', 'row_started', 'pair_started', 'accepted', 'status'):
        assert actual[key] == expected[key], (key, expected, actual)
    assert events == expected['events']
    assert actual['row_completed'] == actual['row_started']
    assert actual['pair_completed'] == actual['pair_started']
    assert len(commits) == actual['accepted']
    before = points
    for event in commits:
        assert event['before_points'] == before
        assert event['before_score'] == oracle.raw(before)
        assert event['score'] == oracle.raw(event['points']) < event['before_score']
        assert all(p[1] in event['rows'] for p in set(before) ^ set(event['points']))
        oracle.geometry.row_state(event['points'], n)
        before = event['points']
    assert before == actual['points']
    if actual['status'] == 'row_cap':
        assert not actual['row_sweep_complete'] and not actual['pair_scan_complete']
    elif actual['status'] == 'pair_cap':
        assert actual['row_sweep_complete'] and not actual['pair_scan_complete']
    return expected, actual


def interrupts(points, n):
    checks = []; work = {}; baseline_commits = []
    baseline = worker.descend(points, n, check=lambda: checks.append(work.get('phase')), work=work,
                              commit=baseline_commits.append)
    assert baseline['status'] == 'zero'
    expected_boundaries = {points} | {e['points'] for e in baseline_commits}
    for stop in range(1, len(checks)+1):
        calls = 0; commits = []; local_work = {}
        def check():
            nonlocal calls
            calls += 1
            if calls == stop:
                raise worker.SearchStop('synthetic_interrupt')
        actual = worker.descend(points, n, check=check, work=local_work, commit=commits.append)
        assert actual['status'] == 'synthetic_interrupt'
        assert actual['points'] in expected_boundaries
        assert actual['points'] == (commits[-1]['points'] if commits else points)
        assert actual['accepted'] == len(commits)
        assert actual['U'] is None or actual['U'] == oracle.raw(actual['points'])
        assert actual['row_completed'] <= actual['row_started'] <= 512
        assert actual['pair_completed'] <= actual['pair_started'] <= 32
        assert actual['row_started']-actual['row_completed'] in (0, 1)
        assert actual['pair_started']-actual['pair_completed'] in (0, 1)
        if actual['index'] is not None:
            index = {key: tuple(actual['points'][i] for i in range(len(actual['points'])) if mask >> i & 1)
                     for key, mask in actual['index'].items()}
            assert index == oracle.geometry.expected_index(actual['points'], n)
    return {'interruptions': len(checks), 'phases': dict(Counter(checks)),
            'positive_commits': sum(e['score'] > 0 for e in baseline_commits)}


def run():
    started = time.monotonic()
    assert sha(worker.__file__) == WORKER_SHA
    assert sha(oracle.__file__) == ORACLE_SHA
    counts = Counter(); outcomes = Counter(); digest = hashlib.sha256()
    representative = None; max_u = -1
    for n in (2, 3, 4):
        for total in (3, 4):
            expected = sorted(cols for k in ((2,) if total == 4 else (1, 2))
                              for cols in combinations(range(n), k))
            assert list(worker.outer_sets(n, total)) == expected
            counts['merged_streams'] += 1
        for costs in product(range(4), repeat=n):
            for load in (1, 2):
                expected = min((sum(costs[y] for y in ys), ys) for ys in combinations(range(n), load))
                assert worker.best_partner(iter(costs), load) == expected
                counts['partner_minima'] += 1
        for points in oracle.geometry.states(n):
            counts['states'] += 1
            current, index, old_u = worker.build_index(points, n)
            assert current == points and old_u == oracle.raw(points)
            members = {key: tuple(points[i] for i in range(len(points)) if mask >> i & 1)
                       for key, mask in index.items()}
            assert members == oracle.geometry.expected_index(points, n)
            ranks = worker.priorities(points, index, n)
            assert ranks == oracle.priorities(points, n)
            counts['priority_rows'] += n
            counts['priority_pairs'] += n*(n-1)//2
            if old_u > max_u:
                max_u = old_u; representative = (points, n)
            for row in range(n):
                actual = worker.row_optimum(points, index, n, row)
                expected = oracle.row_optimum(points, n, row)
                assert (actual['score'], actual['columns']) == expected['minimum']
                assert actual['points'] == expected['points'] and actual['score'] <= old_u
                counts['row_optima'] += 1
                counts['zero_row_optima'] += actual['zero']
            for r, s in combinations(range(n), 2):
                retained = tuple(p for p in points if p[1] not in (r, s))
                base = oracle.raw(retained)
                t = worker.pair_tables(points, index, n, r, s)
                assert t['retained'] == retained and t['retained_score'] == base == old_u-ranks['M'][r,s]
                assert t['u'] == tuple(oracle.raw(retained+((x,r),))-base for x in range(n))
                assert t['v'] == tuple(oracle.raw(retained+((y,s),))-base for y in range(n))
                direct_cross = [sum(oracle.geometry.determinant((x,r),(y,s),q) == 0 for q in retained)
                                for x in range(n) for y in range(n)]
                assert list(t['cross']) == direct_cross
                counts['cross_cells'] += n*n
                counts['positive_vertical_cross_cells'] += sum(t['cross'][x*n+x] > 0 for x in range(n))
                assignments = list(oracle.pair_assignments(points, n, r, s))
                expected, changed = min(assignments, key=lambda z:z[0])
                actual = worker.pair_optimum(points, index, n, r, s)
                assert (actual['score'], actual['X'], actual['Y']) == expected
                assert actual['points'] == changed and actual['score'] <= old_u
                assert actual['zero'] == (expected[0] == 0)
                counts['row_pairs'] += 1
                counts['direct_assignments'] += len(assignments)
                counts['zero_pair_optima'] += actual['zero']
            expected, actual = compare_trace(points, n)
            outcomes[actual['status']] += 1
            digest.update(json.dumps([n,points,expected],sort_keys=True,separators=(',',':')).encode())
            counts['policy_traces'] += 1
    stuck = ((0,0),(0,1),(0,2),(2,1),(2,3),(3,2),(3,3))
    fixtures = []
    for row_cap, pair_cap in ((512,32),(0,32),(2,32),(3,0),(3,1)):
        expected, actual = compare_trace(stuck, 4, row_cap, pair_cap)
        fixtures.append({'row_cap':row_cap,'pair_cap':pair_cap,
                         'result':{k:v for k,v in actual.items() if k != 'index'}})
    # Cross-state cap tests include genuine multiple strict improvements.
    for row_cap in range(9):
        for pair_cap in range(3):
            compare_trace(*representative, row_cap, pair_cap)
            counts['shared_cap_traces'] += 1
    interruptions = [interrupts(*representative), interrupts(stuck, 4)]
    assert interruptions[0]['positive_commits'] > 0
    # Explicit orchestration stub: no genuine positive full local minimum exists
    # among the complete n2..4 traces. This tests terminal control only.
    old_row, old_pair = worker.row_optimum, worker.pair_optimum
    def current_row(points,index,n,row,check,work):
        return {'score':oracle.raw(points),'columns':tuple(x for x,y in points if y == row),
                'points':points,'zero':False,'enumeration_complete':True}
    def current_pair(points,index,n,r,s,check,work):
        return {'score':oracle.raw(points),'X':tuple(x for x,y in points if y == r),
                'Y':tuple(x for x,y in points if y == s),'points':points,'zero':False,'enumeration_complete':True}
    try:
        worker.row_optimum, worker.pair_optimum = current_row, current_pair
        terminal = worker.descend(stuck,4)
        assert terminal['status'] == 'no_strict_descent' and terminal['U'] == 1
        assert terminal['row_sweep_complete'] and terminal['pair_scan_complete']
        assert terminal['accepted'] == 0
    finally:
        worker.row_optimum, worker.pair_optimum = old_row, old_pair
    assert sha(worker.__file__) == WORKER_SHA and sha(oracle.__file__) == ORACLE_SHA
    return {'scope':'SOURCE/TINY only; no actual coordinates, loader or run invocation.',
            'worker_sha256':WORKER_SHA,'oracle_sha256':ORACLE_SHA,'audit_sha256':sha(__file__),
            'counts':dict(counts),'policy_outcomes':dict(outcomes),
            'all_policy_trajectories_sha256':digest.hexdigest(),
            'cap_fixtures':fixtures,'interruptions':interruptions,
            'positive_terminal_control_stub':{k:v for k,v in terminal.items() if k != 'index'},
            'limits':'Positive terminal is an explicit control stub, not genuine geometric local-minimum evidence. No loader, run lifecycle, owned-memory or n75 performance claim.',
            'elapsed_seconds':time.monotonic()-started,'passed':True}


if __name__ == '__main__':
    result = run()
    path = Path('data/two-row-descent-independent-worker-audit-v2.json')
    assert not path.exists(), 'preserve historical evidence'
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cap_fixtures','positive_terminal_control_stub')},sort_keys=True))
    print(sha(path))
