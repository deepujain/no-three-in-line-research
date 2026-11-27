"""Closed synthetic scan/read lifecycle test; semantic association is stubbed."""
import hashlib,tempfile
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row64 as w
from research.restricted_three_row64_independent_closed_graph import closed_graph,compact

def run(mode):
 with tempfile.TemporaryDirectory(prefix='independent-closed64-') as tmp:
  meta,raw,old,new=closed_graph(tmp);meta_bytes=compact(meta);meta_hash=hashlib.sha256(meta_bytes).hexdigest();names=set(raw);events=[]
  class Source:
   def scan(self,name,size,sha):
    events.append(('scan',name));data=raw[name]
    if mode=='scan_mismatch' and name==sorted(names)[-1]:data+=b'x'
    if len(data)!=size or hashlib.sha256(data).hexdigest()!=sha:raise ValueError('synthetic mismatch')
   def read(self,name,size,sha):
    events.append(('read',name));data=meta_bytes if name==w.HANDOFF_PATH else raw[name]
    if mode=='read_mismatch' and name==sorted(k for k in names if k.endswith('.json'))[-1]:data+=b'x'
    if len(data)!=size or hashlib.sha256(data).hexdigest()!=sha:raise ValueError('synthetic mismatch')
    return data
  def associate(docs,metadata,pins,authority_raw,check):
   events.append(('associate',''));assert len(docs)==45 and set(docs)=={n for n in names if n.endswith('.json')}
   assert len([e for e in events if e[0]=='scan'])==51
   return ((1,2),),{'synthetic':True}
  with patch.object(w,'ROLES',frozenset(names)),patch.object(w,'HANDOFF_BYTES',len(meta_bytes)),patch.object(w,'HANDOFF_SHA',meta_hash),patch.object(w,'AUTHORITY',sorted(n for n in names if n.endswith('.json'))[0]),patch.object(w,'validate_metadata',side_effect=lambda value:value),patch.object(w,'checked_pins',side_effect=lambda value:value),patch.object(w,'associate_documents',side_effect=associate):
   try:r=w.association_frame({},lambda:None,Source())
   except ValueError:
    assert mode!='success' and not any(e[0]=='associate' for e in events)
    if mode=='scan_mismatch':assert len([e for e in events if e[0]=='read'])==1
   else:
    assert mode=='success' and r==(((1,2),),{'synthetic':True})
    first_doc_read=next(i for i,e in enumerate(events) if e[0]=='read' and e[1]!=w.HANDOFF_PATH)
    assert all(e[0]=='scan' for e in events[1:first_doc_read]) and len([e for e in events if e[0]=='scan'])==51
for mode in ('success','scan_mismatch','read_mismatch'):run(mode)
print('PASS closed synthetic frame: all 51 hashes scanned before JSON parse, re-read mismatch rejected, semantic association stubbed; no actual inputs')
