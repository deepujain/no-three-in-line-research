"""Root-owned artificial parser/graph/index/34-fsync envelope; no actual input.

JSON shapes are deliberately not valid artifact schemas. Maximum publication
serialization is injected; unchanged frozen FileStore performs real durability.
"""
import gc
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from research import restricted_three_row64 as w
from research import restricted_three_row64_tiny as author


def parser_shape(size):
    # Mostly separately allocated {} nodes, with occasional string values.
    # This exercises decoder expansion while staying below100,000 nodes over
    # the complete311,970-byte JSON allowance. No artifact contents are used.
    values=[];used=2;i=0
    while True:
        token='{}' if i%5 else '"synthetic-padding"'
        extra=len(token)+(1 if values else 0)
        if used+extra>size:break
        values.append(token);used+=extra;i+=1
    raw=('['+','.join(values)+']').encode()
    return raw+b' '*(size-len(raw))


def main():
    sizes=author.sizes();parsed={};parsed_bytes=0;largest_raw=0
    for name in sorted(k for k in sizes if k.endswith('.json')):
        raw=parser_shape(sizes[name]);assert len(raw)==sizes[name]
        parsed[name]=w.decode_json(raw);parsed_bytes+=len(raw);largest_raw=max(largest_raw,len(raw));del raw
        w.GraphBudget().check(parsed)
    assert len(parsed)==45 and parsed_bytes==311970 and largest_raw==68150
    parser_graph=w.GraphBudget().check(parsed)
    del parsed;gc.collect()

    # Near the retained14MiB portion of the16MiB cap, plus the explicit2MiB
    # reserve for pure-helper normalized maps/canonical temporary buffers.
    maximal_graph=['%08d'%i+'x'*212 for i in range(52000)]
    graph_measure=w.GraphBudget().check(maximal_graph,reserve=2*w.MiB)
    assert 13*w.MiB<graph_measure['bytes']<14*w.MiB and graph_measure['nodes']<=100000
    association_reserve=bytearray(2*w.MiB)
    walker_allowance=bytearray(16*w.MiB)
    source_stream=bytearray(65536);current_raw=bytearray(68150);current_decode='d'*68150
    authority_raw=bytearray(9297);metadata_raw=bytearray(10249);manifest_raw=bytearray(128*1024)
    # Opaque quota buffers, not a newly constructed n75 coordinate fixture.
    detached_points=bytearray(32768)
    detached_info=bytearray(4096)
    mask=(1<<149)-1
    left={(1,i-5513,i):int(str(mask-i)) for i in range(11026)}
    right={(2,i-5513,i):int(str(mask-i-11026)) for i in range(11026)}
    unaries=[[10585+x+r for x in range(75)] for r in range(3)]
    cross=bytearray([144])*48;ternary=bytearray([1])*64;domains=[list(range(4)) for _ in range(3)]
    records=[{'seq':i+1,'opaque':'r'*2000} for i in range(16)]
    envelope={'artificial':True,'attempts':records,'candidate':'c'*8192,'header':'h'*65536,'padding':''}
    envelope['padding']='p'*(w.MiB-len(w.compact(envelope)))
    raw=w.compact(envelope);raw2=bytes(bytearray(raw));assert len(raw)==len(raw2)==w.MiB
    with tempfile.TemporaryDirectory(prefix='fixed64-persistence-envelope-') as directory:
        store=w.FileStore(directory)
        with patch.object(w.engine,'authority_bytes',return_value=raw):
            for _ in range(34):store.publish({'opaque_placeholder':True},'artificial_envelope')
            try:store.publish({'opaque_placeholder':True},'rejected35')
            except ValueError:pass
            else:raise AssertionError('35th publication allowed')
        path=Path(directory)/'authority.json'
        assert path.stat().st_size==w.MiB and w.digest(path)==hashlib.sha256(raw).hexdigest()
        assert len(list(Path(directory).iterdir()))==1 and store.publications==34 and not store.uncertain
    assert len(left)==len(right)==11026 and len(association_reserve)==2*w.MiB and len(walker_allowance)==16*w.MiB
    assert len(source_stream)==65536 and len(current_raw)==len(current_decode)==68150
    assert len(authority_raw)==9297 and len(metadata_raw)==10249 and len(manifest_raw)==128*1024
    assert len(detached_points)==32768 and len(detached_info)==4096 and raw==raw2
    assert sum(map(len,unaries))==225 and len(cross)==48 and len(ternary)==64 and sum(map(len,domains))==12
    print(json.dumps({'passed':True,'worker_sha256':w.digest(w.__file__),'stress_sha256':w.digest(__file__),
        'parser_documents':45,'parser_encoded_bytes':parsed_bytes,'parser_max_input_bytes':largest_raw,
        'parser_graph_bytes':parser_graph['bytes'],'parser_nodes':parser_graph['nodes'],
        'retained_artificial_graph_bytes':graph_measure['bytes'],'retained_artificial_graph_nodes':graph_measure['nodes'],
        'association_temporary_reserve_bytes':len(association_reserve),'walker_allowance_bytes':len(walker_allowance),
        'metadata_bytes':10249,'authority_raw_bytes':9297,'manifest_buffer_bytes':128*1024,'indexes':[11026,11026],
        'full_file_directory_fsync_publications':34,'publication_bytes':w.MiB,'publication35_rejected':True,
        'scope':'Artificial bounded JSON shapes, separate released parser phase then near-cap live graph/reserve/aux/buffers/two fake indexes, injected1MiB serializer and unchanged FileStore/fsync. No actual input/schema/geometry or timing forecast.'},sort_keys=True))


if __name__=='__main__':main()
