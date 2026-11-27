"""Independent parent-side acceptance of direct-owned proof output.

The owned worker's JSON never suffices: command, complete regular log, clean
five-second/256MiB guard receipt and independent final pins must all agree.
No process is launched and no proof inference is performed by this module.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import direct_owned_saved_proof as direct


def build_command(source_manifest,source_sha):
    return [sys.executable,str(Path(direct.__file__).resolve()),'--source-pins',
            str(Path(source_manifest).resolve()),'--source-pins-sha256',source_sha,'--seconds','4']


def number(value):
    return type(value) in (int,float) and math.isfinite(value)


def integer(value,low,high):
    return type(value) is int and low<=value<=high


def validate_receipt(job,raw,expected_argv,source_sha,cnf_sha,proof_sha):
    """Pure structure/binding checks; caller additionally verifies actual pins."""
    if type(job) is not dict or job.get('status')!='completed' or job.get('argv')!=expected_argv:
        raise ValueError('owned job/command mismatch')
    gate=job.get('gate')
    if type(gate) is not dict: raise ValueError('missing independent owned receipt')
    if (gate.get('gate_status')!='exited' or type(gate.get('returncode')) is not int or gate['returncode']!=0
            or gate.get('cleanup_status')!='clean' or gate.get('cleanup_error') is not None
            or gate.get('monitor_error') is not None or gate.get('trigger_gate_status') is not None):
        raise ValueError('owned exit/monitor/cleanup failed')
    if (gate.get('seconds_limit')!=5 or gate.get('rss_limit_mib')!=256
            or not number(gate.get('elapsed_seconds')) or not 0<gate['elapsed_seconds']<5
            or not integer(gate.get('peak_sampled_rss_kib'),1,256*1024)
            or not integer(gate.get('rss_samples'),1,1000000)
            or not number(gate.get('cleanup_elapsed_seconds')) or not 0<=gate['cleanup_elapsed_seconds']<=1):
        raise ValueError('owned time/RSS/cleanup evidence invalid')
    if type(raw) is not bytes or not 0<len(raw)<direct.LOG_CAP or not raw.endswith(b'\n'):
        raise ValueError('incomplete/cap-reaching owned log')
    try: receipt=json.loads(raw.decode('ascii'))
    except (UnicodeDecodeError,json.JSONDecodeError): raise ValueError('malformed owned JSON') from None
    if type(receipt) is not dict: raise ValueError('owned receipt must be an object')
    if (receipt.get('protocol')!='direct-owned-monotonic-rup-v1'
            or receipt.get('accepted') is not True or receipt.get('closure') is not True
            or receipt.get('status')!='checked_direct_owned_saved_proof'
            or type(receipt.get('checker_invocations')) is not int or receipt['checker_invocations']!=1
            or type(receipt.get('sat_invocations')) is not int or receipt['sat_invocations']!=0
            or receipt.get('pins_verified_before') is not True or receipt.get('pins_verified_after') is not True
            or receipt.get('identity_valid') is not True or receipt.get('source_pins_sha256')!=source_sha
            or receipt.get('checker_sha256')!=direct.CHECKER_SHA
            or receipt.get('checker_origin')!=str(direct.CHECKER)
            or receipt.get('runtime_manifest_sha256')!=direct.RUNTIME_SHA
            or receipt.get('log_cap_bytes')!=direct.LOG_CAP):
        raise ValueError('direct receipt acceptance/source binding invalid')
    if (not number(receipt.get('cooperative_seconds')) or not 0<receipt['cooperative_seconds']<=4
            or not number(receipt.get('elapsed_seconds')) or not 0<=receipt['elapsed_seconds']<receipt['cooperative_seconds']):
        raise ValueError('cooperative interval invalid')
    identity=receipt.get('owned_identity')
    if (type(identity) is not dict or not integer(identity.get('pid'),1,2**31-1)
            or type(identity.get('pgid')) is not int or type(identity.get('sid')) is not int
            or not identity['pid']==identity['pgid']==identity['sid']
            or identity.get('shared_regular_log') is not True):
        raise ValueError('direct worker owned-root/log identity invalid')
    proof=receipt.get('proof_check')
    if (type(proof) is not dict or proof.get('accepted') is not True or proof.get('closure') is not True
            or proof.get('status')!='checked_monotonic_rup_unsat' or proof.get('full_parse_complete') is not True
            or proof.get('cnf_sha256')!=cnf_sha or proof.get('proof_sha256')!=proof_sha
            or proof.get('expected_cnf_sha256')!=cnf_sha or proof.get('expected_proof_sha256')!=proof_sha
            or proof.get('failure_line') is not None or proof.get('failure_clause') is not None
            or not integer(proof.get('records'),1,50000)
            or not integer(proof.get('checked_empty_line'),1,proof['records'])
            or not integer(proof.get('retained_clauses'),1,13294)
            or not integer(proof.get('retained_literals'),0,34044)
            or not integer(proof.get('work'),1,50000000)
            or not integer(proof.get('cnf_bytes'),1,1602603)
            or not integer(proof.get('proof_bytes'),1,8*1024*1024)):
        raise ValueError('proof completeness/hash/cap receipt invalid')
    return receipt


def accept_actual(job,log_path,source_manifest,source_sha):
    """Root-side post-guard check. Returns rejection on any failed condition."""
    result={'accepted':False,'closure':False,'status':'rejected',
            'source_pins_sha256':source_sha,'checker_sha256':direct.CHECKER_SHA,
            'cnf_sha256':direct.CNF_SHA,'proof_sha256':direct.PROOF_SHA,
            'scope':'Only exact fixed64-cell/246-support scaffold CNF. No149 output,157 witness or other pool.'}
    try:
        deadline=direct.Deadline(5)
        pins=direct.load_context(source_manifest,source_sha,deadline)
        deadline.check()
        with open(log_path,'rb') as log:
            if not stat.S_ISREG(os.fstat(log.fileno()).st_mode): raise ValueError('owned log not regular')
            raw=log.read(direct.LOG_CAP+1)
        deadline.check()
        if 0<len(raw)<direct.LOG_CAP:
            try: result['worker_receipt']=json.loads(raw.decode('ascii'))
            except (UnicodeDecodeError,json.JSONDecodeError): pass
        receipt=validate_receipt(job,raw,build_command(source_manifest,source_sha),source_sha,direct.CNF_SHA,direct.PROOF_SHA)
        direct.verify_pins(pins,deadline); deadline.check()
        result.update(accepted=True,closure=True,status='certified_saved_fixed_pool_unsat',
                      independent_parent_pins_verified=True,owned_gate=job['gate'],worker_receipt=receipt,
                      log_sha256=hashlib.sha256(raw).hexdigest(),log_bytes=len(raw),
                      canonical_guard_sha256=hashlib.sha256(json.dumps(job['gate'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
    except Exception as error: result['error']=f'{type(error).__name__}: {error}'
    return result
