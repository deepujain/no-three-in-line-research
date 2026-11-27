"""Independent synthetic production comparison. Never reads the n74 fixture."""
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import struct

from research import nonuniform_insertion75 as worker
from research import nonuniform_insertion_independent_tiny_oracle as oracle


def decoded(bits, n):
    assert type(bits) is int and bits >= 0 and bits.bit_length() <= (n+1)**2
    return {divmod(i, n+1) for i in range((n+1)**2) if bits & (1 << i)}


def rejected(call):
    try:
        call()
    except (ValueError, TypeError):
        return
    raise AssertionError('invalid input accepted')


def main():
    counts = dict(sources=0, family_runs=0, target_comparisons=0, certificate_checks=0,
                  early_cover_runs=0, positive_complete_runs=0, rectangles=0, lines=0,
                  threshold_cases=0, invalid_full_axis_sources=0, malformed_sources=0,
                  certificate_mutations=0, deadline_falsifiers=0)
    saved = {}
    for n in (2, 3, 4):
        saved[n] = [tuple(sorted(p)) for p in oracle.full_axis_sources(n)]
        for points in saved[n]:
            counts['sources'] += 1
            expected = oracle.expected_gaps(points, n)
            for exclude in (False, True):
                included = {gap for gap, info in expected.items() if not exclude or not info['excluded']}
                old = {gap for gap in included if expected[gap]['old']}
                new = {gap for gap in included if expected[gap]['new']}
                valid = {gap for gap in included if expected[gap]['valid']}
                full = worker.cover_family(points, n, exclude_corners=exclude, exhaustive=True)
                fast = worker.cover_family(tuple(reversed(points)), n, exclude_corners=exclude)
                assert full['old_complete'] and full['new_complete'] and full['geometry_complete']
                assert decoded(full['old_blocked'], n) == old
                assert decoded(full['new_blocked'], n) == new
                for result in (full, fast):
                    counts['family_runs'] += 1
                    counts['target_comparisons'] += len(included)
                    assert decoded(result['included'], n) == included
                    assert decoded(result['uncovered'], n) == valid
                    assert set(result['certificates']) == included-valid
                    assert result['certificate_complete'] == (not valid)
                    assert decoded(result['old_blocked'], n) <= old
                    assert decoded(result['new_blocked'], n) <= new
                    if result['old_complete']:
                        assert decoded(result['old_blocked'], n) == old
                    if result['new_complete']:
                        assert decoded(result['new_blocked'], n) == new
                    if valid:
                        assert result['geometry_complete']
                        counts['positive_complete_runs'] += 1
                    elif not result['geometry_complete']:
                        counts['early_cover_runs'] += 1
                    for gap, cert in result['certificates'].items():
                        assert tuple(cert['indices']) in expected[gap][cert['kind']]
                        if not expected[gap]['excluded']:
                            oracle.check_certificate(points, n, gap, cert['kind'], cert['indices'])
                        else:
                            triple = [expected[gap]['target'][i] for i in cert['indices']]
                            if cert['kind'] == 'new': triple.append(gap)
                            assert len(set(triple)) == 3 and oracle.collinear(*triple)
                        counts['certificate_checks'] += 1
                assert full['counters']['rectangle_tests'] <= 12*len(tuple(combinations(points, 3)))
        for c0 in range(n+1):
            for c1 in range(c0, n+1):
                for r0 in range(n+1):
                    for r1 in range(r0, n+1):
                        rect = c0,c1,r0,r1
                        assert decoded(worker.rectangle_mask(*rect,n),n) == oracle.rectangle_cells(rect)
                        counts['rectangles'] += 1
        for k in (1,2,3,4):
            for coords in product(range(n),repeat=k):
                intervals = worker.threshold_intervals(coords,n)
                assert [v for lo,hi in intervals for v in range(lo,hi+1)] == list(range(n+1))
                assert all(lo <= hi for lo,hi in intervals)
                for lo,hi in intervals:
                    assert len({tuple(v >= gap for v in coords) for gap in range(lo,hi+1)}) == 1
                assert len({tuple(v >= lo for v in coords) for lo,hi in intervals}) == len(intervals)
                counts['threshold_cases'] += 1
        choices = tuple(combinations(range(n),2))
        for rows in product(choices,repeat=n):
            if any(sum(c in row for row in rows) != 2 for c in range(n)): continue
            points = tuple((c,r) for r,row in enumerate(rows) for c in row)
            if oracle.triples(points):
                counters = {}
                rejected(lambda: worker.cover_family(points,n,counters=counters))
                assert not counters['precomputation_complete'] and not counters.get('kernel_source_valid')
                counts['invalid_full_axis_sources'] += 1
    for p,q,bounds,expected in oracle.line_cases():
        actual = list(worker.clipped_line_points(p,q,bounds))
        assert len(actual) == len(set(actual)) and set(actual) == expected
        counts['lines'] += 1
    rejected(lambda: list(worker.clipped_line_points((0,0),(0,0),(0,1,0,1))))
    rejected(lambda: list(worker.clipped_line_points((0,0),(1,1),(1,0,0,1))))
    base = saved[2][0]
    malformed = [(base[:-1],2),(base+(base[0],),2),((base[0],)*4,2),
                 (((-1,0),)+base[1:],2),(((0,2),)+base[1:],2),
                 (((False,0),)+base[1:],2),(((0.0,0),)+base[1:],2),
                 (((0,),)+base[1:],2),(base,True),(base,1),(base,75)]
    for points,n in malformed:
        rejected(lambda: worker.cover_family(points,n)); counts['malformed_sources'] += 1
    n=3; points=saved[n][0]; result=worker.cover_family(points,n)
    records=bytearray(4*(n+1)**2)
    for (c,r),cert in result['certificates'].items():
        fields=(1,*cert['indices']) if cert['kind']=='old' else (2,*cert['indices'],0)
        struct.pack_into('<BBBB',records,4*((n+1)*c+r),*fields)
    assert worker.verify_obstructions(points,n,result['included'],result['uncovered'],records)==result['certificates']
    gap=next(iter(result['certificates'])); offset=4*((n+1)*gap[0]+gap[1])
    for values in ((0,0,0,0),(3,0,1,2),(1,0,0,1),(1,0,1,255),(2,0,1,1)):
        changed=bytearray(records);struct.pack_into('<BBBB',changed,offset,*values)
        rejected(lambda: worker.verify_obstructions(points,n,result['included'],result['uncovered'],changed))
        counts['certificate_mutations'] += 1
    changed=bytearray(records);struct.pack_into('<BBBB',changed,0,2,0,1,0)
    rejected(lambda: worker.verify_obstructions(points,n,result['included'],result['uncovered'],changed))
    counts['certificate_mutations'] += 1
    for phase in ('kernel_source_validation','precomputation','old_triples','new_pairs','certificate_verification'):
        counters={}
        def stop():
            if counters.get('phase')==phase: raise TimeoutError('independent phase stop')
        try: worker.cover_family(base,2,check=stop,counters=counters)
        except TimeoutError: counts['deadline_falsifiers'] += 1
        else: raise AssertionError('deadline swallowed')
    counters={}
    def after_assignment():
        if counters.get('assigned_gaps',0)>0: raise TimeoutError('independent partial coverage stop')
    try: worker.cover_family(points,3,check=after_assignment,counters=counters)
    except TimeoutError: counts['deadline_falsifiers'] += 1
    else: raise AssertionError('partial coverage was returned as complete')
    root=Path(__file__).resolve().parents[1]
    paths=[Path(__file__),Path(worker.__file__),Path(oracle.__file__)]
    report={'passed':True,'counts':counts,'pins':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'scope':'Independent synthetic n2..4 geometry, certificate and helper comparisons only; no actual source read or census.'}
    (root/'data/nonuniform-insertion-independent-worker-audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=='__main__':main()
