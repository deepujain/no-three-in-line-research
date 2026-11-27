"""Explicit independent v2 binding; preserves the failed v1 suite and evidence."""
import hashlib
import json
from pathlib import Path
from research import restricted_three_row64_independent_association_v1 as prior

V2='e5325621cf6f0c48f0d08c94b3439269b47756739f07f5cd7f271347586df210'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    assert sha(prior.__file__)=='e305d855c7d3723377f83e334e3e094bad819ec85a876dbd95dbdd5c5f8d4d26'
    assert sha(prior.worker.__file__)==V2
    prior.WORKER_SHA=V2
    result=prior.run()
    result['v2_binding_source_sha256']=sha(__file__)
    result['binding_note']='Prior suite expected-worker pin explicitly rebound in memory to frozen v2; failed v1 source/evidence preserved.'
    assert result['passed'] and not result['unexpected_acceptances']
    return result


if __name__=='__main__':
    result=run();path=Path('data/restricted-three-row64-independent-association-v2.json');assert not path.exists()
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(passed=True,mutations=result['mutation_count'],rejections=len(result['rejections']),
                         source_sha256=sha(__file__),evidence_sha256=sha(path))))
