"""Artificial allocation and streamed-minima envelope, never board geometry.

Masks/keys/placeholder coordinates are intentionally unrelated. Keep the
largest simultaneously relevant source/JSON buffers live conservatively.
Run only in Root's owned sampled256-MiB guard; no actual input is opened.
"""
import json
from research import two_row_descent75 as w


def main():
    mask=(1<<149)-1
    # Independent key/mask objects for current and pending full indexes.
    left={(1,i-5513,i):int(str(mask-i)) for i in range(11026)}
    right={(2,i-5513,i):int(str(mask-i-11026)) for i in range(11026)}
    I=[(1<<19)+r for r in range(75)]
    J={(r,s):(1<<18)+r+s for r in range(75) for s in range(r+1,75)}
    M={(r,s):I[r]+I[s]-J[r,s] for r,s in J}
    priorities=tuple(sorted(M,key=lambda p:(-M[p],*p)))
    u=[10585+x for x in range(75)]; v=[10585+y for y in range(75)]
    cross=bytearray([146])*5625
    # Eight maximum2-MiB authenticated handoff snapshots, new manifest/raw,
    # current/pending boundary/report encodings. These are upper-envelope
    # opaque byte buffers, not parsed source data or reachable artifacts.
    source_snapshots=[bytearray(2*1024*1024) for _ in range(8)]
    manifest_buffers=[bytearray(2*1024*1024) for _ in range(2)]
    output_buffers=[bytearray(1024*1024) for _ in range(4)]
    point_buffers=[[(74,74)]*149 for _ in range(4)]
    # Full fixed paired-start ceiling on abstract nonzero cost tables.
    work={}; checksum=0
    for _ in range(32):
        for X in w.outer_sets(75,3):
            costs=(v[y]+sum(cross[x*75+y] for x in X) for y in range(75))
            score,Y=w.best_partner(costs,3-len(X),work=work)
            checksum+=score+sum(u[x] for x in X)+sum(Y)
    assert len(left)==len(right)==11026 and len(priorities)==2775
    assert work['partner_visits']==6840000
    total_buffers=sum(map(len,source_snapshots+manifest_buffers+output_buffers))
    assert len(point_buffers)==4 and len(cross)==5625 and len(I)==75
    print(json.dumps({'passed':True,'worker_sha256':w.digest(w.__file__),'stress_sha256':w.digest(__file__),
                      'indexes':[len(left),len(right)],'priority_pairs':len(priorities),'cross_bytes':len(cross),
                      'opaque_live_buffer_bytes':total_buffers,'partner_visits':work['partner_visits'],'checksum':checksum,
                      'scope':'Artificial dict/mask/opaque-buffer and nonzero streamed-cost envelope only. No valid/reachable geometry, actual input, index construction or search throughput claim.'},sort_keys=True))


if __name__=='__main__':main()
