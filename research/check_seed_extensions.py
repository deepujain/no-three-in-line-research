#!/usr/bin/env python3
"""Test single-cell extensions of each translated published n=78 seed."""
import itertools
import json
from pathlib import Path

seed = json.loads((Path(__file__).resolve().parent.parent / 'data/published-n78.json').read_text())['points']
for n in (79, 80):
    for dx in range(n - 77):
        for dy in range(n - 77):
            points = [(x + dx, y + dy) for x, y in seed]
            occupied = set(points)
            pairs = list(itertools.combinations(points, 2))
            free = [(x, y) for x in range(n) for y in range(n)
                    if (x, y) not in occupied and
                    all((x-u[0])*(v[1]-u[1]) != (y-u[1])*(v[0]-u[0])
                        for u, v in pairs)]
            print(f'n={n} offset=({dx},{dy}) addable={len(free)} cells={free}')
