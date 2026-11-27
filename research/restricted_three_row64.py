"""One fixed audited64 allocation. SOURCE/TINY only until Root allocates actual.

No alternate input, historical recount, resume, fallback or automatic next run.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
ENGINE_SHA = 'd4d3a272ca8691c110b881ba739d31f95a858406c20e711ef588e712ebff794c'
ADAPTER_SHA = '0d5537eb46a898a84cb89ba4aceff2a817c122f8b5873492e5cce06e226ad50c'
CHAIN_SHA = '1c896c070f4892a977fcc639e6d1a13d6c436c3d87b07b8674d8edaa1a221a96'
COMMON_SHA = '4fc03f19b7f4e1323cff650615ad4cabca88ca6680450b1bbed080986ab7782a'
SOURCE_IDENTITIES = {'research/restricted_three_row75.py':ENGINE_SHA,
    'research/restricted_three_row_actual_chain_adapter.py':ADAPTER_SHA,
    'research/restricted_three_row_independent_chain_audit.py':CHAIN_SHA,
    'research/two_row_suffix_independent_authority_audit.py':COMMON_SHA,
    'research/two_row_descent75.py':'0211f6be4086d9a9835f6fa71dc6b0f6ded9aedf86dac1ebef8eacac74a5129c',
    'research/two_row_suffix75.py':'fe01dcecf582480754fc076a9a04a2f6d2a24d14d76bb55280f09f0db06cc9f1'}
for _name,_sha in SOURCE_IDENTITIES.items():
    if hashlib.sha256((ROOT/_name).read_bytes()).hexdigest() != _sha: raise ValueError('frozen source drift: '+_name)
from research import restricted_three_row75 as engine
from research import restricted_three_row_actual_chain_adapter as adapter

MiB = 1024*1024
HANDOFF_PATH = 'data/restricted-three-row64-input-identities.json'
HANDOFF_SHA = '2d6ba98abf571bc430f9a6e51a0dec5e99db68246e780ac24a5c8ba65b025ced'
HANDOFF_BYTES = 10249
FIXED_STATE = 'b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7'
PREDECESSOR = engine.FIXED_STATE
REPORT = adapter.REPORT
RECEIPT = adapter.RECEIPT
MANIFEST = adapter.MANIFEST
AUTHORITY = adapter.AUTHORITY
INITIAL = adapter.INITIAL
MOVE = 'data/restricted-three-row75-v1/move-001-attempt-016.json'
AUDIT = 'data/restricted-three-row75-independent-actual-v1-audit.json'
GUARD = 'data/restricted-three-row75-independent-actual-v1-owned-guard.json'
OLD_METADATA = engine.HANDOFF_PATH
SOURCE_REVIEW = 'research/restricted-three-row-independent-chain-audit-source-review.md'
AUDIT_SHA = 'ab302755266615a13423b81eb26c887af6a208d643ce1881a478fe5ee591450d'
GUARD_SHA = 'ab538127454ebe96430788d1f5fb2287636af436559522250cfd46aaa23fc5ac'
REVIEW_SHA = '2d830bf1f7fd45a1d96422700d5298493421d2dcf36e90b2b6bf598fa0fcebe9'
FINAL_COUNTS = {'started':16,'completed':16,'accepted':1}
LAST_CHARGE = {'started':16,'completed':15,'accepted':0}
OLD_ROLES = frozenset(['data/two-row-descent75-v1/'+name for name in
    ('report.json','completed-boundary.json','initial.json','best.json')]
    + [f'data/two-row-descent75-v1/improvement-{i:03d}.json' for i in range(1,29)]
    + ['data/experiments/shepherd-two-row-descent75-v1.json','data/two-row-descent75-source-pins.json',
       'data/two-row-descent75-independent-chain-actual-audit.json','data/two-row-descent75-independent-chain-actual-owned-guard.json',
       'research/two_row_descent75_actual_chain_adapter.py','research/two_row_descent_independent_chain_audit.py',
       'research/two-row-descent75-independent-actual-acceptance-review.md'])
NEW_ROLES = frozenset((REPORT,RECEIPT,MANIFEST,AUTHORITY,INITIAL,MOVE,AUDIT,GUARD,OLD_METADATA,
    'research/restricted-three-row-independent-actual-audit-preparation-addendum.md',SOURCE_REVIEW,
    'research/restricted-three-row75-independent-actual-v1-metadata-review.md'))
ROLES = OLD_ROLES | NEW_ROLES
compact = engine.compact
hashed = engine.hashed
clone = engine.clone
digest = engine.digest
SearchStop = engine.SearchStop
json_file = engine.json_file
validate_points = engine.kernel.validate_points
normalized_sha256 = engine.kernel.normalized_sha256
validate_authority = engine.validate_authority
historical_associate = engine.shared.authenticate_chain
run_associate = adapter.associated
norm_pins = engine.kernel.norm_pins
new_authority = engine.new_authority
build = engine.build
drive = engine.drive
FileStore = engine.FileStore
preserve_zero = engine.preserve_zero


def require(condition, message):
    if not condition: raise ValueError(message)


def same(left,right): return compact(left) == compact(right)


def decode_json(raw):
    def pairs(items):
        value = {}
        for key,item in items:
            if key in value: raise ValueError('duplicate JSON key')
            value[key] = item
        return value
    def bad(value): raise ValueError('nonfinite JSON token')
    return json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=bad)


def validate_metadata(meta):
    fields = {'artifact_byte_sizes','artifact_count','artifacts','inherited_artifact_count','n','normalized_sha256',
              'point_count','predecessor_normalized_sha256','schema','scope','unweighted_score'}
    require(type(meta) is dict and set(meta) == fields,'metadata schema')
    require(meta['schema'] == 'restricted-three-row-fixed64-handoff-identities-v1','metadata schema identity')
    for name,value in (('n',75),('point_count',149),('unweighted_score',64),('artifact_count',51),('inherited_artifact_count',39)):
        require(type(meta[name]) is int and meta[name] == value,'metadata integer '+name)
    require(meta['normalized_sha256'] == FIXED_STATE and meta['predecessor_normalized_sha256'] == PREDECESSOR,'metadata state identity')
    ids = meta['artifacts']; sizes = meta['artifact_byte_sizes']
    require(type(ids) is dict and type(sizes) is dict and set(ids) == set(sizes) == ROLES,'exact51 role set')
    normalized = set()
    for name,sha in ids.items():
        require(type(name) is str and not Path(name).is_absolute() and name == Path(name).as_posix()
                and '..' not in Path(name).parts,'artifact relative path')
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT.resolve()) and path not in normalized and path != (ROOT/HANDOFF_PATH).resolve(),'artifact alias/escape/self')
        normalized.add(path)
        require(type(sha) is str and len(sha) == 64 and all(c in '0123456789abcdef' for c in sha),'artifact digest')
        require(type(sizes[name]) is int and 0 < sizes[name] <= 68150,'artifact size cap')
    require(sum(sizes.values()) == 355145 and max(sizes.values()) == 68150,'aggregate input cap')
    require(sum(sizes[k] for k in ROLES if k.endswith('.json')) == 311970,'JSON aggregate cap')
    require(type(meta['scope']) is str and len(meta['scope']) <= 1024,'metadata scope cap')
    return meta


def parse_metadata(raw, expected_sha=None):
    """Pure synthetic seam; fixed load_handoff never overrides the identity."""
    require(type(raw) is bytes and len(raw) == HANDOFF_BYTES,'metadata byte size')
    require(hashlib.sha256(raw).hexdigest() == (HANDOFF_SHA if expected_sha is None else expected_sha),'metadata byte identity')
    return validate_metadata(decode_json(raw))


class GraphBudget:
    GRAPH_CAP = 16*MiB
    AUX_CAP = 16*MiB
    NODE_CAP = 100000
    DEPTH_CAP = 64
    def check(self,*roots,reserve=0):
        seen = set(); stack = [(value,0) for value in roots]; count = size = seen_bytes = 0
        while stack:
            aux = sys.getsizeof(seen)+seen_bytes+sys.getsizeof(stack)+len(stack)*sys.getsizeof((None,0))+256
            require(aux <= self.AUX_CAP,'graph walker auxiliary cap')
            value,depth = stack.pop(); require(depth <= self.DEPTH_CAP,'JSON depth cap')
            identity = id(value)
            if identity in seen: continue
            seen.add(identity); seen_bytes += sys.getsizeof(identity); count += 1; size += sys.getsizeof(value)
            require(count <= self.NODE_CAP and size+reserve <= self.GRAPH_CAP,'retained JSON graph cap')
            if type(value) is dict:
                for key,item in value.items(): stack.append((key,depth+1)); stack.append((item,depth+1))
            elif type(value) in (list,tuple):
                for item in value: stack.append((item,depth+1))
            elif type(value) not in (str,int,float,bool,type(None)): raise ValueError('non-JSON graph value')
        return {'bytes':size,'nodes':count}


class DiskSource:
    def __init__(self,root,check): self.root=Path(root); self.check=check
    def scan(self,name,size,sha):
        self.check(); path=self.root/name
        require(path.stat().st_size == size,'input size before streaming')
        require(digest(path,self.check) == sha and path.stat().st_size == size,'streamed input identity/size')
    def read(self,name,size,sha):
        self.check();path=self.root/name
        require(path.stat().st_size == size,'input size before decode')
        raw=path.read_bytes()
        require(len(raw) == size and path.stat().st_size == size and hashlib.sha256(raw).hexdigest() == sha,'decoded bytes identity/size')
        self.check();return raw


def checked_pins(pins):
    normalized=norm_pins(pins)
    require(all(len(name) <= 1024 for name in normalized),'pin path length')
    return normalized


def associate_documents(docs,metadata,pins,authority_raw,check=lambda:None,runtime=None):
    """Semantic association only; no independent recount/old loader entrypoint."""
    validate_metadata(metadata);pins=checked_pins(pins)
    require(set(docs) == {p for p in ROLES if p.endswith('.json')},'exact45 parsed JSON roles')
    require(all(pins.get(str((ROOT/name).resolve())) == sha for name,sha in metadata['artifacts'].items()),'all51 input pins')
    require(pins.get(str((ROOT/HANDOFF_PATH).resolve())) == HANDOFF_SHA,'fixed64 metadata pin')
    for name,sha in SOURCE_IDENTITIES.items(): require(pins.get(str((ROOT/name).resolve())) == sha,'mandatory source pin')
    runtime = str(Path(sys.executable).resolve()) if runtime is None else runtime
    require(runtime in pins and str((ROOT/'src/verify.py').resolve()) in pins,'runtime/verifier pin')
    budget=GraphBudget()
    # Pure frozen helpers create bounded normalized pin maps/canonical bytes.
    # Reserve 2MiB within the 16MiB graph ceiling for their temporary copies;
    # fixed inputs total only311,970 JSON bytes and normalized paths are capped.
    budget.check(docs,metadata,pins,reserve=2*MiB)
    old=docs[OLD_METADATA]
    require(type(old) is dict and type(old.get('artifacts')) is dict and set(old['artifacts']) == OLD_ROLES,'inherited39 roles')
    require(all(metadata['artifacts'][k] == v for k,v in old['artifacts'].items()),'inherited39 digest equality')
    check();old_points=historical_associate(docs,old,pins,check)
    initial=docs[INITIAL]
    require(type(initial) is dict and set(initial) == {'n','points','score','state_hash','counters','order_sha256','handoff'},'initial seven-key schema')
    require(type(initial['n']) is int and initial['n'] == 75 and type(initial['score']) is int and initial['score'] == 65,'initial n/score')
    require(validate_points(initial['points'],75) == old_points and initial['state_hash'] == PREDECESSOR,'initial old65 points/identity')
    require(same(initial['counters'],{'started':0,'completed':0,'accepted':0}),'initial fresh counters')
    wrapped=docs[AUTHORITY]
    require(type(authority_raw) is bytes and len(authority_raw) == metadata['artifact_byte_sizes'][AUTHORITY]
            and hashlib.sha256(authority_raw).hexdigest() == metadata['artifacts'][AUTHORITY],'authority raw identity')
    require(type(wrapped) is dict and set(wrapped) == {'payload','payload_sha256'} and wrapped['payload_sha256'] == hashed(wrapped['payload']),'authority envelope')
    a=validate_authority(wrapped['payload'])
    require(a['n'] == 75 and a['origin_hash'] == PREDECESSOR and a['state_hash'] == FIXED_STATE and a['U'] == 64
            and same(a['counters'],FINAL_COUNTS) and a['generation'] == 1 and a['cursor'] == 0 and a['orders'] is None
            and a['pending'] is None and a['status'] == 'block_cap' and a['witness'] is None,'fixed final authority')
    require(len(a['attempts']) == 16 and len(a['artifacts']) == 1,'fixed ledger/reference counts')
    old_order=initial['order_sha256']
    require(type(old_order) is str and len(old_order) == 64 and all(c in '0123456789abcdef' for c in old_order),'initial order digest schema')
    for seq,r in enumerate(a['attempts'],1):
        require(type(r['seq']) is int and r['seq'] == seq and r['order_hash'] == old_order
                and r['state_hash'] == PREDECESSOR and r['before_score'] == 65 and r['cursor'] == seq-1
                and r['outcome'] == ('accepted' if seq == 16 else 'complete')
                and r['minimum'][0] == (64 if seq == 16 else 65),'fixed old-state ledger')
        require(sum(map(len,r['minimum'][1:])) == sum(y in r['rows'] for x,y in old_points),'old selected load')
        for row,domain,cols in zip(r['rows'],r['domains'],r['minimum'][1:]):
            require({x for x,y in old_points if y == row} <= set(domain),'old current-inclusive domain')
            require(all(type(x) is int for x in cols),'strict selected column integers')
    last=a['attempts'][-1]
    require(initial['order_sha256'] == a['attempts'][0]['order_hash'],'initial first-order binding')
    ref=a['artifacts'][0]
    require(same(ref,{'path':Path(MOVE).name,'sha256':metadata['artifacts'][MOVE],'bytes':metadata['artifact_byte_sizes'][MOVE]}),'sole move reference')
    move=docs[MOVE];points=validate_points(move.get('points'),75)
    require(normalized_sha256(75,points) == FIXED_STATE and validate_points(a['points'],75) == points,'detached64 identity')
    rows=last['rows']
    require(tuple(p for p in points if p[1] not in rows) == tuple(p for p in old_points if p[1] not in rows),'move unselected support')
    require(tuple(tuple(x for x,y in points if y == row) for row in rows) == tuple(tuple(c) for c in last['minimum'][1:]),'move selected columns')
    expected_move={'schema':'restricted-three-row-move-v1','n':75,'points':points,'score':64,'before_score':65,
        'before_hash':PREDECESSOR,'state_hash':FIXED_STATE,'generation':1,'attempt':16,'rows':rows,'minimum':last['minimum'],
        'domains':last['domains'],'counters':FINAL_COUNTS,'old_order_hash':last['order_hash'],'old_cursor':15,
        'optimum_established':True,'enumeration_exhausted':True}
    require(same(move,expected_move),'exact accepted move/event association')
    audit=docs[AUDIT];chain=audit.get('chain',{})
    require(audit.get('accepted') is True and type(audit.get('manifest_entries')) is int and audit['manifest_entries'] == 228
            and type(audit.get('effective_pins')) is int and audit['effective_pins'] == 229,'accepted audit/pin counts')
    require(audit.get('audit_source_sha256') == ADAPTER_SHA and audit.get('helper_sha256') == CHAIN_SHA
            and audit.get('common_helper_sha256') == COMMON_SHA and audit.get('runtime_path') == runtime
            and audit.get('runtime_sha256') == pins[runtime],'audit source/runtime')
    require(same(audit.get('artifact_hashes'),{k:metadata['artifacts'][k] for k in (REPORT,RECEIPT,MANIFEST,AUTHORITY,INITIAL,MOVE)}),'six audited artifact identities')
    values={'authority_chain_passed':True,'receipt_acceptance_checked':False,'unique_states_recounted':2,'accepted_scores':[65,64],
        'accepted_state_hashes':[PREDECESSOR,FIXED_STATE],'new_accepted_moves':1,'counters':FINAL_COUNTS,'last_start_charge':LAST_CHARGE,
        'pending_attempt':None,'cursor':0,'durable_status':'block_cap','durable_U':64,'durable_state_hash':FIXED_STATE,
        'recorded_nonimprovements_not_independent_minima':15,'side_outputs':[]}
    require(all(k in chain and same(chain[k],v) for k,v in values.items()),'accepted audit chain contract')
    expected_observations=[{k:r[k] for k in ('seq','state_hash','rows','cursor','outcome')} for r in a['attempts']]
    require(same(chain.get('observations'),expected_observations),'audit ledger observations')
    check()
    effective,resources,count=run_associate(docs[REPORT],docs[RECEIPT],docs[MANIFEST],a,initial,metadata['artifacts'],authority_raw,chain,runtime)
    require(count == 228 and len(effective) == 229 and all(pins.get(k) == v for k,v in effective.items()),'prior229 effective source closure')
    require(same(audit.get('resources'),resources),'audit original resources')
    guard=docs[GUARD]
    engine.kernel.clean_guard(guard,30)
    require(guard.get('status') == 'completed' and guard.get('argv') == [str(ROOT/'.venv/bin/python'),
        'research/restricted_three_row_actual_chain_adapter.py','--seconds','25','--output',AUDIT],'flat audit guard status/argv')
    require(guard.get('audit_output_sha256') == metadata['artifacts'][AUDIT] == AUDIT_SHA
            and metadata['artifacts'][GUARD] == GUARD_SHA,'audit guard output identity')
    source_roles={SOURCE_REVIEW:REVIEW_SHA,'research/restricted_three_row_actual_chain_adapter.py':ADAPTER_SHA,
        'research/restricted_three_row_independent_chain_audit.py':CHAIN_SHA,'research/two_row_suffix_independent_authority_audit.py':COMMON_SHA}
    guard_pins=checked_pins(guard.get('source_pins'))
    require(guard_pins == checked_pins(source_roles) and all(pins.get(k) == v for k,v in guard_pins.items()),'four audit guard source roles')
    for name in ('elapsed_seconds','cleanup_elapsed_seconds'):
        require(type(guard.get(name)) in (int,float) and math.isfinite(guard[name]) and 0 <= guard[name] < 30,'audit guard time')
    elapsed=audit.get('elapsed_seconds')
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0 <= elapsed < 25 and elapsed <= guard['elapsed_seconds'],'audit elapsed interval')
    check()
    # No container from docs is returned. Strings/ints are immutable scalars;
    # coordinate tuples are rebuilt even if a validator supplied tuples.
    detached=tuple(tuple(int(v) for v in point) for point in points)
    info={'metadata_sha256':HANDOFF_SHA,'normalized_sha256':FIXED_STATE,'score':64,'predecessor_normalized_sha256':PREDECESSOR,
          'artifact_count':51,'prior_manifest_sha256':metadata['artifacts'][MANIFEST],'prior_audit_sha256':metadata['artifacts'][AUDIT],
          'historical_counters':dict(FINAL_COUNTS),'coverage_basis':'historical_execution_not_new_state_coverage'}
    require(GraphBudget().check(detached)['bytes'] <= 32768 and len(compact(info)) <= 4096,'detached handoff cap')
    return detached,info


def association_frame(pins,check,source=None):
    """All temporary parsed/history owners end before this function returns."""
    source=DiskSource(ROOT,check) if source is None else source
    raw=source.read(HANDOFF_PATH,HANDOFF_BYTES,HANDOFF_SHA);metadata=parse_metadata(raw);del raw
    pins=checked_pins(pins);budget=GraphBudget();docs={};authority_raw=None
    budget.check(metadata,pins,docs)
    for name in sorted(ROLES):
        check();source.scan(name,metadata['artifact_byte_sizes'][name],metadata['artifacts'][name])
    for name in sorted(k for k in ROLES if k.endswith('.json')):
        check();raw=source.read(name,metadata['artifact_byte_sizes'][name],metadata['artifacts'][name])
        docs[name]=decode_json(raw)
        if name == AUTHORITY: authority_raw=raw
        del raw
        budget.check(metadata,pins,docs)
    return associate_documents(docs,metadata,pins,authority_raw,check)


def load_handoff(pins,check): return association_frame(pins,check)


def run(out,manifest,seconds=25,*,started=None,clock=time.monotonic):
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 2 < seconds <= 25: raise ValueError('duration')
    start=clock() if started is None else started;soft=start+seconds;search=soft-2
    def final_check():
        if clock() >= soft: raise TimeoutError('main soft deadline')
    def search_check():
        if clock() >= search: raise SearchStop('search_deadline')
    out=Path(out);store=FileStore(out);pins={};ready=False;result=None;input_info=None
    report={'method':'fixed64_restricted_three_row75','accepted':False,'identity_valid':False,'closure':False,
        'n':75,'k':149,'status':'incomplete','soft_seconds':seconds,'search_seconds':seconds-2,'block_cap':16,
        'witness_saved':False,'work':{},'scope':'One immutable64 induced-three-row four-column allocation; no automatic continuation.'}
    def verify_pins():
        for name,sha in pins.items():
            if digest(name,final_check) != sha: raise ValueError('pin drift: '+name)
    def save_zero(points): return preserve_zero(points,75,out,final_check,report)
    try:
        final_check();path=Path(manifest).resolve()
        require(path.stat().st_size <= 128*1024,'manifest byte cap')
        raw=path.read_bytes();manifest_sha=hashlib.sha256(raw).hexdigest();decoded=decode_json(raw)
        pins=checked_pins(decoded);GraphBudget().check(decoded,pins);del raw,decoded
        required={str(Path(__file__).resolve()),str(ROOT/'src/verify.py'),str(Path(sys.executable).resolve()),str(ROOT/HANDOFF_PATH)}
        require(required <= pins.keys() and pins[str(ROOT/HANDOFF_PATH)] == HANDOFF_SHA,'mandatory wrapper/input/runtime pins')
        require(all(pins.get(str(ROOT/name)) == sha for name,sha in SOURCE_IDENTITIES.items()),'frozen source closure')
        require(str(path) not in pins,'manifest self entry');pins[str(path)]=manifest_sha
        verify_pins();ready=True
        points,input_info=load_handoff(pins,final_check)
        # The association frame has ended. No historical graph is live here.
        validation=engine.kernel.dual_validate(points,75,64,final_check)
        require(validation['validators'][0]['normalized_sha256'] == FIXED_STATE,'fresh64 validation identity')
        del validation
        initial_state=[build(points,75,search_check,report['work'])]
        require(initial_state[0][2] == 64 and normalized_sha256(75,initial_state[0][0]) == FIXED_STATE,'initial64 index identity/score')
        a=new_authority(points,75,prepared=initial_state[0],check=search_check,work=report['work'])
        final_check();store.publish(a,'initialize')
        json_file(out/'initial.json',{'n':75,'points':points,'score':64,'state_hash':FIXED_STATE,'counters':a['counters'],
            'order_sha256':a['orders']['sha256'],'handoff':input_info},cap=16384,immutable=True)
        result=drive(a,check=search_check,publish=store.publish,save_move=store.save_move,save_zero=save_zero,
            prepared=initial_state.pop(),work=report['work'])
        report['status']=result['status']
        if result['error']: report['search_error']=result['error']
        if result.get('attempted_charge'): report['last_attempted_charge']=result['attempted_charge']
        if not store.uncertain:
            final=clone(result['authority']);final['status']=result['status'];store.publish(final,'final_stop')
    except Exception as exc: report.update(status='error',error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(authority_publications=store.publications,authority_uncertain=store.uncertain)
    if store.last_durable is not None:
        a=store.last_durable
        report['state']={k:a[k] for k in ('n','U','state_hash','generation','counters','cursor','pending','status')}
        report.update(artifacts=a['artifacts'],attempts=a['attempts'],order_sha256=None if a['orders'] is None else a['orders']['sha256'])
        try:
            report['authority_sha256']=digest(out/'authority.json',final_check);report['authority_bytes']=(out/'authority.json').stat().st_size
        except Exception as exc: report['authority_identity_error']=f'{type(exc).__name__}: {str(exc)[:1000]}'
    try:
        require(ready and store.last_durable is not None and not store.uncertain,'no unambiguous durable authority')
        verify_pins();final_check();report['identity_valid']=True
        errors=any(k == 'error' or k.endswith('_error') for k in report)
        report['accepted']=(report['status'] in ('block_cap','restricted_candidate_list_exhausted','search_deadline','zero') and not errors
            and report['work'].get('indexes_started',0) <= 17 and (store.last_durable['U'] > 0 or report['witness_saved'])
            and (result is None or result.get('attempted_charge') is None or all(store.last_durable['counters'][k] >= result['attempted_charge'][k]
                for k in ('started','completed','accepted')))
            and (not report['witness_saved'] or store.last_durable['U'] == 0 and store.last_durable['witness'] == report.get('witness')))
    except Exception as exc: report.update(accepted=False,identity_valid=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}')
    report.update(pins=pins,handoff=input_info,elapsed_seconds=clock()-start)
    try: json_file(out/'report.json',report);final_check()
    except Exception as exc:
        report.update(accepted=False,final_error=f'{type(exc).__name__}: {str(exc)[:1000]}',elapsed_seconds=clock()-start)
        json_file(out/'report.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--source-pins',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    report=run(args.output_dir,args.source_pins,args.seconds,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('status','accepted','witness_saved','state','authority_publications','elapsed_seconds')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__ == '__main__': sys.exit(main())
