"""Fixed64 full-run gating with synthetic loader/controller/storage; no actual inputs."""
import hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row64 as w

def case(mode):
 with tempfile.TemporaryDirectory(prefix='fixed64-gate-') as tmp:
  root=Path(tmp).resolve();out=root/'out';out.mkdir();(root/'src').mkdir();(root/'data').mkdir()
  (root/'src/verify.py').write_text('stub');handoff=root/w.HANDOFF_PATH;handoff.write_text('stub')
  import sys
  paths=[Path(w.__file__).resolve(),root/'src/verify.py',Path(sys.executable).resolve(),handoff]
  pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest=root/'pins.json';manifest.write_text(json.dumps(pins));meta_sha=pins[str(handoff)]
  class Store:
   def __init__(self,out):self.out=out;self.publications=0;self.last_durable=None;self.uncertain=False
   def publish(self,a,tag):self.publications+=1;self.last_durable=dict(a);(self.out/'authority.json').write_text(json.dumps(a))
   def save_move(self,move):return {'path':'m','sha256':'a'*64,'bytes':1}
  def zero(points,n,out,check,report):
   ref={'path':'valid149.json','sha256':'a'*64,'bytes':1};report.update(witness_saved=True,witness=ref)
   if mode=='metadata_failure':report['witness_metadata_error']='injected'
   return ref
  authority={'U':64,'witness':None,'n':4,'state_hash':'x','generation':0,'counters':{'started':1,'completed':0,'accepted':0},'cursor':0,'pending':None,'status':'active','artifacts':[],'attempts':[],'orders':{'sha256':'x'}}
  def drive(a,**kw):
   if mode=='metadata_failure':ref=kw['save_zero']([]);a=dict(a,U=0,witness=ref,status='zero');status='zero';error=None
   elif mode=='witness_failed_authority':kw['save_zero']([]);status='search_deadline';error=None
   elif mode=='failed_start':status='error';error='start publication interrupted with unresolved charge'
   else:status='search_deadline';error=None
   return {'authority':a,'status':status,'error':error,'attempted_charge':{'started':1,'completed':0,'accepted':0}}
  with patch.object(w,'ROOT',root),patch.object(w,'SOURCE_IDENTITIES',{}),patch.object(w,'HANDOFF_SHA',meta_sha),patch.object(w,'FileStore',Store),patch.object(w,'load_handoff',return_value=([],{})),patch.object(w.engine.kernel,'dual_validate',return_value={'validators':[{'normalized_sha256':w.FIXED_STATE}]}),patch.object(w,'normalized_sha256',return_value=w.FIXED_STATE),patch.object(w,'build',return_value=([],{},64)),patch.object(w,'new_authority',return_value=authority),patch.object(w,'drive',drive),patch.object(w,'preserve_zero',zero):
   report=w.run(out,manifest,started=0,clock=lambda:1)
  assert report['accepted'] is (mode=='ordinary_stop'),(mode,report)
for mode in ('ordinary_stop','failed_start','witness_failed_authority','metadata_failure'):case(mode)
print('PASS synthetic fixed64 run gate: lost charge, old authority and witness metadata errors rejected; loader/controller/geometry/storage stubbed')
