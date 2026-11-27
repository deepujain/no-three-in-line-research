"""Single from-scratch row-block pilot. Actual search requires Lead allocation.

No checkpoint input/resume API. Pure helpers support synthetic grids only until
the independently reviewed CLI receives a separate actual allocation.
"""
import time
ENTRY_STARTED = time.monotonic()
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from itertools import combinations
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce, normalized_sha256

N = 75
SEED = 275149
MAX_STEPS = 200000
CHECKPOINT_CAP = 2*1024*1024
REPORT_CAP = 1024*1024


class SearchStop(Exception):
    pass


class WeightCap(Exception):
    pass


@dataclass(frozen=True)
class Policy:
    migration_period: int = 16
    migration_samples: int = 32
    penalty_period: int = 32
    max_weight_keys: int = 65536
    max_weight: int = 65535


@dataclass(frozen=True)
class Boundary:
    n: int
    points: tuple
    index: dict
    unweighted: int
    weighted: int
    conflict_rows: tuple
    deficient_row: int
    best_points: tuple
    best_unweighted: int
    best_weighted_at_capture: int
    best_weight_epoch: int
    weights: dict
    rng_state: tuple
    stagnation: int
    logical: dict


def choose2(t): return t*(t-1)//2
def choose3(t): return t*(t-1)*(t-2)//6


def line_key(p, q):
    a, b = q[1]-p[1], p[0]-q[0]
    g = math.gcd(abs(a), abs(b))
    if not g:
        raise ValueError('line requires distinct points')
    a //= g; b //= g
    if a < 0 or (a == 0 and b < 0): a, b = -a, -b
    return (a, b, a*p[0]+b*p[1])


def _phase(work, name, check):
    work['phase'] = name; check()


def _inc(work, key, value=1):
    work[key] = work.get(key, 0)+value


def validate_points(points, n):
    if type(n) is not int or not 2 <= n <= 75: raise ValueError('grid order')
    points = tuple(sorted(map(tuple, points)))
    if len(points) != 2*n-1 or len(set(points)) != len(points): raise ValueError('cardinality/duplicates')
    if any(len(p) != 2 or any(type(v) is not int or not 0 <= v < n for v in p) for p in points):
        raise ValueError('coordinate domain')
    rows = Counter(y for _,y in points)
    if sorted(rows.get(r,0) for r in range(n)) != [1]+[2]*(n-1): raise ValueError('row capacity/deficiency')
    return points


def score_index(points, index, weights, check=lambda: None):
    raw = weighted = bad = 0
    for key, mask in index.items():
        check(); t = mask.bit_count()
        if t >= 3:
            count = choose3(t); raw += count; weighted += weights.get(key,1)*count; bad |= mask
    rows = tuple(sorted({points[i][1] for i in range(len(points)) if bad & (1 << i)}))
    return raw, weighted, rows


def build_index(points, n, weights=None, check=None, work=None):
    check = check or (lambda: None); work = {} if work is None else work
    points = validate_points(points,n); weights = {} if weights is None else weights
    _phase(work,'index_build',check); _inc(work,'indexes_started'); index = {}
    for i,j in combinations(range(len(points)),2):
        check(); key = line_key(points[i],points[j]); _inc(work,'index_pairs')
        index[key] = index.get(key,0) | (1 << i) | (1 << j)
    raw, weighted, rows = score_index(points,index,weights,check)
    if len(index) > choose2(len(points)) or not 0 <= raw <= choose3(len(points)):
        raise ValueError('index/score ceiling')
    _inc(work,'indexes_completed')
    return points,index,raw,weighted,rows


def row_costs(points, index, row, weights, n, check=None, work=None):
    check = check or (lambda: None); work = {} if work is None else work
    if type(row) is not int or not 0 <= row < n: raise ValueError('row')
    rowmask = sum(1 << i for i,p in enumerate(points) if p[1] == row)
    raw = [0]*n; weighted = [0]*n
    _phase(work,'row_costs',check)
    for (a,b,c),mask in index.items():
        check(); _inc(work,'row_line_visits'); t = (mask & ~rowmask).bit_count()
        if t < 2 or a == 0: continue
        numerator = c-b*row
        if numerator % a: continue
        x = numerator//a
        if 0 <= x < n:
            count = choose2(t); raw[x] += count; weighted[x] += weights.get((a,b,c),1)*count
    return {'unweighted': tuple(raw), 'weighted': tuple(weighted)}


def best_row_alternatives(points, row, costs, n, check=None, work=None):
    check = check or (lambda: None); work = {} if work is None else work
    old = tuple(sorted(x for x,y in points if y == row))
    if len(old) not in (1,2): raise ValueError('row size')
    choices = ((x,) for x in range(n)) if len(old) == 1 else combinations(range(n),2)
    minimum = None; ties = []
    _phase(work,'row_alternatives',check)
    for choice in choices:
        check(); _inc(work,'row_alternatives')
        if choice == old: continue
        score = sum(costs['weighted'][x] for x in choice)
        if minimum is None or score < minimum: minimum,ties = score,[choice]
        elif score == minimum: ties.append(choice)
    return minimum,ties


def _point_cost(point, others, weights, check, work):
    groups = Counter()
    for q in others:
        check(); groups[line_key(point,q)] += 1; _inc(work,'migration_incidences')
    raw = sum(choose2(t) for t in groups.values())
    weighted = sum(weights.get(key,1)*choose2(t) for key,t in groups.items())
    return raw,weighted


def migration_delta(points, donor, destination, weights, check=None, work=None):
    check = check or (lambda: None); work = {} if work is None else work
    donor,destination = tuple(donor),tuple(destination)
    if donor not in points or destination in points or donor[1] == destination[1]: raise ValueError('migration membership')
    rows = Counter(y for _,y in points)
    if rows[donor[1]] != 2 or rows[destination[1]] != 1: raise ValueError('migration rows')
    remaining = tuple(p for p in points if p != donor)
    removed = _point_cost(donor,remaining,weights,check,work)
    inserted = _point_cost(destination,remaining,weights,check,work)
    return {'unweighted': inserted[0]-removed[0], 'weighted': inserted[1]-removed[1]}


def make_boundary(points, n, rng, *, weights=None, check=None, work=None):
    check = check or (lambda: None); work = {} if work is None else work
    weights = {} if weights is None else dict(weights)
    points,index,raw,weighted,rows = build_index(points,n,weights,check,work)
    deficient = next(r for r in range(n) if sum(y == r for _,y in points) == 1)
    logical = dict(transitions=0,row_transitions=0,migration_transitions=0,penalty_events=0,
                   best_improvements=0,best_improvements_after_penalty=0,raw_down=0,raw_neutral=0,raw_up=0)
    return Boundary(n,points,index,raw,weighted,rows,deficient,points,raw,weighted,0,weights,rng.getstate(),0,logical)


def initial_boundary(n, rng, *, check=None, work=None):
    deficient = rng.randrange(n); points = []
    for row in range(n):
        points.extend((x,row) for x in rng.sample(range(n),1 if row == deficient else 2))
    return make_boundary(points,n,rng,check=check,work=work)


def _penalties(index, weights, policy, check, work):
    _phase(work,'penalty_precheck',check)
    violated = []
    for key,mask in index.items():
        check()
        if mask.bit_count() >= 3:
            if weights.get(key,1) >= policy.max_weight: raise WeightCap('weight_value_cap')
            violated.append(key)
    if len(weights)+sum(key not in weights for key in violated) > policy.max_weight_keys:
        raise WeightCap('weight_key_cap')
    _phase(work,'penalty_copy',check); staged = dict(weights)
    _phase(work,'penalty_update',check)
    for key in violated:
        check(); staged[key] = staged.get(key,1)+1
    return staged


def propose_transition(boundary, rng, *, policy=Policy(), check=None, work=None):
    """Return one completed transaction; every exception restores committed RNG."""
    check = check or (lambda: None); work = {} if work is None else work
    if boundary.unweighted == 0: raise ValueError('zero boundary must be validated, never moved')
    if rng.getstate() != boundary.rng_state: raise ValueError('RNG boundary mismatch')
    _inc(work,'transitions_started'); b = boundary
    try:
        step = b.logical['transitions']+1
        migration = step % policy.migration_period == 0
        if migration:
            _phase(work,'migration_sampling',check); outcomes = {}
            donors = tuple(p for p in b.points if p[1] != b.deficient_row)
            vacant = tuple(x for x in range(b.n) if (x,b.deficient_row) not in b.points)
            for _ in range(policy.migration_samples):
                _phase(work,'migration_before_draw',check)
                donor = rng.choice(donors); destination = (rng.choice(vacant),b.deficient_row)
                _phase(work,'migration_after_draw',check); _inc(work,'migration_attempts')
                delta = migration_delta(b.points,donor,destination,b.weights,check,work)
                points = tuple(sorted(tuple(p for p in b.points if p != donor)+(destination,)))
                outcomes.setdefault(points,(delta,donor,destination))
            _phase(work,'migration_sample_complete',check)
            minimum = min(b.weighted+record[0]['weighted'] for record in outcomes.values())
            ties = sorted(points for points,record in outcomes.items() if b.weighted+record[0]['weighted'] == minimum)
            points = rng.choice(ties); expected = outcomes[points][0]
            expected = (b.unweighted+expected['unweighted'],b.weighted+expected['weighted'])
        else:
            _phase(work,'row_before_draw',check); row = rng.choice(b.conflict_rows)
            _phase(work,'row_after_draw',check)
            costs = row_costs(b.points,b.index,row,b.weights,b.n,check,work)
            minimum,ties = best_row_alternatives(b.points,row,costs,b.n,check,work)
            if not ties: raise SearchStop('no_distinct_row_alternative')
            _phase(work,'row_tie_before_draw',check); chosen = rng.choice(ties)
            _phase(work,'row_tie_after_draw',check)
            old = tuple(x for x,y in b.points if y == row)
            expected = (b.unweighted+sum(costs['unweighted'][x] for x in chosen)-sum(costs['unweighted'][x] for x in old),
                        b.weighted+minimum-sum(costs['weighted'][x] for x in old))
            points = tuple(p for p in b.points if p[1] != row)+tuple((x,row) for x in chosen)
        points,index,raw,weighted,rows = build_index(points,b.n,b.weights,check,work)
        if (raw,weighted) != expected: raise ValueError('exact move delta disagrees with rebuilt index')
        logical = dict(b.logical); logical['transitions'] += 1
        logical['migration_transitions' if migration else 'row_transitions'] += 1
        logical['raw_down' if raw < b.unweighted else 'raw_neutral' if raw == b.unweighted else 'raw_up'] += 1
        improved = raw < b.best_unweighted
        best = points if improved else b.best_points; best_raw = min(raw,b.best_unweighted)
        best_weighted = weighted if improved else b.best_weighted_at_capture
        best_epoch = logical['penalty_events'] if improved else b.best_weight_epoch
        stagnant = 0 if improved else b.stagnation+1
        if improved:
            logical['best_improvements'] += 1
            if logical['penalty_events']: logical['best_improvements_after_penalty'] += 1
        weights = b.weights
        if raw:
            if stagnant >= policy.penalty_period:
                weights = _penalties(index,weights,policy,check,work)
                raw2,weighted,rows = score_index(points,index,weights,check)
                if raw2 != raw: raise ValueError('weight update changed geometry score')
                logical['penalty_events'] += 1; stagnant = 0
            _phase(work,'precommit',check)
        # Completed zero bypasses optional penalties and ordinary search checks.
        deficient = next(r for r in range(b.n) if sum(y == r for _,y in points) == 1)
        result = Boundary(b.n,points,index,raw,weighted,rows,deficient,best,best_raw,best_weighted,best_epoch,
                          weights,rng.getstate(),stagnant,logical)
        _inc(work,'transitions_completed'); work['phase'] = 'committed_zero' if not raw else 'committed'
        return result
    except Exception:
        rng.setstate(b.rng_state); _inc(work,'transitions_aborted'); raise


def compact(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


def checkpoint_bytes(boundary, identities, *, policy=Policy(), validation=None, check=None):
    check = check or (lambda: None); b = boundary
    validation = validation or ('unverified_zero_candidate' if b.unweighted == 0 else 'invalid_research_state')
    if validation not in ('invalid_research_state','unverified_zero_candidate','dual_verified_witness') or ((b.unweighted == 0) != (validation != 'invalid_research_state')):
        raise ValueError('checkpoint validation classification')
    if validate_points(b.points,b.n) != b.points or validate_points(b.best_points,b.n) != b.best_points:
        raise ValueError('checkpoint state order')
    if (any(type(v) is not int or v < 0 for v in (b.unweighted,b.weighted,b.best_unweighted,b.best_weighted_at_capture,b.stagnation,b.best_weight_epoch))
            or b.best_unweighted > b.unweighted or b.unweighted > choose3(len(b.points))
            or b.weighted > 65535*choose3(len(b.points)) or not 0 <= b.stagnation < policy.penalty_period
            or b.logical['row_transitions']+b.logical['migration_transitions'] != b.logical['transitions']
            or b.best_weight_epoch > b.logical['penalty_events']
            or sum(y == b.deficient_row for _,y in b.points) != 1):
        raise ValueError('checkpoint boundary schema')
    if type(b.rng_state[0]) is not int or b.rng_state[0] != 3 or b.rng_state[2] is not None or len(b.rng_state[1]) != 625:
        raise ValueError('RNG schema')
    if (any(type(v) is not int or not 0 <= v <= 0xffffffff for v in b.rng_state[1][:-1])
            or type(b.rng_state[1][-1]) is not int or not 0 <= b.rng_state[1][-1] <= 624):
        raise ValueError('RNG words/index')
    if any(type(v) is not int or not 0 <= v < 2**64 for v in b.logical.values()): raise ValueError('logical counter schema')
    records = []
    if len(b.weights) > policy.max_weight_keys: raise ValueError('checkpoint key cap')
    for (a,bb,c),w in sorted(b.weights.items()):
        check()
        if any(type(v) is not int for v in (a,bb,c,w)) or not (0 <= a <= 74 and -74 <= bb <= 74 and abs(c) <= 10952
                and math.gcd(a,abs(bb)) == 1 and (a > 0 or bb > 0) and 1 < w <= policy.max_weight):
            raise ValueError('checkpoint weight schema')
        records.append([a,bb,c,w])
    metadata = {'schema':'row-block-completed-boundary-v1','identities':identities,
                'policy':dict(n=b.n,k=2*b.n-1,seed=SEED,max_steps=MAX_STEPS,**policy.__dict__),
                'logical':b.logical,'stagnation':b.stagnation,'deficient_row':b.deficient_row,
                'current_unweighted':b.unweighted,'current_weighted':b.weighted,
                'best_unweighted':b.best_unweighted,'best_weighted_at_capture':b.best_weighted_at_capture,
                'best_weight_epoch':b.best_weight_epoch,'validation':validation,
                'current_normalized_sha256':normalized_sha256(b.n,b.points),
                'best_normalized_sha256':normalized_sha256(b.n,b.best_points)}
    if len(compact(metadata)) > 16384: raise ValueError('checkpoint metadata cap')
    check(); raw = compact({'metadata':metadata,'current':b.points,'best':b.best_points,'weights':records,'rng':b.rng_state})
    if len(raw) > CHECKPOINT_CAP: raise ValueError('checkpoint byte cap')
    return raw


def digest(path, check=lambda:None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check(); block = stream.read(1024*1024)
            if not block:return h.hexdigest()
            h.update(block)


def atomic_bytes(path, raw):
    fd,name = tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name,path)
    finally:Path(name).unlink(missing_ok=True)


def save_json(path,value,cap=REPORT_CAP):
    raw = compact(value)
    if len(raw) > cap:raise ValueError('JSON output cap')
    atomic_bytes(path,raw)


def validator_summary(report):
    return {key:value for key,value in report.items() if key != 'conflicts'}


def dual_validate(points,n,score,check):
    candidate = {'n':n,'points':list(points),'claimed_conflict_count':score,'novelty_claimed':False}
    check(); a = verify_certificate(candidate); check(); b = verify_certificate_bruteforce(candidate)
    if not (a['point_count'] == b['point_count'] == len(points) and a['normalized_sha256'] == b['normalized_sha256']
            and a['conflict_count'] == b['conflict_count'] == score and a['conflicts'] == b['conflicts']
            and a['valid'] is b['valid'] is (score == 0) and not a['errors'] and not b['errors']):
        raise ValueError('dual validator disagreement')
    conflicts_sha = None if score == 0 else hashlib.sha256(compact(a['conflicts'])).hexdigest()
    return candidate,[validator_summary(a),validator_summary(b)],conflicts_sha


def run(out,manifest,seconds=25,*,started=None,clock=time.monotonic):
    if isinstance(seconds,bool) or not math.isfinite(seconds) or not 2 < seconds <= 25:raise ValueError('duration')
    start = clock() if started is None else started; soft = start+seconds; search = soft-2
    def final_check():
        if clock() >= soft:raise TimeoutError('main soft deadline')
    def search_check():
        if clock() >= search:raise SearchStop('search_deadline')
    report = {'method':'from_scratch_row_block_breakout75','status':'incomplete','accepted':False,'closure':False,
              'witness_saved':False,'checkpoint_saved':False,'identity_valid':False,'work':{},'checkpoints':[],'penalty_checkpoints':[],
              'n':N,'k':2*N-1,'seed':SEED,'max_steps':MAX_STEPS,'policy':Policy().__dict__,
              'scope':'One scratch row/soft-column/adaptive-weight trajectory; no exclusion, source seed, restart, resume CLI or automatic continuation.'}
    pins = {}; pins_ready = False; boundary = None; rng = random.Random(SEED); classification = 'invalid_research_state'
    def verify_pins():
        for path,expected in pins.items():
            if digest(path,final_check) != expected:raise ValueError('pin drift: '+path)
    try:
        final_check(); raw_manifest = Path(manifest).read_bytes()
        if len(raw_manifest) > 2*1024*1024:raise ValueError('manifest size')
        sources = json.loads(raw_manifest)
        if type(sources) is not dict or not 1 <= len(sources) <= 512:raise ValueError('manifest shape')
        for name,sha in sources.items():
            if type(name) is not str or type(sha) is not str or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('pin schema')
            path = str((ROOT/name).resolve())
            if path in pins:raise ValueError('duplicate normalized pin')
            pins[path] = sha
        runtime = str(Path(sys.executable).resolve()); random_module = str(Path(random.__file__).resolve())
        required = {str(Path(__file__).resolve()),str((ROOT/'src/verify.py').resolve()),runtime,random_module}
        if not required <= pins.keys():raise ValueError('missing worker/verifier/runtime/RNG pins')
        manifest_name = str(Path(manifest).resolve())
        if manifest_name in pins:raise ValueError('manifest self entry')
        manifest_sha = hashlib.sha256(raw_manifest).hexdigest(); pins[manifest_name] = manifest_sha
        verify_pins(); pins_ready = True
        identities = {'manifest_path':manifest_name,'manifest_sha256':manifest_sha,'worker_sha256':pins[str(Path(__file__).resolve())],
                      'runtime_path':runtime,'runtime_sha256':pins[runtime],'python_version':sys.version,
                      'random_module_path':random_module,'random_module_sha256':pins[random_module],'RNG_version':3}
        boundary = initial_boundary(N,rng,check=search_check,work=report['work'])
        if boundary.unweighted:
            save_json(out/'initial.json',{'n':N,'points':boundary.points,'unweighted':boundary.unweighted,'weighted':boundary.weighted,'valid':False})
        report['initial_unweighted'] = boundary.unweighted
        for _ in range(MAX_STEPS):
            # Zero is processed before ordinary search-deadline or optional work.
            if boundary.unweighted == 0:break
            previous_penalties = boundary.logical['penalty_events']
            boundary = propose_transition(boundary,rng,check=search_check,work=report['work'])
            step = boundary.logical['transitions']
            if not boundary.unweighted:break
            if boundary.logical['penalty_events'] != previous_penalties and len(report['penalty_checkpoints']) < 32:
                report['penalty_checkpoints'].append({'step':step,'unweighted':boundary.unweighted,
                    'penalty_events':boundary.logical['penalty_events'],'state_sha256':normalized_sha256(N,boundary.points)})
            if step & (step-1) == 0 and len(report['checkpoints']) < 64:
                report['checkpoints'].append({'step':step,'unweighted':boundary.unweighted,'best':boundary.best_unweighted,
                                             'penalty_events':boundary.logical['penalty_events'],
                                             'state_sha256':normalized_sha256(N,boundary.points)})
        report['status'] = 'zero_candidate' if boundary.unweighted == 0 else 'step_cap'
    except (SearchStop,WeightCap) as error:report['status'] = str(error)
    except Exception as error:report.update(status='error',error=f'{type(error).__name__}: {str(error)[:1000]}')
    # A committed zero is handled even when the final transition crossed search time.
    if boundary is not None and boundary.unweighted == 0:
        classification = 'unverified_zero_candidate'
        try:
            candidate,validators,conflicts_sha = dual_validate(boundary.points,N,0,final_check)
            # No deadline/pin/checkpoint work between successful validator2 and save.
            save_json(out/'valid149.json',{'certificate':candidate,'validators':validators,'conflicts_sha256':conflicts_sha})
            report.update(witness_saved=True,status='verified149',witness_normalized_sha256=validators[0]['normalized_sha256'])
            classification = 'dual_verified_witness'
        except Exception as error:report.update(status='validation_incomplete',validation_error=f'{type(error).__name__}: {str(error)[:1000]}')
    elif boundary is not None and boundary.best_unweighted <= 1000 and clock() < soft-0.5:
        try:
            candidate,validators,conflicts_sha = dual_validate(boundary.best_points,N,boundary.best_unweighted,final_check)
            save_json(out/'best.json',{'certificate':candidate,'validators':validators,'conflicts_sha256':conflicts_sha,
                                     'valid':False,'classification':'dual_checked_invalid_research_state'})
            report['best_diagnostic_saved'] = True
        except Exception as error:report['best_diagnostic_error'] = f'{type(error).__name__}: {str(error)[:1000]}'
    if boundary is not None:
        try:
            # Mandatory bounded serialization/publication may finish after soft time;
            # final acceptance still fails its deadline. The owned guard is final.
            raw = checkpoint_bytes(boundary,identities,validation=classification)
            atomic_bytes(out/'completed-boundary.json',raw)
            report.update(checkpoint_saved=True,checkpoint_bytes=len(raw),checkpoint_sha256=hashlib.sha256(raw).hexdigest(),
                          logical=boundary.logical,stagnation=boundary.stagnation,current_unweighted=boundary.unweighted,
                          current_weighted=boundary.weighted,best_unweighted=boundary.best_unweighted,
                          weight_keys=len(boundary.weights),weight_key_maximum=len(boundary.weights),validation=classification)
        except Exception as error:report.update(status='checkpoint_failure',checkpoint_error=f'{type(error).__name__}: {str(error)[:1000]}')
    try:
        if not pins_ready:raise ValueError('initial pins incomplete')
        verify_pins(); final_check(); report['identity_valid'] = True
        report['accepted'] = report['checkpoint_saved'] and report['status'] not in ('error','validation_incomplete','checkpoint_failure')
    except Exception as error:report.update(accepted=False,identity_valid=False,final_error=f'{type(error).__name__}: {str(error)[:1000]}')
    report.update(pins=pins,elapsed_seconds=clock()-start)
    save_json(out/'report.json',report)
    try:final_check()
    except TimeoutError:
        report.update(accepted=False,final_error='report publication crossed main soft deadline',elapsed_seconds=clock()-start)
        save_json(out/'report.json',report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--source-pins',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=25);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    report = run(args.output_dir,args.source_pins,args.seconds,started=ENTRY_STARTED)
    print(json.dumps({k:report.get(k) for k in ('status','accepted','witness_saved','checkpoint_saved','current_unweighted','best_unweighted','logical','work','elapsed_seconds')},sort_keys=True))
    return 0 if report['accepted'] else 2


if __name__=='__main__':sys.exit(main())
