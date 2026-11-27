"""One stdlib checker call in the owned worker; no child or process observer.

Actual dispatch requires independent reviews and a separate Root allocation.
Imports have no process/resource side effects. main sets the regular-log cap.
"""
import time
ENTRY_STARTED=time.monotonic()
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import stat
import sys

ROOT=Path(__file__).resolve().parents[1]
CHECKER=ROOT/'research/monotonic_rup_checker.py'
PARENT=ROOT/'research/direct_owned_proof_acceptance.py'
CHECKER_SHA='09e85dced3d7cf572cad4b75f9b4fab50dd051f4fe9f95ded58981de6ded5c90'
RUNTIME=ROOT/'data/fixed-pool-boolean-scaffold-runtime-pins.json'
RUNTIME_SHA='1bac1b03987d26c32a58575b66f569cf5d5561adc4f0952dfb96ade82d8b5f8a'
CNF=ROOT/'data/fixed-pool-boolean-scaffold157-v1/scaffold.cnf'
PROOF=ROOT/'data/fixed-pool-boolean-scaffold157-v1/scaffold.rup'
CNF_SHA='855b54b7c6b05f181ff3c9153ff03c44d310747874577f520ed960a007670fc9'
PROOF_SHA='4c1fc7141a5c889029db91c0dce0255463f472f4db60192fbfc4d016f65d439e'
LOG_CAP=65536
PIN_FILE_CAP=64*1024*1024
MANIFEST_CAP=65536
PIN_COUNT_CAP=512


class Deadline:
    def __init__(self,seconds=4,*,started=None,clock=time.monotonic):
        if isinstance(seconds,bool) or not math.isfinite(seconds) or not 0<seconds<=5:
            raise ValueError('invalid finite deadline')
        self.clock=clock; self.started=clock() if started is None else started; self.end=self.started+seconds

    def check(self):
        if self.clock()>=self.end: raise TimeoutError('direct proof management deadline')


def digest(path,deadline):
    h=hashlib.sha256(); total=0
    deadline.check()
    with open(path,'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('pin is not a regular file')
        while True:
            deadline.check(); block=f.read(65536)
            if not block: break
            total+=len(block)
            if total>PIN_FILE_CAP: raise ValueError('pinned file byte cap')
            h.update(block)
    deadline.check(); return h.hexdigest()


def read_manifest(path,expected,deadline):
    deadline.check()
    with open(path,'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('manifest is not a regular file')
        raw=f.read(MANIFEST_CAP+1)
    deadline.check()
    if len(raw)>=MANIFEST_CAP or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('manifest cap/digest mismatch')
    value=json.loads(raw)
    if type(value) is not dict: raise ValueError('manifest must be an object')
    return value


def normalize_pins(source,runtime,deadline):
    result={}
    for mapping in (source,runtime):
        if type(mapping) is not dict or len(mapping)>PIN_COUNT_CAP: raise ValueError('pin count/format')
        for name,sha in mapping.items():
            deadline.check()
            if (type(name) is not str or type(sha) is not str or len(sha)!=64
                    or any(c not in '0123456789abcdef' for c in sha)):
                raise ValueError('pin entry format')
            path=str((ROOT/name).absolute())
            if path in result and result[path]!=sha: raise ValueError('conflicting path pins')
            result[path]=sha
            if len(result)>PIN_COUNT_CAP: raise ValueError('combined pin count cap')
    return result


def verify_pins(pins,deadline):
    if not pins or len(pins)>PIN_COUNT_CAP: raise ValueError('missing/excess pins')
    for path,sha in pins.items():
        deadline.check()
        if digest(path,deadline)!=sha: raise ValueError('source/input pin changed: '+path)


def load_context(source_manifest,source_sha,deadline,*,cnf=CNF,proof=PROOF,cnf_sha=CNF_SHA,proof_sha=PROOF_SHA):
    source=read_manifest(source_manifest,source_sha,deadline)
    runtime=read_manifest(RUNTIME,RUNTIME_SHA,deadline)
    if (runtime.get('interpreter')!=sys.executable
            or runtime.get('resolved_interpreter')!=str(Path(sys.executable).resolve())):
        raise ValueError('interpreter origin mismatch')
    pins=normalize_pins(source,runtime['pins'],deadline)
    required={str(Path(__file__).resolve()),str(PARENT),str(CHECKER),str(cnf),str(proof),
              str(Path(sys.executable).resolve()),str(RUNTIME)}
    if not required<=pins.keys(): raise ValueError('missing reviewed mandatory pins')
    if (pins[str(CHECKER)]!=CHECKER_SHA or pins[str(cnf)]!=cnf_sha
            or pins[str(proof)]!=proof_sha or pins[str(RUNTIME)]!=RUNTIME_SHA):
        raise ValueError('wrong frozen checker/input/runtime identity')
    pins[str(Path(source_manifest).resolve())]=source_sha
    if len(pins)>PIN_COUNT_CAP: raise ValueError('combined pin count cap')
    verify_pins(pins,deadline)
    return pins


def owned_log_identity():
    identity={'pid':os.getpid(),'pgid':os.getpgrp(),'sid':os.getsid(0)}
    if not identity['pid']==identity['pgid']==identity['sid']:
        raise ValueError('direct worker must be the owned session/group root')
    a,b=os.fstat(1),os.fstat(2)
    if (not stat.S_ISREG(a.st_mode) or not stat.S_ISREG(b.st_mode)
            or (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino)):
        raise ValueError('stdout/stderr must share the owned regular log')
    identity['shared_regular_log']=True
    return identity


def configure_log_cap():
    resource.setrlimit(resource.RLIMIT_FSIZE,(LOG_CAP,LOG_CAP))


def load_checker():
    # Use the exact verified file; do not search another research namespace.
    spec=importlib.util.spec_from_file_location('direct_pinned_monotonic_rup_checker',CHECKER)
    if spec is None or spec.loader is None: raise ValueError('pinned checker loader unavailable')
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    if Path(module.__file__).resolve()!=CHECKER: raise ValueError('checker import origin changed')
    return module.check_pair


def run_pair(cnf,proof,cnf_sha,proof_sha,pins,source_sha,*,started=None,seconds=4,
             clock=time.monotonic):
    """Tiny-testable direct path; actual main supplies only the fixed saved pair."""
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 0<seconds<=4:
        raise ValueError('direct checker interval must be in (0,4]')
    started=clock() if started is None else started; deadline=Deadline(seconds,started=started,clock=clock)
    result={'protocol':'direct-owned-monotonic-rup-v1','accepted':False,'closure':False,'status':'incomplete',
            'checker_invocations':0,'sat_invocations':0,'source_pins_sha256':source_sha,
            'checker_sha256':CHECKER_SHA,'checker_origin':str(CHECKER),'runtime_manifest_sha256':RUNTIME_SHA,
            'pins_verified_before':False,'pins_verified_after':False,'identity_valid':False,
            'cooperative_seconds':seconds,'log_cap_bytes':LOG_CAP,
            'scope':'Only exact fixed64-cell/246-support scaffold formula; no149 output,157 witness, '
                    'other pool, solver run or automatic continuation.'}
    try:
        deadline.check(); result['owned_identity']=owned_log_identity()
        if resource.getrlimit(resource.RLIMIT_FSIZE)!=(LOG_CAP,LOG_CAP): raise ValueError('kernel log cap missing')
        verify_pins(pins,deadline); result['pins_verified_before']=True
        if pins.get(str(CHECKER))!=CHECKER_SHA: raise ValueError('missing frozen checker pin')
        # Import only after pin verification. No solver/native adapter is imported.
        check_pair=load_checker()
        deadline.check(); result['checker_invocations']=1
        receipt=check_pair(cnf,proof,cnf_sha,proof_sha,seconds,started=started,clock=clock)
        result['proof_check']=receipt
        verify_pins(pins,deadline); result.update(pins_verified_after=True,identity_valid=True)
        deadline.check()
        if receipt.get('accepted') is True:
            if (receipt.get('closure') is not True or receipt.get('full_parse_complete') is not True
                    or type(receipt.get('checked_empty_line')) is not int or receipt['checked_empty_line']<1
                    or receipt.get('cnf_sha256')!=cnf_sha or receipt.get('proof_sha256')!=proof_sha
                    or receipt.get('status')!='checked_monotonic_rup_unsat'):
                raise ValueError('checker acceptance completeness/binding')
            result.update(accepted=True,closure=True,status='checked_direct_owned_saved_proof')
        else: result.update(status='proof_'+str(receipt.get('status','rejected')),error=receipt.get('error'))
    except Exception as error:
        result.update(accepted=False,closure=False,status='timeout' if isinstance(error,TimeoutError) else 'error',
                      error=f'{type(error).__name__}: {error}')
    result['elapsed_seconds']=clock()-started
    return result


def emit(result):
    encoded=json.dumps(result,sort_keys=True,ensure_ascii=True).encode('ascii')+b'\n'
    if len(encoded)>=LOG_CAP: raise ValueError('receipt would reach log cap')
    # Fixed bounded receipt, one regular shared log; the kernel also limits writes.
    offset=0
    while offset<len(encoded):
        count=os.write(1,encoded[offset:])
        if count<=0: raise OSError('short receipt write')
        offset+=count


def main():
    configure_log_cap()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-pins',type=Path,required=True); p.add_argument('--source-pins-sha256',required=True)
    p.add_argument('--seconds',type=float,default=4); a=p.parse_args()
    result=None
    try:
        if not 0<a.seconds<=4 or not math.isfinite(a.seconds): raise ValueError('invalid direct interval')
        owned_log_identity(); deadline=Deadline(a.seconds,started=ENTRY_STARTED)
        pins=load_context(a.source_pins,a.source_pins_sha256,deadline)
        result=run_pair(CNF,PROOF,CNF_SHA,PROOF_SHA,pins,a.source_pins_sha256,started=ENTRY_STARTED,seconds=a.seconds)
    except Exception as error:
        result={'protocol':'direct-owned-monotonic-rup-v1','accepted':False,'closure':False,'status':'preflight_error',
                'checker_invocations':0,'sat_invocations':0,'error':f'{type(error).__name__}: {error}'}
    emit(result); return 0 if result['accepted'] else 2


if __name__=='__main__': sys.exit(main())
