"""Independent bounded ASCII RUP checker; no solver or encoder imports.

Each addition must follow by unit propagation under its negation. Deletions
are exact multiset deletions. Acceptance requires a checked empty addition.
This deliberately simple checker may exhaust its time/work cap on large input.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

CNF_CAP = 1602603
PROOF_CAP = 8*1024*1024
VAR_CAP = 2645
CLAUSE_CAP = 89957
LITERAL_CAP = 237112
ACTIVE_CLAUSES = 150000
ACTIVE_LITERALS = 500000
RECORD_CAP = 50000
WORK_CAP = 50000000


class Budget:
    def __init__(self, seconds=5, work=WORK_CAP):
        self.deadline = time.monotonic()+seconds; self.work = 0; self.limit = work

    def check(self, amount=0):
        self.work += amount
        if self.work > self.limit or time.monotonic() >= self.deadline:
            raise TimeoutError('checker time/work cap')


def lines(path, cap, budget):
    """At most one bounded clause line and one 64KiB buffer in flight."""
    h = hashlib.sha256(); total = 0; pending = b''
    with open(path, 'rb') as f:
        while block := f.read(65536):
            budget.check(); total += len(block)
            if total > cap: raise ValueError('input byte cap')
            h.update(block); pending += block
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                if len(line) > 7*VAR_CAP+32: raise ValueError('line cap')
                try: yield line.decode('ascii')
                except UnicodeDecodeError: raise ValueError('non-ASCII input') from None
            if len(pending) > 7*VAR_CAP+32: raise ValueError('line cap')
        if pending: raise ValueError('unterminated input line')
    return h.hexdigest()


def literal(token, variables):
    if not token or token.startswith('+') or not token.lstrip('-').isdigit():
        raise ValueError('invalid literal token')
    if len(token) > 6: raise ValueError('literal token cap')
    v = int(token)
    if not 0 < abs(v) <= variables: raise ValueError('literal domain')
    return v


def clause(tokens, variables):
    if not tokens or tokens[-1] != '0' or len(tokens)-1 > variables:
        raise ValueError('clause terminator/width')
    values = [literal(t, variables) for t in tokens[:-1]]
    return tuple(sorted(set(values))), len(values)


def load_cnf(path, budget):
    source = lines(path, CNF_CAP, budget)
    try: header = next(source).split()
    except StopIteration: raise ValueError('missing header') from None
    if len(header) != 4 or header[:2] != ['p', 'cnf'] or not all(t.isdigit() for t in header[2:]):
        raise ValueError('invalid DIMACS header')
    variables, expected = map(int, header[2:])
    if not 0 <= variables <= VAR_CAP or not 0 <= expected <= CLAUSE_CAP: raise ValueError('CNF dimensions')
    database = Counter(); count = total = 0
    while True:
        budget.check()
        try: line = next(source)
        except StopIteration as done:
            sha = done.value; break
        c, length = clause(line.split(), variables)
        count += 1; total += length
        if count > expected or total > LITERAL_CAP: raise ValueError('CNF count cap')
        database[c] += 1
    if count != expected: raise ValueError('CNF clause count')
    return variables, database, sha, total


def rup(database, added, budget):
    values = {}
    for v in added:
        key, value = abs(v), v < 0
        if key in values and values[key] != value: return True
        values[key] = value
    while True:
        changed = False
        for c in database:
            budget.check(len(c)+1)
            unit = None; unknown = 0; satisfied = False
            for v in c:
                current = values.get(abs(v))
                if current is None: unit = v; unknown += 1
                elif current == (v > 0): satisfied = True; break
            if satisfied: continue
            if not unknown: return True
            if unknown == 1:
                values[abs(unit)] = unit > 0; changed = True
        if not changed: return False


def check_proof(cnf, proof, cnf_sha, proof_sha, seconds=5, work=WORK_CAP):
    if not 0 < seconds <= 5: raise ValueError('checker duration')
    budget = Budget(seconds, work)
    variables, db, actual_cnf, literal_count = load_cnf(cnf, budget)
    if actual_cnf != cnf_sha: raise ValueError('CNF digest mismatch')
    active = sum(db.values()); records = 0; empty = False
    source = lines(proof, PROOF_CAP, budget)
    while True:
        budget.check()
        try: line = next(source)
        except StopIteration as done:
            actual_proof = done.value; break
        records += 1
        if records > RECORD_CAP: raise ValueError('proof record cap')
        tokens = line.split(); deletion = bool(tokens and tokens[0] == 'd')
        if deletion: tokens = tokens[1:]
        c, _ = clause(tokens, variables)
        if deletion:
            if not db.get(c): raise ValueError('nonexistent deletion')
            db[c] -= 1; active -= 1; literal_count -= len(c)
            if not db[c]: del db[c]
        else:
            if not rup(db, c, budget): raise ValueError('non-RUP addition')
            db[c] += 1; active += 1; literal_count += len(c)
            empty |= not c
            if active > ACTIVE_CLAUSES or literal_count > ACTIVE_LITERALS:
                raise ValueError('active proof database cap')
    if actual_proof != proof_sha: raise ValueError('proof digest mismatch')
    if not empty: raise ValueError('missing checked empty clause')
    budget.check()
    return {'accepted': True, 'cnf_sha256': actual_cnf, 'proof_sha256': actual_proof,
            'records': records, 'literal_work': budget.work, 'format': 'ASCII RUP with exact deletions'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cnf', type=Path, required=True); p.add_argument('--proof', type=Path, required=True)
    p.add_argument('--cnf-sha256', required=True); p.add_argument('--proof-sha256', required=True)
    p.add_argument('--seconds', type=float, required=True)
    a = p.parse_args()
    try:
        result = check_proof(a.cnf, a.proof, a.cnf_sha256, a.proof_sha256, a.seconds)
    except Exception as error:
        print(json.dumps({'accepted': False, 'error': f'{type(error).__name__}: {error}'})); return 2
    print(json.dumps(result, sort_keys=True)); return 0


if __name__ == '__main__': sys.exit(main())
