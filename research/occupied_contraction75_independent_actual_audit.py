"""Audit152 saved obstruction certificates; never replay the contraction census."""
from collections import Counter
import hashlib
import json
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / 'data/published-n76.json'
REPORT = ROOT / 'data/occupied-contraction75-v1/report.json'
RECEIPT = ROOT / 'data/experiments/shepherd-occupied-contraction75-v1.json'
MANIFEST = ROOT / 'data/occupied-contraction75-source-pins.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell(raw, n):
    assert type(raw) is list and len(raw) == 2
    assert all(type(v) is int and 0 <= v < n for v in raw)
    return tuple(raw)


def main():
    paths = (FIXTURE, REPORT, RECEIPT, MANIFEST)
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    assert digest(FIXTURE) == 'b5353bc39d2e65c81dca5a5bb5668b93f2c3d14ec80b627d0383cee26d298c17'
    assert digest(MANIFEST) == '5fda6998f0d6a44367e6880092d6442f371c1ea1c359d166a55dd853cb344e0e'
    source = json.loads(FIXTURE.read_text())
    report = json.loads(REPORT.read_text())
    receipt = json.loads(RECEIPT.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert source['n'] == 76 and source['source_record'] == 1
    points = [cell(p, 76) for p in source['points']]
    assert len(points) == len(set(points)) == 152
    points = set(points)
    for axis in (0, 1):
        assert Counter(p[axis] for p in points) == Counter({i: 2 for i in range(76)})
    canonical = json.dumps({'n': 76, 'points': [list(p) for p in sorted(points)]},
                           sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    normalized = hashlib.sha256(canonical.encode()).hexdigest()
    assert normalized == '97591fb28df5c742e090960c8feaf2fad9753b2a187a7b293139a0d574140ff5'
    assert len(report['source_validation']) == 2
    assert {v['algorithm'] for v in report['source_validation']} == {
        'integer_normalized_slopes', 'integer_cross_products'}
    for validation in report['source_validation']:
        assert validation['valid'] is True and validation['point_count'] == 152
        assert validation['normalized_sha256'] == normalized

    expected_pins = {str(ROOT / name): sha for name, sha in manifest.items()}
    expected_pins[str(MANIFEST)] = digest(MANIFEST)
    assert report['pins'] == expected_pins
    before = {str(ROOT / name): sha for name, sha in receipt['sources_before'].items()}
    assert before == expected_pins
    for name, expected in expected_pins.items():
        assert digest(Path(name)) == expected, name
    assert receipt['sources_unchanged'] is True and receipt['status'] == 'completed'
    assert receipt['job']['id'] == 'shepherd-occupied-contraction75-v1'
    assert receipt['argv'][1:] == [
        'research/occupied_contraction75.py', '--seconds', '25', '--output-dir',
        'data/occupied-contraction75-v1', '--source-pins',
        'data/occupied-contraction75-source-pins.json']
    gate = receipt['gate']
    assert gate['gate_status'] == 'exited' and gate['returncode'] == 0
    assert gate['cleanup_status'] == 'clean' and gate['cleanup_error'] is None
    assert gate['monitor_error'] is None and gate['trigger_gate_status'] is None
    assert gate['seconds_limit'] == 30 and gate['rss_limit_mib'] == 256
    assert 0 < gate['elapsed_seconds'] < 30 and 0 < gate['peak_sampled_rss_kib'] <= 256 * 1024
    assert gate['rss_samples'] > 0 and report['elapsed_seconds'] < 25
    assert report['status'] == 'selected_family_obstructed'
    assert all(report[k] is True for k in ('complete', 'closure', 'identity_valid'))
    assert report['witness_saved'] is False and report['zero_cuts'] == []
    assert not (REPORT.parent / 'valid149.json').exists()

    scores = {}
    for record in report['occupied_scores']:
        cut = cell(record['cut'], 76)
        assert cut not in scores
        assert type(record['triples']) is int and 0 < record['triples'] <= comb(149, 3)
        scores[cut] = record['triples']
    assert set(scores) == points
    obstructions = {}
    for record in report['obstructions']:
        cut = cell(record['cut'], 76)
        assert cut not in obstructions
        triple = tuple(cell(p, 76) for p in record['source_triple'])
        assert len(triple) == len(set(triple)) == 3 and set(triple) <= points
        obstructions[cut] = triple
    assert set(obstructions) == points

    checked = []
    for (c, r), triple in sorted(obstructions.items()):
        assert all(x != c and y != r for x, y in triple)
        def image(p):
            x, y = p
            return (x - 1 if x > c else x, y - 1 if y > r else y)
        target = {image(p) for p in points if p[0] != c and p[1] != r}
        assert len(target) == 149
        assert all(0 <= x < 75 and 0 <= y < 75 for x, y in target)
        for axis in (0, 1):
            assert sorted(Counter(p[axis] for p in target).values()) == [1] + [2] * 74
        a, b, d = mapped = [image(p) for p in triple]
        assert len(set(mapped)) == 3 and set(mapped) <= target
        determinant = (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])
        assert determinant == 0
        checked.append({'cut': [c, r], 'source_triple': triple,
                        'contracted_triple': mapped, 'determinant': determinant,
                        'candidate_size': len(target)})
    count = report['counters']
    assert count['triples'] == comb(152, 3) and count['prefix_rows'] == 76
    assert 0 <= count['zero_rectangles'] <= count['rectangles'] <= 16 * comb(152, 3)
    assert 152 <= count['obstruction_cut_tests'] <= 152 * count['zero_rectangles']
    for p in paths:
        assert digest(p) == hashes[str(p.relative_to(ROOT))]
    result = {
        'status': 'PASS_SELECTED_FAMILY_EXCLUSION', 'source_pins_checked': len(expected_pins),
        'manifest_entries': len(manifest), 'input_sha256': hashes,
        'audit_source_sha256': digest(Path(__file__)), 'normalized_source_sha256': normalized,
        'occupied_cut_count': len(checked), 'exact_determinants_checked': len(checked),
        'per_cut_certificates': checked, 'guard': gate,
        'reported_census_counters_not_replayed': count,
        'reported_minimum_score_not_recounted': min(scores.values()),
        'closure': 'All152 occupied-intersection contractions of this exact selected n76 source are invalid.',
        'limits': 'No complete score recount, census replay, independent source geometry replay, '
                  'general n75 exclusion, valid149 construction, or novelty claim.',
    }
    output = ROOT / 'data/occupied-contraction75-independent-actual-audit.json'
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'per_cut_certificates'}, sort_keys=True))


if __name__ == '__main__':
    main()
