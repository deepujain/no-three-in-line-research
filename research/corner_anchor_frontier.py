"""Prepare bounded corner anchor metadata, never run a numerical repair search.

The complete cover antichain is small. Only the requested number of zero-work
origins is written; existing embedding_worker.py executes those frontiers later.
Different anchors may contain the same exact-size deletion set.
"""

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.embedding_audit import insert_grid_lines, stream_cover_repairs
from research.embedding_worker import atomic_json
from research.guided_repair import blockers


def anchor_antichain(eligible):
    """Deduplicate endpoint covers, then remove proper supersets, without D sets."""
    witnesses = {}
    raw_count = 0
    for cell, pairs in eligible:
        for endpoints in itertools.product(*pairs):
            raw_count += 1
            cover = tuple(sorted(endpoints))
            witnesses.setdefault(cover, tuple(cell))
    retained = {}
    for cover in sorted(witnesses, key=lambda c: (len(c), c)):
        if any(subset in retained for size in range(len(cover))
               for subset in itertools.combinations(cover, size)):
            continue
        retained[cover] = witnesses[cover]
    return retained, raw_count, len(witnesses)


def build_manifest(seed, deletion_count=5):
    if type(deletion_count) is not int or not 0 <= deletion_count <= len(seed['points']):
        raise ValueError('invalid exact deletion count')
    cut = (0, 0)
    points = insert_grid_lines(seed['points'], seed['n'], *cut)
    occupied = set(points)
    n = seed['n'] + 1
    eligible = []
    histogram = Counter()
    for cell in itertools.product(range(n), repeat=2):
        if cell in occupied:
            continue
        pairs = blockers(points, cell)
        histogram[len(pairs)] += 1
        if len(pairs) <= deletion_count:
            eligible.append((cell, pairs))
    retained, raw_count, distinct_count = anchor_antichain(eligible)
    anchors = []
    for ordinal, (base, cell) in enumerate(sorted(retained.items(), key=lambda item: (-len(item[0]), item[0]))):
        identity = f'corner-exact{deletion_count}-anchor-{ordinal:05d}'
        anchors.append({'id': identity, 'base_deletion_indices': list(base),
                        'witness_new_cell': list(cell),
                        'total_deletion_sets': math.comb(len(points)-len(base), deletion_count-len(base)),
                        'origin_path': identity + '-origin.json',
                        'tip_path': identity + '-tip.json'})
    return {'kind': 'corner_endpoint_cover_antichain', 'cut': list(cut),
            'translation': [1, 1], 'exact_deletion_count': deletion_count,
            'seed_point_count': len(points), 'n': n,
            'all_empty_cell_blocker_histogram': dict(sorted(histogram.items())),
            'eligible_new_cell_count': len(eligible), 'raw_endpoint_cover_count': raw_count,
            'distinct_endpoint_cover_count': distinct_count,
            'retained_cover_count': len(anchors),
            'retained_cover_size_histogram': dict(sorted(Counter(len(a['base_deletion_indices']) for a in anchors).items())),
            'summed_stream_cases_with_duplicates': sum(a['total_deletion_sets'] for a in anchors),
            'status': 'prepared_no_search_performed', 'completed_deletion_sets': 0,
            'cross_anchor_duplicates': 'Allowed; summed stream cases are not distinct deletions.',
            'closure_requirement': 'Every retained anchor must complete its gapless stream. Prepared origins and partial streams do not close the family.',
            'anchors': anchors}


def prepare(seed, scan, output_directory, initial_origins=3, deletion_count=5):
    if type(initial_origins) is not int or initial_origins < 0:
        raise ValueError('initial_origins must be nonnegative')
    manifest = build_manifest(seed, deletion_count)
    anchors = manifest['anchors']
    if not anchors:
        raise ValueError('no eligible corner anchors')
    # The existing engine supplies its real schema and validates the source and
    # the corner. max_cases=0 means no deletion or addition case is searched.
    template = stream_cover_repairs(seed, scan, (0, 0), anchors[0]['base_deletion_indices'],
                                    deletion_count=deletion_count, max_cases=0, seconds=30)
    if template['completed_deletion_sets'] != 0 or template['next_offset'] != 0:
        raise RuntimeError('zero-work preparation unexpectedly advanced')
    manifest['source_normalized_sha256'] = template['source_normalized_sha256']
    manifest['source_order_sha256'] = template['source_order_sha256']
    output = Path(output_directory)
    manifest['initial_origins'] = []
    for anchor in anchors[:initial_origins]:
        origin = dict(template, base_deletion_indices=anchor['base_deletion_indices'],
                      total_deletion_sets=anchor['total_deletion_sets'],
                      base_is_unique_minimal_cover_through_budget=not anchor['base_deletion_indices'],
                      elapsed_seconds=0.0, preparation_only=True)
        path = output / anchor['origin_path']
        digest = atomic_json(path, origin, immutable=True)
        manifest['initial_origins'].append({'id': anchor['id'], 'path': path.name, 'sha256': digest})
    atomic_json(output / 'manifest.json', manifest, immutable=True)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, default=ROOT/'data/published-n78.json')
    parser.add_argument('--scan', type=Path, default=ROOT/'data/embedding-audit.json')
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--initial-origins', type=int, default=3)
    args = parser.parse_args(argv)
    seed = json.loads(args.seed.read_text())
    scan = json.loads(args.scan.read_text())
    manifest = prepare(seed, scan, args.output_directory, args.initial_origins)
    print(json.dumps({key: manifest[key] for key in ['status', 'raw_endpoint_cover_count',
          'distinct_endpoint_cover_count', 'retained_cover_count', 'retained_cover_size_histogram',
          'summed_stream_cases_with_duplicates', 'initial_origins']}, sort_keys=True))


if __name__ == '__main__':
    main()
