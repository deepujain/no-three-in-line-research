"""Bounded, durable batches of exact corner-anchor repair frontiers.

The source is independently validated once per invocation. Prepared geometry is
then reused by every anchor; running source modules are never edited or patched.
Per-anchor records retain the embedding_worker stream schema and hash chains.
Counts sum overlapping anchor streams and do not count unique deletion sets.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
BATCH_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
sys.path.insert(0,str(ROOT))
from research.embedding_audit import gap_blockers, insert_grid_lines, validate_repair_source
from research.embedding_worker import atomic_json, read_json, resolve_reference
from src.verify import verify_certificate, verify_certificate_bruteforce

ORDER = 'lexicographic itertools.combinations of increasing non-base source indices'


class ChunkTimeout(Exception):
    pass


def _deadline(deadline):
    if time.monotonic() >= deadline:
        raise ChunkTimeout


@contextmanager
def _lock(path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(str(path)+'.lock','a') as stream:
        try:
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f'another worker holds {path.name}') from exc
        yield


def prepare_context(seed,scan,manifest):
    """One source validation; no deletion or addition cases are evaluated."""
    digest=validate_repair_source(seed,scan)
    ordered=hashlib.sha256(json.dumps({'n':seed['n'],'points':seed['points']},
                                    sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if (manifest.get('kind')!='corner_endpoint_cover_antichain' or manifest.get('cut')!=[0,0]
            or manifest.get('translation')!=[1,1]
            or manifest.get('source_normalized_sha256')!=digest
            or manifest.get('source_order_sha256')!=ordered):
        raise ValueError('manifest mapping or source provenance mismatch')
    points=insert_grid_lines(seed['points'],seed['n'],0,0)
    deletion_count=manifest.get('exact_deletion_count')
    if type(deletion_count) is not int or not 0<=deletion_count<=len(points):
        raise ValueError('invalid manifest deletion count')
    if manifest.get('n')!=seed['n']+1 or manifest.get('seed_point_count')!=len(points):
        raise ValueError('manifest grid or source size mismatch')
    identifiers=set()
    for anchor in manifest.get('anchors',[]):
        base=anchor.get('base_deletion_indices')
        name=anchor.get('id')
        if not isinstance(name,str) or not name or Path(name).name!=name or name in identifiers:
            raise ValueError('invalid or duplicate anchor identifier')
        identifiers.add(name)
        if (not isinstance(base,list) or any(type(i) is not int or not 0<=i<len(points) for i in base)
                or base!=sorted(set(base)) or len(base)>deletion_count):
            raise ValueError('invalid anchor base')
        expected=math.comb(len(points)-len(base),deletion_count-len(base))
        if type(anchor.get('total_deletion_sets')) is not int or anchor['total_deletion_sets']!=expected:
            raise ValueError('anchor frontier size mismatch')
    if not identifiers:
        raise ValueError('manifest contains no anchors')
    return {'points':points,'n':seed['n']+1,'source_normalized_sha256':digest,
            'source_order_sha256':ordered,'deletion_count':deletion_count}


def _empty_record(context,anchor,start_offset,max_cases,seconds):
    return {'audit':'streamed_single_cover_exact_deletion_repair',
            'source_normalized_sha256':context['source_normalized_sha256'],
            'source_order_sha256':context['source_order_sha256'],'cut':[0,0],
            'base_deletion_indices':anchor['base_deletion_indices'],
            'base_is_unique_minimal_cover_through_budget':not anchor['base_deletion_indices'],
            'exact_deletion_count':context['deletion_count'],
            'total_deletion_sets':anchor['total_deletion_sets'],'enumeration_order':ORDER,
            'start_offset':start_offset,'next_offset':start_offset,'completed_deletion_sets':0,
            'max_cases':max_cases,'seconds_budget':seconds,'status':'incomplete',
            'tested_addition_subsets':{str(len(context['points'])+g):0 for g in (1,2)},
            'valid_addition_subsets':{str(len(context['points'])+g):0 for g in (1,2)},
            'max_individually_addable_pool':0,'found_certificates':[]}


def stream_prepared(context,anchor,start_offset,max_cases,seconds,on_certificate=None):
    """Exact stream_cover_repairs algorithm with a prevalidated source context.

    The corner is a translation of the validated source, hence every retained
    subset is valid. Only fully completed deletion cases advance the offset.
    """
    if any(type(v) is not int or v<0 for v in (start_offset,max_cases)) or start_offset>anchor['total_deletion_sets']:
        raise ValueError('invalid stream offset/case bound')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('seconds must be finite and nonnegative')
    started=time.monotonic();deadline=started+seconds
    result=_empty_record(context,anchor,start_offset,max_cases,seconds)
    points=context['points'];n=context['n'];count=context['deletion_count']
    base=set(anchor['base_deletion_indices'])
    optional=[i for i in range(len(points)) if i not in base]
    found_sizes=set()
    def collinear(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])==(b[1]-a[1])*(c[0]-a[0])
    try:
        choices=itertools.islice(itertools.combinations(optional,count-len(base)),start_offset,None)
        for extras in choices:
            if result['completed_deletion_sets']>=max_cases:
                result['status']='case_limit_incomplete';break
            _deadline(deadline)
            deleted=base|set(extras)
            retained=[p for i,p in enumerate(points) if i not in deleted]
            occupied=set(retained);columns=[0]*n;rows=[0]*n
            for x,y in retained:columns[x]+=1;rows[y]+=1
            pool=[]
            for p in itertools.product([x for x in range(n) if columns[x]<2],
                                       [y for y in range(n) if rows[y]<2]):
                _deadline(deadline)
                if p not in occupied and not gap_blockers(retained,p):pool.append(p)
            result['max_individually_addable_pool']=max(result['max_individually_addable_pool'],len(pool))
            pair_ok={}
            for a,b in itertools.combinations(pool,2):
                _deadline(deadline)
                pair_ok[a,b]=not any(collinear(a,b,c) for c in retained)
            local_tested={str(len(points)+g):0 for g in (1,2)}
            local_valid={str(len(points)+g):0 for g in (1,2)}
            for gain in (1,2):
                target=str(len(points)+gain)
                for additions in itertools.combinations(pool,count+gain):
                    _deadline(deadline);local_tested[target]+=1
                    if any(not pair_ok[a,b] for a,b in itertools.combinations(additions,2)):continue
                    if any(collinear(a,b,c) for a,b,c in itertools.combinations(additions,3)):continue
                    local_valid[target]+=1
                    if target not in found_sizes:
                        certificate={'n':n,'points':[list(p) for p in retained+list(additions)],
                                     'metadata':{'method':'streamed_embedding_cover_repair','cut':[0,0],
                                                 'deleted_embedding_indices':sorted(deleted),'novelty_claim':False}}
                        checks=[verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
                        if not all(check['valid'] for check in checks):raise RuntimeError('prepared stream certificate failed independent checks')
                        certificate['metadata']['normalized_sha256']=checks[0]['normalized_sha256']
                        result['found_certificates'].append(certificate);found_sizes.add(target)
                        if on_certificate:on_certificate(certificate)
            for target in local_tested:
                result['tested_addition_subsets'][target]+=local_tested[target]
                result['valid_addition_subsets'][target]+=local_valid[target]
            result['completed_deletion_sets']+=1;result['next_offset']+=1
        else:result['status']='complete'
    except ChunkTimeout:result['status']='timeout_incomplete'
    result['elapsed_seconds']=time.monotonic()-started
    return result


def _load_chain(previous,context,anchor,manifest_hash):
    """Existing stream integrity contract, using cached validated source hashes."""
    path=Path(previous).resolve();record,digest=read_json(path)
    if record.get('kind')=='embedding_stream_tip':
        reference=record['record'];path=resolve_reference(reference,path).resolve()
        record,digest=read_json(path)
        if digest!=reference['sha256']:raise ValueError('tip record hash mismatch')
    latest=(path,record,digest);seen=set()
    while True:
        if path in seen:raise ValueError('cycle in stream chain')
        seen.add(path)
        expected={'audit':'streamed_single_cover_exact_deletion_repair','cut':[0,0],
                  'source_normalized_sha256':context['source_normalized_sha256'],
                  'source_order_sha256':context['source_order_sha256'],
                  'base_deletion_indices':anchor['base_deletion_indices'],
                  'exact_deletion_count':context['deletion_count'],
                  'total_deletion_sets':anchor['total_deletion_sets'],'enumeration_order':ORDER}
        if any(record.get(key)!=value for key,value in expected.items()):raise ValueError('stream identity/source mismatch')
        if record.get('manifest_sha256',manifest_hash)!=manifest_hash:raise ValueError('stream manifest mismatch')
        start,end,total,completed=(record.get(key) for key in ('start_offset','next_offset','total_deletion_sets','completed_deletion_sets'))
        if any(type(v) is not int for v in (start,end,total,completed)) or not 0<=start<=end<=total or completed!=end-start:
            raise ValueError('invalid stream offsets')
        if record.get('status') not in ('complete','case_limit_incomplete','timeout_incomplete') or (record['status']=='complete' and end!=total):
            raise ValueError('invalid stream status')
        parent=record.get('previous_record')
        if parent is None:
            if start!=0:raise ValueError('stream has no zero-offset origin')
            break
        previous_path=resolve_reference(parent,path).resolve();previous_record,previous_hash=read_json(previous_path)
        if previous_hash!=parent['sha256'] or previous_record.get('next_offset')!=start:raise ValueError('stream parent hash/gap mismatch')
        path,record,digest=previous_path,previous_record,previous_hash
    return latest


def _publish_tip(path,latest,anchor,manifest_hash):
    record_path,record,digest=latest
    atomic_json(path,{'kind':'embedding_stream_tip','record':{'path':str(record_path),'sha256':digest},
                     'cut':[0,0],'next_offset':record['next_offset'],'total_deletion_sets':record['total_deletion_sets'],
                     'coverage':{'start':0,'end':record['next_offset'],'gapless':True},
                     'frontier_complete':record['next_offset']==record['total_deletion_sets'],
                     'anchor_id':anchor['id'],'manifest_sha256':manifest_hash})


def run_batch(manifest_path,seed,scan,output,records_directory,seconds=900,max_cases=1000000,
              chunk_cases=20000,max_anchor_cases=None,start_anchor=0,stop_anchor=None):
    """One process, global budgets, bounded per-anchor working data and cursor.

    max_anchor_cases optionally selects small frontiers; unselected anchors are
    explicitly outside scope. Existing origins, running modules and other tips
    are untouched. Resume trusts local enumeration records, not numerical replay.
    """
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:raise ValueError('invalid seconds')
    if any(type(v) is not int or v<0 for v in (max_cases,chunk_cases,start_anchor)) or not chunk_cases:raise ValueError('invalid case/anchor bounds')
    if max_anchor_cases is not None and (type(max_anchor_cases) is not int or max_anchor_cases<0):raise ValueError('invalid max_anchor_cases')
    started=time.monotonic();deadline=started+seconds
    output=Path(output).resolve();records_directory=Path(records_directory).resolve()
    records_directory.mkdir(parents=True,exist_ok=True)
    manifest,manifest_hash=read_json(manifest_path)
    context=prepare_context(seed,scan,manifest)
    anchors=manifest['anchors'];stop_anchor=len(anchors) if stop_anchor is None else stop_anchor
    if type(stop_anchor) is not int or not start_anchor<=stop_anchor<=len(anchors):raise ValueError('invalid stop_anchor')
    selected=[i for i in range(start_anchor,stop_anchor) if max_anchor_cases is None or anchors[i]['total_deletion_sets']<=max_anchor_cases]
    selection_hash=hashlib.sha256(json.dumps(selected,separators=(',',':')).encode()).hexdigest()
    prefix=[0]
    for i in selected:prefix.append(prefix[-1]+anchors[i]['total_deletion_sets'])
    identity={'kind':'corner_anchor_batch_cursor_v1','manifest_sha256':manifest_hash,
              'batch_source_sha256':BATCH_SOURCE_SHA256,
              'source_normalized_sha256':context['source_normalized_sha256'],
              'source_order_sha256':context['source_order_sha256'],'selection_sha256':selection_hash,
              'start_anchor':start_anchor,'stop_anchor':stop_anchor,'max_anchor_cases':max_anchor_cases,
              'records_directory':str(records_directory)}
    with _lock(output):
        state=dict(identity,cursor=0,verified_witness_events=0,recent_witness_files=[])
        if output.exists():
            stored,_=read_json(output)
            if any(stored.get(key)!=value for key,value in identity.items()):raise ValueError('batch manifest/source/selection mismatch')
            state=stored
        cursor=state.get('cursor')
        if type(cursor) is not int or not 0<=cursor<=len(selected):raise ValueError('invalid batch cursor')
        # A changed cursor alone must never skip a partial/missing anchor.
        for ordinal in selected[:cursor]:
            anchor=anchors[ordinal];tip=records_directory/(anchor['id']+'-tip.json')
            latest=_load_chain(tip,context,anchor,manifest_hash)
            if latest[1]['next_offset']!=anchor['total_deletion_sets']:raise ValueError('batch cursor skips a partial anchor')
        completed_now=0;active_offset=0;status='partial'
        # Recover durable work before publishing, even with a zero new budget.
        # A tip may also have reached its end before a crash updated the cursor.
        while cursor<len(selected):
            anchor=anchors[selected[cursor]];tip=records_directory/(anchor['id']+'-tip.json')
            if not tip.exists():break
            with _lock(tip):latest=_load_chain(tip,context,anchor,manifest_hash)
            active_offset=latest[1]['next_offset']
            if active_offset!=anchor['total_deletion_sets']:break
            cursor+=1;active_offset=0

        def publish():
            state.update(identity,cursor=cursor,selected_anchor_count=len(selected),
                         selected_frontiers_complete=cursor==len(selected),
                         next_anchor_ordinal=None if cursor==len(selected) else selected[cursor],
                         completed_cases_sum=prefix[cursor]+active_offset,
                         total_selected_cases_sum=prefix[-1],completed_this_invocation=completed_now,
                         current_anchor_next_offset=active_offset,status='complete' if cursor==len(selected) else status,
                         seconds_budget=seconds,max_cases=max_cases,elapsed_seconds=time.monotonic()-started,
                         case_count_semantics='sum across overlapping selected anchor frontiers; not unique deletion sets',
                         distinct_deletion_sets=None,unselected_anchor_count=len(anchors)-len(selected),
                         scope='selected anchors only; partial or filtered batches do not close the full manifest family',
                         records_directory=str(records_directory),
                         source_validation_count_this_invocation=1,
                         resume_trust='local enumeration records are hash/identity/gap checked, not independently replayed')
            atomic_json(output,state)

        def found(certificate):
            checks=[verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
            if (not all(check['valid'] for check in checks) or certificate.get('n')!=context['n']
                    or len(certificate['points']) not in (len(context['points'])+1,len(context['points'])+2)):
                raise RuntimeError('refused invalid/out-of-scope batch witness')
            path=records_directory/('batch-witness-n'+str(context['n'])+'-'+checks[0]['normalized_sha256']+'.json')
            if path.exists():
                existing,_=read_json(path)
                audited=verify_certificate_bruteforce(existing)
                if not audited['valid'] or audited['normalized_sha256']!=checks[0]['normalized_sha256']:raise ValueError('existing witness file mismatch')
            else:atomic_json(path,certificate,immutable=True)
            state['verified_witness_events']+=1
            state['recent_witness_files']=(state['recent_witness_files']+[str(path)])[-16:]
            publish()  # Record the durable witness without advancing case coverage.
            print(json.dumps({'event':'verified_batch_witness_saved','path':str(path),'point_count':len(certificate['points'])}),flush=True)

        publish()
        while cursor<len(selected) and completed_now<max_cases and time.monotonic()<deadline:
            ordinal=selected[cursor];anchor=anchors[ordinal]
            tip=records_directory/(anchor['id']+'-tip.json')
            with _lock(tip):
                if tip.exists():latest=_load_chain(tip,context,anchor,manifest_hash)
                else:
                    origin_path=records_directory/(anchor['id']+'-origin.json')
                    if not origin_path.exists():
                        origin=_empty_record(context,anchor,0,0,0)
                        origin.update(status='case_limit_incomplete',elapsed_seconds=0.0,preparation_only=True,
                                      anchor_id=anchor['id'],manifest_sha256=manifest_hash,
                                      batch_source_sha256=BATCH_SOURCE_SHA256)
                        atomic_json(origin_path,origin,immutable=True)
                    latest=_load_chain(origin_path,context,anchor,manifest_hash)
                    _publish_tip(tip,latest,anchor,manifest_hash)
                active_offset=latest[1]['next_offset'];publish()
                while active_offset<anchor['total_deletion_sets'] and completed_now<max_cases and time.monotonic()<deadline:
                    remaining=deadline-time.monotonic()
                    result=stream_prepared(context,anchor,active_offset,min(chunk_cases,max_cases-completed_now),
                                           max(0.0,remaining),on_certificate=found)
                    if not result['completed_deletion_sets']:break
                    result.update(previous_record={'path':str(latest[0]),'sha256':latest[2]},
                                  anchor_id=anchor['id'],manifest_sha256=manifest_hash,
                                  batch_source_sha256=BATCH_SOURCE_SHA256)
                    path=records_directory/(anchor['id']+'-start-'+str(result['start_offset'])+'-end-'+str(result['next_offset'])+'-'+uuid.uuid4().hex[:8]+'.json')
                    digest=atomic_json(path,result,immutable=True);latest=(path,result,digest)
                    _publish_tip(tip,latest,anchor,manifest_hash)
                    completed_now+=result['completed_deletion_sets'];active_offset=result['next_offset'];publish()
                if active_offset==anchor['total_deletion_sets']:
                    cursor+=1;active_offset=0;publish()
                else:
                    status='case_limit_incomplete' if completed_now>=max_cases else 'timeout_incomplete'
                    publish();break
        if cursor<len(selected):status='case_limit_incomplete' if completed_now>=max_cases else 'timeout_incomplete'
        publish()
        return state


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=ROOT/'data/corner-anchor-frontier/manifest.json')
    parser.add_argument('--seed',type=Path,default=ROOT/'data/published-n78.json')
    parser.add_argument('--scan',type=Path,default=ROOT/'data/embedding-audit.json')
    parser.add_argument('--output',type=Path,required=True,help='durable batch cursor')
    parser.add_argument('--records-directory',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=900)
    parser.add_argument('--max-cases',type=int,default=1000000)
    parser.add_argument('--chunk-cases',type=int,default=20000)
    parser.add_argument('--max-anchor-cases',type=int,help='select only small anchor frontiers, e.g.1')
    parser.add_argument('--start-anchor',type=int,default=0)
    parser.add_argument('--stop-anchor',type=int)
    args=parser.parse_args(argv)
    try:
        seed,_=read_json(args.seed);scan,_=read_json(args.scan)
        result=run_batch(args.manifest,seed,scan,args.output,args.records_directory,args.seconds,
                         args.max_cases,args.chunk_cases,args.max_anchor_cases,args.start_anchor,args.stop_anchor)
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'error','error':str(exc),'batch_source_sha256':BATCH_SOURCE_SHA256}),file=sys.stderr);return 2
    print(json.dumps(result,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    sys.exit(main())
