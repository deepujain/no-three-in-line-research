"""Coordinate-free fixed64 manifest contract; never imports the worker."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKER = 'research/restricted_three_row64.py'
WORKER_SHA = 'e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
PRIOR = 'data/restricted-three-row75-source-pins.json'
PRIOR_SHA = '7d0ab3cc50b2e7349218be5b33ea6897047a69879f27c03693efa7656e16a51d'
METADATA = 'data/restricted-three-row64-input-identities.json'
METADATA_SHA = '2d6ba98abf571bc430f9a6e51a0dec5e99db68246e780ac24a5c8ba65b025ced'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON token')
    return json.loads(raw.decode('ascii'), object_pairs_hook=pairs, parse_constant=constant)


def normalize(pins, root):
    require(type(pins) is dict and len(pins) <= 512, 'pin map/count')
    result = {}
    for name, value in pins.items():
        require(type(name) is str and 0 < len(name) <= 1024, 'pin path')
        require(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'pin digest')
        target = str((root / name).resolve())
        require(len(target) <= 1024 and target not in result, 'pin normalized alias/path')
        result[target] = value
    return result


def worker_identities(raw):
    """Read literal assignments from hash-bound AST; do not execute source."""
    require(sha(raw) == WORKER_SHA, 'worker source identity')
    env = {}
    def literal(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return env[node.id]
        if isinstance(node, ast.Dict):
            return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
        raise ValueError('nonliteral source identity assignment')
    for node in ast.parse(raw).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name == 'SOURCE_IDENTITIES':
            result = literal(node.value)
            require(type(result) is dict and len(result) == 6, 'six frozen source identities')
            return result
        if isinstance(node.value, ast.Constant):
            env[name] = node.value.value
    raise ValueError('missing SOURCE_IDENTITIES assignment')


def read_contract(root=ROOT):
    """Reads only two coordinate-free documents and reviewed worker source."""
    root = Path(root).resolve()
    prior_raw = (root / PRIOR).read_bytes()
    metadata_raw = (root / METADATA).read_bytes()
    require(sha(prior_raw) == PRIOR_SHA, 'prior manifest identity')
    require(len(metadata_raw) == 10249 and sha(metadata_raw) == METADATA_SHA, 'fixed metadata identity')
    prior, metadata = decode(prior_raw), decode(metadata_raw)
    require(type(prior) is dict and len(prior) == 228, 'prior228 map')
    require(type(metadata) is dict and metadata['artifact_count'] == 51 and len(metadata['artifacts']) == 51,
            'fixed51 metadata roles')
    return {'root': root, 'prior': prior, 'metadata': metadata,
            'sources': worker_identities((root / WORKER).read_bytes())}


def required_pins(contract, runtime=None):
    root = contract['root']
    result = normalize(contract['prior'], root)
    def add(name, value):
        key = str((root / name).resolve())
        require(key not in result or result[key] == value, 'contract pin conflict')
        result[key] = value
    add(PRIOR, PRIOR_SHA)
    for name, value in contract['metadata']['artifacts'].items():
        add(name, value)
    for name, value in contract['sources'].items():
        add(name, value)
    add(METADATA, METADATA_SHA)
    add(WORKER, WORKER_SHA)
    runtime = str(Path(sys.executable if runtime is None else runtime).resolve())
    verifier = str((root / 'src/verify.py').resolve())
    require(runtime in result and verifier in result, 'prior runtime/verifier identities')
    return result


def check_manifest(pins, contract, manifest_path, runtime=None):
    root = contract['root']
    normalized = normalize(pins, root)
    require(str(Path(manifest_path).resolve()) not in normalized, 'manifest self entry')
    required = required_pins(contract, runtime)
    for name, expected in required.items():
        require(name in normalized, 'missing required pin: ' + name)
        require(normalized[name] == expected, 'required pin digest: ' + name)
    return {'passed': True, 'manifest_entries': len(normalized), 'effective_entries_after_self': len(normalized) + 1,
            'mandatory_union_entries': len(required), 'worker_source_identities': len(contract['sources']),
            'fixed_artifact_roles': 51, 'inherited_manifest_entries': 228, 'prior_manifest_self_required': True,
            'runtime_verifier_worker_metadata_required': True}


def preflight(path, root=ROOT):
    path = Path(path).resolve()
    raw = path.read_bytes()
    require(len(raw) <= 128 * 1024, 'manifest byte cap')
    result = check_manifest(decode(raw), read_contract(root), path)
    return dict(result, manifest_sha256=sha(raw), manifest_bytes=len(raw),
                scope='Coordinate-free presence/identity contract only; no artifact contents, worker import, loader, geometry or execution.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    print(json.dumps(preflight(args.manifest), sort_keys=True))


if __name__ == '__main__':
    main()
