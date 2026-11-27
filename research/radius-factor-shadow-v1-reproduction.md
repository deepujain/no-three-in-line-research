# Reproduce the six-prefix evidence without local checkpoints

The original shadow run bound private, immutable checkpoint bytes and their accepted receipts. These local checkpoint files remain ignored. The public actual report stores every selected prefix orbit ID, full mask, quotient demand, edge list and SAT edge witness, so its geometric and degree evidence can be reconstructed from a fresh repository clone.

From the repository root, run:

```sh
.venv/bin/python - <<'PYCODE'
import json
from research.near_quarter_factor_shadow import mask_and_bounds
r = json.load(open('data/radius-factor-shadow-v1/report.json'))
for sample in r['samples']:
    replay = mask_and_bounds(79, sample['ids'], lambda: None)
    for key in ('points_sha256', 'mask_sha256', 'mask', 'demands', 'edges',
                'orbit_shortfall', 'row_shortfall', 'graph_obstruction'):
        assert replay[key] == sample[key], key
    f = sample['factor']
    if f['status'] == 'sat':
        degree = [0] * len(sample['demands'])
        for i in f['selected_edge_indices']:
            u, v = sample['edges'][i]
            degree[u] += 1
            degree[v] += 1
        assert degree == sample['demands']
    else:
        assert f['basis'] == 'degree_shortfall'
        degree = [0] * len(sample['demands'])
        for u, v in sample['edges']:
            degree[u] += 1
            degree[v] += 1
        assert any(a < b for a, b in zip(degree, sample['demands']))
print('Six masks and degree results reproduced; no geometric solution claimed.')
PYCODE
```

This replay does not launch a native solver, alter a frontier, or assert that a degree-feasible edge selection is geometrically compatible. The independent audit additionally regenerated quarter-turn orbits and checked masks by a separate integer-geometry oracle. Five degree-feasible results and one already-detected degree shortage gave zero additional pruning on the six selected prefixes.
