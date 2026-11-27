"""Closed fixed64 audit fixtures: approved n4 route, explicit identity/geometry spies."""
from contextlib import ExitStack,contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
from research import restricted_three_row64_actual_chain_adapter as adapter

ROOT=adapter.ROOT
CONTROL='data/restricted-three-row-independent-control-preparation.json'
CONTROL_SHA='d8086c685854cc28eedeb1a9422d7330657ce880f01d12cc14f75be497f49c1e'
OLD=((0,0),(0,1),(0,2),(0,3),(1,1),(2,2),(3,3))
chain=adapter.chain
pack=chain.canonical

def digest(raw):return hashlib.sha256(raw).hexdigest()
def normalized(points):return tuple(sorted(tuple(p) for p in points))

def chain_fixture(mode='cap',fixed=True):
    raw=(ROOT/CONTROL).read_bytes();assert digest(raw)==CONTROL_SHA
    steps=json.loads(raw)['steps'];count={'nostart':0,'pending':0,'complete':1,'positive':4,'cap':16,'zero':4}[mode]
    used=steps[:count];profiles={}
    for points in [OLD]+[s['points'] for s in used]:
        points=normalized(points)
        if points not in profiles:profiles[points]=chain.geometry(points,4,lambda:None)
    if fixed:
        for points,p in profiles.items():
            p['U']+=56
            p['state_hash']=adapter.STATE if points==OLD else digest(pack({'declared_fixed64_control':points}))
            p['orders']['sha256']=chain.hashed({'state_hash':p['state_hash'],'policy':chain.POLICY,'blocks':p['orders']['blocks']})
        if mode=='zero':profiles[normalized(used[-1]['points'])]['U']=0
    n=75 if fixed else 4
    current=deepcopy(profiles[OLD]);origin=current['state_hash'];initial_order=current['orders']['sha256']
    counts=dict.fromkeys(chain.COUNTERS,0);cursor=0;records=[];refs=[];blobs={};last_charge=None
    def save(name,value):
        raw=pack(value);blobs[name]=raw;return {'path':name,'sha256':digest(raw),'bytes':len(raw)}
    for step in used:
        rows=current['orders']['blocks'][cursor][:3];assert rows==step['rows']
        counts['started']+=1;last_charge=dict(counts);seq=counts['started']
        after=deepcopy(profiles[normalized(step['points'])]);accepted=step['strict'];score=after['U']
        minimum=[score]+deepcopy(step['item'][1:]);domains=deepcopy(step['domains'])
        record={'seq':seq,'rows':rows,'state_hash':current['state_hash'],'order_hash':current['orders']['sha256'],
            'cursor':cursor,'outcome':'accepted' if accepted else 'complete','before_score':current['U'],
            'minimum':minimum,'optimum_established':True,'enumeration_exhausted':True,'domains':domains,'after_hash':after['state_hash']}
        records.append(record);counts['completed']+=1
        if accepted:
            counts['accepted']+=1
            move={'schema':'restricted-three-row-move-v1','n':n,'points':[list(p) for p in after['points']],
                'score':score,'before_score':current['U'],'before_hash':current['state_hash'],'state_hash':after['state_hash'],
                'generation':counts['accepted'],'attempt':seq,'rows':rows,'minimum':minimum,'domains':domains,
                'counters':dict(counts),'old_order_hash':current['orders']['sha256'],'old_cursor':cursor,
                'optimum_established':True,'enumeration_exhausted':True}
            refs.append(save(f'move-{counts["accepted"]:03d}.json',move));current=after;cursor=0
        else:cursor+=1
    pending=None;status='block_cap' if mode=='cap' else ('zero' if mode=='zero' else 'search_deadline')
    if mode=='pending':
        counts['started']+=1;last_charge=dict(counts);pending=1
        records.append({'seq':1,'rows':current['orders']['blocks'][0][:3],'state_hash':current['state_hash'],
            'order_hash':current['orders']['sha256'],'cursor':0,'outcome':'pending','before_score':current['U']})
    witness=None
    if mode=='zero':
        assert fixed,'zero endpoint is explicitly declared only'
        witness=save('witness.json',{'certificate':{'n':n,'points':current['points'],'claimed_conflict_count':0}})
    orders=None if records and records[-1]['outcome']=='accepted' else deepcopy(current['orders'])
    authority={'schema':'restricted-three-row-authority-v1','policy':chain.POLICY,'n':n,'points':current['points'],
        'U':current['U'],'state_hash':current['state_hash'],'origin_hash':origin,'generation':counts['accepted'],
        'counters':counts,'start_cap':16,'orders':orders,'cursor':cursor,'pending':pending,'attempts':records,
        'artifacts':refs,'witness':witness,'status':status}
    initial={'n':n,'points':OLD,'score':profiles[OLD]['U'],'state_hash':origin,'counters':dict.fromkeys(chain.COUNTERS,0),
        'order_sha256':initial_order,'handoff':deepcopy(adapter.HANDOFF) if fixed else {'synthetic_n4':True}}
    return {'authority':authority,'initial':initial,'blobs':blobs,'profiles':profiles,'last_charge':last_charge,'fixed':fixed}


def wrapped(a):return pack({'payload':a,'payload_sha256':chain.hashed(a)})


@contextmanager
def geometry_spies(fixture):
    """Actual helper fold; declared n75 identity, scores, ranking and structure."""
    original=chain.points_checked;profiles=fixture['profiles'];calls=[]
    def points(values,n):
        assert n==75
        value=original(values,4);assert value in profiles,'unapproved coordinate fixture';return value
    def identity(n,values):assert n==75;return profiles[normalized(values)]['state_hash']
    def geometry(values,n,check):
        check();assert n==75;key=normalized(values);calls.append(key);return deepcopy(profiles[key])
    with patch.object(chain,'points_checked',points),patch.object(chain.common,'state_identity',identity),patch.object(chain,'geometry',geometry):
        yield calls


def fixture(mode='cap',manifest_count=297):
    f=chain_fixture(mode,True);a=f['authority'];initial=f['initial'];directory='synthetic-fixed64-run'
    paths={'report':directory+'/report.json','authority':directory+'/authority.json','initial':directory+'/initial.json',
           'manifest':'synthetic-fixed64-manifest.json','receipt':'synthetic-fixed64-owned.json'}
    artifacts={f'synthetic-closure/input-{i:02d}.json':digest(f'input-{i}'.encode()) for i in range(49)}
    artifacts['data/restricted-three-row75-source-pins.json']=adapter.PRIOR_MANIFEST
    artifacts['data/restricted-three-row75-independent-actual-v1-audit.json']=adapter.PRIOR_AUDIT
    metadata={'artifacts':artifacts};rawmeta=pack(metadata);assert len(rawmeta)<10249;rawmeta+=b' '*(10249-len(rawmeta))
    meta_sha=digest(rawmeta);handoff=deepcopy(adapter.HANDOFF);handoff['metadata_sha256']=meta_sha;initial['handoff']=deepcopy(handoff)
    runtime=str(Path(sys.executable).resolve());label=digest(b'synthetic-source-label')
    manifest={str((ROOT/name).resolve()):sha for name,sha in {**adapter.SOURCE_PINS,**artifacts}.items()}
    manifest[str((ROOT/adapter.HANDOFF_PATH).resolve())]=meta_sha
    manifest[runtime]=label;manifest[str(ROOT/'src/verify.py')]=label
    assert len(manifest)<=manifest_count
    for i in range(manifest_count-len(manifest)):manifest[str(ROOT/f'synthetic-pin-{i}')]=label
    manifest_raw=pack(manifest);manifest_sha=digest(manifest_raw);effective=dict(manifest);effective[str(ROOT/paths['manifest'])]=manifest_sha
    authority_raw=wrapped(a)
    report={'method':'fixed64_restricted_three_row75','accepted':True,'identity_valid':True,'closure':False,'authority_uncertain':False,
        'n':75,'k':149,'block_cap':16,'soft_seconds':25,'search_seconds':23,'authority_bytes':len(authority_raw),
        'authority_sha256':digest(authority_raw),'state':{k:deepcopy(a[k]) for k in ('n','U','state_hash','generation','counters','cursor','pending','status')},
        'attempts':deepcopy(a['attempts']),'artifacts':deepcopy(a['artifacts']),'order_sha256':None if a['orders'] is None else a['orders']['sha256'],
        'status':a['status'],'witness_saved':mode=='zero','authority_publications':2+a['counters']['started']+a['counters']['completed'],
        'work':{'indexes_started':1+a['counters']['accepted']},'handoff':deepcopy(handoff),'pins':deepcopy(effective),'elapsed_seconds':3.}
    if f['last_charge'] is not None:report['last_attempted_charge']=deepcopy(f['last_charge'])
    if a['witness'] is not None:report['witness']=deepcopy(a['witness'])
    receipt={'argv':[str(ROOT/'.venv/bin/python'),'research/restricted_three_row64.py','--seconds','25','--output-dir',directory,
        '--source-pins',paths['manifest']],'status':'completed','sources_unchanged':True,'source_manifest_sha256':manifest_sha,
        'sources_before':deepcopy(effective),'elapsed_seconds':5.,'gate':{'returncode':0,'seconds_limit':30,'rss_limit_mib':256,
        'peak_sampled_rss_kib':1024,'rss_samples':3,'cleanup_samples':1,'gate_status':'exited','cleanup_status':'clean',
        'cleanup_error':None,'monitor_error':None,'trigger_gate_status':None,'elapsed_seconds':4.,'cleanup_elapsed_seconds':.1}}
    f.update(paths=paths,directory=directory,metadata=metadata,metadata_raw=rawmeta,metadata_sha=meta_sha,handoff=handoff,
             manifest=manifest,report=report,receipt=receipt,runtime=runtime)
    reseal(f);return f


def reseal(f):
    """Rehash independent outer artifact bytes; never silently mirror semantic peers."""
    raw={k:pack(f[k]) for k in ('report','receipt','manifest','initial')};raw['authority']=wrapped(f['authority'])
    f['spec']={'schema':'fixed64-successful-run-audit-input-v1','manifest_entries':len(f['manifest']),
        'artifacts':{role:{'path':f['paths'][role],'sha256':digest(blob),'bytes':len(blob)} for role,blob in raw.items()}}
    f['files']={str(ROOT/f['paths'][role]):blob for role,blob in raw.items()}
    f['files'][str(ROOT/adapter.HANDOFF_PATH)]=f['metadata_raw']
    f['files'].update({str(ROOT/f['directory']/name):blob for name,blob in f['blobs'].items()})
    f['labels']=dict(f['manifest']);f['labels'].update({str(ROOT/name):sha for name,sha in adapter.HELPER_PINS.items()})
    f['labels'][adapter.__file__]=digest(Path(adapter.__file__).read_bytes())


class ClosedSource:
    def __init__(self,f,fail_read=None,drift=None):self.f=f;self.events=[];self.fail_read=fail_read;self.drift=drift;self.counts={}
    def read(self,name,expected,check,cap,length=None):
        check();key=str(name);assert key in self.f['files'],'unexpected read '+key;self.events.append(('read',key))
        if self.fail_read==key:raise OSError('injected closed read failure')
        raw=self.f['files'][key]
        assert len(raw)<=cap and (length is None or len(raw)==length),'closed byte length'
        if digest(raw)!=expected:raise ValueError('closed byte digest')
        return raw,adapter.decode(raw)
    def digest(self,name,check):
        check();key=str(name);self.events.append(('digest',key));self.counts[key]=self.counts.get(key,0)+1
        if self.drift==(key,self.counts[key]):return '0'*64
        if key in self.f['files']:return digest(self.f['files'][key])
        assert key in self.f['labels'],'unexpected digest '+key
        return self.f['labels'][key]


@contextmanager
def fixture_patches(f):
    with patch.object(adapter,'HANDOFF_SHA',f['metadata_sha']),patch.object(adapter,'HANDOFF',f['handoff']),geometry_spies(f) as calls:
        yield calls
