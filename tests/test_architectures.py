import unittest
from silicon_professor.engine.arch_cpu import execute_architecture
from silicon_professor.engine.lab_cpu import simulate_core


class TestArchitectureSemantics(unittest.TestCase):
    def test_x86_flags_unsigned_vs_signed_branches(self):
        p='MOV EAX, 0xffffffff\nMOV EBX, 1\nCMP EAX, EBX\nJL negative\nMOV ECX, 9\nnegative:\nMOV EDX, 3\nHALT'
        r=execute_architecture('x86_32',p)
        self.assertEqual(r['registers'][0],0xffffffff)
        self.assertEqual(r['registers'][1],0)
        self.assertEqual(r['registers'][2],3)
        self.assertTrue(r['flags']['SF'])
        self.assertFalse(r['flags']['CF'])

    def test_x86_add_updates_zero_carry_overflow(self):
        r=execute_architecture('x86_32','MOV EAX, 0xffffffff\nADD EAX, 1\nHALT')
        self.assertEqual(r['registers'][0],0)
        self.assertTrue(r['flags']['ZF']);self.assertTrue(r['flags']['CF']);self.assertFalse(r['flags']['OF'])
        r=execute_architecture('x86_32','MOV EAX, 0x7fffffff\nADD EAX, 1\nHALT')
        self.assertTrue(r['flags']['OF']);self.assertFalse(r['flags']['CF'])

    def test_x86_mov_does_not_change_flags_and_real_encoding(self):
        r=execute_architecture('x86_32','MOV EAX, 7\nCMP EAX, 7\nMOV EBX, 3\nHALT')
        self.assertTrue(r['flags']['ZF'])
        self.assertEqual(r['listing'][0]['bytes'],'b807000000')
        self.assertEqual(r['registers'][8] & (1<<6),1<<6)

    def test_x86_memory_and_flags_dependency_timing(self):
        p='MOV EAX, 6\nMOV EBX, 7\nIMUL EAX, EBX\nMOV [0], EAX\nMOV ECX, [0]\nCMP ECX, 42\nJNE fail\nMOV EDX, 1\nHALT\nfail:\nMOV EDX, 9\nHALT'
        r=simulate_core(p,architecture='x86_32',extensions=[])
        self.assertEqual(r['registers'][1],42)
        self.assertEqual(r['registers'][2],1)
        self.assertEqual(r['memory'][0],42)

    def test_a64_writes_w_zero_extend_x(self):
        r=execute_architecture('aarch64','MOV X0, #-1\nMOV W0, #1\nMOV X1, XZR\nADD X2, X0, #2\nHALT')
        self.assertEqual(r['registers'][:3],[1,0,3])

    def test_a64_zero_register_flags_and_borrow(self):
        r=execute_architecture('aarch64','MOV X0, #0\nMOV X1, #1\nCMP X0, X1\nB.LO below\nMOV X2, #9\nbelow:\nMOV X3, #3\nHALT')
        self.assertEqual(r['registers'][2],0);self.assertEqual(r['registers'][3],3)
        self.assertFalse(r['flags']['C'])
        self.assertEqual(r['registers'][32] & (1<<31),1<<31)
        r=execute_architecture('aarch64','MOV XZR, #9\nMOV X0, XZR\nHALT')
        self.assertEqual(r['registers'][0],0)

    def test_a64_64bit_memory_and_link(self):
        p='MOV X0, #-1\nSTR X0, [X4, #8]\nLDR X1, [X4, #8]\nBL function\nHALT\nfunction:\nMOV X2, #7\nRET'
        r=simulate_core(p,architecture='aarch64',extensions=[])
        self.assertEqual(r['registers'][1],0xffffffffffffffff)
        self.assertEqual(r['registers'][2],7)
        self.assertEqual(r['registers'][30],16)
        self.assertEqual(r['memory'][8],0xffffffff);self.assertEqual(r['memory'][12],0xffffffff)

    def test_a64_immediate_mov_encoding_and_invalid_base(self):
        r=execute_architecture('aarch64','MOV X0,#42\nMOV X1,#-1\nHALT')
        self.assertEqual(r['listing'][0]['word'],0xd2800540)
        self.assertEqual(r['listing'][1]['word'],0x92800001)
        with self.assertRaises(ValueError):execute_architecture('aarch64','LDR X0,[XZR]')

    def test_unimplemented_architecture_or_extension_rejected(self):
        with self.assertRaises(ValueError):execute_architecture('mips','ADD $1,$2,$3')
        with self.assertRaises(ValueError):simulate_core('MOV EAX,1',architecture='x86_32',extensions=['AVX'])

    def test_a64_sp_and_unencoded_addressing_are_rejected(self):
        for p in ('ADD X0,XZR,#1','ADD XZR,X0,#1','LDR X0,[X1,#3]'):
            with self.assertRaises(ValueError):execute_architecture('aarch64',p)

    def test_x86_undefined_imul_flags_not_used_as_fact(self):
        p='MOV EAX,2\nMOV EBX,3\nIMUL EAX,EBX\nJE done\ndone:\nHALT'
        with self.assertRaises(ValueError):execute_architecture('x86_32',p)


if __name__=='__main__':unittest.main()
