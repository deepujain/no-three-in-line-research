"""Opt-in real-host n3/n5 standalone residual guard lifecycle gate.

Preparation is not execution authorization. Root schedules only after review.
Exactly four successful guard invocations and one observed-worker cancellation
are attempted, with no retry. Witness order is NOT observed by this gate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import diagonal_residual_checkpoint_guard as guard
from research import diagonal_residual_checkpoint as core
from research.diagonal_secant_checkpoint import encode,sha
from research.diagonal_secant_dfs_fast import pair_orbits
from src.verify import verify_certificate,verify_certificate_bruteforce

EXPECTED_SOURCES={
    'checkpoint_utilities':'48f49f36a7f99bc3d42bc5c4376c3267c5d0f0b05ba9af27f4619403e20f6721',
    'entrypoint':'8aea8375bd334fb3a3fd73fbe1f550f78e528eddd102bc9a866cb0f1400daadd',
    'fast_core':'38ec5044a8db85f046be24feb97c51adb6a95825afccac375d078195a57022a3',
    'guard':'8aea8375bd334fb3a3fd73fbe1f550f78e528eddd102bc9a866cb0f1400daadd',
    'helper':'c119b58f1950f4b0b8554c2ec2065f377efbfcfb53e83d48921f505ef4c6ee48',
    'original_core':'6b92f7189b7658b465cd9162992b7ea28ad79a4b30de9ea488b6f20776b7c4a7',
    'residual_checkpoint':'d8576102cbd904a23a6170807e89df9d4ab5610bdc1acb88351a7f8d6660ce6c',
    'residual_tiny_reference':'56aa4158a56b675722e70b2241c0b4d54c1d26a890c536728d451c0fb19a9387',
    'tiny_reference':'27d74e27fa29557cf867ba7f9591e0a349427def5a0a017f4fc9b7a88b36e0e2',
    'verifier':'e995c2367481bc63174b8f80d63048bdae6ebf75232e026509c6012157c11c4c'}
ORACLE=ROOT/'data/diagonal-residual-checkpoint-tiny-evidence.json'
ORACLE_SHA='3bc2773387fe320e440bbc6a02a5b53dc4952bf17bd31ecb75ebb94b6789ec7a'
SECONDS=10
RSS_MIB=256


def require(condition,message):
    if not condition:raise ValueError(message)


def raw(path,limit=1_000_000):
    with Path(path).open('rb') as stream:data=stream.read(limit+1)
    require(len(data)<=limit,'artifact exceeds gate read bound')
    return data


def digest(path):return hashlib.sha256(raw(path)).hexdigest()
def read_json(path):return json.loads(raw(path))


def identity(path,n):
    data=read_json(path)
    require(data['identity']=={
        'format':'diagonal-residual-rowbatch-frontier-v1','n':n,
        'deficits':list(range(n)),'diagonals':list(range(n)),
        'branch_order':'minimum-viable-row-then-lexicographic-unordered-batch-v1',
        'prune_policy':'residual-row-degree-component-parity-bipartite-sum-v1',
        'orbit_order_sha256':sha(encode(pair_orbits(n))),
        'source_hashes':{key:EXPECTED_SOURCES[key] for key in core.SOURCES}},
        'checkpoint identity mismatch')
    return data


def command(n,checkpoint,report,quota,pin=None):
    args=[sys.executable,str(guard.SOURCES['entrypoint']),'--n',str(n),
          '--seconds',str(SECONDS),'--rss-mib',str(RSS_MIB),'--max-nodes',str(quota),
          '--checkpoint',str(checkpoint),'--output',str(report)]
    return args+(['--expected-sha256',pin] if pin else [])


def check_helper(report,expected_status='exited'):
    g=report['guard']
    require(report['source_hashes']==EXPECTED_SOURCES and g['source_stable'],
            'report source mismatch')
    require(g['gate_status']==expected_status and g['cleanup_status']=='clean',
            'helper did not meet status/cleanup gate')
    require(g.get('monitor_error') is None and g.get('cleanup_error') is None,
            'helper monitor or cleanup error')
    require(g['rss_samples']>0 and g['cleanup_samples']>0,'missing positive monitor samples')
    require(0<g['peak_sampled_rss_kib']<=RSS_MIB*1024,'RSS gate failed')
    require(0<g['seconds_limit']<=SECONDS and g['rss_limit_mib']==RSS_MIB,
            'helper caps mismatch')
    require(g['elapsed_seconds']<g['seconds_limit'] and report['elapsed_seconds']<SECONDS,
            'helper/invocation elapsed gate failed')
    if expected_status=='exited':require(g['returncode']==0,'worker failed')


def witnesses(report,n):
    result=[]
    for path in sorted(Path(report['witness_dir']).glob('*.json')):
        cert=read_json(path);checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
        require(cert['n']==n and all(c['valid'] and c['point_count']==2*n-1 for c in checks),
                'invalid witness')
        require({(y,x) for x,y in cert['points']}=={tuple(p) for p in cert['points']},
                'witness lacks reflection symmetry')
        require(checks[0]['normalized_sha256']==checks[1]['normalized_sha256']==path.stem,
                'witness normalized digest mismatch')
        meta=cert['metadata']
        require(meta['method']=='diagonal_residual_checkpoint' and
                meta['guard_source_hashes']==EXPECTED_SOURCES and
                meta['normalized_sha256']==path.stem,'witness metadata mismatch')
        result.append({'path':str(path),'sha256':digest(path),'normalized_sha256':path.stem,
                       'deficit':meta['deficit'],'diagonal':meta['diagonal'],
                       'verifiers':checks})
    return result


def stop_supervisor(process):
    """Only signal our unreaped direct child; never signal a cached worker PID."""
    if process is None or process.poll() is not None:return False
    process.terminate()
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:pass
        return True
    return False


def run_stage(args,stem,summary,*,cancel=False):
    process=None;observed=None
    attempt={'command':args,'stdout':str(stem)+'.stdout','stderr':str(stem)+'.stderr'}
    summary['attempts'].append(attempt)
    with open(attempt['stdout'],'wb') as stdout,open(attempt['stderr'],'wb') as stderr:
        try:
            process=subprocess.Popen(args,cwd=ROOT,stdout=stdout,stderr=stderr)
            if cancel:
                deadline=time.monotonic()+SECONDS
                while time.monotonic()<deadline and process.poll() is None:
                    ps=subprocess.run(['ps','-axo','pid=,ppid=,args='],capture_output=True,
                                      text=True,check=True,timeout=1)
                    for row in ps.stdout.splitlines():
                        fields=row.strip().split(None,2)
                        if (len(fields)==3 and int(fields[1])==process.pid and
                            str(guard.SOURCES['entrypoint']) in fields[2] and '--_worker' in fields[2]):
                            observed=int(fields[0]);break
                    if observed is not None:break
                    time.sleep(.005)
                require(observed is not None,'did not observe actual worker before exit')
                attempt['observed_worker_pid']=observed
                require(process.poll() is None,'supervisor exited before cancellation')
                process.send_signal(signal.SIGTERM)
                attempt['sigterm_sent_to_supervisor']=True
            process.wait(timeout=15)
            attempt['exit_code']=process.returncode
            if observed is not None:
                try:os.kill(observed,0)
                except ProcessLookupError:attempt['observed_worker_pid_absent']=True
                else:raise RuntimeError('observed worker PID still present after supervisor exit')
            return attempt
        finally:
            if process is not None and process.poll() is None:
                attempt['cleanup_unknown']=True
                attempt['supervisor_required_hard_kill']=stop_supervisor(process)
                summary['ownership_audit_required']=True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--expected-script-sha256',required=True)
    args=parser.parse_args()
    require(digest(Path(__file__))==args.expected_script_sha256,'gate script hash mismatch')
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    summary={'schema':'diagonal-residual-checkpoint-host-gate-v1','status':'incomplete',
             'gate_script_sha256':args.expected_script_sha256,'source_hashes':EXPECTED_SOURCES,
             'oracle_evidence_sha256':ORACLE_SHA,'output_dir':str(out),'n_values':[3,5],
             'witness_order_observed':False,'attempts':[],'successful_runs':[]}
    started=time.monotonic()
    try:
        require(guard.hashes()==EXPECTED_SOURCES,'source changed before gate')
        require(digest(ORACLE)==ORACLE_SHA,'saved tiny oracle evidence mismatch')
        oracle={row['n']:set(row['full_certificate_hashes']) for row in
                read_json(ORACLE)['checks']['independent_all_prefix_oracle'] if row['n'] in (3,5)}
        initial_n5=None
        for n,total,count in ((3,19,4),(5,192,16)):
            checkpoint=out/f'n{n}.frontier.json';pin=None;all_witnesses=[];stages=[]
            for name,quota in (('initial',1),('resume',1000)):
                report_path=out/f'n{n}-{name}.report.json'
                attempt=run_stage(command(n,checkpoint,report_path,quota,pin),out/f'n{n}-{name}',summary)
                report=read_json(report_path);check_helper(report)
                require(attempt['exit_code']==0,'supervisor unsuccessful')
                require(report['previous_checkpoint_sha256']==pin,'report predecessor mismatch')
                require(report['accepted_checkpoint_sha256']==report['published_checkpoint_sha256']==digest(checkpoint),
                        'checkpoint not accepted exactly')
                data=identity(checkpoint,n)
                require(data['previous_checkpoint_sha256']==pin,'checkpoint predecessor mismatch')
                wr=report['worker_result']
                require(wr['nodes_total']==data['nodes'] and wr['witness_visits_total']==data['witness_visits'] and
                        wr['slice_index']==data['slice_index'] and wr['slice_counts']==data['slice_counts'],
                        'report counters mismatch')
                expected_nodes=1 if name=='initial' else total
                require(wr['nodes_total']==expected_nodes and wr['nodes_this_run']==(1 if name=='initial' else total-1),
                        'unexpected logical node counts')
                require(report['status']==('node_limit' if name=='initial' else 'all_declared_slices_exhausted') and
                        report['complete']==(name=='resume'),'unexpected lifecycle status')
                if name=='resume':
                    require(data['slice_index']==n*n and data['frames']==[] and data['witness_visits']==count,
                            'terminal frontier mismatch')
                items=witnesses(report,n);all_witnesses.extend(items)
                snapshot=out/f'n{n}-{name}.checkpoint.json';snapshot.write_bytes(raw(checkpoint))
                if n==5 and name=='initial':initial_n5=snapshot
                pin=digest(checkpoint)
                stages.append({'report':str(report_path),'report_sha256':digest(report_path),
                               'checkpoint':str(snapshot),'checkpoint_sha256':pin,'guard':report['guard']})
            hashes=[item['normalized_sha256'] for item in all_witnesses]
            require(len(hashes)==len(set(hashes))==count and set(hashes)==oracle[n],
                    'witness distinct set differs from saved independent tiny oracle')
            summary['successful_runs'].append({'n':n,'nodes_total':total,'witness_count':count,
                                               'stages':stages,'witnesses_sorted_by_hash':sorted(all_witnesses,key=lambda w:w['normalized_sha256'])})
        require(initial_n5 is not None,'missing cancellation starting checkpoint')
        checkpoint=out/'n5-cancel.frontier.json';checkpoint.write_bytes(raw(initial_n5));pin=digest(checkpoint)
        report_path=out/'n5-cancel.report.json'
        attempt=run_stage(command(5,checkpoint,report_path,1000,pin),out/'n5-cancel',summary,cancel=True)
        report=read_json(report_path);check_helper(report,'cancelled')
        require(attempt['exit_code']==2 and report['status']=='cancelled' and not report['complete'],
                'cancellation not rejected')
        require(report['previous_checkpoint_sha256']==pin and
                report['accepted_checkpoint_sha256'] is None and report['published_checkpoint_sha256'] is None,
                'cancelled frontier promoted')
        require(digest(checkpoint)==pin,'cancelled checkpoint changed');identity(checkpoint,5)
        summary['cancellation']={'report':str(report_path),'report_sha256':digest(report_path),
                                 'checkpoint_sha256':pin,'guard':report['guard'],
                                 'observed_worker_pid':attempt['observed_worker_pid'],'observed_worker_pid_absent':True}
        require(guard.hashes()==EXPECTED_SOURCES and digest(Path(__file__))==args.expected_script_sha256,
                'source changed during gate')
        require(digest(ORACLE)==ORACLE_SHA,'oracle evidence changed during gate')
        summary['status']='passed'
    except Exception as exc:
        summary.update(status='failed',error=f'{type(exc).__name__}: {exc}')
    finally:
        summary['elapsed_seconds']=time.monotonic()-started
        (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
    return 0 if summary['status']=='passed' else 2


if __name__=='__main__':sys.exit(main())
