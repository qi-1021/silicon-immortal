import json
import unittest

from silicon_professor.data.core_designs import default_hardware
from silicon_professor.engine.core_studio import run_design, verify_design, structure, design_model
from silicon_professor.engine.labs import json_result
from silicon_professor.engine.observatory import execution_snapshot


class TestObservatory(unittest.TestCase):
    def test_smt_testbench_compares_solo_runs_and_verifies_both_contexts(self):
        h=default_hardware('cpu');h.update(smt_threads=2,mshrs=4,branch_predictor='two_bit')
        r=run_design('cpu',h,dict(source='LW x1,0(x0)\nHALT',source2='ADDI x1,x0,9\nHALT',memory='0 7'))
        self.assertIn('speedup',r)
        self.assertEqual(len(r['threads']),2)
        self.assertIn('双上下文隔离',[c['name'] for c in verify_design('cpu',h)['cases']])
        self.assertIn('2 个上下文',structure('cpu',h)['nodes'][0]['detail'])
        self.assertGreater(design_model('cpu','SMT',h)['logic_area'],design_model('cpu','solo',default_hardware('cpu'))['logic_area'])
        json.dumps(json_result(r))
        for tid in (0,1):
            s=execution_snapshot(r,r['cycles'],thread=tid)
            self.assertEqual(s['registers'],r['threads'][tid]['registers'])
            self.assertEqual(s['retired'],r['threads'][tid]['instructions'])

    def test_gpu_issue_events_match_resource_budget_and_output_ready_time(self):
        h=default_hardware('gpu');h.update(alu_latency=8,resident_warps=4)
        r=run_design('gpu',h,dict(task='branch',pattern='alternating',elements=19))
        self.assertTrue(all(w['issues'] for w in r['warps']))
        issued={}
        for w in r['warps']:
            for event in w['issues']:
                key=(w['processor'],event['cycle'])
                self.assertNotIn(key,issued);issued[key]=True
                self.assertEqual(event['done']-event['cycle'],8)
        first=execution_snapshot(r,0)
        self.assertTrue(first['active'])
        self.assertTrue(all(v is None for v in first['output']))
        final=execution_snapshot(r,r['cycles'])
        self.assertEqual(final['output'],r['output']);self.assertEqual(final['phase'],'完成')
        self.assertEqual(execution_snapshot(r,r['compute_cycles'])['phase'],'传输账本')

    def test_npu_wavefront_and_wrap_accumulators(self):
        h=default_hardware('npu');h.update(rows=2,cols=2)
        r=run_design('npu',h,dict(m=2,n=2,k=2))
        s=execution_snapshot(r,1)
        self.assertEqual(s['accumulators'][0][0],r['input_a'][0][0]*r['input_b'][0][0])
        self.assertEqual(s['accumulators'][1][1],0)
        self.assertEqual(execution_snapshot(r,r['cycles'])['output'],r['output'])
        for cycle in range(r['compute_cycles']):
            self.assertLessEqual(len(execution_snapshot(r,cycle)['active']),4)

    def test_isp_stages_and_progress_are_actual_pixel_results(self):
        h=default_hardware('isp')
        r=run_design('isp',h,dict(width=4,height=4,gain=2.0,gamma=1.0))
        self.assertEqual(r['stage_outputs']['quantize'],r['output'])
        self.assertNotEqual(r['stage_outputs']['black_level'],r['stage_outputs']['gain'])
        first=execution_snapshot(r,0)
        self.assertEqual(first['emitted_pixels'],0)
        final=execution_snapshot(r,r['cycles'])
        self.assertEqual(final['emitted_pixels'],16)
        self.assertEqual(final['output'],r['output'])
        h['demosaic_enabled']=False
        self.assertNotIn('demosaic',run_design('isp',h)['stage_outputs'])

    def test_cycle_boundaries_and_no_mutation(self):
        for kind in ('cpu','gpu','npu','isp'):
            r=run_design(kind,default_hardware(kind))
            for bad in (-1,r['cycles']+1,True,1.5):
                with self.assertRaises(ValueError):execution_snapshot(r,bad)
            execution_snapshot(r,0);execution_snapshot(r,r['cycles'])
            self.assertTrue(r['functional_check'])
