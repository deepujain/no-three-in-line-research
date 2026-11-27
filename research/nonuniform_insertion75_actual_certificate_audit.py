"""Read-only audit of a completed n74 insertion artifact; never run a census.

Requires an existing report and owned receipt. This script must be separately
allocated after the actual run completes. It writes no outputs or artifacts.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'data/published-n74.json'
FIXTURE_SHA = '276340cef4486bd33666a664e2eba968cbef7deda4398c26590f1307ccf280d4'
NORMALIZED = '3c9c8bf350cb3441dfcef0cdef24a3ba2d53cd0895a3885da18680e2407f27a5'


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        while block := stream.read(65536): h.update(block)
    return h.hexdigest()


def audit(report_path, receipt_path, manifest_path):
    report = json.loads(Path(report_path).read_text())
    receipt = json.loads(Path(receipt_path).read_text())
    if digest(FIXTURE) != FIXTURE_SHA: raise ValueError('source fixture digest')
    source = json.loads(FIXTURE.read_text())
    if source.get('n') != 74 or source.get('source_record') != 1: raise ValueError('source identity')
    points = sorted(tuple(p) for p in source['points'])
    canonical = json.dumps({'n': 74, 'points': [list(p) for p in points]}, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    if (len(points) != 148 or len(set(points)) != 148 or any(len(p) != 2 or any(type(v) is not int or not 0 <= v < 74 for v in p) for p in points)
            or any(Counter(p[a] for p in points) != Counter({v: 2 for v in range(74)}) for a in (0,1))
            or hashlib.sha256(canonical).hexdigest() != NORMALIZED):
        raise ValueError('normalized source identity')
    if receipt.get('status') != 'completed' or receipt.get('sources_unchanged') is not True: raise ValueError('receipt status/source drift')
    manifest_path = Path(manifest_path).resolve()
    if digest(manifest_path) != '47df9cc3c735b5908a516925031519dde65df2a7cb75d0de98ea9017402c3b4c': raise ValueError('manifest digest')
    manifest = json.loads(manifest_path.read_text())
    if type(manifest) is not dict or not manifest: raise ValueError('manifest shape')
    normalize = lambda mapping: {str((ROOT/Path(k)).resolve()): v for k,v in mapping.items()}
    expected_pins = normalize(manifest)
    expected_pins[str(manifest_path)] = digest(manifest_path)
    if len(expected_pins) != len(manifest)+1: raise ValueError('duplicate normalized manifest paths')
    if len(normalize(report['pins'])) != len(report['pins']) or len(normalize(receipt['sources_before'])) != len(receipt['sources_before']): raise ValueError('duplicate normalized aliases')
    if normalize(report['pins']) != expected_pins or normalize(receipt['sources_before']) != expected_pins:
        raise ValueError('manifest/report/receipt source identity')
    worker = ROOT/'research/nonuniform_insertion75.py'
    if expected_pins.get(str(FIXTURE)) != FIXTURE_SHA or str(ROOT/'src/verify.py') not in expected_pins: raise ValueError('missing fixture/verifier pins')
    if expected_pins.get(str(worker)) != '2ae115db7f54325006f7498673650952bf9c40814e50a884389430fffa9b138b': raise ValueError('worker identity')
    expected_argv = [str(ROOT/'.venv/bin/python'), 'research/nonuniform_insertion75.py', '--seconds', '25',
                     '--output-dir', str(Path(report_path).resolve().parent.relative_to(ROOT)),
                     '--source-pins', str(manifest_path.relative_to(ROOT))]
    if receipt.get('argv') != expected_argv: raise ValueError('receipt command mismatch')
    gate = receipt['gate']
    if any(type(gate.get(k)) is not int for k in ('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')) or gate['rss_samples'] < 1 or gate['cleanup_samples'] < 1: raise ValueError('gate integer evidence')
    if (gate.get('gate_status') != 'exited' or gate.get('returncode') != 0
            or gate.get('cleanup_status') != 'clean' or gate.get('cleanup_error') is not None
            or gate.get('monitor_error') is not None or gate.get('trigger_gate_status') is not None
            or gate.get('seconds_limit') != 30 or gate.get('rss_limit_mib') != 256
            or not 0 < gate.get('elapsed_seconds', 30) < 30
            or not 0 < gate.get('peak_sampled_rss_kib', 0) <= 256*1024):
        raise ValueError('owned gate')
    if type(receipt.get('elapsed_seconds')) not in (int,float) or not math.isfinite(receipt['elapsed_seconds']) or not 0 < receipt['elapsed_seconds'] <= 30: raise ValueError('outer elapsed')
    if type(gate.get('elapsed_seconds')) not in (int,float) or not math.isfinite(gate['elapsed_seconds']): raise ValueError('gate elapsed')
    for name, sha in report['pins'].items():
        if digest(name) != sha: raise ValueError('report pin drift: '+name)
    elapsed = report.get('elapsed_seconds')
    if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0 <= elapsed < 25: raise ValueError('worker elapsed')
    if elapsed > gate['elapsed_seconds'] or gate['elapsed_seconds'] > receipt['elapsed_seconds']: raise ValueError('elapsed nesting')
    if report.get('method') != 'selected_n74_nonuniform_insertion' or report.get('score_census_complete') is not False: raise ValueError('method/score claim')
    validators = report.get('source_validation')
    if type(validators) is not list or len(validators) != 2: raise ValueError('source validator count')
    for validator, algorithm in zip(validators, ('integer_normalized_slopes','integer_cross_products')):
        if validator.get('algorithm') != algorithm or validator.get('valid') is not True or validator.get('point_count') != 148 or validator.get('normalized_sha256') != NORMALIZED or validator.get('n') != 74 or validator.get('errors') != [] or validator.get('conflict_count') != 0 or validator.get('conflicts') != []: raise ValueError('source validator identity')
    if (report.get('status') != 'selected_family_obstructed' or report.get('complete') is not True
            or report.get('closure') is not True or report.get('identity_valid') is not True
            or report.get('certificate_complete') is not True or report.get('witness_saved') is not False
            or report.get('source_sha256') != FIXTURE_SHA or report.get('normalized_source_sha256') != NORMALIZED
            or report.get('source_record') != 1 or report.get('unexcluded_gaps') != []):
        raise ValueError('report is not a complete negative certificate')
    family = report.get('family', {})
    if family.get('source_n') != 74 or family.get('gaps') != [0,74] or family.get('exclude_both_boundary') is not True or family.get('included_count') != 5621 or family.get('bit_index') != '(source_n+1)*c+r': raise ValueError('family identity')
    included = {(c,r) for c in range(75) for r in range(75) if not (c in (0,74) and r in (0,74))}
    records = report['obstructions']; seen = set(); counts = {'old': 0, 'new': 0}
    for record in records:
        c,r = record['gap']; gap = (c,r)
        if type(c) is not int or type(r) is not int: raise ValueError('gap coordinate type')
        if gap not in included or gap in seen: raise ValueError('duplicate/excluded/invalid gap')
        seen.add(gap); kind = record['kind']; indices = record['indices']
        if kind not in counts or len(indices) != (3 if kind == 'old' else 2): raise ValueError('kind/arity')
        if any(type(i) is not int or not 0 <= i < 148 for i in indices) or len(set(indices)) != len(indices): raise ValueError('source indices')
        mapped = [(points[i][0]+int(points[i][0] >= c), points[i][1]+int(points[i][1] >= r)) for i in indices]
        if kind == 'new': mapped.append(gap)
        if len(set(mapped)) != 3: raise ValueError('non-distinct mapped points')
        a,b,d = mapped
        if (b[0]-a[0])*(d[1]-a[1]) != (b[1]-a[1])*(d[0]-a[0]): raise ValueError('noncollinear obstruction')
        counts[kind] += 1
    if seen != included or len(records) != 5621: raise ValueError('incomplete coverage')
    return {'accepted': True, 'scope': 'only selected source and 5621 non-boundary gaps',
            'obstructions': counts, 'report_sha256': digest(report_path), 'receipt_sha256': digest(receipt_path),
            'manifest_sha256': digest(manifest_path), 'fixture_sha256': FIXTURE_SHA, 'normalized_source_sha256': NORMALIZED, 'pins_checked': len(report['pins'])}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--report', type=Path, required=True); p.add_argument('--receipt', type=Path, required=True); p.add_argument('--manifest', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(audit(a.report, a.receipt, a.manifest), sort_keys=True))


if __name__ == '__main__': main()
