"""Finite schema/quota/stubbed-zero checks; no real geometric calculation."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from research import full_complement_row75_core as core
from research import full_complement_row75_driver as driver
from research import full_complement_row75_independent as independent

POINTS = ((0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,1),(1,2),(1,3))
SOURCE_PINS = {
    'full_complement_row75_core.py':'aa463fe45df59865660659a58a4f23d70ca677f232859fd228a4b4a7c4010f2b',
    'full_complement_row75_primary.py':'2780666ac7f2a1d31e4b735135164fd4f0baf6c06b1424fb6eff405d01006e0e',
    'full_complement_row75_independent.py':'c8fcea3629d5a4d3ccac5f92d925a3e88306fa3e747b40f109142d310dbe07e3',
    'full_complement_row75_driver.py':'970eacf3f4a9e95141d83a227cffc3a835eca14c746dbd08860fc089ca999ffc'}


def check_sources():
    for name,expected in SOURCE_PINS.items():
        core.require(core.sha((Path(__file__).parent/name).read_bytes()) == expected,'frozen test source '+name)


def baseline_map():
    result = dict(driver.MODULE_IDENTITIES)
    result.update({driver.POINT_PATH:driver.POINT_SHA,driver.HANDOFF_PATH:driver.HANDOFF_SHA,
                   driver.HANDOFF_REVIEW:driver.HANDOFF_REVIEW_SHA,'src/verify.py':driver.VERIFIER_SHA,
                   str(Path(driver.__file__).resolve()):SOURCE_PINS['full_complement_row75_driver.py'],
                   str(Path(driver.sys.executable).resolve()):'1'*64})
    return result


def schema_checks():
    handoff = {'schema':1,'n':75,'point_count':149,'raw_score':64,'normalized_sha256':driver.POINT_SHA,
               'snapshot':{'path':driver.POINT_PATH,'sha256':driver.POINT_SHA,'bytes':driver.POINT_BYTES},
               'provenance':deepcopy(driver.PROVENANCE),'scope':'pure coordinate-free declared test metadata'}
    driver.validate_handoff(handoff)
    mapping = baseline_map()
    manifest = driver.ROOT/'data/full-complement-row75-test-map-only.json'
    driver.check_manifest_map(mapping,manifest)
    rejections = []
    def reject(label,operation):
        try:
            operation()
        except (ValueError,TypeError) as exc:
            rejections.append({'case':label,'error':str(exc)[:300]})
        else:
            raise AssertionError(label)
    for name in tuple(mapping):
        changed = dict(mapping)
        del changed[name]
        reject('missing_pin:'+name,lambda changed=changed:driver.check_manifest_map(changed,manifest))
    for name in tuple(driver.MODULE_IDENTITIES)+(driver.POINT_PATH,driver.HANDOFF_PATH,driver.HANDOFF_REVIEW,'src/verify.py'):
        changed = dict(mapping)
        changed[name] = '0'*64
        reject('changed_mandatory_digest:'+name,lambda changed=changed:driver.check_manifest_map(changed,manifest))
    changed = dict(mapping)
    changed[str(manifest)] = '0'*64
    reject('manifest_self',lambda:driver.check_manifest_map(changed,manifest))
    changed = dict(mapping)
    changed['research/./full_complement_row75_core.py'] = SOURCE_PINS['full_complement_row75_core.py']
    reject('normalized_alias',lambda:driver.check_manifest_map(changed,manifest))
    for descriptor in driver.PROVENANCE.values():
        changed = dict(mapping)
        changed[descriptor['path']] = descriptor['sha256']
        reject('forbidden_history_pin:'+descriptor['path'],lambda changed=changed:driver.check_manifest_map(changed,manifest))
    for key in ('schema','n','point_count','raw_score'):
        changed = deepcopy(handoff)
        changed[key] = True
        reject('boolean_handoff:'+key,lambda changed=changed:driver.validate_handoff(changed))
    changed = deepcopy(handoff)
    changed['snapshot']['bytes'] = True
    reject('boolean_snapshot_size',lambda:driver.validate_handoff(changed))
    changed = deepcopy(handoff)
    del changed['provenance']['accepted_audit']
    reject('missing_provenance',lambda:driver.validate_handoff(changed))
    reject('duplicate_json',lambda:core.decode(b'{"a":1,"a":2}'))
    reject('nonfinite_json',lambda:core.decode(b'{"a":NaN}'))
    for label,points,n in [('boolean_n',POINTS,True),('missing',POINTS[:-1],5),
                           ('boolean_cell',((False,0),)+POINTS[1:],5),('duplicate',POINTS[:-1]+(POINTS[0],),5)]:
        reject(label,lambda points=points,n=n:core.validate_points(points,n))
    return rejections


class MemoryStore:
    def __init__(self,budget):
        self.budget = budget
        self.references = {}
        self.events = []
        self.uncertain = False

    def prepare(self,value,cap):
        self.events.append('prepare')
        raw = core.compact(value)
        core.require(len(raw) <= cap,'stub byte cap')
        self.budget.check_graph(value,raw)
        return raw

    def commit_prepared(self,name,raw,cap,*,urgent=False):
        self.budget.charge('publications','persistence',timed=not urgent)
        self.events.append('commit:'+name+':'+str(urgent))
        reference = {'path':name,'bytes':len(raw),'sha256':core.sha(raw)}
        self.references[name] = reference
        return reference


def zero_case(mode):
    state = {'time':0.0,'candidate_direct':0,'candidate_endpoint':0}
    def check(boundary):
        if state['time'] >= boundary:
            raise TimeoutError('scripted boundary '+str(boundary))
    work = lambda:check(23)
    final = lambda:check(25)
    owned = lambda:check(30)
    budget = core.Budget(work)
    store = MemoryStore(budget)
    def records(*args):
        state['time'] = 22.9
        yield {'row':0,'current':(0,1),'best':(2,3),'best_score':0}
    primary = SimpleNamespace(costs=lambda *args:{'baseline':14,'costs':[[0]*5 for _ in range(5)]},row_records=records)
    def direct(points,n,budget,component='independent_baseline'):
        if component == 'independent_baseline':
            return 14
        state['candidate_direct'] += 1
        state['time'] = 25.1 if mode == 'late_second_start' else 24.8
        budget.charge('raw_triples','synthetic')
        return 0
    def endpoint(points,n,budget,component='independent_candidate_lines'):
        state['candidate_endpoint'] += 1
        state['time'] = 30.1 if mode == 'owned_expiry' else 26.0
        budget.charge('pair_lines','synthetic')
        return 0
    try:
        with patch.object(independent,'direct_raw',direct),patch.object(independent,'endpoint_raw',endpoint):
            report = driver.diagnose(POINTS,5,14,{}, {'snapshot_sha256':driver.TINY_SHA},store,budget,primary,independent,core,
                                    work_check=work,final_check=final,owned_check=owned)
    except TimeoutError:
        core.require(mode != 'late_second_finish' and not store.references,'expired stub saved nothing')
        if mode == 'late_second_start':
            core.require(state['candidate_endpoint'] == 0,'second validator refused before start')
        return {'mode':mode,'expected_refusal':True,'events':store.events,'real_geometry':0}
    core.require(mode == 'late_second_finish' and report['witness_saved'] and not report['profile_verified']
                 and not report['diagnostic_complete'] and store.events[-1] == 'commit:witness.json:True',
                 'late validated zero immediate declared save')
    return {'mode':mode,'declared_witness_saved':True,'events':store.events,'real_geometry':0,
            'limitation':'raw results and persistence are explicit stubs; this is not a zero witness or durability test'}


def run():
    check_sources()
    rejected = schema_checks()
    counters = []
    for kind,limit in core.LIMITS.items():
        budget = core.Budget()
        budget.counts[kind] = limit
        try:
            budget.charge(kind,'synthetic')
        except core.QuotaExceeded:
            counters.append(kind)
        else:
            raise AssertionError('counter did not refuse before operation')
    zero = [zero_case(mode) for mode in ('late_second_finish','late_second_start','owned_expiry')]
    check_sources()
    return {'passed':True,'source_pins':SOURCE_PINS,'source_sha256':core.sha(Path(__file__).read_bytes()),
            'schema_rejections':rejected,'seeded_counter_refusals':counters,'stubbed_zero_modes':zero,
            'real_geometric_operations':0,'resource_envelope_executed':False,
            'scope':'Pure manifest/handoff/schema checks, synthetic counters and fully stubbed zero orchestration. No actual loader, real geometry, fsync or actual outcome claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('immutable evidence exists')
    try:
        result = run()
    except Exception as exc:
        failed = args.output.with_name(args.output.stem+'-failure.json')
        with failed.open('x') as output:
            json.dump({'passed':False,'error':type(exc).__name__+': '+str(exc)[:1000],'real_geometry':0},output,sort_keys=True)
        raise
    raw = (json.dumps(result,sort_keys=True,indent=2)+'\n').encode('ascii')
    core.require(len(raw) <= 64*1024,'pregeometry evidence cap')
    with args.output.open('xb') as output:
        core.require(output.write(raw) == len(raw),'complete evidence write')


if __name__ == '__main__':
    main()
