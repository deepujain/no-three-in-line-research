"""Audit one corner, checking the source symmetry that makes four equivalent."""
import argparse
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.guided_repair import audit_translation
from src.verify import verify_certificate,verify_certificate_bruteforce


def quarter_turn_invariant(seed):
    n=seed['n']
    points={tuple(p) for p in seed['points']}
    return {(n-1-y,x) for x,y in points} == points


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=Path,default=ROOT/'data/published-n78.json')
    parser.add_argument('--max-deletions',type=int,default=4)
    parser.add_argument('--seconds',type=float,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds<=0:
        parser.error('seconds must be finite and positive')
    start=time.monotonic()
    seed=json.loads(args.seed.read_text())
    if not all(check(seed)['valid'] for check in (verify_certificate,verify_certificate_bruteforce)):
        parser.error('invalid source seed')
    if not quarter_turn_invariant(seed):
        parser.error('cannot infer corner equivalence without exact source quarter-turn invariance')
    result=audit_translation(seed,0,0,args.max_deletions,deadline=start+args.seconds)
    report={'method':'exact_single_corner_with_checked_source_rotation',
            'source_quarter_turn_checked':True,'computed_corner_count':1,
            'equivalent_corner_count':4,'status':result['status'],
            'elapsed_seconds':time.monotonic()-start,'result':result,
            'scope':'Only this source and this deletion budget; a completed representative audit transfers to all four corners by rotation. Counts are computed once, not four times.',
            'symmetry_argument':'If R_n(S)=S, R_(n+1) maps S+(0,0) to S+(1,0), then to +(1,1), then +(0,1). It bijects deleted and inserted sets and preserves all collinearity.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ['status','elapsed_seconds','computed_corner_count','equivalent_corner_count']}))
    return 0 if result['status']=='complete' else 2


if __name__=='__main__':
    sys.exit(main())
