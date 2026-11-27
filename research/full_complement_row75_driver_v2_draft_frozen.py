"""One fixed full-complement row diagnostic; no resume or candidate adoption."""
import time
ENTRY_STARTED = time.monotonic()
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
MODULE_IDENTITIES = {
    'research/full_complement_row75_core.py':'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b',
    'research/full_complement_row75_primary.py':'2780666ac7f2a1d31e4b735135164fd4f0baf6c06b1424fb6eff405d01006e0e',
    'research/full_complement_row75_independent.py':'6bad0b8ec41e4068d5015f719895949278f4ddad867f5d989ea543e79ccab1a1'}
POINT_PATH = 'data/full-complement-row75-fixed64-points-v1.json'
POINT_SHA = 'b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7'
POINT_BYTES = 1166
HANDOFF_PATH = 'data/full-complement-row75-fixed64-handoff-v1.json'
HANDOFF_SHA = '6fc5cea2902fc361421238dbfb9d02513e0ff390d122a81b2238ca83a64c0a3c'
HANDOFF_BYTES = 1120
HANDOFF_REVIEW = 'research/full-complement-row75-fixed64-independent-handoff-review.md'
HANDOFF_REVIEW_SHA = 'f6a0165b0c3ffa2d367a8226abe9bbd2899977cee7f6ffb7953d3cb3b575e1ad'
VERIFIER_SHA = 'e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c'
TINY_SHA = '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37'
PROVENANCE = {
    'source_initial':{'path':'data/restricted-three-row64-v2/initial.json','bytes':2012,
                      'sha256':'1756d83bc3bfa5bf491d37e5c59bdc785a095184aa285c260820670a39938ead'},
    'accepted_audit':{'path':'data/restricted-three-row64-independent-actual-v2-audit.json','bytes':7565,
                      'sha256':'df58ba6557f95f42db3d64cf645d391de7171d0bc44b3088f0652d9989b287d7'},
    'acceptance_review':{'path':'research/restricted-three-row64-independent-actual-v2-metadata-review.md','bytes':2138,
                         'sha256':'a3cb672e70bbf00d872d80d5f973ea91a7e8d63150b7ce1190b100155b0e957e'}}


def require(condition,message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path,check):
    value = hashlib.sha256()
    with Path(path).open('rb') as source:
        while True:
            check()
            block = source.read(65536)
            if not block:
                return value.hexdigest()
            value.update(block)


def load_modules(check):
    for name,expected in MODULE_IDENTITIES.items():
        require(digest(ROOT/name,check) == expected,'mandatory module source drift: '+name)
    modules = []
    for name in MODULE_IDENTITIES:
        module = importlib.import_module('research.'+Path(name).stem)
        require(Path(module.__file__).resolve() == (ROOT/name).resolve(),'module origin')
        modules.append(module)
    return tuple(modules)


def validate_handoff(value):
    require(type(value) is dict and set(value) == {'schema','n','point_count','raw_score','normalized_sha256',
                                                  'snapshot','provenance','scope'},'handoff exact schema')
    for key,expected in (('schema',1),('n',75),('point_count',149),('raw_score',64)):
        require(type(value[key]) is int and value[key] == expected,'handoff strict integer '+key)
    require(value['normalized_sha256'] == POINT_SHA,'handoff normalized identity')
    expected_snapshot = {'path':POINT_PATH,'sha256':POINT_SHA,'bytes':POINT_BYTES}
    require(type(value['snapshot']) is dict and set(value['snapshot']) == set(expected_snapshot)
            and value['snapshot'] == expected_snapshot and type(value['snapshot']['bytes']) is int,'fixed snapshot descriptor')
    require(type(value['provenance']) is dict and set(value['provenance']) == set(PROVENANCE),'exact three provenance roles')
    for role,expected in PROVENANCE.items():
        descriptor = value['provenance'][role]
        require(type(descriptor) is dict and set(descriptor) == {'path','sha256','bytes'}
                and descriptor == expected and type(descriptor['bytes']) is int,'fixed provenance descriptor: '+role)
    require(type(value['scope']) is str and len(value['scope']) <= 1024,'handoff scope bound')
    return value


def normalize_pins(mapping):
    require(type(mapping) is dict and 1 <= len(mapping) <= 256,'manifest map/count')
    result = {}
    for name,value in mapping.items():
        require(type(name) is str and 0 < len(name) <= 1024 and type(value) is str and len(value) == 64
                and all(c in '0123456789abcdef' for c in value),'manifest pin schema')
        path = str((ROOT/name).resolve())
        require(len(path) <= 1024 and path not in result,'manifest alias/path cap')
        result[path] = value
    return result


def check_manifest_map(mapping,manifest_path,*,runtime=None):
    """Presence and expected digest, not just matching whatever was listed."""
    pins = normalize_pins(mapping)
    required = dict(MODULE_IDENTITIES)
    required.update({POINT_PATH:POINT_SHA,HANDOFF_PATH:HANDOFF_SHA,HANDOFF_REVIEW:HANDOFF_REVIEW_SHA,
                     'src/verify.py':VERIFIER_SHA})
    for name,expected in required.items():
        path = str((ROOT/name).resolve())
        require(pins.get(path) == expected,'missing or changed mandatory pin: '+name)
    physical_runtime = str(Path(sys.executable if runtime is None else runtime).resolve())
    require(physical_runtime in pins and str(Path(__file__).resolve()) in pins,'runtime and driver mandatory presence')
    require(str(Path(manifest_path).resolve()) not in pins,'manifest self entry')
    forbidden = {str((ROOT/d['path']).resolve()) for d in PROVENANCE.values()}
    require(not forbidden.intersection(pins),'history is referenced, never opened by diagnostic')
    return pins


def read_exact(path,size,expected,check):
    check()
    path = Path(path)
    require(path.stat().st_size == size,'fixed file byte size')
    raw = path.read_bytes()
    require(len(raw) == size and path.stat().st_size == size and sha(raw) == expected,'fixed file identity')
    check()
    return raw


def verify_pins(pins,check):
    for path,expected in pins.items():
        require(digest(path,check) == expected,'source/input pin drift: '+path)


def load_input(manifest,core,budget):
    """One detached input; this frame opens no referenced historical artifact."""
    path = Path(manifest).resolve()
    require(path.stat().st_size <= 64*1024,'manifest byte cap')
    raw = path.read_bytes()
    require(len(raw) <= 64*1024,'manifest encoded cap')
    manifest_sha = sha(raw)
    mapping = core.decode(raw)
    handoff_raw = read_exact(ROOT/HANDOFF_PATH,HANDOFF_BYTES,HANDOFF_SHA,budget.checkpoint)
    handoff = validate_handoff(core.decode(handoff_raw))
    pins = check_manifest_map(mapping,path)
    pins[str(path)] = manifest_sha
    del mapping,raw,handoff_raw
    budget.set_roots(pins,handoff)
    budget.check_graph()
    verify_pins(pins,budget.checkpoint)
    raw = read_exact(ROOT/POINT_PATH,POINT_BYTES,POINT_SHA,budget.checkpoint)
    document = core.decode(raw)
    require(type(document) is dict and set(document) == {'n','points'} and type(document['n']) is int
            and document['n'] == 75,'fixed point document schema')
    points = core.validate_points(document['points'],75)
    require(core.compact({'n':75,'points':points}) == raw and core.normalized_sha256(points,75) == POINT_SHA,
            'exact canonical normalized point identity')
    info = {'snapshot_sha256':POINT_SHA,'snapshot_bytes':POINT_BYTES,'handoff_sha256':HANDOFF_SHA,
            'handoff_review_sha256':HANDOFF_REVIEW_SHA,'normalized_sha256':POINT_SHA,'n':75,'point_count':149,
            'raw_score':64,'provenance':handoff['provenance'],'history_opened':False}
    return points,pins,info


def candidate_document(points,n,record,input_info,core):
    row,columns,predicted = record['row'],record['best'],record['best_score']
    candidate = tuple(sorted(tuple(p for p in points if p[1] != row)+tuple((x,row) for x in columns)))
    candidate = core.validate_points(candidate,n)
    identity = core.normalized_sha256(candidate,n)
    value = {'schema':1,'kind':'zero_witness' if predicted == 0 else 'strict_row_proposal',
             'n':n,'points':candidate,'raw_score':predicted,'normalized_sha256':identity,
             'before_normalized_sha256':core.normalized_sha256(points,n),'row':row,'columns':columns,
             'input_snapshot_sha256':input_info['snapshot_sha256'],'adopted':False}
    return candidate,value


def diagnose(points,n,expected,pins,input_info,store,budget,primary,independent,core,*,work_check,final_check):
    """No loader here: tiny callers still need the one approved literal identity."""
    points = core.validate_points(points,n)
    expected_identity = POINT_SHA if n == 75 else TINY_SHA
    require(type(expected) is int and expected == (64 if n == 75 else 14)
            and core.normalized_sha256(points,n) == expected_identity,'one authorized fixed input')
    report = {'method':'full-complement-exact-same-load-single-row','n':n,'input':input_info,
              'baseline':expected,'accepted':False,'profile_verified':False,'diagnostic_complete':False,
              'witness_saved':False,'candidate_saved':False,'adopted':False,'rows':[]}
    records = report['rows']
    budget.set_roots(points,pins,input_info,report)
    direct = independent.direct_raw(points,n,budget)
    require(type(direct) is int and direct == expected,'fresh direct baseline')
    primary_result = primary.costs(points,n,budget)
    require(type(primary_result) is dict and set(primary_result) == {'baseline','costs'}
            and type(primary_result['baseline']) is int and primary_result['baseline'] == direct,'fresh pair-line baseline')
    matrix = primary_result['costs']
    del primary_result
    report['all_costs_computed'] = True
    report['baseline_validators'] = {'direct':direct,'pair_lines':expected}
    budget.set_roots(points,pins,input_info,report,matrix)
    budget.check_graph()
    best = None
    generator = primary.row_records(points,n,matrix,expected,budget)
    try:
        for record in generator:
            records.append(record)
            if record['best_score'] == 0:
                require(expected > 0,'strict zero')
                candidate,value = candidate_document(points,n,record,input_info,core)
                budget.check = final_check
                prepared = store.prepare(value,16*1024)
                budget.set_roots(points,pins,input_info,report,matrix,candidate,prepared)
                validation = independent.verify_candidate(points,candidate,n,record['row'],record['best'],0,budget)
                require(validation['score'] == 0 and validation['normalized_sha256'] == value['normalized_sha256'],
                        'validated zero identity')
                # No clock, graph, source check or optional metadata before this durable save.
                reference = store.commit_prepared('witness.json',prepared,16*1024,urgent=True)
                report['witness_saved'] = True
                report['witness'] = reference
                report.update(status='zero_witness',candidate_validation=validation,zero_row=record['row'])
                return report
            if record['best_score'] < expected:
                key = record['best_score'],record['row'],record['best']
                if best is None:
                    best = key
                else:
                    budget.charge('comparisons','selection')
                    if key < best:
                        best = key
    finally:
        generator.close()
    require(len(records) == n,'all rows provisionally recorded')
    verification = independent.verify_profiles(points,n,matrix,records,expected,budget)
    require(verification.get('all_unaries_and_lexical_minima_verified') is True
            and verification.get('verified_rows') == n and verification.get('verified_cells') == n*n,'complete independent profile')
    report.update(profile_verified=True,diagnostic_complete=True,profile_verification=verification)
    unary = {'schema':1,'n':n,'input_normalized_sha256':expected_identity,'costs':matrix,'rows':records,
             'independently_verified':True}
    prepared_unary = store.prepare(unary,64*1024)
    report['unaries'] = store.commit_prepared('unaries.json',prepared_unary,64*1024)
    if best is None:
        report['status'] = 'no_strict_same_load_row'
        return report
    score,row,columns = best
    require(0 < score < expected,'one strict positive candidate')
    record = records[row]
    require(record['best'] == columns and record['best_score'] == score,'global winner record')
    candidate,value = candidate_document(points,n,record,input_info,core)
    prepared = store.prepare(value,16*1024)
    budget.set_roots(points,pins,input_info,report,matrix,candidate,prepared)
    validation = independent.verify_candidate(points,candidate,n,row,columns,score,budget)
    require(validation['score'] == score and validation['normalized_sha256'] == value['normalized_sha256'],
            'validated positive candidate identity')
    work_check()
    report['candidate'] = store.commit_prepared('candidate.json',prepared,16*1024)
    report.update(status='strict_row_proposal',candidate_saved=True,candidate_validation=validation,
                  best_row=row,best_columns=columns,best_score=score)
    return report


def run(out,manifest,*,started=None,clock=time.monotonic):
    start = clock() if started is None else started
    def work_check():
        if clock() >= start+23:
            raise TimeoutError('23-second work boundary')
    def final_check():
        if clock() >= start+25:
            raise TimeoutError('25-second soft boundary')
    out = Path(out)
    out.mkdir(exist_ok=False)
    core = None
    budget = store = None
    pins = {}
    report = {'accepted':False,'status':'error','witness_saved':False,'candidate_saved':False,'adopted':False}
    try:
        core,primary,independent = load_modules(work_check)
        budget = core.Budget(work_check)
        store = core.ImmutableStore(out,budget)
        points,pins,info = load_input(manifest,core,budget)
        report = diagnose(points,75,64,pins,info,store,budget,primary,independent,core,
                          work_check=work_check,final_check=final_check)
        budget.check = final_check
        verify_pins(pins,final_check)
        require(not store.uncertain,'uncertain publication')
        final_check()
        report.update(accepted=True,identity_valid=True,pins=pins,elapsed_before_report=clock()-start,
                      operation_counts_before_report=budget.snapshot(),expected_final_publications=budget.counts['publications']+1)
        raw = store.prepare(report,128*1024)
        store.commit_prepared('report.json',raw,128*1024)
        verify_pins(pins,final_check)
        final_check()
        return report
    except Exception as exc:
        if budget is not None:
            budget.check = lambda:None
        # Durable zero/proposal references survive errors inside diagnose through store ownership.
        if store is not None:
            if 'witness.json' in store.references:
                report['witness_saved'] = True
                report['witness'] = store.references['witness.json']
            if 'candidate.json' in store.references:
                report['candidate_saved'] = True
                report['candidate'] = store.references['candidate.json']
        report.update(accepted=False,status='error',error=type(exc).__name__+': '+str(exc)[:1000],
                      elapsed_seconds=clock()-start,authority_adopted=False)
        identities = {}
        for name in tuple(MODULE_IDENTITIES)+(str(Path(__file__).relative_to(ROOT)),):
            try:
                source_path = ROOT/name
                require(source_path.stat().st_size <= 128*1024,'bounded failure identity size')
                with source_path.open('rb') as source:
                    raw = source.read(128*1024+1)
                require(len(raw) <= 128*1024,'bounded failure identity read')
                identities[name] = {'sha256':sha(raw),'error':None}
            except Exception as error:
                identities[name] = {'sha256':None,'error':type(error).__name__+': '+str(error)[:1000]}
        report['observed_source_identities'] = identities
        if budget is not None:
            report.update(operation_counts=budget.snapshot(),publication_uncertain=store.uncertain)
        try:
            raw = (json.dumps(report,sort_keys=True,separators=(',',':'),ensure_ascii=True)).encode('ascii')
            require(len(raw) <= 128*1024,'failure report cap')
            if store is not None:
                store.commit_prepared('failure.json',raw,128*1024,urgent=True)
            else:
                # Dependency authentication can fail before shared quota code is imported.
                with (out/'failure.json').open('xb') as output:
                    require(output.write(raw) == len(raw),'complete failure artifact write')
                    output.flush()
                    import os
                    os.fsync(output.fileno())
                directory = os.open(out,os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        except Exception as error:
            report['failure_persistence_error'] = type(error).__name__+': '+str(error)[:1000]
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--source-pins',type=Path,required=True)
    args = parser.parse_args()
    report = run(args.output_dir,args.source_pins,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('accepted','status','witness_saved','candidate_saved','diagnostic_complete',
                                              'error','failure_persistence_error')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__ == '__main__':
    sys.exit(main())
