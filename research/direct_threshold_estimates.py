"""Tiny counts and per-support algebra only; never builds native CNFs or solves."""
import hashlib
import json
from math import comb
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.near_quarter_direct_thresholds import CapacityThresholds,shared_capacity_clauses,streamed_cnf
from src.near_quarter_model import orbit_map


def capacity_estimate(light,guards,thresholds,*,heavy=0,forced=0):
    """Clauses/auxiliaries for installed seqcounter edge forms; see native check."""
    if (any(type(v) is not int or v < 0 for v in (light,guards,heavy,forced)) or
            guards > 2 or not isinstance(thresholds,CapacityThresholds)):
        raise ValueError('invalid synthetic support counts or thresholds')
    clauses = forced + comb(heavy,2) + heavy*light + guards*heavy
    auxiliary = 0
    if light <= max(2,thresholds.atmost_two):
        clauses += comb(light,3) if light >= 3 else 0
    elif light == 3:
        clauses += 1
    else:
        clauses += 5*light-12
        auxiliary += 2*light-4
    if guards and light > 1:
        if light <= thresholds.conditional_atmost_one:
            clauses += guards*comb(light,2)
        else:
            if light == 2:
                clauses += 1
            else:
                clauses += 3*light-4
                auxiliary += light-1
            if guards > 1:
                clauses += guards
                auxiliary += 1
    return {'clauses':clauses,'auxiliaries':auxiliary}


def native_capacity_counts(light,guards,thresholds,*,heavy=0,forced=0):
    """Only a tiny Python clause list; no native solver is instantiated."""
    from pysat.formula import IDPool
    if light > 12 or heavy > 2 or forced > 2:
        raise ValueError('this evidence tool permits only tiny synthetic supports')
    coefficients = forced*[3]+heavy*[2]+light*[1]
    real = len(coefficients)+guards
    pool = IDPool(start_from=real+1)
    clauses = list(shared_capacity_clauses(enumerate(coefficients,1),
        range(len(coefficients)+1,real+1),pool,thresholds))
    return {'clauses':len(clauses),'auxiliaries':pool.top-real,
            'literals':sum(map(len,clauses))}


def tiny_formula_counts(n,thresholds):
    if type(n) is not int or n not in (3,5,7,9):
        raise ValueError('only n3/n5/n7/n9 count evidence is permitted')
    model = orbit_map(n)
    clauses = list(streamed_cnf(model,thresholds))
    real = len(model['orbits'])
    variables = max([real]+[abs(v) for clause in clauses for v in clause])
    return {'n':n,'thresholds':{'atmost_two':thresholds.atmost_two,
                              'conditional_atmost_one':thresholds.conditional_atmost_one},
            'clauses':len(clauses),'variables':variables,'auxiliaries':variables-real,
            'literals':sum(map(len,clauses)),'count_only':True,'search_performed':False}


def report():
    import pysat
    configurations = [CapacityThresholds(a,b) for a in (5,6,7) for b in (5,6,7)]
    checked = 0
    for light in range(13):
        for guards in (0,1,2):
            for heavy,forced in ((0,0),(1,0),(2,1)):
                for config in configurations+[CapacityThresholds(0,0)]:
                    predicted = capacity_estimate(light,guards,config,heavy=heavy,forced=forced)
                    actual = native_capacity_counts(light,guards,config,heavy=heavy,forced=forced)
                    if predicted != {key:actual[key] for key in predicted}:
                        raise ValueError(f'per-support estimate mismatch: {(light,guards,heavy,forced,config)}')
                    checked += 1
    support_rows = []
    for light in (5,6,7,8):
        for guards in (0,1,2):
            baseline = native_capacity_counts(light,guards,CapacityThresholds(5,5))
            for config in configurations:
                actual = native_capacity_counts(light,guards,config)
                support_rows.append({'light':light,'guards':guards,
                    'thresholds':{'atmost_two':config.atmost_two,
                                  'conditional_atmost_one':config.conditional_atmost_one},
                    **actual,'delta_clauses_from_5_5':actual['clauses']-baseline['clauses'],
                    'delta_auxiliaries_from_5_5':actual['auxiliaries']-baseline['auxiliaries']})
    return {'status':'tiny_counts_complete','search_performed':False,'native_solver_constructed':False,
            'n79_geometry_enumerated':False,'n79_build_performed':False,
            'installed_python_sat_version':pysat.__version__,
            'algebraic_native_cross_checks':checked,
            'scope':'exact tiny/per-support counts; no large-grid totals or RSS prediction',
            'source_hashes':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(__file__).resolve(),ROOT/'src/near_quarter_direct_thresholds.py',
                    ROOT/'src/near_quarter_compact.py',ROOT/'src/near_quarter_row_quota.py',
                    ROOT/'src/near_quarter_model.py',ROOT/'src/line_model.py')},
            'per_support':support_rows,
            'tiny_formulas':[tiny_formula_counts(n,c) for n in (3,5,7,9) for c in configurations]}


if __name__ == '__main__':
    print(json.dumps(report(),sort_keys=True))
