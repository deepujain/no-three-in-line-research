"""Authenticate published n74 archive record1; no extension or insertion search."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.verify import verify_certificate, verify_certificate_bruteforce

RAW_SHA='1c276251f9c819d2941eedb1fa02bd860c093b970af395d8baea86ad4cd5c9f0'
URL='https://wwwhomes.uni-bielefeld.de/~achim/no3in/download/configurations/n74_rot4.few'
ALPHABET='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&@?!()[]<>{}=*+|-/~^_:;,.'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True)
    a=p.parse_args(); raw=a.raw.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=RAW_SHA: raise ValueError('archive byte identity')
    records=raw.decode('ascii').splitlines()
    if len(records)!=2 or any(len(c)!=149 or c[0]!='o' for c in records):
        raise ValueError('archive record count/encoding')
    code=records[0]; points=[[ALPHABET.index(code[1+2*y+j]),y] for y in range(74) for j in range(2)]
    cert={'n':74,'points':points,'source_url':URL,'source_record':1,'encoded_source':code,
          'alphabet':ALPHABET,'raw_sha256':RAW_SHA,
          'provenance_note':'Published n74 rot4 archive, explicitly selected record1; identity with the forum fixed-embedding experiment is unknown. Not a new construction.'}
    reports=[verify_certificate(cert),verify_certificate_bruteforce(cert)]
    if not all(r['valid'] and r['point_count']==148 for r in reports): raise ValueError('source dual validation')
    if reports[0]['normalized_sha256']!=reports[1]['normalized_sha256']: raise ValueError('normalization disagreement')
    for axis in (0,1):
        if Counter(p[axis] for p in points)!=Counter({v:2 for v in range(74)}): raise ValueError('source axes')
    fixture=json.dumps(cert,indent=2)+'\n'
    evidence={'source_url':URL,'source_record':1,'archive_records':2,'raw_sha256':RAW_SHA,
              'fixture_sha256':hashlib.sha256(fixture.encode()).hexdigest(),
              'normalized_sha256':reports[0]['normalized_sha256'],'point_count':148,
              'validators':reports,'axes':{'rows_of_load2':74,'columns_of_load2':74},
              'retrieved_at_utc':datetime.datetime.fromtimestamp(a.raw.stat().st_mtime,datetime.timezone.utc).isoformat(),
              'retrieval_timestamp_basis':'Local curl output file modification time, not server attestation',
              'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope':'Source authentication only; no n75 insertion, extension, score or search.'}
    for path,data in [(ROOT/'data/published-n74-raw.few',raw),
                      (ROOT/'data/published-n74.json',fixture.encode()),
                      (ROOT/'data/published-n74-validation.json',(json.dumps(evidence,indent=2)+'\n').encode())]:
        with path.open('xb') as f:f.write(data)
    print(json.dumps(evidence,sort_keys=True))


if __name__=='__main__':main()
