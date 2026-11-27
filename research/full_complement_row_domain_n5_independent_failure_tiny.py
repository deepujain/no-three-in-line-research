"""Source-only failure persistence/identity tests; no normal diagnostic geometry."""
from pathlib import Path
import json,sys,tempfile
from unittest.mock import patch
from research import full_complement_row_domain_n5_tiny as t

with tempfile.TemporaryDirectory(prefix='n5-failure-review-') as d:
 root=Path(d);path=root/'evidence.json';failure=root/'evidence-failure.json'
 with patch.object(sys,'argv',['tiny','--mode','pregeometry','--output',str(path)]),patch.object(t,'run_pregeometry',side_effect=ValueError('injected')):
  try:t.main()
  except ValueError as e:assert str(e)=='injected'
  else:raise AssertionError('injected failure accepted')
 assert not path.exists() and json.loads(failure.read_bytes())['passed'] is False
 initial=failure.read_bytes()
 with patch.object(sys,'argv',['tiny','--mode','pregeometry','--output',str(path)]),patch.object(t,'run_pregeometry',side_effect=ValueError('second injected')):
  try:t.main()
  except FileExistsError:pass
  else:raise AssertionError('existing failure overwritten')
 assert failure.read_bytes()==initial
 source_failure=root/'source-lost.json'
 original_read=Path.read_bytes
 def missing_producer(path):
  if path==Path(t.producer.__file__):raise PermissionError('synthetic unreadable producer')
  return original_read(path)
 with patch.object(sys,'argv',['tiny','--mode','pregeometry','--output',str(source_failure)]),patch.object(t,'run_pregeometry',side_effect=PermissionError('synthetic source check')),patch.object(Path,'read_bytes',missing_producer):
  try:t.main()
  except PermissionError:pass
  else:raise AssertionError('unreadable producer accepted')
 observed=json.loads((root/'source-lost-failure.json').read_bytes())['observed_source_identities']['producer']
 assert observed['sha256'] is None and observed['error'].startswith('PermissionError:')
 oversized=root/'oversized.json'
 try:t.write_immutable(oversized,{'padding':'x'*t.OUTPUT_CAP})
 except AssertionError:pass
 else:raise AssertionError('oversized output accepted')
 assert not oversized.exists()
 initial_ids=t.source_identity()
 for role in initial_ids:
  changed=dict(initial_ids);changed[role]=73 if role=='fixture_bytes' else '0'*64
  try:t.compare_identities(initial_ids,changed)
  except AssertionError:pass
  else:raise AssertionError('identity drift accepted: '+role)
print('PASS injected failure preserved without overwrite, 64KiB cap and four identity drift rejections; no normal geometry')
