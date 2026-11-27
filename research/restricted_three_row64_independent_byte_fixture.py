"""Closed genuine-byte fixture for future loader orchestration tests.

Internal semantic links deliberately retain the declared graph's labels. This
fixture verifies authentication/reading/parsing only with association replaced
by an argument-checking spy; it is not a semantically valid historical chain.
No actual file is read, written, discovered, or authenticated by this module.
"""
import hashlib
import json
from research import restricted_three_row64_independent_synthetic_graph as graph


def packed(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()


def contract_sizes():
    """Public size contract copied from previously authenticated coordinate-free metadata.

    No metadata/artifact is opened here. These are byte caps, not geometry.
    """
    sizes={graph.OLD_REPORT:25842,graph.OLD_RECEIPT:11817,graph.OLD_MANIFEST:9707,
           graph.OLD_BOUNDARY:12530,graph.OLD_INITIAL:1587,graph.OLD_BEST:2138,
           graph.OLD_AUDIT:68150,graph.OLD_GUARD:1378,graph.OLD_ADAPTER:11846,
           graph.OLD_HELPER:13289,graph.OLD_REVIEW:5695,graph.OLD_METADATA:5645,
           graph.adapter.MANIFEST:28283,graph.adapter.REPORT:49235,graph.adapter.RECEIPT:30748,
           graph.adapter.AUTHORITY:9297,graph.adapter.INITIAL:1698,graph.MOVE:1743,
           graph.AUDIT:6908,graph.GUARD:1711,graph.PREPARATION:7293,graph.SOURCE_REVIEW:3129,graph.METADATA_REVIEW:1923}
    sizes.update(zip(graph.MOVES,[1553,1553,1553,1555,1555,1555,1555,1555,1555,1555,1555,1555,1554,1555,
                                 1555,1556,1557,1556,1557,1557,1557,1556,1557,1557,1557,1556,1555,1557]))
    assert len(sizes)==51 and sum(sizes.values())==355145
    return sizes


def pad(raw,size):
    if len(raw)>size:raise ValueError('synthetic role exceeds fixed byte envelope')
    return raw+b' '*(size-len(raw))


def fixture():
    declared=graph.fixture()
    blobs={name:packed(value) for name,value in declared['docs'].items()}
    for name in declared['source_roles']:
        blobs[name]=('SYNTHETIC TEXT ROLE '+name+'\n').encode('ascii')
    assert len(blobs)==51
    sizes=contract_sizes()
    blobs={name:pad(raw,sizes[name]) for name,raw in blobs.items()}
    metadata=declared['metadata']
    metadata['artifacts']={name:digest(raw) for name,raw in blobs.items()}
    metadata['artifact_byte_sizes']={name:len(raw) for name,raw in blobs.items()}
    metadata['scope']='SYNTHETIC BYTE/PARSER FIXTURE; semantic associations separately declared, not validated here.'
    metadata_raw=pad(packed(metadata),10249);all_blobs={**blobs,graph.NEW_METADATA:metadata_raw}
    pins={str(graph.ROOT/name):digest(raw) for name,raw in all_blobs.items()}
    return dict(blobs=all_blobs,metadata=metadata,metadata_raw=metadata_raw,metadata_sha256=digest(metadata_raw),
                pins=pins,expected_documents=declared['docs'],authority_raw=blobs[graph.adapter.AUTHORITY],
                artifact_count=len(blobs),total_role_count=len(all_blobs),
                scope='Genuine synthetic byte hashes for exactly52roles, no semantic chain acceptance and no geometry.')


class ClosedSource:
    """Mirrors the planned scan/read interface with genuine byte authentication.

    Immutable fixture blobs are fixture-owned; this class does not establish
    parser release or physical memory bounds. Only scalar access events persist.
    """
    def __init__(self,blobs):self.blobs=blobs;self.events=[];self.fail=None
    def _checked(self,name,size,sha,kind):
        if type(name)is not str or name not in self.blobs:raise AssertionError('unexpected source role '+repr(name))
        raw=self.blobs[name];self.events.append((kind,name,size,sha))
        if self.fail==(kind,name):raise ValueError('injected synthetic '+kind+' rejection')
        if type(size)is not int or len(raw)!=size:raise ValueError('synthetic exact size mismatch')
        if digest(raw)!=sha:raise ValueError('synthetic exact byte digest mismatch')
        return raw
    def scan(self,name,size,sha):self._checked(name,size,sha,'scan')
    def read(self,name,size,sha):return self._checked(name,size,sha,'read')
