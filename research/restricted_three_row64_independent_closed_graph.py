"""Synthetic 51-role byte graph for future fixed64 loader tests; no actual inputs.

All bytes, names, hashes and metadata are artificial. The graph is a test
fixture, not an independently valid historical chain or geometry certificate.
"""
import hashlib
import json
from pathlib import Path


def compact(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode('ascii')


def closed_graph(root):
    root=Path(root)
    inherited=[f'synthetic/inherited-{i:02d}.json' for i in range(39)]
    added=[f'synthetic/new-{i:02d}.json' for i in range(6)]+[f'synthetic/review-{i:02d}.txt' for i in range(6)]
    names=inherited+added
    raw={name:(compact({'role':name,'synthetic':True,'items':[i,{'flag':True}]}) if name.endswith('.json')
               else f'synthetic text role {name}\n'.encode('ascii')) for i,name in enumerate(names)}
    hashes={name:hashlib.sha256(blob).hexdigest() for name,blob in raw.items()}
    sizes={name:len(blob) for name,blob in raw.items()}
    metadata={'schema':'synthetic-closed-graph','artifact_count':51,'inherited_artifact_count':39,
              'artifacts':hashes,'artifact_byte_sizes':sizes}
    for name,blob in raw.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
    assert len(names)==51 and len(inherited)==39 and len(added)==12
    assert sum(name.endswith('.json') for name in names)==45
    assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==hashes[name] for name in names)
    return metadata,raw,inherited,added

if __name__=='__main__':
    import tempfile
    with tempfile.TemporaryDirectory(prefix='synthetic-fixed64-graph-') as directory:
        meta,raw,old,new=closed_graph(directory)
        print('PASS synthetic 51 roles, 39 inherited, 12 added, 45 JSON, 6 text; hashes verified; no actual artifacts')
