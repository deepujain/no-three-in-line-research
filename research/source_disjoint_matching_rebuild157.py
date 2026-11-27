"""One source-disjoint matching rebuild: exact valid-prefix MRV, bounded pilot."""
import argparse
from collections import Counter,deque
from itertools import combinations
import hashlib,json,math,os
from pathlib import Path
import sys,tempfile,time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.verify import verify_certificate,verify_certificate_bruteforce,normalized_sha256
PUBLISHED='data/published-n78.json'
EXCLUDED='data/trades-n79-seed270079-state.json'
INPUT_PINS={PUBLISHED:'4c13bf3e807885f9e61d00593bb27d060b773e40d887f63d955d962d9890a912',EXCLUDED:'9566a3196faf2f5233b9e8b2e1fcd5d23c0c9ed70262baec1a24b45a9bb32f26'}
MAX_INSERTIONS=2000


class InsertionCap(Exception):pass


def cells(points,n):
    if type(n)is not int or n<2:raise ValueError('invalid board')
    result=list(points)
    if any(not isinstance(p,tuple) or len(p)!=2 or any(type(c)is not int or not 0<=c<n for c in p) for p in result) or len(set(result))!=len(result):raise ValueError('invalid or duplicate cells')
    return set(result)


def deterministic_matching(points,n,check=lambda:None):
    """Lexicographically first edge of every degree-two component has color0."""
    B=cells(points,n)
    if len(B)!=2*n or any(Counter(p[a] for p in B)!=Counter({i:2 for i in range(n)}) for a in (0,1)):raise ValueError('not a degree-two source')
    graph={}
    for x,y in sorted(B):graph.setdefault((0,x),[]).append((1,y));graph.setdefault((1,y),[]).append((0,x))
    remaining=set(B);retained=set();components=[]
    while remaining:
        check();start=min(remaining);current,nxt=(0,start[0]),(1,start[1]);length=0
        while True:
            check();edge=(current[1],nxt[1]) if current[0]==0 else (nxt[1],current[1])
            if length and edge==start:break
            if edge not in remaining:raise RuntimeError('cycle did not close correctly')
            remaining.remove(edge)
            if length%2==0:retained.add(edge)
            following=next(v for v in graph[nxt] if v!=current)
            current,nxt=nxt,following;length+=1
        if length%2 or current!=(0,start[0]):raise RuntimeError('invalid cycle parity')
        components.append({'least_edge':list(start),'edges':length})
    if len(retained)!=n or any(Counter(p[a] for p in retained)!=Counter(range(n)) for a in (0,1)):raise RuntimeError('invalid retained matching')
    return tuple(sorted(retained)),components


def line_cells(n,a,b):
    """Primitive lattice line, each in-bounds cell exactly once; no float math."""
    if a==b:raise ValueError('coincident line points')
    dx,dy=b[0]-a[0],b[1]-a[1];d=math.gcd(dx,dy);dx//=d;dy//=d
    if dx<0 or dx==0 and dy<0:dx=-dx;dy=-dy
    lows=[];highs=[]
    for c,step in zip(a,(dx,dy)):
        if step>0:lows.append((-c+step-1)//step);highs.append((n-1-c)//step)
        elif step<0:
            step=-step;lows.append((c-(n-1)+step-1)//step);highs.append(c//step)
    for t in range(max(lows),min(highs)+1):yield a[0]+t*dx,a[1]+t*dy


def scan_line(n,a,b,unsafe,phase,counters,check):
    counters[phase+'_lines_started']+=1;check()
    for x,y in line_cells(n,a,b):
        counters[phase+'_cell_visits_started']+=1;check()
        unsafe|=1<<(n*x+y)
        counters[phase+'_cell_visits_completed']+=1
    counters[phase+'_lines_completed']+=1
    return unsafe


def root_domains(n,R,forbidden,counters,check):
    unsafe=0
    for a,b in combinations(R,2):unsafe=scan_line(n,a,b,unsafe,'root',counters,check)
    domains=[]
    for row in range(n):
        mask=0
        for col in range(n):
            counters['root_domain_cells_started']+=1;check()
            if (row,col) not in forbidden and not unsafe>>(n*row+col)&1:mask|=1<<col
            counters['root_domain_cells_completed']+=1
        domains.append(mask)
    return unsafe,domains


def columns(mask):
    while mask:
        bit=mask&-mask;yield bit.bit_length()-1;mask-=bit


def maximum_matching(domains,n,counters,check):
    """At most one visit per row per root augmentation; each allowed edge once."""
    matched=[-1]*n
    for root in range(n):
        seen_rows=set();seen_cols=set()
        def augment(row):
            check()
            if row in seen_rows:return False
            seen_rows.add(row)
            for col in columns(domains[row]):
                counters['matching_edge_scans_started']+=1;check();counters['matching_edge_scans_completed']+=1
                if col in seen_cols:continue
                seen_cols.add(col)
                if matched[col]<0 or augment(matched[col]):matched[col]=row;return True
            return False
        augment(root)
    primal=sorted((row,col) for col,row in enumerate(matched) if row>=0)
    row_match=dict(primal);reachable_rows=set(range(n))-set(row_match);reachable_cols=set();queue=deque(sorted(reachable_rows))
    while queue:
        check();row=queue.popleft()
        for col in columns(domains[row]):
            counters['cover_edge_scans_started']+=1;check();counters['cover_edge_scans_completed']+=1
            if row_match.get(row)==col or col in reachable_cols:continue
            reachable_cols.add(col)
            if matched[col]>=0 and matched[col] not in reachable_rows:reachable_rows.add(matched[col]);queue.append(matched[col])
    cover_rows=sorted(set(range(n))-reachable_rows);cover_cols=sorted(reachable_cols)
    certificate={'matching':[list(e) for e in primal],'cover_rows':cover_rows,'cover_columns':cover_cols,'matching_size':len(primal)}
    validate_matching_cover(domains,n,certificate,check,counters)
    return certificate


def validate_matching_cover(domains,n,certificate,check=lambda:None,counters=None):
    primal=certificate['matching'];U=certificate['cover_rows'];V=certificate['cover_columns']
    if (len(domains)!=n or any(type(mask)is not int or mask<0 or mask>>n for mask in domains)
            or len(primal)!=certificate['matching_size'] or len({p[0] for p in primal})!=len(primal) or len({p[1] for p in primal})!=len(primal)
            or any(len(p)!=2 or any(type(v)is not int or not 0<=v<n for v in p) or not domains[p[0]]>>p[1]&1 for p in primal)
            or U!=sorted(set(U)) or V!=sorted(set(V)) or any(type(v)is not int or not 0<=v<n for v in U+V)
            or len(U)+len(V)!=len(primal)):raise ValueError('invalid matching/cover certificate')
    for row in range(n):
        for col in columns(domains[row]):
            if counters is not None:counters['certificate_edge_checks_started']+=1
            check()
            if row not in U and col not in V:raise ValueError('cover misses an allowed edge')
            if counters is not None:counters['certificate_edge_checks_completed']+=1
    return True


def new_counters():
    names=('root_lines','root_cell_visits','root_domain_cells','matching_edge_scans','cover_edge_scans','certificate_edge_checks','insertions','candidate_lines','candidate_cell_visits')
    return {**{name+'_'+phase:0 for name in names for phase in ('started','completed')},'backtracks':0,'rollbacks':0,'domain_wipeouts':0,'maximum_added':0,'full_assignments':0}


class Constructor:
    """Pure search kernel; a test callback may collect all tiny completions."""
    def __init__(self,n,retained,forbidden,domains,unsafe,counters,check,limit):
        if type(limit)is not int or not 0<=limit<=MAX_INSERTIONS:raise ValueError('invalid insertion cap')
        self.n=n;self.R=tuple(retained);self.forbidden=frozenset(forbidden);self.domains=tuple(domains);self.root_unsafe=unsafe
        self.counters=counters;self.check=check;self.limit=limit;self.path=[];self.root_restored=False
    def run(self,on_prefix):
        before=(self.R,self.domains,self.root_unsafe,self.forbidden)
        def dfs(assigned,used,unsafe):
            self.check();depth=len(self.path)
            if depth in (self.n-1,self.n):
                if depth==self.n:self.counters['full_assignments']+=1
                if on_prefix(tuple(self.path)):
                    if depth!=self.n:raise RuntimeError('only full witness may stop callback')
                    return True
            if depth==self.n:return False
            choices=[]
            for row in range(self.n):
                self.check()
                if assigned>>row&1:continue
                options=self.domains[row]&~used&~(unsafe>>(self.n*row))&((1<<self.n)-1)
                if not options:self.counters['domain_wipeouts']+=1;return False
                choices.append((options.bit_count(),row,options))
            _,row,options=min(choices)
            for col in columns(options):
                if self.counters['insertions_started']>=self.limit:raise InsertionCap
                self.counters['insertions_started']+=1;self.check();point=(row,col);following=unsafe
                for other in self.R+tuple(self.path):following=scan_line(self.n,point,other,following,'candidate',self.counters,self.check)
                self.path.append(point);self.counters['insertions_completed']+=1
                self.counters['maximum_added']=max(self.counters['maximum_added'],len(self.path))
                stopped=False
                try:
                    stopped=dfs(assigned|1<<row,used|1<<col,following)
                    if stopped:return True
                finally:
                    if self.path.pop()!=point:raise RuntimeError('rollback mismatch')
                    self.counters['rollbacks']+=1
                    if not stopped:self.counters['backtracks']+=1
            return False
        try:return dfs(0,0,self.root_unsafe)
        finally:
            self.root_restored=not self.path and before==(self.R,self.domains,self.root_unsafe,self.forbidden)
            if not self.root_restored:raise RuntimeError('root state not restored')


def canonical_conflicts(report):return sorted(tuple(sorted(map(tuple,c['points']))) for c in report['conflicts'])


def dual_valid(points,n,check):
    cert={'n':n,'points':[list(p) for p in sorted(points)]}
    check();first=verify_certificate(cert);check();second=verify_certificate_bruteforce(cert)
    if (any(v['errors'] or not v['valid'] or v['point_count']!=len(points) or v['conflict_count'] for v in (first,second))
            or first['normalized_sha256']!=second['normalized_sha256'] or canonical_conflicts(first)!=canonical_conflicts(second)):
        raise RuntimeError('dual validity disagreement')
    return cert,[first,second]


def atomic(path,value):
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def save_candidate(n,R,M,B,S,path,kind,check,pins):
    P=set(R)|set(M)
    if (len(P)!=len(R)+len(M) or not set(R)<=B or set(M)&(B|S)
            or P&B!=set(R) or P&S!=set(R)&S
            or len({x for x,y in M})!=len(M) or len({y for x,y in M})!=len(M)
            or any(max(Counter(p[a] for p in P).values())>2 for a in (0,1))):raise RuntimeError('candidate family/distance mismatch')
    if len(B)==2*(n-1) and len(B-P)!=n-1:raise RuntimeError('published distance mismatch')
    if len(S)==2*n and len(S-P)<n+1:raise RuntimeError('excluded-source distance mismatch')
    if len(M) not in (n-1,n) or len(R)!=n-1:raise RuntimeError('candidate target mismatch')
    if len(M)==n and any([Counter(p[a] for p in P)[i] for i in range(n)]!=[2]*(n-1)+[1] for a in (0,1)):raise RuntimeError('full degree pattern mismatch')
    cert,reports=dual_valid(P,n,check)
    cert['metadata']={'method':'source_disjoint_matching_rebuild','kind':kind,'valid':True,'normalized_sha256':reports[0]['normalized_sha256'],'retained':list(R),'matching':list(M),'published_deleted':len(B-P),'published_retained':len(P&B),'excluded_source_deleted':len(S-P),'excluded_source_retained':len(P&S),'new_points_outside_published':len(P-B),'improves_verified_lower_bound':kind=='full_witness','novelty_claim':False,'pins':pins}
    cert['validators']=reports
    # No deadline check after both validators: persist completed valid evidence.
    atomic(path,cert);return cert['metadata']


def verify_pins(pins):
    for path,expected in pins.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('pinned source/input changed: '+str(path))


def load_sources(check,pins):
    docs={}
    for name,expected in INPUT_PINS.items():
        check();path=ROOT/name;raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('fixed source bytes mismatch')
        pins[str(path)]=expected;docs[name]=json.loads(raw)
    b,s=docs[PUBLISHED],docs[EXCLUDED]
    if b['n']!=78 or s['n']!=79:raise ValueError('fixed source dimensions mismatch')
    B=cells([tuple(p) for p in b['points']],78);S=cells([tuple(p) for p in s['points']],79)
    if len(B)!=156 or len(S)!=158:raise ValueError('fixed source cardinality mismatch')
    if any(Counter(p[a] for p in B)!=Counter({i:2 for i in range(78)}) for a in (0,1)):raise ValueError('published source axes mismatch')
    _,reports=dual_valid(B,78,check)
    return B,S,reports


def search_anchor(n,B,S,R,out,report,check,pins,max_insertions):
    R=tuple(R);B=cells(B,n);S=cells(S,n);forbidden=B|S;c=report['counters'];kernel=None
    if (len(R)!=n-1 or not set(R)<=B
            or any(Counter(p[a] for p in R)!=Counter(range(n-1)) for a in (0,1))):raise ValueError('invalid retained matching')
    try:
        unsafe=0
        for a,b in combinations(R,2):unsafe=scan_line(n,a,b,unsafe,'root',c,check)
        report['root_mask_complete']=True;report['root_unsafe_hex']=hex(unsafe)
        domains=[]
        for row in range(n):
            mask=0
            for col in range(n):
                c['root_domain_cells_started']+=1;check()
                if (row,col) not in forbidden and not unsafe>>(n*row+col)&1:mask|=1<<col
                c['root_domain_cells_completed']+=1
            domains.append(mask)
        report['root_domains_complete']=True;report['root_domains']=[list(columns(mask)) for mask in domains]
        gate=maximum_matching(domains,n,c,check);report['root_matching_complete']=True;report['root_matching_cover']=gate
        if gate['matching_size']<n:report['status']='root_matching_obstruction';report['complete']=True;report['closure']=True
        else:
            kernel=Constructor(n,R,forbidden,domains,unsafe,c,check,max_insertions)
            def on_prefix(M):
                if len(M)==n-1 and report['diagnostic156'] is None:report['diagnostic156']=save_candidate(n,R,M,B,S,out/'diagnostic156.json','diagnostic156',check,pins)
                if len(M)==n:
                    report['witness157']=save_candidate(n,R,M,B,S,out/'witness157.json','full_witness',check,pins);return True
                return False
            stopped=kernel.run(on_prefix)
            report['status']='witness' if stopped else 'fixed_family_exhausted';report['complete']=True;report['closure']=not stopped
    finally:
        report['root_state_restored']=None if kernel is None else kernel.root_restored


def run(out,seconds=25,max_insertions=MAX_INSERTIONS,*,clock=time.monotonic,started=None):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:raise ValueError('invalid shared duration')
    if type(max_insertions)is not int or not 0<=max_insertions<=MAX_INSERTIONS:raise ValueError('invalid insertion cap')
    start=clock() if started is None else started;deadline=start+seconds
    def check():
        if clock()>=deadline:raise TimeoutError
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),ROOT/'src/verify.py')}
    c=new_counters();report={'method':'one_source_disjoint_matching_rebuild157','status':'incomplete','complete':False,'closure':False,'n':79,'target':157,'max_insertions':max_insertions,'shared_soft_seconds':seconds,'counters':c,'root_mask_complete':False,'root_domains_complete':False,'root_matching_complete':False,'diagnostic156':None,'witness157':None,'scope':'One deterministic retained matching, forbidden published/excluded sources; no alternate anchor, restart or automatic continuation.'}
    report['arithmetic_bounds']={'root_lines':3003,'root_cell_visits':237237,'root_domain_cells':6241,'augmenting_matching_edge_scans':493039,'cover_edge_scans':6241,'certificate_edge_checks':6241,'candidate_cell_visits_per_insertion':12324,'candidate_cell_visits':12324*max_insertions,'maximum_added':79}
    try:
        B,S,source_reports=load_sources(check,pins);report['published_validation']=source_reports;report['excluded_source_normalized_sha256']=normalized_sha256(79,S)
        R,components=deterministic_matching(B,78,check)
        report['retained_points']=[list(p) for p in R];report['retained_normalized_sha256']=normalized_sha256(79,R);report['components']=components
        # R is a subset of dual-verified B; no source S geometry is evaluated.
        search_anchor(79,B,S,R,out,report,check,pins,max_insertions)
    except TimeoutError:report['status']='timeout'
    except InsertionCap:report['status']='insertion_cap'
    except Exception as error:report['status']='error';report['error']=f'{type(error).__name__}: {error}'
    report.setdefault('root_state_restored',None)
    try:verify_pins(pins)
    except (ValueError,OSError) as error:report['status']='error';report['complete']=False;report['closure']=False;report['error']=str(error)
    report['pins']=pins;report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',report);return report


def main():
    started=time.monotonic()
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--seconds',type=float,default=25);parser.add_argument('--max-insertions',type=int,default=MAX_INSERTIONS)
    a=parser.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.output_dir,a.seconds,a.max_insertions,started=started);print(json.dumps(result,sort_keys=True));return 1 if result['status']=='error' else (0 if result['complete'] else 2)


if __name__=='__main__':sys.exit(main())
