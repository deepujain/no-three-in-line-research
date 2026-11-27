"""Genuine synthetic byte/JSON fixture preparation; no new wrapper comparison."""
import hashlib
import json
from pathlib import Path
from research import restricted_three_row64_independent_byte_fixture as byte_fixture


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    f=byte_fixture.fixture();sources={str(Path(p).relative_to(byte_fixture.graph.ROOT)):sha(p)
        for p in (__file__,byte_fixture.__file__,byte_fixture.graph.__file__)}
    good=byte_fixture.ClosedSource(f['blobs']);parsed=0
    for name,raw in f['blobs'].items():
        expected=byte_fixture.digest(raw);good.scan(name,len(raw),expected)
        if name.endswith('.json'):
            value=json.loads(good.read(name,len(raw),expected));parsed+=1
            assert value==(f['metadata'] if name==byte_fixture.graph.NEW_METADATA else f['expected_documents'][name])
    assert parsed==46 and len(f['blobs'])==52
    rejected=[]
    for name,raw in f['blobs'].items():
        expected=byte_fixture.digest(raw)
        for kind,bad in (('size',raw+b' '),('digest',bytes([raw[0]^1])+raw[1:])):
            changed=dict(f['blobs']);changed[name]=bad;reader=byte_fixture.ClosedSource(changed)
            try:reader.read(name,len(raw),expected)
            except ValueError as error:rejected.append(dict(role=name,kind=kind,error=str(error)))
            else:raise AssertionError('corrupted bytes accepted '+name)
    assert len(rejected)==104
    assert all(sha(byte_fixture.graph.ROOT/p)==s for p,s in sources.items())
    return dict(passed=True,sources=sources,artifact_roles=51,total_roles_with_metadata=52,
                metadata_bytes=10249,artifact_bytes=355145,total_bytes=365394,genuine_byte_scans=52,genuine_json_decodes=46,
                rejection_count=len(rejected),rejections=rejected,
                scope='Genuine hashes, exact byte sizes and JSON decoding for a closed52-role synthetic graph padded to the approved envelope. No actual artifact read or geometry.',
                limitations='Internal historical semantic links remain declared labels. This fixture is for real loader orchestration with association an argument-checking spy. No new wrapper, source I/O, memory lifetime, process guard or semantic-chain PASS is claimed.')


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-byte-preparation.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,genuine_byte_roles=52,json_decodes=46,rejections=104,
                         source_sha256=sha(__file__),fixture_sha256=sha(byte_fixture.__file__),evidence_sha256=sha(path))))
