"""One fixed n5 singleton-relocation diagnostic; source stage until Root gate."""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = 'data/full-complement-row-domain-n5-fixture-v1.json'
FIXTURE_SHA = '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37'
SPEC = 'research/singleton-migration-n5-source-tiny-spec-v1.md'
SPEC_SHA = 'e00ed95695cd77cd6986938557279755c3cd41a1fef940f642107e7f9260dcf3'
NOTE = 'research/singleton-migration-n5-implementation-v1.md'
CAPS = {'determinants':312, 'pair_keys':72, 'incidences':144,
        'recoveries':72, 'endpoint_visits':360, 'scores':64,
        'key_comparisons':64, 'publications':3}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',',':'), allow_nan=False).encode('ascii')


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('JSON constant')))


class Budget:
    def __init__(self, started=None, clock=time.monotonic):
        self.clock = clock
        self.started = clock() if started is None else started
        self.counts = dict.fromkeys(CAPS, 0)
        self.components = {}

    def check(self, limit=7):
        require(self.clock()-self.started < limit, 'deadline')

    def charge(self, kind, component, limit=7):
        self.check(limit)
        require(self.counts[kind] < CAPS[kind], 'quota '+kind)
        self.counts[kind] += 1
        key = component+':'+kind
        self.components[key] = self.components.get(key, 0)+1


def validate_points(value):
    require(type(value) in (list,tuple) and len(value)==9, 'nine points')
    out=[]
    for p in value:
        require(type(p) in (list,tuple) and len(p)==2, 'point pair')
        require(all(type(v) is int and 0<=v<5 for v in p), 'strict coordinate')
        out.append(tuple(p))
    require(len(set(out))==9 and out==sorted(out), 'distinct canonical points')
    return tuple(out)


def validate_fixture(raw):
    require(type(raw) is bytes and len(raw)==72 and hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,
            'fixed n5 byte identity')
    doc=decode(raw)
    require(type(doc) is dict and set(doc)=={'n','points'} and type(doc['n']) is int and doc['n']==5,
            'fixed document schema')
    points=validate_points(doc['points'])
    require(compact({'n':5,'points':points})==raw, 'canonical fixture bytes')
    require(tuple(sum(p[1]==r for p in points) for r in range(5))==(2,2,2,2,1), 'fixed row loads')
    require((0,4) in points, 'fixed singleton')
    return points


def producer(points, budget):
    """Adjacent-edge determinants; no line-table or oracle routine shared."""
    d=[0]*9; c=[0]*4; h=[[0]*9 for _ in range(4)]; baseline=0
    for i,j,k in itertools.combinations(range(9),3):
        budget.charge('determinants','producer_baseline')
        a,b,z=points[i],points[j],points[k]
        if (b[0]-a[0])*(z[1]-b[1])==(b[1]-a[1])*(z[0]-b[0]):
            baseline+=1; d[i]+=1; d[j]+=1; d[k]+=1
    require(baseline==14, 'producer baseline')
    for qi in range(4):
        q=(qi+1,4)
        for i,j in itertools.combinations(range(9),2):
            budget.charge('determinants','producer_destinations')
            a,b=points[i],points[j]
            if (b[0]-a[0])*(q[1]-b[1])==(b[1]-a[1])*(q[0]-b[0]):
                c[qi]+=1; h[qi][i]+=1; h[qi][j]+=1
    best=None
    for i,p in enumerate(points):
        if p[1]==4:
            continue
        for qi in range(4):
            budget.charge('scores','producer')
            score=baseline-d[i]+c[qi]-h[qi][i]
            key=(score,p[1],p[0],qi+1)
            budget.charge('key_comparisons','producer')
            if score<baseline and (best is None or key<best):
                best=key
    return {'baseline':baseline,'d':d,'c':c,'h':h,'best':best}


def validate_profile(profile):
    require(type(profile) is dict and set(profile)=={'baseline','d','c','h','best'}, 'profile schema')
    require(type(profile['baseline']) is int and profile['baseline']==14, 'profile baseline')
    for name,size,bound in (('d',9,28),('c',4,36)):
        row=profile[name]
        require(type(row) is list and len(row)==size and
                all(type(v) is int and 0<=v<=bound for v in row), 'profile '+name)
    require(type(profile['h']) is list and len(profile['h'])==4, 'profile h rows')
    for row in profile['h']:
        require(type(row) is list and len(row)==9 and all(type(v) is int and 0<=v<=8 for v in row), 'profile h cells')
    best=profile['best']
    require(best is None or (type(best) is tuple and len(best)==4 and all(type(v) is int for v in best)
            and 0<=best[0]<14 and 0<=best[1]<4 and 0<=best[2]<5 and 1<=best[3]<5), 'profile best')


def verify_profile(points, profile, budget):
    """Independent signed direction/intercept endpoint table and scalar minimum."""
    validate_profile(profile)
    table={}
    try:
        for i in range(9):
            for j in range(i+1,9):
                budget.charge('pair_keys','independent_current')
                x,y=points[i]; xx,yy=points[j]
                dx,dy=xx-x,yy-y; g=math.gcd(abs(dx),abs(dy)); dx//=g; dy//=g
                if dx<0 or (dx==0 and dy<0):
                    dx=-dx; dy=-dy
                key=(dx,dy,dx*y-dy*x)
                table[key]=table.get(key,0)|(1<<i)|(1<<j)
        require(len(table)<=36, 'current line cap')
        baseline=0; independent_d=[0]*9
        for key,mask in table.items():
            budget.charge('recoveries','independent_current')
            m=mask.bit_count(); require(2<=m<=9, 'line multiplicity')
            baseline+=m*(m-1)*(m-2)//6
            pending=mask
            while pending:
                budget.charge('endpoint_visits','independent_d')
                bit=pending & -pending; i=bit.bit_length()-1; pending^=bit
                independent_d[i]+=(m-1)*(m-2)//2
            table[key]=(mask,m)
        require(baseline==14 and independent_d==profile['d'] and sum(independent_d)==42, 'independent baseline/d')
        singleton=points.index((0,4))
        for qi in range(4):
            qx,qy=qi+1,4; independent_c=0; independent_h=[0]*9
            for (dx,dy,intercept),(mask,m) in table.items():
                budget.charge('incidences','independent_current')
                if dx*qy-dy*qx!=intercept:
                    continue
                independent_c+=m*(m-1)//2; pending=mask
                while pending:
                    budget.charge('endpoint_visits','independent_h')
                    bit=pending & -pending; i=bit.bit_length()-1; pending^=bit
                    independent_h[i]+=m-1
            require(independent_c==profile['c'][qi] and independent_h==profile['h'][qi], 'independent c/h')
            require(sum(independent_h)==2*independent_c and independent_h[singleton]==0, 'h identities')
    finally:
        table.clear()
    best=None
    for row in range(4):
        for i,p in enumerate(points):
            if p[1]!=row:
                continue
            for x in range(1,5):
                budget.charge('scores','independent_minimum')
                score=14-profile['d'][i]+profile['c'][x-1]-profile['h'][x-1][i]
                require(0<=score and profile['c'][x-1]>=profile['h'][x-1][i], 'score nonnegative correction')
                key=(score,row,p[0],x)
                budget.charge('key_comparisons','independent_minimum')
                if score<14 and (best is None or key<best):
                    best=key
    require(best==profile['best'], 'independent global move minimum')
    return best


def check_candidate(original, candidate, move):
    candidate=validate_points(candidate)
    score,row,removed_x,inserted_x=move
    require(type(score) is int and 0<=score<14 and type(row) is int and 0<=row<4,
            'candidate move')
    removed=(removed_x,row); inserted=(inserted_x,4)
    require(removed in original and inserted not in original, 'candidate endpoints')
    require(set(original)-set(candidate)=={removed} and set(candidate)-set(original)=={inserted}, 'exact relocation')
    require(tuple(sum(p[1]==r for p in candidate) for r in range(5))==tuple(1 if r==row else 2 for r in range(5)), 'candidate row loads')
    return candidate


def direct_candidate_raw(points,budget):
    """Fresh base-vertex determinant oracle, separate from producer."""
    raw=0
    for i in range(len(points)-2):
        for j in range(i+1,len(points)-1):
            for k in range(j+1,len(points)):
                budget.charge('determinants','candidate_direct')
                a,b,c=points[i],points[j],points[k]
                raw+=int((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1])==0)
    return raw


def endpoint_candidate_raw(points,budget):
    """Fresh normal-form line oracle; does not call current-table builder."""
    lines={}
    try:
        for i,a in enumerate(points):
            for j in range(i+1,len(points)):
                budget.charge('pair_keys','candidate_endpoint')
                b=points[j]; A=b[1]-a[1]; B=a[0]-b[0]; C=-(A*a[0]+B*a[1])
                divisor=math.gcd(math.gcd(abs(A),abs(B)),abs(C))
                A//=divisor; B//=divisor; C//=divisor
                if A<0 or (A==0 and B<0): A=-A; B=-B; C=-C
                key=(A,B,C); lines[key]=lines.get(key,0)|(1<<i)|(1<<j)
        require(len(lines)<=36, 'candidate line cap')
        total=0
        for mask in lines.values():
            budget.charge('recoveries','candidate_endpoint')
            count=mask.bit_count(); require(2<=count<=9, 'candidate multiplicity')
            total+=count*(count-1)*(count-2)//6
        return total
    finally:
        lines.clear()


def diagnose(points,budget):
    points=validate_points(points)
    require(hashlib.sha256(compact({'n':5,'points':points})).hexdigest()==FIXTURE_SHA, 'diagnose fixed identity')
    profile=producer(points,budget)
    best=verify_profile(points,profile,budget)
    if best is None:
        return profile,None,None
    score,row,removed_x,inserted_x=best
    candidate=tuple(sorted(tuple(p for p in points if p!=(removed_x,row))+((inserted_x,4),)))
    candidate=check_candidate(points,candidate,best)
    budget.check()
    direct=direct_candidate_raw(candidate,budget)
    require(direct==score, 'candidate direct score')
    budget.check()
    endpoint=endpoint_candidate_raw(candidate,budget)
    require(endpoint==score, 'candidate endpoint score')
    return profile,candidate,{'direct_raw':direct,'endpoint_raw':endpoint}


def digest(path,budget,limit=7):
    result=hashlib.sha256()
    with Path(path).open('rb') as source:
        while True:
            budget.check(limit)
            block=source.read(65536)
            if not block: return result.hexdigest()
            result.update(block)


def load_pins(path,budget):
    path=Path(path).resolve()
    require(path.stat().st_size<=65536, 'manifest byte cap')
    raw=path.read_bytes(); require(len(raw)<=65536, 'manifest encoded cap')
    mapping=decode(raw)
    require(type(mapping) is dict and 1<=len(mapping)<=64, 'manifest count')
    pins={}
    for name,value in mapping.items():
        require(type(name) is str and 0<len(name)<=1024 and type(value) is str and len(value)==64
                and all(c in '0123456789abcdef' for c in value), 'pin schema')
        resolved=str((ROOT/name).resolve())
        require(len(resolved)<=1024 and resolved not in pins and resolved!=str(path), 'pin alias/self')
        pins[resolved]=value
    for name,expected in ((FIXTURE,FIXTURE_SHA),(SPEC,SPEC_SHA)):
        require(pins.get(str((ROOT/name).resolve()))==expected, 'mandatory fixed pin')
    for required in (Path(__file__).resolve(),Path(sys.executable).resolve(),ROOT/NOTE):
        require(str(required) in pins, 'mandatory source/runtime/note pin')
    pins[str(path)]=hashlib.sha256(raw).hexdigest()
    verify_pins(pins,budget)
    return pins


def verify_pins(pins,budget,limit=7):
    for path,expected in pins.items():
        require(digest(path,budget,limit)==expected, 'pin drift '+path)


class Store:
    def __init__(self,path,budget):
        self.path=Path(path); self.budget=budget
        self.path.mkdir(parents=False,exist_ok=False)

    def publish(self,name,value,cap,*,failure=False):
        # Failure gets the owned interval; successful publications use the soft limit.
        self.budget.charge('publications','failure' if failure else name,limit=10 if failure else 9)
        require(name in {'evidence.json','candidate.json','witness.json','failure.json'}, 'publication name')
        raw=compact(value); require(len(raw)<=cap, 'publication byte cap')
        path=self.path/name
        with path.open('xb') as output:
            output.write(raw); output.flush(); os.fsync(output.fileno())
        directory=os.open(self.path,os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
        return hashlib.sha256(raw).hexdigest()


def run(output,manifest,*,started=None,clock=time.monotonic):
    budget=Budget(started=started,clock=clock); store=None
    try:
        store=Store(output,budget)
        pins=load_pins(manifest,budget)
        fixture=ROOT/FIXTURE
        require(fixture.stat().st_size==72, 'fixture file size')
        points=validate_fixture(fixture.read_bytes())
        profile,candidate,raw_checks=diagnose(points,budget)
        candidate_sha=None
        if candidate is not None:
            doc={'n':5,'points':candidate,'raw_score':profile['best'][0],
                 'normalized_sha256':hashlib.sha256(compact({'n':5,'points':candidate})).hexdigest(),
                 'move':profile['best'],'input_sha256':FIXTURE_SHA,'raw_checks':raw_checks,
                 'adopted':False,'requires_independent_witness_acceptance':profile['best'][0]==0}
            candidate_sha=store.publish('witness.json' if profile['best'][0]==0 else 'candidate.json',doc,16384)
        verify_pins(pins,budget,9)
        report={'schema':1,'scope':'one fixed n5 singleton relocation diagnostic',
                'input_sha256':FIXTURE_SHA,'n':5,'point_count':9,'baseline':14,
                'profile':profile,'all_arrays_verified':True,'all_32_moves_verified':True,
                'candidate_sha256':candidate_sha,'raw_checks':raw_checks,'adopted':False,
                'status':'no_strict_relocation' if candidate is None else 'strict_relocation_proposal',
                'source_pins':pins,'counters':dict(budget.counts),'components':dict(budget.components),
                'ceilings':CAPS,'owned_guard_required':True,'failure_invalidates_receipt':True}
        # Include the pending evidence attempt in its own immutable counter snapshot.
        report['counters']['publications']+=1
        report['components']['evidence.json:publications']=1
        evidence_sha=store.publish('evidence.json',report,65536)
        verify_pins(pins,budget,9)
        budget.check(9)
        return {'status':report['status'],'evidence_sha256':evidence_sha,'candidate_sha256':candidate_sha}
    except Exception as error:
        if store is not None:
            try:
                store.publish('failure.json',{'status':'failed','error_type':type(error).__name__,
                    'message':str(error)[:1024],'counts':dict(budget.counts),'components':dict(budget.components),
                    'candidate_or_witness_may_exist':True},16384,failure=True)
            except Exception:
                pass
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.output,args.manifest,started=ENTRY_STARTED),sort_keys=True))
