"""Independent completed-artifact audit; no walk/trajectory replay."""
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.verify import verify_certificate,verify_certificate_bruteforce
from research.near_quarter_packed_worker import validate_gate
start=time.monotonic()
def h(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_bytes())
def pin(p,s):assert h(p)==s,p
def norm(P):return hashlib.sha256(json.dumps({'n':79,'points':[list(p) for p in sorted(P)]},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def conflicts(P):return tuple(t for t in combinations(sorted(P),3) if (t[1][0]-t[0][0])*(t[2][1]-t[0][1])==(t[1][1]-t[0][1])*(t[2][0]-t[0][0]))
def ct(v):return sorted(tuple(sorted(map(tuple,t['points']))) for t in v['conflicts'])
rp='data/score11-conflict-focused-tabu-v1/report.json';ep='data/experiments/shepherd-score11-conflict-focused-tabu-v1.json'
fixed={rp:'37b320a4682a6f18a281b6f4937566b6ac0c3c8994bc16a55b036018d6affa27',ep:'58bb81fa946752978aa8f70eabae92fca2417f69f9e3ba994d993ca54e61cd13'}
for p,s in fixed.items():pin(p,s)
r=read(rp);e=read(ep)
assert e['status']=='completed' and e['sources_unchanged'] is True
assert e['argv']==['.venv/bin/python','research/score11_conflict_focused_tabu.py','--seconds','25','--max-steps','2000','--seed','279179','--output-dir','data/score11-conflict-focused-tabu-v1']
assert datetime.fromisoformat(e['started_at'])<datetime.fromisoformat(e['finished_at'])
assert e['job']['seconds']==30;validate_gate(e['gate'],30,256)
assert 0<r['elapsed_seconds']<=e['elapsed_seconds']<30
for p,s in e['sources_before'].items():pin(p,s)
manifest=read('data/score11-conflict-focused-tabu-source-pins.json')
assert len(manifest)==15 and len(e['sources_before'])==16
assert all(e['sources_before'][p]==s for p,s in manifest.items())
assert len(r['pins'])==8
for p,s in r['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==s
heads=[]
for chain,audit in [('data/packed-readonly-n79-r1.chain','data/packed-readonly-chain-main600-r2-independent-audit.json'),('data/packed-readonly-n79-middle-d1541.chain','data/packed-middle-d1541-chain600-r2-independent-audit.json')]:
 p=chain+'/accepted.json';pin(p,read(audit)['final_head_sha']);heads.append({'path':p,'sha256':h(p)})
s=read('data/trades-n79-seed270079-state.json');a=read('data/score11-deficiency-walk-seed279157-v1/best-state.json')
S=set(map(tuple,s['points']));A=set(map(tuple,a['points']))
assert s['n']==a['n']==79 and len(S)==len(s['points'])==158 and len(A)==157 and S-A=={(78,78)} and A<S
assert norm(S)=='f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d'
records=[]
for label,filename,score,distance in [('best','candidate-0000.json',5,1),('distance_exit','candidate-0001.json',45,13)]:
 p='data/score11-conflict-focused-tabu-v1/'+filename;fixed[p]=h(p);doc=read(p);meta=doc['metadata'];pointer=r[label]
 assert pointer['path']==p and {k:v for k,v in pointer.items() if k!='path'}==meta
 assert meta['pins']==r['pins'] and doc['n']==79
 assert all(len(q)==2 and all(type(v)is int and 0<=v<79 for v in q) for q in doc['points'])
 P=set(map(tuple,doc['points']));assert len(P)==len(doc['points'])==157
 deficiencies=[]
 for axis in (0,1):
  degrees=Counter(q[axis] for q in P);assert sorted(degrees[i] for i in range(79))==[1]+[2]*78
  deficiencies.append(next(i for i in range(79) if degrees[i]==1))
 direct=conflicts(P);assert len(direct)==score
 fresh=[verify_certificate(doc),verify_certificate_bruteforce(doc)]
 assert fresh==doc['validators']
 for v in fresh:
  assert not v['errors'] and not v['valid'] and v['point_count']==157 and v['conflict_count']==score
  assert v['normalized_sha256']==norm(P)==meta['normalized_sha256'] and ct(v)==list(direct)
 assert meta['valid'] is False and meta['exact_conflict_count']==score
 assert len(S-P)==meta['source_deleted']==distance and len(P-S)==distance-1
 if label=='best':
  assert P==A and meta['labels']==['initial_best'] and deficiencies==[78,78]
 else:
  assert meta['labels']==['distance_exit'] and P!=A and score>5
 records.append({'label':label,'path':p,'sha256':h(p),'normalized_sha256':norm(P),'point_count':157,'exact_conflict_count':score,'valid':False,'source_deleted':distance,'source_retained':len(S&P),'new_points_outside_source':len(P-S),'deficient_row':deficiencies[0],'deficient_column':deficiencies[1],'equals_initial':P==A,'initial_removed':len(A-P),'initial_added':len(P-A),'direct_conflict_triples':[list(map(list,t)) for t in direct],'both_saved_validators_reproduced':True})
assert r['status']=='step_cap' and r['complete'] is True and r['witness'] is None
assert (r['seed'],r['seconds'],r['max_steps'],r['tabu_capacity'])==(279179,25,2000,64)
assert r['steps_started']==r['steps_completed']==r['accepted']==2000
assert r['candidates_started']==r['candidates_completed']==64000==32*r['steps_completed']
assert r['uphill']==834 and r['neutral']==510 and r['downhill']==656
assert r['uphill']+r['neutral']+r['downhill']==r['accepted']
assert r['tabu_evictions']==1937==r['accepted']+1-64
hist={int(k):v for k,v in r['accepted_score_histogram'].items()}
assert all(type(v)is int and v>0 for v in hist.values()) and sum(hist.values())==r['accepted'] and min(hist)>5
class_totals=Counter()
for k,expected in [('row',16000),('column',16000),('rectangle',32000)]:
 c=r['classes'][k];assert c['started']==c['completed']==expected
 assert sum(c[name] for name in ['illegal','duplicates','tabu','admissible'])==expected
 assert all(type(v)is int and v>=0 for v in c.values())
 class_totals.update(c)
assert class_totals['started']==class_totals['completed']==64000
assert class_totals['admissible']>=r['accepted']
assert sorted(p.name for p in (ROOT/'data/score11-conflict-focused-tabu-v1').iterdir())==['candidate-0000.json','candidate-0001.json','report.json']
for p,s in fixed.items():pin(p,s)
for p,s in e['sources_before'].items():pin(p,s)
result={'accepted':True,'search_complete':False,'policy_run_complete':True,'decision':'Accept fixed invalid artifacts and bounded policy receipt. Best is exact initial score5; D13 score45 is only a source-distance observation. No witness/improvement/global exclusion or automatic continuation.','fixed_artifact_sha256':fixed,'receipt_pin_count':16,'manifest_pin_count':15,'report_and_artifact_pin_count':8,'accepted_chain_heads_unchanged':heads,'states':records,'source_pinned_history':{'steps':2000,'proposal_attempts':64000,'accepted_transitions':2000,'uphill':834,'neutral':510,'downhill':656,'tabu_evictions':1937,'class_totals':dict(class_totals),'accepted_histogram_min':min(hist),'accepted_histogram_max':max(hist),'accepted_histogram_distinct_scores':len(hist),'first_distance_exit_claim':'source-pinned execution history; first occurrence not independently replayed'},'guard':{'outer_seconds':e['elapsed_seconds'],'peak_sampled_rss_kib':e['gate']['peak_sampled_rss_kib'],'cleanup_status':e['gate']['cleanup_status'],'status':e['gate']['gate_status'],'returncode':e['gate']['returncode']},'trajectory_replayed':False,'new_candidates_scored':False,'independent_determinant_triple_checks':2*157*156*155//6,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'audit_elapsed_seconds':time.monotonic()-start}
p=ROOT/'data/score11-conflict-focused-tabu-v1-independent-actual-audit.json';p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='states'},sort_keys=True));print('states',[(v['label'],v['sha256'],v['deficient_row'],v['deficient_column']) for v in records]);print('audit_sha256',hashlib.sha256(p.read_bytes()).hexdigest())
