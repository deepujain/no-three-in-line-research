"""Durable, bounded worker for one existing embedding-repair frontier.

--previous accepts an immutable stream record or a durable tip pointer.
--output is the tip file to atomically update. Each chunk writes a NEW immutable
offset-specific record alongside the tip; earlier records are never changed.
All links are hash checked and must cover the frontier gaplessly from zero.
"""

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.embedding_audit import stream_cover_repairs, validate_repair_source
from src.verify import verify_certificate, verify_certificate_bruteforce


def digest_bytes(content):
    return hashlib.sha256(content).hexdigest()


def read_json(path):
    raw=Path(path).read_bytes()
    return json.loads(raw),digest_bytes(raw)


def atomic_json(path,value,immutable=False):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if immutable and path.exists():
        raise FileExistsError(f'immutable result already exists: {path}')
    payload=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(prefix='.'+path.name+'.',dir=path.parent,delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if immutable:
            # Hard-link publication refuses an existing destination atomically.
            os.link(temporary,path)
            temporary.unlink()
        else:
            os.replace(temporary,path)
        temporary=None
        return digest_bytes(payload)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def resolve_reference(reference,relative_to):
    path=Path(reference['path'])
    if not path.is_absolute():
        return Path(relative_to).parent/path
    if path.exists():
        return path
    # Published immutable records retain their original bytes and hashes.
    # A moved checkout resolves the same basename beside its referring record;
    # load_gapless_chain still checks the referenced bytes against their hash.
    return Path(relative_to).parent/path.name


def load_gapless_chain(previous,seed,scan):
    """Return the latest immutable record after checking its whole ancestry."""
    source_hash=validate_repair_source(seed,scan)
    order_hash=digest_bytes(json.dumps({'n':seed['n'],'points':seed['points']},
                                     sort_keys=True,separators=(',',':')).encode())
    path=Path(previous).resolve()
    record,record_hash=read_json(path)
    if record.get('kind')=='embedding_stream_tip':
        reference=record['record']
        path=resolve_reference(reference,path).resolve()
        record,record_hash=read_json(path)
        if record_hash!=reference['sha256']:
            raise ValueError('tip record hash mismatch')
    latest=(path,record,record_hash)
    fields=('cut','base_deletion_indices','exact_deletion_count','total_deletion_sets',
            'enumeration_order','source_normalized_sha256','source_order_sha256')
    parameters={field:record.get(field) for field in fields}
    seen=set()
    while True:
        if path in seen:
            raise ValueError('cycle in resume chain')
        seen.add(path)
        if record.get('audit')!='streamed_single_cover_exact_deletion_repair':
            raise ValueError('previous record is not a compatible stream result')
        if record.get('source_normalized_sha256')!=source_hash or record.get('source_order_sha256')!=order_hash:
            raise ValueError('previous record source/hash does not match the current seed')
        if any(record.get(field)!=parameters[field] for field in fields):
            raise ValueError('resume chain changes frontier parameters')
        start,end,total,completed=(record.get(field) for field in
                                   ('start_offset','next_offset','total_deletion_sets','completed_deletion_sets'))
        if any(type(value) is not int for value in (start,end,total,completed)):
            raise ValueError('resume offsets must be integers')
        if not 0<=start<=end<=total or completed!=end-start:
            raise ValueError('inconsistent resume offsets or completion counters')
        if record.get('status') not in ('complete','case_limit_incomplete','timeout_incomplete'):
            raise ValueError('unrecognized stream status')
        if record['status']=='complete' and end!=total:
            raise ValueError('complete stream result does not reach the frontier end')
        parent=record.get('previous_record')
        if parent is None:
            if start!=0:
                raise ValueError('resume chain has no zero-offset origin')
            break
        parent_path=resolve_reference(parent,path).resolve()
        parent_record,parent_hash=read_json(parent_path)
        if parent_hash!=parent['sha256']:
            raise ValueError('previous record hash mismatch')
        if parent_record.get('next_offset')!=start:
            raise ValueError('gap or overlap in resume chain')
        path,record,record_hash=parent_path,parent_record,parent_hash
    return latest+(seen,)


def _run_worker_unlocked(previous,output,seed,scan,seconds=900,max_cases=10**9,chunk_cases=20000):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
        raise ValueError('seconds must be finite and nonnegative')
    if any(type(v) is not int or v<0 for v in (max_cases,chunk_cases)) or chunk_cases==0:
        raise ValueError('max_cases must be nonnegative and chunk_cases positive')
    started=time.monotonic()
    deadline=started+seconds
    output=Path(output).resolve()
    latest_path,latest,latest_hash,ancestors=load_gapless_chain(previous,seed,scan)
    if output in ancestors:
        raise ValueError('output tip must not overwrite the previous immutable record')
    if output.exists():
        existing,_=read_json(output)
        if existing.get('kind')!='embedding_stream_tip':
            raise ValueError('output already contains a non-tip artifact')
        old_path,old_record,old_hash,old_ancestors=load_gapless_chain(output,seed,scan)
        identity=('cut','base_deletion_indices','exact_deletion_count','total_deletion_sets','enumeration_order')
        if any(old_record[key]!=latest[key] for key in identity):
            raise ValueError('existing tip belongs to a different frontier')
        if old_record['next_offset']>=latest['next_offset']:
            latest_path,latest,latest_hash=old_path,old_record,old_hash
    completed_this_invocation=0
    written=[]
    witnesses=[]

    def publish_tip():
        atomic_json(output,{'kind':'embedding_stream_tip',
                    'record':{'path':str(latest_path),'sha256':latest_hash},
                    'cut':latest['cut'],'next_offset':latest['next_offset'],
                    'total_deletion_sets':latest['total_deletion_sets'],
                    'coverage':{'start':0,'end':latest['next_offset'],'gapless':True},
                    'frontier_complete':latest['next_offset']==latest['total_deletion_sets']})

    def found(certificate):
        checks=[verify_certificate(certificate),verify_certificate_bruteforce(certificate)]
        if not all(check['valid'] for check in checks):
            raise RuntimeError('worker refused invalid witness')
        name=f'embedding-witness-n{certificate["n"]}-{checks[0]["normalized_sha256"][:16]}-{uuid.uuid4().hex[:8]}.json'
        path=output.parent/name
        atomic_json(path,certificate,immutable=True)
        witnesses.append(str(path))
        print(json.dumps({'event':'verified_witness_saved','path':str(path),
                          'point_count':len(certificate['points'])}),flush=True)

    publish_tip()
    while latest['next_offset']<latest['total_deletion_sets']:
        remaining=deadline-time.monotonic()
        allowance=max_cases-completed_this_invocation
        if remaining<=0 or allowance<=0:
            break
        result=stream_cover_repairs(seed,scan,latest['cut'],latest['base_deletion_indices'],
                                   deletion_count=latest['exact_deletion_count'],
                                   start_offset=latest['next_offset'],
                                   expected_source_order_sha256=latest['source_order_sha256'],
                                   max_cases=min(chunk_cases,allowance),seconds=remaining,
                                   on_certificate=found)
        if result['total_deletion_sets']!=latest['total_deletion_sets']:
            raise ValueError('recomputed frontier size differs from previous record')
        if result['completed_deletion_sets']==0:
            break
        result['previous_record']={'path':str(latest_path),'sha256':latest_hash}
        a,b=result['cut']
        name=(f'embedding-stream-cut-{a}-{b}-start-{result["start_offset"]}'
              f'-end-{result["next_offset"]}-{uuid.uuid4().hex[:8]}.json')
        new_path=output.parent/name
        new_hash=atomic_json(new_path,result,immutable=True)
        latest_path,latest,latest_hash=new_path,result,new_hash
        completed_this_invocation+=result['completed_deletion_sets']
        written.append(str(new_path))
        publish_tip()
        print(json.dumps({'event':'embedding_checkpoint','path':str(new_path),
                          'next_offset':latest['next_offset'],'status':latest['status']}),flush=True)
    return {'status':'complete' if latest['next_offset']==latest['total_deletion_sets'] else 'partial',
            'output_tip':str(output),'next_offset':latest['next_offset'],
            'total_deletion_sets':latest['total_deletion_sets'],
            'completed_this_invocation':completed_this_invocation,'new_records':written,
            'witness_files':witnesses,'elapsed_seconds':time.monotonic()-started}


def run_worker(previous,output,seed,scan,seconds=900,max_cases=10**9,chunk_cases=20000):
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    # Prevent two processes from racing the same durable tip backwards.
    with open(str(output)+'.lock','a') as lock:
        try:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('another worker already holds this frontier tip') from exc
        return _run_worker_unlocked(previous,output,seed,scan,seconds,max_cases,chunk_cases)


def main(argv=None):
    arguments=list(sys.argv[1:] if argv is None else argv)
    if '--batch' in arguments:
        arguments.remove('--batch')
        from research.corner_batch_worker import main as batch_main
        return batch_main(arguments)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True,help='durable tip JSON path')
    parser.add_argument('--seed',type=Path,default=ROOT/'data/published-n78.json')
    parser.add_argument('--scan',type=Path,default=ROOT/'data/embedding-audit.json')
    parser.add_argument('--seconds',type=float,default=900)
    parser.add_argument('--max-cases',type=int,default=10**9)
    parser.add_argument('--chunk-cases',type=int,default=20000)
    args=parser.parse_args(arguments)
    try:
        seed,_=read_json(args.seed)
        scan,_=read_json(args.scan)
        result=run_worker(args.previous,args.output,seed,scan,args.seconds,args.max_cases,args.chunk_cases)
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'error','error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True),flush=True)
    return 0


if __name__=='__main__':
    sys.exit(main())
