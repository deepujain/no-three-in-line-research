"""One owned n5 pipeline parity pass. Preparing this file does not authorize it."""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'research/full_complement_row75_core.py': 'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b',
    'research/full_complement_row75_primary.py': '2780666ac7f2a1d31e4b735135164fd4f0baf6c06b1424fb6eff405d01006e0e',
    'research/full_complement_row75_independent.py': 'c8fcea3629d5a4d3ccac5f92d925a3e88306fa3e747b40f109142d310dbe07e3',
    'research/full_complement_row75_driver.py': '970eacf3f4a9e95141d83a227cffc3a835eca14c746dbd08860fc089ca999ffc',
    'data/full-complement-row-domain-n5-fixture-v1.json': '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37',
    'data/full-complement-row-domain-n5-author-tiny-v1.json': '4e0477a27d5517c27d583c15f2dec706446527c1671f1c8963c00c1dfca2d941',
    'research/full-complement-row-domain-n5-normal-metadata-review.md': '842b68c52103dc3ae97aac7c13c8ea6b9994b10e964c5756b630fc9fcbe970f4',
}
TINY_LIMITS = {'raw_triples': 168, 'pair_lines': 184, 'intersections': 292,
               'recoveries': 184, 'comparisons': 82, 'cost_columns': 25, 'publications': 4}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded_read(path, cap):
    require(path.stat().st_size <= cap, 'bounded file size')
    with path.open('rb') as source:
        raw = source.read(cap+1)
    require(len(raw) <= cap, 'bounded file read')
    return raw


def identities(check):
    actual = {}
    for name, expected in PINS.items():
        check()
        actual[name] = sha(bounded_read(ROOT/name, 128*1024))
        require(actual[name] == expected, 'fixed source/reference identity: '+name)
    actual[str(Path(__file__).relative_to(ROOT))] = sha(bounded_read(Path(__file__), 128*1024))
    return actual


def run(output):
    output.mkdir(exist_ok=False)
    budget = store = None
    def work_check():
        if time.monotonic() >= ENTRY_STARTED+7:
            raise TimeoutError('tiny 7-second work boundary')
    def final_check():
        if time.monotonic() >= ENTRY_STARTED+9:
            raise TimeoutError('tiny 9-second soft boundary')
    def owned_check():
        if time.monotonic() >= ENTRY_STARTED+10:
            raise TimeoutError('tiny 10-second owned boundary')
    try:
        before = identities(work_check)
        from research import full_complement_row75_core as core
        from research import full_complement_row75_primary as primary
        from research import full_complement_row75_independent as independent
        from research import full_complement_row75_driver as driver
        for module in (core, primary, independent, driver):
            require(Path(module.__file__).resolve() == (ROOT/'research'/Path(module.__file__).name).resolve(),
                    'fixed module origin')
        class TinyBudget(core.Budget):
            def charge(self, kind, component, *, timed=True):
                core.require(type(kind) is str and kind in TINY_LIMITS, 'tiny counter kind')
                if self.counts[kind] >= TINY_LIMITS[kind]:
                    raise core.QuotaExceeded('tiny '+kind+' cap before operation')
                super().charge(kind, component, timed=timed)
        budget = TinyBudget(work_check)
        store = core.ImmutableStore(output, budget)
        fixture_raw = bounded_read(ROOT/'data/full-complement-row-domain-n5-fixture-v1.json', 72)
        require(len(fixture_raw) == 72, 'exact approved fixture length')
        fixture = core.decode(fixture_raw)
        require(fixture['n'] == 5, 'approved n5 fixture')
        points = core.validate_points(fixture['points'], 5)
        old = core.decode(bounded_read(ROOT/'data/full-complement-row-domain-n5-author-tiny-v1.json', 64*1024))
        require(old['passed'] is True and old['mode'] == 'normal' and old['producer']['baseline'] == 14,
                'accepted old n5 evidence schema')
        info = {'snapshot_sha256': PINS['data/full-complement-row-domain-n5-fixture-v1.json'],
                'scope': 'Only the approved n5 literal; no actual input loader.'}
        # Exactly one real pipeline invocation. No actual loader or alternate fixture.
        report = driver.diagnose(points, 5, 14, before, info, store, budget, primary, independent, core,
                                 work_check=work_check, final_check=final_check, owned_check=owned_check)
        require(report['accepted'] is False and report['status'] == 'strict_row_proposal'
                and report['profile_verified'] is True and report['diagnostic_complete'] is True
                and report['candidate_saved'] is True and report['witness_saved'] is False,
                'complete positive diagnostic, pending owned receipt acceptance')
        require(set(store.references) == {'unaries.json', 'candidate.json'} and not store.uncertain,
                'one unary artifact and exactly one candidate')
        for name, reference in store.references.items():
            raw = bounded_read(output/name, 64*1024 if name == 'unaries.json' else 16*1024)
            require(sha(raw) == reference['sha256'] and len(raw) == reference['bytes'], 'saved artifact binding')
        unary = core.decode(bounded_read(output/'unaries.json', 64*1024))
        expected_rows = [{key: row[key] for key in ('row', 'current', 'best', 'best_score')}
                         for row in old['producer']['rows']]
        require(unary['costs'] == [row['unary'] for row in old['producer']['rows']]
                and unary['rows'] == expected_rows and unary['independently_verified'] is True,
                'all 25 unaries and all row minima match accepted n5 evidence')
        expected_winner = min((row['best_score'], row['row'], tuple(row['best']))
                              for row in old['producer']['rows'] if row['best_score'] < 14)
        require(expected_winner == (5, 2, (3,4)), 'saved global winner binding')
        require((report['best_score'], report['best_row'], report['best_columns']) == expected_winner,
                'single global lexical winner')
        candidate = core.decode(bounded_read(output/'candidate.json', 16*1024))
        expected_points = tuple(sorted(tuple(point for point in points if point[1] != 2)+((3,2),(4,2))))
        require(tuple(tuple(point) for point in candidate['points']) == expected_points
                and candidate['raw_score'] == 5 and candidate['adopted'] is False,
                'exact saved candidate and no adoption')
        validation = report['candidate_validation']
        require(validation['score'] == validation['direct_score'] == validation['endpoint_score'] == 5
                and validation['normalized_sha256'] == core.normalized_sha256(expected_points, 5)
                == candidate['normalized_sha256'], 'one candidate dual validation')
        counts = budget.snapshot()
        totals, components = counts['totals'], counts['components']
        require(totals['raw_triples'] == 168 and totals['pair_lines'] == 184
                and totals['cost_columns'] == 25 and totals['publications'] == 2, 'exact pipeline operation counts')
        require(components['independent_baseline']['raw_triples'] == 84
                and components['independent_candidate_direct']['raw_triples'] == 84
                and components['primary']['pair_lines'] == 36
                and components['independent_retained']['pair_lines'] == 112
                and components['independent_candidate_lines']['pair_lines'] == 36
                and components['independent_retained']['comparisons'] == 28, 'independent component counts')
        require(components['primary']['intersections'] == 5*(components['primary']['recoveries']-4)
                and components['independent_retained']['intersections'] == components['independent_retained']['recoveries'],
                'line intersection accounting')
        require(all(totals[kind] == sum(part[kind] for part in components.values())
                    and totals[kind] <= TINY_LIMITS[kind] for kind in TINY_LIMITS), 'shared accounting and tiny caps')
        budget.check = final_check
        after = identities(final_check)
        require(before == after, 'pre/post source and reference identity')
        result = {'passed': True, 'scope': 'One approved n5 pipeline; saved older results compared without rerunning their geometry.',
                  'receipt_acceptance_required': True, 'failure_artifact_invalidates_receipt': True,
                  'source_before': before, 'source_after': after, 'pipeline_invocations': 1,
                  'candidate_validations': 1, 'all_25_costs_and_five_row_minima_match': True,
                  'global_winner': expected_winner, 'operation_counts_before_receipt': counts,
                  'expected_final_publications': 3, 'tiny_limits': TINY_LIMITS,
                  'pipeline_report': report, 'elapsed_before_receipt': time.monotonic()-ENTRY_STARTED}
        raw = store.prepare(result, 64*1024)
        store.commit_prepared('parity.json', raw, 64*1024)
        require(identities(final_check) == before, 'final source/reference identity')
        final_check()
        return True, {'passed': True, 'output_dir': str(output), 'parity_sha256': sha(raw)}
    except Exception as error:
        failure = {'passed': False, 'error': type(error).__name__+': '+str(error)[:1000],
                   'scope': 'Failed single n5 pipeline gate; preserve artifacts and stop without retry.'}
        if budget is not None:
            budget.check = lambda: None
            failure['operation_counts'] = budget.snapshot()
        if store is not None:
            failure['saved_references'] = store.references
            failure['publication_uncertain'] = store.uncertain
        raw = json.dumps(failure, sort_keys=True, separators=(',',':')).encode('ascii')
        require(len(raw) <= 64*1024, 'failure byte cap')
        try:
            if store is not None:
                store.commit_prepared('failure.json', raw, 64*1024, urgent=True)
            else:
                import os
                with (output/'failure.json').open('xb') as target:
                    require(target.write(raw) == len(raw), 'complete failure write')
                    target.flush()
                    os.fsync(target.fileno())
                directory = os.open(output, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        except Exception as persistence_error:
            failure['failure_persistence_error'] = type(persistence_error).__name__+': '+str(persistence_error)[:1000]
        return False, failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    passed, summary = run(args.output_dir)
    print(json.dumps(summary, sort_keys=True))
    return 0 if passed else 2


if __name__ == '__main__':
    sys.exit(main())
