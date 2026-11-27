import json,hashlib,sys,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,'.')
from research.corner_batch_worker import prepare_context,ORDER
from research.embedding_worker import read_json,resolve_reference
root=Path('.');p=root/'data/corner-batch-small-records';manifest_path=root/'data/corner-anchor-frontier/manifest.json'
manifest,mhash=read_json(manifest_path);seed=json.load(open('data/published-n78.json'));scan=json.load(open('data/embedding-audit.json'));ctx=prepare_context(seed,scan,manifest)
cursor_path=root/'data/corner-batch-small.json';cursor,chash=read_json(cursor_path)
anchors=manifest['anchors'];selected=[i for i,a in enumerate(anchors) if a['total_deletion_sets']<=1];selection=hashlib.sha256(json.dumps(selected,separators=(',',':')).encode()).hexdigest()
bhash=hashlib.sha256((root/'research/corner_batch_worker.py').read_bytes()).hexdigest()
assert mhash==cursor['manifest_sha256'] and bhash==cursor['batch_source_sha256'] and selection==cursor['selection_sha256']
assert len(selected)==cursor['cursor']==cursor['selected_anchor_count']==cursor['completed_cases_sum']==8136 and cursor['selected_frontiers_complete'] and cursor['status']=='complete' and cursor['distinct_deletion_sets'] is None and cursor['unselected_anchor_count']==2168
assert cursor['source_normalized_sha256']==ctx['source_normalized_sha256'] and cursor['source_order_sha256']==ctx['source_order_sha256']
tested=Counter();valid=Counter();record_count=0;completed=0
for i in selected:
 a=anchors[i];tip_path=p/(a['id']+'-tip.json');tip,_=read_json(tip_path)
 assert tip['anchor_id']==a['id'] and tip['manifest_sha256']==mhash and tip['frontier_complete'] and tip['coverage']=={'start':0,'end':1,'gapless':True} and tip['next_offset']==tip['total_deletion_sets']==1
 ref=tip['record'];path=resolve_reference(ref,tip_path);r,h=read_json(path);assert h==ref['sha256']
 seen=set();end=1
 while True:
  assert path.resolve() not in seen;seen.add(path.resolve());record_count+=1
  expected={'audit':'streamed_single_cover_exact_deletion_repair','anchor_id':a['id'],'cut':[0,0],'source_normalized_sha256':ctx['source_normalized_sha256'],'source_order_sha256':ctx['source_order_sha256'],'base_deletion_indices':a['base_deletion_indices'],'exact_deletion_count':5,'total_deletion_sets':1,'enumeration_order':ORDER,'manifest_sha256':mhash,'batch_source_sha256':bhash}
  assert all(r.get(k)==v for k,v in expected.items()),(a['id'],path)
  start=r['start_offset'];stop=r['next_offset'];comp=r['completed_deletion_sets'];assert type(start)==type(stop)==type(comp)==int and 0<=start<=stop<=1 and stop==end and comp==stop-start
  assert r['status'] in ('complete','case_limit_incomplete','timeout_incomplete') and (r['status']!='complete' or stop==1)
  assert not r.get('found_certificates',[]) and not r.get('witness_files',[])
  assert set(r['tested_addition_subsets'])==set(r['valid_addition_subsets'])=={'157','158'}
  assert all(type(v)==int and v>=0 for v in list(r['tested_addition_subsets'].values())+list(r['valid_addition_subsets'].values()))
  tested.update(r['tested_addition_subsets']);valid.update(r['valid_addition_subsets']);completed+=comp
  if not r.get('previous_record'):
   assert start==0;break
  ref=r['previous_record'];path=resolve_reference(ref,path);r,h=read_json(path);assert h==ref['sha256'];end=start
assert completed==8136 and not any(valid.values()) and record_count==16272
files=list(p.glob('*.json'));witness=list(p.glob('embedding-witness-*.json'));assert not witness
assert len(files)==24408
summary={'status':'complete_selected_one_case_anchor_families_conditional_on_trusted_computation','audited_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'selected_anchor_count':len(selected),'unselected_anchor_count':len(anchors)-len(selected),'completed_anchor_cases_sum':completed,'unique_deletion_set_count':None,'tip_files':len(selected),'linked_origin_and_result_records':record_count,'json_files_in_directory':len(files),'witness_files':len(witness),'tested_addition_subsets':dict(tested),'valid_addition_subsets':dict(valid),'source_normalized_sha256':ctx['source_normalized_sha256'],'source_order_sha256':ctx['source_order_sha256'],'manifest_sha256':mhash,'selection_sha256':selection,'batch_source_sha256':bhash,'cursor_sha256':chash,'scope':'The selected one-case exact-five anchor families of the single checked source and corner; overlapping anchor cases are not a distinct count. Other 2168 anchors remain outside this selection.','trust':'Full linked artifacts and counters checked; numerical computations not independently replayed. Hashes provide consistency, not proof of execution.','no_global_or_full_corner_claim':True}
(root/'data/corner-batch-small-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
