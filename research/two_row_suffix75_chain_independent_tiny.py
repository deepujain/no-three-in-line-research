import copy,sys
from pathlib import Path
from unittest.mock import patch
from research import two_row_suffix75 as w
R=w.ROOT; H='a'*64; runtime=str(Path(sys.executable).resolve())
report='data/two-row-descent75-v1/report.json'; receipt='data/experiments/shepherd-two-row-descent75-v1.json'; manifest='data/two-row-descent75-source-pins.json'; boundary='data/two-row-descent75-v1/completed-boundary.json'; initial='data/two-row-descent75-v1/initial.json'; best='data/two-row-descent75-v1/best.json'; audit='data/two-row-descent75-independent-chain-actual-audit.json'; guard='data/two-row-descent75-independent-chain-actual-owned-guard.json'; adapter='research/two_row_descent75_actual_chain_adapter.py'; helper='research/two_row_descent_independent_chain_audit.py'
moves=[f'data/two-row-descent75-v1/improvement-{i:03d}.json' for i in range(1,29)]; names=[report,receipt,manifest,boundary,initial,best,audit,guard,adapter,helper,'research/two-row-descent75-independent-actual-acceptance-review.md']+moves
ids={n:H for n in names}; old={str(R/'research/two_row_descent75.py'):w.KERNEL_SHA,runtime:H,str(R/'src/verify.py'):H}; oldpins={**old,str(R/manifest):H}; pins={**oldpins,**{str(R/n):v for n,v in ids.items()}}
meta={'schema':'two-row-fixed-suffix-handoff-identities-v1','n':75,'point_count':149,'unweighted_score':65,'normalized_sha256':w.FIXED_STATE,'inherited_counters':dict(w.BASE),'prior_initial_normalized_sha256':w.kernel.BEST_NORMALIZED,'historical_coverage':{'basis':'source_bound_prior_execution_not_independent_minimum_certificate','pair_prefix':32,'pair_scan_complete':False,'row_sweep_complete':True,'status':'pair_cap'},'artifacts':ids}
def gate():return {'gate_status':'exited','returncode':0,'cleanup_status':'clean','cleanup_error':None,'monitor_error':None,'trigger_gate_status':None,'seconds_limit':30,'rss_limit_mib':256,'peak_sampled_rss_kib':100,'rss_samples':1,'cleanup_samples':1,'elapsed_seconds':1.0}
oldstate=dict(w.BASE,status='pair_cap',U=65,row_sweep_complete=True,pair_scan_complete=False); hi={'handoff_sha256':w.kernel.HANDOFF_SHA}; records=[];docs={}; scores=[97]+list(range(96,69,-1))+[65]; hashes=[w.kernel.BEST_NORMALIZED]+[format(i,'064x') for i in range(1,28)]+[w.FIXED_STATE]
for i,name in enumerate(moves,1):
 x={'path':name,'sha256':H,'kind':'row','rows':[0],'before_normalized_sha256':hashes[i-1],'normalized_sha256':hashes[i],'before_score':scores[i-1],'score':scores[i]}; records.append(x)
 docs[name]={**x,'row_started':i,'row_completed':i,'pair_started':0,'pair_completed':0,'points':[]}
r={'pins':oldpins,'method':'exact_raw_two_row_descent75','accepted':True,'identity_valid':True,'closure':False,'boundary_saved':True,'witness_saved':False,'status':'pair_cap','validation':'invalid_research_state','n':75,'k':149,'row_cap':512,'pair_cap':32,'soft_seconds':25,'search_seconds':23,'boundary_sha256':H,'current_unweighted':65,'best_unweighted':65,'elapsed_seconds':1.0,'state':oldstate,'improvements':records,'handoff':hi}
b={'state':oldstate,'improvements':records,'schema':'two-row-raw-descent-boundary-v1','n':75,'normalized_sha256':w.FIXED_STATE,'policy':{'row_cap':512,'pair_cap':32},'validation':'invalid_research_state','handoff':hi,'points':[]}
j={'sources_before':oldpins,'argv':[str(R/'.venv/bin/python'),'research/two_row_descent75.py','--seconds','25','--output-dir','data/two-row-descent75-v1','--source-pins',manifest],'status':'completed','sources_unchanged':True,'source_manifest_sha256':H,'gate':gate()}
a={'accepted':True,'pilot_artifact_hashes':{k:H for k in (report,receipt,manifest,boundary)},'audited_chain_artifact_hashes':{initial:H,**{x:H for x in moves}},'pilot_pins_checked':len(oldpins),'audit_source_sha256':H,'chain_helper_sha256':H,'runtime_path':runtime,'runtime_sha256':H,'chain':{'artifact_chain_passed':True,'n':75,'states_recounted':29,'scores':scores,'final_counters':{k:w.BASE[k] for k in ('row_started','row_completed','pair_started','pair_completed')},'zero_geometry_verified':False}}
g=gate();g.update(status='completed',argv=[str(R/'.venv/bin/python'),adapter,'--seconds','25','--output',audit],audit_output_sha256=H,source_pins={adapter:H,helper:H})
vals=[{'algorithm':alg,'normalized_sha256':w.FIXED_STATE,'conflict_count':65,'valid':False,'errors':[],'point_count':149,'n':75} for alg in ('integer_normalized_slopes','integer_cross_products')]
docs.update({report:r,receipt:j,manifest:old,boundary:b,initial:{'normalized_sha256':w.kernel.BEST_NORMALIZED,'score':97,'handoff':hi},best:{'classification':'dual_checked_invalid_research_state','valid':False,'certificate':{'claimed_conflict_count':65,'points':[]},'validators':vals},audit:a,guard:g})
with patch.object(w.kernel,'validate_points',return_value=()),patch.object(w.kernel,'normalized_sha256',return_value=w.FIXED_STATE):
 assert w.authenticate_chain(docs,meta,pins)==()
 checks=[(r,'accepted',False),(r,'identity_valid',False),(j,'sources_unchanged',False),(j['gate'],'cleanup_status','error'),(a,'accepted',False),(a['chain'],'artifact_chain_passed',False),(g,'audit_output_sha256','b'*64),(g,'cleanup_status','error'),(b,'normalized_sha256','b'*64),(docs[moves[-1]],'score',64),(docs[best],'valid',True)]
 for obj,k,v in checks:
  oldval=obj[k];obj[k]=v
  try:w.authenticate_chain(docs,meta,pins)
  except ValueError:pass
  else:raise AssertionError(k)
  finally:obj[k]=oldval
 print('PASS complete synthetic 39-item metadata association; 11 mutations rejected; geometry stubbed')
