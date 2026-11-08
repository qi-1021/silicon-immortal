import unittest
from silicon_professor.engine.lab_accelerators import gpu_lab,npu_lab,isp_lab


class TestAccelerators(unittest.TestCase):
    def test_gpu_per_lane_output_and_divergence(self):
        r=gpu_lab(elements=32,warp_size=8,processors=1,task='branch',pattern='alternating')
        a=gpu_lab(elements=32,warp_size=8,processors=1,task='branch',pattern='uniform')
        self.assertTrue(r['functional_check'])
        self.assertGreater(r['compute_cycles'],a['compute_cycles'])
        self.assertEqual(len(r['output']),32)

    def test_npu_integer_gemm_exact_and_accumulator_overflow(self):
        r=npu_lab(m=2,n=2,k=2,rows=2,cols=2,a=[[1,2],[3,4]],b=[[5,6],[7,8]])
        self.assertEqual(r['output'],[[19,22],[43,50]])
        r=npu_lab(m=1,n=1,k=4,rows=1,cols=1,accumulator_bits=16,a=[[127]*4],b=[[127] for _ in range(4)])
        self.assertEqual(r['overflow_count'],1)
        self.assertEqual(r['output'][0][0],-1020)

    def test_npu_scratchpad_and_bandwidth_constraints(self):
        r=npu_lab(m=8,n=8,k=8,rows=8,cols=8,scratchpad_kb=1)
        self.assertTrue(r['scratchpad_fits'])
        small=npu_lab(m=32,n=32,k=64,rows=32,cols=32,scratchpad_kb=1)
        self.assertFalse(small['scratchpad_fits'])
        a=npu_lab(bandwidth_gbs=1);b=npu_lab(bandwidth_gbs=16)
        self.assertGreater(a['transfer_cycles'],b['transfer_cycles'])

    def test_isp_constant_raw_black_level_and_gamma(self):
        r=isp_lab(width=4,height=4,raw=[[1088]*4 for _ in range(4)],black_level=64,gain=1,gamma=1,output_bits=8)
        self.assertEqual(r['output'][0][0],[64,64,64])
        self.assertTrue(r['functional_check'])
        z=isp_lab(width=4,height=4,raw=[[32]*4 for _ in range(4)],black_level=64)
        self.assertEqual(z['output'][2][2],[0,0,0])

    def test_invalid_shapes_and_precision_rejected(self):
        with self.assertRaises(ValueError):npu_lab(m=2,n=2,k=2,a=[[1]],b=[[1]])
        with self.assertRaises(ValueError):npu_lab(precision_bits=4)
        with self.assertRaises(ValueError):isp_lab(gamma=0)


if __name__=='__main__':unittest.main()
