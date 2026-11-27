"""Artificial max-buffer and538 full-size durable-publication envelope.

This does not describe a valid/reachable authority or board. Serialization is
explicitly replaced with a preencoded1-MiB opaque envelope while the unchanged
FileStore publication-count and file/directory-fsync path executes. No actual
input, geometry or optimizer is accessed. Root owns the execution allocation.
"""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import two_row_suffix75 as s


def main():
    mask=(1<<149)-1
    left={(1,i-5513,i):int(str(mask-i)) for i in range(11026)}
    right={(2,i-5513,i):int(str(mask-i-11026)) for i in range(11026)}
    # Opaque buffers conservatively cover every39 historical snapshot at its
    # parser cap. They contain no source data or coordinate fixture.
    source_buffers=[bytearray(1024*1024) for _ in range(39)]
    cross=bytearray([146])*5625;unaries=[[10585+i for i in range(75)] for _ in range(2)]
    records=[{'seq':i+1,'kind':'row' if i<204 else 'pair','padding':str(i)+'x'*900} for i in range(268)]
    pairs=[[r,t,65] for r in range(75) for t in range(r+1,75)]
    envelope={'artificial':True,'attempts':records,'pairs':pairs,'rows':list(range(75)),
              'header':'h'*65000,'duplicate_coordinate_placeholders':[[74,74]]*149,'padding':''}
    empty=s.compact(envelope);envelope['padding']='p'*(s.CAP-len(empty));raw=s.compact(envelope)
    raw2=bytes(bytearray(raw))
    assert len(raw)==len(raw2)==s.CAP and len(records)==268 and len(pairs)==2775
    with tempfile.TemporaryDirectory(prefix='suffix-persistence-envelope-') as directory:
        store=s.FileStore(directory)
        # The source serialization/authority checker is covered by real tiny
        # fixtures separately. This injected buffer isolates worst-size I/O.
        with patch.object(s,'authority_bytes',return_value=raw):
            for _ in range(538):store.publish({'opaque_placeholder':True},'artificial_envelope')
            try:store.publish({'opaque_placeholder':True},'rejected_539th')
            except ValueError:pass
            else:raise AssertionError('publication cap failed')
        path=Path(directory)/'authority.json'
        assert path.stat().st_size==s.CAP and s.digest(path)==__import__('hashlib').sha256(raw).hexdigest()
        assert len(list(Path(directory).iterdir()))==1 and store.publications==538 and not store.uncertain
    assert len(left)==len(right)==11026 and sum(map(len,source_buffers))==39*1024*1024
    assert len(cross)==5625 and sum(map(len,unaries))==150 and raw==raw2
    print(json.dumps({'passed':True,'worker_sha256':s.digest(s.__file__),'stress_sha256':s.digest(__file__),
                      'indexes':[len(left),len(right)],'opaque_source_buffer_bytes':sum(map(len,source_buffers)),
                      'attempt_records':len(records),'pair_entries':len(pairs),'publication_bytes':len(raw),
                      'full_file_and_directory_fsync_publications':538,'total_published_bytes':538*len(raw),
                      'publication_539_rejected':True,'live_max_publication_buffers':2,
                      'scope':'Artificial opaque buffer/dict/mask allocation and real unchanged FileStore fsync publication path only; authority serialization is injected, no valid/reachable geometry or actual source, no throughput forecast.'},sort_keys=True))


if __name__=='__main__':main()
