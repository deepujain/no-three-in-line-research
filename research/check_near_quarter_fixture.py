"""Recheck the published n=71 encoded fixture and model orbit membership."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from near_quarter_model import orbit_map, expand, family_counts
from verify import verify_certificate, verify_certificate_bruteforce

fixture=json.loads((ROOT/'data/published-n71-rct4.json').read_text())
n=fixture['n']; code=fixture['encoded_source']; alphabet=fixture['alphabet']
assert n==71 and len(code)==2*n+1 and code[0]=='c'
assert hashlib.sha256(code.encode()).hexdigest()==fixture['encoded_source_sha256']
points=[[alphabet.index(code[1+2*y+j]),y] for y in range(n) for j in range(2)]
assert points==fixture['points']
checks=[verify_certificate(fixture),verify_certificate_bruteforce(fixture)]
assert all(c['valid'] and c['point_count']==2*n for c in checks)
assert all(c['normalized_sha256']==fixture['normalized_sha256'] for c in checks)
assert fixture['orientation_for_model']=='identity'
model=orbit_map(n); digest=family_counts(model)['orbit_mapping_sha256']
assert digest==fixture['model_orbit_mapping_sha256']
assert all(tuple(p) in model['point_to_var'] for p in points)
ids=sorted({model['point_to_var'][tuple(p)] for p in points})
assert ids==fixture['model_selected_orbit_ids']
assert set(map(tuple,expand(model,ids)))==set(map(tuple,points))
assert sum(i<=model['four_count'] for i in ids)==35
assert sum(i>model['four_count'] for i in ids)==1
print(json.dumps({'valid':True,'n':n,'points':len(points),'orbit_ids':len(ids),
                  'orientation':'identity','geometry_algorithms':[c['algorithm'] for c in checks],
                  'normalized_sha256':fixture['normalized_sha256'],'orbit_mapping_sha256':digest},indent=2))
