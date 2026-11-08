import unittest
from silicon_professor.engine.arch_cpu import execute_architecture
from silicon_professor.engine.lab_cpu import simulate_core


class TestX64(unittest.TestCase):
    def execute(self,program):return execute_architecture('x86_64',program)

    def test_full_width_extended_registers_and_eax_zero_extends(self):
        r=self.execute('MOV RAX,0x1234567800000001\nMOV R8,0x1122334455667788\nMOV R9,R8\nMOV EAX,7\nMOV R8D,9\nHALT')
        regs=dict(zip(r['register_names'],r['registers']))
        self.assertEqual(regs['RAX'],7);self.assertEqual(regs['R8'],9);self.assertEqual(regs['R9'],0x1122334455667788)
        self.assertEqual(r['listing'][1]['bytes'],'49b88877665544332211')
        self.assertEqual(r['listing'][2]['bytes'],'4d89c1')

    def test_signed_immediate_flags_and_qword_memory(self):
        p='MOV RAX,0x7fffffffffffffff\nADD RAX,1\nMOV R8,256\nMOV [R8],RAX\nMOV R9,[R8]\nCMP R9,RAX\nJE done\nMOV R10,77\ndone:\nHALT'
        r=self.execute(p);self.assertEqual(r['registers'][9],0x8000000000000000)
        self.assertEqual(r['registers'][10],0);self.assertTrue(r['flags']['ZF'])
        self.assertEqual(r['listing'][1]['bytes'],'4881c001000000')
        self.assertEqual(r['listing'][3]['bytes'],'49898000000000')
        traced=simulate_core(p,architecture='x86_64',extensions=[])
        self.assertEqual(traced['registers'],r['registers'])
        self.assertEqual(next(row for row in traced['rows'] if row['instruction'].op=='SW')['store_bits'],64)

    def test_imul_and_shift_widths(self):
        r=self.execute('MOV R8,-7\nMOV R9,3\nIMUL R8,R9\nMOV R10,R8\nSHR R10,63\nMOV R11,R8\nSAR R11,63\nHALT')
        self.assertEqual(r['registers'][8],(1<<64)-21)
        self.assertEqual(r['registers'][10],1);self.assertEqual(r['registers'][11],(1<<64)-1)

    def test_rejects_unimplemented_or_unencodable_forms(self):
        for p in ['MOV RAX,EBX','ADD RAX,0x80000000','MOV [1234],RAX','MOV AX,1','VADDPS XMM0,XMM1,XMM2']:
            with self.subTest(p=p),self.assertRaises(ValueError):self.execute(p)

    def test_zero_count_dword_shift_keeps_flags_and_writes_dword(self):
        r=self.execute('MOV RAX,0x1234567800000001\nCMP RAX,RAX\nSHL EAX,0\nHALT')
        self.assertEqual(r['registers'][0],1);self.assertTrue(r['flags']['ZF'])
