import unittest

from silicon_professor.engine.lab_cpu import simulate_core
from silicon_professor.engine.lab_accelerators import gpu_lab, isp_lab


class TestCoreResources(unittest.TestCase):
    def test_in_order_cannot_issue_past_blocked_instruction(self):
        source='ADDI x1,x0,3\nMUL x2,x1,x1\nADD x3,x2,x1\nADDI x4,x0,7\nHALT'
        args=dict(width=4,execution_ports=4,pipeline=2,multiply_latency=12)
        ordered=simulate_core(source,issue_order='in_order',**args)
        unordered=simulate_core(source,issue_order='out_of_order',**args)
        self.assertGreaterEqual(ordered['rows'][3]['issue'],ordered['rows'][2]['issue'])
        self.assertLess(unordered['rows'][3]['issue'],unordered['rows'][2]['issue'])
        self.assertEqual(ordered['registers'],unordered['registers'])

    def test_cpu_alu_resources_and_cache_geometry_are_used(self):
        source='\n'.join(f'ADDI x{i},x0,{i}' for i in range(1,17))+'\nHALT'
        one=simulate_core(source,width=8,execution_ports=8,alu_ports=1)
        four=simulate_core(source,width=8,execution_ports=8,alu_ports=4)
        self.assertGreater(one['cycles'],four['cycles'])
        memory_source='LW x1,0(x0)\nLW x2,1024(x0)\nLW x3,0(x0)\nHALT'
        direct=simulate_core(memory_source,cache_kb=1,cache_ways=1)
        assoc=simulate_core(memory_source,cache_kb=1,cache_ways=2)
        self.assertEqual(direct['cache']['misses'],3)
        self.assertEqual(assoc['cache']['misses'],2)

    def test_gpu_resident_warps_hide_alu_latency(self):
        args=dict(elements=128,warp_size=8,processors=1,alu_latency=6)
        one=gpu_lab(resident_warps=1,**args)
        four=gpu_lab(resident_warps=4,**args)
        self.assertEqual(one['output'],four['output'])
        self.assertGreater(one['compute_cycles'],four['compute_cycles'])
        slow=gpu_lab(resident_warps=4,issue_interval=4,**args)
        self.assertGreater(slow['compute_cycles'],four['compute_cycles'])

    def test_isp_stage_bypass_changes_function_and_buffer_requirements(self):
        raw=[[1088]*4 for _ in range(4)]
        full=isp_lab(width=4,height=4,raw=raw,black_level=64,gamma=1,
                     stages=['black_level','gain','demosaic','gamma'])
        bypass=isp_lab(width=4,height=4,raw=raw,black_level=64,gamma=1,stages=[])
        self.assertEqual(full['output'][0][0],[64,64,64])
        self.assertEqual(bypass['output'][0][0],[68,68,68])
        self.assertEqual(bypass['color_mode'],'raw_mono')
        self.assertEqual(bypass['line_buffer_bytes'],0)
        self.assertGreater(full['compute_cycles'],bypass['compute_cycles'])

    def test_resource_inputs_fail_explicitly(self):
        with self.assertRaises(ValueError):simulate_core('HALT',issue_order='speculative')
        with self.assertRaises(ValueError):simulate_core('HALT',alu_ports=0)
        with self.assertRaises(ValueError):gpu_lab(resident_warps=0)
        with self.assertRaises(ValueError):isp_lab(stages=['HDR'])


if __name__=='__main__':unittest.main()
