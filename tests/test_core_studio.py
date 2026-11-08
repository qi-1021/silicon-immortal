import copy
import tempfile
import unittest
from pathlib import Path

from silicon_professor.data.core_designs import default_hardware
from silicon_professor.engine.core_studio import (run_design, verify_design, structure,
                                                validate_hardware, design_model)
from silicon_professor.engine.ip_library import (make_design_asset, validate_asset,
                                                write_asset, read_asset, attach_asset)
from silicon_professor.engine.types import empty_design
from silicon_professor.engine.simulate import simulate
from silicon_professor import export


class TestCoreStudio(unittest.TestCase):
    def test_four_hardware_designs_run_and_verify_without_a_course(self):
        for kind in ('cpu','gpu','npu','isp'):
            hardware=default_hardware(kind)
            self.assertTrue(run_design(kind,hardware)['functional_check'])
            checks=verify_design(kind,hardware)
            self.assertTrue(checks['passed'],kind)
            self.assertGreaterEqual(len(checks['cases']),2)

    def test_cpu_multi_architecture_and_extension_design(self):
        for architecture in ('riscv32','x86_32','aarch64'):
            hardware=default_hardware('cpu');hardware['architecture']=architecture
            checks=verify_design('cpu',hardware)
            self.assertTrue(checks['passed'],architecture)
            self.assertGreaterEqual(len(checks['cases']),4)
        h=default_hardware('cpu');h['enable_m']=False
        with self.assertRaises(ValueError):run_design('cpu',h,{'source':'MUL x1,x0,x0\nHALT'})

    def test_identity_uses_hardware_not_testbench(self):
        h=default_hardware('cpu')
        a=make_design_asset('cpu','my core',h)
        run_design('cpu',h,{'source':'ADDI x1,x0,77\nHALT'})
        b=make_design_asset('cpu','my core',h)
        self.assertEqual(a['id'],b['id'])
        h['alu_ports']=3
        self.assertNotEqual(a['id'],make_design_asset('cpu','my core',h)['id'])
        self.assertEqual(a['identity_basis'],'kind/name/design')

    def test_cor_roundtrip_rebuilds_mapping_and_rechecks(self):
        for kind in ('cpu','gpu','npu','isp'):
            a=make_design_asset(kind,'my '+kind,default_hardware(kind))
            with tempfile.TemporaryDirectory() as td:
                path=write_asset(Path(td)/kind,a)
                self.assertEqual(path.suffix,'.cor')
                restored=read_asset(path)
                self.assertEqual(restored['design'],a['design'])
                self.assertEqual(restored['id'],a['id'])
                self.assertTrue(restored['verification']['passed'])
                bad=copy.deepcopy(a);bad['config']={'source':'untrusted'}
                self.assertEqual(validate_asset(bad)['config'],a['config'])
                bad['design']['hardware']['unsupported_speculation']=True
                with self.assertRaises(ValueError):validate_asset(bad)

    def test_soc_uses_design_resources_and_survives_sil(self):
        d=empty_design('sandbox');d.cores=[]
        for kind in ('cpu','gpu','npu','isp'):
            attach_asset(d,make_design_asset(kind,'Studio '+kind,default_hardware(kind)))
        r=simulate(d);self.assertTrue(r['valid'],r['errors'])
        with tempfile.TemporaryDirectory() as td:
            path=export.export_to(Path(td)/'studio.sil',d,r)
            restored,_=export.read_design(path)
            self.assertEqual(restored.embedded_ips.keys(),d.embedded_ips.keys())
            self.assertEqual(simulate(restored)['die_area'],r['die_area'])

    def test_hardware_controls_graph_and_ppa(self):
        h=default_hardware('cpu');one=design_model('cpu','cpu',h)
        h['alu_ports']=4;four=design_model('cpu','cpu',h)
        self.assertGreater(four['logic_area'],one['logic_area'])
        h=default_hardware('isp');h['demosaic_enabled']=False
        graph=structure('isp',h)
        self.assertNotIn('demosaic',{node['id'] for node in graph['nodes']})
        self.assertNotIn('line_buffer',{node['id'] for node in graph['nodes']})
        self.assertIn('quantize',{node['id'] for node in graph['nodes']})

    def test_hardware_rejects_bench_fields_and_small_scratchpad(self):
        h=default_hardware('cpu');h['source']='HALT'
        with self.assertRaises(ValueError):validate_hardware('cpu',h)
        h=default_hardware('npu');h.update(rows=64,cols=64,scratchpad_kb=1)
        with self.assertRaisesRegex(ValueError,'scratchpad'):validate_hardware('npu',h)


if __name__=='__main__':unittest.main()
