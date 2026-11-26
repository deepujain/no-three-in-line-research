"""Build the standalone evidence page from checked repository data."""
import datetime
import itertools
import json
import pathlib
from verify import verify_certificate, verify_certificate_bruteforce

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    seed = json.loads((ROOT / 'data/published-n78.json').read_text())
    certificate = {'n': 79, 'points': seed['points'],
                   'origin': 'Published Thomas Prellberg n=78 witness embedded in n=79; not a new construction',
                   'source_url': seed['source_url']}
    best = ROOT / 'data/best-n79.json'
    if best.exists():
        candidate = json.loads(best.read_text())
        if candidate['n'] == 79 and len(candidate['points']) >= len(certificate['points']):
            certificate = candidate
    reports = [verify_certificate(certificate), verify_certificate_bruteforce(certificate)]
    if not all(r['valid'] for r in reports):
        raise ValueError('Refusing to publish an invalid witness')
    # Only promote improvements after updating the page's claim/provenance text.
    if len(certificate['points']) != 156:
        raise ValueError('Improvement needs explicit claim and provenance review before publication')
    (ROOT / 'data/baseline-n79.json').write_text(json.dumps(certificate, indent=2) + '\n')
    (ROOT / 'data/baseline-verification.json').write_text(json.dumps(reports, indent=2) + '\n')
    points = certificate['points']
    used = {tuple(p) for p in points}
    choices = sorted(((x,y) for x in range(79) for y in range(79) if (x,y) not in used),
                     key=lambda p:(p[0]-39)**2+(p[1]-39)**2)
    conflict = None
    for c in choices:
        for a,b in itertools.combinations(points,2):
            if a[0] != b[0] and a[1] != b[1] and (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]):
                if (a[0]-b[0])**2+(a[1]-b[1])**2 < 1200:
                    conflict = {'candidate':list(c),'pair':[a,b]}
                    break
        if conflict:
            break
    if conflict is None:
        raise ValueError('No illustrative exact conflict found')
    data = {'n':79, 'points':points, 'conflict':conflict,
            'updated':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
            'approaches':json.loads((ROOT/'research/approaches.json').read_text())}
    payload=json.dumps(data,separators=(',',':')).replace('<','\\u003c')
    template=(ROOT/'docs/index.template.html').read_text()
    if template.count('__RESEARCH_DATA__') != 1:
        raise ValueError('Expected one data marker')
    (ROOT/'index.html').write_text(template.replace('__RESEARCH_DATA__',payload))
    print(json.dumps({'page':'index.html','points':len(points),'verified_by':2,'new_result':False}))


if __name__ == '__main__':
    main()
