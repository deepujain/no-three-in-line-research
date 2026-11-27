"""Real fixed64 association-frame orchestration on genuine synthetic52-role bytes."""
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import restricted_three_row64 as worker
from research import restricted_three_row64_independent_byte_fixture as fixture_source

WORKER_SHA='e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def invoke(f,source,expect_success=True):
    called=[];checks=[]
    def check():checks.append(1)
    def forbidden(*a,**kw):raise AssertionError('forbidden historical/actual geometry service')
    def associate(docs,metadata,pins,authority_raw,supplied_check):
        assert supplied_check is check
        assert docs==f['expected_documents'] and metadata==f['metadata'] and pins==f['pins']
        assert authority_raw==f['authority_raw']
        called.append(1)
        return tuple(map(tuple,fixture_source.graph.NEW_POINTS)),dict(score=64,declared=True)
    with patch.object(worker,'HANDOFF_SHA',f['metadata_sha256']),patch.object(worker,'associate_documents',associate),\
         patch.object(worker.engine.kernel,'dual_validate',forbidden),patch.object(worker.engine.kernel,'build_index',forbidden),\
         patch.object(worker.engine.shared,'load_handoff',forbidden),patch.object(worker.adapter,'audit',forbidden),\
         patch.object(worker.adapter.chain,'audit_chain',forbidden):
        result=worker.association_frame(f['pins'],check,source)
    assert called==[1] and checks and result[1]['score']==64
    return result


def repack(f,name,raw):
    """Authenticate intentionally malformed synthetic JSON, not a byte-drift test."""
    assert len(raw)==len(f['blobs'][name]);f['blobs'][name]=raw
    h=fixture_source.digest(raw);f['metadata']['artifacts'][name]=h;f['pins'][str(worker.ROOT/name)]=h
    m=fixture_source.pad(fixture_source.packed(f['metadata']),worker.HANDOFF_BYTES)
    f['metadata_raw']=m;f['metadata_sha256']=fixture_source.digest(m);f['blobs'][worker.HANDOFF_PATH]=m
    f['pins'][str(worker.ROOT/worker.HANDOFF_PATH)]=f['metadata_sha256']


def run():
    assert sha(worker.__file__)==WORKER_SHA
    f=fixture_source.fixture();reader=fixture_source.ClosedSource(f['blobs']);invoke(f,reader)
    events=reader.events
    assert events[0][0:2]==('read',worker.HANDOFF_PATH)
    assert [e[1] for e in events if e[0]=='scan']==sorted(worker.ROLES)
    assert [e[1] for e in events if e[0]=='read']==[worker.HANDOFF_PATH]+sorted(p for p in worker.ROLES if p.endswith('.json'))
    assert [e[0] for e in events]==['read']+['scan']*51+['read']*45
    # A second pass uses the real production DiskSource against only new
    # temporary files, so its stat/stream/read/hash checks are not mocked.
    with tempfile.TemporaryDirectory(prefix='fixed64-independent-bytes-') as directory:
        root=Path(directory)
        for name,raw in f['blobs'].items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        source=worker.DiskSource(root,lambda:None);invoke(f,source)
    rejections=[]
    for role in sorted(worker.ROLES):
        f=fixture_source.fixture();reader=fixture_source.ClosedSource(f['blobs']);reader.fail=('scan',role)
        try:invoke(f,reader)
        except ValueError as error:
            assert [e[1] for e in reader.events if e[0]=='read']==[worker.HANDOFF_PATH]
            rejections.append(dict(case='preflight_'+role,error=str(error)))
        else:raise AssertionError('preflight failure accepted')
    for role in (sorted(k for k in worker.ROLES if k.endswith('.json'))[0],worker.AUTHORITY):
        f=fixture_source.fixture();reader=fixture_source.ClosedSource(f['blobs']);reader.fail=('read',role)
        try:invoke(f,reader)
        except ValueError as error:rejections.append(dict(case='read_'+role,error=str(error)))
        else:raise AssertionError('read failure accepted')
    malformed={'duplicate_key':b'{"x":1,"x":2}', 'nonfinite':b'{"x":NaN}', 'nonascii':b'{"x":"\xff"}', 'syntax':b'{'}
    for name,raw in malformed.items():
        f=fixture_source.fixture();role=worker.INITIAL
        repack(f,role,fixture_source.pad(raw,len(f['blobs'][role])))
        reader=fixture_source.ClosedSource(f['blobs'])
        try:invoke(f,reader)
        except (ValueError,UnicodeError) as error:rejections.append(dict(case='authenticated_json_'+name,error=str(error)))
        else:raise AssertionError('malformed JSON accepted')
    f=fixture_source.fixture();f['blobs'][worker.HANDOFF_PATH]=b' '+f['blobs'][worker.HANDOFF_PATH][1:]
    try:invoke(f,fixture_source.ClosedSource(f['blobs']))
    except ValueError as error:rejections.append(dict(case='metadata_byte_drift',error=str(error)))
    else:raise AssertionError('metadata drift accepted')
    assert len(rejections)==58 and sha(worker.__file__)==WORKER_SHA
    return dict(passed=True,worker_sha256=WORKER_SHA,source_sha256=sha(__file__),fixture_sha256=sha(fixture_source.__file__),
                closed_reader_success=True,real_disk_source_success=True,exact_roles=52,preflight_before_parsed_artifacts=True,
                json_roles_read=46,text_roles_hash_only=6,rejections=rejections,
                scope='Real association_frame, metadata schema/parser, quotas and real DiskSource over genuine synthetic bytes. All51 preflight scans precede45artifact decodes. New semantic association is an exact argument-checking spy.',
                limitations='Internal synthetic graph semantics are tested separately. No actual inputs/geometry, whole-wrapper run, physical-memory bound, durable publication or actual outcome acceptance.')


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-frame-v2.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,rejections=len(result['rejections']),source_sha256=sha(__file__),evidence_sha256=sha(path))))
