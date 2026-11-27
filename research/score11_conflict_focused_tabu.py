"""Bounded conflict-focused direct-deficiency sampled tabu search."""
import argparse
from collections import Counter, deque
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research import score11_deficiency_walk as base
from research import score11_deficiency_neighborhood as one
from src.verify import normalized_direction, normalized_sha256

SOURCE = base.SOURCE
SOURCE_SHA = base.SOURCE_SHA
AUDIT = ROOT / 'data/score11-deficiency-walk-seed279157-v1-independent-actual-audit.json'
AUDIT_SHA = '419039ebf5828b8fef5b22a0eac29f63e4da4ff203a263aae14c30f704b4faec'
MAX_STEPS = 2000
SAMPLES = 32
TABU_SIZE = 64


def conflict_triples(points, check):
    """Exact sorted coordinate triples, with deadline checks in pair/group loops."""
    ordered = sorted(points); triples = []
    for i, a in enumerate(ordered):
        groups = {}
        for b in ordered[i+1:]:
            check()
            groups.setdefault(normalized_direction(b[0]-a[0], b[1]-a[1]), []).append(b)
        for group in groups.values():
            for b, c in itertools.combinations(group, 2):
                check(); triples.append((a, b, c))
    return sorted(triples)


def incidence(point, others, check):
    directions = Counter()
    for x, y in others:
        check(); directions[normalized_direction(x-point[0], y-point[1])] += 1
    return sum(count*(count-1)//2 for count in directions.values())


def move(points, n, kind, first, second, check):
    r, c = base.axes(points, n)
    if first not in points:
        raise ValueError('old cell absent')
    if kind in ('row', 'column'):
        dest = (r, first[1]) if kind == 'row' else (first[0], c)
        if dest == first or dest in points:
            return None
        remain = points - {first}
        delta = -incidence(first, remain, check) + incidence(dest, remain, check)
        result = remain | {dest}
    elif kind == 'rectangle':
        if second not in points:
            raise ValueError('second cell absent')
        if first == second or first[0] == second[0] or first[1] == second[1]:
            return None
        add = ((first[0], second[1]), (second[0], first[1]))
        if any(p in points for p in add):
            return None
        mid = points - {first}; remain = mid - {second}
        delta = -incidence(first, mid, check) - incidence(second, remain, check)
        delta += incidence(add[0], remain, check) + incidence(add[1], remain | {add[0]}, check)
        result = remain | set(add)
    else:
        raise ValueError('invalid move class')
    base.axes(result, n)
    return delta, result


def candidate(n, points, score, source, output_dir, index, labels, check, pins, expected_normalized=None):
    base.axes(points, n)
    one.recheck_pins(pins)
    cert = {'n': n, 'points': [list(p) for p in sorted(points)]}
    check(); a = base.verify_certificate(cert)
    check(); b = base.verify_certificate_bruteforce(cert)
    if (any(v['errors'] or v['point_count'] != len(points) or v['conflict_count'] != score or v['valid'] != (score == 0) for v in (a,b))
            or a['normalized_sha256'] != b['normalized_sha256']
            or base.canonical_conflicts(a) != base.canonical_conflicts(b)
            or (expected_normalized is not None and a['normalized_sha256'] != expected_normalized)):
        raise RuntimeError('dual validator disagreement')
    meta = {'labels': labels, 'valid': score == 0, 'exact_conflict_count': score,
            'source_deleted': len(source-points), 'normalized_sha256': a['normalized_sha256'],
            'pins': {str(k):v for k,v in pins.items()}}
    cert.update(metadata=meta, validators=[a,b])
    path = output_dir / f'candidate-{index:04d}.json'
    # A completed second validator is saved even after a soft deadline.
    base.atomic(path, cert)
    return {'path': str(path), **meta}


def walk(n, initial, source, initial_score, output_dir, *, seed=279179, seconds=25,
         max_steps=MAX_STEPS, clock=time.monotonic, started=None, pins=None,
         expected_initial=None):
    if (type(seed) is not int or type(max_steps) is not int or not 0 <= max_steps <= MAX_STEPS
            or isinstance(seconds, bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0 < seconds <= 25):
        raise ValueError('invalid budget or seed')
    start = clock() if started is None else started; deadline = start + seconds
    def check():
        if clock() >= deadline: raise TimeoutError('shared soft deadline')
    pins = {} if pins is None else dict(pins)
    rng = random.Random(seed); points = set(initial); source = set(source)
    report = {'status':'timeout','complete':False,'seed':seed,'seconds':seconds,'max_steps':max_steps,
              'steps_started':0,'steps_completed':0,'candidates_started':0,'candidates_completed':0,
              'classes':{k:{'started':0,'completed':0,'illegal':0,'duplicates':0,'tabu':0,'admissible':0} for k in ('row','column','rectangle')},
              'accepted':0,'uphill':0,'neutral':0,'downhill':0,'tabu_capacity':TABU_SIZE,'tabu_evictions':0,
              'accepted_score_histogram':{},'best':None,'distance_exit':None,'witness':None,
              'scope':'157-point sampled tabu walk; no source-retention constraint or exhaustive claim'}
    histogram=Counter(); artifact=0
    try:
        base.axes(points,n)
        if not points <= source or len(source-points)!=1: raise ValueError('invalid initial source relation')
        initial_labels = ['witness','initial_best'] if initial_score == 0 else ['initial_best']
        initial_record=candidate(n,points,initial_score,source,output_dir,artifact,initial_labels,check,pins,expected_initial)
        report['best']=initial_record; artifact+=1
        best=initial_score; score=initial_score
        recent=deque([tuple(sorted(points))]); recent_set={recent[0]}
        if score==0:
            report['witness']=initial_record; report['status']='witness'; report['complete']=True
        else:
            for _ in range(max_steps):
                check();report['steps_started']+=1
                triples=conflict_triples(points,check)
                if len(triples)!=score: raise RuntimeError('incremental score mismatch')
                if not triples: raise RuntimeError('zero score not saved')
                focus=sorted({p for triple in triples for p in triple}); ordered=sorted(points)
                seen=set(); choices=[]
                for sample in range(SAMPLES):
                    check(); kind=('row' if sample<8 else 'column' if sample<16 else 'rectangle')
                    row=report['classes'][kind];row['started']+=1;report['candidates_started']+=1
                    first=rng.choice(focus); second=rng.choice(ordered) if kind=='rectangle' else None
                    proposal=move(points,n,kind,first,second,check)
                    row['completed']+=1;report['candidates_completed']+=1
                    if proposal is None:
                        row['illegal']+=1;continue
                    delta, result=proposal; key=tuple(sorted(result)); result_score=score+delta
                    if key in seen:
                        row['duplicates']+=1;continue
                    seen.add(key)
                    if key in recent_set and result_score>=best:
                        row['tabu']+=1;continue
                    row['admissible']+=1;choices.append((result_score,key,result))
                report['steps_completed']+=1
                if not choices:
                    report['status']='no_admissible_sample';report['complete']=True;break
                new_score,key,new_points=min(choices,key=lambda x:(x[0],x[1]))
                diff=new_score-score
                report['accepted']+=1;report['uphill' if diff>0 else 'downhill' if diff<0 else 'neutral']+=1
                histogram[new_score]+=1;points=new_points;score=new_score
                recent.append(key);recent_set.add(key)
                if len(recent)>TABU_SIZE:
                    old=recent.popleft();recent_set.remove(old);report['tabu_evictions']+=1
                labels=[]
                if score==0: labels.append('witness')
                if score<best: labels.append('strict_best')
                if report['distance_exit'] is None and len(source-points)>=13: labels.append('distance_exit')
                if labels:
                    record=candidate(n,points,score,source,output_dir,artifact,labels,check,pins)
                    artifact+=1
                    if 'witness' in labels: report['witness']=record
                    if 'strict_best' in labels: best=score;report['best']=record
                    if 'distance_exit' in labels: report['distance_exit']=record
                    if 'witness' in labels: report['status']='witness';report['complete']=True;break
            else:
                report['status']='step_cap';report['complete']=True
    except TimeoutError as error:
        report['timeout_phase']=str(error)
    except Exception as error:
        report['status']='error';report['complete']=False;report['error']=f'{type(error).__name__}: {error}'
    report['accepted_score_histogram']=dict(sorted(histogram.items()))
    report['elapsed_seconds']=clock()-start
    return report


def main():
    started=time.monotonic()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=279179)
    parser.add_argument('--seconds',type=float,default=25)
    parser.add_argument('--max-steps',type=int,default=MAX_STEPS)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    fixed={one.INPUT:one.INPUT_SHA, SOURCE:SOURCE_SHA, AUDIT:AUDIT_SHA}
    one.recheck_pins(fixed)
    initial_doc=json.loads(one.INPUT.read_bytes()); source_doc=json.loads(SOURCE.read_bytes())
    if initial_doc['n']!=79 or source_doc['n']!=79:
        raise ValueError('source dimensions mismatch')
    a=[tuple(p) for p in initial_doc['points']];s=[tuple(p) for p in source_doc['points']]
    if len(a)!=len(set(a)) or len(s)!=len(set(s)) or len(a)!=157 or len(s)!=158:
        raise ValueError('source cardinality mismatch')
    if normalized_sha256(79,s)!=base.SOURCE_NORMALIZED or set(s)-set(a)!={(78,78)}:
        raise ValueError('source normalized identity or containment mismatch')
    if any(Counter(p[axis] for p in s)!=Counter({i:2 for i in range(79)}) for axis in (0,1)):
        raise ValueError('source axis mismatch')
    paths=('research/score11_conflict_focused_tabu.py','research/score11_deficiency_walk.py','research/score11_deficiency_neighborhood.py','src/trade_search.py','src/verify.py')
    pins={ROOT/p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths};pins.update(fixed)
    report=walk(79,set(a),set(s),5,args.output_dir,seed=args.seed,seconds=args.seconds,max_steps=args.max_steps,
                started=started,pins=pins,expected_initial=one.INPUT_NORMALIZED)
    one.finalize_identity(report,pins)
    # JSON-compatible path keys, while retaining recheck on Path keys above.
    report['pins']={str(k):v for k,v in pins.items()}
    base.atomic(args.output_dir/'report.json',report)
    print(json.dumps(report,sort_keys=True))
    return 1 if report['status']=='error' else (0 if report['complete'] else 2)


if __name__=='__main__':
    sys.exit(main())
