"""Audit saved two-move receipt and four fixed states; does not enumerate neighbors."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / name).read_bytes())
def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
def det_count(points):
    return sum((b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]) for a,b,c in itertools.combinations(sorted(points), 3))
def norm(points):
    return hashlib.sha256(json.dumps({'n':79,'points':[list(p) for p in sorted(points)]}, sort_keys=True, separators=(',',':')).encode()).hexdigest()
def state(path):
    doc=load(path)
    points={tuple(p) for p in doc['points']}
    assert doc['n']==79 and len(doc['points'])==len(points)==157
    assert all(type(x) is int and type(y) is int and 0<=x<79 and 0<=y<79 for x,y in points)
    for axis in (0,1):
        counts=Counter(p[axis] for p in points)
        assert sorted(counts.values()) == [1]+[2]*78 and len(counts)==79
    return points

report_path='data/score11-deficiency-second-neighborhood-v1/report.json'
receipt_path='data/experiments/shepherd-score11-deficiency-second-neighborhood-v1.json'
pins_path='data/score11-deficiency-second-neighborhood-source-pins.json'
manifest_path='data/score11-deficiency-neighborhood-v1-independent-plus1-exit-manifest.json'
input_path='data/score11-deficiency-walk-seed279157-v1/best-state.json'
r=load(report_path); receipt=load(receipt_path); pins=load(pins_path); manifest=load(manifest_path)
assert digest(pins_path)=='b8024f93c3ccf9991a252d17925656639c8b9037d96f57ebd9a74ea1c09de30f'
assert all(digest(k)==v for k,v in pins.items())
assert receipt['sources_unchanged'] and all(digest(k)==v for k,v in receipt['sources_before'].items())
assert all(receipt['sources_before'].get(k)==v for k,v in pins.items())
assert all(digest(k)==v for k,v in r['pins'].items())
assert receipt['argv'][1]=='research/score11_deficiency_second_neighborhood.py'
g=receipt['gate']
assert receipt['status']=='completed' and g['gate_status']=='exited' and g['returncode']==0 and g['cleanup_status']=='clean' and g['trigger_gate_status'] is None and g['monitor_error'] is None
assert g['seconds_limit']==30 and g['rss_limit_mib']==256 and g['peak_sampled_rss_kib']<256*1024 and g['elapsed_seconds']<30
assert r['status']=='complete' and r['complete'] and r['preseed_complete'] and r['n']==79 and r['seconds']==25
assert r['best_score'] is None and r['best_normalized_sha256'] is None
assert sorted(p.name for p in (ROOT/'data/score11-deficiency-second-neighborhood-v1').iterdir())==['report.json']
a=state(input_path)
assert det_count(a)==5 and norm(a)==r['initial_normalized_sha256']==manifest['input_normalized_sha256']
parents=[]
for i,item in enumerate(manifest['exits']):
    assert digest(item['path'])==item['sha256']
    p=state(item['path'])
    assert det_count(p)==6 and norm(p)==item['normalized_sha256']==r['parents'][i]['normalized_sha256']
    removed={tuple(q) for q in item['removed']}; added={tuple(q) for q in item['added']}
    assert a-p==removed and p-a==added and item['delta']==1
    if item['kind']=='column':
        assert len(removed)==len(added)==1 and next(iter(removed))[0]==next(iter(added))[0]
    else:
        assert item['kind']=='rectangle' and len(removed)==len(added)==2
        assert Counter(q[0] for q in removed)==Counter(q[0] for q in added)
        assert Counter(q[1] for q in removed)==Counter(q[1] for q in added)
    parents.append(p)
assert len({frozenset(p) for p in parents})==3
assert len(a^parents[0])==2 and len(a^parents[1])==2 and len(a^parents[2])==4
assert len(parents[0]^parents[1])==2 and len(parents[0]^parents[2])==6 and len(parents[1]^parents[2])==6
legal=illegal=started=completed=0
neg=Counter(); zeros=0
for parent in r['parents']:
    for kind,row in parent['classes'].items():
        expected=12246 if kind=='rectangle' else 157
        assert row['started']==row['completed']==expected
        assert row['completed']==row['legal']+row['illegal'] and row['legal']==sum(row['deltas'].values())
        assert all(int(k)>=-1 for k in row['deltas'])
        neg.update({int(k):v for k,v in row['deltas'].items() if int(k)<0})
        zeros+=row['deltas'].get('0',0)
        started+=row['started'];completed+=row['completed'];legal+=row['legal'];illegal+=row['illegal']
assert started==completed==37680 and neg==Counter({-1:3}) and zeros==2
assert legal==r['novel_first_insertions']+r['preexisting_occurrences']
assert r['map_size']==4+r['novel_first_insertions'] and r['map_size']<=37684
assert sum(r['novel_histogram'].values())==r['novel_first_insertions']
assert min(map(int,r['novel_histogram']))==7
assert r['backtrack_occurrences']==3 and r['exit_occurrences']==2 and r['cross_parent_revisits']==6 and r['same_parent_repeats']==0
assert r['preexisting_occurrences']==9
unique=Counter({int(k):v for k,v in r['novel_histogram'].items()});unique[5]+=1;unique[6]+=2
assert dict(sorted(unique.items()))=={int(k):v for k,v in r['generated_unique_histogram'].items()}
assert sum(unique.values())==legal-r['cross_parent_revisits']
result={'accepted':True,'report_sha256':digest(report_path),'receipt_sha256':digest(receipt_path),
'pins_sha256':digest(pins_path),'pin_count':len(pins),'receipt_pin_count':len(receipt['sources_before']),
'fixed_state_determinant_scores':[5,6,6,6],'fixed_state_identities':[norm(a)]+[norm(p) for p in parents],
'attempted':started,'legal':legal,'illegal':illegal,'distinct_generated':sum(unique.values()),
'novel_states':r['novel_first_insertions'],'backtracks':3,'exit_hits':2,'cross_parent_revisits':6,
'novel_min_score':7,'guard_elapsed_seconds':g['elapsed_seconds'],'guard_peak_sampled_rss_kib':g['peak_sampled_rss_kib'],
'receipt_hypothesis_note':'The receipt hypothesis field is stale one-neighborhood text; argv and result identify the three-parent second-neighborhood run.',
'limit':'Fixed states and counters independently checked, but full neighbor scores/histograms were not independently replayed. The negative result relies on the reviewed source execution and complete receipt; only two-move paths through the three specified exits are covered.'}
out=ROOT/'data/score11-deficiency-second-neighborhood-v1-independent-actual-audit.json'
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
