"""Artificial key/mask allocation envelope, NOT reachable geometry or search.

Two full independent maps, two maximum-size indexes and compact JSON buffers
remain live together. Keys/masks need not describe any board configuration;
repeated coordinate slots are deliberately invalid placeholders. Run under the
owned sampled256MiB guard for process memory evidence, not search throughput.
"""
import hashlib
import json
from math import gcd
from pathlib import Path
import random
from research import row_block_breakout75 as worker


def key_stream():
    for a in range(1,75):
        for b in range(-74,75):
            if gcd(a,abs(b)) != 1:continue
            for c in range(-10952,10953):yield a,b,c


def fresh(key):return tuple(int(str(value)) for value in key)


def main():
    keys=[]
    for key in key_stream():
        keys.append(key)
        if len(keys)==65536:break
    first={fresh(key):int('65535') for key in keys}
    second={fresh(key):int('65535') for key in keys}
    mask=(1<<149)-1
    left={fresh(key):mask-i for i,key in enumerate(keys[:11026])}
    right={fresh(key):mask-i for i,key in enumerate(keys[-11026:])}
    records=[[a,b,c,value] for (a,b,c),value in sorted(second.items())]
    metadata={'artificial_envelope':True,'padding':'x'*15000}
    raw=worker.compact({'metadata':metadata,'weights':records,'rng':random.Random(275149).getstate(),
                        'current':[[74,74]]*149,'best':[[74,74]]*149})
    # Keep a second serialization buffer alive, as a conservative encoder envelope.
    raw2=bytes(bytearray(raw))
    assert len(first)==len(second)==65536 and len(left)==len(right)==11026
    assert len(raw)<=2*1024*1024 and raw2==raw
    report={'passed':True,'worker_sha256':worker.digest(worker.__file__),'stress_sha256':worker.digest(__file__),
            'weight_maps':[len(first),len(second)],'indexes':[len(left),len(right)],'serialized_bytes':len(raw),
            'serialized_sha256':hashlib.sha256(raw).hexdigest(),'live_serialization_buffers':2,
            'scope':'Artificial canonical-key/mask/dictionary/JSON allocation only; masks and duplicate coordinate placeholders are not a valid/reachable state. No n75 geometry, source read or search.'}
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__':main()
