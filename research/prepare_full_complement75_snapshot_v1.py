from pathlib import Path
import json,hashlib
sha=lambda raw:hashlib.sha256(raw).hexdigest()
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
source=Path('data/restricted-three-row64-v2/initial.json');raw=source.read_bytes();assert sha(raw)=='1756d83bc3bfa5bf491d37e5c59bdc785a095184aa285c260820670a39938ead'
v=json.loads(raw);points=v['points'];assert v['n']==75 and v['score']==64 and len(points)==149
assert all(type(z) is int and 0<=z<75 for p in points for z in p)
assert all(len(p)==2 for p in points) and points==sorted(points) and len(set(map(tuple,points)))==149
assert sorted(sum(p[1]==r for p in points) for r in range(75))==[1]+[2]*74
snapshot=canonical({'n':75,'points':points});identity=sha(snapshot);assert identity==v['state_hash']=='b72f8f1ad19c2d06e97bd31de96ab57ed7d4d96af19429b27e5b223b82e444f7'
p=Path('data/full-complement-row75-fixed64-points-v1.json');assert not p.exists();p.write_bytes(snapshot)
provenance={}
for role,path,expected in [('source_initial',str(source),'1756d83bc3bfa5bf491d37e5c59bdc785a095184aa285c260820670a39938ead'),('accepted_audit','data/restricted-three-row64-independent-actual-v2-audit.json','df58ba6557f95f42db3d64cf645d391de7171d0bc44b3088f0652d9989b287d7'),('acceptance_review','research/restricted-three-row64-independent-actual-v2-metadata-review.md','a3cb672e70bbf00d872d80d5f973ea91a7e8d63150b7ce1190b100155b0e957e')]:
 b=Path(path).read_bytes();assert sha(b)==expected;provenance[role]={'path':path,'sha256':expected,'bytes':len(b)}
handoff={'schema':1,'n':75,'point_count':149,'raw_score':64,'normalized_sha256':identity,'snapshot':{'path':str(p),'sha256':sha(snapshot),'bytes':len(snapshot)},'provenance':provenance,'scope':'Root detached canonical snapshot of independently accepted unchanged64 endpoint. Structural/identity association only here; no geometry replay. New diagnostic must freshly check raw64 with both exact procedures. No adoption, iteration or old-family continuation.'}
h=Path('data/full-complement-row75-fixed64-handoff-v1.json');assert not h.exists();h.write_bytes(canonical(handoff))
print(json.dumps({'snapshot':handoff['snapshot'],'handoff':{'path':str(h),'sha256':sha(h.read_bytes()),'bytes':h.stat().st_size},'schema_keys':sorted(handoff),'provenance':provenance},sort_keys=True))
