"""Discover the suite; narrowly identify integrations requiring the original Mac."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import near_quarter_depth12_seeded_chunk as anchor

TARGETS = frozenset({
    'test_near_quarter_depth12_seeded_chunk.LoaderTests.test_actual_anchor_identity_reads_only',
    'tests.test_near_quarter_depth12_seeded_chunk.LoaderTests.test_actual_anchor_identity_reads_only',
})
ORIGINAL_RUNTIME = '.venv/lib/python3.14/site-packages/'
HOST_RUNTIME_MANIFEST = 'data/fixed-pool-boolean-scaffold-runtime-pins.json'
HOST_RUNTIME_SHA = '1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a'
HOST_TESTS = frozenset({
    'test_fixed_pool_boolean_scaffold.NativeTinyTests.test_identity_caps_timeout_fork',
    'test_fixed_pool_boolean_scaffold.NativeTinyTests.test_kernel_native_file_caps_and_fork_inheritance',
    'test_fixed_pool_boolean_scaffold.NativeTinyTests.test_real_tiny_sat_unsat_and_independent_proof',
    'test_fixed_pool_boolean_scaffold.PureTests.test_loaded_backend_origins_and_optional_presence',
    'test_monotonic_rup_checker.NativeTinyTests.test_only_synthetic_pair_in_one_checker_child',
})


def original_host_runtime_missing(root, manifest_name=HOST_RUNTIME_MANIFEST,
                                  manifest_sha=HOST_RUNTIME_SHA, platform_name=sys.platform):
    """Linux may lack the exact Mac; present mismatches and partial local runtimes fail."""
    data = (Path(root)/manifest_name).read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest_sha:
        raise ValueError('pinned host runtime manifest changed')
    runtime = json.loads(data)
    if not isinstance(runtime.get('pins'), dict) or not runtime['pins']:
        raise ValueError('empty host runtime pins')
    interpreter = Path(runtime['interpreter'])
    if not interpreter.is_absolute() or str(interpreter) not in runtime['pins']:
        raise ValueError('missing absolute host interpreter pin')
    missing = []
    for name, expected in runtime['pins'].items():
        p = Path(name)
        if not p.is_absolute(): raise ValueError('nonabsolute host runtime pin')
        try: raw = p.read_bytes()
        except FileNotFoundError: missing.append(name)
        else:
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('present host runtime pin changed: '+name)
    if missing and (platform_name != 'linux' or interpreter.exists()):
        raise ValueError('original host runtime is incomplete, not absent on Linux')
    return sorted(missing)


def select_original_host_tests(suite, availability):
    """Exactly five reviewed integrations; every other discovered test stays untouched."""
    found = {name: [] for name in HOST_TESTS}
    def visit(node):
        if isinstance(node, unittest.TestSuite):
            for child in node: visit(child)
        else:
            name = node.id().removeprefix('tests.')
            if name in found: found[name].append(node)
    visit(suite)
    if any(len(tests) != 1 for tests in found.values()):
        raise RuntimeError('expected exactly one of each of five original-host tests')
    for tests in found.values():
        test = tests[0]; original = getattr(test, test._testMethodName)
        def guarded(original=original):
            missing = availability()
            if missing:
                raise unittest.SkipTest('exact original Mac runtime absent on Linux: '+', '.join(missing))
            original()
        setattr(test, test._testMethodName, guarded)
    return suite


def verify_anchor_availability(root, fixed_pins, receipt_name):
    """Return missing original-runtime paths; raise on every other integrity issue."""
    root = Path(root)
    def checked_name(name):
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('invalid pinned path: ' + name)
        return root.joinpath(*p.parts)
    def read_matching(name, expected):
        data = checked_name(name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('pinned file changed: ' + name)
        return data
    # Trust neither the list of required runtime paths nor its expected hashes
    # until every fixed anchor artifact, including the receipt, is checked.
    fixed_bytes = {name: read_matching(name, expected) for name, expected in fixed_pins.items()}
    receipt = json.loads(fixed_bytes[receipt_name])
    sources = receipt['sources_before']
    if not isinstance(sources, dict) or not sources:
        raise ValueError('invalid receipt sources')
    missing = []
    for name, expected in sources.items():
        try:
            read_matching(name, expected)
        except FileNotFoundError:
            if not name.startswith(ORIGINAL_RUNTIME):
                raise
            missing.append(name)
    return sorted(missing)


def select_portable_test(suite, availability):
    """Wrap exactly one discovered test; synthetic and all other tests are untouched."""
    selected = []
    def visit(node):
        if isinstance(node, unittest.TestSuite):
            for child in node:
                visit(child)
        elif node.id() in TARGETS:
            selected.append(node)
    visit(suite)
    if len(selected) != 1:
        raise RuntimeError(f'expected exactly one original-runtime integration; found {len(selected)}')
    test = selected[0]
    original = getattr(test, test._testMethodName)
    def guarded():
        missing = availability()
        if missing:
            raise unittest.SkipTest('original pinned runtime files absent: ' + ', '.join(missing))
        original()
    setattr(test, test._testMethodName, guarded)
    return suite


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test*.py')
    select_portable_test(suite, lambda: verify_anchor_availability(ROOT, anchor.FIXED_PINS, anchor.ANCHOR_RECEIPT))
    select_original_host_tests(suite, lambda: original_host_runtime_missing(ROOT))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
