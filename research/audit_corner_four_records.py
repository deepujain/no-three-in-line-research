"""Audit completed size-four batch records; never replays numeric search.

Run from research workspace while original loose records are present. Rewrites
only the compact summary, including a new audit timestamp.
"""
import collections
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.corner_batch_worker import prepare_context, ORDER
from research.embedding_worker import read_json, resolve_reference

p=ROOT/'data/corner-batch-four-records'
manifest_path=ROOT/'data/corner-anchor-frontier/manifest.json'
manifest,mhash=read_json(manifest_path)
seed=json.loads((ROOT/'data/published-n78.json').read_text())
scan=json.loads((ROOT/'data/embedding-audit.json').read_text())
ctx=prepare_context(seed,scan,manifest)
cursor,chash=read_json(ROOT/'data/corner-batch-four.json')
anchors=manifest['anchors']; selected=[i for i in range(8136,10072) if anchors[i]['total_deletion_sets']<=152]
selection=hashlib.sha256(json.dumps(selected,separators=(',',':')).encode()).hexdigest()
bhash=hashlib.sha256((ROOT/'research/corner_batch_worker.py').read_bytes()).hexdigest()
assert cursor['manifest_sha256']==mhash and cursor['batch_source_sha256']==bhash and cursor['selection_sha256']==selection
assert cursor['source_normalized_sha256']==ctx['source_normalized_sha256'] and cursor['source_order_sha256']==ctx['source_order_sha256']
assert cursor['start_anchor']==8136 and cursor['stop_anchor']==10072 and cursor['max_anchor_cases']==152
assert len(selected)==cursor['cursor']==cursor['selected_anchor_count']==1936
assert cursor['status']=='complete' and cursor['selected_frontiers_complete'] and cursor['completed_cases_sum']==1936*152 and cursor['distinct_deletion_sets'] is None
assert cursor['verified_witness_events']==0 and not cursor['recent_witness_files']
tested=collections.Counter(); valid=collections.Counter(); allpaths=set(); linked=0; completed=0
for ordinal in selected:
 a=anchors[ordinal]; assert len(a['base_deletion_indices'])==4 and a['total_deletion_sets']==152
 tip_path=p/(a['id']+'-tip.json'); tip,_=read_json(tip_path); allpaths.add(tip_path.resolve())
 assert tip['anchor_id']==a['id'] and tip['manifest_sha256']==mhash and tip['frontier_complete']
 assert tip['coverage']=={'start':0,'end':152,'gapless':True} and tip['next_offset']==tip['total_deletion_sets']==152
 ref=tip['record']; path=resolve_reference(ref,tip_path); record,digest=read_json(path); assert digest==ref['sha256'] and record['status']=='complete'
 visited=set();end=152;anchor_cases=0
 while True:
  real=path.resolve();assert real not in visited and real not in allpaths;visited.add(real);allpaths.add(real);linked+=1
  expected={'audit':'streamed_single_cover_exact_deletion_repair','anchor_id':a['id'],'cut':[0,0],
   'source_normalized_sha256':ctx['source_normalized_sha256'],'source_order_sha256':ctx['source_order_sha256'],
   'base_deletion_indices':a['base_deletion_indices'],'exact_deletion_count':5,'total_deletion_sets':152,
   'enumeration_order':ORDER,'manifest_sha256':mhash,'batch_source_sha256':bhash}
  assert all(record.get(k)==v for k,v in expected.items()),(a['id'],path)
  start,stop,done=(record[k] for k in ('start_offset','next_offset','completed_deletion_sets'))
  assert type(start)==type(stop)==type(done)==int and 0<=start<=stop<=152 and stop==end and done==stop-start
  assert record['status'] in ('complete','case_limit_incomplete','timeout_incomplete') and (record['status']!='complete' or stop==152)
  assert not record.get('found_certificates',[]) and not record.get('witness_files',[])
  assert set(record['tested_addition_subsets'])==set(record['valid_addition_subsets'])=={'157','158'}
  assert all(type(v) is int and v>=0 for v in list(record['tested_addition_subsets'].values())+list(record['valid_addition_subsets'].values()))
  tested.update(record['tested_addition_subsets']);valid.update(record['valid_addition_subsets']);anchor_cases+=done
  ref=record.get('previous_record')
  if ref is None:
   assert start==0;break
  path=resolve_reference(ref,path);record,digest=read_json(path);assert digest==ref['sha256'];end=start
 assert anchor_cases==152;completed+=anchor_cases
assert completed==294272 and not any(valid.values())
witnesses=list(p.glob('embedding-witness-*.json')); assert not witnesses
jsonfiles={q.resolve() for q in p.glob('*.json')}
summary={'status':'complete_selected_size_four_anchor_families_conditional_on_trusted_computation',
 'audited_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'selected_ordinal_range':[8136,10072],
 'selected_anchor_count':len(selected),'unselected_anchor_count':len(anchors)-len(selected),
 'completed_anchor_cases_sum':completed,'unique_deletion_set_count':None,'tip_files':len(selected),
 'linked_origin_and_result_records':linked,'referenced_json_files':len(allpaths),
 'all_json_files_in_directory':len(jsonfiles),'unreferenced_json_files':len(jsonfiles-allpaths),
 'witness_files':len(witnesses),'tested_addition_subsets':dict(tested),'valid_addition_subsets':dict(valid),
 'source_normalized_sha256':ctx['source_normalized_sha256'],'source_order_sha256':ctx['source_order_sha256'],
 'manifest_sha256':mhash,'selection_sha256':selection,'batch_source_sha256':bhash,'cursor_sha256':chash,
 'scope':'The selected size-four exact-five anchor families of one corner and one source; anchor families can overlap. Other 8368 manifest anchors are outside this selection.',
 'trust':'Full linked artifacts and counters checked; numerical computations not independently replayed. Hashes provide consistency, not proof of execution.',
 'no_global_or_full_corner_claim':True}
(ROOT/'data/corner-batch-four-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
