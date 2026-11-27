"""Full run acceptance gating with synthetic loader/controller/files; no actual inputs."""
import hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row75 as w

def case(mode):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp).resolve();out=root/'out';out.mkdir();(root/'src').mkdir();(root/'data').mkdir()
  (root/'src/verify.py').write_text('stub');(root/'data/two-row-suffix75-input-identities.json').write_text('stub')
  import sys
  paths=[Path(w.__file__).resolve(),Path(w.kernel.__file__).resolve(),Path(w.shared.__file__).resolve(),root/'src/verify.py',Path(sys.executable).resolve(),root/'data/two-row-suffix75-input-identities.json']
  pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest=root/'pins.json';manifest.write_text(json.dumps(pins))
  class Store:
   def __init__(self,out):self.out=out;self.publications=0;self.last_durable=None;self.uncertain=False
   def publish(self,a,tag):
    self.publications+=1;self.last_durable=dict(a);(self.out/'authority.json').write_text(json.dumps(a))
   def save_move(self,move):return {'path':'m','sha256':'a'*64,'bytes':1}
  def zero(points,n,out,check,report):
   ref={'path':'valid149.json','sha256':'a'*64,'bytes':1};report.update(witness_saved=True,witness=ref)
   if mode=='metadata_failure':report['witness_metadata_error']='injected'
   return ref
  authority={'U':65,'witness':None,'n':4,'state_hash':'x','generation':0,'counters':{'started':1,'completed':0,'accepted':0},'cursor':0,'pending':None,'status':'active','artifacts':[],'attempts':[],'orders':{'sha256':'x'}}
  def drive(a,**kw):
   if mode=='metadata_failure':
    ref=kw['save_zero']([]);a=dict(a,U=0,witness=ref,status='zero');status='zero';err=None
   elif mode=='witness_failed_authority':kw['save_zero']([]);status='search_deadline';err=None
   elif mode=='failed_start':status='error';err='start publication interrupted with unresolved charge'
   else:status='search_deadline';err=None
   return {'authority':a,'status':status,'error':err,'attempted_charge':{'started':1,'completed':0,'accepted':0}}
  with patch.object(w,'ROOT',root),patch.object(w,'FileStore',Store),patch.object(w,'load_handoff',return_value=([],{})),patch.object(w,'build',return_value=([],{},65)),patch.object(w,'new_authority',return_value=authority),patch.object(w,'drive',drive),patch.object(w,'preserve_zero',zero):
   report=w.run(out,manifest,started=0,clock=lambda:1)
  assert report['accepted'] is (mode=='ordinary_stop'),(mode,report)
for mode in ('witness_failed_authority','failed_start','ordinary_stop','metadata_failure'):case(mode)
print('PASS: synthetic full-run gate rejects lost charge and witness/metadata errors; ordinary stop accepted. All loader/controller/storage are stubbed.')
