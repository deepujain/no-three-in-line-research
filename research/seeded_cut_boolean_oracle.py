"""Fixed five-variable direct-Boolean oracle for seeded-cut continuation tests.

No SAT library, production search helper, or n79 computation is imported.
"""
import hashlib
import itertools
import json
from pathlib import Path

POINTS = ((0, 0), (1, 0), (2, 0), (3, 0), (0, 1))
ORBIT_MAP = (101, 103, 107, 109, 113)
SEED = ((1, 2, 3),)
NEW = ((1, 2, 4), (1, 3, 4), (2, 3, 4))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def selected_assignments(cuts):
    # Fixed exhaustive truth table: exactly three selected out of five variables.
    return [list(chosen) for chosen in itertools.combinations(range(1, 6), 3)
            if all(not set(cut) <= set(chosen) for cut in cuts)]


def fixture():
    stages = []
    for added in range(4):
        cuts = SEED + NEW[:added]
        stages.append({'retained_cuts': 1, 'new_cuts': added, 'total_cuts': 1 + added,
                       'cut_ids': [list(c) for c in cuts],
                       'allowed_exact_three_assignments': selected_assignments(cuts)})
    assert [len(s['allowed_exact_three_assignments']) for s in stages] == [9, 8, 7, 6]
    for cut in SEED + NEW:
        a, b, c = (POINTS[v - 1] for v in cut)
        assert (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0])
    assert [1, 2, 3] not in stages[0]['allowed_exact_three_assignments']
    assert [1, 2, 4] in stages[0]['allowed_exact_three_assignments']
    assert [1, 2, 4] not in stages[1]['allowed_exact_three_assignments']
    assert [1, 2, 5] in stages[-1]['allowed_exact_three_assignments']
    # Both maps give a collinear seed, so geometry alone cannot authorize map reuse.
    changed_map = (109, 103, 107, 101, 113)
    assert digest(ORBIT_MAP) != digest(changed_map)
    original_clause_orbits = [ORBIT_MAP[i-1] for i in SEED[0]]
    changed_clause_orbits = [changed_map[i-1] for i in SEED[0]]
    assert set(original_clause_orbits) != set(changed_clause_orbits)
    return {
        'scope': 'TINY ONLY; direct exact-three truth table on five singleton point labels, not a quarter-orbit search',
        'point_by_local_variable': [list(p) for p in POINTS],
        'local_variable_to_orbit_id': list(ORBIT_MAP),
        'mapping_sha256': digest(ORBIT_MAP),
        'retained_cut_ids': [list(c) for c in SEED],
        'new_cut_sequence': [list(c) for c in NEW],
        'base_exact_three_assignment_count': 10,
        'stages': stages,
        'budget_oracles': [
            {'retained': 1, 'total_cap': 1, 'new_allowance': 0},
            {'retained': 1, 'total_cap': 2, 'new_allowance': 1},
            {'retained': 1, 'total_cap': 4, 'new_allowance': 3},
            {'retained': 181, 'total_cap': 1000, 'new_allowance': 819}],
        'required_error_cases': [
            {'kind': 'retained_cut_violating_model', 'selected_ids': [1, 2, 3], 'violated_cut': [1, 2, 3]},
            {'kind': 'new_cut_repeated_model_after_first_addition', 'selected_ids': [1, 2, 4], 'violated_cut': [1, 2, 4]},
            {'kind': 'duplicate_seed', 'cut_ids': [[1, 2, 3], [1, 2, 3]]},
            {'kind': 'map_identity_changed_even_if_geometry_remains_collinear',
             'changed_map': list(changed_map), 'changed_mapping_sha256': digest(changed_map),
             'original_clause_orbits': original_clause_orbits, 'changed_clause_orbits': changed_clause_orbits}],
        'independent_valid_candidate_after_all_cuts': [1, 2, 5],
        'cut_geometry_checked': 4,
        'production_source_tested': False,
        'n79_formula_or_solver_used': False,
    }


if __name__ == '__main__':
    result = fixture()
    result['oracle_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out = Path(__file__).resolve().parents[1] / 'data/depth12-seeded-cut-tiny-boolean-oracle.json'
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'path': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                      'allowed_counts': [len(s['allowed_exact_three_assignments']) for s in result['stages']],
                      'real_scope_arithmetic_only_allowance': 1000-181}, sort_keys=True))
