import unittest
from silicon_professor.engine.cpu_features import run_cpu_pair
from silicon_professor.engine.lab_cpu import simulate_core, architectural_state_at

class TestCPUFeatures(unittest.TestCase):
    def test_smt_shares_ports_and_preserves_independent_registers(self):
        a='ADDI x1,x0,1\n'+'MUL x1,x1,x1\n'*20+'HALT'
        b='ADDI x1,x0,7\n'+'ADDI x2,x0,9\n'*20+'HALT'
        r=run_cpu_pair(a,b,width=2,execution_ports=2,alu_ports=1,multiply_ports=1,multiply_latency=8,pipeline=2)
        self.assertTrue(r['functional_check'])
        self.assertEqual(r['threads'][0]['registers'][1],1)
        self.assertEqual(r['threads'][1]['registers'][1],7)
        for cycle in range(r['cycles']+1):
            rows=[v for v in r['rows'] if v['issue']==cycle]
            self.assertLessEqual(len(rows),2)
            self.assertLessEqual(sum(v['unit']=='alu' for v in rows),1)
        self.assertLess(r['cycles'],r['sequential_cycles'])

    def test_mshrs_overlap_independent_misses_not_dependencies(self):
        source='LW x1,0(x0)\nLW x2,64(x0)\nLW x3,128(x0)\nHALT'
        one=simulate_core(source,pipeline=2,mshrs=1)
        four=simulate_core(source,pipeline=2,mshrs=4)
        self.assertEqual(one['registers'],four['registers'])
        self.assertLess(four['cycles'],one['cycles'])
        chain='LW x1,0(x0)\nLW x2,0(x1)\nHALT'
        a=simulate_core(chain,memory={0:64,64:5},pipeline=2,mshrs=1)
        b=simulate_core(chain,memory={0:64,64:5},pipeline=2,mshrs=4)
        self.assertGreaterEqual(b['rows'][1]['issue'],b['rows'][0]['done'])
        self.assertEqual(a['registers'],b['registers'])

    def test_predictor_learns_loop_and_keeps_same_function(self):
        source='ADDI x1,x0,16\nloop:\nADDI x1,x1,-1\nBNE x1,x0,loop\nHALT'
        off=simulate_core(source,pipeline=12)
        on=simulate_core(source,pipeline=12,branch_predictor='two_bit')
        self.assertEqual(off['registers'],on['registers'])
        self.assertEqual(on['prediction']['mispredictions'],2)
        self.assertLess(on['cycles'],off['cycles'])

    def test_second_thread_requires_hardware_and_no_invalid_controls(self):
        with self.assertRaises(ValueError):simulate_core('HALT',source2='HALT',smt_threads=1)
        with self.assertRaises(ValueError):simulate_core('HALT',mshrs=0)
        with self.assertRaises(ValueError):simulate_core('HALT',branch_predictor='magic')

    def test_pair_accepts_hardware_smt_setting(self):
        result=run_cpu_pair('ADDI x1,x0,3\nHALT','ADDI x1,x0,9\nHALT',smt_threads=2)
        self.assertEqual([t['registers'][1] for t in result['threads']],[3,9])
        self.assertEqual(len(result['solo']),2)

    def test_replay_filters_thread_and_does_not_stop_at_slow_other_thread(self):
        result=run_cpu_pair('LW x1,0(x0)\nHALT','ADDI x1,x0,9\nHALT',pipeline=2,miss_latency=80,memory={0:7})
        early=next(r['retire'] for r in result['rows'] if r['thread']==1)
        state=architectural_state_at(result,early,thread=1)
        self.assertEqual(state['registers'][1],9)
        self.assertGreater(state['retired'],0)
        self.assertEqual(architectural_state_at(result,early,thread=0)['registers'][1],0)
        for tid in (0,1):
            state=architectural_state_at(result,result['cycles'],thread=tid)
            self.assertEqual(state['registers'],result['threads'][tid]['registers'])
            self.assertEqual(state['memory'],result['threads'][tid]['memory'])
        with self.assertRaises(ValueError):architectural_state_at(result,0,thread=2)

    def test_smt_functional_state_across_all_integer_isas(self):
        for arch,a,b,index in [
            ('riscv32','ADDI x1,x0,3\nSW x1,0(x0)\nHALT','ADDI x1,x0,9\nSW x1,0(x0)\nHALT',1),
            ('x86_32','MOV EAX,3\nMOV [0],EAX\nHALT','MOV EAX,9\nMOV [0],EAX\nHALT',0),
            ('x86_64','MOV RAX,3\nMOV R8,0\nMOV [R8],RAX\nHALT','MOV RAX,9\nMOV R8,0\nMOV [R8],RAX\nHALT',0),
            ('aarch64','MOV X0,#3\nSTR X0,[X1]\nHALT','MOV X0,#9\nSTR X0,[X1]\nHALT',0),
        ]:
            with self.subTest(architecture=arch):
                r=run_cpu_pair(a,b,architecture=arch,extensions=('M',) if arch=='riscv32' else (),mshrs=2)
                self.assertEqual([t['registers'][index] for t in r['threads']],[3,9])
                self.assertEqual([t['memory'][0] for t in r['threads']],[3,9])

    def test_replay_initial_memory_normalizes_signed_input(self):
        r=run_cpu_pair('LW x1,0(x0)\nHALT','LW x2,0(x0)\nHALT',memory={0:-1},mshrs=2)
        for tid in (0,1):
            state=architectural_state_at(r,r['cycles'],thread=tid)
            self.assertEqual(state['memory'],r['threads'][tid]['memory'])

    def test_used_ops_preserve_source_branch_aliases_from_both_threads(self):
        from silicon_professor.engine.labs import run_experiment
        r=run_experiment('cpu',dict(architecture='x86_32',extensions=[],smt_threads=2,
            source='MOV EAX,3\nHALT',source2='MOV EAX,0xffffffff\nCMP EAX,1\nJL done\nMOV EAX,9\ndone:\nHALT'))
        self.assertIn('JL',r['used_ops'])
