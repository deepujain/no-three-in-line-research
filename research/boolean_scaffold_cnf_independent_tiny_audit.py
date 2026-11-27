"""Independent semantic CNF audit on synthetic boards; no native solver."""
from collections import Counter, defaultdict
from itertools import combinations, product
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import boolean_scaffold_independent_tiny_oracle as oracle
from research import blocker_guided_eight_arc_scaffold157 as scaffold


def make_inputs(A, points):
    A = tuple(sorted(A)); points = tuple(sorted(points)); pool = []
    for q in points:
        edges = [(i, j) for i, j in combinations(range(len(A)), 2)
                 if oracle.determinant(A[i], A[j], q) == 0]
        neighbors = defaultdict(set)
        for i, j in edges:
            neighbors[i].add(j); neighbors[j].add(i)
        unseen = set(neighbors); groups = []
        while unseen:
            root = min(unseen); group = {root} | neighbors[root]
            assert all(neighbors[v] == group-{v} for v in group)
            unseen -= group; groups.append(tuple(sorted(group)))
        groups.sort()
        pool.append(scaffold.PoolCell(q, sum(len(g)-1 for g in groups),
            tuple(sum(1 << v for v in g) for g in groups),
            tuple((1 << i) | (1 << j) for i, j in edges)))
    arcs = []
    for i, q in enumerate(points):
        for a, b in product(range(len(A)), repeat=2):
            if A[a][0] == q[0] and A[b][1] == q[1]:
                assert A[a][0] != A[b][0] and A[a][1] != A[b][1]
                arcs.append(scaffold.Arc(i, a, b, (1 << a) | (1 << b),
                    (1 << A[a][0]) | (1 << A[b][0]),
                    (1 << A[a][1]) | (1 << A[b][1])))
    tables = {}
    for i, j in combinations(range(len(pool)), 2):
        old = sum(1 << v for v, p in enumerate(A) if not oracle.determinant(points[i], points[j], p))
        new = sum(1 << v for v, p in enumerate(points) if v not in (i, j) and not oracle.determinant(points[i], points[j], p))
        tables[i, j] = old, new
    conflicts = tuple(sum(1 << v for v in t) for t in combinations(range(len(A)), 3)
                      if not oracle.determinant(*(A[v] for v in t)))
    return A, tuple(pool), tuple(arcs), tables, conflicts


def valuation(layout, A, pool, arcs, selected, k):
    selected = set(selected)
    v = {i: False for i in range(1, layout.variables+1)}
    for i in selected:
        v[layout.x(i)] = True
    for i in range(len(pool)):
        v[layout.q(i)] = any(arcs[e].pool == i for e in selected)
    for i in range(len(A)):
        v[layout.d(i)] = any(i in (arcs[e].a, arcs[e].b) for e in selected)
    for i in range(1, len(arcs)+1):
        for j in range(1, min(i, k+1)+1):
            v[layout.z(i, j)] = sum(e < i for e in selected) >= j
    return v


def satisfies(clauses, v):
    return all(any(v[abs(lit)] == (lit > 0) for lit in clause) for clause in clauses)


def check_fixture(m, A, S, points, k, counts):
    args = make_inputs(A, points)
    A, pool, arcs, tables, conflicts = args
    layout = m.Layout(len(arcs), len(pool), len(A), k)
    grouped = tuple(m.iter_clauses(*args, layout))
    clauses = tuple(c for _, c in grouped)
    assert all(all(type(v) is int and 0 < abs(v) <= layout.variables for v in c) for c in clauses)
    assert all(len(c) == len(set(c)) and not set(c) & {-v for v in c} for c in clauses)
    counts['formulae'] += 1; counts['clauses_examined'] += len(clauses)
    # Independently exhaust each OR identity's support and output bits, including
    # empty support lists. This checks both forward and reverse implications.
    for kind, variables in [('q', [layout.q(i) for i in range(len(pool))]),
                            ('d', [layout.d(i) for i in range(len(A))])]:
        for variable in variables:
            identity = [c for group, c in grouped if group == kind and any(abs(v) == variable for v in c)]
            inputs = sorted({abs(v) for c in identity for v in c}-{variable})
            for values in product((False, True), repeat=len(inputs)):
                permitted = []
                for output in (False, True):
                    vals = dict(zip(inputs, values)); vals[variable] = output
                    if satisfies(identity, vals): permitted.append(output)
                    counts['union_identity_assignments'] += 1
                assert permitted == [any(values)]
    decoded_arcs = tuple((pool[a.pool].point, A[a.a], A[a.b]) for a in arcs)
    expected_arcs, records = oracle.enumerate_projection(set(A), S, points, k)
    assert tuple(sorted(decoded_arcs)) == expected_arcs
    expected = {tuple(sorted(record[0])) for record in records if all(record[3])}
    accepted = set()
    for selected in combinations(range(len(arcs)), k):
        picked = tuple(decoded_arcs[e] for e in selected)
        Q, F = oracle.derive(picked); P = (set(A)-F) | Q
        want = oracle.compatible(picked) and oracle.valid(P)
        values = valuation(layout, A, pool, arcs, selected, k)
        got = satisfies(clauses, values)
        assert got == want
        counts['support_sets'] += 1
        if got:
            accepted.add(tuple(sorted(picked)))
            counts['valid_scaffolds'] += 1
            assert len(S-P) == 2*k+1 and len(P-S) == k
            raw = ' '.join(str(i if values[i] else -i) for i in sorted(values))
            parsed = m.parse_model(raw, layout.variables)
            assert parsed == values
            assert m.verify_model(parsed, *args, layout) == tuple(selected)
            counts['complete_model_roundtrips'] += 1
            # Every derived semantic or counter bit is forced. Separate tests
            # below exhaust all counter assignments, rather than only flips.
            for variable in range(len(arcs)+1, layout.variables+1):
                mutated = dict(values); mutated[variable] = not values[variable]
                assert not satisfies(clauses, mutated)
                counts['single_auxiliary_bit_mutations_rejected'] += 1
        elif oracle.compatible(picked):
            classes = oracle.four_classes(set(A), Q, F)
            for i, good in enumerate(classes):
                counts['invalid_class_%d' % i] += not good
    assert accepted == expected
    # Exhaust all x assignments on small catalogs, including wrong cardinality.
    if len(arcs) <= 9:
        for bits in product((False, True), repeat=len(arcs)):
            selected = tuple(i for i, b in enumerate(bits) if b)
            picked = tuple(decoded_arcs[e] for e in selected)
            Q, F = oracle.derive(picked)
            want = len(selected) == k and oracle.compatible(picked) and oracle.valid((set(A)-F) | Q)
            assert satisfies(clauses, valuation(layout, A, pool, arcs, selected, k)) == want
            counts['all_support_boolean_assignments'] += 1


def check_thresholds(m, counts):
    for n in range(1, 5):
        A = {(i, i) for i in range(2*n)}
        points = [(2*i, 2*i+1) for i in range(n)]
        args = make_inputs(A, points)
        assert len(args[2]) == n
        for k in range(1, n+1):
            layout = m.Layout(n, n, 2*n, k)
            zvars = [layout.z(i, j) for i in range(1, n+1) for j in range(1, min(i, k+1)+1)]
            counter = [clause for _, clause in m.iter_clauses(*args, layout)
                       if any(abs(v) in zvars for v in clause)]
            for bits in product((False, True), repeat=n):
                extensions = []
                for aux in product((False, True), repeat=len(zvars)):
                    vals = dict(zip(zvars, aux)); vals.update({layout.x(i): bit for i, bit in enumerate(bits)})
                    if satisfies(counter, vals):
                        extensions.append(vals)
                    counts['threshold_full_assignments'] += 1
                assert len(extensions) == int(sum(bits) == k)
                if extensions:
                    for i in range(1, n+1):
                        for j in range(1, min(i, k+1)+1):
                            assert extensions[0][layout.z(i, j)] == (sum(bits[:i]) >= j)
            counts['exhaustive_threshold_formulae'] += 1


def check_single_model_flow(m, counts):
    from research import fixed_pool_boolean_scaffold157 as gate
    A = {(i, i) for i in range(4)}; S = A | {(3, 2)}
    cases = [('ready', [(1, 2), (3, 0)]), ('matching_obstruction', [(0, 1), (2, 3)])]
    for label, points in cases:
        args = make_inputs(A, points); old_points, pool, arcs, tables, conflicts = args
        assert len(arcs) == 2
        layout = m.Layout(2, 2, 4, 2)
        values = valuation(layout, old_points, pool, arcs, (0, 1), 2)
        raw = ' '.join(str(i if values[i] else -i) for i in sorted(values))
        calls = []
        def child(command, seconds, pins):
            calls.append(command)
            formula = Path(command[command.index('--cnf')+1])
            return {'reason': 'exited', 'returncode': 0, 'cleanup': {'clean': True},
                    'stdout': json.dumps({'answer': 'SAT', 'model': raw,
                        'cnf_sha256': m.digest(formula), 'pgid': os.getpgrp(), 'sid': os.getsid(0)})}
        report = {'sat_invocations': 0, 'checker_invocations': 0, 'counters': gate.old.new_counters()}
        with tempfile.TemporaryDirectory() as tmp, patch.object(gate.native, 'run_child', child):
            out = Path(tmp)
            gate.execute(4, old_points, S, pool, arcs, tables, conflicts, out,
                         report, lambda: None, {}, 25, clock=lambda: 0, seed_count=2)
            encoded = (out/'scaffold.cnf').read_bytes()
            rows = encoded.decode('ascii').splitlines(); header = rows.pop(0).split()
            assert header[:2] == ['p', 'cnf'] and int(header[2]) == layout.variables
            parsed_clauses = []
            for line in rows:
                literals = tuple(map(int, line.split()))
                assert literals[-1] == 0 and all(0 < abs(v) <= layout.variables for v in literals[:-1])
                parsed_clauses.append(literals[:-1])
            assert int(header[3]) == len(parsed_clauses) == report['cnf']['clauses']
            assert sum(map(len, parsed_clauses)) == report['cnf']['literals']
            assert hashlib.sha256(encoded).hexdigest() == report['cnf']['sha256']
            assert parsed_clauses == [v for _, v in m.iter_clauses(*args, layout)]
            assert satisfies(parsed_clauses, values)
            counts['independent_dimacs_roundtrips'] += 1
            assert len(calls) == report['sat_invocations'] == 1 and report['checker_invocations'] == 0
            assert report['complete'] and report['diagnostic_saved'] and report['diagnostic_complete']
            diagnostic = json.loads((out/'valid149-diagnostic.json').read_text())
            md = diagnostic['metadata']
            assert md['point_count'] == 2 and md['source_deleted'] == 5 and md['new_points_outside_source'] == 2
            assert not md['is_full_witness'] and not md['improves_verified_lower_bound'] and not md['root_ready']
            assert oracle.valid(set(map(tuple, diagnostic['points'])))
            assert report['root']['status'] == label
            if label == 'ready':
                ready = json.loads((out/'root-ready149.json').read_text())
                metadata = ready['metadata']; P = set(map(tuple, ready['points']))
                plan = set(map(tuple, metadata['residual_plan']))
                assert metadata['root_ready'] and not metadata['residual_plan_joint_geometry_checked']
                assert all(oracle.valid(P | {p}) for p in plan) and not oracle.valid(P | plan)
                assert report['status'] == 'root_ready'
            else:
                assert not (out/'root-ready149.json').exists()
                assert report['status'] == 'valid_scaffold' and report['root']['matching_cover']['matching_size'] == 1
            counts['stubbed_single_model_pipelines'] += 1


def main():
    # Import only after the implementation has been explicitly frozen for review.
    from research import boolean_scaffold_cnf as m
    counts = Counter()
    from tests.test_boolean_scaffold_independent_tiny_oracle import ProjectionOracleTests
    for A, S, points, k in ProjectionOracleTests().fixtures():
        check_fixture(m, A, S, points, k, counts)
    # Complete small-board source subsets, with two selected arcs where possible.
    grid = set(product(range(3), repeat=2))
    for A in combinations(sorted(grid), 4):
        if any(max(Counter(p[h] for p in A).values()) > 2 for h in (0, 1)):
            continue
        S = set(A) | {max(grid-set(A))}; points = sorted(grid-S)
        check_fixture(m, set(A), S, points, 1, counts)
    # Full support matchings on six rows admit depth-three all-new triples.
    rng = random.Random(20261127)
    grid6 = set(product(range(6), repeat=2))
    for _ in range(20):
        columns = rng.sample(list(range(6)), 6); A = {(i, columns[i]) for i in range(6)}
        S = A | {max(grid6-A)}
        points = rng.sample(sorted(grid6-S), 12)
        check_fixture(m, A, S, points, 3, counts)
    check_thresholds(m, counts)
    check_single_model_flow(m, counts)
    result = {'status': 'PASS', 'counts': dict(counts),
        'scope': 'Pure source/encoding and synthetic tiny boards only; no n79 reconstruction, native solver or search.',
        'pins': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (Path(m.__file__), Path(oracle.__file__), Path(__file__),
                    ROOT/'research/fixed_pool_boolean_scaffold157.py', ROOT/'tests/test_fixed_pool_boolean_scaffold.py')}}
    path = ROOT/'data/boolean-scaffold-cnf-independent-tiny-audit.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
