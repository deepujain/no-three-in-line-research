"""Audit both completed size-three histories without replaying numerical search.

Refuses to issue a summary until both cursors are complete and stable. Reads and
rehashes every referenced file; all record counters remain trusted computation.
"""
import collections
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.corner_batch_worker import prepare_context, ORDER
from research.embedding_worker import read_json, resolve_reference
from src.verify import verify_certificate, verify_certificate_bruteforce


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    paths = [ROOT/'data/corner-batch-three-a.json', ROOT/'data/corner-batch-three-b.json']
    snapshots = [read_json(p) for p in paths]
    if not all(c['status'] == 'complete' and c['selected_frontiers_complete'] for c, _ in snapshots):
        print(json.dumps({'status':'incomplete', 'partitions':[
            {'path':str(p), 'status':c['status'], 'cursor':c['cursor'],
             'selected_anchor_count':c['selected_anchor_count'], 'selected_frontiers_complete':c['selected_frontiers_complete']}
            for p, (c, _) in zip(paths, snapshots)]}, indent=2))
        return None
    manifest_path = ROOT/'data/corner-anchor-frontier/manifest.json'
    seed_path = ROOT/'data/published-n78.json'
    scan_path = ROOT/'data/embedding-audit.json'
    inputs = {p.resolve():digest(p) for p in (manifest_path, seed_path, scan_path, ROOT/'research/corner_batch_worker.py', ROOT/'research/embedding_worker.py')}
    manifest, mhash = read_json(manifest_path)
    context = prepare_context(json.loads(seed_path.read_text()), json.loads(scan_path.read_text()), manifest)
    anchors = manifest['anchors']
    batch_hash = inputs[(ROOT/'research/corner_batch_worker.py').resolve()]
    partitions = []
    all_selected = set()
    all_records = {}
    totals = collections.Counter()
    valid_totals = collections.Counter()
    witnesses = {}
    for path, (cursor, chash), (start, stop, letter) in zip(paths, snapshots, [(10072,10184,'a'), (10184,10296,'b')]):
        directory = ROOT/f'data/corner-batch-three-{letter}-records'
        selected = [i for i in range(start, stop) if anchors[i]['total_deletion_sets'] <= 11628]
        assert len(selected) == 112 and not all_selected.intersection(selected)
        all_selected.update(selected)
        selection = hashlib.sha256(json.dumps(selected, separators=(',', ':')).encode()).hexdigest()
        expected = {'manifest_sha256':mhash, 'batch_source_sha256':batch_hash,
                    'source_normalized_sha256':context['source_normalized_sha256'],
                    'source_order_sha256':context['source_order_sha256'], 'selection_sha256':selection,
                    'start_anchor':start, 'stop_anchor':stop, 'max_anchor_cases':11628,
                    'records_directory':str(directory.resolve()), 'selected_anchor_count':112,
                    'cursor':112, 'completed_cases_sum':112*11628, 'total_selected_cases_sum':112*11628,
                    'current_anchor_next_offset':0, 'next_anchor_ordinal':None,
                    'distinct_deletion_sets':None, 'unselected_anchor_count':len(anchors)-112}
        assert all(cursor.get(k) == v for k,v in expected.items()), (letter, 'cursor identity')
        tested = collections.Counter(); valid = collections.Counter(); cases = records = 0
        partition_files = set()
        for ordinal in selected:
            a = anchors[ordinal]
            assert len(a['base_deletion_indices']) == 3 and a['total_deletion_sets'] == 11628
            tip_path = directory/(a['id']+'-tip.json')
            tip, thash = read_json(tip_path)
            all_records[tip_path.resolve()] = thash; partition_files.add(tip_path.resolve())
            assert tip['anchor_id'] == a['id'] and tip['manifest_sha256'] == mhash
            assert tip['cut'] == [0,0] and tip['frontier_complete'] is True
            assert tip['coverage'] == {'start':0, 'end':11628, 'gapless':True}
            assert tip['next_offset'] == tip['total_deletion_sets'] == 11628
            ref = tip['record']; record_path = resolve_reference(ref, tip_path); end = 11628
            anchor_cases = 0
            while True:
                resolved = record_path.resolve()
                assert resolved.parent == directory.resolve() and resolved not in all_records
                record, rhash = read_json(record_path)
                assert rhash == ref['sha256']
                all_records[resolved] = rhash; partition_files.add(resolved); records += 1
                identity = {'audit':'streamed_single_cover_exact_deletion_repair', 'anchor_id':a['id'],
                            'cut':[0,0], 'source_normalized_sha256':context['source_normalized_sha256'],
                            'source_order_sha256':context['source_order_sha256'], 'base_deletion_indices':a['base_deletion_indices'],
                            'exact_deletion_count':5, 'total_deletion_sets':11628, 'enumeration_order':ORDER,
                            'manifest_sha256':mhash, 'batch_source_sha256':batch_hash}
                assert all(record.get(k) == v for k,v in identity.items()), (a['id'], str(record_path))
                begin, finish, done = (record[k] for k in ('start_offset','next_offset','completed_deletion_sets'))
                assert all(type(x) is int for x in (begin,finish,done)) and 0 <= begin <= finish <= 11628
                assert finish == end and done == finish-begin
                assert record['status'] in ('complete','case_limit_incomplete','timeout_incomplete')
                assert record['status'] != 'complete' or finish == 11628
                t, v = record['tested_addition_subsets'], record['valid_addition_subsets']
                assert set(t) == set(v) == {'157','158'}
                assert all(type(x) is int and x >= 0 for x in (*t.values(), *v.values()))
                assert all(v[k] <= t[k] for k in t)
                tested.update(t); valid.update(v); anchor_cases += done
                # This audit expects self-contained certificates and the batch
                # witness inventory; unexpected external references fail closed.
                assert not record.get('witness_files', [])
                for cert in record.get('found_certificates', []):
                    checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
                    assert all(c['valid'] and c['point_count'] in (157,158) for c in checks)
                    assert checks[0]['normalized_sha256'] == checks[1]['normalized_sha256']
                    witnesses[checks[0]['normalized_sha256']] = 'record'
                ref = record.get('previous_record')
                if ref is None:
                    assert begin == 0
                    break
                end = begin; record_path = resolve_reference(ref, record_path)
            assert anchor_cases == 11628
            cases += anchor_cases
        assert cases == cursor['completed_cases_sum']
        disk_witnesses = list(directory.glob('batch-witness-*.json')) + list(directory.glob('embedding-witness-*.json'))
        for witness in disk_witnesses:
            cert, whash = read_json(witness)
            checks = [verify_certificate(cert), verify_certificate_bruteforce(cert)]
            assert all(c['valid'] and c['point_count'] in (157,158) for c in checks)
            assert checks[0]['normalized_sha256'] == checks[1]['normalized_sha256']
            witnesses[checks[0]['normalized_sha256']] = 'file'
            all_records[witness.resolve()] = whash
        assert (cursor['verified_witness_events'] == 0) == (not disk_witnesses)
        disk_json = {p.resolve() for p in directory.glob('*.json')}
        partitions.append({'name':letter, 'ordinal_range':[start,stop], 'selection_sha256':selection,
                           'cursor_sha256':chash, 'anchors':len(selected), 'anchor_cases':cases,
                           'tip_count':len(selected), 'linked_records':records,
                           'all_json_files':len(disk_json), 'unreferenced_json_files':len(disk_json-partition_files-set(p.resolve() for p in disk_witnesses)),
                           'witness_files':len(disk_witnesses), 'tested':dict(tested), 'valid':dict(valid)})
        totals.update(tested); valid_totals.update(valid)
    assert all_selected == set(range(10072,10296))
    for p, h in {**inputs, **all_records, **{p.resolve():h for p, (_,h) in zip(paths,snapshots)}}.items():
        assert digest(p) == h, ('changed while auditing',str(p))
    index = ''.join(f'{h}  {p.relative_to(ROOT)}\n' for p,h in sorted(all_records.items(), key=lambda pair:str(pair[0])))
    return {'status':'complete_selected_size_three_anchor_families_conditional_on_trusted_computation',
            'audited_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'manifest_sha256':mhash, 'source_normalized_sha256':context['source_normalized_sha256'],
            'source_order_sha256':context['source_order_sha256'], 'input_hashes':{str(p.relative_to(ROOT)):h for p,h in inputs.items()},
            'referenced_file_count':len(all_records), 'referenced_path_hash_index_sha256':hashlib.sha256(index.encode()).hexdigest(),
            'selected_anchor_count':len(all_selected), 'completed_anchor_cases_sum':sum(p['anchor_cases'] for p in partitions),
            'unique_deletion_sets':None, 'tested_addition_subsets':dict(totals), 'valid_addition_subsets':dict(valid_totals),
            'unique_verified_witnesses':len(witnesses), 'partitions':partitions,
            'scope':'Two size-three selected partitions for one corner and one source; anchor cases overlap, and this audit alone does not close the full corner family.',
            'trust':'Linked bytes, identities, gapless intervals and counters checked; numerical computation not replayed. Hash consistency is not an execution proof.'}


if __name__ == '__main__':
    summary = audit()
    if summary is None: sys.exit(2)
    output = ROOT/'data/corner-batch-three-summary.json'
    output.write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print(json.dumps(summary, indent=2, sort_keys=True))
