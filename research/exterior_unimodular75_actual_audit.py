"""Independent read-only negative-certificate audit; run only after actual completion.

No worker imports or search. Reconstructs the finite domain and candidate coverage
from the saved source and certificate. Outer owned guard must bound execution.
"""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/'data/published-n74.json'
FIXTURE_SHA = '276340cef4486bd33666a664e2eba968cbef7deda4398c26590f1307ccf280d4'
NORM = '3c9c8bf350cb3441dfcef0cdef24a3ba2d53cd0895a3885da18680e2407f27a5'
WORKER_SHA = 'c06b018195fd11f262e61c1f61aa0b18fba1cc531dc1d7cc8f64b3e4639b36df'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(65536): h.update(block)
    return h.hexdigest()


def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def dot(a,p): return a[0]*p[0]+a[1]*p[1]
def norm(mapping):
    if type(mapping) is not dict: raise ValueError('pin map')
    result = {str((ROOT/Path(k)).resolve()): v for k,v in mapping.items()}
    if len(result) != len(mapping): raise ValueError('duplicate normalized pins')
    return result


def validate(report_path, receipt_path, manifest_path, expected_manifest_sha):
    report_path, receipt_path, manifest_path = map(Path, (report_path, receipt_path, manifest_path))
    if sha(manifest_path) != expected_manifest_sha: raise ValueError('manifest digest')
    manifest_raw, report_raw, receipt_raw = (p.read_bytes() for p in (manifest_path, report_path, receipt_path))
    manifest = json.loads(manifest_raw); report = json.loads(report_raw); job = json.loads(receipt_raw)
    snapshot_hashes = [hashlib.sha256(b).hexdigest() for b in (manifest_raw, report_raw, receipt_raw)]
    if snapshot_hashes[0] != expected_manifest_sha: raise ValueError('manifest snapshot digest')
    pins = norm(manifest); manifest_path = manifest_path.resolve()
    if str(manifest_path) in pins: raise ValueError('manifest self entry')
    pins[str(manifest_path)] = expected_manifest_sha
    if pins != norm(report['pins']) or pins != norm(job['sources_before']): raise ValueError('manifest/report/receipt pins')
    if pins.get(str(FIXTURE)) != FIXTURE_SHA or pins.get(str(ROOT/'research/exterior_unimodular75.py')) != WORKER_SHA or str(ROOT/'src/verify.py') not in pins:
        raise ValueError('required source pins')
    for path, expected in pins.items():
        if sha(path) != expected: raise ValueError('source pin drift')
    argv = [str(ROOT/'.venv/bin/python'), 'research/exterior_unimodular75.py', '--seconds', '25', '--output-dir',
            str(report_path.resolve().parent.relative_to(ROOT)), '--source-pins', str(manifest_path.relative_to(ROOT))]
    if job.get('status') != 'completed' or job.get('sources_unchanged') is not True or job.get('argv') != argv: raise ValueError('job binding')
    gate = job['gate']
    if any(type(gate.get(k)) is not int for k in ('returncode','seconds_limit','rss_limit_mib','peak_sampled_rss_kib','rss_samples','cleanup_samples')): raise ValueError('gate integer types')
    if (gate.get('gate_status') != 'exited' or gate['returncode'] != 0 or gate.get('cleanup_status') != 'clean'
        or gate.get('cleanup_error') is not None or gate.get('monitor_error') is not None or gate.get('trigger_gate_status') is not None
        or gate['seconds_limit'] != 30 or gate['rss_limit_mib'] != 256 or not 0 < gate['peak_sampled_rss_kib'] <= 256*1024
        or gate['rss_samples'] < 1 or gate['cleanup_samples'] < 1): raise ValueError('guard failure')
    elapsed = [report.get('elapsed_seconds'),gate.get('elapsed_seconds'),job.get('elapsed_seconds')]
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in elapsed) or not 0 <= elapsed[0] < 25 or not 0 < elapsed[1] < 30 or not 0 < elapsed[2] <= 30 or not elapsed[0] <= elapsed[1] <= elapsed[2]:
        raise ValueError('elapsed binding')
    if (report.get('method') != 'selected_n74_exterior_unimodular_extension' or report.get('status') != 'selected_exterior_family_obstructed'
        or report.get('complete') is not True or report.get('closure') is not True or report.get('identity_valid') is not True
        or report.get('witness_saved') is not False or report.get('source_record') != 1 or report.get('source_sha256') != FIXTURE_SHA
        or report.get('normalized_source_sha256') != NORM): raise ValueError('negative report status')
    family = report['family']
    if family.get('ordinary_axis_frames_excluded') is not True or family.get('signed_row_permutations_quotiented') is not True: raise ValueError('family flags')
    if family != {'source_n':74,'target_n':75,'determinants':[-1,1],'protected_closed_box':[-1,74],
                  'ordinary_axis_frames_excluded':True,'signed_row_permutations_quotiented':True}: raise ValueError('family identity')
    checks = report.get('source_validation')
    if type(checks) is not list or len(checks) != 2: raise ValueError('source validator count')
    for item, algorithm in zip(checks, ('integer_normalized_slopes','integer_cross_products')):
        if item.get('algorithm') != algorithm or item.get('valid') is not True or item.get('n') != 74 or item.get('point_count') != 148 or item.get('normalized_sha256') != NORM or item.get('errors') != [] or item.get('conflict_count') != 0 or item.get('conflicts') != []: raise ValueError('source validator')
    source = json.loads(FIXTURE.read_text()); points = sorted(tuple(p) for p in source['points'])
    canonical = json.dumps({'n':74,'points':[list(p) for p in points]},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    if (source.get('n') != 74 or source.get('source_record') != 1 or len(points) != 148 or len(set(points)) != 148
        or any(len(p) != 2 or any(type(v) is not int or not 0 <= v < 74 for v in p) for p in points)
        or any(Counter(p[a] for p in points) != Counter({v:2 for v in range(74)}) for a in (0,1))
        or hashlib.sha256(canonical).hexdigest() != NORM): raise ValueError('fixture geometry identity')
    analysis = report['analysis']; inv = analysis['inventory']
    if any(analysis.get(k) is not True for k in ('inventory_complete','candidates_complete','pairs_complete','family_complete','certificate_complete')) or analysis.get('survivors') != []: raise ValueError('incomplete classification')
    if inv.get('inventory_complete') is not True or [list(p) for p in points] != inv['points']: raise ValueError('inventory source')
    rows = {}; cols = {}
    for i,(x,y) in enumerate(points): rows.setdefault(y,[]).append(i); cols.setdefault(x,[]).append(i)
    h, hw = max((abs(points[i][0]-points[j][0]), (i,j)) for i,j in rows.values())
    v, vw = max((abs(points[i][1]-points[j][1]), (i,j)) for i,j in cols.values())
    if (inv['H'],inv['V'],tuple(inv['H_witness']),tuple(inv['V_witness']),inv['a_bound'],inv['b_bound']) != (h,v,hw,vw,74//h,74//v): raise ValueError('axis witnesses/cutoffs')
    expected = {(a,b) for a in range(-74//h-1,74//h+1) for b in range(-74//v-1,74//v+1)
                if abs(a) <= 74//h and abs(b) <= 74//v and (a > 0 or a == 0 and b > 0) and math.gcd(abs(a),abs(b)) == 1}
    seen=set(); admitted={}
    for accepted, records in ((True,inv['admitted']),(False,inv['rejected'])):
        for record in records:
            u=tuple(record['vector'])
            if u not in expected or u in seen or any(type(x) is not int for x in u): raise ValueError('direction coverage')
            seen.add(u)
            if accepted:
                values=[dot(u,p) for p in points]; lo,hi=min(values),max(values)
                if hi-lo not in (73,74) or (record['min'],record['max'],record['width']) != (lo,hi,hi-lo): raise ValueError('accepted width')
                if record['levels'] != [list(x) for x in sorted(Counter(values).items())]: raise ValueError('level histogram')
                for key,level in (('min_index',lo),('max_index',hi)):
                    i=record[key]
                    if type(i) is not int or not 0<=i<148 or values[i] != level: raise ValueError('extreme index')
                admitted[u]=values
            else:
                i,j=record['indices']
                if type(i) is not int or type(j) is not int or not 0<=i<148 or not 0<=j<148 or i==j or abs(dot(u,points[i])-dot(u,points[j])) <=74: raise ValueError('rejected width witness')
    if seen != expected or len(admitted)>4 or not {(1,0),(0,1)} <= admitted.keys(): raise ValueError('inventory incomplete')
    signed=set(admitted)|{(-a,-b) for a,b in admitted}|{(0,0)}
    if len({(a%3,b%3) for a,b in signed}) != len(signed): raise ValueError('mod3 contradiction')
    frames=[(u,v) for u,v in combinations(sorted(admitted),2) if abs(cross(u,v))==1 and {u,v}!={(1,0),(0,1)}]
    if len(frames)>5 or [[list(u),list(v)] for u,v in frames] != analysis['frames']: raise ValueError('frame completeness')
    choices=[]; eligible={}; exclusions=[]
    for u,v in frames:
        xx,yy=admitted[u],admitted[v]; d=cross(u,v)
        for tx in range(-min(xx),75-max(xx)):
            for ty in range(-min(yy),75-max(yy)):
                image={(x+tx,y+ty) for x,y in zip(xx,yy)}; cx=Counter(x for x,y in image); cy=Counter(y for x,y in image)
                for x in range(75):
                    for y in range(75):
                        if cx[x]>=2 or cy[y]>=2: continue
                        a,b=x-tx,y-ty; q=((v[1]*a-u[1]*b)//d,(-v[0]*a+u[0]*b)//d)
                        if (dot(u,q)+tx,dot(v,q)+ty)!=(x,y): raise ValueError('inverse')
                        reason = 'occupied' if (x,y) in image else 'protected' if -1<=q[0]<=74 and -1<=q[1]<=74 else 'duplicate' if q in eligible else 'eligible'
                        item={'frame':[list(u),list(v)],'translation':[tx,ty],'added':[x,y],'preimage':list(q),'reason':reason}; choices.append(item)
                        if reason=='eligible': eligible[q]=item
                        else: exclusions.append(item)
    if len(choices)>20 or choices != analysis['candidate_choices'] or exclusions != analysis['exclusions'] or list(eligible.values()) != analysis['eligible_candidates']:
        raise ValueError('candidate coverage')
    seen_q=set()
    for item in analysis['pair_obstructions']:
        q=tuple(item['preimage']); i,j=item['indices']
        if len(q) != 2 or any(type(x) is not int for x in q): raise ValueError('obstruction preimage types')
        if q not in eligible or q in seen_q or type(i) is not int or type(j) is not int or not 0<=i<j<148: raise ValueError('obstruction identity')
        a,b=points[i],points[j]
        if (b[0]-a[0])*(q[1]-a[1]) != (b[1]-a[1])*(q[0]-a[0]): raise ValueError('obstruction determinant')
        seen_q.add(q)
    if seen_q != set(eligible): raise ValueError('obstruction coverage')
    if [sha(p) for p in (manifest_path, report_path, receipt_path)] != snapshot_hashes: raise ValueError('audit snapshot changed')
    return {'accepted':True,'scope':'selected source exterior unimodular family only','directions':len(admitted),'frames':len(frames),
            'choices':len(choices),'eligible':len(eligible),'obstructions':len(seen_q),'pins_checked':len(pins),
            'report_sha256':snapshot_hashes[1],'receipt_sha256':snapshot_hashes[2],'manifest_sha256':expected_manifest_sha}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--report',type=Path,required=True); p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True); p.add_argument('--manifest-sha256',required=True); a=p.parse_args()
    print(json.dumps(validate(a.report,a.receipt,a.manifest,a.manifest_sha256),sort_keys=True))


if __name__ == '__main__': main()
