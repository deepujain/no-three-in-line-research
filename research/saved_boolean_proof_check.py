"""Separate one-child monotonic-RUP check of one immutable saved Boolean trace.

Source/tiny import is harmless. Actual main/run requires a separate Root
allocation and unchanged owned30s/256MiB guard. No solver imports or invocations.
"""
import time
ENTRY_STARTED=time.monotonic()
import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import boolean_scaffold_native as native

SAVED_CNF=ROOT/'data/fixed-pool-boolean-scaffold157-v1/scaffold.cnf'
SAVED_PROOF=ROOT/'data/fixed-pool-boolean-scaffold157-v1/scaffold.rup'
CNF_SHA='855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9'
PROOF_SHA='4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e'
CHECKER=ROOT/'research/monotonic_rup_checker.py'


def atomic(path,value):
    fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(value,f,sort_keys=True,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        Path(temp).unlink(missing_ok=True)


def execute(cnf,proof,cnf_sha,proof_sha,pins,report,deadline,check,*,clock=time.monotonic):
    """Tiny-testable one-child path. Actual caller supplies only pinned saved pair."""
    check(); native.verify_pins(pins); check()
    seconds=min(5,deadline-clock()-1)
    if seconds<=0: raise TimeoutError('no proof-only child slice before reserve')
    command=[sys.executable,str(CHECKER),'--cnf',str(cnf),'--proof',str(proof),
             '--cnf-sha256',cnf_sha,'--proof-sha256',proof_sha,'--seconds',str(seconds)]
    report['checker_invocations']+=1
    result=native.run_child(command,seconds,pins,latest_end=deadline-1); report['checker_process']=result
    if result['reason']!='exited' or not result['cleanup']['clean']:
        report.update(status='native_incomplete',error='proof child incomplete or cleanup uncertain'); return
    if result['returncode'] not in (0,2): raise ValueError('unexpected checker return code')
    receipt=json.loads(result['stdout']); report['proof_check']=receipt
    if type(receipt) is not dict or type(receipt.get('accepted')) is not bool:
        raise ValueError('checker receipt format')
    if result['returncode']!=(0 if receipt['accepted'] else 2): raise ValueError('checker status mismatch')
    if not receipt['accepted']:
        report.update(status='proof_'+str(receipt.get('status','rejected')),error=receipt.get('error')); return
    if (receipt.get('closure') is not True or receipt.get('full_parse_complete') is not True
            or type(receipt.get('checked_empty_line')) is not int or receipt['checked_empty_line']<1
            or receipt.get('cnf_sha256')!=cnf_sha or receipt.get('proof_sha256')!=proof_sha
            or receipt.get('status')!='checked_monotonic_rup_unsat'):
        raise ValueError('accepted proof receipt binding/completeness mismatch')
    check(); native.verify_pins(pins); check()
    report.update(status='checked_saved_fixed_pool_unsat',complete=True,closure=True)


def run(out,source_manifest,seconds=25,*,started=None,clock=time.monotonic):
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 0<seconds<=25:
        raise ValueError('invalid shared proof-only duration')
    start=clock() if started is None else started; deadline=start+seconds
    def check():
        if clock()>=deadline: raise TimeoutError('shared proof-only soft deadline')
    pins={}; report={'method':'saved_boolean_monotonic_rup_check','status':'incomplete','complete':False,
                     'closure':False,'checker_invocations':0,'sat_invocations':0,'shared_soft_seconds':seconds,
                     'scope':'Only the exact saved fixed64-cell/246-support scaffold CNF. '
                             'No149 diagnostic,157 witness, other pool, SAT rerun or automatic continuation.'}
    try:
        check(); sources=json.loads(Path(source_manifest).read_text())
        pins.update({str(ROOT/p):sha for p,sha in sources.items()})
        runtime=native.runtime_contract(); pins.update(runtime['pins'])
        required={str(Path(__file__).resolve()),str(CHECKER),str(Path(native.__file__).resolve()),
                  str(SAVED_CNF),str(SAVED_PROOF),str(Path(sys.executable).resolve())}
        if not required<=pins.keys() or pins[str(SAVED_CNF)]!=CNF_SHA or pins[str(SAVED_PROOF)]!=PROOF_SHA:
            raise ValueError('missing reviewed source/saved-pair pins')
        pins[str(Path(source_manifest).resolve())]=native.digest(source_manifest)
        check(); native.verify_pins(pins); check()
        execute(SAVED_CNF,SAVED_PROOF,CNF_SHA,PROOF_SHA,pins,report,deadline,check,clock=clock)
    except TimeoutError as error: report.update(status='timeout',error=str(error),complete=False,closure=False)
    except Exception as error: report.update(status='error',error=f'{type(error).__name__}: {error}',complete=False,closure=False)
    try: native.verify_pins(pins)
    except Exception as error:
        report.update(status='error',error='final pin check: '+str(error),identity_valid=False,complete=False,closure=False)
    else: report['identity_valid']=True
    report.update(pins=pins,elapsed_seconds=clock()-start); atomic(out/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--source-pins',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=25); a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.output_dir,a.source_pins,a.seconds,started=ENTRY_STARTED)
    print(json.dumps(result,sort_keys=True)); return 0 if result['complete'] else 2


if __name__=='__main__': sys.exit(main())
