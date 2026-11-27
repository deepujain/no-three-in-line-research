import json,hashlib,collections,pathlib,datetime
from src.verify import verify_certificate,verify_certificate_bruteforce
p=pathlib.Path('/private/tmp/no-three-n76-rot4.few'); raw=p.read_bytes(); assert hashlib.sha256(raw).hexdigest() == '1d5e1fccce84372714da7d97d4d490bf2e6b49f2c1bc451ca974d2b8bf0fc412'; assert raw == pathlib.Path('data/published-n76-reader-transcript.txt').read_bytes(); pathlib.Path('data/published-n76-raw.few').write_bytes(raw); records=raw.decode('ascii').splitlines(); alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&@?!()[]<>{}=*+|-/~^_:;,.'
assert len(records)==2 and all(len(c)==153 and c[0]=='o' for c in records)
code=records[0]; points=[[alphabet.index(code[1+2*y+j]),y] for y in range(76) for j in range(2)]
assert len(points)==152 and len(set(map(tuple,points)))==152 and all(0<=x<76 for x,y in points)
assert sorted(collections.Counter(x for x,y in points).values())==[2]*76
assert sorted(collections.Counter(y for x,y in points).values())==[2]*76
fixture={'n':76,'points':points,'source_url':'https://wwwhomes.uni-bielefeld.de/~achim/no3in/download/configurations/n76_rot4.few','source_record':1,'source_encoding':code,'alphabet':alphabet,'provenance_note':'Raw archive bytes fetched independently and matched the connected reader transcript.'}
a=verify_certificate(fixture); b=verify_certificate_bruteforce(fixture)
assert a['valid'] and b['valid'] and a['normalized_sha256']==b['normalized_sha256']
fp=pathlib.Path('data/published-n76.json'); fp.write_text(json.dumps(fixture,indent=2)+'\n')
evidence={'source_record':1,'raw_bytes_authenticated':True,'raw_sha256':hashlib.sha256(raw).hexdigest(),'reader_transcript_sha256':hashlib.sha256(pathlib.Path('data/published-n76-reader-transcript.txt').read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(fp.read_bytes()).hexdigest(),'normalized_sha256':a['normalized_sha256'],'point_count':152,'row_and_column_loads':{'rows':{'2':76},'columns':{'2':76}},'validators':[a,b],'source_url':fixture['source_url'],'source_format':'first symmetry symbol then two column characters per row','retrieval':'Root fetched archive bytes; separately matched connected reader transcript','validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
pathlib.Path('data/published-n76-validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence))
