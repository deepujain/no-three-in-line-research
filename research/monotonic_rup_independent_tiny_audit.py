"""Independent synthetic-only UP oracle; no actual certificate input paths."""
from itertools import combinations, product
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PINS = {
    'research/monotonic_rup_checker.py': '09e85dced3d7cf572cad4b75f9b4fab50dd051f4fe9f95ded58981de6ded5c90',
    'research/saved_boolean_proof_check.py': 'f7addf7c68dfbd510572e7fc70ece579e44fb8a4048b0ee0eb5d7be471a13d17',
    'tests/test_monotonic_rup_checker.py': '05ff5e9d4254d4389bcff02c841e97dc5b7da32cfe2f1cc11b600319a527d203',
}


def literal_up(formula, candidate):
    """Literal-set closure, independent of production bit masks and Budget."""
    known = {-v for v in candidate}
    while True:
        if any(-v in known for v in known):
            return True
        forced = set()
        for raw in formula:
            current = set(raw)
            if any(-v in current for v in current):
                continue
            if current & known:
                continue
            residual = {v for v in current if -v not in known}
            if not residual:
                return True
            if len(residual) == 1:
                forced.update(residual)
        if forced <= known:
            return False
        known.update(forced)


def truth_entails(formula, candidate, n=2):
    for values in product((False, True), repeat=n):
        def satisfied(clause):
            return any(values[abs(v) - 1] == (v > 0) for v in clause)
        if all(satisfied(c) for c in formula) and not satisfied(candidate):
            return False
    return True


def all_small_cases():
    literals = (-2, -1, 1, 2)
    candidates = [tuple(c) for k in range(5) for c in combinations(literals, k)]
    clauses = [c for c in candidates if not any(-v in c for v in c)]
    assert len(clauses) == 9 and len(candidates) == 16
    for mask in range(1 << len(clauses)):
        formula = [c for i, c in enumerate(clauses) if mask & (1 << i)]
        for candidate in candidates:
            expected = literal_up(formula, candidate)
            if expected:
                assert truth_entails(formula, candidate)
            yield formula, candidate, expected


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for relative, expected in PINS.items():
        assert digest(ROOT / relative) == expected
    sys.path.insert(0, str(ROOT))
    from research import monotonic_rup_checker as checker

    def masks(clause):
        pos = neg = 0
        for v in clause:
            if v > 0:
                pos |= 1 << (v - 1)
            else:
                neg |= 1 << (-v - 1)
        return pos, neg

    compared = accepted = 0
    for formula, candidate, expected in all_small_cases():
        for actual_formula in (formula, formula + [(-1, 1), (-2, 2)]):
            assert literal_up(actual_formula, candidate) == expected
            inference = [(*masks(c), len(c)) for c in actual_formula]
            got = checker.rup(inference, masks(candidate), checker.Budget())
            assert got == expected, (actual_formula, candidate, got, expected)
            if got:
                assert truth_entails(actual_formula, candidate)
            compared += 1
            accepted += got

    receipts = []
    with tempfile.TemporaryDirectory(prefix='independent-monotonic-rup-') as tmp:
        cnf = Path(tmp) / 'synthetic.cnf'
        proof = Path(tmp) / 'synthetic.rup'

        def run(label, formula, trace, want, **kwargs):
            cnf.write_text('p cnf 3 %d\n' % len(formula) + ''.join(
                ' '.join(map(str, c)) + (' ' if c else '') + '0\n' for c in formula))
            proof.write_bytes(trace.encode('ascii'))
            result = checker.check_pair(cnf, proof, digest(cnf), digest(proof), **kwargs)
            assert result['accepted'] is want and result['closure'] is want, (label, result)
            if want:
                assert result['full_parse_complete'] and result['checked_empty_line'] >= 1
                assert result['cnf_sha256'] == digest(cnf) and result['proof_sha256'] == digest(proof)
            receipts.append({'label': label, 'receipt': result})
            return result

        contradictory = [(1,), (-1,)]
        cube = list(product(*[(i, -i) for i in range(1, 4)]))
        run('checked_empty', contradictory, '0\n', True)
        run('nonunit_reason_retained', [(1,), (-1, 2), (-2,)], 'd -1 2 0\n0\n', True)
        run('duplicate_deletions_valid', [(1,), (1,), (-1,)], 'd 1 0\nd 1 0\n0\n', True)
        bad = run('duplicate_deletions_excess', [(1,), (1,), (-1,)], 'd 1 0\nd 1 0\nd 1 0\n0\n', False)
        assert bad['failure_line'] == 3
        run('RAT_not_RUP_rejected', [(-1, 2), (2,)], '1 0\n0\n', False)
        run('unjustified_unit_rejected', [(1, 2)], '1 0\n0\n', False)
        run('UNSAT_cube_not_initially_UP', cube, '0\n', False)
        run('cube_derivation', cube, '2 3 0\n3 0\n1 0\n0\n', True)
        run('bad_suffix_after_empty', contradictory, '0\nx 0\n', False)
        run('bad_deletion_after_empty', contradictory, '0\nd 2 0\n', False)
        run('truncated_suffix_after_empty', contradictory, '0\n1 0', False)
        run('valid_suffix_after_empty', contradictory, '0\nd 1 0\n', True)
        run('missing_empty', contradictory, '1 0\n', False)
        for label, limits in (
            ('work_cap', replace(checker.Limits(), work=0)),
            ('record_cap', replace(checker.Limits(), proof_records=0)),
            ('retained_storage_cap', replace(checker.Limits(), retained_clauses=2)),
            ('proof_byte_cap', replace(checker.Limits(), proof_bytes=1)),
        ):
            run(label, contradictory, '0\n', False, limits=limits)
        run('exact_byte_cap', contradictory, '0\n', True, limits=replace(checker.Limits(), proof_bytes=2))
        run('wall_cap', contradictory, '0\n', False, seconds=.1, started=0, clock=lambda: 1)
        run('prepare_digest_fixture', contradictory, '0\n', True)
        for label, cnf_sha, proof_sha in (
            ('wrong_CNF_digest', '0' * 64, digest(proof)),
            ('wrong_proof_digest', digest(cnf), '0' * 64),
        ):
            result = checker.check_pair(cnf, proof, cnf_sha, proof_sha)
            assert not result['accepted'] and not result['closure']
            receipts.append({'label': label, 'receipt': result})
        original_hash = checker.hash_file
        cnf_sha, proof_sha = digest(cnf), digest(proof)

        def mutate_after_preflight(path, cap, budget):
            result = original_hash(path, cap, budget)
            if path == proof:
                proof.write_text('0\n1 0\n')
            return result

        checker.hash_file = mutate_after_preflight
        try:
            result = checker.check_pair(cnf, proof, cnf_sha, proof_sha)
        finally:
            checker.hash_file = original_hash
        assert not result['accepted'] and 'proof parse digest mismatch' in result['error']
        receipts.append({'label': 'post_empty_parse_digest_required', 'receipt': result})

    for relative, expected in PINS.items():
        assert digest(ROOT / relative) == expected
    result = {
        'status': 'PASS_SYNTHETIC_ONLY', 'source_pins': PINS,
        'audit_source_sha256': digest(Path(__file__)),
        'base_formula_count': 512, 'candidate_count': 16,
        'UP_comparisons': compared, 'accepted_additions_truth_checked': accepted,
        'receipt_cases': receipts,
        'scope': 'Synthetic n<=3 only; no saved CNF/proof read, native child, or SAT execution.',
    }
    (ROOT / 'data/monotonic-rup-independent-tiny-audit.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'receipt_cases'}, sort_keys=True))
    print('receipt_cases', len(receipts))


if __name__ == '__main__':
    main()
