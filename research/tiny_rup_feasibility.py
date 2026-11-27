"""TINY proof feasibility only; standard-library RUP checker separate from producer."""
import hashlib,itertools,json,shutil,time
from pathlib import Path

def check_rup(cnf, proof_lines, variables, *, seconds=1, byte_cap=65536, line_cap=1000):
    start=time.monotonic();deadline=start+seconds;visits=0
    if len(proof_lines)>line_cap or sum(len(s.encode('ascii'))+1 for s in proof_lines)>byte_cap:
        raise ValueError('proof capacity')
    def clause(raw):
        if any(type(v)is not int or not 0<abs(v)<=variables for v in raw):raise ValueError('literal domain')
        return tuple(sorted(set(raw)))
    database=[clause(c) for c in cnf];additions=deletions=0;empty_seen=False
    for line in proof_lines:
        if time.monotonic()>=deadline:raise TimeoutError
        tokens=line.split();delete=bool(tokens and tokens[0]=='d');tokens=tokens[1:] if delete else tokens
        if not tokens:raise ValueError('empty proof line')
        integers=[int(t) for t in tokens]
        if integers[-1]!=0 or 0 in integers[:-1]:raise ValueError('bad terminator')
        candidate=clause(integers[:-1])
        if delete:
            if candidate not in database:raise ValueError('deletion not present')
            database.remove(candidate);deletions+=1;continue
        # Negate the candidate and derive contradiction solely by unit propagation.
        assignment={};conflict=False
        def assign(literal):
            variable=abs(literal);value=literal>0
            if variable in assignment:return assignment[variable]==value
            assignment[variable]=value;return True
        for literal in candidate:
            if not assign(-literal):conflict=True;break
        changed=True
        while not conflict and changed:
            changed=False
            for current in database:
                visits+=1
                if time.monotonic()>=deadline:raise TimeoutError
                open_literals=[];satisfied=False
                for lit in current:
                    value=assignment.get(abs(lit))
                    if value is None:open_literals.append(lit)
                    elif value==(lit>0):satisfied=True;break
                if satisfied:continue
                if not open_literals:conflict=True;break
                if len(open_literals)==1:
                    if not assign(open_literals[0]):conflict=True;break
                    changed=True
        if not conflict:raise ValueError('addition is not RUP')
        database.append(candidate);additions+=1
        if not candidate:empty_seen=True
    if not empty_seen:raise ValueError('no checked empty clause')
    return {'accepted':True,'additions':additions,'deletions':deletions,'clause_visits':visits,'elapsed_seconds':time.monotonic()-start}

if __name__=='__main__':
    from pysat.solvers import Glucose3
    results=[]
    cube=[[s*v for s,v in zip(signs,(1,2,3))] for signs in itertools.product((-1,1),repeat=3)]
    fixtures=[('three_variable_cube',cube,3),('unit_contradiction',[[1],[-1]],1)]
    for name,cnf,n in fixtures:
        with Glucose3(with_proof=True) as solver:
            for c in cnf:solver.add_clause(c)
            answer=solver.solve();proof=solver.get_proof()
        assert answer is False
        checked=check_rup(cnf,proof,n)
        results.append({'fixture':name,'variables':n,'cnf':cnf,'proof':proof,'checker':checked})
    with Glucose3(bootstrap_with=[[1],[-1]],with_proof=True) as solver:
        bootstrap_answer=solver.solve();bootstrap_proof=solver.get_proof()
    negatives={}
    for label,cnf,proof,n in [
      ('invalid_empty_for_sat',[[1,2]],['0'],2),
      ('cube_missing_learned_steps',cube,['0'],3),
      ('missing_empty',cube,results[0]['proof'][:-1],3),
      ('malformed_literal',[[1],[-1]],['2 0','0'],1),
      ('absent_deletion',[[1],[-1]],['d 1 -1 0','0'],1)]:
        try:check_rup(cnf,proof,n)
        except ValueError as exc:negatives[label]=str(exc)
        else:raise AssertionError('negative unexpectedly accepted '+label)
    # Exercise actual deletion handling independently of native trace choices.
    deletion=check_rup([[1,2],[1,-2],[-1,2],[-1,-2]],['1 0','d 1 2 0','0'],2)
    root=Path('/Users/dejain/nvidia/oss/work/no-three-in-line-research')
    result={'scope':'TINY ONLY: two native UNSAT fixtures, all at most three variables/eight clauses; no n79 replay or new solver installation','python_sat_version':'1.8.dev24','checker_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixtures':results,'bootstrap_unit_contradiction':{'answer':bootstrap_answer,'proof':bootstrap_proof,'implication':'construct empty with proof enabled before adding clauses, because installed constructor adds bootstrap clauses before enabling trace'},'negative_tests_rejected':negatives,'synthetic_deletion_case':deletion,'external_checker_executables_on_PATH':{n:shutil.which(n) for n in ['drat-trim','gratgen','gratchk','gratcheck','lrat-check','lrat-checker','cake_lpr']}}
    out=root/'data/pysat-glucose3-rup-tiny-feasibility.json';out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,indent=2));print('artifact_sha256',hashlib.sha256(out.read_bytes()).hexdigest())
