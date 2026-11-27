"""Explicit source-only or separately owned normal mode; no automatic geometry."""
import argparse
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
from research import full_complement_row_domain_n5 as producer

ROOT = Path(__file__).resolve().parents[1]
PRODUCER_SHA = '36f4639fededa4fd0e239e397acb43478e7131ee4a1d0f798079d73cf34b5b8e'
FIXTURE_PATH = ROOT / 'data/full-complement-row-domain-n5-fixture-v1.json'
ORACLE_BYTES = b'{"n":5,"points":[[0,0],[0,1],[0,2],[0,3],[0,4],[1,0],[1,1],[1,2],[1,3]]}'
ORACLE_SHA = '5be21073f6b07bc18969b91f9dd9b9196ebe42288cfa9342468171a3c9ef8f37'
OUTPUT_CAP = 64*1024


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_identity():
    raw = Path(producer.__file__).read_bytes()
    check(sha(raw) == PRODUCER_SHA, 'producer source drift')
    fixture_raw = FIXTURE_PATH.read_bytes()
    check(len(fixture_raw) == 72 and fixture_raw == ORACLE_BYTES and sha(fixture_raw) == ORACLE_SHA,
          'canonical fixture bytes')
    check(producer.FIXTURE_BYTES == ORACLE_BYTES and producer.FIXTURE_SHA == ORACLE_SHA,
          'independent fixture constants')
    return {'producer_sha256':PRODUCER_SHA,'harness_sha256':sha(Path(__file__).read_bytes()),
            'fixture_sha256':ORACLE_SHA,'fixture_bytes':72}


def compare_identities(before,after):
    expected = {'producer_sha256','harness_sha256','fixture_sha256','fixture_bytes'}
    check(set(before) == set(after) == expected and before == after, 'source/fixture identity drift before success')


def oracle_points():
    value = json.loads(ORACLE_BYTES)
    return tuple(tuple(p) for p in value['points'])


def shape(points):
    check(type(points) is tuple and len(points) == 9 and tuple(sorted(points)) == points, 'oracle canonical cells')
    check(len(set(points)) == 9 and all(type(x) is int and type(y) is int and 0 <= x < 5 and 0 <= y < 5 for x,y in points),
          'oracle distinct in-grid cells')
    check(tuple(sum(y == row for x,y in points) for row in range(5)) == (2,2,2,2,1), 'oracle preserved loads')


def direct_raw(points,budget):
    """Independent edge-vector determinant; never calls producer geometry."""
    shape(points)
    score = 0
    conflicts = {}
    for first,second,third in combinations(points,3):
        budget.charge('determinants','direct_oracle')
        dx1,dy1 = second[0]-first[0],second[1]-first[1]
        dx2,dy2 = third[0]-second[0],third[1]-second[1]
        if dx1*dy2-dy1*dx2 == 0:
            score += 1
            rows = tuple(sorted((first[1],second[1],third[1])))
            conflicts[rows] = conflicts.get(rows,0)+1
    return score,conflicts


def line_map(points,budget,component):
    lines = {}
    for left,right in combinations(points,2):
        budget.charge('line_keys',component)
        a,b = right[1]-left[1],left[0]-right[0]
        c = right[0]*left[1]-left[0]*right[1]
        divisor = gcd(gcd(abs(a),abs(b)),abs(c))
        check(divisor > 0, 'distinct line endpoints')
        a,b,c = a//divisor,b//divisor,c//divisor
        if a < 0 or a == 0 and b < 0:
            a,b,c = -a,-b,-c
        lines.setdefault((a,b,c),set()).update((left,right))
    return lines


def line_raw(points,budget):
    shape(points)
    lines = line_map(points,budget,'raw_line_oracle')
    check(len(lines) <= 36, 'raw line map cap')
    score = sum(len(v)*(len(v)-1)*(len(v)-2)//6 for v in lines.values())
    return score


def dual_raw(points,budget):
    direct,conflicts = direct_raw(points,budget)
    check(direct == line_raw(points,budget), 'independent raw-score disagreement')
    return direct,conflicts


def replace_row(points,row,columns):
    return tuple(sorted(tuple(p for p in points if p[1] != row)+tuple((x,row) for x in columns)))


def run_normal(budget):
    """A single owned geometric pass is required; caller must select this mode."""
    identities = source_identity()
    points = oracle_points()
    result = producer.make_domains(points,5,budget)
    baseline,conflicts = dual_raw(points,budget)
    check(baseline == result['baseline'] == 14, 'constructed baseline14')
    check(result['n'] == 5 and result['fixture_sha256'] == ORACLE_SHA and len(result['rows']) == 5, 'result schema')
    check(result['current_conflicts'] == [{'rows':rows,'count':count} for rows,count in sorted(conflicts.items())],
          'independent current conflict census')
    row_records = []
    for row,record in enumerate(result['rows']):
        current = tuple(x for x,y in points if y == row)
        check(record['row'] == row and record['current'] == current, 'row/current binding')
        complement = tuple(p for p in points if p[1] != row)
        lines = line_map(complement,budget,'unary_line_oracle')
        check(len(lines) <= 28, 'retained line map cap')
        independent_unary = []
        for x in range(5):
            cost = 0
            for (a,b,c),endpoints in lines.items():
                budget.charge('line_incidences','unary_line_oracle')
                if a*x+b*row+c == 0:
                    cost += len(endpoints)*(len(endpoints)-1)//2
            independent_unary.append(cost)
        del lines
        check(tuple(independent_unary) == record['unary'], 'all unary cells independently checked')
        placements = []
        for columns in combinations(range(5),len(current)):
            candidate = replace_row(points,row,columns)
            score,_ = dual_raw(candidate,budget)
            placements.append({'columns':columns,'score':score})
        minimum = min((p['score'],p['columns']) for p in placements)
        check((record['best_score'],record['best']) == minimum, 'exact independent minimum and lexical tie')
        seed = set(current) | set(minimum[1])
        # Select only the required smallest missing columns, independently of the producer loop.
        missing = sorted(set(range(5))-seed)
        expected_domain = tuple(sorted(seed | set(missing[:4-len(seed)])))
        check(record['domain'] == expected_domain and len(record['domain']) == 4
              and set(current) <= set(record['domain']) and set(minimum[1]) <= set(record['domain']),
              'deterministic current/best-inclusive domain')
        row_records.append({'row':row,'placements':placements,'minimum':minimum})
    singleton = result['rows'][4]
    check(singleton['unary'] == (6,6,2,1,1) and singleton['best'] == (3,)
          and singleton['best_score'] == 9 and singleton['domain'] == (0,1,2,3), 'hand-derived singleton values')
    embeddings = []
    for row,record in enumerate(result['rows']):
        if record['best_score'] >= baseline:
            continue
        eligible = sorted(rows for rows,count in conflicts.items() if count > 0 and row in rows)
        check(bool(eligible), 'strict replacement has old conflict triple')
        rows = eligible[0]
        chosen = {r:record['best'] if r == row else tuple(x for x,y in points if y == r) for r in rows}
        check(all(set(chosen[r]) <= set(result['rows'][r]['domain']) for r in rows), 'embedded domain membership')
        check(tuple(len(chosen[r]) for r in rows) == tuple(sum(y == r for x,y in points) for r in rows)
              and sum(map(len,chosen.values())) in (5,6), 'legal individual and total loads')
        candidate = tuple(sorted(tuple(p for p in points if p[1] not in rows)
                                 +tuple((x,r) for r in rows for x in chosen[r])))
        check(candidate == replace_row(points,row,record['best']), 'embedded exact point identity')
        score,_ = dual_raw(candidate,budget)
        check(score == record['best_score'] and score < baseline, 'strict feasible embedded assignment')
        embeddings.append({'row':row,'block':rows,'columns':chosen,'score':score})
    counts = budget.snapshot()
    components = counts['components']
    check(components['producer']['determinants'] == 644, 'producer geometry count')
    check(components['direct_oracle']['determinants'] == (46+len(embeddings))*84, 'direct oracle count')
    check(components['raw_line_oracle']['line_keys'] == (46+len(embeddings))*36, 'raw line-key count')
    check(components['unary_line_oracle']['line_keys'] == 112
          and components['unary_line_oracle']['line_incidences'] <= 560, 'unary oracle counts')
    check(counts['totals']['determinants'] <= 4928 and counts['totals']['line_keys'] <= 1948
          and counts['totals']['line_incidences'] <= 560, 'derived operation bounds')
    return dict(identities,passed=True,mode='normal',producer=result,independent_rows=row_records,
                embeddings=embeddings,operation_counts=counts,
                scope='One predetermined n5 diagnostic only. No old production comparator, optimizer, alternate fixture or actual input.')


def run_pregeometry():
    identities = source_identity()
    points = oracle_points()
    rejections = []
    mutations = [('boolean_n',points,True),('wrong_n',points,4),('container',None,5),
                 ('missing_cell',points[:-1],5),('duplicate',points[:-1]+(points[0],),5),
                 ('boolean_coordinate',((False,0),)+points[1:],5),
                 ('bounds',((5,0),)+points[1:],5),('cell_shape',((0,),)+points[1:],5),
                 ('wrong_loads',points[:-1]+((2,4),),5),
                 ('different_valid_identity',tuple(sorted(tuple(p for p in points if p != (0,4))+((1,4),))),5)]
    for label,candidate,n in mutations:
        budget = producer.Budget()
        try:
            producer.make_domains(candidate,n,budget)
        except ValueError as exc:
            check(all(value == 0 for value in budget.counts.values()), 'rejected before geometry: '+label)
            rejections.append({'case':label,'error':str(exc),'real_geometric_operations':0})
        else:
            raise AssertionError('accepted malformed/alternate input: '+label)
    counter_checks = []
    for kind,limit in producer.LIMITS.items():
        budget = producer.Budget()
        budget.counts[kind] = limit-1  # Explicit synthetic state, not geometry.
        budget.charge(kind,'synthetic')
        check(budget.counts[kind] == limit, 'last counter charge')
        try:
            budget.charge(kind,'synthetic')
        except producer.BudgetExceeded:
            check(budget.counts[kind] == limit and budget.components['synthetic'][kind] == 1, 'stop before excess operation')
            counter_checks.append({'kind':kind,'last_charge_then_refusal':True,'synthetic_seed':limit-1})
        else:
            raise AssertionError('quota did not stop: '+kind)
    drift_checks = []
    for role in ('producer_sha256','harness_sha256','fixture_sha256','fixture_bytes'):
        changed = dict(identities)
        changed[role] = 73 if role == 'fixture_bytes' else '0'*64
        try:
            compare_identities(identities,changed)
        except AssertionError:
            drift_checks.append({'role':role,'injected_identity_drift_rejected':True,'real_geometric_operations':0})
        else:
            raise AssertionError('identity drift accepted: '+role)
    compare_identities(identities,dict(identities))
    return dict(identities,passed=True,mode='pregeometry',rejections=rejections,counter_checks=counter_checks,drift_checks=drift_checks,
                real_geometric_operations=0,
                scope='Rejection-before-geometry and explicitly seeded synthetic counters only. No normal producer/oracle pass.')


def write_immutable(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode('ascii')
    check(len(raw) <= OUTPUT_CAP, '64KiB evidence cap')
    with path.open('xb') as output:
        output.write(raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('pregeometry','normal'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError('immutable evidence already exists: '+str(args.output))
    budget=producer.Budget()
    try:
        result=run_pregeometry() if args.mode == 'pregeometry' else run_normal(budget)
        compare_identities({k:result[k] for k in ('producer_sha256','harness_sha256','fixture_sha256','fixture_bytes')},
                           source_identity())
        write_immutable(args.output,result)
    except Exception as exc:
        failure={'passed':False,'mode':args.mode,'error':type(exc).__name__+': '+str(exc),
                 'operation_counts':budget.snapshot(),'producer_sha256':sha(Path(producer.__file__).read_bytes()),
                 'harness_sha256':sha(Path(__file__).read_bytes()),'fixture_sha256':ORACLE_SHA,
                 'scope':'Failure preserved; no automatic retry or alternative input.'}
        failed=args.output.with_name(args.output.stem+'-failure.json')
        write_immutable(failed,failure)
        raise
    print(json.dumps({'passed':True,'mode':args.mode,'output':str(args.output)},sort_keys=True))


if __name__ == '__main__':
    main()
