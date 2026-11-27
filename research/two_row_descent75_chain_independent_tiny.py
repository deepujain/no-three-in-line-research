import sys
from pathlib import Path
from unittest.mock import patch
from research import two_row_descent75 as w
R=w.ROOT; runtime=str(Path(sys.executable).resolve()); H='a'*64
names=['data/row-block-breakout75-v1/report.json','data/experiments/shepherd-row-block-breakout75-v1.json','data/row-block-breakout75-source-pins.json','data/row-block-breakout75-v1/completed-boundary.json','data/row-block-breakout75-v1/best.json','data/row-block-breakout75-independent-actual-audit.json','data/row-block-breakout75-independent-actual-audit-owned-guard.json','data/row-block-breakout75-independent-actual-audit.log']
art={n:H for n in names}; manifest=names[2]; cp=names[3]; oldworker=str(R/'research/row_block_breakout75.py'); helper=str(R/'research/row_block_breakout75_actual_audit.py'); helperhash='006110e8799b5f0a508ee1ee870fd7fd8181690f2c6d9c970d2b354e9c76605a'
old={runtime:H,oldworker:H}; oldpins={**old,str(R/manifest):H}; pins={**oldpins,**{str(R/n):H for n in names},helper:helperhash}
def guard(s):return {'gate_status':'exited','returncode':0,'cleanup_status':'clean','cleanup_error':None,'monitor_error':None,'trigger_gate_status':None,'seconds_limit':s,'rss_limit_mib':256,'peak_sampled_rss_kib':100,'rss_samples':1,'cleanup_samples':1,'elapsed_seconds':1.0}
report={'pins':oldpins,'method':'from_scratch_row_block_breakout75','accepted':True,'identity_valid':True,'closure':False,'checkpoint_saved':True,'witness_saved':False,'n':75,'k':149,'best_unweighted':97,'checkpoint_sha256':H,'elapsed_seconds':1.0}
receipt={'sources_before':oldpins,'status':'completed','sources_unchanged':True,'source_manifest_sha256':H,'argv':[str(R/'.venv/bin/python'),'research/row_block_breakout75.py','--seconds','25','--output-dir','data/row-block-breakout75-v1','--source-pins',manifest],'gate':guard(30)}
meta={'schema':'row-block-completed-boundary-v1','best_unweighted':97,'best_normalized_sha256':w.BEST_NORMALIZED,'validation':'invalid_research_state','identities':{'manifest_path':str(R/manifest),'manifest_sha256':H,'runtime_path':runtime,'runtime_sha256':H,'python_version':sys.version,'worker_sha256':H,'soft_seconds':25,'search_seconds':23,'owned_seconds':30,'rss_limit_mib':256}}
cpdoc={'metadata':meta,'current':[],'best':[],'weights':[],'rng':[]}
vals=[{'algorithm':a,'valid':False,'n':75,'point_count':149,'conflict_count':97,'errors':[],'normalized_sha256':w.BEST_NORMALIZED} for a in ('integer_normalized_slopes','integer_cross_products')]
best={'classification':'dual_checked_invalid_research_state','valid':False,'certificate':{'n':75,'claimed_conflict_count':97,'points':[],'axis_counts':{'rows':[0]*75,'columns':[0]*75}},'validators':vals}
audit={'accepted':True,'best_unweighted':97,'checkpoint_sha256':H,'report_sha256':H,'receipt_sha256':H,'manifest_sha256':H,'pins_checked':len(oldpins)}
g=guard(10);g.update(argv=[str(R/'.venv/bin/python'),'research/row_block_breakout75_actual_audit.py','--report',names[0],'--receipt',names[1],'--manifest',manifest,'--manifest-sha256',H],audit_helper_sha256=helperhash)
docs={names[0]:report,names[1]:receipt,names[2]:old,names[3]:cpdoc,names[4]:best,names[5]:audit,names[6]:g}
handoff={'schema':'two-row-fixed-handoff-identities-v1','n':75,'point_count':149,'unweighted_score':97,'best_normalized_sha256':w.BEST_NORMALIZED,'artifacts':art,'scope':'synthetic'}
with patch.object(w,'validate_points',return_value=()),patch.object(w,'normalized_sha256',return_value=w.BEST_NORMALIZED):
 assert w.authenticate_chain(docs,handoff,pins)==()
 checks=[(report,'accepted',False),(report,'identity_valid',False),(receipt,'sources_unchanged',False),(receipt['gate'],'cleanup_status','error'),(audit,'accepted',False),(audit,'checkpoint_sha256','b'*64),(g,'cleanup_status','error'),(g,'audit_helper_sha256','b'*64),(meta['identities'],'python_version','bad'),(meta,'best_unweighted',96),(best,'valid',True)]
 for obj,key,bad in checks:
  prev=obj[key];obj[key]=bad
  try:w.authenticate_chain(docs,handoff,pins)
  except ValueError:pass
  else:raise AssertionError(key)
  finally:obj[key]=prev
 print('synthetic full metadata chain PASS; 11 mutations rejected; geometry stubbed')
