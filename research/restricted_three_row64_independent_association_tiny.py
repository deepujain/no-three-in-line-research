"""Synthetic full association with real frozen pure helpers and explicit hash/geometry stubs."""
from unittest.mock import patch
from research import restricted_three_row64 as w
from research import restricted_three_row64_independent_synthetic_graph as g
import hashlib

def run(mutate=None):
 v=g.fixture();v['pins'][str(w.ROOT/w.HANDOFF_PATH)]=w.HANDOFF_SHA
 if mutate:
  mutate(v)
  envelope=v['docs'][w.AUTHORITY];envelope['payload_sha256']=w.hashed(envelope['payload'])
 original=hashlib.sha256
 class Fake:
  def hexdigest(self):return v['metadata']['artifacts'][w.AUTHORITY]
 def sha(data=b''):return Fake() if data==v['authority_raw'] else original(data)
 def valid(values,n):return tuple(tuple(p) for p in values)
 def norm(n,p):return g.AFTER if valid(p,n)==valid(g.NEW_POINTS,n) else g.BEFORE
 with patch.object(w,'validate_metadata',lambda m:m),patch.object(w,'validate_authority',lambda a:a),patch.object(w,'validate_points',valid),patch.object(w,'normalized_sha256',norm),patch.object(g.shared.kernel,'validate_points',valid),patch.object(g.shared.kernel,'normalized_sha256',lambda n,p:g.BEFORE),patch.object(hashlib,'sha256',sha):
  return w.associate_documents(v['docs'],v['metadata'],v['pins'],v['authority_raw'],runtime=v['runtime'])
assert run()[1]['score']==64
mutations={
 'old_report':lambda v:v['docs'][g.OLD_REPORT].__setitem__('accepted',False),
 'old_guard':lambda v:v['docs'][g.OLD_GUARD].__setitem__('audit_output_sha256','0'*64),
 'boolean_sequence':lambda v:v['docs'][w.AUTHORITY]['payload']['attempts'][0].__setitem__('seq',True),
 'stale_late_order':lambda v:v['docs'][w.AUTHORITY]['payload']['attempts'][8].__setitem__('order_hash','0'*64),
 'initial_schema':lambda v:v['docs'][w.INITIAL].__setitem__('cursor',0),
 'initial_counts':lambda v:v['docs'][w.INITIAL]['counters'].__setitem__('started',1),
 'initial_order':lambda v:v['docs'][w.INITIAL].__setitem__('order_sha256','0'*64),
 'move_points':lambda v:v['docs'][w.MOVE]['points'][0].__setitem__(0,2),
 'report_charge':lambda v:v['docs'][w.REPORT]['last_attempted_charge'].__setitem__('completed',16),
 'receipt_cleanup':lambda v:v['docs'][w.RECEIPT]['gate'].__setitem__('cleanup_status','failed'),
 'audit_states':lambda v:v['docs'][w.AUDIT]['chain'].__setitem__('accepted_scores',[65,65]),
 'audit_pin_count':lambda v:v['docs'][w.AUDIT].__setitem__('effective_pins',228),
 'audit_observation':lambda v:v['docs'][w.AUDIT]['chain']['observations'][0].__setitem__('cursor',1),
 'audit_guard_output':lambda v:v['docs'][w.GUARD].__setitem__('audit_output_sha256','0'*64),
 'audit_guard_argv':lambda v:v['docs'][w.GUARD]['argv'].__setitem__(1,'wrong.py'),
 'audit_guard_source':lambda v:v['docs'][w.GUARD]['source_pins'].__setitem__(g.AUDIT_HELPER,'0'*64),
 'runtime_sha':lambda v:v['docs'][w.AUDIT].__setitem__('runtime_sha256','0'*64),
 'missing_input_pin':lambda v:v['pins'].pop(str(w.ROOT/w.MOVE)),
 'metadata_old_hash':lambda v:v['metadata']['artifacts'].__setitem__(g.MOVES[0],'0'*64),
}
for name,mutate in mutations.items():
 try:run(mutate)
 except (ValueError,KeyError,TypeError) as exc:
  if name in ('boolean_sequence','stale_late_order'):assert str(exc)=='fixed old-state ledger',(name,str(exc))
 else:raise AssertionError('accepted corruption '+name)
print('PASS synthetic association with real frozen pure helpers: one positive and',len(mutations),'mutations; hashes, geometry and authority validation stubbed; no actual inputs')
