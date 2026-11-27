"""Read-only f-factor measurements on six pinned packed prefixes; no DFS."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.near_quarter_packed_state import PackedOrbitState
from research.near_quarter_readonly_probe import probe_orbit
from research.near_quarter_radius_graph import component_obstruction
from research.near_quarter_radius_factor import radius_factor
from research.near_quarter_rowbatch_checkpoint import parse, TrustedRecord
from research.near_quarter_packed_worker import source_manifest
from research.diagonal_secant_checkpoint import atomic, encode
from src.verify import normalized_sha256

INPUTS=(
 ('main','data/packed-readonly-n79-r1.chain','6e1d4279da8a2a0123435e76ee3b4e83693706e82c915ff7cec74552f1811862','a285b9c657315e40c11cab0a76103614adf13981c2814b0ba3e8e59dfb8fc6db','data/packed-readonly-chain-main600-r2-independent-audit.json','5a7d4c14ece999dfab491b2310608d1993798aba9277c21254fd19c747891b50',19),
 ('middle','data/packed-readonly-n79-middle-d1541.chain','b858a09636b64df58721a85b02be6811dd543d62b4fa75802f925329108b707a','4b3bb11dd9726a209941373aab3aca135a27c8406c4794f6c83a7f758b856fd6','data/packed-middle-d1541-chain600-r2-independent-audit.json','a48901aec27ca60bc0742ff5d5b81dc5fad77a33cd52c46be7645476d0edb69e',20),
)


def read_pinned(path,digest,check):
    check(); data=path.read_bytes(); check()
    if hashlib.sha256(data).hexdigest()!=digest: raise ValueError('input hash mismatch')
    return data


def selected_prefix(parsed):
    """Selected path only; a pending batch has not been committed."""
    return (parsed.diagonals[parsed.slice_index],)+tuple(v for frame in parsed.frames for v in frame.incoming)


def prefix_paths(check):
    result=[]; pins=[]
    for label,chain,checkpoint,receipt,audit_path,audit_hash,expected_len in INPUTS:
        cpath=ROOT/chain/(checkpoint+'.nqrb');rpath=ROOT/chain/(receipt+'.receipt.json');apath=ROOT/audit_path
        audit=json.loads(read_pinned(apath,audit_hash,check)); rec=json.loads(read_pinned(rpath,receipt,check))
        raw=read_pinned(cpath,checkpoint,check)
        if audit.get('checkpoint')!=checkpoint or audit.get('final_receipt')!=receipt or rec.get('candidate_sha256')!=checkpoint or rec.get('result')!='eligible':
            raise ValueError('accepted evidence mismatch')
        if rec.get('source_manifest') != source_manifest(check): raise ValueError('source manifest mismatch')
        previous=rec['prior_accepted_record']
        parsed=parse(raw,trusted_record=TrustedRecord(bytes.fromhex(checkpoint),bytes.fromhex(previous['checkpoint_sha256']),bytes.fromhex(rec['chain_id'])),expected_identity=bytes.fromhex(previous['identity_hex']),check=check)
        ids=selected_prefix(parsed)
        if parsed.n!=79 or len(ids)-1!=expected_len: raise ValueError('path depth mismatch')
        for depth in sorted({0,expected_len//2,expected_len}):
            result.append((label,depth,tuple(ids[:depth+1])))
        pins.extend(((cpath,checkpoint),(rpath,receipt),(apath,audit_hash)))
    return result,pins


def mask_and_bounds(n,ids,check):
    state=PackedOrbitState(n,check=check)
    for variable in ids:
        check()
        if not state.push(variable): raise ValueError('invalid prefix')
    t=time.monotonic_ns(); mask=bytearray(state.bounds['four'])
    ones=[0]*n;twos=[0]*n;viable=0
    for variable in range(1,state.bounds['four']+1):
        check()
        if variable in state.selected or not probe_orbit(state,variable,check): continue
        mask[variable-1]=1;viable+=1
        ys=[y for x,y in state.model['orbits'][variable-1]]
        for row in set(ys):
            if state.rows[row]<2:
                (ones if ys.count(row)==1 else twos)[row]+=1
    check(); mask_ns=time.monotonic_ns()-t
    t=time.monotonic_ns(); remaining=state.bounds['m']-state.four_selected
    orbit_shortfall=viable<remaining
    row_shortfall=any(2*min(twos[row],remaining)+min(ones[row],max(0,remaining-twos[row]))<2-state.rows[row] for row in range(n) if state.rows[row]<2)
    mid=n//2;demands=[]
    for u in range(mid+1):
        check();load=state.rows[mid+u]
        if state.rows[mid-u]!=load or (u==0 and load%2): raise ValueError('incoherent radius loads')
        demands.append((2-load)//2 if u==0 else 2-load)
    if sum(demands)!=2*remaining: raise ValueError('radius demand mismatch')
    edges=[]
    for i,marked in enumerate(mask):
        check()
        if marked:
            x,y=state.model['orbits'][i][0]; edges.append((abs(x-mid),abs(y-mid)))
    graph_obstruction=component_obstruction(demands,edges,check)
    check(); bounds_ns=time.monotonic_ns()-t
    return {'ids':list(ids),'points_sha256':normalized_sha256(n,state.points), 'mask_sha256':hashlib.sha256(mask).hexdigest(),
            'mask':list(mask),'demands':demands,'edges':[list(e) for e in edges],
            'orbit_shortfall':orbit_shortfall,'row_shortfall':row_shortfall,'graph_obstruction':graph_obstruction,
            'mask_ns':mask_ns,'bounds_ns':bounds_ns}


def run(out, seconds, *, clock=time.monotonic):
    if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not 0<seconds<=4:
        raise ValueError('soft limit must be in (0,4]')
    start=clock();deadline=start+seconds
    def check():
        if clock()>=deadline: raise TimeoutError
    report={'method':'readonly_radius_factor_shadow','scope':'Only six fixed reachable prefixes; no DFS or frontier modification.',
            'status':'incomplete','complete':False,'samples':[], 'solver':{'backend':'glucose3','encoding':'seqcounter','python_sat_version':version('python-sat')}}
    executing_sources=(Path(__file__).resolve(), ROOT/'research/near_quarter_radius_factor.py')
    local_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in executing_sources}
    baseline_manifest=source_manifest()
    report['local_source_sha256']=local_hashes
    pins=[item for _,chain,c,r,a,ah,_ in INPUTS for item in
          ((ROOT/chain/(c+'.nqrb'),c),(ROOT/chain/(r+'.receipt.json'),r),(ROOT/a,ah))]
    report['samples']=[{'chain':label,'depth':depth,'status':'unstarted'} for label,_,_,_,_,_,length in INPUTS for depth in sorted({0,length//2,length})]
    try:
        paths,_=prefix_paths(check)
        for index,(label,depth,ids) in enumerate(paths):
            check();report['samples'][index]['status']='interrupted'
            sample=mask_and_bounds(79,ids,check);sample.update({'chain':label,'depth':depth})
            t=time.monotonic_ns();factor=radius_factor(sample['demands'],sample['edges'],deadline,clock=clock)
            sample['factor_ns']=time.monotonic_ns()-t;sample['factor']=factor
            sample['old_pass']=not (sample['orbit_shortfall'] or sample['row_shortfall'] or sample['graph_obstruction'])
            sample['useful_unsat']=sample['old_pass'] and factor['status']=='unsat'
            sample['status']='complete' if factor['status']!='unknown' else 'unknown'
            report['samples'][index]=sample
            if factor['status']=='unknown': raise TimeoutError
        report['status']='complete';report['complete']=True
    except TimeoutError:
        report['status']='timeout'
    # Inputs are read again even on timeout, outside the cooperative deadline;
    # the owned hard guard bounds this tail.
    for path,digest in pins:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('input changed during probe')
    if source_manifest()!=baseline_manifest or any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in local_hashes.items()):
        raise ValueError('source changed during probe')
    report['elapsed_seconds']=clock()-start
    atomic(out/'report.json',encode(report))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--seconds',type=float,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
    result=run(a.output_dir,a.seconds);print(json.dumps(result,sort_keys=True))
    return 0 if result['complete'] else 2


if __name__=='__main__': sys.exit(main())
