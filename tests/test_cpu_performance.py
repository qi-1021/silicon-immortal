import unittest
from silicon_professor.data.core_designs import default_hardware
from silicon_professor.engine.core_studio import cpu_performance_report,run_design


class TestCPUPerformance(unittest.TestCase):
    def test_suite_exposes_width_and_cache_tradeoffs_and_does_not_fabricate_speedup(self):
        h=default_hardware('cpu')
        one=h|dict(width=1,execution_ports=1,alu_ports=1,cache_kb=1)
        wide=h|dict(width=4,execution_ports=4,alu_ports=4,cache_kb=16)
        a=cpu_performance_report(one);b=cpu_performance_report(wide)
        aa={x['id']:x for x in a['cases']};bb={x['id']:x for x in b['cases']}
        self.assertGreater(bb['independent']['ipc'],aa['independent']['ipc'])
        self.assertLess(bb['cache']['cycles'],aa['cache']['cycles'])
        self.assertEqual(bb['dependency']['cycles'],aa['dependency']['cycles'])
        self.assertGreater(b['ipc'],a['ipc'])
        for result in [a,b]:
            self.assertAlmostEqual(result['ipc'],result['instructions']/result['cycles'])

    def test_same_short_memory_test_really_can_have_identical_ipc(self):
        h=default_hardware('cpu');a=run_design('cpu',h)
        b=run_design('cpu',h|dict(width=12,execution_ports=12,alu_ports=12,rob_size=128))
        self.assertEqual(a['ipc'],b['ipc'])
        self.assertLess(cpu_performance_report(b['hardware'])['cycles'],cpu_performance_report(h)['cycles'])

    def test_supported_architectures_use_native_programs(self):
        for architecture in ('riscv32','x86_32','aarch64'):
            r=cpu_performance_report(default_hardware('cpu')|dict(architecture=architecture))
            self.assertTrue(all(case['functional_check'] for case in r['cases']))
            self.assertEqual(r['hardware']['architecture'],architecture)
