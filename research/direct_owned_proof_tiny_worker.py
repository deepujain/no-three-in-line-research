"""Synthetic process fixtures only; never opens the saved actual CNF/proof."""
import time
ENTRY_STARTED=time.monotonic()
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research import direct_owned_saved_proof as direct


def main():
    direct.configure_log_cap()
    p=argparse.ArgumentParser(); p.add_argument('mode'); a=p.parse_args()
    identity=direct.owned_log_identity()
    if a.mode=='identity': direct.emit({'identity':identity}); return 0
    if a.mode in ('stdout','stderr','both'):
        signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
        child=None
        if a.mode=='both':
            child=os.fork()
            if child==0:
                try:
                    while True: os.write(1,b'x'*4096)
                except OSError: os._exit(3)
        try:
            while True: os.write(1 if a.mode=='stdout' else 2,b'x'*8192)
        except OSError:
            if child is not None: os.waitpid(child,0)
            return 3
    if a.mode in ('sleep','fork_stubborn'):
        if a.mode=='fork_stubborn':
            child=os.fork()
            if child==0:
                signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(10); os._exit(0)
            direct.emit({'identity':identity,'uncooperative_child':child})
        signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(10); return 0
    if a.mode=='fork':
        child=os.fork()
        if child==0: time.sleep(10); os._exit(0)
        time.sleep(.1); os.kill(child,signal.SIGKILL); os.waitpid(child,0)
        direct.emit({'identity':identity,'fork_reaped':True}); return 0
    if a.mode=='truncated': os.write(1,b'{"protocol":'); return 0
    if a.mode not in ('accepted','rejected','deadline','pinchange'): raise ValueError('fixture mode')
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp); cnf=tmp/'synthetic.cnf'; proof=tmp/'synthetic.rup'; manifest=tmp/'source-pins.json'
        cnf.write_text('p cnf 2 3\n1 0\n-1 2 0\n-2 0\n' if a.mode!='rejected' else 'p cnf 2 1\n1 0\n')
        proof.write_text('d -1 2 0\n0\n' if a.mode!='rejected' else '0\n')
        paths=(Path(direct.__file__).resolve(),direct.PARENT,direct.CHECKER,direct.RUNTIME,
               Path(__file__).resolve(),Path(sys.executable),Path(sys.executable).resolve(),cnf,proof)
        sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        source={str(path):sha(path) for path in paths}
        manifest.write_text(json.dumps(source,sort_keys=True)); source_sha=sha(manifest)
        # This real context-loader test explicitly supplies only the tiny pair.
        pins=direct.load_context(manifest,source_sha,direct.Deadline(4,started=ENTRY_STARTED),
                                 cnf=cnf,proof=proof,cnf_sha=sha(cnf),proof_sha=sha(proof))
        if a.mode=='pinchange': proof.write_text('changed synthetic proof\n')
        result=direct.run_pair(cnf,proof,source[str(cnf)],source[str(proof)],pins,source_sha,
                               started=ENTRY_STARTED,seconds=.000001 if a.mode=='deadline' else 4)
        direct.emit(result); return 0 if result['accepted'] else 2


if __name__=='__main__': sys.exit(main())
