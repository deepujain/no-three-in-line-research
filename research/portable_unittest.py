"""Discover the full suite, conditionally skipping one original-runtime integration."""
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
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
