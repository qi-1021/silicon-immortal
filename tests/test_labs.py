"""依据规范与手算结果检查实验语义，而非只与内部参考执行器互比。"""
import math
import json
from pathlib import Path
import unittest

from silicon_professor.engine.isa import assemble, encode, execute, instruction_catalog, Instruction
from silicon_professor.engine.lab_cpu import PROGRAMS, simulate_core, architectural_state_at
from silicon_professor.engine.lab_memory import Cache, run_cache_trace
from silicon_professor.engine.lab_system import (logic_lab, power_lab, route,
                                                 simulate_network, timing_lab)


def run(source, extensions=("M", "Zbb"), memory=None):
    return execute(assemble(source, extensions), memory)


class TestInstructionSemantics(unittest.TestCase):
    def test_all_encodings_match_pinned_official_opcode_masks(self):
        masks=json.loads((Path(__file__).with_name('fixtures')/'isa_opcode_masks.json').read_text())
        self.assertEqual(set(masks),{op for ops in instruction_catalog().values() for op in ops})
        for op,spec in masks.items():
            word=encode(Instruction(op,rd=1,rs1=2,rs2=0 if op=='ZEXT.H' else 3,imm=4))
            self.assertEqual(word & spec['mask'],spec['value'],op)
    def test_zero_register_and_signed_immediate(self):
        r = run("ADDI x0,x0,7\nADDI x1,x0,-1\nSLTIU x2,x0,-1\nHALT")
        self.assertEqual(r["registers"][:3], [0, 0xffffffff, 1])

    def test_signed_and_unsigned_comparison(self):
        r = run("ADDI x1,x0,-1\nADDI x2,x0,1\nSLT x3,x1,x2\nSLTU x4,x1,x2\nHALT")
        self.assertEqual(r["registers"][3:5], [1, 0])

    def test_shifts_mask_register_amount(self):
        r = run("ADDI x1,x0,-8\nADDI x2,x0,33\nSRA x3,x1,x2\nSRL x4,x1,x2\nHALT")
        self.assertEqual(r["registers"][3:5], [0xfffffffc, 0x7ffffffc])

    def test_multiply_high_and_signed_division(self):
        r = run("ADDI x1,x0,-7\nADDI x2,x0,3\nDIV x3,x1,x2\nREM x4,x1,x2\nMULH x5,x1,x2\nMULHSU x6,x1,x2\nHALT")
        self.assertEqual(r["registers"][3:7], [0xfffffffe, 0xffffffff, 0xffffffff, 0xffffffff])

    def test_division_zero_and_overflow(self):
        r = run("LUI x1,0x80000\nADDI x2,x0,-1\nDIV x3,x1,x2\nREM x4,x1,x2\nDIV x5,x1,x0\nREM x6,x1,x0\nHALT")
        self.assertEqual(r["registers"][3:7], [0x80000000, 0, 0xffffffff, 0x80000000])

    def test_little_endian_partial_store_and_load(self):
        r = run("LUI x1,0x12345\nADDI x1,x1,0x678\nSW x1,0(x0)\nLB x2,0(x0)\nLHU x3,2(x0)\nADDI x4,x0,-1\nSB x4,1(x0)\nLW x5,0(x0)\nHALT")
        self.assertEqual(r["registers"][2], 0x78)
        self.assertEqual(r["registers"][3], 0x1234)
        self.assertEqual(r["registers"][5], 0x1234ff78)

    def test_zbb_zero_counts_and_boolean_ops(self):
        r = run("ADDI x1,x0,-1\nCLZ x2,x0\nCTZ x3,x0\nCPOP x4,x1\nANDN x5,x1,x1\nXNOR x6,x1,x0\nHALT")
        self.assertEqual(r["registers"][2:7], [32, 32, 32, 0, 0])

    def test_rv32_zbb_rotate_extend_and_byte_operations(self):
        r=run("LUI x1,0x12350\nADDI x1,x1,-136\nADDI x2,x0,8\nROL x3,x1,x2\nRORI x4,x1,8\nSEXT.B x5,x1\nZEXT.H x6,x1\nORC.B x7,x1\nREV8 x8,x1\nHALT")
        self.assertEqual(r['registers'][3:9],[0x34ff7812,0x781234ff,0x78,0xff78,0xffffffff,0x78ff3412])
        negative=run('ADDI x1,x0,-128\nSEXT.B x2,x1\nSEXT.H x3,x1\nHALT')
        self.assertEqual(negative['registers'][2:4],[0xffffff80,0xffffff80])

    def test_zbb_min_max_signedness_and_encodings(self):
        r=run("ADDI x1,x0,-1\nADDI x2,x0,1\nMIN x3,x1,x2\nMINU x4,x1,x2\nMAX x5,x1,x2\nMAXU x6,x1,x2\nHALT")
        self.assertEqual(r['registers'][3:7],[0xffffffff,1,1,0xffffffff])
        instructions=assemble('REV8 x1,x2\nZEXT.H x1,x2\nRORI x1,x2,8',extensions=['Zbb'])
        self.assertEqual([encode(i) for i in instructions],[0x69815093,0x080140b3,0x60815093])

    def test_real_encodings(self):
        p = assemble("ADDI x1,x0,1\nADD x3,x1,x2\nSW x3,0(x0)\nMUL x3,x1,x2\nHALT")
        self.assertEqual([encode(i,n*4) for n,i in enumerate(p)], [0x00100093,0x002081b3,0x00302023,0x022081b3,None])

    def test_extension_is_required(self):
        for source in ("MUL x3,x1,x2", "CLZ x2,x1"):
            with self.assertRaises(ValueError): assemble(source, extensions=[])

    def test_branch_and_link(self):
        r = run("JAL x1,exit\nADDI x2,x0,9\nexit:\nADDI x3,x1,1\nHALT")
        self.assertEqual(r["registers"][1:4], [4, 0, 5])

    def test_misaligned_and_outside_code_trap(self):
        for source in ("LW x1,1(x0)\nHALT", "ADDI x1,x0,200\nJALR x0,0(x1)\nHALT"):
            with self.assertRaises(ValueError): run(source)

    def test_m_encoding_input_limit(self):
        with self.assertRaises(ValueError): assemble("ADDI x1,x0,4096")
        with self.assertRaises(ValueError): assemble("SLLI x1,x2,32")


class TestCoreTiming(unittest.TestCase):
    def test_wide_core_helps_independent_instructions(self):
        source = PROGRAMS["independent"]["source"]
        narrow = simulate_core(source, width=1, execution_ports=1)
        wide = simulate_core(source, width=4, execution_ports=4)
        self.assertLess(wide["cycles"], narrow["cycles"])
        self.assertEqual(wide["registers"], narrow["registers"])

    def test_dependency_chain_is_not_four_times_faster(self):
        source = PROGRAMS["dependency"]["source"]
        narrow = simulate_core(source, width=1, execution_ports=1)
        wide = simulate_core(source, width=4, execution_ports=4)
        self.assertGreater(wide["cycles"], narrow["cycles"] * .7)

    def test_array_sum_commits_correct_value(self):
        p = PROGRAMS["sum"]
        result = simulate_core(p["source"], memory=p["memory"])
        self.assertEqual(result["memory"][128], 136)
        for row in result["rows"]:
            self.assertLess(row["dispatch"], row["issue"])
            self.assertLessEqual(row["done"], row["retire"])

    def test_replay_changes_architectural_state_only_at_retirement(self):
        r=simulate_core('ADDI x1,x0,42\nADDI x2,x0,7\nSW x1,0(x0)\nHALT')
        first=r['rows'][0]['retire']
        self.assertEqual(architectural_state_at(r,first-1)['registers'][1],0)
        self.assertEqual(architectural_state_at(r,first)['registers'][1],42)
        final=architectural_state_at(r,r['cycles'])
        self.assertEqual(final['registers'],r['registers'])
        self.assertEqual(final['memory'],r['memory'])

    def test_rename_handles_war_waw_and_memory_order(self):
        source="ADDI x1,x0,2\nADDI x2,x0,3\nMUL x3,x1,x2\nADDI x1,x0,9\nADD x4,x1,x2\nSW x3,0(x0)\nSB x1,1(x0)\nLW x5,0(x0)\nHALT"
        r = simulate_core(source,width=4,execution_ports=4)
        self.assertEqual(r["registers"][3:6],[6,12,0x906])


class TestCache(unittest.TestCase):
    def test_three_c_and_lru(self):
        c = Cache(capacity_bytes=128,line_bytes=64,ways=1)
        rows=[c.access(a) for a in (0,128,0)]
        self.assertEqual([r["miss_type"] for r in rows], ["compulsory","compulsory","conflict"])
        c = Cache(capacity_bytes=64,line_bytes=64,ways=1)
        rows=[c.access(a) for a in (0,64,0)]
        self.assertEqual(rows[-1]["miss_type"],"capacity")

    def test_lru_vs_fifo_and_dirty_writeback(self):
        lru=Cache(128,64,2,'lru'); fifo=Cache(128,64,2,'fifo')
        for a in (0,64,0,128): lru.access(a); fifo.access(a)
        self.assertTrue(lru.access(0)["hit"])
        self.assertFalse(fifo.access(0)["hit"])
        c=Cache(64,64,1); c.access(0,write=True)
        self.assertTrue(c.access(64)["writeback"])

    def test_hand_calculated_amat(self):
        r=run_cache_trace([0,4,8,64],capacity_bytes=128,ways=1,hit_latency=2,miss_latency=40)
        self.assertEqual((r["hits"],r["misses"],r["serial_cycles"],r["amat"]),(2,2,84,21))


class TestSystem(unittest.TestCase):
    def test_route_and_link_arbitration(self):
        self.assertEqual(route(0,15,16,'mesh'),[0,1,2,3,7,11,15])
        self.assertEqual(route(0,7,8,'ring'),[0,7])
        r=simulate_network([(0,1,0),(0,1,0)],count=4)
        self.assertEqual([p["arrival"] for p in r["packets"]],[1,2])
        self.assertEqual(r["queue_wait"],1)

    def test_timing_slack_and_nan_rejected(self):
        r=timing_lab([300,450],clock_ghz=2,setup_ps=40,skew_ps=20)
        self.assertEqual(r["wns"],-10)
        self.assertFalse(r["setup_met"])
        with self.assertRaises(ValueError): timing_lab([100],setup_ps=float('nan'))

    def test_power_units_and_thermal_time_constant(self):
        r=power_lab(capacitance_pf=1000,activity=.2,voltage=1,frequency_ghz=2,leakage_w=.1,thermal_r=5,thermal_c=2,duration=10)
        self.assertAlmostEqual(r["dynamic_w"],.4)
        self.assertAlmostEqual(r["final_c"],25+2.5*(1-math.exp(-1)))

    def test_carry_is_not_signed_overflow(self):
        a=logic_lab('add',127,1,8); b=logic_lab('add',255,1,8)
        self.assertEqual((a["carry"],a["overflow"],a["signed"]),(False,True,-128))
        self.assertEqual((b["carry"],b["overflow"],b["result"]),(True,False,0))


if __name__ == '__main__': unittest.main()
