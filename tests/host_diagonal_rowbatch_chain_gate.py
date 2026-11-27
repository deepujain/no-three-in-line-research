"""Real-host n=3/n=5 row-batch chain lifecycle gate; never runs n=79.

Provide a new output directory. All reports, checkpoints and the summary remain
there for independent inspection. Uses the real owned-process helper and ps.
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
from research.diagonal_rowbatch_checkpoint import run as initial
from research.diagonal_rowbatch_chain import source_hashes
from research.diagonal_secant_checkpoint import encode,sha
from research.diagonal_secant_dfs_fast import pair_orbits
from src.verify import verify_certificate,verify_certificate_bruteforce


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def check_identity(path,n,sources):
    frontier=json.loads(path.read_text());identity=frontier['identity']
    assert identity['format']=='diagonal-rowbatch-frontier-v1' and identity['n']==n
    assert identity['deficits']==identity['diagonals']==list(range(n))
    assert identity['branch_order']=='minimum-viable-row-then-lexicographic-unordered-batch-v1'
    assert identity['orbit_order_sha256']==sha(encode(pair_orbits(n)))
    assert identity['source_hashes']=={'rowbatch_checkpoint':sources['checkpoint_core'],
        'tiny_reference':sources['tiny_reference'],'checkpoint_utilities':sources['checkpoint_utilities'],
        'fast_core':sources['fast_core'],'original_core':sources['original_core'],'verifier':sources['verifier']}


def command(n,checkpoint,pin,ledger,max_nodes,max_invocations):
    return [sys.executable,str(ROOT/'research/diagonal_rowbatch_chain.py'),
            '--n',str(n),'--checkpoint',str(checkpoint),'--expected-sha256',pin,'--ledger-dir',str(ledger),
            '--max-nodes',str(max_nodes),'--seconds','120','--invocation-seconds','10',
            '--max-invocations',str(max_invocations)]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    out=parser.parse_args().output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    summary={'status':'incomplete','output_dir':str(out),'n_values':[3,5]}
    process=None;worker_pid=None
    try:
        successes=[];sources=source_hashes()
        for n in (3,5):
            cp=out/f'n{n}.frontier.json';pin=initial(n,10,1,cp)['checkpoint_sha256']
            ledger_dir=out/f'n{n}-ledger';args=command(n,cp,pin,ledger_dir,3 if n==3 else 1000,26)
            result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=20)
            (out/f'n{n}.stdout').write_text(result.stdout);(out/f'n{n}.stderr').write_text(result.stderr)
            ledger=json.loads((ledger_dir/'ledger.json').read_text());item=ledger['invocations'][-1]
            report=json.loads(Path(item['report']).read_text());g=report['guard']
            assert result.returncode==0 and ledger['status']=='witness' and item['status']=='accepted'
            assert ledger['source_hashes']==sources and len(ledger['invocations']) >= (2 if n==3 else 1)
            assert g['gate_status']=='exited' and g['cleanup_status']=='clean' and g['rss_samples']>0 and g['source_stable']
            assert ledger['current_accepted_sha256']==report['accepted_checkpoint_sha256']==digest(cp)
            check_identity(cp,n,sources)
            witness_paths=[]
            for step in ledger['invocations']:
                step_report=json.loads(Path(step['report']).read_text())
                assert step['status']=='accepted' and step_report['source_hashes']=={k:v for k,v in sources.items() if k!='chain'}
                witness_paths.extend(Path(step_report['witness_dir']).glob('*.json'))
            assert witness_paths and (n!=5 or len(witness_paths)==16)
            for path in witness_paths:
                cert=json.loads(path.read_text());checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
                assert all(c['valid'] and c['point_count']==2*n-1 for c in checks)
                assert {(y,x) for x,y in cert['points']}=={tuple(p) for p in cert['points']}
                assert checks[0]['normalized_sha256']==checks[1]['normalized_sha256']==path.stem
                assert cert['metadata']['method']=='diagonal_rowbatch_checkpoint' and cert['metadata']['guard_source_hashes']=={k:v for k,v in sources.items() if k!='chain'}
            marker=json.loads(Path(str(cp)+'.chain-owner.json').read_text());assert marker['status']=='closed'
            successes.append({'n':n,'command':args,'ledger_sha256':digest(ledger_dir/'ledger.json'),
                              'report_sha256':digest(Path(item['report'])),'checkpoint_sha256':digest(cp),
                              'witness_count':len(witness_paths),'peak_sampled_rss_kib':g['peak_sampled_rss_kib'],
                              'rss_samples':g['rss_samples']})
        cp5=out/'n5-cancel.frontier.json';pin5=initial(5,10,1,cp5)['checkpoint_sha256']
        args5=command(5,cp5,pin5,out/'n5-cancel-ledger',1,26)
        process=subprocess.Popen(args5,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and process.poll() is None:
            ps=subprocess.run(['ps','-axo','pid=,ppid=,args='],capture_output=True,text=True,check=True,timeout=1)
            for row in ps.stdout.splitlines():
                fields=row.strip().split(None,2)
                if len(fields)==3 and int(fields[1])==process.pid and 'diagonal_rowbatch_checkpoint_guard.py' in fields[2] and '--_worker' in fields[2]:
                    worker_pid=int(fields[0]);break
            if worker_pid is not None:break
            time.sleep(.005)
        if worker_pid is None:raise RuntimeError('did not observe an owned worker before process exit')
        os.kill(process.pid,signal.SIGTERM)
        stdout,stderr=process.communicate(timeout=15)
        (out/'n5-cancel.stdout').write_text(stdout);(out/'n5-cancel.stderr').write_text(stderr)
        ledger5=json.loads((out/'n5-cancel-ledger/ledger.json').read_text())
        marker5=json.loads(Path(str(cp5)+'.chain-owner.json').read_text())
        assert ledger5['status'] in ('rejected','cancelled') and not ledger5['complete'] and marker5['status']=='rejected'
        last5=ledger5['invocations'][-1]
        report5=json.loads(Path(last5['report']).read_text())
        assert report5['status']=='cancelled' and report5['guard']['gate_status']=='cancelled'
        assert report5['accepted_checkpoint_sha256'] is None and report5['published_checkpoint_sha256'] is None
        assert digest(cp5)==last5['expected_sha256']==ledger5['current_accepted_sha256']
        check_identity(cp5,5,sources)
        assert ledger5['source_hashes']==sources and report5['source_hashes']=={k:v for k,v in sources.items() if k!='chain'}
        assert report5['guard']['cleanup_status']=='clean' and not report5['complete']
        try:os.kill(worker_pid,0)
        except ProcessLookupError:pass
        else:raise RuntimeError('observed worker PID still present after chain exit')
        summary.update(status='passed',source_hashes=sources,successful_runs=successes,
                       n5_command=args5,n5_exit_code=process.returncode,n5_observed_worker_pid=worker_pid,
                       n5_ledger_sha256=digest(out/'n5-cancel-ledger/ledger.json'),n5_marker_status=marker5['status'],
                       n5_chain_status=ledger5['status'],n5_report_sha256=digest(Path(last5['report'])),
                       n5_guard_status=report5['guard']['gate_status'],n5_cleanup_status=report5['guard']['cleanup_status'])
    except subprocess.TimeoutExpired as exc:
        summary.update(status='failed',error=f'TimeoutExpired: {exc}',cleanup='possibly orphaned worker; ownership unknown',observed_worker_pid=worker_pid)
    except Exception as exc:
        summary.update(status='failed',error=f'{type(exc).__name__}: {exc}',observed_worker_pid=worker_pid)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                try:process.communicate(timeout=2)
                except subprocess.TimeoutExpired:pass
                summary.update(status='failed',cleanup='chain required hard kill; owned worker state unknown')
        (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
    return 0 if summary['status']=='passed' else 2


if __name__=='__main__':sys.exit(main())
