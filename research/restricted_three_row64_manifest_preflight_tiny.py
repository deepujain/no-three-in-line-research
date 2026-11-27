"""Coordinate-free contract mutations; reads no actual outcome artifacts."""
from copy import deepcopy
import json
from pathlib import Path
from research import restricted_three_row64_manifest_preflight as p


def run():
    contract = p.read_contract()
    old_path = p.ROOT / 'data/restricted-three-row64-source-pins.json'
    old_raw = old_path.read_bytes()
    assert p.sha(old_raw) == 'feb16b236a7b4b47220040d75f0f7dea28a2401c9b92cd187e947049e98f5842'
    old = p.decode(old_raw)
    target = p.ROOT / 'data/restricted-three-row64-source-pins-v2.json'
    required = p.required_pins(contract)
    baseline = p.normalize(old, p.ROOT)
    baseline.update(required)
    result = p.check_manifest(baseline, contract, target)
    rejected = []
    def reject(label, candidate, path=target):
        try:
            p.check_manifest(candidate, contract, path)
        except ValueError as exc:
            rejected.append({'case': label, 'error': str(exc)})
        else:
            raise AssertionError(label)
    reject('original289_missing_three_sources', old, old_path)
    for name in required:
        missing = dict(baseline)
        del missing[name]
        reject('missing:' + name, missing)
        changed = dict(baseline)
        changed[name] = '0' * 64 if baseline[name] != '0' * 64 else '1' * 64
        reject('digest:' + name, changed)
    wrong = dict(baseline)
    wrong[str(target)] = '0' * 64
    reject('manifest_self', wrong)
    wrong = dict(baseline)
    first = next(iter(wrong))
    # Retain the lexical alias so normalization, rather than dict insertion, detects it.
    wrong[first.rsplit('/', 1)[0] + '/./' + first.rsplit('/', 1)[1]] = wrong[first]
    reject('normalized_alias', wrong)
    wrong = dict(baseline)
    wrong[first] = True
    reject('boolean_digest', wrong)
    wrong = dict(baseline)
    for i in range(513):
        wrong['synthetic-extra-' + str(i)] = '0' * 64
    reject('entry_cap', wrong)
    for label, raw in [('duplicate_key', b'{"a":1,"a":2}'), ('nonfinite', b'{"a":NaN}')]:
        try:
            p.decode(raw)
        except ValueError as exc:
            rejected.append({'case': label, 'error': str(exc)})
        else:
            raise AssertionError(label)
    worker_raw = (p.ROOT / p.WORKER).read_bytes()
    try:
        p.worker_identities(worker_raw + b'\n')
    except ValueError as exc:
        rejected.append({'case': 'worker_bytes_before_ast', 'error': str(exc)})
    else:
        raise AssertionError('worker_bytes_before_ast')
    changed_contract = deepcopy(contract)
    changed_contract['sources'][next(iter(contract['sources']))] = '0' * 64
    try:
        p.required_pins(changed_contract)
    except ValueError:
        pass
    else:
        raise AssertionError('contract_conflict')
    return {'passed': True, 'baseline': result, 'rejections': rejected,
            'rejection_count': len(rejected), 'contract_conflict_rejected': True,
            'preserved_original_manifest_sha256': p.sha(old_raw),
            'source_sha256': p.sha(Path(p.__file__).read_bytes()),
            'test_sha256': p.sha(Path(__file__).read_bytes()),
            'scope': 'Coordinate-free old/new manifest maps, fixed identity metadata and hash-bound worker AST only. No worker import, outcome artifact decoding, geometry, runtime allocation or retry.'}


if __name__ == '__main__':
    output = p.ROOT / 'data/restricted-three-row64-manifest-preflight-author-tiny-v1.json'
    with output.open('x') as f:
        json.dump(run(), f, indent=2, sort_keys=True)
        f.write('\n')
