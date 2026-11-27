"""Independent declared 52-role graph for SOURCE/TINY association tests.

No artifact discovery or actual input reads. Hash labels in this graph are
declared associations, NOT authenticated byte hashes. Point arrays reuse an
approved n4 control pair, while scores/identities declare historical65/64 for
metadata tests; geometry and normalization must be explicit spies, never run.
"""
from copy import deepcopy
from pathlib import Path
import sys
from research import restricted_three_row_actual_chain_adapter as adapter
from research import two_row_suffix75 as shared

H='a'*64
AFTER='b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7'
BEFORE=adapter.STATE
OLD_POINTS=[[0,0],[0,1],[0,2],[0,3],[1,1],[2,2],[3,3]]
NEW_POINTS=[[0,0],[0,1],[0,2],[0,3],[1,2],[2,1],[2,3]]
ROOT=adapter.ROOT
PREFIX='data/two-row-descent75-v1/'
OLD_REPORT=PREFIX+'report.json'
OLD_RECEIPT='data/experiments/shepherd-two-row-descent75-v1.json'
OLD_MANIFEST='data/two-row-descent75-source-pins.json'
OLD_BOUNDARY=PREFIX+'completed-boundary.json'
OLD_INITIAL=PREFIX+'initial.json'
OLD_BEST=PREFIX+'best.json'
OLD_AUDIT='data/two-row-descent75-independent-chain-actual-audit.json'
OLD_GUARD='data/two-row-descent75-independent-chain-actual-owned-guard.json'
OLD_ADAPTER='research/two_row_descent75_actual_chain_adapter.py'
OLD_HELPER='research/two_row_descent_independent_chain_audit.py'
OLD_REVIEW='research/two-row-descent75-independent-actual-acceptance-review.md'
OLD_METADATA='data/two-row-suffix75-input-identities.json'
NEW_METADATA='data/restricted-three-row64-input-identities.json'
MOVE=adapter.DIRECTORY+'/move-001-attempt-016.json'
AUDIT='data/restricted-three-row75-independent-actual-v1-audit.json'
GUARD='data/restricted-three-row75-independent-actual-v1-owned-guard.json'
PREPARATION='research/restricted-three-row-independent-actual-audit-preparation-addendum.md'
SOURCE_REVIEW='research/restricted-three-row-independent-chain-audit-source-review.md'
METADATA_REVIEW='research/restricted-three-row75-independent-actual-v1-metadata-review.md'
AUDIT_ADAPTER='research/restricted_three_row_actual_chain_adapter.py'
AUDIT_HELPER='research/restricted_three_row_independent_chain_audit.py'
AUDIT_COMMON='research/two_row_suffix_independent_authority_audit.py'
MOVES=[PREFIX+f'improvement-{i:03d}.json' for i in range(1,29)]
INHERITED=[OLD_REPORT,OLD_RECEIPT,OLD_MANIFEST,OLD_BOUNDARY,OLD_INITIAL,OLD_BEST,
           OLD_AUDIT,OLD_GUARD,OLD_ADAPTER,OLD_HELPER,OLD_REVIEW]+MOVES
ADDITIONAL=[OLD_METADATA,adapter.MANIFEST,adapter.REPORT,adapter.RECEIPT,adapter.AUTHORITY,
            adapter.INITIAL,MOVE,AUDIT,GUARD,PREPARATION,SOURCE_REVIEW,METADATA_REVIEW]
assert len(INHERITED)==39 and len(ADDITIONAL)==12 and len(set(INHERITED+ADDITIONAL))==51


def gate():
    return dict(gate_status='exited',returncode=0,cleanup_status='clean',cleanup_error=None,
                monitor_error=None,trigger_gate_status=None,seconds_limit=30,rss_limit_mib=256,
                peak_sampled_rss_kib=1024,rss_samples=2,cleanup_samples=1,elapsed_seconds=4.,cleanup_elapsed_seconds=.1)


def fixture():
    runtime=str(Path(sys.executable).resolve());ids={name:H for name in INHERITED+ADDITIONAL}
    ids.update({**adapter.EXPECTED,OLD_METADATA:adapter.HANDOFF_SHA,
                AUDIT:'ab302755266615a13423b81eb26c887af6a208d643ce1881a478fe5ee591450d',
                GUARD:'ab538127454ebe96430788d1f5fb2287636af436559522250cfd46aaa23fc5ac',
                SOURCE_REVIEW:'2d830bf1f7fd45a1d96422700d5298493421d2dcf36e90b2b6bf598fa0fcebe9',
                METADATA_REVIEW:'affd6aa18f2830958cf3f47fb1037d6210405dca6b853218425573feda0a08e9',
                MOVE:'414f4ac5fb20e84143ba0e26330fcab46b83afd142a5ee4b498028da56c43c76'})
    oldids={k:ids[k] for k in INHERITED}
    oldmanifest={str(ROOT/'research/two_row_descent75.py'):shared.KERNEL_SHA,runtime:H,str(ROOT/'src/verify.py'):H}
    oldpins={**oldmanifest,str(ROOT/OLD_MANIFEST):ids[OLD_MANIFEST]}
    prior={**oldpins,**{str(ROOT/k):v for k,v in oldids.items()},
           str(ROOT/OLD_METADATA):ids[OLD_METADATA],str(ROOT/'research/restricted_three_row75.py'):adapter.WORKER_SHA,
           str(ROOT/'research/two_row_suffix75.py'):adapter.SHARED_SHA}
    # Exact228 original entries plus one authenticated self label. These filler
    # paths are synthetic-only and a closed reader must never open them.
    i=0
    while len(prior)<228:prior[f'/synthetic-only/source-{i}']=H;i+=1
    effective={**prior,str(ROOT/adapter.MANIFEST):ids[adapter.MANIFEST]}
    pins={**effective,**{str(ROOT/k):v for k,v in ids.items()},str(ROOT/AUDIT_ADAPTER):'0d5537eb46a898a84cb89ba4aceff2a817c122f8b5873492e5cce06e226ad50c',
          str(ROOT/AUDIT_HELPER):adapter.HELPER_SHA,str(ROOT/AUDIT_COMMON):adapter.COMMON_SHA}
    coverage=dict(basis='source_bound_prior_execution_not_independent_minimum_certificate',pair_prefix=32,
                  pair_scan_complete=False,row_sweep_complete=True,status='pair_cap')
    oldmeta=dict(schema='two-row-fixed-suffix-handoff-identities-v1',n=75,point_count=149,unweighted_score=65,
                 normalized_sha256=BEFORE,inherited_counters=dict(shared.BASE),prior_initial_normalized_sha256=shared.kernel.BEST_NORMALIZED,
                 historical_coverage=coverage,artifacts=oldids)
    scores=[97]+list(range(96,69,-1))+[65]
    hashes=[shared.kernel.BEST_NORMALIZED]+[format(i,'064x') for i in range(1,28)]+[BEFORE]
    docs={};records=[]
    for i,name in enumerate(MOVES,1):
        m=dict(path=name,sha256=ids[name],kind='row',rows=[0],before_normalized_sha256=hashes[i-1],
               normalized_sha256=hashes[i],before_score=scores[i-1],score=scores[i],bytes=1)
        records.append(m);docs[name]={**m,'row_started':i,'row_completed':i,'pair_started':0,'pair_completed':0,'points':deepcopy(OLD_POINTS)}
    historical=dict(shared.BASE,status='pair_cap',U=65,row_sweep_complete=True,pair_scan_complete=False)
    handoff=dict(handoff_sha256=shared.kernel.HANDOFF_SHA)
    report=dict(pins=oldpins,method='exact_raw_two_row_descent75',accepted=True,identity_valid=True,closure=False,boundary_saved=True,
                witness_saved=False,status='pair_cap',validation='invalid_research_state',n=75,k=149,row_cap=512,pair_cap=32,
                soft_seconds=25,search_seconds=23,boundary_sha256=ids[OLD_BOUNDARY],boundary_bytes=1,current_unweighted=65,
                best_unweighted=65,elapsed_seconds=1.,state=historical,improvements=records,handoff=handoff)
    boundary=dict(state=historical,improvements=records,schema='two-row-raw-descent-boundary-v1',n=75,normalized_sha256=BEFORE,
                  policy=dict(row_cap=512,pair_cap=32),validation='invalid_research_state',handoff=handoff,points=deepcopy(OLD_POINTS))
    job=dict(sources_before=oldpins,argv=[str(ROOT/'.venv/bin/python'),'research/two_row_descent75.py','--seconds','25',
             '--output-dir','data/two-row-descent75-v1','--source-pins',OLD_MANIFEST],status='completed',sources_unchanged=True,
             source_manifest_sha256=ids[OLD_MANIFEST],gate=gate())
    historical_audit=dict(accepted=True,pilot_artifact_hashes={k:ids[k] for k in (OLD_REPORT,OLD_RECEIPT,OLD_MANIFEST,OLD_BOUNDARY)},
             audited_chain_artifact_hashes={k:ids[k] for k in [OLD_INITIAL]+MOVES},pilot_pins_checked=len(oldpins),
             audit_source_sha256=ids[OLD_ADAPTER],chain_helper_sha256=ids[OLD_HELPER],runtime_path=runtime,runtime_sha256=H,
             chain=dict(artifact_chain_passed=True,n=75,states_recounted=29,scores=scores,
                        final_counters={k:shared.BASE[k] for k in ('row_started','row_completed','pair_started','pair_completed')},zero_geometry_verified=False))
    historical_guard=gate();historical_guard.update(status='completed',argv=[str(ROOT/'.venv/bin/python'),OLD_ADAPTER,'--seconds','25','--output',OLD_AUDIT],
             audit_output_sha256=ids[OLD_AUDIT],source_pins={OLD_ADAPTER:ids[OLD_ADAPTER],OLD_HELPER:ids[OLD_HELPER]})
    validators=[dict(algorithm=alg,normalized_sha256=BEFORE,conflict_count=65,valid=False,errors=[],point_count=149,n=75)
                for alg in ('integer_normalized_slopes','integer_cross_products')]
    docs.update({OLD_REPORT:report,OLD_RECEIPT:job,OLD_MANIFEST:oldmanifest,OLD_BOUNDARY:boundary,
                 OLD_INITIAL:dict(normalized_sha256=shared.kernel.BEST_NORMALIZED,score=97,handoff=handoff),
                 OLD_BEST:dict(classification='dual_checked_invalid_research_state',valid=False,
                              certificate=dict(claimed_conflict_count=65,points=deepcopy(OLD_POINTS)),validators=validators),
                 OLD_AUDIT:historical_audit,OLD_GUARD:historical_guard,OLD_METADATA:oldmeta})
    counts=dict(started=16,completed=16,accepted=1);charge=dict(started=16,completed=15,accepted=0)
    order='f'*64;rows=[1,2,3];domains=[[0,1,2,3] for _ in range(3)];attempts=[]
    for seq in range(1,17):
        final=seq==16;minimum=[64,[0,2],[0,1],[0,2]] if final else [65,[0,1],[0,2],[0,3]]
        attempts.append(dict(seq=seq,rows=rows,state_hash=BEFORE,order_hash=order,cursor=seq-1,
             outcome='accepted' if final else 'complete',before_score=65,minimum=minimum,optimum_established=True,
             enumeration_exhausted=True,domains=domains,after_hash=AFTER if final else BEFORE))
    move=dict(schema='restricted-three-row-move-v1',n=75,points=deepcopy(NEW_POINTS),score=64,before_score=65,before_hash=BEFORE,
              state_hash=AFTER,generation=1,attempt=16,rows=rows,minimum=attempts[-1]['minimum'],domains=domains,counters=counts,
              old_order_hash=order,old_cursor=15,optimum_established=True,enumeration_exhausted=True)
    ref=dict(path=Path(MOVE).name,sha256=ids[MOVE],bytes=1743)
    a=dict(schema='restricted-three-row-authority-v1',policy=adapter.chain.POLICY,n=75,points=deepcopy(NEW_POINTS),U=64,state_hash=AFTER,
           origin_hash=BEFORE,generation=1,counters=counts,start_cap=16,orders=None,cursor=0,pending=None,attempts=attempts,
           artifacts=[ref],witness=None,status='block_cap')
    envelope=dict(payload=a,payload_sha256=adapter.chain.hashed(a));raw=adapter.chain.canonical(envelope)
    handoff=dict(metadata_sha256=ids[OLD_METADATA],normalized_sha256=BEFORE,score=65,historical_pair_prefix=32,coverage_basis=coverage['basis'])
    ini=dict(n=75,points=deepcopy(OLD_POINTS),score=65,state_hash=BEFORE,counters=dict.fromkeys(counts,0),order_sha256=order,handoff=handoff)
    r=dict(method='fixed65_restricted_three_row75',accepted=True,identity_valid=True,closure=False,authority_uncertain=False,n=75,k=149,
           block_cap=16,soft_seconds=25,search_seconds=23,authority_bytes=len(raw),authority_sha256=ids[adapter.AUTHORITY],
           state={k:a[k] for k in ('n','U','state_hash','generation','counters','cursor','pending','status')},attempts=attempts,
           artifacts=[ref],order_sha256=None,status='block_cap',witness_saved=False,authority_publications=34,work=dict(indexes_started=2),
           handoff=handoff,pins=effective,elapsed_seconds=3.,last_attempted_charge=charge)
    j=dict(argv=[str(ROOT/'.venv/bin/python'),'research/restricted_three_row75.py','--seconds','25','--output-dir',adapter.DIRECTORY,
                 '--source-pins',adapter.MANIFEST],status='completed',sources_unchanged=True,source_manifest_sha256=ids[adapter.MANIFEST],
           sources_before=effective,elapsed_seconds=5.,gate=gate())
    chain=dict(authority_chain_passed=True,receipt_acceptance_checked=False,counters=counts,last_start_charge=charge,
               accepted_scores=[65,64],accepted_state_hashes=[BEFORE,AFTER],new_accepted_moves=1,unique_states_recounted=2,
               durable_U=64,durable_state_hash=AFTER,durable_status='block_cap',cursor=0,pending_attempt=None,
               recorded_nonimprovements_not_independent_minima=15,side_outputs=[],
               observations=[{k:v[k] for k in ('seq','rows','state_hash','cursor','outcome')} for v in attempts])
    audited=[adapter.REPORT,adapter.RECEIPT,adapter.MANIFEST,adapter.AUTHORITY,adapter.INITIAL,MOVE]
    au=dict(accepted=True,chain=chain,manifest_entries=228,effective_pins=229,artifact_hashes={k:ids[k] for k in audited},
            audit_source_sha256=pins[str(ROOT/AUDIT_ADAPTER)],helper_sha256=adapter.HELPER_SHA,common_helper_sha256=adapter.COMMON_SHA,
            runtime_path=runtime,runtime_sha256=H,elapsed_seconds=1.,resources=dict(elapsed_seconds=4.,peak_sampled_rss_kib=1024,
                 rss_note='Sampled RSS observation; not a proved unsampled maximum.'))
    g=gate();g.update(status='completed',argv=[str(ROOT/'.venv/bin/python'),AUDIT_ADAPTER,'--seconds','25','--output',AUDIT],
            audit_output_sha256=ids[AUDIT],source_pins={k:pins[str(ROOT/k)] for k in (SOURCE_REVIEW,AUDIT_ADAPTER,AUDIT_HELPER,AUDIT_COMMON)})
    docs.update({adapter.MANIFEST:prior,adapter.REPORT:r,adapter.RECEIPT:j,adapter.AUTHORITY:envelope,adapter.INITIAL:ini,
                 MOVE:move,AUDIT:au,GUARD:g})
    sizes={k:1 for k in ids};sizes[MOVE]=1743;sizes[adapter.AUTHORITY]=len(raw)
    meta=dict(schema='restricted-three-row-fixed64-handoff-identities-v1',n=75,point_count=149,unweighted_score=64,
              normalized_sha256=AFTER,predecessor_normalized_sha256=BEFORE,artifact_count=51,inherited_artifact_count=39,
              artifacts=ids,artifact_byte_sizes=sizes,scope='SYNTHETIC DECLARED ASSOCIATION; no byte authentication or geometry claim.')
    assert len(docs)==45 and set(docs)=={k for k in ids if k.endswith('.json')}
    # Independent JSON documents cannot share mutable containers. Preserve that
    # property so a single-document corruption never silently edits its peers.
    return dict(docs={k:deepcopy(v) for k,v in docs.items()},metadata=deepcopy(meta),pins=deepcopy(pins),authority_raw=raw,runtime=runtime,
                old_points=deepcopy(OLD_POINTS),new_points=deepcopy(NEW_POINTS),source_roles=set(ids)-set(docs))
