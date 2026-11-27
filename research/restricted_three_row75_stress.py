"""Artificial buffer/34-publication envelope; execution allocation belongs to Root.

No actual source artifacts, valid geometry, selector or optimizer. The serializer
is explicitly injected; unchanged FileStore runs real file+directory fsync.
"""
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import restricted_three_row75 as s


def main():
    mask=(1<<149)-1
    left={(1,i-5513,i):int(str(mask-i)) for i in range(11026)}
    right={(2,i-5513,i):int(str(mask-i-11026)) for i in range(11026)}
    # One full 1MiB opaque byte snapshot and one parsed-text-size placeholder
    # for each of the 39 authenticated historical artifact cap allowances.
    snapshots=[bytes(bytearray(1024*1024)) for _ in range(39)]
    parsed_placeholders=['x'*(1024*1024) for _ in range(39)]
    unaries=[[10585+x+r for x in range(75)] for r in range(3)]
    C=[bytearray([144])*16 for _ in range(3)];T=bytearray([1])*64
    domains=[list(range(4)) for _ in range(3)]
    records=[{'seq':i+1,'opaque':'r'*2000} for i in range(16)]
    candidate_placeholder='c'*8192;header_placeholder='h'*65536
    envelope={'artificial':True,'attempts':records,'candidate':candidate_placeholder,
              'header':header_placeholder,'padding':''}
    envelope['padding']='p'*(s.CAP-len(s.compact(envelope)))
    raw=s.compact(envelope);raw2=bytes(bytearray(raw))
    assert len(raw)==len(raw2)==s.CAP
    with tempfile.TemporaryDirectory(prefix='three-row-persistence-envelope-') as directory:
        store=s.FileStore(directory)
        with patch.object(s,'authority_bytes',return_value=raw):
            for _ in range(34):store.publish({'opaque_placeholder':True},'artificial_envelope')
            try:store.publish({'opaque_placeholder':True},'rejected35')
            except ValueError:pass
            else:raise AssertionError('35th publication allowed')
        path=Path(directory)/'authority.json'
        assert path.stat().st_size==s.CAP and s.digest(path)==hashlib.sha256(raw).hexdigest()
        assert len(list(Path(directory).iterdir()))==1 and not store.uncertain and store.publications==34
    assert len(left)==len(right)==11026 and sum(map(len,snapshots))==39*1024*1024
    assert sum(map(len,parsed_placeholders))==39*1024*1024 and sum(map(len,unaries))==225
    assert sum(map(len,C))==48 and len(T)==64 and sum(map(len,domains))==12 and raw==raw2
    print(json.dumps({'passed':True,'worker_sha256':s.digest(s.__file__),'stress_sha256':s.digest(__file__),
          'indexes':[len(left),len(right)],'opaque_source_snapshot_bytes':sum(map(len,snapshots)),
          'opaque_parsed_text_bytes':sum(map(len,parsed_placeholders)),'unary_ints':225,'cross_bytes':48,
          'ternary_bytes':64,'domain_columns':12,'attempt_records':16,'candidate_placeholder_bytes':8192,
          'header_placeholder_bytes':65536,'publication_bytes':len(raw),'live_publication_buffers':2,
          'full_file_directory_fsync_publications':34,'total_published_bytes':34*len(raw),'publication35_rejected':True,
          'scope':'Artificial opaque capped-source buffers, two fake complete indexes and maximum components; injected serializer, unchanged FileStore/fsync. Not a valid/reachable authority, input, geometry or runtime forecast.'},sort_keys=True))


if __name__=='__main__':main()
