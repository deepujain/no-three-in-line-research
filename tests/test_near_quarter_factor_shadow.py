import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research import near_quarter_factor_shadow as m
from research.near_quarter_packed_state import PackedOrbitState
from src.verify import verify_certificate_bruteforce


class ShadowTests(unittest.TestCase):
    def test_complete_masks_against_independent_geometry(self):
        for n in (3,5,7):
            state=PackedOrbitState(n);diag=state.bounds['four']+1
            sample=m.mask_and_bounds(n,[diag],lambda:None)
            self.assertEqual(len(sample['mask']),state.bounds['four'])
            for i,marked in enumerate(sample['mask']):
                points=list(state.model['orbits'][diag-1])+list(state.model['orbits'][i])
                report=verify_certificate_bruteforce({'n':n,'points':[list(p) for p in points]})
                from collections import Counter
                axis=all(c<=2 for c in Counter(x for x,y in points).values()) and all(c<=2 for c in Counter(y for x,y in points).values())
                self.assertEqual(bool(marked),report['valid'] and axis)
            self.assertEqual(sum(sample['demands']),2*(n//2))
            self.assertEqual(len(sample['edges']),sum(sample['mask']))

    def test_interruption_no_mask_verdict(self):
        counter=[0]
        def check():
            counter[0]+=1
            if counter[0]==3: raise TimeoutError
        with self.assertRaises(TimeoutError): m.mask_and_bounds(3,[2],check)

    def test_no_input_change_and_explicit_unstarted_on_timeout(self):
        clock=lambda:1
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'INPUTS',()):
            report=m.run(Path(tmp),1,clock=clock)
            self.assertTrue(report['complete'])
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'INPUTS',()):
            with patch.object(m,'prefix_paths',side_effect=TimeoutError):
                report=m.run(Path(tmp),1,clock=clock)
            self.assertFalse(report['complete']);self.assertEqual(report['status'],'timeout')


if __name__=='__main__':unittest.main()

class ShadowBoundaryTests(unittest.TestCase):
    def test_real_tiny_checkpoint_selected_path_excludes_pending(self):
        import hashlib
        from research.near_quarter_rowbatch_core import PackedRowBatchCore, PENDING, ZERO
        from research import near_quarter_rowbatch_checkpoint as ck
        core=PackedRowBatchCore(9)
        for _ in range(1000):
            if len(core.frames)>=2 and core.frames[-1].phase==PENDING:
                break
            core.step()
        else:
            self.fail('no tiny incoming+pending frame')
        raw=ck.encode(core,parent_hash=ZERO,chain_id=b'C'*32)
        parsed=ck.parse(raw,trusted_record=ck.TrustedRecord(hashlib.sha256(raw).digest(),ZERO,b'C'*32),expected_identity=ck.identity(core))
        ids=m.selected_prefix(parsed)
        self.assertTrue(parsed.frames[-1].pending)
        self.assertEqual(set(ids),set(core.state.selected))
        state=PackedOrbitState(9)
        for v in ids: self.assertTrue(state.push(v))
        self.assertEqual(set(state.points),set(core.state.points))
        self.assertTrue(set(parsed.frames[-1].pending).isdisjoint(ids))

    def test_nonempty_mask_and_frozen_old_bounds(self):
        from research.near_quarter_rowbatch_core import PackedRowBatchCore, ORBIT_SHORTFALL, ROW_SHORTFALL, RADIUS_SHORTFALL
        from research.near_quarter_readonly_probe import probe_orbit
        from collections import Counter
        for n in (5,7):
            core=PackedRowBatchCore(n);diag=core.state.bounds['four']+1
            self.assertTrue(core.state.push(diag))
            candidate=next(i for i in range(1,core.state.bounds['four']+1) if probe_orbit(core.state,i))
            self.assertTrue(core.state.push(candidate))
            sample=m.mask_and_bounds(n,[diag,candidate],lambda:None)
            reason,_,_=core._scan(lambda:None)
            expected=(ORBIT_SHORTFALL if sample['orbit_shortfall'] else ROW_SHORTFALL if sample['row_shortfall'] else RADIUS_SHORTFALL if sample['graph_obstruction'] else 0)
            self.assertEqual(reason,expected)
            for i,marked in enumerate(sample['mask']):
                if i+1 in (diag,candidate):
                    self.assertFalse(marked);continue
                pts=list(core.state.points)+list(core.state.model['orbits'][i])
                report=verify_certificate_bruteforce({'n':n,'points':[list(p) for p in pts]})
                axes=all(v<=2 for v in Counter(x for x,y in pts).values()) and all(v<=2 for v in Counter(y for x,y in pts).values())
                self.assertEqual(bool(marked),report['valid'] and axes)

    def test_partial_samples_and_input_bytes_unchanged(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); chain=base/'chain';chain.mkdir()
            paths=[]
            for name in ('a.nqrb','b.receipt.json','audit.json'):
                p=chain/name;p.write_bytes(name.encode());paths.append(p)
            hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
            inputs=(('main',str(chain),'a','b',str(paths[2]),hashes[2],2),)
            # Fixed names are a/b; pins in the mocked input must match their file bytes.
            paths[0].rename(chain/(hashes[0]+'.nqrb'));paths[1].rename(chain/(hashes[1]+'.receipt.json'))
            paths=[chain/(hashes[0]+'.nqrb'),chain/(hashes[1]+'.receipt.json'),paths[2]]
            inputs=(('main',str(chain),hashes[0],hashes[1],str(paths[2]),hashes[2],2),)
            inputs=inputs+(('middle',str(chain),hashes[0],hashes[1],str(paths[2]),hashes[2],2),)
            fake_paths=[(label,d,(1,)) for label in ('main','middle') for d in (0,1,2)]
            sample={'demands':[1,1],'edges':[[0,1]],'orbit_shortfall':False,'row_shortfall':False,'graph_obstruction':None}
            with patch.object(m,'INPUTS',inputs), patch.object(m,'prefix_paths',return_value=(fake_paths,[])), patch.object(m,'mask_and_bounds',side_effect=lambda *args: dict(sample)), patch.object(m,'radius_factor',side_effect=[{'status':'sat'},{'status':'unknown'}]):
                report=m.run(base,4,clock=lambda:0)
            self.assertFalse(report['complete']);self.assertEqual(report['status'],'timeout')
            self.assertEqual([s['status'] for s in report['samples']],['complete','unknown','unstarted','unstarted','unstarted','unstarted'])
            self.assertFalse(report['samples'][1]['useful_unsat'])
            self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() for p in paths],hashes)
