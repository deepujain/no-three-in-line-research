"""Independent tiny geometry/policy/fault review. Never invokes actual main."""
from collections import Counter,deque
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import hashlib,json,random,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from research import score11_conflict_focused_tabu as m

def triples(P):
 return tuple(t for t in combinations(sorted(P),3) if (t[1][0]-t[0][0])*(t[2][1]-t[0][1])==(t[1][1]-t[0][1])*(t[2][0]-t[0][0]))
def axis(P,n):
 result=[]
 for a in (0,1):
  c=Counter(p[a] for p in P);assert sorted(c[i] for i in range(n))==[1]+[2]*(n-1)
  result.append(next(i for i in range(n) if c[i]==1))
 return tuple(result)
def direct_move(P,n,kind,a,b):
 r,c=axis(P,n)
 if kind in ('row','column'):
  q=(r,a[1]) if kind=='row' else (a[0],c)
  return None if q in P else (P-{a})|{q}
 if a==b or a[0]==b[0] or a[1]==b[1]:return None
 add={(a[0],b[1]),(b[0],a[1])}
 return None if add&P else (P-{a,b})|add
counts=Counter();states1=[]
for n in (2,3,4):
 for chosen in combinations(product(range(n),repeat=2),2*n-1):
  P=set(chosen)
  if any(max(Counter(p[a] for p in P).values())>2 for a in (0,1)):continue
  axis(P,n);score=len(triples(P));assert tuple(m.conflict_triples(P,lambda:None))==triples(P)
  counts['states']+=1
  if n==4 and score==1:states1.append(P)
  for kind in ('row','column','rectangle'):
   args=((a,None) for a in sorted(P)) if kind!='rectangle' else combinations(sorted(P),2)
   for a,b in args:
    old=frozenset(P);Q=direct_move(P,n,kind,a,b);actual=m.move(P,n,kind,a,b,lambda:None)
    assert frozenset(P)==old and (actual is None)==(Q is None)
    if Q is not None:
     assert actual[1]==Q and actual[0]==len(triples(Q))-score;axis(Q,n)
     counts['rectangles' if kind=='rectangle' else 'relocations']+=1
assert (counts['states'],counts['relocations'],counts['rectangles'])==(865,8648,8496)
# Fully independent fixed-sample reference: direct endpoints and full determinants.
def reference(P,S,n,steps):
 P=set(P);rng=random.Random(279179);recent=deque([tuple(sorted(P))]);best=len(triples(P));hist=Counter()
 out={'classes':{k:dict.fromkeys(('started','completed','illegal','duplicates','tabu','admissible'),0) for k in ('row','column','rectangle')},'steps_started':0,'steps_completed':0,'candidates_started':0,'candidates_completed':0,'accepted':0,'uphill':0,'neutral':0,'downhill':0,'tabu_evictions':0}
 for _ in range(steps):
  out['steps_started']+=1;focus=sorted({p for t in triples(P) for p in t});oldscore=len(triples(P));seen=set();options=[]
  for sample in range(32):
   kind='row' if sample<8 else 'column' if sample<16 else 'rectangle';row=out['classes'][kind]
   a=rng.choice(focus);b=rng.choice(sorted(P)) if kind=='rectangle' else None
   Q=direct_move(P,n,kind,a,b);row['started']+=1;row['completed']+=1;out['candidates_started']+=1;out['candidates_completed']+=1
   if Q is None:row['illegal']+=1;continue
   key=tuple(sorted(Q));s=len(triples(Q))
   if key in seen:row['duplicates']+=1;continue
   seen.add(key)
   if key in recent and s>=best:row['tabu']+=1;continue
   row['admissible']+=1;options.append((s,key,Q))
  out['steps_completed']+=1
  if not options:out['status']='no_admissible_sample';break
  s,key,P=min(options,key=lambda x:(x[0],x[1]));out['accepted']+=1
  out['uphill' if s>oldscore else 'downhill' if s<oldscore else 'neutral']+=1;hist[s]+=1
  recent.append(key)
  if len(recent)>64:recent.popleft();out['tabu_evictions']+=1
  best=min(best,s)
  if not s:out['status']='witness';break
 else:out['status']='step_cap'
 out['accepted_score_histogram']=dict(sorted(hist.items()));return out
S={(i,i) for i in range(4)}|{(i,3-i) for i in range(4)};A=S-{(0,0)};initial_score=len(triples(A));assert initial_score==5
with tempfile.TemporaryDirectory() as d:
 r=m.walk(4,A,S,initial_score,Path(d),max_steps=8,clock=lambda:0)
 expected=reference(A,S,4,8)
 for key,value in expected.items():assert r[key]==value,(key,r[key],value)
 assert r['witness'] and r['best']==r['witness']
 counts['seeded_reference_steps']=r['steps_completed']
# Policy-only endpoint injection uses REAL tiny degree-valid, score-one states.
# These are arbitrary transitions to test FIFO, not claims of primitive legality.
first=next(P for P in states1 if axis(P,4) not in P);order=[first]+[P for P in states1 if P!=first][:64]
source=first|{axis(first,4)}
def policy_sequence(sequence):
 calls=[0]
 def proposed(P,n,kind,a,b,check):
  check();i=calls[0]//32;calls[0]+=1;Q=set(sequence[i]);return len(triples(Q))-len(triples(P)),Q
 with tempfile.TemporaryDirectory() as d,patch.object(m,'move',proposed):
  return m.walk(4,first,source,1,Path(d),max_steps=len(sequence),clock=lambda:0)
r=policy_sequence(order[1:]+[first])
assert r['accepted']==65 and r['tabu_evictions']==2 and r['neutral']==65 and r['status']=='step_cap'
assert sum(v['tabu'] for v in r['classes'].values())==0
r=policy_sequence(order[1:64]+[first])
assert r['accepted']==63 and r['tabu_evictions']==0 and r['status']=='no_admissible_sample'
assert sum(v['tabu'] for v in r['classes'].values())==1
counts['fifo_cases']=2
# Real n7 source-distance fixtures, using injected endpoints only for policy.
n=7;S7={(i,i) for i in range(n)}|{(i,(i+1)%n) for i in range(n)};A7=S7-{(0,0)}
Q14=({(i,(i+3)%n) for i in range(n)}|{(i,(i+4)%n) for i in range(n)})-{(0,3)}
Q13=(Q14-{(3,0)})|{(0,0)};Q1=S7-{(1,1)}
for P,D in [(Q13,13),(Q14,14),(Q1,1)]:axis(P,n);assert len(S7-P)==D and len(triples(P))>0
assert len(triples(Q13))<len(triples(A7))
sequence=[Q13,Q14,Q1];calls=[0];validation_calls=Counter();real_first=m.base.verify_certificate;real_second=m.base.verify_certificate_bruteforce

def proposed7(P,n,kind,a,b,check):
 check();Q=sequence[calls[0]//32];calls[0]+=1;return len(triples(Q))-len(triples(P)),set(Q)
def track_first(cert):validation_calls[tuple(map(tuple,cert['points']))]+=1;return real_first(cert)
with tempfile.TemporaryDirectory() as d,patch.object(m,'move',proposed7),patch.object(m.base,'verify_certificate',track_first):
 r=m.walk(7,A7,S7,len(triples(A7)),Path(d),max_steps=3,clock=lambda:0)
 assert r['accepted']==3 and r['distance_exit']['source_deleted']==13
 saved=json.loads(Path(r['distance_exit']['path']).read_text());assert set(map(tuple,saved['points']))==Q13
 assert set(saved['metadata']['labels'])=={'strict_best','distance_exit'} and not saved['metadata']['valid']
 assert validation_calls[tuple(sorted(Q13))]==1
 assert sum('distance_exit' in json.loads(p.read_text())['metadata']['labels'] for p in Path(d).iterdir())==1
 counts['distance_transitions']=3
# Every clock/check location on a complete one-step tiny run is faulted.
clock_calls=[0]
def tick():clock_calls[0]+=1;return 0
with tempfile.TemporaryDirectory() as d:baseline=m.walk(4,A,S,5,Path(d),max_steps=1,clock=tick)
for cutoff in range(1,clock_calls[0]):
 seen=[0]
 def deadline():seen[0]+=1;return 26 if seen[0]>=cutoff else 0
 with tempfile.TemporaryDirectory() as d:
  # started=0 avoids making the artificially late first clock a fresh start.
  r=m.walk(4,A,S,5,Path(d),max_steps=1,clock=deadline,started=0)
  if r['steps_completed']==0:assert r['accepted']==0
  for field in ('best','distance_exit','witness'):
   if r[field] is not None:
    p=Path(r[field]['path']);assert p.exists()
    doc=json.loads(p.read_text());assert len(triples(set(map(tuple,doc['points']))))==doc['metadata']['exact_conflict_count']
  if r['status']=='timeout':assert not r['complete']
 counts['clock_fault_cases']+=1
# Late validator two saves one witness artifact; reports share its identity.
now=[0];witness_validations=[0]
def late(cert):
 v=real_second(cert)
 if v['valid']:now[0]=26;witness_validations[0]+=1
 return v
with tempfile.TemporaryDirectory() as d,patch.object(m.base,'verify_certificate_bruteforce',late):
 r=m.walk(4,A,S,5,Path(d),max_steps=8,clock=lambda:now[0])
 assert r['status']=='witness' and r['witness']==r['best'] and witness_validations[0]==1
 assert r['witness']['labels']==['witness','strict_best']
 assert Path(r['witness']['path']).exists()
counts['late_witness_cases']=1
# Timeout before validator two and atomic write failure cannot promote pointers.
real_atomic=m.base.atomic
for failure in ('late_first','write','changed_pin'):
 now=[0]
 def first(cert):
  v=real_first(cert)
  if v['conflict_count']<5 and failure=='late_first':now[0]=26
  return v
 def atomic(path,doc):
  if doc['metadata']['exact_conflict_count']<5 and failure=='write':raise OSError('injected write failure')
  return real_atomic(path,doc)
 with tempfile.TemporaryDirectory() as d,patch.object(m.base,'verify_certificate',first),patch.object(m.base,'atomic',atomic):
  pins={}
  if failure=='changed_pin':
   p=Path(d)/'pin';p.write_bytes(b'changed');pins={p:hashlib.sha256(b'original').hexdigest()}
  r=m.walk(4,A,S,5,Path(d),max_steps=8,clock=lambda:now[0],pins=pins)
  if failure=='changed_pin':assert r['status']=='error' and r['best'] is None
  else:
   assert r['status']==('timeout' if failure=='late_first' else 'error')
   assert r['best']['exact_conflict_count']==5 and r['witness'] is None
 counts['publication_fault_cases']+=1
# Existing final identity hook must override successful status on mutation.
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'pin';p.write_bytes(b'changed');r={'status':'witness','complete':True}
 m.one.finalize_identity(r,{p:hashlib.sha256(b'old').hexdigest()})
 assert r['status']=='error' and r['complete'] is False
counts['final_identity_fault_cases']=1
files=['research/score11_conflict_focused_tabu.py','tests/test_score11_conflict_focused_tabu.py']
out={'accepted':True,'scope':'Independent tiny n2..4 geometry, n7 predetermined distance fixtures, synthetic policy endpoints and fault injection only; no n79 work','counts':dict(counts),'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
p=ROOT/'data/score11-conflict-focused-tabu-independent-tiny-audit.json';p.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True));print('audit_sha256',hashlib.sha256(p.read_bytes()).hexdigest())
