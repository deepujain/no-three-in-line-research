"""Additional tiny reference fixtures with a strictly positive historical best.

The original preparation's injected best=0 states stress algebra but cannot occur
in a live worker, which stops at zero. Use these for production policy comparison.
"""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from research import row_block_independent_oracle as oracle


def tuple_tree(value):
    return tuple(tuple_tree(v) for v in value) if isinstance(value, list) else value


def run():
    records = []
    cap_rejections = 0
    split_comparisons = 0
    for n in (3, 4):
        points = next(p for p in oracle.states(n) if oracle.score(p)[0] > 1)
        best = next(p for p in oracle.states(n) if oracle.score(p)[0] == 1)
        for step, stagnation in ((0, 0), (15, 0), (0, 31), (15, 31)):
            old = oracle.boundary(points, n, best_points=best, step=step, stagnation=stagnation)
            old_dict = asdict(old)
            new = oracle.reference_step(old)
            assert asdict(old) == old_dict
            if new.penalties:
                for kwargs in ({'max_keys': 0}, {'max_weight': 1}):
                    try:
                        oracle.reference_step(old, **kwargs)
                    except oracle.OracleCap:
                        cap_rejections += 1
                    else:
                        raise AssertionError('missing transaction cap')
                    assert asdict(old) == old_dict
            encoded = json.dumps(asdict(new), separators=(',', ':'), sort_keys=True)
            decoded = json.loads(encoded)
            restored = oracle.Boundary(**{key: tuple_tree(value) for key, value in decoded.items()})
            assert restored == new
            assert oracle.reference_step(restored) == oracle.reference_step(new)
            split_comparisons += 1
            records.append({'old': old_dict, 'new': asdict(new)})
    return {'scope': 'tiny-only reference policy and synthetic serialization; no production comparison',
            'reason': 'Production comparison fixtures keep positive historical best until the candidate reaches zero.',
            'reference_transactions': records, 'transaction_cap_rollbacks': cap_rejections,
            'reference_split_roundtrip_comparisons': split_comparisons,
            'oracle_sha256': hashlib.sha256(Path(oracle.__file__).read_bytes()).hexdigest(),
            'fixture_helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = run()
    output = Path('data/row-block-independent-boundary-fixtures.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'transactions': len(result['reference_transactions']),
                      'transaction_cap_rollbacks': result['transaction_cap_rollbacks'],
                      'split_comparisons': result['reference_split_roundtrip_comparisons'],
                      'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}, sort_keys=True))
