"""Synthetic run preflight: each mandatory input/source pin is required before loader."""
import hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
from research import restricted_three_row64 as w

def run(missing=None):
 with tempfile.TemporaryDirectory(prefix='fixed64-required-pins-') as tmp:
  root=Path(tmp).resolve();out=root/'out';out.mkdir();(root/'src').mkdir();(root/'data').mkdir()
  import sys
  runtime=str(Path(sys.executable).resolve());wrapper=str(Path(w.__file__).resolve());verify=str(root/'src/verify.py');handoff=str(root/w.HANDOFF_PATH)
  pins={wrapper:'a'*64,verify:'b'*64,runtime:'c'*64,handoff:'d'*64}
  pins.update({str(root/name):sha for name,sha in w.SOURCE_IDENTITIES.items()})
  keys=list(pins)
  if missing is not None:del pins[keys[missing]]
  manifest=root/'pins.json';manifest.write_text(json.dumps(pins));calls=[]
  def digest(path,check):
   check();p=str(Path(path).resolve())
   return hashlib.sha256(manifest.read_bytes()).hexdigest() if p==str(manifest) else pins[p]
  def stop(*args):calls.append('loader');raise ValueError('synthetic loader sentinel')
  with patch.object(w,'ROOT',root),patch.object(w,'HANDOFF_SHA','d'*64),patch.object(w,'digest',digest),patch.object(w,'load_handoff',stop):
   report=w.run(out,manifest,started=0,clock=lambda:1)
  assert not report['accepted']
  if missing is None:assert calls==['loader'] and 'synthetic loader sentinel' in report['error']
  else:assert calls==[] and ('mandatory wrapper/input/runtime pins' in report['error'] or 'frozen source closure' in report['error'])
  return len(keys)
n=run()
for i in range(n):run(i)
print('PASS synthetic run preflight:',n,'individual mandatory pin omissions rejected before loader; hashing and loader stubbed; no actual inputs')
