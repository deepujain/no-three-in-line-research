"""Only the unprocessed suffix of the pinned score-11 cap-five run."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.score11_five_deletion_repair import (deletion_sets, EXPECTED, SOURCE_BYTES, SOURCE_NORMALIZED,
    HELPER_HASH, REPORT_HASH, ARITHMETIC_HASH, load_source, minimal_covers, search_cover)
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import verify_certificate, verify_certificate_bruteforce

PARENT_HASH = '68fad229ed12321915d5d592f3ceb8500b6c487045d943d2498ab6db00cd307b'
RECEIPT_HASH = '26f7208add6790e769375017cbf5971bfbab45b3683001ff58befd4ff7afedc1'
SOURCE_HASH = 'bdb663f446701fec5d93d4f13fdd7a65f9065e5319f12ab02971e0e8fd65ac54'
PREFIX = 33062
TOTAL = 35809


def checked_json(path, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('pinned input hash mismatch')
    return json.loads(data)


def suffix(deletions, prefix, total):
    if type(prefix) is not int or type(total) is not int or len(deletions) != total or not 0 <= prefix <= total:
        raise ValueError('invalid prefix or total')
    if len(set(deletions)) != total or deletions != sorted(deletions, key=lambda x:(len(x),tuple(sorted(x)))):
        raise ValueError('unordered or duplicated census')
    return deletions[prefix:]


def run(source, predecessor, arithmetic, parent, receipt, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0 < seconds <= 25:
        raise ValueError('invalid soft duration')
    start=clock(); deadline=start+seconds
    for path,digest in ((ROOT/'research/score11_five_deletion_repair.py',SOURCE_HASH),
                        (ROOT/'research/score11_cover_repair.py',HELPER_HASH)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('frozen source mismatch')
    prior = checked_json(predecessor, REPORT_HASH)
    ar = checked_json(arithmetic, ARITHMETIC_HASH)
    parent_report = checked_json(parent, PARENT_HASH)
    receipt_report = checked_json(receipt, RECEIPT_HASH)
    if (prior.get('complete') is not True or prior.get('status') != 'complete' or
        {frozenset(map(tuple,c)) for c in prior['covers']} != EXPECTED or
        ar.get('source_sha256') != SOURCE_BYTES or ar.get('all_source_hitting_sets_through5') != TOTAL):
        raise ValueError('prior cover or arithmetic mismatch')
    if (parent_report.get('status') != 'timeout' or parent_report.get('complete') is not False or
        parent_report.get('completed_deletion_sets') != PREFIX or parent_report.get('deletion_set_count') != TOTAL or
        parent_report.get('source_normalized_sha256') != SOURCE_NORMALIZED or parent_report.get('witness_events') != 0):
        raise ValueError('parent report does not identify expected prefix')
    gate=receipt_report.get('gate',{})
    if (receipt_report.get('status') != 'completed' or receipt_report.get('sources_unchanged') is not True or
        gate.get('gate_status') != 'worker_error' or gate.get('returncode') != 2 or
        gate.get('trigger_gate_status') is not None or gate.get('cleanup_status') != 'clean'):
        raise ValueError('parent process receipt not accepted timeout')
    points, conflicts=load_source(source)
    report={'scope':'Only the 2,747 deletion sets after the pinned completed prefix; not a family closure.',
            'status':'incomplete', 'complete':False, 'suffix_complete':False,
            'parent_report_sha256':PARENT_HASH, 'parent_receipt_sha256':RECEIPT_HASH,
            'source_normalized_sha256':SOURCE_NORMALIZED, 'prefix_count':PREFIX,
            'suffix_count':TOTAL-PREFIX, 'completed_suffix_sets':0, 'witness_events':0,
            'total_candidate_cells':0, 'total_nodes':0}
    def emit(pts):
        cert={'n':79,'points':[list(p) for p in sorted(pts)]}
        checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
        if any(not c['valid'] or c['point_count'] < 157 for c in checks) or checks[0]['normalized_sha256'] != checks[1]['normalized_sha256']:
            raise RuntimeError('witness verification failed')
        digest=checks[0]['normalized_sha256']
        cert['metadata']={'method':'score11_five_deletion_suffix','source_normalized_sha256':SOURCE_NORMALIZED,
                          'normalized_sha256':digest,'novelty_claim':False}
        path=out/('witness-'+digest+'.json')
        if path.exists():
            if json.loads(path.read_text()) != cert:
                raise RuntimeError('conflicting witness file')
        else:
            atomic(path,encode(cert))
        report['witness_events'] += 1
    try:
        covers=minimal_covers(conflicts,5,deadline,clock)
        if set(covers) != EXPECTED:
            raise ValueError('cover census mismatch')
        deletions=deletion_sets(points,covers,deadline,clock)
        if len(deletions) != TOTAL or [sum(len(d)==k for d in deletions) for k in (3,4,5)] != [3,462,35344]:
            raise ValueError('deletion census mismatch')
        for removed in suffix(deletions,PREFIX,TOTAL):
            detail=search_cover(79,points,set(removed),deadline,clock,emit)
            report['completed_suffix_sets'] += 1
            report['total_candidate_cells'] += detail['candidate_cells']
            report['total_nodes'] += detail['nodes']
        report['status']='suffix_complete'; report['suffix_complete']=True
    except TimeoutError:
        report['status']='timeout'
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('source','predecessor','arithmetic','parent','receipt','output-dir'):
        p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.source,a.predecessor,a.arithmetic,a.parent,a.receipt,a.output_dir,a.seconds)
    print(json.dumps(result,sort_keys=True))
    return 0 if result['suffix_complete'] else 2


if __name__=='__main__':
    sys.exit(main())
