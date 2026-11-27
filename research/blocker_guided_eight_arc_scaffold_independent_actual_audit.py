"""Assigned fixed-artifact preprocessing audit; never invoke scaffold search."""
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import blocker_guided_eight_arc_scaffold157 as m
from research.near_quarter_packed_worker import validate_gate


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def h(p):
    return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def read(p):
    return json.loads((ROOT/p).read_text())


def det(a, b, c):
    return a[0]*(b[1]-c[1])+b[0]*(c[1]-a[1])+c[0]*(a[1]-b[1])


def main():
    started = time.monotonic()
    rp = 'data/blocker-guided-eight-arc-scaffold157-v1/report.json'
    ep = 'data/experiments/shepherd-blocker-guided-eight-arc-scaffold157-v1.json'
    fixed = {rp: 'b98c5d0b4b228d3bba4f625bd1f5e40891db178cd63296f2bb0cffefedb8aea9',
             ep: '1f38a57a8f0d223a2606e17a8e1bfa570c4a61bea77dedcebbee07e66975c516'}
    assert all(h(p) == sha for p, sha in fixed.items())
    r = read(rp); e = read(ep); c = r['counters']
    assert e['status'] == 'completed' and e['sources_unchanged'] is True
    assert e['argv'] == ['.venv/bin/python', 'research/blocker_guided_eight_arc_scaffold157.py', '--seconds', '25', '--output-dir', 'data/blocker-guided-eight-arc-scaffold157-v1']
    assert datetime.fromisoformat(e['started_at']) < datetime.fromisoformat(e['finished_at'])
    gate = e['gate']
    assert gate['gate_status'] == 'worker_error' and gate['returncode'] == 2
    # Preserve the original cooperative-cap receipt. Validate other resource and
    # cleanup fields using a local normal-exit substitution only.
    normal = dict(gate, gate_status='exited', returncode=0)
    validate_gate(normal, 30, 256)
    assert e['job']['seconds'] == 30 and 0 < r['elapsed_seconds'] <= e['elapsed_seconds'] < 30
    manifest = read('data/blocker-guided-eight-arc-scaffold157-source-pins.json')
    assert len(manifest) == 26 and len(e['sources_before']) == 27
    assert all(e['sources_before'][p] == sha for p, sha in manifest.items())
    assert all(h(p) == sha for p, sha in e['sources_before'].items())
    assert len(r['pins']) == 7 and all(h(p) == sha for p, sha in r['pins'].items())
    historical = {}
    for path in ('data/conflict-directed-sixteen-cycle-rebuild157-source-pins.json',
                 'data/source-disjoint-matching-rebuild157-source-pins.json'):
        entries = read(path)
        assert all(h(p) == sha for p, sha in entries.items())
        historical[path] = len(entries)
    heads = []
    for chain, audit in [('data/packed-readonly-n79-r1.chain', 'data/packed-readonly-chain-main600-r2-independent-audit.json'),
                         ('data/packed-readonly-n79-middle-d1541.chain', 'data/packed-middle-d1541-chain600-r2-independent-audit.json')]:
        path = chain+'/accepted.json'; sha = read(audit)['final_head_sha']
        assert h(path) == sha
        heads.append({'path': path, 'sha256': sha})
    a = read('data/score11-deficiency-walk-seed279157-v1/best-state.json')
    s = read('data/trades-n79-seed270079-state.json')
    A = tuple(sorted(map(tuple, a['points']))); S = set(map(tuple, s['points']))
    assert a['n'] == s['n'] == 79 and len(A) == len(set(A)) == 157 and len(S) == len(s['points']) == 158
    assert all(type(x) is int and type(y) is int and 0 <= x < 79 and 0 <= y < 79 for x, y in S)
    assert set(A) < S and S-set(A) == {(78, 78)}
    assert all(Counter(p[i] for p in A) == Counter({**{j: 2 for j in range(78)}, 78: 1}) for i in (0, 1))
    assert all(Counter(p[i] for p in S) == Counter({j: 2 for j in range(79)}) for i in (0, 1))
    for P, key in ((A, 'input_normalized_sha256'), (S, 'source_normalized_sha256')):
        assert hashlib.sha256(canonical({'n': 79, 'points': sorted(P)})).hexdigest() == r[key]
    conflicts = [t for t in combinations(A, 3) if not det(*t)]
    assert len(conflicts) == 5
    for v in r['input_validation'] + a['validators']:
        assert v['conflict_count'] == 5 and v['point_count'] == 157 and not v['valid'] and not v['errors']
        assert v['normalized_sha256'] == r['input_normalized_sha256']
        assert sorted(tuple(sorted(map(tuple, t['points']))) for t in v['conflicts']) == conflicts

    # Reconstruct the completed preprocessing only. Solve old-pair determinant
    # equations at integer x slices; no primitive direction grouping is reused.
    blocked_pairs = {q: [] for q in product(range(79), repeat=2) if q not in S}
    slices = pair_hits = 0
    for i, j in combinations(range(len(A)), 2):
        u, v = A[i], A[j]; dx = v[0]-u[0]; dy = v[1]-u[1]
        if dx == 0:
            line = ((u[0], y) for y in range(79))
        else:
            points = []
            for x in range(79):
                slices += 1; num = dy*(x-u[0])
                if num % dx == 0:
                    y = u[1]+num//dx
                    if 0 <= y < 79:
                        points.append((x, y))
            line = points
        for q in line:
            if q in blocked_pairs:
                assert det(u, v, q) == 0
                blocked_pairs[q].append((i, j)); pair_hits += 1
    candidates = []; all_buckets = {}; bucket_count = 0
    for q, pairs in blocked_pairs.items():
        graph = defaultdict(set)
        for i, j in pairs:
            graph[i].add(j); graph[j].add(i)
        unseen = set(graph); buckets = []
        while unseen:
            todo = [min(unseen)]; members = set()
            while todo:
                v = todo.pop()
                if v in members:
                    continue
                members.add(v); todo.extend(graph[v]-members)
            unseen -= members
            assert 2 <= len(members) <= 4
            assert all(j in graph[i] for i, j in combinations(members, 2))
            buckets.append(tuple(sorted(members)))
        buckets.sort(); bucket_count += len(buckets)
        lower = sum(len(b)-1 for b in buckets)
        all_buckets[q] = buckets
        if lower <= 16:
            candidates.append((lower, q))
    selected = sorted(candidates)[:64]
    assert r['pool'] == [{'lower': lower, 'point': list(q)} for lower, q in selected]
    assert len(blocked_pairs) == c['pool_cells_completed'] == c['pool_cells_started'] == 6083
    assert bucket_count == c['pool_bucket_checks_completed'] == c['pool_bucket_checks_started'] == 55307
    assert c['directions_completed'] == c['directions_started'] == 6083*157
    pool = []; direct_checks = 0
    for lower, q in selected:
        pairs = tuple(blocked_pairs[q]); buckets = all_buckets[q]
        exact_pairs = tuple((i, j) for i, j in combinations(range(len(A)), 2) if not det(A[i], A[j], q))
        direct_checks += len(A)*(len(A)-1)//2
        assert pairs == exact_pairs and len(pairs) <= 2*lower and len(buckets) <= lower
        masks = tuple(sum(1 << i for i in b) for b in buckets)
        assert m.partition(A, q, m.new_counters(), lambda: None) == masks
        pool.append(m.PoolCell(q, lower, masks, tuple((1 << i) | (1 << j) for i, j in pairs)))
    cert = r['pool_matching_cover']; M = list(map(tuple, cert['matching']))
    U, V = cert['cover_rows'], cert['cover_columns']; points = {q for _, q in selected}
    assert len(M) == cert['matching_size'] == 24 and set(M) <= points
    assert len({x for x, y in M}) == len({y for x, y in M}) == 24
    assert U == sorted(set(U)) and V == sorted(set(V)) and all(type(i) is int and 0 <= i < 79 for i in U+V)
    assert len(U)+len(V) == 24 and all(x in U or y in V for x, y in points)
    expected_arcs = sorted((lower, q, a, b) for lower, q in selected for a in A for b in A if a[0] == q[0] and b[1] == q[1])
    counter = m.new_counters(); arcs = m.make_arcs(A, pool, counter, lambda: None)
    assert [(pool[a.pool].lower, pool[a.pool].point, A[a.a], A[a.b]) for a in arcs] == expected_arcs
    assert len(arcs) == r['support_arc_count'] == c['support_choices_started'] == c['support_choices_completed'] == 246
    tables = m.make_tables(A, pool, counter, lambda: None)
    independent_tables = []
    for (i, j), (old, new) in tables.items():
        q, t = pool[i].point, pool[j].point
        expected_old = sum(1 << h for h, p in enumerate(A) if not det(q, t, p))
        expected_new = sum(1 << h for h, p in enumerate(pool) if h not in (i, j) and not det(q, t, p.point))
        assert (old, new) == (expected_old, expected_new)
        independent_tables.append([i, j, hex(old), hex(new)])
    assert len(tables) == 2016
    for key, value in [('table_old_points', 316512), ('table_pool_points', 129024)]:
        assert c[key+'_started'] == c[key+'_completed'] == counter[key+'_completed'] == value
    assert r['status'] == 'arc_attempt_cap' and r['complete'] is False and r['closure'] is False
    assert r['scaffold_search_exhausted'] is False and r['root_state_restored'] is True
    assert r['ready_scaffold'] is None and r['roots'] == []
    assert all(r[k] is True for k in ('identity_valid', 'source_validation_complete', 'pool_scan_complete', 'pool_matching_complete', 'supports_complete', 'pair_tables_complete'))
    assert (r['n'], r['pool_limit'], r['arc_limit'], r['root_limit'], r['seed_count'], r['shared_soft_seconds']) == (79, 64, 4096, 4, 8, 25)
    assert c['arc_attempts_started'] == c['arc_attempts_completed'] == 4096
    assert c['arc_admissions'] == c['arc_rollbacks'] == 20 and c['maximum_seeded'] == 7
    assert all(c[k] == 0 for k in c if k.startswith(('root_', 'candidate_', 'insertions_')))
    assert c['complete_scaffold_orderings'] == c['duplicate_scaffolds'] == 0
    assert all(c[k] == c[k.replace('_started', '_completed')] for k in c if k.endswith('_started'))
    assert sorted(p.name for p in (ROOT/Path(rp).parent).iterdir()) == ['report.json']
    assert all(h(p) == sha for p, sha in {**fixed, **e['sources_before'], **r['pins']}.items())
    result = {
        'accepted': True, 'scope': 'Fixed completed preprocessing, saved certificate, identities and guard audited; search trajectory not replayed.',
        'report_sha256': h(rp), 'receipt_sha256': h(ep), 'receipt_source_pins': 27, 'manifest_pins': 26, 'report_pins': 7,
        'historical_manifests_verified': historical, 'accepted_chain_heads_unchanged': heads,
        'initial_conflict_count': 5, 'initial_conflicts': conflicts,
        'outside_cells': len(blocked_pairs), 'all_nontrivial_buckets': bucket_count,
        'independent_integer_x_slices': slices, 'outside_old_pair_incidences': pair_hits,
        'selected_pool_direct_pair_determinants': direct_checks,
        'pool_order_and_lower_bounds_equal': True, 'pool_matching_size_and_cover_size': 24,
        'support_arcs': len(arcs), 'support_arcs_canonical_sha256': hashlib.sha256(canonical(expected_arcs)).hexdigest(),
        'pair_table_entries': len(tables), 'pair_table_determinants': 445536,
        'pair_tables_canonical_sha256': hashlib.sha256(canonical(independent_tables)).hexdigest(),
        'unsaved_preprocessing_note': 'Buckets/supports/tables are independently reconstructed and compared to pinned pure helpers; no persisted table bytes exist.',
        'source_attributed_unreplayed_search_counters': {k: c[k] for k in ('arc_attempts_started', 'arc_admissions', 'arc_rollbacks', 'maximum_seeded', 'pair_lookups_completed', 'forced_points_completed', 'bucket_bounds_completed', 'clauses_completed')},
        'root_checks': 0, 'ready149': None, 'witness157': None, 'closure': False,
        'guard': {'original_status': gate['gate_status'], 'original_returncode': gate['returncode'],
                  'cooperative_cap_exit': True, 'outer_seconds': e['elapsed_seconds'], 'peak_sampled_rss_kib': gate['peak_sampled_rss_kib'], 'cleanup_status': gate['cleanup_status']},
        'decision': 'Curtail this declared gate. Depth seven is an unpersisted partial prefix with possible unhit clauses, not a verified150 scaffold or near-completion certificate. Low cost establishes resource headroom only. No unchanged retry, cap escalation or completion allocation is justified by this result alone.',
        'search_replayed': False, 'scaffold_constructed': False, 'completion_search_run': False,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'audit_elapsed_seconds': time.monotonic()-started}
    out = ROOT/'data/blocker-guided-eight-arc-scaffold157-v1-independent-actual-audit.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('initial_conflicts', 'accepted_chain_heads_unchanged')}, sort_keys=True))
    print('audit_sha256', hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
