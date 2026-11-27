import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research import corner_batch_worker as batch
from research.corner_anchor_frontier import prepare
from research.embedding_audit import stream_cover_repairs,validate_repair_source
from research.embedding_worker import load_gapless_chain
from src.verify import normalized_sha256,verify_certificate_bruteforce


class CornerBatchTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(redirect_stdout(io.StringIO()))
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.seed={'n':2,'points':[[0,0],[0,1],[1,0],[1,1]]}
        self.scan={'source_normalized_sha256':normalized_sha256(2,self.seed['points'])}
        self.manifest=prepare(self.seed,self.scan,self.root/'input',initial_origins=0,deletion_count=2)
        self.manifest_path=self.root/'input/manifest.json'
        self.output=self.root/'batch.json';self.records=self.root/'records'

    def run_batch(self,**options):
        values=dict(seconds=10,max_cases=100,chunk_cases=1)
        values.update(options)
        return batch.run_batch(self.manifest_path,self.seed,self.scan,self.output,self.records,**values)

    def test_prepared_chunks_match_existing_exact_engine(self):
        context=batch.prepare_context(self.seed,self.scan,self.manifest)
        for anchor in self.manifest['anchors']:
            for offset in range(anchor['total_deletion_sets']+1):
                expected=stream_cover_repairs(self.seed,self.scan,(0,0),anchor['base_deletion_indices'],
                    deletion_count=2,start_offset=offset,expected_source_order_sha256=context['source_order_sha256'],
                    max_cases=2,seconds=10)
                actual=batch.stream_prepared(context,anchor,offset,2,10)
                for key in expected:
                    if key!='elapsed_seconds':self.assertEqual(actual[key],expected[key],(anchor['id'],offset,key))

    def test_global_case_cap_partial_restart_and_existing_worker_compatibility(self):
        with patch.object(batch,'validate_repair_source',wraps=validate_repair_source) as validation:
            first=self.run_batch(max_cases=1)
            self.assertEqual(validation.call_count,1)
        self.assertEqual(first['cursor'],0)
        self.assertEqual(first['current_anchor_next_offset'],1)
        self.assertEqual(first['completed_cases_sum'],1)
        second=self.run_batch(max_cases=2)
        self.assertEqual(second['cursor'],1)
        self.assertEqual(second['completed_cases_sum'],3)
        final=self.run_batch()
        self.assertTrue(final['selected_frontiers_complete'])
        self.assertEqual(final['completed_cases_sum'],12)
        self.assertEqual(final['completed_this_invocation'],9)
        for anchor in self.manifest['anchors']:
            tip=self.records/(anchor['id']+'-tip.json')
            _,record,_,_=load_gapless_chain(tip,self.seed,self.scan)
            self.assertEqual(record['next_offset'],anchor['total_deletion_sets'])
        self.assertIsNone(final['distinct_deletion_sets'])
        self.assertIn('not unique',final['case_count_semantics'])

    def test_zero_budget_restart_cannot_regress_active_progress(self):
        self.run_batch(max_cases=1)
        for bounds in ({'seconds':0},{'max_cases':0}):
            restarted=self.run_batch(**bounds)
            self.assertEqual(restarted['cursor'],0)
            self.assertEqual(restarted['current_anchor_next_offset'],1)
            self.assertEqual(restarted['completed_cases_sum'],1)
            self.assertEqual(restarted['completed_this_invocation'],0)

    def test_witness_is_persisted_before_advancing_tip(self):
        original=batch._publish_tip
        checked=[]
        def inspect(path,latest,anchor,digest):
            if latest[1]['found_certificates']:
                files=list(self.records.glob('batch-witness-*.json'))
                self.assertTrue(files)
                for witness in files:self.assertTrue(verify_certificate_bruteforce(json.loads(witness.read_text()))['valid'])
                # The prior cursor is still at its previous committed offset.
                if self.output.exists():
                    cursor=json.loads(self.output.read_text())
                    self.assertLess(cursor['completed_cases_sum'],latest[1]['next_offset'])
                checked.append(True)
            return original(path,latest,anchor,digest)
        with patch.object(batch,'_publish_tip',side_effect=inspect):self.run_batch(max_cases=1)
        self.assertTrue(checked)

    def test_manifest_order_selection_and_cursor_corruption_are_rejected(self):
        self.run_batch(max_cases=1)
        original=self.manifest_path.read_bytes()
        value=json.loads(original);value['review_note']='changed bytes'
        self.manifest_path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'manifest/source/selection'):self.run_batch()
        self.manifest_path.write_bytes(original)
        reordered=copy.deepcopy(self.seed);reordered['points'].reverse()
        with self.assertRaisesRegex(ValueError,'provenance'):
            batch.run_batch(self.manifest_path,reordered,self.scan,self.output,self.records)
        with self.assertRaisesRegex(ValueError,'manifest/source/selection'):self.run_batch(max_anchor_cases=1)
        stored=json.loads(self.output.read_text());stored['cursor']=1
        self.output.write_text(json.dumps(stored))
        with self.assertRaisesRegex(ValueError,'skips a partial'):self.run_batch()

    def test_tip_ahead_of_cursor_is_recovered_and_history_tampering_rejected(self):
        self.run_batch(max_cases=3)
        stored=json.loads(self.output.read_text());stored['cursor']=0
        self.output.write_text(json.dumps(stored))
        restored=self.run_batch(seconds=0)
        self.assertEqual(restored['cursor'],1)
        self.assertEqual(restored['completed_cases_sum'],3)
        origin=self.records/(self.manifest['anchors'][0]['id']+'-origin.json')
        origin.write_text(origin.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'hash/gap'):self.run_batch(seconds=0)

    def test_batch_and_tip_locks_are_exclusive(self):
        with batch._lock(self.output):
            with self.assertRaisesRegex(ValueError,'another worker'):self.run_batch()
        self.run_batch(max_cases=1)
        tip=self.records/(self.manifest['anchors'][0]['id']+'-tip.json')
        with batch._lock(tip):
            with self.assertRaisesRegex(ValueError,'another worker'):self.run_batch()

    def test_interrupted_deletion_case_does_not_advance_cursor(self):
        self.run_batch(seconds=0)
        context=batch.prepare_context(self.seed,self.scan,self.manifest)
        with patch.object(batch,'gap_blockers',side_effect=batch.ChunkTimeout):
            result=batch.stream_prepared(context,self.manifest['anchors'][0],0,1,10)
        self.assertEqual(result['status'],'timeout_incomplete')
        self.assertEqual(result['next_offset'],0)
        self.assertEqual(result['completed_deletion_sets'],0)


if __name__=='__main__':unittest.main()
