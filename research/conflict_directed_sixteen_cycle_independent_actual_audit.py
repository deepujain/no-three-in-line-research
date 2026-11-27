"""Audit fixed completed16cycle artifacts only; no DFS or alternate padding."""
from collections import Counter,deque
from datetime import datetime
from itertools import combinations,product
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from research.near_quarter_packed_worker import validate_gate
started=time.monotonic()
def h(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_bytes())
def pin(p,s):assert h(p)==s,p
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def norm(n,P):return hashlib.sha256(canonical({'n':n,'points':[list(p) for p in sorted(P)]})).hexdigest()
def det(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
rp='data/conflict-directed-sixteen-cycle-rebuild157-v1/report.json';ep='data/experiments/shepherd-conflict-directed-sixteen-cycle-rebuild157-v1.json'
fixed={rp:'4c4cbfe3ee78fd030bd91ad3c3ccb542554e5c8fe2b14a54e078e9864ad346d3',ep:'9d77b220eb5f29b824ccefa91f91189bac037d565342a9e4ddd7725a1e0b6702'}
for p,s in fixed.items():pin(p,s)
r=read(rp);e=read(ep)
assert e['argv']==['.venv/bin/python','research/conflict_directed_sixteen_cycle_rebuild157.py','--seconds','25','--max-insertions','1000','--output-dir','data/conflict-directed-sixteen-cycle-rebuild157-v1']
assert e['status']=='completed' and e['sources_unchanged'] is True
assert datetime.fromisoformat(e['started_at'])<datetime.fromisoformat(e['finished_at'])
assert e['job']['seconds']==30;validate_gate(e['gate'],30,256)
assert 0<r['elapsed_seconds']<=e['elapsed_seconds']<30
for p,s in e['sources_before'].items():pin(p,s)
manifest=read('data/conflict-directed-sixteen-cycle-rebuild157-source-pins.json')
assert len(manifest)==21 and len(e['sources_before'])==22
assert all(e['sources_before'][p]==s for p,s in manifest.items())
for p,s in r['pins'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==s
assert len(r['pins'])==6
oldmanifest=read('data/source-disjoint-matching-rebuild157-source-pins.json')
for p,s in oldmanifest.items():pin(p,s)
heads=[]
for chain,audit in [('data/packed-readonly-n79-r1.chain','data/packed-readonly-chain-main600-r2-independent-audit.json'),('data/packed-readonly-n79-middle-d1541.chain','data/packed-middle-d1541-chain600-r2-independent-audit.json')]:
 p=chain+'/accepted.json';pin(p,read(audit)['final_head_sha']);heads.append({'path':p,'sha256':h(p)})
a=read('data/score11-deficiency-walk-seed279157-v1/best-state.json');s=read('data/trades-n79-seed270079-state.json')
assert a['n']==s['n']==79
A=set(map(tuple,a['points']));S=set(map(tuple,s['points']))
assert len(A)==len(a['points'])==157 and len(S)==len(s['points'])==158
assert all(type(x)is int and type(y)is int and 0<=x<79 and 0<=y<79 for x,y in S)
assert A<S and S-A=={(78,78)}
assert all(Counter(p[i] for p in A)==Counter({**{j:2 for j in range(78)},78:1}) for i in (0,1))
assert all(Counter(p[i] for p in S)==Counter({j:2 for j in range(79)}) for i in (0,1))
assert norm(79,A)==r['input_normalized_sha256']=='adf88a13c3a52a5907e5d0661153d02d8c06a08660eea8dba7d954c5e11e952c'
assert norm(79,S)==r['source_normalized_sha256']=='f0ab1e9b47f89b8252eb5fec00b6d2b451bd25545924dc4a491d0b6638dff34d'
conflicts=tuple(t for t in combinations(sorted(A),3) if det(*t)==0);assert len(conflicts)==5
for v in r['input_validation']+a['validators']:
 assert not v['errors'] and not v['valid'] and v['conflict_count']==5 and v['point_count']==157
 assert v['normalized_sha256']==norm(79,A)
 assert sorted(tuple(sorted(map(tuple,t['points']))) for t in v['conflicts'])==list(conflicts)
# Breadth-first traversal of ordered choice sequences, distinct from the worker's
# recursive implementation. Preserve duplicate paths for raw node/leaf counts.
queue=deque([()]);nodes=leaves=0;kernels=set()
while queue:
 C=queue.popleft();nodes+=1
 unhit=[t for t in conflicts if not set(C)&set(t)]
 if not unhit:kernels.add(tuple(sorted(C)));leaves+=1;continue
 rows={x for x,y in C};cols={y for x,y in C}
 for p in unhit[0]:
  if p[0] not in rows and p[1] not in cols:queue.append(C+(p,))
kernels=sorted(kernels,key=lambda C:(len(C),C))
assert nodes==127 and leaves==81 and len(kernels)==81
# Replay only the declared deterministic first-eight selection, no alternatives.
patches=[];padding_checks=0;padded=0
for C in kernels:
 chosen=set(C)
 while len(chosen)<16:
  for p in sorted(A):
   padding_checks+=1
   if all(p[0]!=q[0] and p[1]!=q[1] for q in chosen):chosen.add(p);break
  else:raise AssertionError('padding impossible')
 F=tuple(sorted(chosen));padded+=1
 if F not in patches:patches.append(F)
 if len(patches)==8:break
assert padding_checks==1439 and padded==8
assert [[list(p) for p in F] for F in patches]==r['selected_patches']
assert len(r['patches'])==8
records=[];visits_total=0;direct_checks=0;mask_slices=0
for index,(F,p) in enumerate(zip(patches,r['patches'])):
 assert p['index']==index and p['deleted']==list(map(list,F))
 assert len(F)==16 and len({x for x,y in F})==len({y for x,y in F})==16 and set(F)<=A
 assert all(set(F)&set(t) for t in conflicts)
 R=tuple(sorted(A-set(F)));assert len(R)==141
 # Exact retained validity follows from the independently exhaustive A conflicts
 # and their intersection with F. Full mask reconstructed by determinant slices:
 # fix each x, solve the integer determinant equation for y, no gcd/line iterator.
 pairs=list(combinations(R,2));assert len(pairs)==9870
 blocked=set();pair_visits=0
 for u,v in pairs:
  dx=v[0]-u[0];dy=v[1]-u[1]
  if dx==0:line={(u[0],y) for y in range(79)}
  else:
   line=set()
   for x in range(79):
    num=dy*(x-u[0]);mask_slices+=1
    if num%dx==0:
     y=u[1]+num//dx
     if 0<=y<79:line.add((x,y))
  assert len(line)<=79 and all(det(u,v,q)==0 for q in line)
  pair_visits+=len(line);blocked.update(line)
 mask=sum(1<<(79*x+y) for x,y in blocked)
 assert hex(mask)==p['root_unsafe_hex']
 domains=[]
 for row,_ in F:
  allowed=[]
  for j,(_,col) in enumerate(F):
   # Evaluate all pair determinants for each freed cell, without early exit.
   unsafe_count=sum(det(u,v,(row,col))==0 for u,v in pairs);direct_checks+=len(pairs)
   assert bool(unsafe_count)==((row,col) in blocked)
   if not unsafe_count and (row,col) not in S:allowed.append(j)
  domains.append(allowed)
 assert domains==p['root_domains']
 cert=p['root_matching_cover'];M=list(map(tuple,cert['matching']));U=cert['cover_rows'];V=cert['cover_columns']
 assert cert['matching_size']==len(M)<16
 assert len({i for i,j in M})==len({j for i,j in M})==len(M)
 assert all(0<=i<16 and 0<=j<16 and j in domains[i] for i,j in M)
 assert U==sorted(set(U)) and V==sorted(set(V)) and all(type(v)is int and 0<=v<16 for v in U+V)
 assert len(U)+len(V)==len(M) and all(i in U or j in V for i in range(16) for j in domains[i])
 assert p['status']=='root_matching_obstruction' and p['complete'] is True and p['closure'] is True
 assert p['dfs_exhausted'] is False and p['root_state_restored'] is None and p['insertions_started']==0
 assert all(p[k] is True for k in ['retained_validation_complete','root_mask_complete','root_domains_complete','root_matching_complete'])
 records.append({'index':index,'deleted':list(map(list,F)),'retained_points':141,'retained_valid_by_complete_conflict_cover':True,'root_pair_cell_visits':pair_visits,'root_unsafe_cells':len(blocked),'domain_edges':sum(map(len,domains)),'matching_size':len(M),'cover_size':len(U)+len(V),'root_domains':domains,'matching_cover':cert,'fixed_patch_excluded':True})
 visits_total+=pair_visits
sizes=[p['matching_size'] for p in records];edges=[p['domain_edges'] for p in records]
assert sizes==edges==[0,0,1,1,1,2,0,0]
c=r['counters']
expected={'cover_nodes_started':nodes,'cover_nodes_completed':nodes,'cover_leaves':leaves,'distinct_kernels':len(kernels),'padded_kernels':padded,'padding_cells_started':padding_checks,'padding_cells_completed':padding_checks,'root_lines_started':8*9870,'root_lines_completed':8*9870,'root_cell_visits_started':visits_total,'root_cell_visits_completed':visits_total,'root_domain_cells_started':2048,'root_domain_cells_completed':2048,'matching_edge_scans_started':5,'matching_edge_scans_completed':5,'certificate_edge_checks_started':5,'certificate_edge_checks_completed':5}
assert visits_total==524918
for k,v in c.items():assert v==expected.get(k,0),(k,v,expected.get(k,0))
assert r['status']=='selected_families_exhausted' and r['complete'] is True and r['closure'] is True
assert r['identity_valid'] is True and all(r[k] is True for k in ['source_validation_complete','kernels_complete','patch_selection_complete'])
assert r['kernel_count']==81 and (r['n'],r['target'],r['width'],r['max_patches'],r['max_insertions'],r['shared_soft_seconds'])==(79,157,16,8,1000,25)
assert r['diagnostic156'] is None and r['witness157'] is None
assert sorted(p.name for p in (ROOT/Path(rp).parent).iterdir())==['report.json']
assert r['arithmetic_bounds']=={'cover_nodes':364,'cover_leaves':243,'padding_cells':610416,'root_lines':78960,'root_cell_visits':6237840,'root_domain_cells':2048,'augmenting_matching_edge_scans':32768,'cover_edge_scans':2048,'certificate_edge_checks':2048,'candidate_cell_visits_per_insertion':12324,'candidate_cell_visits':12324000,'root_plus_candidate_cell_visits':18561840,'maximum_added':16}
for p,s in fixed.items():pin(p,s)
for p,s in e['sources_before'].items():pin(p,s)
result={'accepted':True,'selected_families_complete':True,'unrestricted_closure':False,'decision':'All eight declared deterministic patches independently excluded by complete exact root domains and matching/cover certificates. No conclusion for other padding or general16cycles; no unchanged continuation.','report_sha256':h(rp),'receipt_sha256':h(ep),'receipt_source_pins':22,'manifest_source_pins':21,'report_pins':6,'historical_manifest_pins_verified':len(oldmanifest),'accepted_chain_heads_unchanged':heads,'initial_conflicts':[list(map(list,t)) for t in conflicts],'independent_kernel_nodes':nodes,'independent_kernel_leaves':leaves,'independent_distinct_kernels':len(kernels),'kernels_canonical_sha256':hashlib.sha256(canonical(kernels)).hexdigest(),'padding_checks':padding_checks,'patches':records,'direct_freed_cell_pair_determinant_checks':direct_checks,'full_mask_integer_determinant_x_slices':mask_slices,'total_root_pair_cell_visits':visits_total,'matching_sizes':sizes,'domain_edge_counts':edges,'insertions':0,'diagnostic156':None,'witness157':None,'guard':{'outer_seconds':e['elapsed_seconds'],'peak_sampled_rss_kib':e['gate']['peak_sampled_rss_kib'],'cleanup_status':e['gate']['cleanup_status'],'status':e['gate']['gate_status'],'returncode':e['gate']['returncode']},'search_replayed':False,'alternate_padding_constructed':False,'candidate_geometry_scored':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'audit_elapsed_seconds':time.monotonic()-started}
out=ROOT/'data/conflict-directed-sixteen-cycle-rebuild157-v1-independent-actual-audit.json';out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['patches','initial_conflicts']},sort_keys=True));print('audit_sha256',hashlib.sha256(out.read_bytes()).hexdigest())
