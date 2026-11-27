"""Stream the fixed score-11 paired-three-rotation neighborhood; no unapproved host run."""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.score11_cover_repair import load_source, SOURCE_NORMALIZED, SOURCE_BYTES
from research.diagonal_secant_checkpoint import atomic, encode
from src.trade_search import decompose
from src.verify import collinear_triples, verify_certificate, verify_certificate_bruteforce

ANCHORS=((33,78),(78,78))
EXPECTED_ROWS=(9,12,18,26,28,33,34,36,38,39,40,41,42,48,50,55,56,57,60,67,78)
EXPECTED_TOTAL=144400


def rotated_pair(permutations, rowsets, signs):
    """Rotate both matchings simultaneously, returning final points or None."""
    n=len(permutations[0]); new=[p[:] for p in permutations]
    for color in (0,1):
        rows=tuple(rowsets[color]); sign=signs[color]
        if len(rows)!=3 or len(set(rows))!=3 or any(not 0<=r<n for r in rows) or sign not in (-1,1):
            raise ValueError('invalid rotation')
        old=[permutations[color][r] for r in rows]
        for i,r in enumerate(rows):
            new[color][r]=old[(i+sign)%3]
    if any(new[0][r]==new[1][r] for r in range(n)):
        return None
    return {(r,new[c][r]) for c in (0,1) for r in range(n)}


def old_conflict_possible(conflicts, removed):
    """A surviving old triple requires one common point for a 157 result."""
    survivors=[set(t) for t in conflicts if not set(t)&removed]
    return not survivors or bool(set.intersection(*survivors))


def conflict_deletion_candidates(points):
    """None means a valid full set, otherwise all one-point conflict covers."""
    ordered=sorted(points)
    triples=collinear_triples(ordered)
    if not triples:
        return None
    sets=[{ordered[i] for i in triple} for triple in triples]
    return set.intersection(*sets)


def run(source, out, seconds, *, clock=time.monotonic):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or not 0<seconds<=25:
        raise ValueError('invalid soft duration')
    start=clock();deadline=start+seconds
    points, conflicts=load_source(source)
    rows=tuple(sorted({p[0] for triple in conflicts for p in triple}))
    if rows!=EXPECTED_ROWS:
        raise ValueError('conflict row pool mismatch')
    permutations=decompose(points,79)
    if permutations[0][ANCHORS[0][0]] != ANCHORS[0][1] or permutations[1][ANCHORS[1][0]] != ANCHORS[1][1]:
        raise ValueError('source decomposition mismatch')
    report={'method':'paired-three-edge-rotations','scope':'fixed source, deterministic decomposition and original-conflict incident rows only',
            'source_bytes_sha256':SOURCE_BYTES,'source_normalized_sha256':SOURCE_NORMALIZED,
            'declared_combinations':EXPECTED_TOTAL,'complete':False,'status':'incomplete',
            'processed':0,'collision_rejections':0,'old_conflict_rejections':0,'geometry_checked':0,'witnesses':0}
    def emit(pts):
        cert={'n':79,'points':[list(p) for p in sorted(pts)]}
        checks=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
        if any(not c['valid'] or c['point_count']<157 for c in checks) or checks[0]['normalized_sha256']!=checks[1]['normalized_sha256']:
            raise RuntimeError('witness verification failed')
        digest=checks[0]['normalized_sha256']
        cert['metadata']={'method':'score11_paired_rotations','source_normalized_sha256':SOURCE_NORMALIZED,
                          'normalized_sha256':digest,'novelty_claim':False}
        atomic(out/('witness-'+digest+'.json'),encode(cert))
        report['witnesses']+=1
    choices0=tuple(itertools.combinations((r for r in rows if r!=ANCHORS[0][0]),2))
    choices1=tuple(itertools.combinations((r for r in rows if r!=ANCHORS[1][0]),2))
    if 4*len(choices0)*len(choices1)!=EXPECTED_TOTAL:
        raise ValueError('candidate count mismatch')
    try:
        for c0,c1,s0,s1 in itertools.product(choices0,choices1,(-1,1),(-1,1)):
            if clock()>=deadline:
                raise TimeoutError
            new=rotated_pair(permutations,((ANCHORS[0][0],*c0),(ANCHORS[1][0],*c1)),(s0,s1))
            report['processed']+=1
            if new is None:
                report['collision_rejections']+=1;continue
            removed=points-new
            if not old_conflict_possible(conflicts,removed):
                report['old_conflict_rejections']+=1;continue
            report['geometry_checked']+=1
            deletion=conflict_deletion_candidates(new)
            if deletion is None:
                emit(new); report['status']='witness';break
            if deletion:
                emit(new-{min(deletion)}); report['status']='witness';break
        else:
            report['status']='complete';report['complete']=True
    except TimeoutError:
        report['status']='timeout'
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.source,a.output_dir,a.seconds)
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status'] in ('complete','witness') else 2


if __name__=='__main__':
    sys.exit(main())
