"""Independent SOURCE-only evidence; valid geometry is forbidden here."""
import ast
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'research/full_complement_row_domain_n5.py': '36f4639fededa4fd0e239e397acb43478e7131ee4a1d0f798079d73cf34b5b8e',
    'research/full_complement_row_domain_n5_tiny.py': '5d8e5ecbdb419cd9fa8c118e7ce4b2d788344fc7c247c4bee1995c4755fc9fb5',
    'data/full-complement-row-domain-n5-fixture-v1.json': '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37',
}


def identities():
    actual = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PINS}
    assert actual == PINS
    return actual


def main():
    before = identities()
    for name in PINS:
        if name.endswith('.py'):
            source = (ROOT / name).read_text()
            ast.parse(source, filename=name)
            compile(source, name, 'exec')
    from research import full_complement_row_domain_n5 as producer
    from research import full_complement_row_domain_n5_tiny as harness
    trap_calls = []

    def forbidden(*args, **kwargs):
        trap_calls.append(True)
        raise AssertionError('valid geometry is forbidden in independent source review')

    with patch.object(producer, '_collinear', forbidden), patch.object(harness, 'direct_raw', forbidden), \
            patch.object(harness, 'line_map', forbidden), patch.object(harness, 'run_normal', forbidden):
        result = harness.run_pregeometry()
    assert not trap_calls
    assert len(result['rejections']) == 10
    assert len(result['counter_checks']) == 3
    assert len(result['drift_checks']) == 4
    assert len(result['failure_capture_checks']) == 2
    assert result['real_geometric_operations'] == 0

    # Unusable objects prove that the quota check precedes coordinate access.
    stops = []
    for kind in ('determinants', 'line_keys'):
        budget = producer.Budget()
        budget.counts[kind] = producer.LIMITS[kind]
        prior = budget.snapshot()
        try:
            if kind == 'determinants':
                producer._collinear(object(), object(), object(), budget)
            else:
                harness.line_map((object(), object()), budget, 'raw_line_oracle')
        except producer.BudgetExceeded:
            assert budget.snapshot() == prior
            stops.append({'counter': kind, 'refused_before_coordinate_access': True})
        else:
            raise AssertionError('seeded cap failed before coordinate access')
    after = identities()
    evidence = {
        'passed': True,
        'scope': 'Independent SOURCE-only syntax, trapped rejection and synthetic counter checks. No normal fixture geometry.',
        'source_identity_before': before,
        'source_identity_after': after,
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'syntax_compile_passes': 2,
        'pregeometry': result,
        'forbidden_geometry_trap_calls': len(trap_calls),
        'synthetic_stop_before_coordinate_access': stops,
        'real_geometric_operations': 0,
    }
    raw = (json.dumps(evidence, indent=2, sort_keys=True) + '\n').encode('ascii')
    assert len(raw) <= 65536
    output = ROOT / 'data/full-complement-row-domain-n5-pregeometry-independent-v3.json'
    with output.open('xb') as stream:
        stream.write(raw)
    print(json.dumps({'passed': True, 'output': str(output), 'sha256': hashlib.sha256(raw).hexdigest(),
                      'real_geometric_operations': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
