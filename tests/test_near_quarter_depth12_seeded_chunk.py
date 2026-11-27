from contextlib import ExitStack,contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from research import near_quarter_depth12_seeded_chunk as m
from research.seeded_cut_boolean_oracle import fixture


def synthetic():
    f=fixture();ids=f['retained_cut_ids'];records=[{'ids':c,'points':[f['point_by_local_variable'][v-1] for v in c]} for c in ids]
    seed={'depth':12,'status':'timeout','complete':False,'selected_prefix_ids':list(m.PREFIX),'complete_mask_length':1521,'complete_mask_sha256':m.MASK_HASH,'mask_count':5,'orbit_variable_ids':[1,2,3,4,5],'pair_cut_ids':[[4,5]],'triple_cut_ids':ids,'triple_cut_records':records,'triple_cuts':1,'retained_triple_cuts':1,'new_triple_cuts':0,'total_triple_cuts':1}
    state=SimpleNamespace(map_digest=bytes.fromhex(m.MAP_HASH),points=(),model={'orbits':tuple((tuple(p),) for p in f['point_by_local_variable'])})
    return seed,state


class ConstraintTests(unittest.TestCase):
    @contextmanager
    def tiny(self):
        with patch.object(m,'PRIMARY_COUNT',5),patch.object(m,'ANCHOR_CUT_COUNT',1),patch.object(m,'BINARY_COUNT',1):yield

    def check(self,seed,state,anchor=None):
        return m.validate_constraints(seed,anchor or synthetic()[0],[[4,5]],state,[1,2,3,4,5],m.MASK_HASH,lambda:None)

    def test_valid_seed_and_dynamic_append_preserve_anchor(self):
        seed,state=synthetic()
        with self.tiny():
            self.assertEqual(self.check(seed,state),[(4,5)])
            seed['triple_cut_ids'].append([1,2,4]);seed['triple_cut_records'].append({'ids':[1,2,4],'points':[[0,0],[1,0],[3,0]]})
            seed['triple_cuts']=seed['total_triple_cuts']=2;seed['new_triple_cuts']=1
            self.assertEqual(self.check(seed,state),[(4,5)])
            # A subsequent chunk loads the whole previous list as retained, with no reset.
            next_seed=deepcopy(seed);next_seed['retained_triple_cuts']=2;next_seed['new_triple_cuts']=0
            self.assertEqual(self.check(next_seed,state),[(4,5)])
        self.assertEqual(1000-487,513)

    def test_malformed_scope_binary_and_ternary_seeds_fail(self):
        original,state=synthetic()
        cases=[
            (lambda s:s['selected_prefix_ids'].reverse(),'prefix'),
            (lambda s:s['orbit_variable_ids'].reverse(),'map'),
            (lambda s:s.update(complete_mask_sha256='bad'),'mask'),
            (lambda s:s.update(pair_cut_ids=[[1,2]]),'binary'),
            (lambda s:s.update(pair_cut_ids=[[True,5]]),'binary'),
            (lambda s:s.update(triple_cuts=True),'count'),
            (lambda s:s.update(retained_triple_cuts=True),'count'),
            (lambda s:s['triple_cut_ids'].__setitem__(0,[1,2,4]),'anchor'),
            (lambda s:s['triple_cut_records'][0]['points'].__setitem__(2,[2,1]),'anchor')]
        with self.tiny():
            for change,message in cases:
                seed=deepcopy(original);change(seed)
                with self.assertRaisesRegex(ValueError,message):self.check(seed,state)
            for cut,points,message in [([1,1,4],[[0,0],[1,0],[3,0]],'IDs'),([2,1,4],[[0,0],[1,0],[3,0]],'IDs'),([1,2,6],[[0,0],[1,0],[3,0]],'IDs'),([1,2,4],[[0,0],[0,0],[3,0]],'points'),([1,2,4],[[0,0],[1,0],[3,1]],'collinear'),([1,2,4],[[0,0],[1,0],[2,0]],'membership'),([1,2,4],[[0,0],[1,0],[79,0]],'points'),([1,2,4],[[0,0],[1,0],[True,0]],'points')]:
                seed=deepcopy(original);seed['triple_cut_ids'].append(cut);seed['triple_cut_records'].append({'ids':cut,'points':points});seed.update(triple_cuts=2,total_triple_cuts=2,new_triple_cuts=1)
                with self.assertRaisesRegex(ValueError,message):self.check(seed,state)
            seed=deepcopy(original);seed['triple_cut_ids']*=2;seed['triple_cut_records']*=2;seed.update(triple_cuts=2,total_triple_cuts=2,new_triple_cuts=1)
            with self.assertRaisesRegex(ValueError,'duplicate'):self.check(seed,state)
            state.map_digest=b'x'*32
            with self.assertRaisesRegex(ValueError,'map'):self.check(original,state)


class LoaderTests(unittest.TestCase):
    def write(self,path,value):
        path.write_text(json.dumps(value));return m.digest(path)

    @contextmanager
    def data(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);seed,_=synthetic();source='research/near_quarter_depth12_cut_continuation.py';source_sha=m.digest(m.ROOT/source)
            anchor=d/'anchor'/'report.json';anchor.parent.mkdir();receipt=d/'anchor-receipt.json';audit=d/'anchor-audit.json';base=d/'base-audit.json'
            report={'method':'anchor','status':'timeout','complete':False,'packed_source_manifest':m.frozen.source_manifest(),'stages':[seed],'local_source_sha256':{source:source_sha}}
            rh=self.write(anchor,report)
            gate={'gate_status':'worker_error','returncode':2,'trigger_gate_status':None,'monitor_error':None,'seconds_limit':30,'rss_limit_mib':256,'cleanup_status':'clean','cleanup_error':None,'elapsed_seconds':1,'peak_sampled_rss_kib':100,'rss_samples':2,'cleanup_samples':1,'cleanup_elapsed_seconds':0.01,'rss_scope':'guard parent plus spawned process group and observed descendants; native heap included','gate_semantics':'sampled RSS gate; cleanup included in wall gate; possible sampling overshoot; transient ps excluded'}
            rec={'status':'completed','sources_unchanged':True,'gate':gate,'argv':['.venv/bin/python',source,'--output-dir',str(anchor.parent)],'sources_before':{source:source_sha}}
            eh=self.write(receipt,rec)
            ah=self.write(audit,{'accepted':True,'report_sha256':rh,'receipt_sha256':eh,'total_ternary_cuts':1})
            bh=self.write(base,{'accepted':True,'stages':[{'depth':12,'independent_pair_checks':67896,'independent_complete_mask_sha256':m.MASK_HASH,'pair_rejection_witnesses':[{'ids':[4,5]}]}]})
            with ExitStack() as stack:
                for key,value in [('ANCHOR_REPORT',str(anchor)),('ANCHOR_RECEIPT',str(receipt)),('ANCHOR_AUDIT',str(audit)),('BASE_AUDIT',str(base)),('ANCHOR_CUT_COUNT',1),('FIXED_PINS',{str(anchor):rh,str(receipt):eh,str(audit):ah,str(base):bh})]:stack.enter_context(patch.object(m,key,value))
                yield SimpleNamespace(d=d,anchor=anchor,receipt=receipt,rh=rh,eh=eh,report=report,rec=rec)

    def test_actual_anchor_identity_reads_only(self):
        seed,anchor,binary=m.load_seed(m.ANCHOR_REPORT,m.FIXED_PINS[m.ANCHOR_REPORT],m.ANCHOR_RECEIPT,m.FIXED_PINS[m.ANCHOR_RECEIPT],lambda:None,{})
        self.assertEqual((seed['triple_cuts'],len(binary)),(487,9539));self.assertEqual(seed['triple_cut_records'],anchor['triple_cut_records'])

    def test_explicit_hash_limits_and_receipt_provenance(self):
        with self.data() as d:
            seed,_,cuts=m.load_seed(d.anchor,d.rh,d.receipt,d.eh,lambda:None,{})
            self.assertEqual(seed['triple_cuts'],1);self.assertEqual(cuts,[[4,5]])
            for wrong_report,wrong_receipt in [('0'*64,d.eh),(d.rh,'0'*64)]:
                with self.assertRaisesRegex(ValueError,'hash'):m.load_seed(d.anchor,wrong_report,d.receipt,wrong_receipt,lambda:None,{})
            with self.assertRaisesRegex(ValueError,'output provenance'):
                m.validate_receipt(d.anchor.with_name('unrelated.json'),d.report,d.rec,lambda:None,{})
            with self.assertRaisesRegex(ValueError,'byte bound'):m.read_pinned(d.anchor,d.rh,1,lambda:None,{})
            for mutate in (lambda r:r.update(status='running'),lambda r:r.update(sources_unchanged=False),lambda r:r['argv'].__setitem__(-1,'wrong-output'),lambda r:r['gate'].update(cleanup_status='failed')):
                rec=deepcopy(d.rec);mutate(rec)
                with self.assertRaises((ValueError,RuntimeError)):m.validate_receipt(d.anchor,d.report,rec,lambda:None,{})

    def test_dynamic_second_seed_binds_parent_arrays_and_execution(self):
        with self.data() as d:
            seed=deepcopy(d.report['stages'][0]);seed.update(triple_cuts=2,total_triple_cuts=2,new_triple_cuts=1)
            seed['triple_cut_ids'].append([1,2,4]);seed['triple_cut_records'].append({'ids':[1,2,4],'points':[[0,0],[1,0],[3,0]]})
            source='research/near_quarter_depth12_seeded_chunk.py';sh=m.digest(m.ROOT/source)
            path=d.d/'next'/'report.json';path.parent.mkdir();receipt=d.d/'next-receipt.json'
            parent={'report':str(d.anchor),'report_sha256':d.rh,'receipt':str(d.receipt),'receipt_sha256':d.eh}
            report={'method':m.METHOD,'status':'timeout','complete':False,'packed_source_manifest':m.frozen.source_manifest(),'local_source_sha256':{source:sh},'seed_input':parent,'stages':[seed]};rh=self.write(path,report)
            rec=deepcopy(d.rec);rec['sources_before']={source:sh};rec['argv']=['.venv/bin/python',source,'--output-dir',str(path.parent),'--seed-report',str(d.anchor),'--seed-report-sha256',d.rh,'--seed-receipt',str(d.receipt),'--seed-receipt-sha256',d.eh];eh=self.write(receipt,rec)
            loaded,_,_=m.load_seed(path,rh,receipt,eh,lambda:None,{})
            self.assertEqual(loaded['triple_cut_ids'],[[1,2,3],[1,2,4]])
            rec['argv'][-1]='0'*64
            with self.assertRaisesRegex(ValueError,'predecessor provenance'):m.load_seed(path,rh,receipt,self.write(receipt,rec),lambda:None,{})
            rec['argv'][-1]=d.eh;eh=self.write(receipt,rec)
            report['stages'][0]['triple_cut_records'][0]['points'][0]=[0,1]
            with self.assertRaisesRegex(ValueError,'lost or changed'):m.load_seed(path,self.write(path,report),receipt,eh,lambda:None,{})


class RunnerTests(unittest.TestCase):
    @contextmanager
    def fake(self,status='timeout',at_cap=False,mutate_input=False):
        tick=[0];events=[];deadlines=[];seed,_=synthetic()
        class State:
            points=tuple((i,0) for i in range(50))
            def __init__(self,n,check):pass
            def push(self,v):return True
        class Solver:
            def __init__(self,**kw):events.append('solver');self.clauses=[]
            def add_clause(self,c):self.clauses.append(c)
            def interrupt(self):events.append('interrupt')
            def delete(self):events.append('delete')
        class Timer:
            def __init__(self,remaining,callback):events.append(('timer',remaining))
            def start(self):events.append('start')
            def cancel(self):events.append('cancel')
            def join(self):events.append('join')
        with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
            input_path=Path(tmp)/'input';input_path.write_text('before')
            def load(*args):
                if mutate_input:args[-1][str(input_path)]=m.digest(input_path)
                return seed,deepcopy(seed),[[4,5]]
            def solve(solver,state,variables,demands,edges,stage,check,fired,deadline,clock,out,**kw):
                deadlines.append(deadline);self.assertEqual(kw,{'target_orbits':27,'cut_limit':1 if at_cap else 1000})
                self.assertEqual(solver.clauses,[[-4,-5],[-1,-2,-3]])
                if mutate_input:input_path.write_text('after')
                tick[0]=1
                if status=='timeout':raise TimeoutError
                if status=='error':raise RuntimeError('native model error')
                stage['status']=status;stage['complete']=status in ('unsat_solver_reported','witness')
            for obj,key,value in [(m,'load_seed',load),(m,'validate_constraints',lambda *a:[(4,5)]),(m,'PRIMARY_COUNT',5),(m,'DEGREE_COUNTS',(5,0,0)),(m,'CUT_LIMIT',1 if at_cap else 1000),(m,'Timer',Timer),(m.frozen,'PackedOrbitState',State),(m.frozen,'mask_and_bounds',lambda *a:{'mask':[1]*5+[0]*1516,'mask_sha256':m.MASK_HASH,'demands':[54],'edges':[(0,1)]*5}),(m.frozen,'degree_clauses',lambda *a:([],SimpleNamespace(top=5))),(m.frozen,'validate_formula',lambda *a:0),(m.frozen,'solve_models',solve),(m.frozen,'source_manifest',lambda:{}),(m.frozen,'incompatible_pairs',lambda *a:(_ for _ in ()).throw(AssertionError('pair reprobe')))]:stack.enter_context(patch.object(obj,key,value))
            stack.enter_context(patch('pysat.solvers.Solver',Solver))
            yield SimpleNamespace(tick=tick,events=events,deadlines=deadlines)

    def run_fake(self,f):
        with tempfile.TemporaryDirectory() as tmp:return m.run(Path(tmp),25,'seed','0'*64,'receipt','0'*64,clock=lambda:f.tick[0])

    def test_one_stage_shared_deadline_and_cleanup_all_answers(self):
        for status in ('timeout','solver_unknown','unsat_solver_reported','witness','cut_limit'):
            with self.fake(status) as f:r=self.run_fake(f)
            self.assertEqual(r['status'],status);self.assertEqual(len(r['stages']),1)
            self.assertEqual(r['stages'][0]['retained_triple_cuts'],1);self.assertEqual(r['stages'][0]['new_triple_cuts'],0)
            self.assertEqual(f.deadlines,[25]);self.assertEqual([e for e in f.events if e in ('cancel','join','delete')],['cancel','join','delete'])
        with self.fake('error') as f,self.assertRaisesRegex(RuntimeError,'native model'):self.run_fake(f)
        self.assertEqual([e for e in f.events if e in ('cancel','join','delete')],['cancel','join','delete'])

    def test_cap_avoids_solver_and_input_mutation_blocks_publication(self):
        with self.fake(at_cap=True) as f:r=self.run_fake(f)
        self.assertEqual(r['status'],'cut_limit');self.assertNotIn('solver',f.events)
        with self.fake(mutate_input=True) as f,self.assertRaisesRegex(ValueError,'immutable source/input'):self.run_fake(f)
        real=m.digest
        with self.fake('unsat_solver_reported') as f,patch.object(m,'digest',side_effect=lambda p:'0'*64 if f.tick[0] and str(p).endswith('near_quarter_depth12_seeded_chunk.py') else real(p)),self.assertRaisesRegex(ValueError,'immutable source/input'):
            self.run_fake(f)


if __name__=='__main__':unittest.main()
