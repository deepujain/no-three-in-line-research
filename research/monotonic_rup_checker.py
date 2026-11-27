"""Bounded monotonic RUP certificate checker, independent bit-mask inference.

Deletion records change exact active-multiset bookkeeping only. Every input
clause and every checked addition remains in the inference database. No solver,
encoder or previous checker is imported. Every accepted retained clause is
entailed by the original CNF, so a checked empty addition proves that CNF UNSAT.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys


@dataclass(frozen=True)
class Limits:
    variables: int = 2645
    retained_clauses: int = 13294
    retained_literals: int = 34044
    proof_records: int = 50000
    cnf_bytes: int = 1602603
    proof_bytes: int = 8*1024*1024
    work: int = 50000000

    def __post_init__(self):
        ceilings = (2645,13294,34044,50000,1602603,8*1024*1024,50000000)
        if any(type(v) is not int or not 0 <= v <= cap for v,cap in zip(
                (self.variables,self.retained_clauses,self.retained_literals,self.proof_records,
                 self.cnf_bytes,self.proof_bytes,self.work),ceilings)):
            raise ValueError('limits must be nonnegative integers within reviewed ceilings')


class Rejected(Exception):
    pass


class Budget:
    """One charged unit per parser token/byte block and width+1 per mask clause.

    Mask operations have bounded2645-bit operands. Work is a conservative
    accounting unit, not a measured literal-visit or CPU-time claim.
    """
    def __init__(self, seconds=5, work=50000000, *, started=None, clock=time.monotonic):
        if isinstance(seconds,bool) or not math.isfinite(seconds) or not 0 < seconds <= 5:
            raise ValueError('checker duration must be in (0,5]')
        self.clock=clock; self.deadline=(clock() if started is None else started)+seconds
        self.work=0; self.limit=work

    def charge(self, amount=1):
        self.work += amount
        if self.work > self.limit: raise TimeoutError('checker work cap')
        if self.clock() >= self.deadline: raise TimeoutError('checker wall cap')


def hash_file(path, cap, budget):
    total=0; h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            budget.charge(); block=f.read(65536)
            if not block: break
            total += len(block)
            if total > cap: raise Rejected('input byte cap')
            h.update(block)
    return h.hexdigest(),total


def read_lines(path, cap, line_cap, budget):
    """Bounded bytes, complete ASCII lines, and an independently checked digest."""
    pending=b''; total=0; h=hashlib.sha256()
    with open(path,'rb') as f:
        while True:
            budget.charge(); block=f.read(65536)
            if not block: break
            total += len(block)
            if total > cap: raise Rejected('input byte cap')
            h.update(block); pending += block
            while True:
                budget.charge(); cut=pending.find(b'\n')
                if cut < 0: break
                raw,pending=pending[:cut],pending[cut+1:]
                if len(raw)>line_cap: raise Rejected('input line cap')
                try: yield raw.decode('ascii')
                except UnicodeDecodeError: raise Rejected('non-ASCII input') from None
            if len(pending)>line_cap: raise Rejected('input line cap')
        if pending: raise Rejected('unterminated input line')
    return h.hexdigest()


def parse_clause(tokens, variables, budget):
    if not tokens or tokens[-1]!='0' or len(tokens)-1>variables:
        raise Rejected('clause terminator/width')
    positive=negative=0; raw=[]
    for token in tokens[:-1]:
        budget.charge()
        if (not token or len(token)>6 or token.startswith('+')
                or not token.lstrip('-').isdigit()): raise Rejected('literal token')
        try: value=int(token)
        except ValueError: raise Rejected('literal token') from None
        if not 0 < abs(value) <= variables: raise Rejected('literal domain')
        raw.append(value)
        if value>0: positive |= 1 << (value-1)
        else: negative |= 1 << (-value-1)
    return (positive,negative),tuple(raw)


def rup(inference, candidate, budget):
    """Repeated bounded-width integer-mask propagation; candidate is not inserted."""
    positive,negative=candidate
    true_bits,false_bits=negative,positive
    if true_bits & false_bits: budget.charge(); return True
    while True:
        budget.charge(); before=true_bits | false_bits
        for pos,neg,width in inference:
            budget.charge(width+1)
            if pos & neg or pos & true_bits or neg & false_bits: continue
            unknown=(pos | neg) & ~(true_bits | false_bits)
            if not unknown: return True
            if not unknown & (unknown-1):
                if pos & unknown: true_bits |= unknown
                else: false_bits |= unknown
        if true_bits | false_bits == before: return False


def check_pair(cnf, proof, expected_cnf, expected_proof, seconds=5, *, limits=Limits(),
               started=None, clock=time.monotonic):
    """Return a bounded receipt on every ordinary rejection; never raise for proof failure."""
    budget=Budget(seconds,limits.work,started=started,clock=clock)
    receipt={'accepted':False,'closure':False,'status':'incomplete','full_parse_complete':False,
             'format':'monotonic RUP; exact active multiset deletion validation',
             'expected_cnf_sha256':expected_cnf,'expected_proof_sha256':expected_proof,
             'records':0,'additions':0,'deletions':0,'checked_empty_line':None,
             'failure_line':None,'failure_clause':None,'retained_clauses':0,'retained_literals':0,
             'work_unit':'parser token/block and mask-clause width+1; bounded2645-bit operands'}
    proof_line=None; raw_clause=None
    try:
        actual_cnf,cnf_size=hash_file(cnf,limits.cnf_bytes,budget)
        actual_proof,proof_size=hash_file(proof,limits.proof_bytes,budget)
        receipt.update(cnf_sha256=actual_cnf,proof_sha256=actual_proof,cnf_bytes=cnf_size,proof_bytes=proof_size)
        if actual_cnf!=expected_cnf or actual_proof!=expected_proof: raise Rejected('preflight digest mismatch')
        source=read_lines(cnf,limits.cnf_bytes,7*limits.variables+32,budget)
        try: header=next(source).split()
        except StopIteration: raise Rejected('missing CNF header') from None
        if (len(header)!=4 or header[:2]!=['p','cnf'] or any(len(t)>10 or not t.isdigit() for t in header[2:])):
            raise Rejected('CNF header')
        variables,declared=map(int,header[2:])
        if variables>limits.variables or declared>limits.retained_clauses: raise Rejected('CNF dimensions cap')
        inference=[]; active=Counter(); active_count=0
        while True:
            budget.charge()
            try: line=next(source)
            except StopIteration as done:
                if done.value!=expected_cnf: raise Rejected('CNF parse digest mismatch')
                break
            key,raw=parse_clause(line.split(),variables,budget)
            receipt['retained_clauses']+=1; receipt['retained_literals']+=len(raw)
            if receipt['retained_clauses']>declared or receipt['retained_literals']>limits.retained_literals:
                raise Rejected('CNF storage/count cap')
            inference.append((*key,len(raw))); active[key]+=1; active_count+=1
        if receipt['retained_clauses']!=declared: raise Rejected('CNF clause count mismatch')
        receipt['variables']=variables; source=read_lines(proof,limits.proof_bytes,7*limits.variables+32,budget)
        while True:
            raw_clause=None; proof_line=receipt['records']+1; budget.charge()
            try: line=next(source)
            except StopIteration as done:
                proof_line=None
                if done.value!=expected_proof: raise Rejected('proof parse digest mismatch')
                break
            receipt['records']=proof_line
            if proof_line>limits.proof_records: raise Rejected('proof record cap')
            tokens=line.split(); deletion=bool(tokens and tokens[0]=='d')
            key,raw_clause=parse_clause(tokens[1:] if deletion else tokens,variables,budget)
            if deletion:
                if active.get(key,0)==0: raise Rejected('nonexistent/excess deletion')
                active[key]-=1; active_count-=1; receipt['deletions']+=1
                if not active[key]: del active[key]
            else:
                if (receipt['retained_clauses']+1>limits.retained_clauses
                        or receipt['retained_literals']+len(raw_clause)>limits.retained_literals):
                    raise Rejected('retained inference storage cap')
                if not rup(inference,key,budget): raise Rejected('non-RUP addition')
                inference.append((*key,len(raw_clause))); active[key]+=1; active_count+=1
                receipt['retained_clauses']+=1; receipt['retained_literals']+=len(raw_clause); receipt['additions']+=1
                if not raw_clause and receipt['checked_empty_line'] is None: receipt['checked_empty_line']=proof_line
        # Complete parser/hash validation remains mandatory after a checked empty.
        receipt['full_parse_complete']=True; proof_line=None; raw_clause=None
        if receipt['checked_empty_line'] is None: raise Rejected('missing checked empty addition')
        budget.charge(); receipt.update(accepted=True,closure=True,status='checked_monotonic_rup_unsat',active_clauses=active_count)
    except (Rejected,TimeoutError,OSError,ValueError) as error:
        receipt.update(status='timeout' if isinstance(error,TimeoutError) else 'rejected',
                       error=f'{type(error).__name__}: {error}',failure_line=proof_line,
                       failure_clause=list(raw_clause) if raw_clause is not None else None)
    receipt['work']=budget.work
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cnf',type=Path,required=True); p.add_argument('--proof',type=Path,required=True)
    p.add_argument('--cnf-sha256',required=True); p.add_argument('--proof-sha256',required=True)
    p.add_argument('--seconds',type=float,default=5); a=p.parse_args()
    result=check_pair(a.cnf,a.proof,a.cnf_sha256,a.proof_sha256,a.seconds,started=ENTRY_STARTED)
    print(json.dumps(result,sort_keys=True)); return 0 if result['accepted'] else 2


if __name__=='__main__': sys.exit(main())
