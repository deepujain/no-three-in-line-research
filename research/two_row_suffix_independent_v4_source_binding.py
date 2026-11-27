"""Immutable v2-to-v4 source binding only; no imports of research workers."""
import ast
import hashlib
import json
from pathlib import Path

V2 = '11fc0200742a14f5baa8cfffe85c91b34353b4990608f70efba66cc20dd750a2'
V4 = 'fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run():
    old = Path('research/two_row_suffix75_v2_frozen.py')
    new = Path('research/two_row_suffix75.py')
    assert sha(old) == V2 and sha(new) == V4
    before, after = (ast.parse(p.read_text()) for p in (old, new))
    old_functions = {n.name: ast.dump(n, include_attributes=False) for n in before.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: ast.dump(n, include_attributes=False) for n in after.body if isinstance(n, ast.FunctionDef)}
    assert old_functions.keys() == new_functions.keys()
    changed = sorted(k for k in old_functions if old_functions[k] != new_functions[k])
    assert changed == ['preserve_zero', 'run']
    predicate = ast.dump(ast.parse("'witness_metadata_error' not in report", mode='eval').body, include_attributes=False)
    removed = []
    class StripPredicate(ast.NodeTransformer):
        def visit_BoolOp(self, node):
            self.generic_visit(node)
            kept = []
            for value in node.values:
                if ast.dump(value, include_attributes=False) == predicate:
                    removed.append(value)
                else: kept.append(value)
            node.values = kept
            return node
    for tree in (before, after):
        tree.body = [n for n in tree.body if not isinstance(n, ast.FunctionDef) or n.name != 'preserve_zero']
    StripPredicate().visit(after)
    assert len(removed) == 1
    assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False)
    assert sha(old) == V2 and sha(new) == V4
    return {'passed': True, 'scope': 'SOURCE ONLY; no geometry, worker imports, loaders or run',
            'v2_sha256': V2, 'v4_sha256': V4, 'changed_functions': changed,
            'only_other_change': 'one witness_metadata_error not-in-report acceptance conjunct',
            'unchanged_math_controller_ast': True, 'source_sha256': sha(__file__),
            'prior_logical_evidence_sha256': sha('data/two-row-suffix-independent-worker-audit-v2.json'),
            'limits': 'Source equivalence transfers unchanged logical properties only. No claim of rerunning the v2 suite at v4 or independently exercising lifecycle faults.'}

if __name__ == '__main__':
    evidence = Path('data/two-row-suffix-independent-v4-source-binding.json')
    assert not evidence.exists()
    result = run()
    evidence.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'passed': True, 'source_sha256': result['source_sha256'], 'evidence_sha256': sha(evidence)}))
